class IamArmorError(Exception):
    """Base exception for iamarmor."""


class ParseError(IamArmorError):
    """Raised when a .tf file cannot be parsed."""
