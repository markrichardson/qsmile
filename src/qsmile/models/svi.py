"""SVI (Stochastic Volatility Inspired) raw parameterisation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray


@dataclass
class SVIParams:
    """Raw SVI parameters.

    Parameters
    ----------
    a : float
        Vertical translation (overall variance level).
    b : float
        Slope of the wings. Must be >= 0.
    rho : float
        Correlation / rotation. Must be in (-1, 1).
    m : float
        Horizontal translation (log-moneyness shift).
    sigma : float
        Curvature at the vertex. Must be > 0.
    """

    a: float
    b: float
    rho: float
    m: float
    sigma: float

    def __post_init__(self) -> None:
        """Validate SVI parameter constraints."""
        if self.b < 0:
            msg = f"b must be non-negative, got {self.b}"
            raise ValueError(msg)
        if not (-1 < self.rho < 1):
            msg = f"rho must be in (-1, 1), got {self.rho}"
            raise ValueError(msg)
        if self.sigma <= 0:
            msg = f"sigma must be positive, got {self.sigma}"
            raise ValueError(msg)


def svi_total_variance(
    k: ArrayLike,
    params: SVIParams,
) -> NDArray[np.float64] | np.float64:
    """Compute SVI total implied variance.

    w(k) = a + b * (rho * (k - m) + sqrt((k - m)^2 + sigma^2))

    Parameters
    ----------
    k : ArrayLike
        Log-moneyness values.
    params : SVIParams
        Raw SVI parameters.

    Returns:
    -------
    Total implied variance at each k.
    """
    k = np.asarray(k, dtype=np.float64)
    d = k - params.m
    return params.a + params.b * (params.rho * d + np.sqrt(d**2 + params.sigma**2))


def svi_implied_vol(
    k: ArrayLike,
    params: SVIParams,
    expiry: float,
) -> NDArray[np.float64] | np.float64:
    """Compute SVI implied volatility from total variance.

    sigma_IV = sqrt(w(k) / T)

    Parameters
    ----------
    k : ArrayLike
        Log-moneyness values.
    params : SVIParams
        Raw SVI parameters.
    expiry : float
        Time to expiration in years. Must be positive.

    Returns:
    -------
    Implied volatility at each k.
    """
    if expiry <= 0:
        msg = f"expiry must be positive, got {expiry}"
        raise ValueError(msg)
    w = svi_total_variance(k, params)
    return np.sqrt(w / expiry)
