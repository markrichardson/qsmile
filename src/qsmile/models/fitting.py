"""Smile fitting engine."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.optimize import least_squares

from qsmile.data.vols import SmileData
from qsmile.models.protocol import SmileModel
from qsmile.models.svi import SVIParams


@dataclass
class SmileResult:
    """Result of a smile model fit.

    Attributes:
    ----------
    params : SmileModel
        Fitted model instance.
    residuals : NDArray[np.float64]
        Per-observation residuals (model minus observed values in native coordinates).
    rmse : float
        Root mean square error of the fit.
    success : bool
        Whether the optimiser converged.
    """

    params: SmileModel
    residuals: NDArray[np.float64]
    rmse: float
    success: bool

    def evaluate(self, x: ArrayLike) -> NDArray[np.float64] | np.float64:
        """Compute model output at arbitrary x values in native coordinates."""
        return self.params.evaluate(x)


def _residuals(
    x: NDArray[np.float64],
    model: SmileModel,
    x_obs: NDArray[np.float64],
    y_obs: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Residual function for least_squares: model - observed."""
    fitted = model.from_array(x)
    y_model = np.asarray(fitted.evaluate(x_obs), dtype=np.float64)
    return y_model - y_obs


def fit(
    chain: SmileData,
    model: SmileModel,
    initial_params: SmileModel | None = None,
) -> SmileResult:
    """Fit a smile model to market data.

    Parameters
    ----------
    chain : SmileData
        Market data to fit. Uses mid values for fitting.
        Internally transforms to the model's native coordinates.
    model : SmileModel
        A model instance that defines native coordinates, bounds,
        evaluation, and initial-guess heuristic.
    initial_params : SmileModel, optional
        Initial parameter guess (must be same model type).
        If None, the model's heuristic initial guess is computed.

    Returns:
    -------
    SmileResult
        Fitted parameters, residuals, RMSE, and convergence status.
    """
    sd = chain.transform(model.native_x_coord, model.native_y_coord)
    x_obs = sd.x
    y_obs = sd.y_mid

    x0 = initial_params.to_array() if initial_params is not None else model.initial_guess(x_obs, y_obs)

    lower, upper = model.bounds

    result = least_squares(
        _residuals,
        x0,
        args=(model, x_obs, y_obs),
        bounds=(lower, upper),
        method="trf",
        max_nfev=10_000,
    )

    fitted_params = model.from_array(result.x)
    residuals = result.fun
    rmse = float(np.sqrt(np.mean(residuals**2)))

    return SmileResult(
        params=fitted_params,
        residuals=residuals,
        rmse=rmse,
        success=bool(result.success),
    )


def fit_svi(chain: SmileData, initial_params: SVIParams | None = None) -> SmileResult:
    """Fit SVI raw parameters to option chain data.

    Convenience wrapper around ``fit()`` with an SVI model.

    Parameters
    ----------
    chain : SmileData
        Market data to fit. Uses mid values for fitting.
        Internally transforms to (LogMoneynessStrike, TotalVariance).
    initial_params : SVIParams, optional
        Initial parameter guess. If None, a heuristic guess is computed.

    Returns:
    -------
    SmileResult
        Fitted parameters, residuals, RMSE, and convergence status.
    """
    # Use initial_params as both the model template and the starting point,
    # or create a default SVI model for the fit.
    if initial_params is not None:
        return fit(chain, initial_params, initial_params)
    # Need a valid SVIParams to serve as the model; params don't matter since
    # initial_guess will be used.
    model = SVIParams(a=0.0, b=0.01, rho=0.0, m=0.0, sigma=0.1)
    return fit(chain, model)
