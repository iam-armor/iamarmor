"""Config loader for .iamarmor.yml."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

from iamarmor.exceptions import ConfigError

_SUPPORTED_VERSIONS = {1}
_KNOWN_TOP_KEYS = {"version", "severity_threshold", "fail_on", "rules", "paths"}
_SEVERITY_VALUES = {"info", "low", "medium", "high", "critical"}


def _warn(msg: str) -> None:
    print(f"[iamarmor] warning: {msg}", file=sys.stderr)


def discover_config(start_path: Path) -> Path | None:
    """Walk upward from *start_path* looking for .iamarmor.yml.

    Returns the first match or None if no config is found before the filesystem root.
    """
    candidate = start_path if start_path.is_dir() else start_path.parent
    candidate = candidate.resolve()
    while True:
        config_file = candidate / ".iamarmor.yml"
        if config_file.is_file():
            return config_file
        parent = candidate.parent
        if parent == candidate:
            # Reached filesystem root
            return None
        candidate = parent


def load_config(path: Path) -> "IamArmorConfig":
    """Load and validate a .iamarmor.yml file.

    Raises:
        ConfigError: If the file cannot be read, is malformed YAML, or fails validation.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"Cannot read config file {path}: {exc}") from exc

    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ConfigError(f"YAML parse error in {path}: {exc}") from exc

    if data is None:
        data = {}

    if not isinstance(data, dict):
        raise ConfigError(f"Config file {path} must be a YAML mapping, got {type(data).__name__}")

    # Warn about unknown top-level keys (forward-compat)
    for key in data:
        if key not in _KNOWN_TOP_KEYS:
            _warn(f"Unknown key {key!r} in {path} — ignoring (forward-compat)")

    # Validate version
    version = data.get("version")
    if version is None:
        raise ConfigError(f"Config file {path} is missing required key 'version'")
    if version not in _SUPPORTED_VERSIONS:
        raise ConfigError(
            f"Config file {path} has unsupported version {version!r}. "
            f"Supported versions: {sorted(_SUPPORTED_VERSIONS)}"
        )

    # Validate severity_threshold
    severity_threshold = data.get("severity_threshold")
    if severity_threshold is not None:
        if severity_threshold not in _SEVERITY_VALUES:
            raise ConfigError(
                f"Config file {path}: 'severity_threshold' must be one of {sorted(_SEVERITY_VALUES)}, "
                f"got {severity_threshold!r}"
            )

    # Validate fail_on
    fail_on = data.get("fail_on")
    if fail_on is not None:
        valid_fail_on = _SEVERITY_VALUES | {"none"}
        if fail_on not in valid_fail_on:
            raise ConfigError(
                f"Config file {path}: 'fail_on' must be one of {sorted(valid_fail_on)}, "
                f"got {fail_on!r}"
            )

    # Validate rules section
    rules_cfg = data.get("rules", {})
    if not isinstance(rules_cfg, dict):
        raise ConfigError(f"Config file {path}: 'rules' must be a mapping")

    select = rules_cfg.get("select")
    ignore = rules_cfg.get("ignore")

    if select is not None and ignore is not None:
        raise ConfigError(
            f"Config file {path}: 'rules.select' and 'rules.ignore' are mutually exclusive — "
            "use one or the other, not both"
        )

    if select is not None and not isinstance(select, list):
        raise ConfigError(f"Config file {path}: 'rules.select' must be a list")
    if ignore is not None and not isinstance(ignore, list):
        raise ConfigError(f"Config file {path}: 'rules.ignore' must be a list")

    overrides: dict[str, Any] = {}
    raw_overrides = rules_cfg.get("overrides", {})
    if not isinstance(raw_overrides, dict):
        raise ConfigError(f"Config file {path}: 'rules.overrides' must be a mapping")
    for rule_id, override_val in raw_overrides.items():
        if not isinstance(override_val, dict):
            raise ConfigError(
                f"Config file {path}: 'rules.overrides.{rule_id}' must be a mapping"
            )
        if "severity" in override_val and override_val["severity"] not in _SEVERITY_VALUES:
            raise ConfigError(
                f"Config file {path}: 'rules.overrides.{rule_id}.severity' must be one of "
                f"{sorted(_SEVERITY_VALUES)}, got {override_val['severity']!r}"
            )
        overrides[rule_id] = override_val

    # Validate paths section
    paths_cfg = data.get("paths", {})
    if not isinstance(paths_cfg, dict):
        raise ConfigError(f"Config file {path}: 'paths' must be a mapping")

    include_globs: list[str] = paths_cfg.get("include", []) or []
    exclude_globs: list[str] = paths_cfg.get("exclude", []) or []

    if not isinstance(include_globs, list):
        raise ConfigError(f"Config file {path}: 'paths.include' must be a list")
    if not isinstance(exclude_globs, list):
        raise ConfigError(f"Config file {path}: 'paths.exclude' must be a list")

    return IamArmorConfig(
        config_path=path,
        version=version,
        severity_threshold=severity_threshold,
        fail_on=fail_on,
        select=list(select) if select is not None else None,
        ignore=list(ignore) if ignore is not None else None,
        overrides=overrides,
        include_globs=include_globs,
        exclude_globs=exclude_globs,
    )


class IamArmorConfig:
    """Parsed and validated .iamarmor.yml configuration."""

    def __init__(
        self,
        *,
        config_path: Path,
        version: int,
        severity_threshold: str | None,
        fail_on: str | None,
        select: list[str] | None,
        ignore: list[str] | None,
        overrides: dict[str, Any],
        include_globs: list[str],
        exclude_globs: list[str],
    ) -> None:
        self.config_path = config_path
        self.version = version
        self.severity_threshold = severity_threshold
        self.fail_on = fail_on
        self.select = select
        self.ignore = ignore
        self.overrides = overrides
        self.include_globs = include_globs
        self.exclude_globs = exclude_globs
