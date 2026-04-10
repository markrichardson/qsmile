"""SVI (Stochastic Volatility Inspired) raw parameterisation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

import numpy as np
from numpy.typing import ArrayLike, NDArray

from qsmile.core.coords import XCoord, YCoord
from qsmile.models.protocol import AbstractSmileModel


@dataclass
class SVIModel(AbstractSmileModel):
    """Raw SVI parameterisation: model definition and fitted parameters.

    The SVI raw parameterisation models total implied variance as:

        w(k) = a + b * (rho * (k - m) + sqrt((k - m)^2 + sigma^2))

    where k = ln(K/F) is log-moneyness.

    Pass this class to ``fit()`` as the model, and receive instances
    back as fitted parameters::

        result = fit(sd, model=SVIModel)
        result.params          # → SVIModel instance
        result.params.evaluate(k)

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

    # -- Class-level model metadata (excluded from dataclass fields) --

    native_x_coord: ClassVar[XCoord] = XCoord.LogMoneynessStrike
    native_y_coord: ClassVar[YCoord] = YCoord.TotalVariance
    param_names: ClassVar[tuple[str, ...]] = ("a", "b", "rho", "m", "sigma")
    bounds: ClassVar[tuple[list[float], list[float]]] = (
        [-np.inf, 0.0, -0.999, -np.inf, 1e-8],
        [np.inf, np.inf, 0.999, np.inf, np.inf],
    )

    def __post_init__(self) -> None:
        """Validate SVI parameter constraints."""
        super().__post_init__()
        if self.b < 0:
            msg = f"b must be non-negative, got {self.b}"
            raise ValueError(msg)
        if not (-1 < self.rho < 1):
            msg = f"rho must be in (-1, 1), got {self.rho}"
            raise ValueError(msg)
        if self.sigma <= 0:
            msg = f"sigma must be positive, got {self.sigma}"
            raise ValueError(msg)

    def evaluate(self, x: ArrayLike) -> NDArray[np.float64] | np.float64:
        """Compute SVI total variance at the given log-moneyness values.

        w(k) = a + b * (rho * (k - m) + sqrt((k - m)^2 + sigma^2))
        """
        k = np.asarray(x, dtype=np.float64)
        d = k - self.m
        return self.a + self.b * (self.rho * d + np.sqrt(d**2 + self.sigma**2))

    def implied_vol(self, k: ArrayLike, expiry: float) -> NDArray[np.float64] | np.float64:
        """Compute SVI implied volatility from total variance.

        sigma_IV = sqrt(w(k) / T)

        Parameters
        ----------
        k : ArrayLike
            Log-moneyness values.
        expiry : float
            Time to expiration in years. Must be positive.
        """
        if expiry <= 0:
            msg = f"expiry must be positive, got {expiry}"
            raise ValueError(msg)
        w = self.evaluate(k)
        return np.sqrt(w / expiry)

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
