"""Black76 forward option pricing and implied volatility inversion."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.stats import invgauss, norm


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

    Uses the explicit closed-form solution of Schadner (2026), "An Explicit
    Solution to Black-Scholes Implied Volatility" (arXiv:2604.24480), which
    expresses implied volatility as a direct transform of the option price
    via the inverse Gaussian quantile function -- no root finding required.

    For a call with normalized price ``c = C / (D F)`` and forward
    log-moneyness ``k = log(K/F)``::

        sigma = 2 / sqrt(T * F_IG^{-1}((1-c)/m; 2/|k|, 1))

    where ``m = 1`` if ``K > F`` and ``m = K/F`` if ``K < F``. At ``k = 0``
    the formula collapses to ``sigma = (2/sqrt(T)) * Phi^{-1}((c+1)/2)``.
    The put case follows from put-call parity.

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
        Tolerance for arbitrage-bound checks and the intrinsic-value
        short-circuit (returns ``0.0``).
    max_vol : float
        Retained for backward compatibility. The closed-form solution does
        not perform a search, so this argument is unused.
    """
    del max_vol  # unused; closed-form solution does not search
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

    # Edge case: price equals intrinsic -> vol is 0
    if price <= intrinsic + tol:
        return 0.0

    # Normalized price c = C / (D * F); k = log(K / F)
    df_f = discount_factor * forward
    k = float(np.log(strike / forward))

    # ATM case: explicit Gaussian-quantile form (Schadner Eq. 2)
    if abs(k) < 1e-15:
        c = price / df_f
        v = 2.0 * float(norm.ppf((c + 1.0) / 2.0))
        return v / float(np.sqrt(expiry))

    # Compute the IG quantile argument q in a numerically stable form that
    # avoids catastrophic cancellation when the option is deep ITM (i.e. when
    # the normalized price c is close to 1). Schadner's m factor folds the
    # ITM case into the OTM one via parity; combined with the price/(D*F)
    # normalization this yields:
    #   call:  q = (D*F - price) / (D * min(F, K))
    #   put :  q = (D*K - price) / (D * min(F, K))
    # We additionally compute the complementary probability qc = 1 - q in a
    # form that does not cancel, so we can use the survival-function inverse
    # ``invgauss.isf`` whenever q > 0.5. Computing the smaller of (q, qc)
    # accurately preserves machine precision in deep ITM/OTM regimes where
    # the quantile lies far in the tail of the inverse Gaussian.
    df = discount_factor
    denom = df * min(forward, strike)
    if is_call:
        numer = df * forward - price
        # qc = 1 - q; time value above intrinsic, normalized by D*K when ITM
        qc = price / (df * forward) if strike >= forward else (price - df * (forward - strike)) / (df * strike)
    else:
        numer = df * strike - price
        qc = (price - df * (strike - forward)) / (df * forward) if strike >= forward else price / (df * strike)
    q = numer / denom

    # Numerical guard: q must lie in (0, 1).
    q = min(max(q, 1e-300), 1.0)
    qc = min(max(qc, 1e-300), 1.0)

    # scipy.stats.invgauss is parameterised by mu with shape lambda = 1,
    # matching Schadner's F_IG(.; 2/|k|, 1). Use isf when q > 0.5 because the
    # survival-function inversion is better-conditioned in the right tail.
    mu = 2.0 / abs(k)
    x = float(invgauss.isf(qc, mu)) if q > 0.5 else float(invgauss.ppf(q, mu))
    return 2.0 / float(np.sqrt(expiry * x))
