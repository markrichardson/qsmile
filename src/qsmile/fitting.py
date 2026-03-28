"""SVI smile fitting engine."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.optimize import least_squares

from qsmile.chain import OptionChain
from qsmile.svi import SVIParams, svi_total_variance


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


def _initial_guess(chain: OptionChain) -> NDArray[np.float64]:
    """Compute a heuristic initial guess for SVI parameters from market data."""
    k = chain.log_moneyness
    w = chain.total_variance

    # a: ATM total variance (interpolate or use closest to k=0)
    atm_idx = int(np.argmin(np.abs(k)))
    a0 = float(w[atm_idx])

    # b*rho: slope estimate from linear regression of w on k
    slope = float(np.polyfit(k, w, 1)[0]) if len(k) > 1 else 0.0

    b0 = max(float(np.std(w)) * 2, 0.01)
    rho0 = np.clip(slope / b0, -0.9, 0.9)
    m0 = float(k[atm_idx])
    sigma0 = max(float(np.std(k)) * 0.5, 0.01)

    return np.array([a0, b0, rho0, m0, sigma0])


def _residuals(x: NDArray[np.float64], k: NDArray[np.float64], w_obs: NDArray[np.float64]) -> NDArray[np.float64]:
    """Residual function for least_squares: model - observed."""
    params = SVIParams(a=x[0], b=x[1], rho=x[2], m=x[3], sigma=x[4])
    w_model = svi_total_variance(k, params)
    return w_model - w_obs


def fit_svi(chain: OptionChain, initial_params: SVIParams | None = None) -> SmileResult:
    """Fit SVI raw parameters to option chain data.

    Parameters
    ----------
    chain : OptionChain
        Market data to fit.
    initial_params : SVIParams, optional
        Initial parameter guess. If None, a heuristic guess is computed.

    Returns:
    -------
    SmileResult
        Fitted parameters, residuals, RMSE, and convergence status.
    """
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
        x0 = _initial_guess(chain)

    # Box constraints: a unbounded, b >= 0, -1 < rho < 1, m unbounded, sigma > 0
    lower = [-np.inf, 0.0, -0.999, -np.inf, 1e-8]
    upper = [np.inf, np.inf, 0.999, np.inf, np.inf]

    result = least_squares(
        _residuals,
        x0,
        args=(k, w_obs),
        bounds=(lower, upper),
        method="trf",
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
