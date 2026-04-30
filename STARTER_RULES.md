# Default Rule Pack — iamarmor Starter Rules

iamarmor ships with **10 foundational IAM rules** that catch the most common and
dangerous IAM misconfigurations in Terraform code. These rules are deterministic,
require no AWS credentials, and run entirely against static Terraform files.

Resources whose `policy` attribute is a Terraform expression (e.g.
`data.aws_iam_policy_document.foo.json`) cannot be evaluated statically and are
**silently skipped** to avoid false positives. Use `aws_iam_policy_document` data
sources for full coverage.

---

## IAM001 — No `Action: "*"`

| Field | Value |
|---|---|
| **ID** | IAM001 |
| **Severity** | High |
| **Targets** | All policy documents (managed, inline, assume-role, data sources) |

**Rationale:** A statement with `Action: "*"` grants every IAM action to the
principal. This is almost never intentional in production and is the single most
common overly-permissive IAM mistake. Always grant the minimum set of actions
actually required.

❌ **Bad example** (`tests/fixtures/rules/IAM001_action_wildcard/fail.tf`):
```hcl
resource "aws_iam_policy" "bad" {
  name   = "bad"
  policy = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":\"*\",\"Resource\":\"*\"}]}"
}
```

✅ **Good example** (`tests/fixtures/rules/IAM001_action_wildcard/pass.tf`):
```hcl
resource "aws_iam_policy" "example" {
  name   = "example"
  policy = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":[\"s3:GetObject\",\"s3:PutObject\"],\"Resource\":\"arn:aws:s3:::my-bucket/*\"}]}"
}
```

**How to disable / configure** via `.iamarmor.yml`:
```yaml
rules:
  ignore: [IAM001]          # disable entirely
  overrides:
    IAM001:
      severity: critical    # escalate to critical for stricter enforcement
```

---

## IAM002 — No `Resource: "*"` with sensitive actions

| Field | Value |
|---|---|
| **ID** | IAM002 |
| **Severity** | High |
| **Targets** | All policy documents |

**Rationale:** Combining a sensitive service action (`s3:*`, `iam:*`, `kms:*`,
`secretsmanager:*`, `sts:*`) with `Resource: "*"` grants unscoped access to every
resource in the account. Always constrain the Resource to specific ARNs.

❌ **Bad example** (`tests/fixtures/rules/IAM002_resource_wildcard_sensitive/fail.tf`):
```hcl
resource "aws_iam_policy" "bad" {
  name   = "bad"
  policy = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":[\"s3:*\"],\"Resource\":\"*\"}]}"
}
```

✅ **Good example** (`tests/fixtures/rules/IAM002_resource_wildcard_sensitive/pass.tf`):
```hcl
resource "aws_iam_policy" "example" {
  name   = "example"
  policy = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":[\"ec2:DescribeInstances\"],\"Resource\":\"*\"}]}"
}
```

**How to disable / configure** via `.iamarmor.yml`:
```yaml
rules:
  ignore: [IAM002]          # disable entirely
  overrides:
    IAM002:
      severity: critical    # escalate for environments with strict data-access controls
```

---

## IAM003 — No inline policies

| Field | Value |
|---|---|
| **ID** | IAM003 |
| **Severity** | Medium |
| **Targets** | `aws_iam_role_policy`, `aws_iam_user_policy`, `aws_iam_group_policy` |

**Rationale:** Inline policies are embedded directly on the principal. They are
harder to audit, cannot be reused across multiple principals, and are deleted when
the principal is deleted. Use `aws_iam_policy` + a policy attachment resource instead.

❌ **Bad example** (`tests/fixtures/rules/IAM003_no_inline_policies/fail.tf`):
```hcl
resource "aws_iam_role_policy" "bad" {
  name   = "bad-inline"
  role   = "my-role"
  policy = "{...}"
}
```

✅ **Good example** (`tests/fixtures/rules/IAM003_no_inline_policies/pass.tf`):
```hcl
resource "aws_iam_role_policy_attachment" "example" {
  role       = "my-role"
  policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
}
```

**How to disable / configure** via `.iamarmor.yml`:
```yaml
rules:
  ignore: [IAM003]          # disable if your org permits inline policies
```

---

## IAM004 — IAM roles must set `max_session_duration`

| Field | Value |
|---|---|
| **ID** | IAM004 |
| **Severity** | Low |
| **Targets** | `aws_iam_role` |

