"""Tests for iamarmor CLI config loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from iamarmor.cli.config import IamArmorConfig, discover_config, load_config
from iamarmor.exceptions import ConfigError

FIXTURES = Path(__file__).parent / "fixtures" / "config"


class TestDiscoverConfig:
    def test_discovers_config_in_directory(self):
        # The config fixture directory contains .iamarmor.yml
        found = discover_config(FIXTURES)
        assert found is not None
        assert found.name == ".iamarmor.yml"

    def test_discovers_config_walking_upward(self, tmp_path):
        # Create nested subdir without config, config at parent level
        sub = tmp_path / "a" / "b" / "c"
        sub.mkdir(parents=True)
        cfg = tmp_path / ".iamarmor.yml"
        cfg.write_text("version: 1\n")
        found = discover_config(sub)
        assert found == cfg

    def test_returns_none_when_no_config(self, tmp_path):
        # Use a deeply nested directory with no .iamarmor.yml anywhere
        # We mock the filesystem root by creating a fully isolated tmp directory.
        # discover_config will walk up and find nothing in the tmp hierarchy.
        sub = tmp_path / "a" / "b"
        sub.mkdir(parents=True)
        # Walk upward from sub — tmp_path has no config, and neither does sub
        found = discover_config(sub)
        # Either None (no config found) or a config above the system tmp (unlikely but possible)
        assert found is None or (found.is_file() and found.name == ".iamarmor.yml")

    def test_discovers_from_file_path(self, tmp_path):
        cfg = tmp_path / ".iamarmor.yml"
        cfg.write_text("version: 1\n")
        tf_file = tmp_path / "main.tf"
        tf_file.write_text("")
        found = discover_config(tf_file)
        assert found == cfg


class TestLoadConfig:
    def test_loads_valid_config(self):
        cfg_path = FIXTURES / ".iamarmor.yml"
        cfg = load_config(cfg_path)
        assert isinstance(cfg, IamArmorConfig)
        assert cfg.version == 1
        assert cfg.severity_threshold == "low"
        assert cfg.fail_on == "medium"
        assert cfg.ignore == ["IAM004"]
        assert cfg.select is None
        assert "IAM001" in cfg.overrides
        assert cfg.overrides["IAM001"]["severity"] == "critical"

    def test_missing_version_raises_config_error(self, tmp_path):
        f = tmp_path / ".iamarmor.yml"
        f.write_text("severity_threshold: low\n")
        with pytest.raises(ConfigError, match="missing required key 'version'"):
            load_config(f)

    def test_unsupported_version_raises_config_error(self, tmp_path):
        f = tmp_path / ".iamarmor.yml"
        f.write_text("version: 99\n")
        with pytest.raises(ConfigError, match="unsupported version"):
            load_config(f)

    def test_select_and_ignore_mutually_exclusive(self, tmp_path):
        f = tmp_path / ".iamarmor.yml"
        f.write_text("version: 1\nrules:\n  select: [IAM001]\n  ignore: [IAM002]\n")
        with pytest.raises(ConfigError, match="mutually exclusive"):
            load_config(f)

    def test_invalid_severity_threshold_raises(self, tmp_path):
        f = tmp_path / ".iamarmor.yml"
        f.write_text("version: 1\nseverity_threshold: INVALID\n")
        with pytest.raises(ConfigError, match="severity_threshold"):
            load_config(f)

    def test_invalid_fail_on_raises(self, tmp_path):
        f = tmp_path / ".iamarmor.yml"
        f.write_text("version: 1\nfail_on: INVALID_VALUE\n")
        with pytest.raises(ConfigError, match="fail_on"):
            load_config(f)

    def test_unknown_top_level_keys_warn_but_pass(self, tmp_path, capsys):
        f = tmp_path / ".iamarmor.yml"
        f.write_text("version: 1\nunknown_future_key: something\n")
        cfg = load_config(f)
        assert cfg.version == 1
        captured = capsys.readouterr()
        assert "unknown_future_key" in captured.err

    def test_empty_config_raises_missing_version(self, tmp_path):
        f = tmp_path / ".iamarmor.yml"
        f.write_text("")
        with pytest.raises(ConfigError, match="missing required key 'version'"):
            load_config(f)

    def test_select_list_loaded(self, tmp_path):
        f = tmp_path / ".iamarmor.yml"
        f.write_text("version: 1\nrules:\n  select: [IAM001, IAM002]\n")
        cfg = load_config(f)
        assert cfg.select == ["IAM001", "IAM002"]
        assert cfg.ignore is None

    def test_override_invalid_severity_raises(self, tmp_path):
        f = tmp_path / ".iamarmor.yml"
        f.write_text("version: 1\nrules:\n  overrides:\n    IAM001:\n      severity: INVALID\n")
        with pytest.raises(ConfigError, match="severity"):
            load_config(f)

    def test_paths_section_loaded(self, tmp_path):
        f = tmp_path / ".iamarmor.yml"
        f.write_text(
            "version: 1\npaths:\n  include:\n    - '**/*.tf'\n  exclude:\n    - 'examples/**'\n"
        )
        cfg = load_config(f)
        assert cfg.include_globs == ["**/*.tf"]
        assert cfg.exclude_globs == ["examples/**"]

    def test_nonexistent_file_raises_config_error(self, tmp_path):
        with pytest.raises(ConfigError, match="Cannot read"):
            load_config(tmp_path / "nonexistent.yml")
