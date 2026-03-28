"""Option chain market data model."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass
class OptionChain:
    """Validated container for single-expiry option chain market data.

    Parameters
    ----------
    strikes : ArrayLike
        Strike prices. Must be positive.
    ivs : ArrayLike
        Implied volatilities corresponding to each strike. Must be non-negative.
    forward : float
        Forward price of the underlying. Must be positive.
    expiry : float
        Time to expiration in years. Must be positive.
    """

    strikes: NDArray[np.float64]
    ivs: NDArray[np.float64]
    forward: float
    expiry: float

    def __post_init__(self) -> None:
        """Validate and convert inputs."""
        self.strikes = np.asarray(self.strikes, dtype=np.float64)
        self.ivs = np.asarray(self.ivs, dtype=np.float64)

        if len(self.strikes) != len(self.ivs):
            msg = f"strikes and ivs must have the same length, got {len(self.strikes)} and {len(self.ivs)}"
            raise ValueError(msg)
        if len(self.strikes) < 3:
            msg = f"at least 3 data points required, got {len(self.strikes)}"
            raise ValueError(msg)
        if self.forward <= 0:
            msg = f"forward must be positive, got {self.forward}"
            raise ValueError(msg)
        if self.expiry <= 0:
            msg = f"expiry must be positive, got {self.expiry}"
            raise ValueError(msg)
        if np.any(self.strikes <= 0):
            msg = "all strikes must be positive"
            raise ValueError(msg)
        if np.any(self.ivs < 0):
            msg = "implied volatilities must be non-negative"
            raise ValueError(msg)

    @property
    def log_moneyness(self) -> NDArray[np.float64]:
        """Log-moneyness k = ln(K / F) for each strike."""
        return np.log(self.strikes / self.forward)

    @property
    def total_variance(self) -> NDArray[np.float64]:
        """Total implied variance w = iv^2 * T for each observation."""
        return self.ivs**2 * self.expiry
