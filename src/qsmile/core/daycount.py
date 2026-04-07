"""Day-count conventions for year-fraction computation."""

from __future__ import annotations

from enum import Enum

import pandas as pd


class DayCount(Enum):
    """Day-count convention for computing year fractions.

    Parameters
    ----------
    value : str
        Human-readable convention name.
    """

    ACT365 = "ACT/365"
    ACT360 = "ACT/360"

    def year_fraction(self, start: pd.Timestamp, end: pd.Timestamp) -> float:
        """Compute the year fraction between two dates.

        Parameters
        ----------
        start : pd.Timestamp
            Start date (valuation date).
        end : pd.Timestamp
            End date (expiry date).

        Returns:
        -------
        float
            Year fraction according to this convention.
        """
        days = (end - start).days
        match self:
            case DayCount.ACT365:
                return days / 365.0
            case DayCount.ACT360:
                return days / 360.0