**Rationale:** Without an explicit `max_session_duration`, AWS defaults to 1 hour
for roles assumed via STS. Setting a shorter duration reduces the window in which
leaked credentials can be exploited. It is also a clear signal of intent in your
Terraform configuration.

❌ **Bad example** (`tests/fixtures/rules/IAM004_role_max_session_duration/fail.tf`):
```hcl
resource "aws_iam_role" "bad" {
  name               = "bad"
  assume_role_policy = "{...}"
}
```

✅ **Good example** (`tests/fixtures/rules/IAM004_role_max_session_duration/pass.tf`):
```hcl
resource "aws_iam_role" "example" {
  name                 = "example"
  max_session_duration = 3600
  assume_role_policy   = "{...}"
}
```

**How to disable / configure** via `.iamarmor.yml`:
```yaml
rules:
  ignore: [IAM004]          # disable if you accept AWS's default session duration
```

---

## IAM005 — No `iam:PassRole` with `Resource: "*"`

| Field | Value |
|---|---|
| **ID** | IAM005 |
| **Severity** | High |
| **Targets** | All policy documents |

**Rationale:** `iam:PassRole` with `Resource: "*"` effectively allows the principal
to pass any role in the account to any service, which is a well-known privilege
escalation vector. Always constrain `Resource` to the specific role ARNs that need
to be passed.

❌ **Bad example** (`tests/fixtures/rules/IAM005_passrole_resource_wildcard/fail.tf`):
```hcl
resource "aws_iam_policy" "bad" {
  name   = "bad"
  policy = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":[\"iam:PassRole\"],\"Resource\":\"*\"}]}"
}
```

✅ **Good example** (`tests/fixtures/rules/IAM005_passrole_resource_wildcard/pass.tf`):
```hcl
resource "aws_iam_policy" "example" {
  name   = "example"
  policy = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":[\"iam:PassRole\"],\"Resource\":\"arn:aws:iam::123456789012:role/my-specific-role\"}]}"
}
```

**How to disable / configure** via `.iamarmor.yml`:
```yaml
rules:
  ignore: [IAM005]          # disable if IAM005 produces false positives in your setup
  overrides:
    IAM005:
      severity: critical    # escalate for environments with strict privilege controls
```

---

## IAM006 — No wildcard `Principal` in resource-based policies

| Field | Value |
|---|---|
| **ID** | IAM006 |
| **Severity** | High |
| **Targets** | All policy documents |

**Rationale:** A wildcard `Principal` (`"*"` or `{"AWS": "*"}`) in a resource-based
policy grants access to any AWS identity — or even unauthenticated internet traffic
for some services. Always specify concrete principal ARNs.

❌ **Bad example** (`tests/fixtures/rules/IAM006_principal_wildcard/fail.tf`):
```hcl
resource "aws_iam_policy" "bad" {
  name   = "bad"
  policy = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":\"*\",\"Action\":\"sts:AssumeRole\",\"Resource\":\"*\"}]}"
}
```

✅ **Good example** (`tests/fixtures/rules/IAM006_principal_wildcard/pass.tf`):
```hcl
resource "aws_iam_policy" "example" {
  name   = "example"
  policy = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":{\"AWS\":\"arn:aws:iam::123456789012:root\"},\"Action\":\"sts:AssumeRole\",\"Resource\":\"*\"}]}"
}
```

**How to disable / configure** via `.iamarmor.yml`:
```yaml
rules:
  ignore: [IAM006]          # disable if you intentionally use public S3/SNS policies
```

---

## IAM007 — `assume_role_policy` must specify a concrete principal

| Field | Value |
|---|---|
| **ID** | IAM007 |
| **Severity** | High |
| **Targets** | Synthetic `assume_role_policy` resources extracted from `aws_iam_role` |

**Rationale:** An `assume_role_policy` without a concrete principal (or with
`Principal: "*"`) allows any identity to assume the role — a critical
misconfiguration. Always specify the exact services or account ARNs that should be
permitted to assume the role.

❌ **Bad example** (`tests/fixtures/rules/IAM007_assume_role_concrete_principal/fail.tf`):
```hcl
resource "aws_iam_role" "bad" {
  name                 = "bad"
  max_session_duration = 3600
  assume_role_policy   = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":\"*\",\"Action\":\"sts:AssumeRole\"}]}"
}
```

✅ **Good example** (`tests/fixtures/rules/IAM007_assume_role_concrete_principal/pass.tf`):
```hcl
resource "aws_iam_role" "example" {
  name                 = "example"
  max_session_duration = 3600
  assume_role_policy   = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":{\"Service\":\"lambda.amazonaws.com\"},\"Action\":\"sts:AssumeRole\"}]}"
}
```

