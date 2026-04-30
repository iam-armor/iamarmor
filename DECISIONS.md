# Architecture Decision Records

## 2026-04 — `python-hcl2` chosen for HCL parsing

**Status:** Accepted

**Context:**
The iamarmor engine needs to parse Terraform HCL2 files to extract IAM resource
definitions. Several approaches were considered.

**Decision:**
Use [`python-hcl2`](https://github.com/amplify-education/python-hcl2) (backed by the
[Lark](https://github.com/lark-parser/lark) parser) as the sole HCL parsing dependency.

**Rationale:**
- Mature library with wide adoption in the Terraform-tooling Python ecosystem.
- Returns plain Python dicts — no custom AST traversal required.
- Pure-Python install; no C extensions or CGo compilation needed.
- Actively maintained with releases tracking the HCL2 grammar.

**Alternatives rejected:**
- *Writing our own HCL2 parser* — significant scope creep; the grammar is non-trivial.
- *Calling HashiCorp's `hcl` library via FFI / subprocess* — adds a Go toolchain dependency,
  complicates packaging, and is harder to test in CI.
- *`pyhcl`* — targets the older HCL1 syntax; incompatible with modern Terraform configs.

## 2026-04 — YAML for rule definitions, Python for predicates

**Status:** Accepted

**Context:**
The rules engine needs a way to define rule metadata (ID, severity, message, description)
separately from the predicate logic that evaluates each rule.

**Decision:**
Rule metadata lives in YAML (`default_pack.yml`); predicate logic lives in typed Python
functions (`checks.py`). The `check:` field in each YAML entry binds the two via a
registry (`@register_check` decorator).

**Rationale:**
- YAML keeps rule metadata (id/severity/message) reviewable and diff-friendly — non-engineers
  can read and propose changes to rule descriptions or severities without touching Python.
- Predicate logic stays type-checked in Python; no need to invent a DSL or expression language.
- The `check:` field provides a clear, auditable seam between the two. Fail-fast validation
  at load time ensures no rule silently references an unregistered predicate.
- The pattern scales cleanly to premium packs in Phase 2 (private `iamarmor-app` repo) —
  they import the same engine, just supply additional YAML + Python predicates.

## 2026-04 — Resources with un-parseable `policy` expressions are skipped, not flagged

**Status:** Accepted

**Context:**
Terraform `policy` attributes can be set to dynamic expressions such as
`data.aws_iam_policy_document.foo.json` or `jsonencode({...})`. These cannot be
evaluated without running Terraform.

**Decision:**
When `policy_document` is `None` (i.e. `_try_parse_json` returned `None` because the
attribute was not a static JSON string), the rule predicates call `_iter_statements`
which returns nothing — the resource is silently skipped.

**Rationale:**
- Attempting to flag un-parseable resources would produce false positives on legitimate
  code that uses `aws_iam_policy_document` data sources (which we *can* analyse) or
  `jsonencode` (which we cannot).
- Users get full coverage by writing policies as `aws_iam_policy_document` data sources.
- The skip behaviour is documented in `STARTER_RULES.md` and in the rule descriptions
  in `default_pack.yml` so users understand the coverage boundary.
