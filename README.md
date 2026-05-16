# iamarmor

**A static analyzer for AWS IAM policies in Terraform — catch over-permissioned policies before they merge.**

[![PyPI version](https://img.shields.io/pypi/v/iamarmor.svg)](https://pypi.org/project/iamarmor/)
[![Python versions](https://img.shields.io/pypi/pyversions/iamarmor.svg)](https://pypi.org/project/iamarmor/)
[![CI](https://github.com/iam-armor/iamarmor/actions/workflows/ci.yml/badge.svg)](https://github.com/iam-armor/iamarmor/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## Why iam-armor?

IAM misconfigurations are the #1 cause of AWS breaches — wildcards on `Action` and
`Resource`, forgotten `AdministratorAccess` attachments, and overly-permissive
`assume_role_policy` are easy to ship and hard to spot in code review.

`iamarmor` is a **static analyzer for Terraform IAM resources**. It runs entirely
offline — no AWS credentials and no `terraform plan` required — and fits cleanly
into your workflow as a pre-commit hook or CI step.

```
$ iamarmor scan modules/iam/

  modules/iam/main.tf
  ✘ IAM001 [HIGH]   resource 'aws_iam_policy.app' has Action: "*" — grant least-privilege actions instead.
  ✘ IAM005 [HIGH]   resource 'aws_iam_policy.deployer' grants iam:PassRole on Resource: "*" — scope to specific role ARNs.
  ✘ IAM010 [HIGH]   resource 'aws_iam_role_policy_attachment.admin' attaches AdministratorAccess — grant only required permissions.

  3 findings  (3 high, 0 medium, 0 low)  in 0.12 s
  exit 1
```

---

## Demo

![iamarmor demo](docs/demo.gif)

> Regenerate with: `vhs docs/demo.tape`

---

## Quickstart

```bash
# Install (requires Python 3.11+)
pip install iamarmor

# Scan the current directory
iamarmor scan .

# Scan a specific file
iamarmor scan modules/iam/main.tf

# Machine-readable output for CI pipelines
iamarmor scan . --format json
```

`iamarmor scan` exits **0** when clean, **1** when findings meet the `fail_on`
threshold (default: `medium`), **2** on usage/config errors, and **3** on
internal errors — making CI integration trivial.

---

## Configuration

Place a `.iamarmor.yml` in the root of your Terraform repository:

```yaml
version: 1
severity_threshold: low   # report findings at or above this level (default: info)
fail_on: high             # exit 1 only for high/critical (default: medium)

rules:
  ignore: [IAM004]        # skip noisy rules for your environment
  overrides:
    IAM002:
      severity: critical  # escalate a rule's severity

paths:
  exclude:
    - "modules/legacy/**"  # skip paths you're not ready to fix yet
```

iamarmor auto-discovers `.iamarmor.yml` by walking upward from the target path.
Pass `--no-config` to skip loading.

See [docs/config.md](docs/config.md) for the full configuration reference.

---

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

See [STARTER_RULES.md](STARTER_RULES.md) for full documentation of each rule,
including rationale, examples, and configuration options.

---

## Pre-commit hook

Add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/iam-armor/iamarmor
    rev: v0.2.0

---

## GitHub Actions CI

Add to your workflow to scan Terraform in every PR:

```yaml
- name: Scan IAM policies
  run: |
    pip install iamarmor
    iamarmor scan . --fail-on high
```

Or pin a specific version:

```yaml
- name: Scan IAM policies
  run: |
    pip install iamarmor==0.2.0
    iamarmor scan modules/iam/ --format json > iam-findings.json
```

---

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

---

## Regenerating the demo GIF

The demo GIF was recorded with [VHS](https://github.com/charmbracelet/vhs).
To regenerate it:

```bash
# Install VHS (requires Go)
go install github.com/charmbracelet/vhs@latest

# Re-record
vhs docs/demo.tape
```

The resulting `docs/demo.gif` is committed to the repository. The tape script
exercises `iamarmor scan` against the bundled `tests/fixtures/` directory.

---

## Roadmap

`iamarmor` (this repo) is the OSS static analyzer engine. The hosted GitHub App at
**[iamarmor.dev](https://iamarmor.dev)** (coming soon) will add:

- 🔌 GitHub App with inline PR annotations
- 📦 Premium rule packs: SOC 2, PCI-DSS, HIPAA, AWS Well-Architected Security
- 📊 Findings dashboard and trend tracking
- 🔧 One-click auto-fix suggestions

---

## Contributing

Contributions are welcome! Please open an issue before submitting a PR for new
features or rules. See [STARTER_RULES.md](STARTER_RULES.md) for the existing
rule inventory and [docs/](docs/) for design docs.

```bash
git clone https://github.com/iam-armor/iamarmor.git
cd iamarmor
pip install -e ".[dev]"
pytest
ruff check src/ tests/
```

---

## License

[MIT](LICENSE) © 2026 iam-armor
