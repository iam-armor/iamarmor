# JSON Output Schema

The `--format json` flag emits a single JSON object to stdout. This schema
is **stable** and is the contract relied on by the future iamarmor GitHub App
(`iamarmor-app`).

## Schema

```json
{
  "version": 1,
  "tool": {
    "name": "iamarmor",
    "version": "0.1.1"
  },
  "summary": {
    "total": 3,
    "by_severity": {
      "info":     0,
      "low":      0,
      "medium":   2,
      "high":     1,
      "critical": 0
    },
    "files_scanned": 7
  },
  "findings": [
    {
      "rule_id":       "IAM001",
      "severity":      "high",
      "message":       "Action \"*\" is not allowed",
      "resource_type": "aws_iam_policy",
      "resource_name": "admin",
      "file":          "modules/iam/main.tf",
      "line":          42,
      "extra":         {}
    }
  ]
}
```

## Field reference

### Top level

| Field | Type | Description |
|-------|------|-------------|
| `version` | integer | Schema version. Always `1` for this release. |
| `tool` | object | Tool name and version that produced the report. |
| `summary` | object | Aggregated counts. |
| `findings` | array | List of individual violations. Empty array when clean. |

### `tool`

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Always `"iamarmor"`. |
| `version` | string | iamarmor version string (semver). |

### `summary`

| Field | Type | Description |
|-------|------|-------------|
| `total` | integer | Total number of findings after threshold filtering. |
| `by_severity` | object | Count per severity level. Keys: `info`, `low`, `medium`, `high`, `critical`. |
| `files_scanned` | integer | Number of `.tf` files examined. |

### `findings[]`

| Field | Type | Description |
|-------|------|-------------|
| `rule_id` | string | Rule identifier, e.g. `"IAM001"`. |
| `severity` | string | One of `info`, `low`, `medium`, `high`, `critical`. |
| `message` | string | Human-readable description of the violation. |
| `resource_type` | string | Terraform resource type, e.g. `"aws_iam_policy"`. |
| `resource_name` | string | Terraform resource name from the `.tf` file. |
| `file` | string | Repo-relative path to the offending file (CWD-relative if no config root found). |
| `line` | integer or null | Line number of the resource block, or `null` if unavailable. |
| `extra` | object | Rule-specific additional data. Schema varies by rule; may be empty. |

## Stability guarantee

- `version`, `tool`, `summary`, `findings` top-level keys will not be removed
  or renamed in minor/patch releases.
- New top-level keys may be added in minor releases.
- `findings[].rule_id`, `severity`, `message`, `resource_type`, `resource_name`,
  `file`, `line`, `extra` will not be removed or renamed in minor/patch releases.
- New keys inside `findings[]` may be added in minor releases.
- `extra` contents are rule-specific and are **not** covered by the stability guarantee.

## Example — consuming the output in CI

```bash
iamarmor lint . --format json > iamarmor-report.json
# Upload as a CI artifact, post to a GitHub Check, etc.
```
