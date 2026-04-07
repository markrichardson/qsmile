"""Tests for DayCount enum."""

from __future__ import annotations

import pandas as pd

from qsmile.core.daycount import DayCount


class TestDayCount:
    """Tests for DayCount year_fraction."""

    def test_act365_full_year(self) -> None:
        start = pd.Timestamp("2024-01-01")
        end = pd.Timestamp("2025-01-01")
        result = DayCount.ACT365.year_fraction(start, end)
        assert result == 366 / 365.0  # 2024 is a leap year

    def test_act365_exact_365_days(self) -> None:
        pd.Timestamp("2023-01-01")
        pd.Timestamp("2023-12-31")  # 364 days
        # 365 days: Jan 1 to Jan 1 next year
        start2 = pd.Timestamp("2025-01-01")
        end2 = pd.Timestamp("2026-01-01")
        assert DayCount.ACT365.year_fraction(start2, end2) == 1.0

    def test_act360_exact_360_days(self) -> None:
        start = pd.Timestamp("2024-01-01")
        end = pd.Timestamp("2024-12-26")  # 360 days
        assert DayCount.ACT360.year_fraction(start, end) == 1.0

    def test_act365_fractional(self) -> None:
        start = pd.Timestamp("2024-01-01")
        end = pd.Timestamp("2024-04-01")  # 91 days
        assert DayCount.ACT365.year_fraction(start, end) == 91 / 365.0

    def test_act360_fractional(self) -> None:
        start = pd.Timestamp("2024-01-01")
        end = pd.Timestamp("2024-04-01")  # 91 days
        assert DayCount.ACT360.year_fraction(start, end) == 91 / 360.0

    def test_same_day(self) -> None:
        d = pd.Timestamp("2024-06-15")
        assert DayCount.ACT365.year_fraction(d, d) == 0.0
        assert DayCount.ACT360.year_fraction(d, d) == 0.0

    def test_enum_values(self) -> None:
        assert DayCount.ACT365.value == "ACT/365"
        assert DayCount.ACT360.value == "ACT/360"
