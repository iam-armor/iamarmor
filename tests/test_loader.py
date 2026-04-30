"""Tests for the iamarmor rules loader."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from iamarmor.exceptions import RuleLoadError
from iamarmor.rules import Severity, load_default_rules, load_rules_from_yaml
from iamarmor.rules.registry import CHECKS

# Ensure all checks are registered before we run loader tests
import iamarmor.rules.checks  # noqa: F401


class TestLoadDefaultRules:
    def test_returns_ten_rules(self):
        rules = load_default_rules()
        assert len(rules) == 10

    def test_all_have_valid_severities(self):
        rules = load_default_rules()
        valid_severities = set(Severity)
        for rule in rules:
            assert rule.severity in valid_severities, f"{rule.id} has invalid severity {rule.severity}"

    def test_all_check_names_registered(self):
        rules = load_default_rules()
        for rule in rules:
            assert rule.check in CHECKS, f"{rule.id} references unregistered check {rule.check!r}"

    def test_rule_ids_are_unique(self):
        rules = load_default_rules()
        ids = [r.id for r in rules]
        assert len(ids) == len(set(ids)), "Duplicate rule IDs found"

    def test_iam001_through_iam010_present(self):
        rules = load_default_rules()
        ids = {r.id for r in rules}
        for n in range(1, 11):
            expected = f"IAM{n:03d}"
            assert expected in ids, f"{expected} not found in default pack"

    def test_all_rules_have_non_empty_message(self):
        rules = load_default_rules()
        for rule in rules:
            assert rule.message.strip(), f"{rule.id} has empty message"


class TestLoadRulesFromYaml:
    def test_valid_yaml_loads_rules(self, tmp_path: Path):
        yaml_content = textwrap.dedent("""\
            - id: TEST001
              name: Test rule
              severity: high
              message: "test message {resource} {stmt_index}"
              check: iam001_action_wildcard
        """)
        p = tmp_path / "rules.yml"
        p.write_text(yaml_content)
        rules = load_rules_from_yaml(p)
        assert len(rules) == 1
        assert rules[0].id == "TEST001"
        assert rules[0].severity == Severity.HIGH

    def test_tags_loaded(self, tmp_path: Path):
        yaml_content = textwrap.dedent("""\
            - id: TEST001
              name: Test rule
              severity: high
              message: "msg {resource} {stmt_index}"
              check: iam001_action_wildcard
              tags: [foo, bar]
        """)
        p = tmp_path / "rules.yml"
        p.write_text(yaml_content)
        rules = load_rules_from_yaml(p)
        assert rules[0].tags == ("foo", "bar")

    def test_description_loaded(self, tmp_path: Path):
        yaml_content = textwrap.dedent("""\
            - id: TEST001
              name: Test rule
              severity: medium
              message: "msg {resource} {stmt_index}"
              check: iam001_action_wildcard
              description: "Some description"
        """)
        p = tmp_path / "rules.yml"
        p.write_text(yaml_content)
        rules = load_rules_from_yaml(p)
        assert rules[0].description == "Some description"

    def test_malformed_yaml_raises_rule_load_error(self, tmp_path: Path):
        p = tmp_path / "bad.yml"
        p.write_text("key: [unclosed")
        with pytest.raises(RuleLoadError):
            load_rules_from_yaml(p)

    def test_non_list_yaml_raises_rule_load_error(self, tmp_path: Path):
        p = tmp_path / "bad.yml"
        p.write_text("key: value\n")
        with pytest.raises(RuleLoadError):
            load_rules_from_yaml(p)

    def test_missing_required_key_raises_rule_load_error(self, tmp_path: Path):
        yaml_content = textwrap.dedent("""\
            - id: TEST001
              name: Missing severity and message and check
        """)
        p = tmp_path / "bad.yml"
        p.write_text(yaml_content)
        with pytest.raises(RuleLoadError):
            load_rules_from_yaml(p)

    def test_unknown_severity_raises_rule_load_error(self, tmp_path: Path):
        yaml_content = textwrap.dedent("""\
            - id: TEST001
              name: Test
              severity: ultra-critical
              message: "msg {resource} {stmt_index}"
              check: iam001_action_wildcard
        """)
        p = tmp_path / "bad.yml"
        p.write_text(yaml_content)
        with pytest.raises(RuleLoadError, match="unknown severity"):
            load_rules_from_yaml(p)

    def test_unknown_check_raises_rule_load_error(self, tmp_path: Path):
        yaml_content = textwrap.dedent("""\
            - id: TEST001
              name: Test
              severity: high
              message: "msg {resource} {stmt_index}"
              check: nonexistent_check_that_does_not_exist
        """)
        p = tmp_path / "bad.yml"
        p.write_text(yaml_content)
        with pytest.raises(RuleLoadError, match="unknown check"):
            load_rules_from_yaml(p)

    def test_missing_file_raises_rule_load_error(self, tmp_path: Path):
        with pytest.raises(RuleLoadError):
            load_rules_from_yaml(tmp_path / "nonexistent.yml")
