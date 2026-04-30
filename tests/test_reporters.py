"""Tests for iamarmor CLI reporters."""

from __future__ import annotations

import json
from pathlib import Path


from iamarmor.cli.reporters import json_report, text_report
from iamarmor.rules.models import Finding, Severity

_DUMMY_PATH = Path("/tmp/modules/iam/main.tf")
_BASE_PATH = Path("/tmp")


def _make_finding(
    rule_id: str = "IAM001",
    severity: Severity = Severity.HIGH,
    message: str = 'Action "*" is not allowed',
    resource_type: str = "aws_iam_policy",
    resource_name: str = "admin",
    file_path: Path = _DUMMY_PATH,
    line: int | None = 42,
) -> Finding:
    return Finding(
        rule_id=rule_id,
        severity=severity,
        message=message,
        resource_type=resource_type,
        resource_name=resource_name,
        file_path=file_path,
        line=line,
    )


class TestJsonReporter:
    def test_json_schema_keys_present(self):
        findings = [_make_finding()]
        output = json_report(findings, files_scanned=7, base_path=_BASE_PATH)
        data = json.loads(output)
        assert data["version"] == 1
        assert data["tool"]["name"] == "iamarmor"
        assert "version" in data["tool"]
        assert "summary" in data
        assert "findings" in data

    def test_summary_counts_correct(self):
        findings = [
            _make_finding(severity=Severity.HIGH),
            _make_finding(severity=Severity.MEDIUM),
            _make_finding(severity=Severity.MEDIUM),
        ]
        output = json_report(findings, files_scanned=3)
        data = json.loads(output)
        assert data["summary"]["total"] == 3
        assert data["summary"]["by_severity"]["high"] == 1
        assert data["summary"]["by_severity"]["medium"] == 2
        assert data["summary"]["by_severity"]["low"] == 0
        assert data["summary"]["files_scanned"] == 3

    def test_finding_shape(self):
        findings = [_make_finding(line=42)]
        output = json_report(findings, files_scanned=1, base_path=_BASE_PATH)
        data = json.loads(output)
        f = data["findings"][0]
        assert f["rule_id"] == "IAM001"
        assert f["severity"] == "high"
        assert f["line"] == 42
        assert f["resource_type"] == "aws_iam_policy"
        assert f["resource_name"] == "admin"
        assert "file" in f
        assert "extra" in f

    def test_empty_findings_valid_json(self):
        output = json_report([], files_scanned=5)
        data = json.loads(output)
        assert data["summary"]["total"] == 0
        assert data["findings"] == []
        assert data["summary"]["files_scanned"] == 5

    def test_file_path_relative_to_base(self):
        findings = [_make_finding(file_path=_DUMMY_PATH)]
        output = json_report(findings, files_scanned=1, base_path=_BASE_PATH)
        data = json.loads(output)
        # Path should be relative: modules/iam/main.tf
        assert data["findings"][0]["file"] == "modules/iam/main.tf"

    def test_all_severity_keys_present_in_summary(self):
        output = json_report([], files_scanned=0)
        data = json.loads(output)
        for sev in ("info", "low", "medium", "high", "critical"):
            assert sev in data["summary"]["by_severity"]

    def test_json_is_stable_contract(self):
        """The JSON output schema must remain stable for downstream consumers."""
        findings = [_make_finding()]
        output = json_report(findings, files_scanned=1, base_path=_BASE_PATH)
        data = json.loads(output)
        # Top-level keys
        assert set(data.keys()) >= {"version", "tool", "summary", "findings"}
        # tool keys
        assert set(data["tool"].keys()) >= {"name", "version"}
        # summary keys
        assert set(data["summary"].keys()) >= {"total", "by_severity", "files_scanned"}


class TestTextReporter:
    def test_no_findings_prints_success(self, capsys):
        text_report([], files_scanned=3, no_color=True)
        captured = capsys.readouterr()
        assert "No IAM policy violations found" in captured.out

    def test_findings_printed_with_rule_id(self, capsys):
        findings = [_make_finding()]
        text_report(findings, files_scanned=1, no_color=True)
        captured = capsys.readouterr()
        assert "IAM001" in captured.out

    def test_findings_include_severity(self, capsys):
        findings = [_make_finding(severity=Severity.HIGH)]
        text_report(findings, files_scanned=1, no_color=True)
        captured = capsys.readouterr()
        assert "HIGH" in captured.out

    def test_summary_line_shows_count(self, capsys):
        findings = [_make_finding(), _make_finding(rule_id="IAM002")]
        text_report(findings, files_scanned=2, no_color=True)
        captured = capsys.readouterr()
        assert "2 finding" in captured.out

    def test_no_color_flag_respected(self, capsys):
        findings = [_make_finding()]
        # no_color=True means no ANSI escape codes
        text_report(findings, files_scanned=1, no_color=True)
        captured = capsys.readouterr()
        # If no_color works, we should NOT have ANSI escape sequences
        assert "\x1b[" not in captured.out
