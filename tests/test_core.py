"""Tests for qsmile.core."""

from __future__ import annotations

from qsmile.core import greet


def test_greet():
    """Verify greet returns expected greeting."""
    assert greet("World") == "Hello, World!"


def test_greet_empty():
    """Verify greet handles empty name."""
    assert greet("") == "Hello, !"
