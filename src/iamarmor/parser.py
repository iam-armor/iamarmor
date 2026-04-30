from __future__ import annotations

from pathlib import Path

import hcl2

from .exceptions import ParseError


def parse_file(path: str | Path) -> dict:
    """Parse a single Terraform .tf file via python-hcl2.

    Returns the raw parsed dict.
    Raises ParseError (wrapping the underlying exception) if the file is malformed.
    """
    path = Path(path)
    try:
        with path.open(encoding="utf-8") as fh:
            return hcl2.load(fh)
    except Exception as exc:
        raise ParseError(f"Failed to parse {path}: {exc}") from exc


def parse_directory(path: str | Path) -> dict[Path, dict]:
    """Recursively find all *.tf files under *path* and parse each one.

    Returns a mapping of absolute file path → parsed dict.
    Skips files inside hidden directories (e.g. .terraform/) and any directory
    whose name starts with '.'.
    """
    path = Path(path)
    result: dict[Path, dict] = {}
    for tf_file in sorted(path.rglob("*.tf")):
        # Skip files nested inside any hidden/vendored directory
        relative = tf_file.relative_to(path)
        if any(part.startswith(".") for part in relative.parts[:-1]):
            continue
        result[tf_file] = parse_file(tf_file)
    return result
