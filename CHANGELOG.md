# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added

- Core Python library (`src/iamarmor/`) that parses Terraform `.tf` files via `python-hcl2`
  and extracts IAM resources (`aws_iam_policy`, `aws_iam_role`, `aws_iam_role_policy`,
  `aws_iam_user_policy`, `aws_iam_group_policy`, `aws_iam_policy_document` data sources).
- `IamResource` dataclass with `resource_type`, `name`, `file_path`, `attributes`, and
  optional `line` fields.
- Synthetic `assume_role_policy` resource extracted from every `aws_iam_role` block.
- Automatic JSON parsing of inline `policy` attributes into `attributes["policy_document"]`.
- `ParseError` (and base `IamArmorError`) custom exceptions with file-path context.
- `parse_file` / `parse_directory` public API for HCL parsing.
- `extract_resources` / `extract_from_directory` public API for IAM resource extraction.
- Test suite under `tests/` with fixtures covering valid policies, wildcard actions,
  role + inline policy combinations, malformed HCL, and non-IAM resources.
- `pyproject.toml` updated with `python-hcl2>=4.3` runtime dependency and `dev` extras
  (`pytest`, `pytest-cov`, `ruff`).
