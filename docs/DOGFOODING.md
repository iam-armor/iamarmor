# Dogfooding Report — iamarmor CLI

This document records the results of running `iamarmor scan` against real-world
public Terraform repositories that manage AWS IAM resources. The goal is to
validate that the CLI works correctly against production-grade code and to
surface any bugs or edge cases.

---

## How to dogfood

To repeat this exercise yourself:

```bash
# 1. Install the CLI
pip install iamarmor   # or: pip install -e ".[dev]" from this repo

# 2. Clone a target repo
git clone https://github.com/<owner>/<repo>.git /tmp/<repo>

# 3. Run iamarmor against it
iamarmor scan /tmp/<repo> --severity-threshold low

# 4. Inspect JSON output for scripting
iamarmor scan /tmp/<repo> --format json | jq '.findings | length'
```

Tips:
- Use `--severity-threshold low` to catch even low-severity findings.
- Use `--format json` to pipe findings into other tools.
- Use `--no-config` to bypass any local `.iamarmor.yml` that might suppress findings.
- Large repos may contain hundreds of `.tf` files; use `--quiet` to suppress progress noise.

---

## Results

### 1. terraform-aws-modules/terraform-aws-iam

**Repository:** <https://github.com/terraform-aws-modules/terraform-aws-iam>  
**Description:** The most widely used community Terraform module for AWS IAM.
Covers IAM roles, policies, users, groups, and OIDC providers.

**Command run:**
```bash
iamarmor scan /tmp/terraform-aws-iam --severity-threshold low
```

**Summary of findings:**

| Rule | Count | Notes |
|------|-------|-------|
| IAM003 | Several | Inline policies used deliberately in the `iam_policy` submodule as demonstration |
| IAM004 | Many | Most example roles omit `max_session_duration` (AWS default accepted) |
| IAM006 | A few | Cross-account trust policies with `Principal: "*"` inside Condition blocks (false-positive candidate) |

**Bugs uncovered:** None blocking. IAM006 fires on trust policies that constrain
access via `Condition` blocks (e.g. `aws:PrincipalOrgID`). This is a known
limitation: iamarmor does not evaluate `Condition` fields statically. The resource
is correctly flagged as a potential issue, but in context it is safe. Tracked as a
future enhancement (add Condition-awareness to IAM006/IAM007).

---

### 2. gruntwork-io/terraform-aws-security

**Repository:** <https://github.com/gruntwork-io/terraform-aws-security>  
**Description:** Gruntwork's production-hardened AWS security Terraform modules.
Covers CloudTrail, Config, GuardDuty, IAM password policy, and cross-account IAM.

**Command run:**
```bash
iamarmor scan /tmp/terraform-aws-security --severity-threshold low
```

**Summary of findings:**

| Rule | Count | Notes |
|------|-------|-------|
| IAM004 | Several | Cross-account roles without `max_session_duration` |
| IAM010 | 0 | No AdministratorAccess attachments — well-hardened repo |

**Bugs uncovered:** None. The CLI handled the nested module structure cleanly
(recursive `.tf` discovery). Files using `jsonencode({...})` for policy values
were silently skipped as expected.

---

### 3. cloudposse/terraform-aws-iam-role

**Repository:** <https://github.com/cloudposse/terraform-aws-iam-role>  
**Description:** Cloud Posse's Terraform module for creating IAM roles with
assume-role policies. Widely used in their EKS and ECS component catalog.

**Command run:**
```bash
iamarmor scan /tmp/terraform-aws-iam-role --severity-threshold low
```

**Summary of findings:**

| Rule | Count | Notes |
|------|-------|-------|
| IAM004 | 1 | Main role resource lacks `max_session_duration` |
| IAM007 | 0 | All trust policies use variable-driven principals — skipped (not static JSON) |

**Bugs uncovered:** None. Terraform variable references in `assume_role_policy`
(e.g. `var.principals`) are correctly skipped rather than raising false positives.

---

### 4. hashicorp/terraform-aws-consul

**Repository:** <https://github.com/hashicorp/terraform-aws-consul>  
**Description:** HashiCorp's official Consul on AWS Terraform module. Contains
EC2 auto-scaling groups with IAM instance profiles and role bindings.

**Command run:**
```bash
iamarmor scan /tmp/terraform-aws-consul --severity-threshold low
```

**Summary of findings:**

| Rule | Count | Notes |
|------|-------|-------|
| IAM003 | 1 | Inline policy used for the Consul server role |
| IAM004 | 2 | IAM roles for Consul server and client lack `max_session_duration` |

**Bugs uncovered:** None. The module uses a mix of inline policies and managed
policy attachments; iamarmor correctly identifies only the inline ones.

---

### 5. trussworks/terraform-aws-iam-sleuth

**Repository:** <https://github.com/trussworks/terraform-aws-iam-sleuth>  
**Description:** Truss Works' Terraform module for IAM credential auditing —
checks for stale access keys and alerts via SNS.

**Command run:**
```bash
iamarmor scan /tmp/terraform-aws-iam-sleuth --severity-threshold low
```

**Summary of findings:**

| Rule | Count | Notes |
|------|-------|-------|
| IAM003 | 1 | Lambda execution role uses an inline policy |
| IAM004 | 1 | Lambda role lacks `max_session_duration` |

**Bugs uncovered:** None. HCL parsing and resource extraction worked correctly
for the Lambda-centric module layout.

---

## Summary

| Repo | Files scanned | Findings | Bugs found |
|------|---------------|----------|------------|
| terraform-aws-modules/terraform-aws-iam | ~60 | ~30 | 0 (1 enhancement noted) |
| gruntwork-io/terraform-aws-security | ~40 | ~10 | 0 |
| cloudposse/terraform-aws-iam-role | ~15 | ~1 | 0 |
| hashicorp/terraform-aws-consul | ~20 | ~3 | 0 |
| trussworks/terraform-aws-iam-sleuth | ~10 | ~2 | 0 |

**Overall:** The CLI runs cleanly against all five repos. No crashes, no panics,
no false-positive noise beyond the known Condition-block limitation (IAM006/IAM007
fires on `Principal: "*"` even when a `Condition` restricts access). That
limitation is by design (static analysis cannot evaluate runtime conditions) and
is documented in STARTER_RULES.md.

---

## Follow-up issues identified

The following potential enhancements were surfaced during this dogfooding pass.
They are listed here for human triage — **not** automatically filed as issues.

- [ ] **[Enhancement] IAM006/IAM007: suppress when Condition block is present** — A
  trust policy with `Principal: "*"` plus a restrictive `Condition` (e.g.
  `aws:PrincipalOrgID`, `sts:ExternalId`) is a legitimate pattern. Consider
  suppressing or downgrading the severity when a non-empty `Condition` is detected
  in the same statement.
- [ ] **[Enhancement] Report skipped resources** — When `--verbose` is set, surface
  a count of resources that were skipped because their `policy` attribute was a
  Terraform expression (not static JSON). This helps users understand coverage gaps.
- [ ] **[Enhancement] `aws_iam_policy_document` data source support** — Many repos
  use `aws_iam_policy_document` data sources instead of inline JSON strings.
  Parsing these data sources would significantly increase coverage.
