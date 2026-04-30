"""iamarmor — IAM Policy Analyzer & Fixer (core library)."""

from .exceptions import IamArmorError, ParseError, RuleLoadError, UnknownCheckError
from .parser import parse_directory, parse_file
from .resources import IamResource, extract_from_directory, extract_resources
from .rules import Finding, Rule, RuleEngine, Severity, load_default_rules, load_rules_from_yaml

__version__ = "0.0.2"

__all__ = [
    "__version__",
    "parse_file",
    "parse_directory",
    "extract_resources",
    "extract_from_directory",
    "IamResource",
    "IamArmorError",
    "ParseError",
    "RuleLoadError",
    "UnknownCheckError",
    "Rule",
    "Severity",
    "Finding",
    "RuleEngine",
    "load_default_rules",
    "load_rules_from_yaml",
]
