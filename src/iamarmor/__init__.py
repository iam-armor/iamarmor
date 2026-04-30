"""iamarmor — IAM Policy Analyzer & Fixer (core library)."""

from .exceptions import IamArmorError, ParseError
from .parser import parse_directory, parse_file
from .resources import IamResource, extract_from_directory, extract_resources

__version__ = "0.0.1"

__all__ = [
    "__version__",
    "parse_file",
    "parse_directory",
    "extract_resources",
    "extract_from_directory",
    "IamResource",
    "IamArmorError",
    "ParseError",
]
