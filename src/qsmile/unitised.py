"""Unitised (normalised) volatility space representation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    import matplotlib.figure

    from qsmile.smile_data import SmileData
    from qsmile.vols import OptionChainVols


@dataclass
class UnitisedSpaceVols:
    """Smile in unitised coordinates.

    Coordinates:
        k_unitised = log(K/F) / (sigma_ATM * sqrt(T))
        variance_bid/ask = sigma_k^2 * T  (total variance)

    Parameters
    ----------
    k_unitised : NDArray[np.float64]
        Unitised log-moneyness.
    variance_bid : NDArray[np.float64]
        Total variance bid at each point.
    variance_ask : NDArray[np.float64]
        Total variance ask at each point.
    sigma_atm : float
        ATM implied volatility used for normalisation.
    expiry : float
        Time to expiry in years.
    """

    k_unitised: NDArray[np.float64]
    variance_bid: NDArray[np.float64]
    variance_ask: NDArray[np.float64]
    sigma_atm: float
    expiry: float

    def __post_init__(self) -> None:
        """Validate and convert inputs."""
        self.k_unitised = np.asarray(self.k_unitised, dtype=np.float64)
        self.variance_bid = np.asarray(self.variance_bid, dtype=np.float64)
        self.variance_ask = np.asarray(self.variance_ask, dtype=np.float64)

        n = len(self.k_unitised)
        if len(self.variance_bid) != n or len(self.variance_ask) != n:
            msg = f"all arrays must have the same length, got {n}, {len(self.variance_bid)}, {len(self.variance_ask)}"
            raise ValueError(msg)
        if np.any(self.variance_bid < 0):
            msg = "total variance bid must be non-negative"
            raise ValueError(msg)
        if np.any(self.variance_ask < 0):
            msg = "total variance ask must be non-negative"
            raise ValueError(msg)
        if np.any(self.variance_bid > self.variance_ask):
            msg = "variance bid must not exceed variance ask"
            raise ValueError(msg)
        if self.sigma_atm <= 0:
            msg = f"sigma_atm must be positive, got {self.sigma_atm}"
            raise ValueError(msg)
        if self.expiry <= 0:
            msg = f"expiry must be positive, got {self.expiry}"
            raise ValueError(msg)

    @property
    def variance_mid(self) -> NDArray[np.float64]:
        """Midpoint of bid and ask total variance."""
        return (self.variance_bid + self.variance_ask) / 2.0

    def to_vols(
        self,
        forward: float,
        strikes: NDArray[np.float64],
        discount_factor: float = 1.0,
    ) -> OptionChainVols:
        """Convert back to OptionChainVols by inverting the normalisation.

        Parameters
        ----------
        forward : float
            Forward price.
        strikes : NDArray[np.float64]
            Strike prices (absolute, not unitised).
        discount_factor : float
            Discount factor.
        """
        from qsmile.vols import OptionChainVols

        # Invert: v = sigma^2 * T → sigma = sqrt(v / T)
        vol_bid = np.sqrt(self.variance_bid / self.expiry)
        vol_ask = np.sqrt(self.variance_ask / self.expiry)

        return OptionChainVols(
            strikes=strikes,
            vol_bid=vol_bid,
            vol_ask=vol_ask,
            forward=forward,
            discount_factor=discount_factor,
            expiry=self.expiry,
        )

    def to_smile_data(self) -> SmileData:
        """Convert to a SmileData with (StandardisedStrike, TotalVariance) coordinates."""
        from qsmile.coords import XCoord, YCoord
        from qsmile.metadata import SmileMetadata
        from qsmile.smile_data import SmileData

        return SmileData(
            x=self.k_unitised.copy(),
            y_bid=self.variance_bid.copy(),
            y_ask=self.variance_ask.copy(),
            x_coord=XCoord.StandardisedStrike,
            y_coord=YCoord.TotalVariance,
            metadata=SmileMetadata(
                forward=1.0,  # Not available in unitised space; placeholder
                discount_factor=1.0,  # Not available in unitised space; placeholder
                expiry=self.expiry,
                sigma_atm=self.sigma_atm,
            ),
        )

    def plot(self, *, title: str = "Unitised Space Volatilities") -> matplotlib.figure.Figure:
        """Plot bid/ask total variance as error bars vs unitised log-moneyness."""
        from qsmile.plot import plot_bid_ask

        return plot_bid_ask(
            self.k_unitised,
            self.variance_mid,
            self.variance_bid,
            self.variance_ask,
            xlabel="Unitised Log-Moneyness",
            ylabel="Total Variance",
            title=title,
            label="Variance",
        )
