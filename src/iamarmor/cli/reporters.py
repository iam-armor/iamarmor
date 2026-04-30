"""Output formatters for iamarmor CLI findings."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from iamarmor import __version__
from iamarmor.rules.models import Finding, Severity

_SEVERITY_ORDER = [s.value for s in Severity]  # info, low, medium, high, critical


def _severity_color(severity: str) -> str:
    return {
        "critical": "bold red",
        "high": "red",
        "medium": "yellow",
        "low": "cyan",
        "info": "dim",
    }.get(severity, "white")


# ── Text reporter ─────────────────────────────────────────────────────────────

def text_report(
    findings: list[Finding],
    files_scanned: int,
    *,
    no_color: bool = False,
    base_path: Path | None = None,
) -> None:
    """Print a human-readable report to stdout using rich."""
    from rich.console import Console
    from rich.text import Text

    console = Console(no_color=no_color, highlight=False)

    if not findings:
        console.print("[bold green]✓ No IAM policy violations found.[/bold green]")
        return

    # Group findings by file
    by_file: dict[Path, list[Finding]] = {}
    for finding in findings:
        by_file.setdefault(finding.file_path, []).append(finding)

    for file_path, file_findings in sorted(by_file.items(), key=lambda kv: str(kv[0])):
        rel = _rel_path(file_path, base_path)
        for f in file_findings:
            loc = f"{rel}:{f.line}" if f.line is not None else str(rel)
            sev = f.severity.value.upper()
            color = _severity_color(f.severity.value)
            line = Text()
            line.append(f"{loc}  ", style="bold")
            line.append(f"{sev}  ", style=color)
            line.append(f"{f.rule_id}  ", style="bold")
            line.append(f.message)
            console.print(line)

    # Summary
    by_severity: dict[str, int] = {s: 0 for s in _SEVERITY_ORDER}
    for f in findings:
        by_severity[f.severity.value] += 1

    parts = [f"{count} {sev}" for sev, count in by_severity.items() if count]
    summary = f"Found {len(findings)} finding(s) ({', '.join(parts)}) across {files_scanned} file(s)."
    console.print(f"\n[bold]{summary}[/bold]")


# ── JSON reporter ─────────────────────────────────────────────────────────────

def json_report(
    findings: list[Finding],
    files_scanned: int,
    *,
    base_path: Path | None = None,
) -> str:
    """Return a JSON string representing the findings report."""
    by_severity: dict[str, int] = {s: 0 for s in _SEVERITY_ORDER}
    for f in findings:
        by_severity[f.severity.value] += 1

    findings_list: list[dict[str, Any]] = []
    for f in sorted(findings, key=lambda x: (str(x.file_path), x.line or 0)):
        findings_list.append(
            {
                "rule_id": f.rule_id,
                "severity": f.severity.value,
                "message": f.message,
                "resource_type": f.resource_type,
                "resource_name": f.resource_name,
                "file": str(_rel_path(f.file_path, base_path)),
                "line": f.line,
                "extra": f.extra,
            }
        )

    output: dict[str, Any] = {
        "version": 1,
        "tool": {"name": "iamarmor", "version": __version__},
        "summary": {
            "total": len(findings),
            "by_severity": by_severity,
            "files_scanned": files_scanned,
        },
        "findings": findings_list,
    }
    return json.dumps(output, indent=2)


# ── helpers ───────────────────────────────────────────────────────────────────

def _rel_path(file_path: Path, base_path: Path | None) -> Path:
    """Return a path relative to *base_path* if possible, else return as-is."""
    if base_path is None:
        return file_path
    try:
        return file_path.relative_to(base_path)
    except ValueError:
        return file_path
