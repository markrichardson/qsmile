"""Unified smile data container with coordinate transforms."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike, NDArray

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
class VolData:
    """Coordinate-labelled smile data with bid/ask.

    Parameters
    ----------
    strikearray : StrikeArray
        Strike-indexed data containing at least ``y_bid`` and ``y_ask``
        columns.  Optional ``volume`` and ``open_interest`` columns are
        supported.
    current_x_coord : XCoord
        Which X-coordinate system the data is currently expressed in.
    current_y_coord : YCoord
        Which Y-coordinate system the data is currently expressed in.
    metadata : SmileMetadata
        Parameters needed by coordinate transforms.
    """

    strikearray: StrikeArray
    current_x_coord: XCoord
    current_y_coord: YCoord
    metadata: SmileMetadata
    _native_x_coord: XCoord = field(init=False, repr=False)
    _native_y_coord: YCoord = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Validate inputs and record native coordinates."""
        # Record native coords (first construction sets them)
        if not hasattr(self, "_native_set"):
            object.__setattr__(self, "_native_x_coord", self.current_x_coord)
            object.__setattr__(self, "_native_y_coord", self.current_y_coord)
            object.__setattr__(self, "_native_set", True)

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
        if self.current_x_coord in (XCoord.FixedStrike, XCoord.MoneynessStrike) and np.any(x <= 0):
            msg = f"all x values must be positive for {self.current_x_coord.name}"
            raise ValueError(msg)

        if self.current_y_coord in (YCoord.Volatility, YCoord.Variance, YCoord.TotalVariance):
            for key in (("y", "bid"), ("y", "ask")):
                arr = sa.get_values(key)
                if arr is not None and np.any(arr < 0):
                    msg = f"y values must be non-negative for {self.current_y_coord.name}"
                    raise ValueError(msg)

        for key in (("meta", "volume"), ("meta", "open_interest")):
            arr = sa.get_values(key)
            if arr is not None and np.any(arr < 0):
                msg = f"{key[1]} must be non-negative"
                raise ValueError(msg)

    # ── native coordinate properties ──────────────────────────────

    @property
    def native_x_coord(self) -> XCoord:
        """X-coordinate system the data was originally constructed in."""
        return self._native_x_coord

    @property
    def native_y_coord(self) -> YCoord:
        """Y-coordinate system the data was originally constructed in."""
        return self._native_y_coord

    # ── convenience accessors (lazy transform) ────────────────────

    def _is_native(self) -> bool:
        """True if current coords match native coords."""
        return self.current_x_coord == self._native_x_coord and self.current_y_coord == self._native_y_coord

    @property
    def x(self) -> NDArray[np.float64]:
        """X-coordinate values in current coordinate system."""
        native_x = self.strikearray.strikes
        if self._is_native():
            return native_x
        x_chain = compose_x_maps(self._native_x_coord, self.current_x_coord)
        return apply_x_chain(native_x, x_chain, self.metadata)

    @property
    def y_bid(self) -> NDArray[np.float64]:
        """Y-coordinate bid values in current coordinate system."""
        native_bid = self.strikearray.values(("y", "bid"))
        if self._is_native():
            return native_bid
        native_x = self.strikearray.strikes
        y_chain = compose_y_maps(self._native_y_coord, self.current_y_coord)
        return apply_y_chain(
            native_bid,
            native_x,
            y_chain,
            self.metadata,
            self._native_x_coord,
            self.current_x_coord,
        )

    @property
    def y_ask(self) -> NDArray[np.float64]:
        """Y-coordinate ask values in current coordinate system."""
        native_ask = self.strikearray.values(("y", "ask"))
        if self._is_native():
            return native_ask
        native_x = self.strikearray.strikes
        y_chain = compose_y_maps(self._native_y_coord, self.current_y_coord)
        return apply_y_chain(
            native_ask,
            native_x,
            y_chain,
            self.metadata,
            self._native_x_coord,
            self.current_x_coord,
        )

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
        """Midpoint of bid and ask Y values in current coordinate system."""
        return (self.y_bid + self.y_ask) / 2.0

    def transform(self, target_x: XCoord, target_y: YCoord) -> VolData:
        """Return a copy expressed in the target coordinate system.

        This is lightweight: it shares the same underlying StrikeArray
        and only updates the current coordinate labels. Property
        accessors apply transforms lazily on access.

        Parameters
        ----------
        target_x : XCoord
            Target X-coordinate system.
        target_y : YCoord
            Target Y-coordinate system.

        Returns:
        -------
        VolData
            New VolData in the target coordinates.
        """
        new = VolData.__new__(VolData)
        object.__setattr__(new, "strikearray", self.strikearray)
        object.__setattr__(new, "current_x_coord", target_x)
        object.__setattr__(new, "current_y_coord", target_y)
        object.__setattr__(new, "metadata", self.metadata)
        object.__setattr__(new, "_native_x_coord", self._native_x_coord)
        object.__setattr__(new, "_native_y_coord", self._native_y_coord)
        object.__setattr__(new, "_native_set", True)
        return new

    @classmethod
    def from_mid_vols(
        cls,
        strikes: NDArray[np.float64],
        ivs: NDArray[np.float64],
        metadata: SmileMetadata,
    ) -> VolData:
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
            current_x_coord=XCoord.FixedStrike,
            current_y_coord=YCoord.Volatility,
            metadata=meta,
        )

    def evaluate(self, x: ArrayLike) -> NDArray[np.float64]:
        """Interpolate mid-smile at arbitrary x in current coordinates.

        Uses cubic spline interpolation on ``y_mid``. Returns ``NaN``
        for points outside the data domain (no extrapolation).

        Parameters
        ----------
        x : ArrayLike
            X values in the current coordinate system.

        Returns:
        -------
        NDArray[np.float64]
            Interpolated mid Y values.
        """
        from scipy.interpolate import CubicSpline

        x_arr = np.asarray(x, dtype=np.float64)
        current_x = self.x
        current_y_mid = self.y_mid

        cs = CubicSpline(current_x, current_y_mid, extrapolate=False)
        return np.asarray(cs(x_arr), dtype=np.float64)

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
            xlabel=self.current_x_coord.name,
            ylabel=self.current_y_coord.name,
            title=title,
            fmt="none",
            color=color,
            ax=ax,
            **kwargs,
        )
