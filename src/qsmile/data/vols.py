"""Unified smile data container with coordinate transforms."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
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
from qsmile.data.strikes import StrikeArray


@dataclass
class SmileData:
    """Coordinate-labelled smile data with bid/ask.

    Parameters
    ----------
    strikearray : StrikeArray
        Strike-indexed data containing at least ``y_bid`` and ``y_ask``
        columns.  Optional ``volume`` and ``open_interest`` columns are
        supported.
    x_coord : XCoord
        Which X-coordinate system the data is in.
    y_coord : YCoord
        Which Y-coordinate system the data is in.
    metadata : SmileMetadata
        Parameters needed by coordinate transforms.
    """

    strikearray: StrikeArray
    x_coord: XCoord
    y_coord: YCoord
    metadata: SmileMetadata

    def __post_init__(self) -> None:
        """Validate inputs."""
        sa = self.strikearray
        n = len(sa)

        if n < 3:
            msg = f"at least 3 data points required, got {n}"
            raise ValueError(msg)

        y_bid = sa.get_values(("y", "bid"))
        y_ask = sa.get_values(("y", "ask"))

        if y_bid is not None and y_ask is not None and np.any(y_bid > y_ask):
            msg = "y_bid must not exceed y_ask"
            raise ValueError(msg)

        x = sa.strikes
        if self.x_coord in (XCoord.FixedStrike, XCoord.MoneynessStrike) and np.any(x <= 0):
            msg = f"all x values must be positive for {self.x_coord.name}"
            raise ValueError(msg)

        if self.y_coord in (YCoord.Volatility, YCoord.Variance, YCoord.TotalVariance):
            for key in (("y", "bid"), ("y", "ask")):
                arr = sa.get_values(key)
                if arr is not None and np.any(arr < 0):
                    msg = f"y values must be non-negative for {self.y_coord.name}"
                    raise ValueError(msg)

        for key in (("meta", "volume"), ("meta", "open_interest")):
            arr = sa.get_values(key)
            if arr is not None and np.any(arr < 0):
                msg = f"{key[1]} must be non-negative"
                raise ValueError(msg)

    # ── convenience accessors ─────────────────────────────────────

    @property
    def x(self) -> NDArray[np.float64]:
        """X-coordinate values (strike axis)."""
        return self.strikearray.strikes

    @property
    def y_bid(self) -> NDArray[np.float64]:
        """Y-coordinate bid values."""
        return self.strikearray.values(("y", "bid"))

    @property
    def y_ask(self) -> NDArray[np.float64]:
        """Y-coordinate ask values."""
        return self.strikearray.values(("y", "ask"))

    @property
    def volume(self) -> NDArray[np.float64] | None:
        """Per-point traded volume, or None."""
        return self.strikearray.get_values(("meta", "volume"))

    @property
    def open_interest(self) -> NDArray[np.float64] | None:
        """Per-point open interest, or None."""
        return self.strikearray.get_values(("meta", "open_interest"))

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

        new_sa = StrikeArray()
        new_idx = pd.Index(new_x, dtype=np.float64)
        new_sa.set(("y", "bid"), pd.Series(new_y_bid, index=new_idx))
        new_sa.set(("y", "ask"), pd.Series(new_y_ask, index=new_idx))

        vol = self.volume
        if vol is not None:
            new_sa.set(("meta", "volume"), pd.Series(vol.copy(), index=new_idx))
        oi = self.open_interest
        if oi is not None:
            new_sa.set(("meta", "open_interest"), pd.Series(oi.copy(), index=new_idx))

        return SmileData(
            strikearray=new_sa,
            x_coord=target_x,
            y_coord=target_y,
            metadata=metadata,
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

        sa = StrikeArray()
        idx = pd.Index(strikes, dtype=np.float64)
        sa.set(("y", "bid"), pd.Series(ivs, index=idx))
        sa.set(("y", "ask"), pd.Series(ivs.copy(), index=idx))

        return cls(
            strikearray=sa,
            x_coord=XCoord.FixedStrike,
            y_coord=YCoord.Volatility,
            metadata=meta,
        )

    def plot(self, *, title: str = "Smile Data", ax=None, color="k", **kwargs) -> matplotlib.figure.Figure:
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
            fmt="none",
            color=color,
            ax=ax,
            **kwargs,
        )
