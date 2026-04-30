"""Default predicate implementations for the iamarmor rule pack."""

from __future__ import annotations

import fnmatch
from typing import Iterable

from iamarmor.resources import IamResource
from iamarmor.rules.models import Finding, Rule
from iamarmor.rules.registry import register_check

# Sensitive service prefixes used by IAM002 / IAM005
_SENSITIVE_PREFIXES: list[str] = [
    "s3:*",
    "iam:*",
    "kms:*",
    "secretsmanager:*",
    "sts:*",
]


# ─── helpers ────────────────────────────────────────────────────────────────


def _iter_statements(resource: IamResource) -> Iterable[dict]:
    """Yield statement dicts from ``resource.attributes["policy_document"]``.

    Returns nothing if ``policy_document`` is ``None`` (un-parseable expression)
    — those resources are silently skipped to avoid false positives.
    """
    doc = resource.attributes.get("policy_document")
    if not isinstance(doc, dict):
        return

    raw_stmts = doc.get("Statement", [])
    if isinstance(raw_stmts, dict):
        raw_stmts = [raw_stmts]

    for stmt in raw_stmts:
        if isinstance(stmt, dict):
            yield stmt


def _normalize(value: object) -> list[str]:
    """Wrap a scalar string in a list; return lists as-is; ignore other types."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [v for v in value if isinstance(v, str)]
    return []


def _action_matches(action: str, patterns: list[str]) -> bool:
    """Return True if *action* matches any glob pattern in *patterns*."""
    action_lower = action.lower()
    for pattern in patterns:
        if fnmatch.fnmatchcase(action_lower, pattern.lower()):
            return True
    return False


def _make_finding(rule: Rule, resource: IamResource, message: str, **extra: object) -> Finding:
    return Finding(
        rule_id=rule.id,
        severity=rule.severity,
        message=message,
        resource_type=resource.resource_type,
        resource_name=resource.name,
        file_path=resource.file_path,
        line=resource.line,
        extra=dict(extra),
    )


# ─── IAM001: No Action: "*" ──────────────────────────────────────────────────


@register_check("iam001_action_wildcard")
def check_iam001(rule: Rule, resource: IamResource) -> Iterable[Finding]:
    for i, stmt in enumerate(_iter_statements(resource)):
        actions = _normalize(stmt.get("Action", []))
        if "*" in actions:
            yield _make_finding(
                rule,
                resource,
                rule.message.format(resource=resource.name, stmt_index=i),
                stmt_index=i,
            )


# ─── IAM002: No Resource: "*" with sensitive actions ─────────────────────────


@register_check("iam002_resource_wildcard_sensitive")
def check_iam002(rule: Rule, resource: IamResource) -> Iterable[Finding]:
    for i, stmt in enumerate(_iter_statements(resource)):
        resources_field = _normalize(stmt.get("Resource", []))
        if "*" not in resources_field:
            continue
        actions = _normalize(stmt.get("Action", []))
        for action in actions:
            if _action_matches(action, _SENSITIVE_PREFIXES):
                yield _make_finding(
                    rule,
                    resource,
                    rule.message.format(resource=resource.name, action=action, stmt_index=i),
                    stmt_index=i,
                    action=action,
                )
                break  # one finding per statement is enough


# ─── IAM003: No inline policies ──────────────────────────────────────────────

_INLINE_POLICY_TYPES = frozenset(
    {"aws_iam_role_policy", "aws_iam_user_policy", "aws_iam_group_policy"}
)


@register_check("iam003_no_inline_policies")
def check_iam003(rule: Rule, resource: IamResource) -> Iterable[Finding]:
    if resource.resource_type in _INLINE_POLICY_TYPES:
        yield _make_finding(
            rule,
            resource,
            rule.message.format(resource=resource.name, resource_type=resource.resource_type),
        )


# ─── IAM004: Role must set max_session_duration ───────────────────────────────


@register_check("iam004_role_max_session_duration")
def check_iam004(rule: Rule, resource: IamResource) -> Iterable[Finding]:
    if resource.resource_type != "aws_iam_role":
        return
    if "max_session_duration" not in resource.attributes:
        yield _make_finding(
            rule,
            resource,
            rule.message.format(resource=resource.name),
        )


# ─── IAM005: No iam:PassRole with Resource: "*" ───────────────────────────────

_PASSROLE_PATTERNS = ["iam:passrole", "iam:*"]


@register_check("iam005_passrole_resource_wildcard")
def check_iam005(rule: Rule, resource: IamResource) -> Iterable[Finding]:
    for i, stmt in enumerate(_iter_statements(resource)):
        resources_field = _normalize(stmt.get("Resource", []))
        if "*" not in resources_field:
            continue
        actions = _normalize(stmt.get("Action", []))
        for action in actions:
            if _action_matches(action, _PASSROLE_PATTERNS):
                yield _make_finding(
                    rule,
                    resource,
                    rule.message.format(resource=resource.name, action=action, stmt_index=i),
                    stmt_index=i,
                    action=action,
                )
                break


# ─── IAM006: No wildcard Principal in resource-based policies ─────────────────


def _principal_is_wildcard(principal: object) -> bool:
    """Return True if Principal is "*" or {"AWS": "*"}."""
    if principal == "*":
        return True
    if isinstance(principal, dict):
        for val in principal.values():
            if val == "*" or (isinstance(val, list) and "*" in val):
                return True
    return False


@register_check("iam006_principal_wildcard")
def check_iam006(rule: Rule, resource: IamResource) -> Iterable[Finding]:
    for i, stmt in enumerate(_iter_statements(resource)):
        principal = stmt.get("Principal")
        if principal is not None and _principal_is_wildcard(principal):
            yield _make_finding(
                rule,
                resource,
                rule.message.format(resource=resource.name, stmt_index=i),
                stmt_index=i,
            )


# ─── IAM007: assume_role_policy must specify a concrete principal ──────────────


@register_check("iam007_assume_role_concrete_principal")
def check_iam007(rule: Rule, resource: IamResource) -> Iterable[Finding]:
    if resource.resource_type != "assume_role_policy":
        return

    doc = resource.attributes.get("policy_document")
    if doc is None:
        # Can't evaluate — skip to avoid false positives
        return

    stmts = list(_iter_statements(resource))
    if not stmts:
        yield _make_finding(
            rule,
            resource,
            rule.message.format(resource=resource.name),
        )
        return

    for i, stmt in enumerate(stmts):
        principal = stmt.get("Principal")
        if principal is None or _principal_is_wildcard(principal):
            yield _make_finding(
                rule,
                resource,
                rule.message.format(resource=resource.name, stmt_index=i),
                stmt_index=i,
            )


# ─── IAM008: No NotAction in Allow statements ─────────────────────────────────


@register_check("iam008_not_action")
def check_iam008(rule: Rule, resource: IamResource) -> Iterable[Finding]:
    for i, stmt in enumerate(_iter_statements(resource)):
        effect = stmt.get("Effect", "Allow")
        if effect == "Allow" and "NotAction" in stmt:
            yield _make_finding(
                rule,
                resource,
                rule.message.format(resource=resource.name, stmt_index=i),
                stmt_index=i,
            )


# ─── IAM009: No NotResource in Allow statements ───────────────────────────────


@register_check("iam009_not_resource")
def check_iam009(rule: Rule, resource: IamResource) -> Iterable[Finding]:
    for i, stmt in enumerate(_iter_statements(resource)):
        effect = stmt.get("Effect", "Allow")
        if effect == "Allow" and "NotResource" in stmt:
            yield _make_finding(
                rule,
                resource,
                rule.message.format(resource=resource.name, stmt_index=i),
                stmt_index=i,
            )


# ─── IAM010: Do not attach AdministratorAccess managed policy ─────────────────

_ADMIN_POLICY_ARN = "arn:aws:iam::aws:policy/AdministratorAccess"

_ATTACHMENT_TYPES = frozenset(
    {
        "aws_iam_role_policy_attachment",
        "aws_iam_user_policy_attachment",
        "aws_iam_group_policy_attachment",
    }
)


@register_check("iam010_no_admin_managed_policy")
def check_iam010(rule: Rule, resource: IamResource) -> Iterable[Finding]:
    # Check policy_arn on attachment resources
    if resource.resource_type in _ATTACHMENT_TYPES:
        policy_arn = resource.attributes.get("policy_arn", "")
        if isinstance(policy_arn, str) and policy_arn.strip('"') == _ADMIN_POLICY_ARN:
            yield _make_finding(
                rule,
                resource,
                rule.message.format(resource=resource.name),
            )
        return

    # Check managed_policy_arns list on aws_iam_role
    if resource.resource_type == "aws_iam_role":
        arns = _normalize(resource.attributes.get("managed_policy_arns", []))
        for arn in arns:
            if arn.strip('"') == _ADMIN_POLICY_ARN:
                yield _make_finding(
                    rule,
                    resource,
                    rule.message.format(resource=resource.name),
                    arn=arn,
                )
                break
