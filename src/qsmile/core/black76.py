"""Black76 forward option pricing and implied volatility inversion."""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import ArrayLike, NDArray
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


def _initial_vol_guess(
    call_undisc: float,
    forward: float,
    strike: float,
    expiry: float,
) -> float:
    """Closed-form initial guess for the implied volatility of an undiscounted call.

    Uses the Corrado-Miller (1996) rational approximation, which is exact at
    the money and accurate for moderate moneyness, falling back to the
    Brenner-Subrahmanyam (1988) ATM formula when the CM discriminant is
    negative (e.g. far-from-the-money quotes).
    """
    sqrt_t = math.sqrt(expiry)
    half_diff = 0.5 * (forward - strike)
    # Corrado-Miller discriminant
    disc = (call_undisc - half_diff) ** 2 - (forward - strike) ** 2 / math.pi
    if disc >= 0.0 and (forward + strike) > 0.0:
        sigma = (math.sqrt(2.0 * math.pi) / (forward + strike)) * (
            (call_undisc - half_diff) + math.sqrt(disc)
        )
        if sigma > 0.0 and math.isfinite(sigma):
            return sigma / sqrt_t
    # Brenner-Subrahmanyam ATM fallback: σ ≈ √(2π/T) · C/F
    sigma = math.sqrt(2.0 * math.pi) * call_undisc / max(forward, 1e-300)
    if sigma > 0.0 and math.isfinite(sigma):
        return sigma / sqrt_t
    return 0.2  # last-ditch default


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

    Uses a semi-closed-form algorithm: a closed-form analytical initial
    guess (Corrado-Miller, with a Brenner-Subrahmanyam fallback) is refined
    by safeguarded Newton-Raphson iterations against the analytical Black76
    vega. Convergence is quadratic and typically reaches machine precision
    in a handful of iterations, with no bracket-based root-finder required.

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
        Convergence tolerance on the price residual (in undiscounted units).
    max_vol : float
        Upper bound for the implied volatility search.
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

    # Reduce put to call via put-call parity: C - P = D * (F - K).
    # The Black76 vega is identical for calls and puts, so a single Newton
    # loop on the call branch handles both option types.
    f, k, t = float(forward), float(strike), float(expiry)
    df = float(discount_factor)
    if is_call:
        call_undisc = price / df
    else:
        call_undisc = price / df + (f - k)

    sqrt_t = math.sqrt(t)
    log_fk = math.log(f / k)

    # Tolerance on the *undiscounted* call price (Newton's price residual).
    price_tol = max(tol, 1e-15) * max(f, k, 1.0)

    sigma = _initial_vol_guess(call_undisc, f, k, t)
    # Clamp the seed into a reasonable open interval.
    sigma = min(max(sigma, 1e-8), max_vol)

    max_iter = 64
    for _ in range(max_iter):
        v_sqrt_t = sigma * sqrt_t
        d1 = (log_fk + 0.5 * v_sqrt_t * v_sqrt_t) / v_sqrt_t
        d2 = d1 - v_sqrt_t
        model = f * norm.cdf(d1) - k * norm.cdf(d2)
        diff = model - call_undisc
        if abs(diff) <= price_tol:
            return sigma
        # Black76 vega (undiscounted): F * sqrt(T) * φ(d1)
        vega = f * sqrt_t * norm.pdf(d1)
        if vega < 1e-300:
            # Vega has vanished; bisect-style nudge toward the bound.
            sigma = 0.5 * (sigma + (max_vol if diff < 0 else 0.0))
            continue
        step = diff / vega
        next_sigma = sigma - step
        # Safeguard: keep iterates strictly inside (0, max_vol]. If Newton
        # overshoots, halve the step until it lies in-bounds.
        while next_sigma <= 0.0 or next_sigma > max_vol:
            step *= 0.5
            next_sigma = sigma - step
            if abs(step) < 1e-300:
                break
        if abs(next_sigma - sigma) <= tol:
            return next_sigma
        sigma = next_sigma

    # Fell through without meeting the strict tolerance; return best estimate.
    return sigma
