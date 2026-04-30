"""Tests for the iamarmor RuleEngine."""

from __future__ import annotations

from pathlib import Path

import pytest

from iamarmor import IamResource, RuleEngine
from iamarmor.exceptions import UnknownCheckError
from iamarmor.rules import Finding, Rule, Severity

# Ensure checks are registered
import iamarmor.rules.checks  # noqa: F401

_DUMMY_PATH = Path("/dev/null/dummy.tf")


def _make_resource(resource_type: str = "aws_iam_policy", name: str = "r", attrs: dict | None = None) -> IamResource:
    return IamResource(resource_type=resource_type, name=name, file_path=_DUMMY_PATH, attributes=attrs or {})


def _simple_rule(check: str = "iam001_action_wildcard") -> Rule:
    return Rule(id="TEST001", name="test", severity=Severity.HIGH, message="msg", check=check)


class TestRuleEngineEmpty:
    def test_empty_rules_returns_empty(self):
        engine = RuleEngine(rules=[])
        result = engine.run([_make_resource()])
        assert result == []

    def test_empty_resources_returns_empty(self):
        engine = RuleEngine(rules=[_simple_rule()])
        result = engine.run([])
        assert result == []

    def test_both_empty_returns_empty(self):
        engine = RuleEngine(rules=[])
        result = engine.run([])
        assert result == []


class TestRuleEngineUnknownCheck:
    def test_raises_unknown_check_error(self):
        rule = Rule(id="X", name="x", severity=Severity.LOW, message="m", check="nonexistent_check_xyz")
        engine = RuleEngine(rules=[rule])
        with pytest.raises(UnknownCheckError):
            engine.run([_make_resource()])


class TestRuleEngineFindings:
    def test_finding_accumulates_across_resources(self):
        """Two resources each triggering the same rule → two findings."""
        wildcard_attrs = {
            "policy_document": {
                "Version": "2012-10-17",
                "Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}],
            }
        }
        r1 = _make_resource(attrs=wildcard_attrs, name="r1")
        r2 = _make_resource(attrs=wildcard_attrs, name="r2")
        engine = RuleEngine(rules=[_simple_rule("iam001_action_wildcard")])
        findings = engine.run([r1, r2])
        assert len(findings) == 2
        assert all(f.rule_id == "TEST001" for f in findings)

    def test_multiple_rules_accumulate(self):
        """Multiple rules each producing a finding → all collected."""
        wildcard_attrs = {
            "policy_document": {
                "Version": "2012-10-17",
                "Statement": [{"Effect": "Allow", "Action": ["*", "s3:*"], "Resource": "*"}],
            }
        }
        resource = _make_resource(attrs=wildcard_attrs)
        rule1 = Rule(id="A", name="a", severity=Severity.HIGH, message="m {resource} {stmt_index}", check="iam001_action_wildcard")
        rule2 = Rule(id="B", name="b", severity=Severity.HIGH, message="m {resource} {action} {stmt_index}", check="iam002_resource_wildcard_sensitive")
        engine = RuleEngine(rules=[rule1, rule2])
        findings = engine.run([resource])
        rule_ids = {f.rule_id for f in findings}
        assert "A" in rule_ids
        assert "B" in rule_ids

    def test_finding_fields_populated(self):
        attrs = {
            "policy_document": {
                "Version": "2012-10-17",
                "Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}],
            }
        }
        resource = _make_resource(attrs=attrs, name="mypolicy")
        rule = Rule(id="IAM001", name="n", severity=Severity.HIGH, message="hit {resource} {stmt_index}", check="iam001_action_wildcard")
        engine = RuleEngine(rules=[rule])
        findings = engine.run([resource])
        assert len(findings) == 1
        f: Finding = findings[0]
        assert f.rule_id == "IAM001"
        assert f.severity == Severity.HIGH
        assert f.resource_name == "mypolicy"
        assert f.resource_type == "aws_iam_policy"
        assert f.file_path == _DUMMY_PATH

    def test_no_violation_returns_empty(self):
        safe_attrs = {
            "policy_document": {
                "Version": "2012-10-17",
                "Statement": [{"Effect": "Allow", "Action": ["s3:GetObject"], "Resource": "arn:aws:s3:::b/*"}],
            }
        }
        resource = _make_resource(attrs=safe_attrs)
        engine = RuleEngine(rules=[_simple_rule("iam001_action_wildcard")])
        findings = engine.run([resource])
        assert findings == []

    def test_none_policy_document_skipped(self):
        """Resources with policy_document=None are silently skipped."""
        resource = _make_resource(attrs={"policy_document": None})
        engine = RuleEngine(rules=[_simple_rule("iam001_action_wildcard")])
        assert engine.run([resource]) == []
