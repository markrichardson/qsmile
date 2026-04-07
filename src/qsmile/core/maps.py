"""Coordinate transform maps and composition."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from qsmile.core.coords import XCoord, YCoord

if TYPE_CHECKING:
    from qsmile.data.meta import SmileMetadata

# Type alias for map functions
# X-maps: (x_array, metadata) -> x_array
# Y-maps: (y_array, x_array, metadata) -> y_array
XMapFn = Callable[["NDArray[np.float64]", "SmileMetadata"], "NDArray[np.float64]"]
YMapFn = Callable[
    ["NDArray[np.float64]", "NDArray[np.float64]", "SmileMetadata"],
    "NDArray[np.float64]",
]

# Ordered ladders
X_LADDER: list[XCoord] = [
    XCoord.FixedStrike,
    XCoord.MoneynessStrike,
    XCoord.LogMoneynessStrike,
    XCoord.StandardisedStrike,
]

Y_LADDER: list[YCoord] = [
    YCoord.Price,
    YCoord.Volatility,
    YCoord.Variance,
    YCoord.TotalVariance,
]


# --- X-map functions ---


def _fixed_to_moneyness(x: NDArray[np.float64], meta: SmileMetadata) -> NDArray[np.float64]:
    if meta.forward is None:
        msg = "forward is required for FixedStrike to MoneynessStrike transform"
        raise TypeError(msg)
    return x / meta.forward


def _moneyness_to_fixed(x: NDArray[np.float64], meta: SmileMetadata) -> NDArray[np.float64]:
    if meta.forward is None:
        msg = "forward is required for MoneynessStrike to FixedStrike transform"
        raise TypeError(msg)
    return x * meta.forward


def _moneyness_to_log_moneyness(x: NDArray[np.float64], meta: SmileMetadata) -> NDArray[np.float64]:
    return np.log(x)


def _log_moneyness_to_moneyness(x: NDArray[np.float64], meta: SmileMetadata) -> NDArray[np.float64]:
    return np.exp(x)


def _log_moneyness_to_standardised(x: NDArray[np.float64], meta: SmileMetadata) -> NDArray[np.float64]:
    if meta.sigma_atm is None:
        msg = "sigma_atm is required for StandardisedStrike transforms"
        raise ValueError(msg)
    return x / (meta.sigma_atm * np.sqrt(meta.expiry))


def _standardised_to_log_moneyness(x: NDArray[np.float64], meta: SmileMetadata) -> NDArray[np.float64]:
    if meta.sigma_atm is None:
        msg = "sigma_atm is required for StandardisedStrike transforms"
        raise ValueError(msg)
    return x * meta.sigma_atm * np.sqrt(meta.expiry)


# --- Y-map functions ---


def _vol_to_variance(y: NDArray[np.float64], x: NDArray[np.float64], meta: SmileMetadata) -> NDArray[np.float64]:
    return y**2


def _variance_to_vol(y: NDArray[np.float64], x: NDArray[np.float64], meta: SmileMetadata) -> NDArray[np.float64]:
    return np.sqrt(y)


def _variance_to_total_variance(
    y: NDArray[np.float64], x: NDArray[np.float64], meta: SmileMetadata
) -> NDArray[np.float64]:
    return y * meta.expiry


def _total_variance_to_variance(
    y: NDArray[np.float64], x: NDArray[np.float64], meta: SmileMetadata
) -> NDArray[np.float64]:
    return y / meta.expiry


def _vol_to_price(y: NDArray[np.float64], x: NDArray[np.float64], meta: SmileMetadata) -> NDArray[np.float64]:
    """Convert implied volatilities to Black76 call prices.

    x must be in FixedStrike coordinates (absolute strikes).
    """
    from qsmile.core.black76 import black76_call

    if meta.forward is None or meta.discount_factor is None:
        msg = "forward and discount_factor are required for vol-to-price transform"
        raise TypeError(msg)
    return np.asarray(
        black76_call(meta.forward, x, meta.discount_factor, y, meta.expiry),
        dtype=np.float64,
    )


def _price_to_vol(y: NDArray[np.float64], x: NDArray[np.float64], meta: SmileMetadata) -> NDArray[np.float64]:
    """Convert Black76 call prices to implied volatilities.

    x must be in FixedStrike coordinates (absolute strikes).
    """
    from qsmile.core.black76 import black76_implied_vol

    if meta.forward is None or meta.discount_factor is None:
        msg = "forward and discount_factor are required for price-to-vol transform"
        raise TypeError(msg)
    n = len(y)
    result = np.empty(n, dtype=np.float64)
    for i in range(n):
        result[i] = black76_implied_vol(
            float(y[i]),
            meta.forward,
            float(x[i]),
            meta.discount_factor,
            meta.expiry,
            is_call=True,
        )
    return result


# --- Registries ---

# X-map registry: (source, target) -> map function
_X_MAPS: dict[tuple[XCoord, XCoord], XMapFn] = {
    (XCoord.FixedStrike, XCoord.MoneynessStrike): _fixed_to_moneyness,
    (XCoord.MoneynessStrike, XCoord.FixedStrike): _moneyness_to_fixed,
    (XCoord.MoneynessStrike, XCoord.LogMoneynessStrike): _moneyness_to_log_moneyness,
    (XCoord.LogMoneynessStrike, XCoord.MoneynessStrike): _log_moneyness_to_moneyness,
    (XCoord.LogMoneynessStrike, XCoord.StandardisedStrike): _log_moneyness_to_standardised,
    (XCoord.StandardisedStrike, XCoord.LogMoneynessStrike): _standardised_to_log_moneyness,
}

# Y-map registry: (source, target) -> map function
_Y_MAPS: dict[tuple[YCoord, YCoord], YMapFn] = {
    (YCoord.Price, YCoord.Volatility): _price_to_vol,
    (YCoord.Volatility, YCoord.Price): _vol_to_price,
    (YCoord.Volatility, YCoord.Variance): _vol_to_variance,
    (YCoord.Variance, YCoord.Volatility): _variance_to_vol,
    (YCoord.Variance, YCoord.TotalVariance): _variance_to_total_variance,
    (YCoord.TotalVariance, YCoord.Variance): _total_variance_to_variance,
}


def _ladder_path(ladder: list, source: object, target: object) -> list:
    """Return the sequence of ladder steps from source to target."""
    src_idx = ladder.index(source)
    tgt_idx = ladder.index(target)
    if src_idx == tgt_idx:
        return []
    step = 1 if tgt_idx > src_idx else -1
    return [(ladder[i], ladder[i + step]) for i in range(src_idx, tgt_idx, step)]


def compose_x_maps(
    source: XCoord,
    target: XCoord,
) -> list[tuple[XCoord, XCoord, XMapFn]]:
    """Return the chain of X-maps needed to go from source to target."""
    path = _ladder_path(X_LADDER, source, target)
    return [(s, t, _X_MAPS[(s, t)]) for s, t in path]


def compose_y_maps(
    source: YCoord,
    target: YCoord,
) -> list[tuple[YCoord, YCoord, YMapFn]]:
    """Return the chain of Y-maps needed to go from source to target."""
    path = _ladder_path(Y_LADDER, source, target)
    return [(s, t, _Y_MAPS[(s, t)]) for s, t in path]


def apply_x_chain(
    x: NDArray[np.float64],
    chain: list[tuple[XCoord, XCoord, XMapFn]],
    meta: SmileMetadata,
) -> NDArray[np.float64]:
    """Apply a chain of X-maps sequentially."""
    result = x
    for _s, _t, fn in chain:
        result = fn(result, meta)
    return result


def apply_y_chain(
    y: NDArray[np.float64],
    x: NDArray[np.float64],
    chain: list[tuple[YCoord, YCoord, YMapFn]],
    meta: SmileMetadata,
    x_coord: XCoord,
    target_x: XCoord,
) -> NDArray[np.float64]:
    """Apply a chain of Y-maps sequentially.

    For the Price↔Volatility step, X must be in FixedStrike.
    If needed, temporarily converts X to FixedStrike and back.
    """
    result = y
    current_x = x.copy()
    current_x_coord = x_coord

    for s, t, fn in chain:
        needs_fixed = (s == YCoord.Price and t == YCoord.Volatility) or (s == YCoord.Volatility and t == YCoord.Price)
        if needs_fixed and current_x_coord != XCoord.FixedStrike:
            # Convert X to FixedStrike
            to_fixed = compose_x_maps(current_x_coord, XCoord.FixedStrike)
            fixed_x = apply_x_chain(current_x, to_fixed, meta)
            result = fn(result, fixed_x, meta)
            # X stays in current_x_coord (unchanged for subsequent steps)
        else:
            result = fn(result, current_x, meta)

    return result
