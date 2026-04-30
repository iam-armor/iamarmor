# `.iamarmor.yml` Configuration Reference

Place `.iamarmor.yml` in the root of your Terraform repository. iamarmor
auto-discovers it by walking upward from the path you lint (same pattern as
`.eslintrc` or `pyproject.toml`). You can also pass `--config <path>` to
point at a specific file, or `--no-config` to ignore any config entirely.

## Supported keys

```yaml
# .iamarmor.yml — full reference

version: 1                          # required; only version 1 is supported

severity_threshold: info            # optional — filter out findings below this level
                                    # values: info | low | medium | high | critical
                                    # default: info (report everything)

fail_on: medium                     # optional — exit 1 only when a finding is at or above this level
                                    # values: info | low | medium | high | critical | none
                                    # default: medium
                                    # use "none" to always exit 0 (useful for advisory-only runs)

rules:
  select: [IAM001, IAM002]          # optional — only run these rule IDs
                                    # mutually exclusive with `ignore`

  ignore: [IAM004]                  # optional — skip these rule IDs
                                    # mutually exclusive with `select`

  overrides:                        # optional — per-rule severity adjustments
    IAM004:
      severity: info                # override severity for this run only
                                    # values: info | low | medium | high | critical

paths:
  include:                          # optional — only scan files matching these globs
    - "**/*.tf"                     # default: all .tf files
  exclude:                          # optional — skip files matching these globs
    - "examples/**"
    - "**/.terraform/**"
```

## Key details

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `version` | integer | — (required) | Config schema version. Must be `1`. |
| `severity_threshold` | string | `info` | Minimum severity to report. |
| `fail_on` | string | `medium` | Minimum severity that triggers a non-zero exit code. |
| `rules.select` | list of strings | — | Allowlist of rule IDs to run. Mutually exclusive with `rules.ignore`. |
| `rules.ignore` | list of strings | — | Denylist of rule IDs to skip. Mutually exclusive with `rules.select`. |
| `rules.overrides` | mapping | — | Per-rule severity overrides for this run. |
| `paths.include` | list of globs | all `.tf` | File patterns to include. |
| `paths.exclude` | list of globs | `.terraform/**` | File patterns to exclude. |

## CLI flag precedence

CLI flags always override values from `.iamarmor.yml`:

```
--severity-threshold  >  severity_threshold in config
--fail-on             >  fail_on in config
--select              >  rules.select in config
--ignore              >  rules.ignore in config
```

## Example: CI-hardened config

```yaml
version: 1
fail_on: high          # only fail CI on high/critical findings
severity_threshold: low  # still report low findings for visibility

rules:
  ignore:
    - IAM004           # relax session-duration check for this repo
```

## Forward compatibility

Unknown top-level keys produce a warning to stderr but do **not** fail the
run. This lets you add keys supported by newer versions of iamarmor without
breaking older installs.
