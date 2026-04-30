# iamarmor
IAM Policy Analyzer & Fixer

## Status: Week 2 — rules engine + default rule pack

The core Python library is live with a YAML-driven rules engine and 10 default IAM
rules. Week 1 (HCL parser + IAM resource extractor) is already merged. The CLI
(`iamarmor lint`) is coming in Week 3.

### Quick example — extract resources and run the engine

```python
from iamarmor import extract_from_directory, RuleEngine, load_default_rules

resources = extract_from_directory("path/to/terraform/")
engine = RuleEngine(rules=load_default_rules())
findings = engine.run(resources)

for finding in findings:
    print(f"[{finding.rule_id}] {finding.severity.value.upper()} — {finding.message}")
```

### Default rule pack

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

See [STARTER_RULES.md](STARTER_RULES.md) for full documentation of each rule with
passing and failing examples.

### Installation (development)

```bash
pip install -e ".[dev]"
```

### Running tests

```bash
pytest
```
