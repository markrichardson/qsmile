"""Coordinate system enums for smile data."""

from __future__ import annotations

from enum import Enum


class XCoord(Enum):
    """X-coordinate (strike) representations."""

    FixedStrike = "fixed_strike"
    MoneynessStrike = "moneyness_strike"
    LogMoneynessStrike = "log_moneyness_strike"
    StandardisedStrike = "standardised_strike"


class YCoord(Enum):
    """Y-coordinate (value) representations."""

    Price = "price"
    Volatility = "volatility"
    Variance = "variance"
    TotalVariance = "total_variance"
