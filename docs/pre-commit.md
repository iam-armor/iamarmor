# Pre-commit Hook

iamarmor ships a [pre-commit](https://pre-commit.com/) hook that blocks
commits containing Terraform IAM policy violations.

## Setup

Add the following to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/iam-armor/iamarmor
    rev: v0.1.1          # pin to the latest release tag
    hooks:
      - id: iamarmor
```

Then install the hook:

```bash
pre-commit install
```

From now on, every `git commit` will automatically run
`iamarmor lint` against the repository root. Commits are blocked if any
finding is at or above the `fail_on` threshold (default: `medium`).

## Customisation

You can pass extra args to the hook:

```yaml
repos:
  - repo: https://github.com/iam-armor/iamarmor
    rev: v0.1.1
    hooks:
      - id: iamarmor
        args: ["--fail-on", "high", "--format", "text"]
```

Or use a `.iamarmor.yml` in the root of your repo — the hook picks it up
automatically (see [Configuration](config.md)).

## Running manually

```bash
pre-commit run iamarmor --all-files
```

## One-shot install (no pre-commit)

```bash
pipx install iamarmor
iamarmor lint .
```
