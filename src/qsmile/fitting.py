"""SVI smile fitting engine."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.optimize import least_squares

from qsmile.coords import XCoord, YCoord
from qsmile.smile_data import SmileData
from qsmile.svi import SVIParams, svi_total_variance
from qsmile.vols import OptionChainVols


@dataclass
class SmileResult:
    """Result of an SVI fit.

    Attributes:
    ----------
    params : SVIParams
        Fitted SVI parameters.
    residuals : NDArray[np.float64]
        Per-observation residuals (model minus observed total variance).
    rmse : float
        Root mean square error of the fit.
    success : bool
        Whether the optimiser converged.
    """

    params: SVIParams
    residuals: NDArray[np.float64]
    rmse: float
    success: bool

    def evaluate(self, k: ArrayLike) -> NDArray[np.float64] | np.float64:
        """Compute SVI total variance at arbitrary log-moneyness values."""
        return svi_total_variance(k, self.params)


def _initial_guess(k: NDArray[np.float64], w: NDArray[np.float64]) -> NDArray[np.float64]:
    """Compute a heuristic initial guess for SVI parameters from market data."""
    # a: ATM total variance (closest to k=0)
    atm_idx = int(np.argmin(np.abs(k)))
    a0 = float(w[atm_idx])

    # Estimate slope and curvature from a quadratic fit: w ≈ c0 + c1*k + c2*k²
    if len(k) >= 3:
        coeffs = np.polyfit(k, w, 2)
        c2, c1, _c0 = coeffs
        # b controls wings (curvature), rho controls skew (slope)
        # From SVI asymptotics: dw/dk|0 ≈ b*rho, d²w/dk²|0 ≈ b/sigma
        b0 = max(abs(c1) + 2 * abs(c2), 0.01)
        rho0 = np.clip(c1 / b0, -0.9, 0.9)
    else:
        b0 = max(float(np.std(w)) * 2, 0.01)
        rho0 = 0.0

    m0 = float(k[atm_idx])
    sigma0 = max(float(np.std(k)) * 0.5, 0.01)

    return np.array([a0, b0, rho0, m0, sigma0])


def _residuals(x: NDArray[np.float64], k: NDArray[np.float64], w_obs: NDArray[np.float64]) -> NDArray[np.float64]:
    """Residual function for least_squares: model - observed."""
    params = SVIParams(a=x[0], b=x[1], rho=x[2], m=x[3], sigma=x[4])
    w_model = svi_total_variance(k, params)
    return w_model - w_obs


def fit_svi(chain: OptionChainVols | SmileData, initial_params: SVIParams | None = None) -> SmileResult:
    """Fit SVI raw parameters to option chain data.

    Parameters
    ----------
    chain : OptionChainVols | SmileData
        Market data to fit. Uses mid vols for fitting.
        If SmileData, transforms to (LogMoneynessStrike, TotalVariance) internally.
    initial_params : SVIParams, optional
        Initial parameter guess. If None, a heuristic guess is computed.

    Returns:
    -------
    SmileResult
        Fitted parameters, residuals, RMSE, and convergence status.
    """
    if isinstance(chain, SmileData):
        sd = chain.transform(XCoord.LogMoneynessStrike, YCoord.TotalVariance)
        k = sd.x
        w_obs = sd.y_mid
    else:
        k = chain.log_moneyness
        w_obs = chain.total_variance

    if initial_params is not None:
        x0 = np.array(
            [
                initial_params.a,
                initial_params.b,
                initial_params.rho,
                initial_params.m,
                initial_params.sigma,
            ]
        )
    else:
        x0 = _initial_guess(k, w_obs)

    # Box constraints: a unbounded, b >= 0, -1 < rho < 1, m unbounded, sigma > 0
    lower = [-np.inf, 0.0, -0.999, -np.inf, 1e-8]
    upper = [np.inf, np.inf, 0.999, np.inf, np.inf]

    result = least_squares(
        _residuals,
        x0,
        args=(k, w_obs),
        bounds=(lower, upper),
        method="trf",
        max_nfev=10_000,
    )

    fitted_params = SVIParams(
        a=float(result.x[0]),
        b=float(result.x[1]),
        rho=float(result.x[2]),
        m=float(result.x[3]),
        sigma=float(result.x[4]),
    )
    residuals = result.fun
    rmse = float(np.sqrt(np.mean(residuals**2)))

    return SmileResult(
        params=fitted_params,
        residuals=residuals,
        rmse=rmse,
        success=bool(result.success),
    )
