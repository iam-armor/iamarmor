"""iamarmor CLI — entry point."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Optional

import typer

from iamarmor import __version__, extract_from_directory, load_default_rules
from iamarmor.cli.config import IamArmorConfig, discover_config, load_config
from iamarmor.cli.reporters import json_report, text_report
from iamarmor.exceptions import ConfigError, IamArmorError
from iamarmor.rules import RuleEngine, Severity

app = typer.Typer(
    name="iamarmor",
    help="IAM policy linter for Terraform.",
    add_completion=False,
)

_SEVERITY_NAMES = [s.value for s in Severity]  # info, low, medium, high, critical
_FAIL_ON_NAMES = _SEVERITY_NAMES + ["none"]


class OutputFormat(str, Enum):
    text = "text"
    json = "json"


class SeverityChoice(str, Enum):
    info = "info"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class FailOnChoice(str, Enum):
    info = "info"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"
    none = "none"


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"{__version__}")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """iamarmor — IAM policy linter for Terraform."""


@app.command()
def lint(
    path: Path = typer.Argument(
        Path("."),
        help="Path to Terraform files (file or directory). Defaults to current directory.",
        exists=False,  # We validate manually for better error messages
    ),
    format: OutputFormat = typer.Option(
        OutputFormat.text,
        "--format",
        "-f",
        help="Output format.",
    ),
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        help="Path to .iamarmor.yml. Defaults to auto-discovery upward from PATH.",
    ),
    no_config: bool = typer.Option(
        False,
        "--no-config",
        help="Ignore any .iamarmor.yml file.",
    ),
    severity_threshold: Optional[SeverityChoice] = typer.Option(
        None,
        "--severity-threshold",
        help="Only report findings at or above this severity (default: info).",
    ),
    fail_on: Optional[FailOnChoice] = typer.Option(
        None,
        "--fail-on",
        help="Exit non-zero if any finding meets this threshold (default: medium). Use 'none' to always exit 0.",
    ),
    select: Optional[str] = typer.Option(
        None,
        "--select",
        help="Comma-separated rule IDs to include (e.g. IAM001,IAM005).",
    ),
    ignore: Optional[str] = typer.Option(
        None,
        "--ignore",
        help="Comma-separated rule IDs to skip.",
    ),
    no_color: bool = typer.Option(
        False,
        "--no-color",
        help="Disable ANSI colors in text output.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Verbose logging to stderr.",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress non-error output (still emits findings).",
    ),
) -> None:
    """Scan Terraform files at PATH and report IAM policy violations."""
    # ── 1. Validate PATH ─────────────────────────────────────────────────────
    resolved_path = path.resolve()
    if not resolved_path.exists():
        typer.echo(f"[iamarmor] error: path does not exist: {path}", err=True)
        raise typer.Exit(code=2)

    # ── 2. Load config ───────────────────────────────────────────────────────
    cfg: IamArmorConfig | None = None
    if not no_config:
        cfg_path: Path | None = None
        if config is not None:
            cfg_path = config.resolve()
            if not cfg_path.is_file():
                typer.echo(f"[iamarmor] error: config file not found: {config}", err=True)
                raise typer.Exit(code=2)
        else:
            cfg_path = discover_config(resolved_path)

        if cfg_path is not None:
            if verbose:
                typer.echo(f"[iamarmor] loading config: {cfg_path}", err=True)
            try:
                cfg = load_config(cfg_path)
            except ConfigError as exc:
                typer.echo(f"[iamarmor] error: {exc}", err=True)
                raise typer.Exit(code=2)

    # ── 3. Determine effective settings (CLI overrides config) ───────────────
    effective_threshold_str = (
        severity_threshold.value
        if severity_threshold is not None
        else (cfg.severity_threshold if cfg else None) or "info"
    )
    effective_fail_on_str = (
        fail_on.value
        if fail_on is not None
        else (cfg.fail_on if cfg else None) or "medium"
    )

    # --select / --ignore CLI flags (split comma-separated)
    cli_select: list[str] | None = None
    cli_ignore: list[str] | None = None
    if select is not None:
        cli_select = [s.strip() for s in select.split(",") if s.strip()]
    if ignore is not None:
        cli_ignore = [s.strip() for s in ignore.split(",") if s.strip()]

    # CLI takes precedence over config
    effective_select: list[str] | None = cli_select if cli_select is not None else (cfg.select if cfg else None)
    effective_ignore: list[str] | None = cli_ignore if cli_ignore is not None else (cfg.ignore if cfg else None)

    # ── 4. Collect resources ─────────────────────────────────────────────────
    try:
        if resolved_path.is_file():
            from iamarmor import extract_resources, parse_file
            parsed = parse_file(resolved_path)
            resources = extract_resources(parsed, resolved_path)
        else:
            resources = extract_from_directory(resolved_path)
    except IamArmorError as exc:
        typer.echo(f"[iamarmor] error: {exc}", err=True)
        raise typer.Exit(code=3)

    # ── 5. Build rule list ───────────────────────────────────────────────────
    try:
        rules = load_default_rules()
    except IamArmorError as exc:
        typer.echo(f"[iamarmor] error: loading rules: {exc}", err=True)
        raise typer.Exit(code=3)

    # Apply config-level severity overrides
    if cfg and cfg.overrides:
        from iamarmor.rules.models import Rule
        overridden: list = []
        for rule in rules:
            if rule.id in cfg.overrides:
                ov = cfg.overrides[rule.id]
                new_sev = Severity(ov["severity"]) if "severity" in ov else rule.severity
                overridden.append(
                    Rule(
                        id=rule.id,
                        name=rule.name,
                        severity=new_sev,
                        message=rule.message,
                        check=rule.check,
                        description=rule.description,
                        tags=rule.tags,
                    )
                )
            else:
                overridden.append(rule)
        rules = overridden

    # Apply select / ignore filters
    if effective_select is not None:
        select_set = set(effective_select)
        rules = [r for r in rules if r.id in select_set]
    elif effective_ignore is not None:
        ignore_set = set(effective_ignore)
        rules = [r for r in rules if r.id not in ignore_set]

    # ── 6. Run engine ────────────────────────────────────────────────────────
    try:
        all_findings = RuleEngine(rules=rules).run(resources)
    except IamArmorError as exc:
        typer.echo(f"[iamarmor] error: {exc}", err=True)
        raise typer.Exit(code=3)

    # ── 7. Filter by severity threshold ─────────────────────────────────────
    threshold_sev = Severity(effective_threshold_str)
    threshold_rank = _SEVERITY_NAMES.index(threshold_sev.value)
    findings = [
        f for f in all_findings
        if _SEVERITY_NAMES.index(f.severity.value) >= threshold_rank
    ]

    # Count scanned files
    scanned_files = _count_tf_files(resolved_path)

    # ── 8. Format and print ──────────────────────────────────────────────────
    base_path = resolved_path if resolved_path.is_dir() else resolved_path.parent

    if format == OutputFormat.json:
        output = json_report(findings, scanned_files, base_path=base_path)
        if not quiet:
            typer.echo(output)
    else:
        if not quiet:
            text_report(findings, scanned_files, no_color=no_color, base_path=base_path)

    # ── 9. Exit code ─────────────────────────────────────────────────────────
    if effective_fail_on_str == "none":
        raise typer.Exit(code=0)

    fail_sev = Severity(effective_fail_on_str)
    fail_rank = _SEVERITY_NAMES.index(fail_sev.value)
    has_failing = any(
        _SEVERITY_NAMES.index(f.severity.value) >= fail_rank
        for f in findings
    )
    raise typer.Exit(code=1 if has_failing else 0)


def _count_tf_files(path: Path) -> int:
    """Count .tf files under *path* (or 1 if path is a single file)."""
    if path.is_file():
        return 1
    return sum(1 for _ in path.rglob("*.tf"))


if __name__ == "__main__":
    app()
