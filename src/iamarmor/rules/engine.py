"""Rule engine — runs a set of rules against a list of IamResource objects."""

from __future__ import annotations

from dataclasses import dataclass, field

from iamarmor.exceptions import UnknownCheckError
from iamarmor.resources import IamResource
from iamarmor.rules.models import Finding, Rule
from iamarmor.rules.registry import CHECKS


@dataclass
class RuleEngine:
    """Stateless, deterministic rules engine."""

    rules: list[Rule] = field(default_factory=list)

    def run(self, resources: list[IamResource]) -> list[Finding]:
        """Run all rules against *resources* and return every finding.

        Args:
            resources: IAM resources extracted from Terraform files.

        Returns:
            A flat list of :class:`Finding` objects; empty if no violations found.

        Raises:
            UnknownCheckError: If a rule references a check name not in the registry.
        """
        findings: list[Finding] = []
        for rule in self.rules:
            check = CHECKS.get(rule.check)
            if check is None:
                raise UnknownCheckError(
                    f"Rule {rule.id!r} references unknown check {rule.check!r}. "
                    "Is the checks module imported?"
                )
            for resource in resources:
                findings.extend(check(rule, resource))
        return findings
