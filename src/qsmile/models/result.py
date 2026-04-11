"""Smile fitting engine."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import least_squares

from qsmile.data.meta import SmileMetadata
from qsmile.data.vols import SmileData
from qsmile.models.base import SmileModel


@dataclass
class SmileResult:
    """Result of a smile model fit.

    Attributes:
    ----------
    model : SmileModel
        Fitted model instance (coordinate-aware).
    residuals : NDArray[np.float64]
        Per-observation residuals (model minus observed values in native coordinates).
    rmse : float
        Root mean square error of the fit.
    success : bool
        Whether the optimiser converged.
    """

    model: SmileModel
    residuals: NDArray[np.float64]
    rmse: float
    success: bool


def _residuals(
    x: NDArray[np.float64],
    model: type[SmileModel],
    x_obs: NDArray[np.float64],
    y_obs: NDArray[np.float64],
    metadata: SmileMetadata,
) -> NDArray[np.float64]:
    """Residual function for least_squares: model - observed."""
    fitted = model.from_array(x, metadata=metadata)
    y_model = np.asarray(fitted._evaluate(x_obs), dtype=np.float64)
    return y_model - y_obs


def fit(
    chain: SmileData,
    model: type[SmileModel],
    initial_guess: SmileModel | None = None,
) -> SmileResult:
    """Fit a smile model to market data.

    Parameters
    ----------
    chain : SmileData
        Market data to fit. Uses mid values for fitting.
        Internally transforms to the model's native coordinates.
    model : type[SmileModel]
        A model class (e.g. ``SVIModel``) that defines native coordinates,
        bounds, evaluation, and initial-guess heuristic.
    initial_guess : SmileModel, optional
        Initial parameter guess (e.g. an ``SVIModel(...)`` instance).
        If None, the model's heuristic initial guess is computed from data.

    Returns:
    -------
    SmileResult
        Fitted model, residuals, RMSE, and convergence status.
    """
    sd = chain.transform(model.native_x_coord, model.native_y_coord)
    x_obs = sd.x
    y_obs = sd.y_mid
    metadata = sd.metadata

    x0 = initial_guess.to_array() if initial_guess is not None else model.initial_guess(x_obs, y_obs)

    lower, upper = model.bounds

    result = least_squares(
        _residuals,
        x0,
        args=(model, x_obs, y_obs, metadata),
        bounds=(lower, upper),
        method="trf",
        max_nfev=10_000,
    )

    fitted_params = model.from_array(result.x, metadata=metadata)
    residuals = result.fun
    rmse = float(np.sqrt(np.mean(residuals**2)))

    return SmileResult(
        model=fitted_params,
        residuals=residuals,
        rmse=rmse,
        success=bool(result.success),
    )
