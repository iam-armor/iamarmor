"""YAML loader for iamarmor rule packs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from iamarmor.exceptions import RuleLoadError
from iamarmor.rules.models import Rule, Severity
from iamarmor.rules.registry import CHECKS

_REQUIRED_KEYS = {"id", "name", "severity", "message", "check"}


def load_rules_from_yaml(path: Path) -> list[Rule]:
    """Load rules from a YAML file at *path*.

    Raises:
        RuleLoadError: If the file is missing, malformed, or contains unknown
            severities or check names.
    """
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise RuleLoadError(f"Cannot read rules file {path}: {exc}") from exc

    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise RuleLoadError(f"YAML parse error in {path}: {exc}") from exc

    if not isinstance(data, list):
        raise RuleLoadError(f"Expected a YAML list of rule objects in {path}, got {type(data).__name__}")

    rules: list[Rule] = []
    for i, entry in enumerate(data):
        if not isinstance(entry, dict):
            raise RuleLoadError(f"Rule #{i} in {path} is not a mapping")

        missing = _REQUIRED_KEYS - entry.keys()
        if missing:
            raise RuleLoadError(f"Rule #{i} in {path} is missing required keys: {missing}")

        raw_severity = entry["severity"]
        try:
            severity = Severity(raw_severity)
        except ValueError:
            valid = [s.value for s in Severity]
            raise RuleLoadError(
                f"Rule #{i} ({entry.get('id', '?')}) has unknown severity {raw_severity!r}. "
                f"Valid values: {valid}"
            )

        check_name: str = entry["check"]
        if check_name not in CHECKS:
            raise RuleLoadError(
                f"Rule #{i} ({entry.get('id', '?')}) references unknown check {check_name!r}. "
                "Make sure iamarmor.rules.checks is imported before loading rules."
            )

        raw_tags = entry.get("tags", [])
        tags: tuple[str, ...] = tuple(raw_tags) if isinstance(raw_tags, list) else (raw_tags,)

        rules.append(
            Rule(
                id=entry["id"],
                name=entry["name"],
                severity=severity,
                message=entry["message"],
                check=check_name,
                description=entry.get("description", ""),
                tags=tags,
            )
        )

    return rules


def load_default_rules() -> list[Rule]:
    """Load the bundled default rule pack that ships with iamarmor.

    Returns:
        A list of :class:`Rule` objects from ``default_pack.yml``.
    """
    # Import checks module to populate the CHECKS registry before loading YAML.
    import iamarmor.rules.checks  # noqa: F401

    import importlib.resources as pkg_resources

    try:
        # Python 3.9+: use files() API
        ref = pkg_resources.files("iamarmor.rules").joinpath("default_pack.yml")
        path = Path(str(ref))
        return load_rules_from_yaml(path)
    except (TypeError, AttributeError):
        # Fallback: locate the file relative to this module
        path = Path(__file__).parent / "default_pack.yml"
        return load_rules_from_yaml(path)
