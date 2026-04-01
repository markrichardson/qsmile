"""Bid/ask implied volatility option chain representation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    import matplotlib.figure

    from qsmile.smile_data import SmileData


@dataclass
class OptionChainVols:
    """Bid/ask implied volatility chain for a single expiry.

    Parameters
    ----------
    strikes : NDArray[np.float64]
        Strike prices. Must be positive.
    vol_bid : NDArray[np.float64]
        Bid implied volatilities. Must be non-negative.
    vol_ask : NDArray[np.float64]
        Ask implied volatilities. Must be non-negative and >= vol_bid.
    forward : float
        Forward price. Must be positive.
    discount_factor : float
        Discount factor. Must be positive.
    expiry : float
        Time to expiry in years. Must be positive.
    """

    strikes: NDArray[np.float64]
    vol_bid: NDArray[np.float64]
    vol_ask: NDArray[np.float64]
    forward: float
    discount_factor: float
    expiry: float

    def __post_init__(self) -> None:
        """Validate and convert inputs."""
        self.strikes = np.asarray(self.strikes, dtype=np.float64)
        self.vol_bid = np.asarray(self.vol_bid, dtype=np.float64)
        self.vol_ask = np.asarray(self.vol_ask, dtype=np.float64)

        n = len(self.strikes)
        if len(self.vol_bid) != n or len(self.vol_ask) != n:
            msg = (
                f"all arrays must have the same length as strikes ({n}), "
                f"got vol_bid={len(self.vol_bid)}, vol_ask={len(self.vol_ask)}"
            )
            raise ValueError(msg)
        if n < 3:
            msg = f"at least 3 strikes required, got {n}"
            raise ValueError(msg)
        if np.any(self.strikes <= 0):
            msg = "all strikes must be positive"
            raise ValueError(msg)
        if np.any(self.vol_bid < 0):
            msg = "vol_bid must be non-negative"
            raise ValueError(msg)
        if np.any(self.vol_ask < 0):
            msg = "vol_ask must be non-negative"
            raise ValueError(msg)
        if np.any(self.vol_bid > self.vol_ask):
            msg = "vol_bid must not exceed vol_ask"
            raise ValueError(msg)
        if self.forward <= 0:
            msg = f"forward must be positive, got {self.forward}"
            raise ValueError(msg)
        if self.discount_factor <= 0:
            msg = f"discount_factor must be positive, got {self.discount_factor}"
            raise ValueError(msg)
        if self.expiry <= 0:
            msg = f"expiry must be positive, got {self.expiry}"
            raise ValueError(msg)

    @property
    def vol_mid(self) -> NDArray[np.float64]:
        """Midpoint of bid and ask implied volatilities."""
        return (self.vol_bid + self.vol_ask) / 2.0

    @property
    def log_moneyness(self) -> NDArray[np.float64]:
        """Log-moneyness k = ln(K / F) for each strike."""
        return np.log(self.strikes / self.forward)

    @property
    def total_variance(self) -> NDArray[np.float64]:
        """Total implied variance w = vol_mid^2 * T for each observation."""
        return self.vol_mid**2 * self.expiry

    @property
    def sigma_atm(self) -> float:
        """Mid implied volatility at the strike closest to the forward."""
        atm_idx = int(np.argmin(np.abs(self.strikes - self.forward)))
        return float(self.vol_mid[atm_idx])

    def to_smile_data(self) -> SmileData:
        """Convert to a SmileData with (FixedStrike, Volatility) coordinates."""
        from qsmile.coords import XCoord, YCoord
        from qsmile.metadata import SmileMetadata
        from qsmile.smile_data import SmileData

        return SmileData(
            x=self.strikes.copy(),
            y_bid=self.vol_bid.copy(),
            y_ask=self.vol_ask.copy(),
            x_coord=XCoord.FixedStrike,
            y_coord=YCoord.Volatility,
            metadata=SmileMetadata(
                forward=self.forward,
                discount_factor=self.discount_factor,
                expiry=self.expiry,
                sigma_atm=self.sigma_atm,
            ),
        )

    @classmethod
    def from_mid_vols(
        cls,
        strikes: NDArray[np.float64],
        ivs: NDArray[np.float64],
        forward: float,
        expiry: float,
        discount_factor: float = 1.0,
    ) -> OptionChainVols:
        """Create from mid implied vols (setting bid = ask = ivs).

        Parameters
        ----------
        strikes : NDArray[np.float64]
            Strike prices.
        ivs : NDArray[np.float64]
            Mid implied volatilities.
        forward : float
            Forward price.
        expiry : float
            Time to expiry in years.
        discount_factor : float
            Discount factor, defaults to 1.0.
        """
        ivs = np.asarray(ivs, dtype=np.float64)
        return cls(
            strikes=strikes,
            vol_bid=ivs,
            vol_ask=ivs.copy(),
            forward=forward,
            discount_factor=discount_factor,
            expiry=expiry,
        )

    def plot(self, *, title: str = "Implied Volatilities") -> matplotlib.figure.Figure:
        """Plot bid/ask implied vols as error bars vs strike."""
        from qsmile.plot import plot_bid_ask

        return plot_bid_ask(
            self.strikes,
            self.vol_mid,
            self.vol_bid,
            self.vol_ask,
            xlabel="Strike",
            ylabel="Implied Volatility",
            title=title,
            label="IV",
        )
