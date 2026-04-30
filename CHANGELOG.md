# Changelog

All notable changes to this project will be documented in this file.

## [0.0.2] — 2026-04-30

### Added

- **Rules engine** (`src/iamarmor/rules/`): YAML-driven, deterministic, stateless
  engine that runs a set of `Rule` objects against a list of `IamResource` objects
  and returns `Finding` violations.
- **Core types**: `Rule`, `Severity` (enum), `Finding` dataclasses in
  `iamarmor.rules.models`.
- **Predicate registry** (`iamarmor.rules.registry`): `@register_check` decorator
  and `CHECKS` dict for binding YAML rule definitions to Python predicate functions.
- **YAML loader** (`iamarmor.rules.loader`): `load_rules_from_yaml(path)` and
  `load_default_rules()` — uses `importlib.resources` to locate the bundled
  `default_pack.yml`; validates severity, required keys, and registered check names.
- **Default rule pack** (`src/iamarmor/rules/default_pack.yml`) — 10 foundational
  IAM rules:
  - IAM001 — No `Action: "*"`
  - IAM002 — No `Resource: "*"` with sensitive actions (`s3:*`, `iam:*`, `kms:*`, …)
  - IAM003 — No inline policies (`aws_iam_role_policy`, `aws_iam_user_policy`, `aws_iam_group_policy`)
  - IAM004 — IAM roles must set `max_session_duration`
  - IAM005 — No `iam:PassRole` with `Resource: "*"`
  - IAM006 — No wildcard `Principal` in resource-based policies
  - IAM007 — `assume_role_policy` must specify a concrete principal
  - IAM008 — No `NotAction` in Allow statements
  - IAM009 — No `NotResource` in Allow statements
  - IAM010 — Do not attach `AdministratorAccess` managed policy
- **New resource types** extracted by `resources.py`:
  `aws_iam_role_policy_attachment`, `aws_iam_user_policy_attachment`,
  `aws_iam_group_policy_attachment` (needed for IAM010).
- **New exceptions**: `RuleLoadError` (malformed YAML / unknown severity / unknown
  check) and `UnknownCheckError` (rule references a check not in the registry).
- **Test suite** extended to 95 tests: `test_engine.py`, `test_loader.py`,
  `test_default_rules.py`, new attachment cases in `test_resources.py`.
- **Per-rule fixtures**: `tests/fixtures/rules/IAMxxx_*/pass.tf` and `fail.tf`
  for all 10 rules.
- **`STARTER_RULES.md`**: full documentation for all 10 default rules with
  rationale, passing and failing examples.
- **`pyyaml >= 6.0`** added as runtime dependency.
- **`pyproject.toml`**: `[tool.hatch.build.targets.wheel]` section ensures
  `default_pack.yml` is included in the wheel.

## [Unreleased] (Week 1)

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
