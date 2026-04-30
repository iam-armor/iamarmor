class IamArmorError(Exception):
    """Base exception for iamarmor."""


class ParseError(IamArmorError):
    """Raised when a .tf file cannot be parsed."""


class RuleLoadError(IamArmorError):
    """Raised when a rules YAML file is malformed or references unknown checks."""


class UnknownCheckError(IamArmorError):
    """Raised when the engine encounters a rule whose check name is not registered."""
