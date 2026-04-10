"""SABR stochastic volatility model — Hagan et al. (2002) lognormal approximation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

import numpy as np
from numpy.typing import ArrayLike, NDArray

from qsmile.core.coords import XCoord, YCoord
from qsmile.models.protocol import AbstractSmileModel


@dataclass
class SABRModel(AbstractSmileModel):
    """SABR model with Hagan (2002) lognormal implied volatility approximation.

    The SABR model describes the dynamics of a forward rate F and its
    stochastic volatility alpha via:

        dF = alpha * F^beta * dW_1
        dalpha = nu * alpha * dW_2
        <dW_1, dW_2> = rho * dt

    The Hagan et al. (2002) formula maps these parameters to a
    closed-form lognormal implied volatility approximation.

    Fitted parameters (included in the parameter vector):
        alpha, beta, rho, nu

    Context (provided via ``metadata``):
        expiry and forward are read from ``metadata.texpiry``
        and ``metadata.forward``.

    Parameters
    ----------
    alpha : float
        Initial volatility. Must be > 0.
    beta : float
        CEV exponent. Must be in [0, 1].
    rho : float
        Correlation between forward and vol. Must be in (-1, 1).
    nu : float
        Vol-of-vol. Must be >= 0.
    metadata : SmileMetadata
        Market context containing expiry, forward, etc.
    """

    alpha: float
    beta: float
    rho: float
    nu: float

    # -- Class-level model metadata --

    native_x_coord: ClassVar[XCoord] = XCoord.LogMoneynessStrike
    native_y_coord: ClassVar[YCoord] = YCoord.Volatility
    param_names: ClassVar[tuple[str, ...]] = ("alpha", "beta", "rho", "nu")
    bounds: ClassVar[tuple[list[float], list[float]]] = (
        [1e-8, 0.0, -0.999, 0.0],
        [np.inf, 1.0, 0.999, np.inf],
    )

    def __post_init__(self) -> None:
        """Validate SABR parameter constraints."""
        super().__post_init__()
        if self.alpha <= 0:
            msg = f"alpha must be positive, got {self.alpha}"
            raise ValueError(msg)
        if not (0 <= self.beta <= 1):
            msg = f"beta must be in [0, 1], got {self.beta}"
            raise ValueError(msg)
        if not (-1 < self.rho < 1):
            msg = f"rho must be in (-1, 1), got {self.rho}"
            raise ValueError(msg)
        if self.nu < 0:
            msg = f"nu must be non-negative, got {self.nu}"
            raise ValueError(msg)

    def evaluate(self, x: ArrayLike) -> NDArray[np.float64] | np.float64:
        """Compute Hagan (2002) lognormal implied volatility at log-moneyness values.

        Parameters
        ----------
        x : ArrayLike
            Log-moneyness k = ln(K/F).

        Returns:
        -------
        NDArray[np.float64] | np.float64
            Implied volatility (lognormal).
        """
        k = np.asarray(x, dtype=np.float64)
        forward = self.metadata.forward
        expiry = self.metadata.texpiry
        strikes = forward * np.exp(k)
        return self._hagan_implied_vol(forward, strikes, expiry, self.alpha, self.beta, self.rho, self.nu)

    @staticmethod
    def _hagan_implied_vol(
        fwd: float,
        strikes: NDArray[np.float64] | float,
        expiry: float,
        alpha: float,
        beta: float,
        rho: float,
        nu: float,
    ) -> NDArray[np.float64] | np.float64:
        """Hagan et al. (2002) lognormal implied vol approximation.

        Handles ATM (K ≈ F) and OTM/ITM cases separately for numerical
        stability.
        """
        strikes = np.asarray(strikes, dtype=np.float64)
        eps = 1e-12

        # ATM mask
        is_atm = np.abs(strikes - fwd) < eps * fwd

        # --- ATM formula ---
        fb = fwd ** (1 - beta)
        atm_vol = (alpha / fb) * (
            1
            + (
                ((1 - beta) ** 2 / 24) * alpha**2 / fwd ** (2 * (1 - beta))
                + 0.25 * rho * beta * nu * alpha / fb
                + (2 - 3 * rho**2) / 24 * nu**2
            )
            * expiry
        )

        # --- OTM/ITM formula ---
        fk_mid = np.where(is_atm, fwd, np.sqrt(fwd * strikes))
        fk_mid_b = fk_mid ** (1 - beta)
        log_fk = np.where(is_atm, 0.0, np.log(fwd / strikes))

        z = np.where(is_atm, 0.0, (nu / alpha) * fk_mid_b * log_fk)
        x_z = np.where(
            is_atm,
            1.0,
            np.where(
                np.abs(z) < eps,
                1.0,
                z / np.log((np.sqrt(1 - 2 * rho * z + z**2) + z - rho) / (1 - rho + eps)),
            ),
        )

        term1 = alpha / (fk_mid_b * (1 + (1 - beta) ** 2 / 24 * log_fk**2 + (1 - beta) ** 4 / 1920 * log_fk**4))
        correction = (
            1
            + (
                (1 - beta) ** 2 / 24 * alpha**2 / fk_mid ** (2 * (1 - beta))
                + 0.25 * rho * beta * nu * alpha / fk_mid_b
                + (2 - 3 * rho**2) / 24 * nu**2
            )
            * expiry
        )

        otm_vol = term1 * x_z * correction

        result = np.where(is_atm, atm_vol, otm_vol)
        # Clamp to avoid negative implied vol from numerical issues
        return np.maximum(result, eps)

    @staticmethod
    def initial_guess(x: NDArray[np.float64], y: NDArray[np.float64]) -> NDArray[np.float64]:
        """Compute a heuristic initial guess for SABR parameters from market data.

        Parameters
        ----------
        x : NDArray[np.float64]
            Log-moneyness values.
        y : NDArray[np.float64]
            Observed implied volatility values.
        """
        # alpha: ATM implied vol is a reasonable starting point
        atm_idx = int(np.argmin(np.abs(x)))
        alpha0 = max(float(y[atm_idx]), 0.01)

        # beta: start at 0.5 (between normal and lognormal)
        beta0 = 0.5

        # rho: estimate skew direction from slope of iv vs moneyness
        if len(x) >= 3:
            coeffs = np.polyfit(x, y, 1)
            rho0 = float(np.clip(coeffs[0] / (alpha0 + 1e-8), -0.9, 0.9))
        else:
            rho0 = 0.0

        # nu: estimate from curvature (smile convexity)
        if len(x) >= 3:
            coeffs2 = np.polyfit(x, y, 2)
            nu0 = max(float(np.abs(coeffs2[0])) * 2, 0.1)
        else:
            nu0 = 0.3

        return np.array([alpha0, beta0, rho0, nu0])
