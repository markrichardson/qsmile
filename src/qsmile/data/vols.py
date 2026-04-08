"""Unified smile data container with coordinate transforms."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    import matplotlib.figure

from qsmile.core.coords import XCoord, YCoord
from qsmile.core.maps import (
    apply_x_chain,
    apply_y_chain,
    compose_x_maps,
    compose_y_maps,
)
from qsmile.data.meta import SmileMetadata


@dataclass
class SmileData:
    """Coordinate-labelled smile data with bid/ask.

    Parameters
    ----------
    x : NDArray[np.float64]
        X-coordinate values.
    y_bid : NDArray[np.float64]
        Y-coordinate bid values.
    y_ask : NDArray[np.float64]
        Y-coordinate ask values.
    x_coord : XCoord
        Which X-coordinate system the data is in.
    y_coord : YCoord
        Which Y-coordinate system the data is in.
    metadata : SmileMetadata
        Parameters needed by coordinate transforms.
    """

    x: NDArray[np.float64]
    y_bid: NDArray[np.float64]
    y_ask: NDArray[np.float64]
    x_coord: XCoord
    y_coord: YCoord
    metadata: SmileMetadata
    volume: NDArray[np.float64] | None = field(default=None)
    open_interest: NDArray[np.float64] | None = field(default=None)

    def __post_init__(self) -> None:
        """Validate and convert inputs."""
        self.x = np.asarray(self.x, dtype=np.float64)
        self.y_bid = np.asarray(self.y_bid, dtype=np.float64)
        self.y_ask = np.asarray(self.y_ask, dtype=np.float64)

        n = len(self.x)
        if len(self.y_bid) != n or len(self.y_ask) != n:
            msg = (
                f"all arrays must have the same length as x ({n}), got y_bid={len(self.y_bid)}, y_ask={len(self.y_ask)}"
            )
            raise ValueError(msg)

        if n < 3:
            msg = f"at least 3 data points required, got {n}"
            raise ValueError(msg)

        if np.any(self.y_bid > self.y_ask):
            msg = "y_bid must not exceed y_ask"
            raise ValueError(msg)

        if self.x_coord in (XCoord.FixedStrike, XCoord.MoneynessStrike) and np.any(self.x <= 0):
            msg = f"all x values must be positive for {self.x_coord.name}"
            raise ValueError(msg)

        if self.y_coord in (YCoord.Volatility, YCoord.Variance, YCoord.TotalVariance) and (
            np.any(self.y_bid < 0) or np.any(self.y_ask < 0)
        ):
            msg = f"y values must be non-negative for {self.y_coord.name}"
            raise ValueError(msg)

        for attr in ("volume", "open_interest"):
            arr = getattr(self, attr)
            if arr is not None:
                arr = np.asarray(arr, dtype=np.float64)
                setattr(self, attr, arr)
                if len(arr) != n:
                    msg = f"{attr} must have the same length as x ({n}), got {len(arr)}"
                    raise ValueError(msg)
                if np.any(arr < 0):
                    msg = f"{attr} must be non-negative"
                    raise ValueError(msg)

    @property
    def y_mid(self) -> NDArray[np.float64]:
        """Midpoint of bid and ask Y values."""
        return (self.y_bid + self.y_ask) / 2.0

    def transform(self, target_x: XCoord, target_y: YCoord) -> SmileData:
        """Re-express data in target coordinate system.

        Parameters
        ----------
        target_x : XCoord
            Target X-coordinate system.
        target_y : YCoord
            Target Y-coordinate system.

        Returns:
        -------
        SmileData
            New SmileData in the target coordinates.
        """
        # Transform X
        x_chain = compose_x_maps(self.x_coord, target_x)
        new_x = apply_x_chain(self.x, x_chain, self.metadata)

        # Transform Y (bid and ask independently)
        y_chain = compose_y_maps(self.y_coord, target_y)
        new_y_bid = apply_y_chain(self.y_bid, self.x, y_chain, self.metadata, self.x_coord, target_x)
        new_y_ask = apply_y_chain(self.y_ask, self.x, y_chain, self.metadata, self.x_coord, target_x)

        # If we now have vols in FixedStrike and sigma_atm is missing, derive it
        metadata = self.metadata
        if target_y == YCoord.Volatility and target_x == XCoord.FixedStrike and metadata.sigma_atm is None:
            if metadata.forward is None:
                msg = "forward is required to derive sigma_atm"
                raise TypeError(msg)
            atm_idx = int(np.argmin(np.abs(new_x - metadata.forward)))
            sigma_atm = float((new_y_bid[atm_idx] + new_y_ask[atm_idx]) / 2.0)
            metadata = replace(metadata, sigma_atm=sigma_atm)

        return SmileData(
            x=new_x,
            y_bid=new_y_bid,
            y_ask=new_y_ask,
            x_coord=target_x,
            y_coord=target_y,
            metadata=metadata,
            volume=self.volume.copy() if self.volume is not None else None,
            open_interest=self.open_interest.copy() if self.open_interest is not None else None,
        )

    @classmethod
    def from_mid_vols(
        cls,
        strikes: NDArray[np.float64],
        ivs: NDArray[np.float64],
        metadata: SmileMetadata,
    ) -> SmileData:
        """Create from mid implied vols (setting y_bid = y_ask = ivs).

        Parameters
        ----------
        strikes : NDArray[np.float64]
            Strike prices.
        ivs : NDArray[np.float64]
            Mid implied volatilities.
        metadata : SmileMetadata
            Smile metadata. ``metadata.forward`` must not be ``None``.
            ``sigma_atm`` is always recomputed from the data.
        """
        strikes = np.asarray(strikes, dtype=np.float64)
        ivs = np.asarray(ivs, dtype=np.float64)

        if metadata.forward is None:
            msg = "metadata.forward must not be None"
            raise TypeError(msg)

        atm_idx = int(np.argmin(np.abs(strikes - metadata.forward)))
        sigma_atm = float(ivs[atm_idx])
        meta = replace(metadata, sigma_atm=sigma_atm)

        return cls(
            x=strikes,
            y_bid=ivs,
            y_ask=ivs.copy(),
            x_coord=XCoord.FixedStrike,
            y_coord=YCoord.Volatility,
            metadata=meta,
        )

    def plot(self, *, title: str = "Smile Data") -> matplotlib.figure.Figure:
        """Plot bid/ask Y-values as error bars vs X.

        Axis labels are derived from coordinate names.
        """
        from qsmile.core.plot import plot_bid_ask

        return plot_bid_ask(
            self.x,
            self.y_mid,
            self.y_bid,
            self.y_ask,
            xlabel=self.x_coord.name,
            ylabel=self.y_coord.name,
            title=title,
        )
