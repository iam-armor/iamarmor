# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] — Week 4 Polish

### Added

- **Polished README** rewritten for PyPI/Marketplace readiness: strong hero
  tagline ("ESLint for AWS IAM"), PyPI/CI/license badges, "Why iam-armor" pitch,
  extended Quickstart, example terminal output block, demo GIF placeholder with
  regeneration instructions, `.iamarmor.yml` config example, pre-commit hook
  snippet, GitHub Actions CI usage example, Roadmap section pointing at
  `iamarmor.dev`, Contributing and License sections.
- **`docs/demo.tape`** — runnable [VHS](https://github.com/charmbracelet/vhs)
  script that exercises `iamarmor lint` against `tests/fixtures/` and records
  `docs/demo.gif`. Regenerate with `vhs docs/demo.tape`.
- **`STARTER_RULES.md`** extended with ❌/✅ labelled examples and a
  "How to disable / configure" `.iamarmor.yml` snippet for every rule; premium
  rule-pack teaser added at the end.
- **`docs/DOGFOODING.md`** — dogfooding report against 5 real public Terraform
  repos (`terraform-aws-modules/terraform-aws-iam`,
  `gruntwork-io/terraform-aws-security`, `cloudposse/terraform-aws-iam-role`,
  `hashicorp/terraform-aws-consul`, `trussworks/terraform-aws-iam-sleuth`),
  including findings summaries and follow-up enhancement candidates.
- **`.github/workflows/ci.yml`** updated: pip cache enabled; matrix narrowed to
  Python 3.11 and 3.12; `pytest -q` (quieter output); separate `package` job
  added that runs `python -m build` and `twine check dist/*` on every push to
  confirm the wheel builds cleanly.

## [0.1.0] — 2026-04-30

### Added

- **`iamarmor lint` CLI** (`src/iamarmor/cli/main.py`) built with
  [Typer](https://typer.tiangolo.com/). Supports `--format text|json`,
  `--config`, `--no-config`, `--severity-threshold`, `--fail-on`,
  `--select`, `--ignore`, `--no-color`, `--verbose`, `--quiet`, `--version`.
- **`.iamarmor.yml` config loader** (`src/iamarmor/cli/config.py`) — auto-discovery
  walks upward from the linted path; hand-rolled YAML validator with clear error
  messages; supports `version`, `severity_threshold`, `fail_on`, `rules.select`,
  `rules.ignore`, `rules.overrides`, `paths.include`, `paths.exclude`.
- **Human-readable text reporter** — colorized via [Rich](https://rich.readthedocs.io/),
  grouped by file, with severity, rule ID, and summary footer.
- **Machine-readable JSON reporter** (`--format json`) — stable schema documented in
  `docs/json-output.md`; consumed by the future GitHub App handler.
- **Exit codes**: `0` clean, `1` findings at or above `--fail-on` threshold, `2`
  usage/config error, `3` internal error.
- **`ConfigError`** added to `iamarmor.exceptions` (subclass of `IamArmorError`).
- **`.pre-commit-hooks.yaml`** — plug-and-play pre-commit integration.
- **`.github/workflows/ci.yml`** — matrix CI on Python 3.10, 3.11, 3.12 with
  `ruff check` + `pytest --cov`.
- **`.github/workflows/publish.yml`** — PyPI publish via OIDC trusted publishing on
  `v*.*.*` tag push; no API tokens stored.
- **`typer >= 0.12`** and **`rich >= 13`** added as runtime dependencies.
- **`[project.scripts]`** entry point: `iamarmor = "iamarmor.cli.main:app"`.
- **`[project.urls] Changelog`** link added to `pyproject.toml`.
- **Test suite** extended to 140 tests: `test_cli.py`, `test_config.py`,
  `test_reporters.py`, plus updated version assertion in `test_resources.py`.
- **Docs**: `docs/config.md`, `docs/pre-commit.md`, `docs/json-output.md`,
  `docs/release.md`.
- **README** updated with Quickstart, Configuration, and Pre-commit sections.

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
