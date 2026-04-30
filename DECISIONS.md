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
