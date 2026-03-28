"""Black76 forward option pricing and implied volatility inversion."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.optimize import brentq
from scipy.stats import norm


def _validate_common(
    forward: ArrayLike,
    strike: ArrayLike,
    discount_factor: ArrayLike,
    expiry: float,
) -> None:
    """Validate common inputs for Black76 functions."""
    if expiry <= 0:
        msg = f"expiry must be positive, got {expiry}"
        raise ValueError(msg)
    forward_arr = np.asarray(forward)
    strike_arr = np.asarray(strike)
    df_arr = np.asarray(discount_factor)
    if np.any(forward_arr <= 0):
        msg = "forward must be positive"
        raise ValueError(msg)
    if np.any(strike_arr <= 0):
        msg = "strike must be positive"
        raise ValueError(msg)
    if np.any(df_arr <= 0):
        msg = "discount_factor must be positive"
        raise ValueError(msg)


def black76_call(
    forward: ArrayLike,
    strike: ArrayLike,
    discount_factor: ArrayLike,
    vol: ArrayLike,
    expiry: float,
) -> NDArray[np.float64] | np.floating:
    """Compute Black76 call option price.

    C = D * [F * Phi(d1) - K * Phi(d2)]

    Parameters
    ----------
    forward : ArrayLike
        Forward price. Must be positive.
    strike : ArrayLike
        Strike price. Must be positive.
    discount_factor : ArrayLike
        Discount factor. Must be positive.
    vol : ArrayLike
        Volatility. Must be non-negative.
    expiry : float
        Time to expiry in years. Must be positive.
    """
    _validate_common(forward, strike, discount_factor, expiry)
    vol_arr = np.asarray(vol, dtype=np.float64)
    if np.any(vol_arr < 0):
        msg = "vol must be non-negative"
        raise ValueError(msg)

    F = np.asarray(forward, dtype=np.float64)
    K = np.asarray(strike, dtype=np.float64)
    D = np.asarray(discount_factor, dtype=np.float64)
    sqrt_t = np.sqrt(expiry)

    # Handle zero vol case
    zero_vol = vol_arr == 0.0
    safe_vol = np.where(zero_vol, 1.0, vol_arr)  # avoid division by zero

    d1 = (np.log(F / K) + 0.5 * safe_vol**2 * expiry) / (safe_vol * sqrt_t)
    d2 = d1 - safe_vol * sqrt_t

    price = D * (F * norm.cdf(d1) - K * norm.cdf(d2))

    # Zero vol: intrinsic value
    intrinsic = D * np.maximum(F - K, 0.0)
    return np.where(zero_vol, intrinsic, price)


def black76_put(
    forward: ArrayLike,
    strike: ArrayLike,
    discount_factor: ArrayLike,
    vol: ArrayLike,
    expiry: float,
) -> NDArray[np.float64] | np.floating:
    """Compute Black76 put option price.

    P = D * [K * Phi(-d2) - F * Phi(-d1)]

    Parameters
    ----------
    forward : ArrayLike
        Forward price. Must be positive.
    strike : ArrayLike
        Strike price. Must be positive.
    discount_factor : ArrayLike
        Discount factor. Must be positive.
    vol : ArrayLike
        Volatility. Must be non-negative.
    expiry : float
        Time to expiry in years. Must be positive.
    """
    _validate_common(forward, strike, discount_factor, expiry)
    vol_arr = np.asarray(vol, dtype=np.float64)
    if np.any(vol_arr < 0):
        msg = "vol must be non-negative"
        raise ValueError(msg)

    F = np.asarray(forward, dtype=np.float64)
    K = np.asarray(strike, dtype=np.float64)
    D = np.asarray(discount_factor, dtype=np.float64)
    sqrt_t = np.sqrt(expiry)

    zero_vol = vol_arr == 0.0
    safe_vol = np.where(zero_vol, 1.0, vol_arr)

    d1 = (np.log(F / K) + 0.5 * safe_vol**2 * expiry) / (safe_vol * sqrt_t)
    d2 = d1 - safe_vol * sqrt_t

    price = D * (K * norm.cdf(-d2) - F * norm.cdf(-d1))

    intrinsic = D * np.maximum(K - F, 0.0)
    return np.where(zero_vol, intrinsic, price)


def black76_implied_vol(
    price: float,
    forward: float,
    strike: float,
    discount_factor: float,
    expiry: float,
    *,
    is_call: bool,
    tol: float = 1e-12,
    max_vol: float = 10.0,
) -> float:
    """Invert Black76 to recover implied volatility.

    Parameters
    ----------
    price : float
        Observed option price.
    forward : float
        Forward price. Must be positive.
    strike : float
        Strike price. Must be positive.
    discount_factor : float
        Discount factor. Must be positive.
    expiry : float
        Time to expiry in years. Must be positive.
    is_call : bool
        True for call, False for put.
    tol : float
        Root-finding tolerance.
    max_vol : float
        Upper bound for vol search.
    """
    _validate_common(forward, strike, discount_factor, expiry)

    # No-arbitrage bounds
    if is_call:
        intrinsic = discount_factor * max(forward - strike, 0.0)
        upper_bound = discount_factor * forward
    else:
        intrinsic = discount_factor * max(strike - forward, 0.0)
        upper_bound = discount_factor * strike

    if price < intrinsic - tol:
        msg = f"price {price} is below intrinsic value {intrinsic}"
        raise ValueError(msg)
    if price > upper_bound + tol:
        msg = f"price {price} exceeds upper bound {upper_bound}"
        raise ValueError(msg)

    # Edge case: price equals intrinsic → vol is 0
    if price <= intrinsic + tol:
        return 0.0

    pricer = black76_call if is_call else black76_put

    def objective(sigma: float) -> float:
        return float(pricer(forward, strike, discount_factor, sigma, expiry)) - price

    return brentq(objective, 0.0, max_vol, xtol=tol)
