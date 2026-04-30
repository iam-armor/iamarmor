"""Predicate registry for iamarmor rule checks."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Iterable

if TYPE_CHECKING:
    from iamarmor.resources import IamResource
    from iamarmor.rules import Finding, Rule

CheckFn = Callable[["Rule", "IamResource"], Iterable["Finding"]]

CHECKS: dict[str, CheckFn] = {}


def register_check(name: str) -> Callable[[CheckFn], CheckFn]:
    """Decorator that registers a predicate function under *name*."""

    def deco(fn: CheckFn) -> CheckFn:
        if name in CHECKS:
            raise ValueError(f"duplicate check registration: {name}")
        CHECKS[name] = fn
        return fn

    return deco