**How to disable / configure** via `.iamarmor.yml`:
```yaml
rules:
  ignore: [IAM007]          # disable if your use case requires open trust policies
  overrides:
    IAM007:
      severity: critical    # escalate for production environments
```

---

## IAM008 — No `NotAction` in Allow statements

| Field | Value |
|---|---|
| **ID** | IAM008 |
| **Severity** | Medium |
| **Targets** | All policy documents |

**Rationale:** `NotAction` in an `Allow` statement grants every action *except*
those listed. This pattern is counterintuitive and often grants far more than
intended. Use explicit `Action` lists instead.

❌ **Bad example** (`tests/fixtures/rules/IAM008_not_action/fail.tf`):
```hcl
resource "aws_iam_policy" "bad" {
  name   = "bad"
  policy = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"NotAction\":[\"iam:*\"],\"Resource\":\"*\"}]}"
}
```

✅ **Good example** (`tests/fixtures/rules/IAM008_not_action/pass.tf`):
```hcl
resource "aws_iam_policy" "example" {
  name   = "example"
  policy = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":[\"s3:GetObject\"],\"Resource\":\"arn:aws:s3:::my-bucket/*\"}]}"
}
```

**How to disable / configure** via `.iamarmor.yml`:
```yaml
rules:
  ignore: [IAM008]          # disable if your org uses NotAction patterns deliberately
```

---

## IAM009 — No `NotResource` in Allow statements

| Field | Value |
|---|---|
| **ID** | IAM009 |
| **Severity** | Medium |
| **Targets** | All policy documents |

**Rationale:** `NotResource` in an `Allow` statement grants the action on every
resource *except* those listed. This pattern is error-prone and frequently exposes
unintended resources. Use explicit `Resource` ARNs instead.

❌ **Bad example** (`tests/fixtures/rules/IAM009_not_resource/fail.tf`):
```hcl
resource "aws_iam_policy" "bad" {
  name   = "bad"
  policy = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":[\"s3:GetObject\"],\"NotResource\":[\"arn:aws:s3:::protected-bucket/*\"]}]}"
}
```

✅ **Good example** (`tests/fixtures/rules/IAM009_not_resource/pass.tf`):
```hcl
resource "aws_iam_policy" "example" {
  name   = "example"
  policy = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":[\"s3:GetObject\"],\"Resource\":\"arn:aws:s3:::my-bucket/*\"}]}"
}
```

**How to disable / configure** via `.iamarmor.yml`:
```yaml
rules:
  ignore: [IAM009]          # disable if your policies use NotResource for deny patterns
```

---

## IAM010 — Do not attach `AdministratorAccess` managed policy

| Field | Value |
|---|---|
| **ID** | IAM010 |
| **Severity** | High |
| **Targets** | `aws_iam_role_policy_attachment`, `aws_iam_user_policy_attachment`, `aws_iam_group_policy_attachment`, `managed_policy_arns` on `aws_iam_role` |

**Rationale:** The AWS-managed `AdministratorAccess` policy grants full access to
all AWS services and resources. Attaching it violates the principle of least
privilege. Use a custom policy with only the permissions your workload actually needs.

❌ **Bad example** (`tests/fixtures/rules/IAM010_no_admin_managed_policy/fail.tf`):
```hcl
resource "aws_iam_role_policy_attachment" "bad" {
  role       = "my-role"
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}
```

✅ **Good example** (`tests/fixtures/rules/IAM010_no_admin_managed_policy/pass.tf`):
```hcl
resource "aws_iam_role_policy_attachment" "example" {
  role       = "my-role"
  policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
}
```

**How to disable / configure** via `.iamarmor.yml`:
```yaml
rules:
  ignore: [IAM010]          # disable if you intentionally use AdministratorAccess (not recommended)
  overrides:
    IAM010:
      severity: critical    # escalate for production environments
```

---

## Premium rule packs

The 10 rules above are the OSS default pack, freely available in this repository.

**Premium rule packs** — covering SOC 2, PCI-DSS, HIPAA, and the AWS
Well-Architected Security Pillar — are available via the hosted app at
**[iamarmor.dev](https://iamarmor.dev)** (coming soon). These packs extend
the default 10 rules with dozens of additional checks mapped to specific
compliance controls, and are not part of this OSS repository.
