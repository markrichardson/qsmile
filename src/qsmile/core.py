"""Core qsmile functionality."""

from __future__ import annotations

from chebfun import Chebfun


def greet(name: str) -> str:
    """Return a greeting string."""
    return f"Hello, {name}!"


def approximate(func, domain=(-1, 1)):
    """Approximate a function using Chebyshev polynomials."""
    return Chebfun.from_function(func, domain=domain)
