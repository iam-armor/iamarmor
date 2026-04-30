from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .parser import parse_directory

# Terraform resource types that map to IAM constructs
_IAM_RESOURCE_TYPES: frozenset[str] = frozenset(
    {
        "aws_iam_policy",
        "aws_iam_role",
        "aws_iam_role_policy",
        "aws_iam_user_policy",
        "aws_iam_group_policy",
        "aws_iam_role_policy_attachment",
        "aws_iam_user_policy_attachment",
        "aws_iam_group_policy_attachment",
    }
)

# Attachment resource types that carry a policy_arn but no inline policy document
_IAM_ATTACHMENT_TYPES: frozenset[str] = frozenset(
    {
        "aws_iam_role_policy_attachment",
        "aws_iam_user_policy_attachment",
        "aws_iam_group_policy_attachment",
    }
)

# Terraform data source types that map to IAM constructs
_IAM_DATA_TYPES: frozenset[str] = frozenset({"aws_iam_policy_document"})


@dataclass(frozen=True)
class IamResource:
    """A single IAM-related resource extracted from a Terraform file."""

    resource_type: str  # e.g. "aws_iam_policy", "aws_iam_role", "assume_role_policy"
    name: str  # Terraform local label (e.g. "my_role")
    file_path: Path  # source .tf file
    attributes: dict = field(hash=False, compare=False)  # raw attribute block
    line: int | None = None  # best-effort line number (None if unavailable)


def _strip_hcl_quotes(s: str) -> str:
    """Strip surrounding double-quotes that python-hcl2 v8 preserves on identifiers."""
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        return s[1:-1]
    return s


def _try_parse_json(value: Any) -> Any:
    """Return a parsed JSON object from *value* if possible, else None.

    python-hcl2 v8 wraps HCL string literals in an extra layer of JSON encoding,
    so a plain JSON policy string requires two json.loads calls:
      1. Unwrap the outer HCL-string quoting → inner JSON string
      2. Parse the inner JSON string → Python dict
    """
    if not isinstance(value, str):
        return None
    try:
        result = json.loads(value)
        # If the first load returned a string (double-encoded), parse once more.
        if isinstance(result, str):
            result = json.loads(result)
        if isinstance(result, dict):
            return result
        return None
    except (json.JSONDecodeError, ValueError):
        return None


def _unwrap_attrs(attrs_raw: Any) -> dict:
    """Normalise the attribute block returned by python-hcl2.

    python-hcl2 may return either a dict or a list containing a single dict.
    Internal bookkeeping keys (prefixed with '__') are stripped.
    """
    if isinstance(attrs_raw, list):
        base = dict(attrs_raw[0]) if attrs_raw else {}
    else:
        base = dict(attrs_raw)
    # Remove internal hcl2 metadata keys
    return {k: v for k, v in base.items() if not (isinstance(k, str) and k.startswith("__"))}


def extract_resources(parsed: dict, file_path: Path) -> list[IamResource]:
    """Extract IAM resources from a single parsed Terraform file dict.

    Args:
        parsed:    The dict returned by parse_file().
        file_path: The path to the source .tf file (used for IamResource.file_path).

    Returns:
        A list of IamResource objects found in the file.
    """
    resources: list[IamResource] = []

    # ── regular resource blocks ─────────────────────────────────────────────
    for resource_block in parsed.get("resource", []):
        for raw_type, instances in resource_block.items():
            resource_type = _strip_hcl_quotes(raw_type)
            if resource_type not in _IAM_RESOURCE_TYPES:
                continue

            for raw_name, attrs_raw in instances.items():
                name = _strip_hcl_quotes(raw_name)
                resources.extend(_process_resource(resource_type, name, attrs_raw, file_path))

    # ── data source blocks ──────────────────────────────────────────────────
    for data_block in parsed.get("data", []):
        for raw_type, instances in data_block.items():
            data_type = _strip_hcl_quotes(raw_type)
            if data_type not in _IAM_DATA_TYPES:
                continue

            for raw_name, attrs_raw in instances.items():
                name = _strip_hcl_quotes(raw_name)
                attrs = _unwrap_attrs(attrs_raw)
                resources.append(
                    IamResource(resource_type=data_type, name=name, file_path=file_path, attributes=attrs)
                )

    return resources


def _process_resource(
    resource_type: str,
    name: str,
    attrs_raw: Any,
    file_path: Path,
) -> list[IamResource]:
    """Build IamResource(s) for a single Terraform resource block."""
    result: list[IamResource] = []
    attrs = _unwrap_attrs(attrs_raw)

    # Attempt to JSON-parse the inline policy attribute
    if "policy" in attrs:
        attrs["policy_document"] = _try_parse_json(attrs["policy"])

    result.append(
        IamResource(resource_type=resource_type, name=name, file_path=file_path, attributes=attrs)
    )

    # For aws_iam_role, surface assume_role_policy as a separate logical resource
    if resource_type == "aws_iam_role" and "assume_role_policy" in attrs:
        assume_attrs: dict = {
            "policy": attrs["assume_role_policy"],
            "policy_document": _try_parse_json(attrs["assume_role_policy"]),
        }
        result.append(
            IamResource(resource_type="assume_role_policy", name=name, file_path=file_path, attributes=assume_attrs)
        )

    return result


def extract_from_directory(path: str | Path) -> list[IamResource]:
    """Convenience wrapper: parse every .tf file under *path* and extract IAM resources.

    Args:
        path: Root directory to search recursively.

    Returns:
        A flat list of IamResource objects from all .tf files found.
    """
    path = Path(path)
    resources: list[IamResource] = []
    for file_path, parsed in parse_directory(path).items():
        resources.extend(extract_resources(parsed, file_path))
    return resources

