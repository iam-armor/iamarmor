"""Parametrized tests for each of the 10 default IAM rules.

Each test loads the rule in isolation, then runs it against the rule's
pass.tf fixture (expecting zero findings) and its fail.tf fixture
(expecting ≥1 finding with the matching rule_id).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from iamarmor import RuleEngine, extract_from_directory, load_default_rules
from iamarmor.rules import Finding

FIXTURES_ROOT = Path(__file__).parent / "fixtures" / "rules"

# Map each rule ID to the fixture sub-directory name
_RULE_FIXTURES: list[tuple[str, str]] = [
    ("IAM001", "IAM001_action_wildcard"),
    ("IAM002", "IAM002_resource_wildcard_sensitive"),
    ("IAM003", "IAM003_no_inline_policies"),
    ("IAM004", "IAM004_role_max_session_duration"),
    ("IAM005", "IAM005_passrole_resource_wildcard"),
    ("IAM006", "IAM006_principal_wildcard"),
    ("IAM007", "IAM007_assume_role_concrete_principal"),
    ("IAM008", "IAM008_not_action"),
    ("IAM009", "IAM009_not_resource"),
    ("IAM010", "IAM010_no_admin_managed_policy"),
]


def _rule_engine_for(rule_id: str) -> RuleEngine:
    """Return a RuleEngine containing only the rule with *rule_id*."""
    all_rules = load_default_rules()
    rules = [r for r in all_rules if r.id == rule_id]
    assert rules, f"Rule {rule_id} not found in default pack"
    return RuleEngine(rules=rules)


def _findings_for_fixture(rule_id: str, fixture_dir: str, fixture_file: str) -> list[Finding]:
    path = FIXTURES_ROOT / fixture_dir / fixture_file
    assert path.exists(), f"Fixture not found: {path}"
    resources = extract_from_directory(path.parent)
    # Only keep resources from this specific fixture file
    resources = [r for r in resources if r.file_path == path]
    engine = _rule_engine_for(rule_id)
    return engine.run(resources)


@pytest.mark.parametrize("rule_id,fixture_dir", _RULE_FIXTURES)
class TestDefaultRulePassFixture:
    def test_pass_fixture_produces_zero_findings(self, rule_id: str, fixture_dir: str):
        findings = _findings_for_fixture(rule_id, fixture_dir, "pass.tf")
        violations = [f for f in findings if f.rule_id == rule_id]
        assert violations == [], (
            f"{rule_id} produced unexpected findings on pass.tf:\n"
            + "\n".join(f"  {f.message}" for f in violations)
        )


@pytest.mark.parametrize("rule_id,fixture_dir", _RULE_FIXTURES)
class TestDefaultRuleFailFixture:
    def test_fail_fixture_produces_at_least_one_finding(self, rule_id: str, fixture_dir: str):
        findings = _findings_for_fixture(rule_id, fixture_dir, "fail.tf")
        violations = [f for f in findings if f.rule_id == rule_id]
        assert len(violations) >= 1, (
            f"{rule_id} produced zero findings on fail.tf (expected ≥1)"
        )

    def test_fail_fixture_finding_has_correct_rule_id(self, rule_id: str, fixture_dir: str):
        findings = _findings_for_fixture(rule_id, fixture_dir, "fail.tf")
        for f in findings:
            if f.rule_id == rule_id:
                assert f.rule_id == rule_id
                return
        pytest.fail(f"No finding with rule_id={rule_id!r} in fail.tf findings")
