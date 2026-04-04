"""Smile fitting engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.optimize import least_squares

from qsmile.data.vols import SmileData
from qsmile.models.protocol import P, SmileModel


@dataclass
class SmileResult(Generic[P]):
    """Result of a smile model fit.

    Generic over ``P`` so that ``result.params`` preserves the
    concrete params type (e.g. ``SVIParams``).

    Attributes:
    ----------
    params : P
        Fitted parameter values.
    residuals : NDArray[np.float64]
        Per-observation residuals (model minus observed values in native coordinates).
    rmse : float
        Root mean square error of the fit.
    success : bool
        Whether the optimiser converged.
    """

    params: P
    residuals: NDArray[np.float64]
    rmse: float
    success: bool

    def evaluate(self, x: ArrayLike) -> NDArray[np.float64] | np.float64:
        """Compute model output at arbitrary x values in native coordinates."""
        return self.params.evaluate(x)


def _residuals(
    x: NDArray[np.float64],
    model: type[SmileModel[P]],
    x_obs: NDArray[np.float64],
    y_obs: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Residual function for least_squares: model - observed."""
    fitted = model.from_array(x)
    y_model = np.asarray(fitted.evaluate(x_obs), dtype=np.float64)
    return y_model - y_obs


def fit(
    chain: SmileData,
    model: type[SmileModel[P]],
    initial_guess: P | None = None,
) -> SmileResult[P]:
    """Fit a smile model to market data.

    Parameters
    ----------
    chain : SmileData
        Market data to fit. Uses mid values for fitting.
        Internally transforms to the model's native coordinates.
    model : type[SmileModel[P]]
        A model class (e.g. ``SVIModel``) that defines native coordinates,
        bounds, evaluation, and initial-guess heuristic.
    initial_guess : P, optional
        Initial parameter guess (e.g. an ``SVIParams`` instance).
        If None, the model's heuristic initial guess is computed from data.

    Returns:
    -------
    SmileResult[P]
        Fitted parameters, residuals, RMSE, and convergence status.
    """
    sd = chain.transform(model.native_x_coord, model.native_y_coord)
    x_obs = sd.x
    y_obs = sd.y_mid

    x0 = initial_guess.to_array() if initial_guess is not None else model.initial_guess(x_obs, y_obs)

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
