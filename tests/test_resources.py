"""Tests for iamarmor.resources."""

from pathlib import Path

import pytest

import iamarmor
from iamarmor import (
    IamArmorError,
    IamResource,
    ParseError,
    extract_from_directory,
    extract_resources,
    parse_file,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _extract(filename: str) -> list[IamResource]:
    """Helper: parse a fixture file and extract IAM resources."""
    path = FIXTURES / filename
    parsed = parse_file(path)
    return extract_resources(parsed, path)


class TestPublicApi:
    def test_version_is_set(self):
        assert iamarmor.__version__ == "0.0.1"

    def test_all_public_names_importable(self):
        from iamarmor import (  # noqa: F401
            IamArmorError,
            IamResource,
            ParseError,
            extract_from_directory,
            extract_resources,
            parse_directory,
            parse_file,
        )

    def test_iam_armor_error_is_base(self):
        assert issubclass(ParseError, IamArmorError)


class TestExtractSimplePolicy:
    def test_returns_one_resource(self):
        resources = _extract("simple_policy.tf")
        assert len(resources) == 1

    def test_resource_type_is_aws_iam_policy(self):
        resources = _extract("simple_policy.tf")
        assert resources[0].resource_type == "aws_iam_policy"

    def test_resource_name_is_example(self):
        resources = _extract("simple_policy.tf")
        assert resources[0].name == "example"

    def test_policy_document_is_parsed(self):
        resources = _extract("simple_policy.tf")
        doc = resources[0].attributes.get("policy_document")
        assert doc is not None
        assert doc["Version"] == "2012-10-17"

    def test_file_path_matches(self):
        path = FIXTURES / "simple_policy.tf"
        parsed = parse_file(path)
        resources = extract_resources(parsed, path)
        assert resources[0].file_path == path


class TestExtractRoleWithInlinePolicy:
    def test_returns_three_resources(self):
        resources = _extract("role_with_inline_policy.tf")
        # aws_iam_role + assume_role_policy (synthetic) + aws_iam_role_policy
        assert len(resources) == 3

    def test_resource_types_present(self):
        resources = _extract("role_with_inline_policy.tf")
        types = {r.resource_type for r in resources}
        assert "aws_iam_role" in types
        assert "aws_iam_role_policy" in types
        assert "assume_role_policy" in types

    def test_assume_role_policy_is_parsed(self):
        resources = _extract("role_with_inline_policy.tf")
        assume = next(r for r in resources if r.resource_type == "assume_role_policy")
        doc = assume.attributes.get("policy_document")
        assert doc is not None
        assert doc["Version"] == "2012-10-17"

    def test_inline_policy_document_is_parsed(self):
        resources = _extract("role_with_inline_policy.tf")
        inline = next(r for r in resources if r.resource_type == "aws_iam_role_policy")
        doc = inline.attributes.get("policy_document")
        assert doc is not None


class TestExtractAssumeRole:
    def test_returns_two_resources(self):
        resources = _extract("assume_role.tf")
        # aws_iam_role + assume_role_policy (synthetic)
        assert len(resources) == 2

    def test_role_resource_present(self):
        resources = _extract("assume_role.tf")
        types = {r.resource_type for r in resources}
        assert "aws_iam_role" in types
        assert "assume_role_policy" in types

    def test_jsonencode_policy_document_is_none(self):
        """jsonencode({...}) is not a JSON string — policy_document should be None."""
        resources = _extract("assume_role.tf")
        assume = next(r for r in resources if r.resource_type == "assume_role_policy")
        # jsonencode returns a dict/expression, not a plain JSON string
        assert assume.attributes.get("policy_document") is None


class TestExtractWildcardAction:
    def test_returns_one_resource(self):
        resources = _extract("wildcard_action.tf")
        assert len(resources) == 1

    def test_wildcard_in_action(self):
        resources = _extract("wildcard_action.tf")
        doc = resources[0].attributes.get("policy_document")
        assert doc is not None
        action = doc["Statement"][0]["Action"]
        assert "*" in action


class TestExtractPolicyDocumentData:
    def test_extracts_data_source(self):
        resources = _extract("policy_document_data.tf")
        assert len(resources) == 1

    def test_resource_type_is_policy_document(self):
        resources = _extract("policy_document_data.tf")
        assert resources[0].resource_type == "aws_iam_policy_document"

    def test_resource_name(self):
        resources = _extract("policy_document_data.tf")
        assert resources[0].name == "example"



    def test_returns_empty_list(self):
        resources = _extract("no_iam_resources.tf")
        assert resources == []


class TestExtractFromDirectory:
    def test_returns_list_of_iam_resources(self, tmp_path):
        import shutil

        shutil.copy(FIXTURES / "simple_policy.tf", tmp_path / "simple_policy.tf")
        shutil.copy(FIXTURES / "wildcard_action.tf", tmp_path / "wildcard_action.tf")

        resources = extract_from_directory(tmp_path)
        assert len(resources) >= 2
        assert all(isinstance(r, IamResource) for r in resources)

    def test_skips_dot_terraform(self, tmp_path):
        import shutil

        shutil.copy(FIXTURES / "simple_policy.tf", tmp_path / "simple_policy.tf")
        dot_terraform = tmp_path / ".terraform"
        dot_terraform.mkdir()
        shutil.copy(FIXTURES / "simple_policy.tf", dot_terraform / "should_skip.tf")

        resources = extract_from_directory(tmp_path)
        # Only the visible file should be processed
        assert all(str(r.file_path).find(".terraform") == -1 for r in resources)

    def test_accepts_string_path(self, tmp_path):
        import shutil

        shutil.copy(FIXTURES / "simple_policy.tf", tmp_path / "simple_policy.tf")
        resources = extract_from_directory(str(tmp_path))
        assert len(resources) >= 1

    def test_iam_resource_is_frozen(self):
        resources = _extract("simple_policy.tf")
        r = resources[0]
        with pytest.raises((AttributeError, TypeError)):
            r.name = "mutated"  # type: ignore[misc]
