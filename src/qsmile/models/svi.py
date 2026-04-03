"""SVI (Stochastic Volatility Inspired) raw parameterisation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

from qsmile.core.coords import XCoord, YCoord


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

    @property
    def native_x_coord(self) -> XCoord:
        """SVI operates in log-moneyness space."""
        return XCoord.LogMoneynessStrike

    @property
    def native_y_coord(self) -> YCoord:
        """SVI models total implied variance."""
        return YCoord.TotalVariance

    @property
    def param_names(self) -> tuple[str, ...]:
        """Parameter names in array order."""
        return ("a", "b", "rho", "m", "sigma")

    @property
    def bounds(self) -> tuple[list[float], list[float]]:
        """Box constraints: a unbounded, b >= 0, -1 < rho < 1, m unbounded, sigma > 0."""
        lower = [-np.inf, 0.0, -0.999, -np.inf, 1e-8]
        upper = [np.inf, np.inf, 0.999, np.inf, np.inf]
        return (lower, upper)

    def to_array(self) -> NDArray[np.float64]:
        """Pack parameters into a flat array."""
        return np.array([self.a, self.b, self.rho, self.m, self.sigma])

    @staticmethod
    def from_array(x: NDArray[np.float64]) -> SVIParams:
        """Reconstruct SVIParams from a flat array."""
        return SVIParams(
            a=float(x[0]),
            b=float(x[1]),
            rho=float(x[2]),
            m=float(x[3]),
            sigma=float(x[4]),
        )

    def evaluate(self, x: ArrayLike) -> NDArray[np.float64] | np.float64:
        """Compute SVI total variance at the given log-moneyness values."""
        return svi_total_variance(x, self)

    @staticmethod
    def initial_guess(x: NDArray[np.float64], y: NDArray[np.float64]) -> NDArray[np.float64]:
        """Compute a heuristic initial guess for SVI parameters from market data.

        Parameters
        ----------
        x : NDArray[np.float64]
            Log-moneyness values.
        y : NDArray[np.float64]
            Observed total variance values.
        """
        # a: ATM total variance (closest to k=0)
        atm_idx = int(np.argmin(np.abs(x)))
        a0 = float(y[atm_idx])

        # Estimate slope and curvature from a quadratic fit: w ≈ c0 + c1*k + c2*k²
        if len(x) >= 3:
            coeffs = np.polyfit(x, y, 2)
            c2, c1, _c0 = coeffs
            b0 = max(abs(c1) + 2 * abs(c2), 0.01)
            rho0 = np.clip(c1 / b0, -0.9, 0.9)
        else:
            b0 = max(float(np.std(y)) * 2, 0.01)
            rho0 = 0.0

        m0 = float(x[atm_idx])
        sigma0 = max(float(np.std(x)) * 0.5, 0.01)

        return np.array([a0, b0, rho0, m0, sigma0])


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
