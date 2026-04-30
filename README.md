# iamarmor
IAM Policy Analyzer & Fixer

## Status: Week 3 — CLI + config + PyPI publish

The `iamarmor lint` CLI is live. Install from PyPI, point it at a Terraform
directory, and get actionable findings in seconds.

## Quickstart

```bash
# Install (requires Python 3.10+)
pipx install iamarmor

# Lint the current directory
iamarmor lint .

# Lint a specific file
iamarmor lint modules/iam/main.tf

# Machine-readable output for CI pipelines
iamarmor lint . --format json
```

`iamarmor lint` exits **0** when clean, **1** when findings meet the `fail_on`
threshold (default: `medium`), **2** on usage/config errors, and **3** on
internal errors — making CI integration trivial.

## Configuration

Place a `.iamarmor.yml` in the root of your Terraform repository:

```yaml
version: 1
severity_threshold: low   # report findings at or above this level (default: info)
fail_on: high             # exit 1 only for high/critical (default: medium)

rules:
  ignore: [IAM004]        # skip specific rules
```

iamarmor auto-discovers the config by walking upward from the linted path
(same pattern as `.eslintrc`). Use `--no-config` to skip loading.

See [docs/config.md](docs/config.md) for the full configuration reference.

## Pre-commit

Add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/iam-armor/iamarmor
    rev: v0.1.0
    hooks:
      - id: iamarmor
```

See [docs/pre-commit.md](docs/pre-commit.md) for details.

## Default rule pack

iamarmor ships with **10 default IAM rules** covering the most common misconfigurations:

| ID | Name | Severity |
|---|---|---|
| IAM001 | No `Action: "*"` | High |
| IAM002 | No `Resource: "*"` with sensitive actions | High |
| IAM003 | No inline policies | Medium |
| IAM004 | IAM roles must set `max_session_duration` | Low |
| IAM005 | No `iam:PassRole` with `Resource: "*"` | High |
| IAM006 | No wildcard `Principal` in resource-based policies | High |
| IAM007 | `assume_role_policy` must specify a concrete principal | High |
| IAM008 | No `NotAction` in Allow statements | Medium |
| IAM009 | No `NotResource` in Allow statements | Medium |
| IAM010 | Do not attach `AdministratorAccess` managed policy | High |

See [STARTER_RULES.md](STARTER_RULES.md) for full documentation of each rule.

## Python API

The CLI is the recommended entry point for most users. For embedding iamarmor
in other tools, the Python API is also public:

```python
from iamarmor import extract_from_directory, RuleEngine, load_default_rules

resources = extract_from_directory("path/to/terraform/")
engine = RuleEngine(rules=load_default_rules())
findings = engine.run(resources)

for finding in findings:
    print(f"[{finding.rule_id}] {finding.severity.value.upper()} — {finding.message}")
```

## Installation (development)

```bash
pip install -e ".[dev]"
```

## Running tests

```bash
pytest
```
