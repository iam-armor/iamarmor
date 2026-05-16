"""Tests for iamarmor CLI — uses Typer's CliRunner."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from typer.testing import CliRunner

from iamarmor.cli.main import app

runner = CliRunner()

FIXTURES = Path(__file__).parent / "fixtures"
RULES = FIXTURES / "rules"
IAM001_FAIL = RULES / "IAM001_action_wildcard" / "fail.tf"
IAM001_PASS = RULES / "IAM001_action_wildcard" / "pass.tf"
IAM001_DIR = RULES / "IAM001_action_wildcard"


class TestScanBasic:
    def test_fail_tf_exits_1_and_shows_finding(self):
        result = runner.invoke(app, ["scan", str(IAM001_FAIL)])
        assert result.exit_code == 1
        assert "IAM001" in result.stdout

    def test_pass_tf_exits_0(self):
        result = runner.invoke(app, ["scan", str(IAM001_PASS)])
        assert result.exit_code == 0
        assert "No IAM policy violations found" in result.stdout

    def test_bad_path_exits_2(self):
        result = runner.invoke(app, ["scan", "/nonexistent/path/does/not/exist"])
        assert result.exit_code == 2

    def test_version_flag(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "0.1.1" in result.stdout

    def test_lint_command_is_removed(self):
        result = runner.invoke(app, ["lint", str(IAM001_PASS)])
        assert result.exit_code == 2
        assert "No such command 'lint'" in result.output


class TestScanJsonFormat:
    def test_json_output_valid_json(self):
        result = runner.invoke(app, ["scan", "--format", "json", str(IAM001_FAIL)])
        assert result.exit_code == 1
        data = json.loads(result.stdout)
        assert data["version"] == 1
        assert data["tool"]["name"] == "iamarmor"
        assert "summary" in data
        assert "findings" in data

    def test_json_output_schema_shape(self):
        result = runner.invoke(app, ["scan", "--format", "json", str(IAM001_FAIL)])
        data = json.loads(result.stdout)
        assert data["summary"]["total"] >= 1
        assert "by_severity" in data["summary"]
        assert "files_scanned" in data["summary"]
        # Check first finding shape
        finding = data["findings"][0]
        for key in ("rule_id", "severity", "message", "resource_type", "resource_name", "file", "extra"):
            assert key in finding, f"Missing key: {key}"

    def test_json_pass_exits_0_empty_findings(self):
        result = runner.invoke(app, ["scan", "--format", "json", str(IAM001_PASS)])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["summary"]["total"] == 0
        assert data["findings"] == []


class TestScanSelect:
    def test_select_runs_only_specified_rule(self):
        result = runner.invoke(app, ["scan", "--select", "IAM001", str(IAM001_FAIL)])
        assert result.exit_code == 1
        assert "IAM001" in result.stdout

    def test_select_nonmatching_rule_exits_0(self):
        result = runner.invoke(app, ["scan", "--select", "IAM002", str(IAM001_FAIL)])
        assert result.exit_code == 0

    def test_ignore_iam001_exits_0_on_fail_tf(self):
        result = runner.invoke(app, ["scan", "--ignore", "IAM001", str(IAM001_FAIL)])
        assert result.exit_code == 0


class TestScanSeverityAndFailOn:
    def test_severity_threshold_filters_out_lower(self):
        # IAM003 is medium severity. When threshold=high, medium findings are filtered out.
        # We use --select IAM003 to only run that rule so other high-sev rules don't trigger.
        iam003_fail = RULES / "IAM003_no_inline_policies" / "fail.tf"
        result = runner.invoke(
            app,
            ["scan", "--select", "IAM003", "--severity-threshold", "high", "--fail-on", "high",
             str(iam003_fail)],
        )
        # IAM003 is medium, so at threshold=high it should be filtered → exit 0
        assert result.exit_code == 0

    def test_fail_on_none_always_exits_0(self):
        result = runner.invoke(
            app, ["scan", "--fail-on", "none", str(IAM001_FAIL)]
        )
        assert result.exit_code == 0

    def test_fail_on_high_exits_1_for_high_finding(self):
        result = runner.invoke(
            app, ["scan", "--fail-on", "high", str(IAM001_FAIL)]
        )
        assert result.exit_code == 1

    def test_fail_on_critical_exits_0_for_high_finding(self):
        # IAM001 is HIGH, so fail-on critical should not trigger
        result = runner.invoke(
            app, ["scan", "--fail-on", "critical", str(IAM001_FAIL)]
        )
        assert result.exit_code == 0


class TestScanNoConfig:
    def test_no_config_ignores_bad_config(self, tmp_path):
        # Place a broken .iamarmor.yml next to the target file
        bad_cfg = tmp_path / ".iamarmor.yml"
        bad_cfg.write_text("version: 1\nfail_on: INVALID\n")
        # Copy pass.tf into tmp dir
        shutil.copy(IAM001_PASS, tmp_path / "pass.tf")
        result = runner.invoke(app, ["scan", "--no-config", str(tmp_path / "pass.tf")])
        assert result.exit_code == 0

    def test_malformed_config_exits_2(self, tmp_path):
        bad_cfg = tmp_path / ".iamarmor.yml"
        bad_cfg.write_text("version: 1\nfail_on: INVALID\n")
        shutil.copy(IAM001_PASS, tmp_path / "pass.tf")
        result = runner.invoke(app, ["scan", str(tmp_path / "pass.tf")])
        assert result.exit_code == 2

    def test_directory_scan(self):
        result = runner.invoke(app, ["scan", str(IAM001_DIR)])
        # Directory has both fail.tf and pass.tf, so we expect findings
        assert result.exit_code == 1
        assert "IAM001" in result.stdout
