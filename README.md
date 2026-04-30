# iamarmor
IAM Policy Analyzer & Fixer

## Status: Week 1 — core library

The core Python parsing library is live. It can parse Terraform `.tf` files, extract IAM resources, and expose a clean Python API. The CLI and rules engine are coming in subsequent weeks.

### Quick example

```python
from iamarmor import extract_from_directory, IamResource

resources = extract_from_directory("path/to/terraform/")
for r in resources:
    print(r.resource_type, r.name, r.file_path)
    if r.attributes.get("policy_document"):
        print("  parsed policy:", r.attributes["policy_document"])
```

### Installation (development)

```bash
pip install -e ".[dev]"
```

### Running tests

```bash
pytest
```
