"""Smile metadata for coordinate transforms."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from qsmile.core.daycount import DayCount


@dataclass(frozen=True)
class SmileMetadata:
    """Parameters needed by coordinate transforms.

    Parameters
    ----------
    date : pd.Timestamp
        Valuation / pricing date.
    expiry : pd.Timestamp
        Expiry date. Must be strictly after ``date``.
    daycount : DayCount
        Day-count convention for computing the year fraction.
        Defaults to ``DayCount.ACT365``.
    forward : float | None
        Forward price. Must be positive when provided.
    discount_factor : float | None
        Discount factor. Must be positive when provided.
    sigma_atm : float | None
        ATM implied volatility. Must be positive when provided.
        Required for StandardisedStrike transforms.
    """

    date: pd.Timestamp
    expiry: pd.Timestamp
    daycount: DayCount = DayCount.ACT365
    forward: float | None = None
    discount_factor: float | None = None
    sigma_atm: float | None = None

    @property
    def texpiry(self) -> float:
        """Year fraction derived from (date, expiry, daycount)."""
        return self.daycount.year_fraction(self.date, self.expiry)

    def __post_init__(self) -> None:
        """Validate inputs."""
        if self.expiry <= self.date:
            msg = f"expiry must be after date, got date={self.date}, expiry={self.expiry}"
            raise ValueError(msg)
        if self.forward is not None and self.forward <= 0:
            msg = f"forward must be positive, got {self.forward}"
            raise ValueError(msg)
        if self.discount_factor is not None and self.discount_factor <= 0:
            msg = f"discount_factor must be positive, got {self.discount_factor}"
            raise ValueError(msg)
        if self.sigma_atm is not None and self.sigma_atm <= 0:
            msg = f"sigma_atm must be positive, got {self.sigma_atm}"
            raise ValueError(msg)
