"""Tests for iamarmor.parser."""

from pathlib import Path

import pytest

from iamarmor import ParseError, parse_directory, parse_file

FIXTURES = Path(__file__).parent / "fixtures"


class TestParseFile:
    def test_valid_file_returns_dict_with_resource_key(self):
        result = parse_file(FIXTURES / "simple_policy.tf")
        assert isinstance(result, dict)
        assert "resource" in result

    def test_valid_no_iam_file_returns_dict_with_resource_key(self):
        result = parse_file(FIXTURES / "no_iam_resources.tf")
        assert isinstance(result, dict)
        assert "resource" in result

    def test_invalid_hcl_raises_parse_error(self):
        with pytest.raises(ParseError) as exc_info:
            parse_file(FIXTURES / "invalid_hcl.tf")
        assert "invalid_hcl.tf" in str(exc_info.value)

    def test_parse_error_message_contains_file_path(self):
        bad = FIXTURES / "invalid_hcl.tf"
        with pytest.raises(ParseError) as exc_info:
            parse_file(bad)
        assert str(bad) in str(exc_info.value)

    def test_parse_error_chains_original_exception(self):
        with pytest.raises(ParseError) as exc_info:
            parse_file(FIXTURES / "invalid_hcl.tf")
        assert exc_info.value.__cause__ is not None


class TestParseDirectory:
    def test_returns_mapping_of_path_to_dict(self, tmp_path):
        import shutil

        for name in ("simple_policy.tf", "no_iam_resources.tf", "wildcard_action.tf"):
            shutil.copy(FIXTURES / name, tmp_path / name)

        result = parse_directory(tmp_path)
        assert isinstance(result, dict)
        for key, value in result.items():
            assert isinstance(key, Path)
            assert isinstance(value, dict)

    def test_finds_all_tf_files_except_invalid(self, tmp_path):
        # Copy valid fixtures only to a temp dir
        import shutil

        for name in ("simple_policy.tf", "no_iam_resources.tf", "wildcard_action.tf"):
            shutil.copy(FIXTURES / name, tmp_path / name)

        result = parse_directory(tmp_path)
        assert len(result) == 3

    def test_skips_dotterraform_directory(self, tmp_path):
        import shutil

        shutil.copy(FIXTURES / "simple_policy.tf", tmp_path / "simple_policy.tf")

        dot_terraform = tmp_path / ".terraform"
        dot_terraform.mkdir()
        shutil.copy(FIXTURES / "simple_policy.tf", dot_terraform / "hidden.tf")

        result = parse_directory(tmp_path)
        assert len(result) == 1
        assert all(".terraform" not in str(p) for p in result)

    def test_skips_any_hidden_directory(self, tmp_path):
        import shutil

        shutil.copy(FIXTURES / "simple_policy.tf", tmp_path / "visible.tf")

        hidden_dir = tmp_path / ".hidden"
        hidden_dir.mkdir()
        shutil.copy(FIXTURES / "simple_policy.tf", hidden_dir / "inside.tf")

        result = parse_directory(tmp_path)
        assert len(result) == 1

    def test_results_are_keyed_by_absolute_path(self, tmp_path):
        import shutil

        shutil.copy(FIXTURES / "simple_policy.tf", tmp_path / "simple_policy.tf")
        result = parse_directory(tmp_path)
        for p in result:
            assert p.is_absolute()
