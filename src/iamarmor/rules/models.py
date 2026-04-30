"""Core types for the iamarmor rules engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class Rule:
    """Definition of a single IAM rule."""

    id: str                         # e.g. "IAM001"
    name: str                       # short human title
    severity: Severity
    message: str                    # default human-readable message; may include {placeholders}
    check: str                      # name of the predicate registered in checks.py
    description: str = ""           # longer description / rationale
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class Finding:
    """A single violation found by a rule against a resource."""

    rule_id: str
    severity: Severity
    message: str
    resource_type: str
    resource_name: str
    file_path: Path
    line: int | None = None
    extra: dict = field(default_factory=dict)
