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

## 2026-04 — Typer chosen for the CLI

**Status:** Accepted

**Context:**
Week 3 required a polished CLI entry point for `iamarmor scan`. Both Click and
Typer were considered.

**Decision:**
Use [Typer](https://typer.tiangolo.com/) (`typer >= 0.12`) as the CLI framework.

**Rationale:**
- Type-hint-driven: option definitions are just function arguments with type
  annotations — less boilerplate, easier to read.
- Built on Click under the hood, so the ecosystem (testing via `CliRunner`,
  shell completion, integration with other Click apps) is fully compatible.
- Rich integration for `--no-color` and pretty help text.

**Trade-off:**
One extra runtime dependency (Typer + Rich). The noticeably nicer CLI surface
and reduced boilerplate justify this.

## 2026-05 — Use `scan` as the only CLI verb and drop third-party linter analogy

**Status:** Accepted

**Decision:**
Rename the CLI subcommand to `scan` and remove the old `lint` verb entirely, with
no alias. Update positioning copy to remove third-party linter references and
describe iamarmor directly as a static analyzer for Terraform IAM policies.

**Rationale:**
- The project has no active external users yet, so a clean break is cheaper than
  carrying a long-term alias.
- `scan` is clearer and more intuitive for security-focused workflows in CI and
  pre-commit pipelines.
- Avoiding third-party brand analogies reduces trademark risk and keeps product
  messaging independent.

## 2026-04 — Hand-rolled YAML config validator (no pydantic/jsonschema)

**Status:** Accepted

**Context:**
`.iamarmor.yml` needs validation. pydantic and jsonschema are common choices.

**Decision:**
Hand-roll the validator in `src/iamarmor/cli/config.py` using only `pyyaml`
(already a dep from Week 2).

**Rationale:**
- Schema is small (~6 top-level keys, shallow nesting) — a full schema library
  adds more weight than it removes.
- Error messages are tailored to users (mention the key name, the file path,
  and the expected values) rather than generic schema-violation text.
- Keeps the dependency footprint tight for a CLI tool.

**Revisit condition:**
If the config schema grows past ~8 keys with deep nesting, switch to pydantic v2.

## 2026-04 — PyPI Trusted Publishing (OIDC) over API tokens

**Status:** Accepted

**Context:**
The `publish.yml` GitHub Actions workflow needs to push packages to PyPI. The
traditional approach stores a PyPI API token as a GitHub secret.

**Decision:**
Use [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (OIDC)
so no long-lived credentials are stored in the repository.

**Rationale:**
- No secrets to rotate, leak, or revoke.
- Publishing permission is scoped to a specific workflow file + environment,
  not a project-wide token.
- PyPI supports OIDC from GitHub Actions natively via `pypa/gh-action-pypi-publish`.


## Week 4 — Polish + dogfood + content

**Status:** Accepted

**Context:**
Week 4 focused on polishing the OSS CLI for Marketplace/PyPI readiness without
adding new linter features.

**Decisions and outcomes:**
- README rewritten with hero tagline, badges, demo GIF placeholder, quickstart,
  config example, pre-commit/CI snippets, roadmap, and contributing guide.
- CI workflow updated: Python 3.11+3.12 matrix, pip cache, `pytest -q`; separate
  `package` job added (`python -m build` + `twine check`) to verify the wheel
  builds cleanly on every push.
- `STARTER_RULES.md` extended with ❌/✅ labelled examples and a "How to
  disable/configure" snippet for every rule — canonical OSS rule reference.
- `docs/demo.tape` added as a reproducible VHS recording script.
- Dogfooding pass run against 5 real public Terraform repos and documented in
  `docs/DOGFOODING.md`. No blocking bugs found; 3 follow-up enhancement
  candidates noted (Condition-awareness for IAM006/IAM007, verbose skip
  reporting, `aws_iam_policy_document` data-source analysis).

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
