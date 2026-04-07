"""Smile fitting engine."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Any, Generic

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.optimize import least_squares

from qsmile.data.vols import SmileData
from qsmile.models.protocol import M, SmileModel


@dataclass
class SmileResult(Generic[M]):
    """Result of a smile model fit.

    Generic over ``M`` so that ``result.params`` preserves the
    concrete model type (e.g. ``SVIModel``).

    Attributes:
    ----------
    params : M
        Fitted parameter values.
    residuals : NDArray[np.float64]
        Per-observation residuals (model minus observed values in native coordinates).
    rmse : float
        Root mean square error of the fit.
    success : bool
        Whether the optimiser converged.
    """

    params: M
    residuals: NDArray[np.float64]
    rmse: float
    success: bool

    def evaluate(self, x: ArrayLike) -> NDArray[np.float64] | np.float64:
        """Compute model output at arbitrary x values in native coordinates."""
        return self.params.evaluate(x)


def _context_for_model(model: type[SmileModel], sd: SmileData) -> dict[str, Any]:
    """Extract non-param context fields from SmileData for models that need them.

    Compares the model's dataclass fields against ``param_names`` to find
    context fields (e.g. ``expiry``, ``forward`` for SABR).  Values are
    sourced from ``SmileData.metadata``.

    Models that declare an ``expiry: float`` context field receive
    ``metadata.texpiry`` (the derived year-fraction), not ``metadata.expiry``
    (which is a ``pd.Timestamp``).
    """
    _METADATA_ALIAS: dict[str, str] = {"expiry": "texpiry"}

    if not dataclasses.is_dataclass(model):
        return {}
    all_field_names = {f.name for f in dataclasses.fields(model)}
    context_fields = all_field_names - set(model.param_names)
    context: dict[str, Any] = {}
    for name in context_fields:
        attr = _METADATA_ALIAS.get(name, name)
        if hasattr(sd.metadata, attr):
            context[name] = getattr(sd.metadata, attr)
    return context


def _residuals(
    x: NDArray[np.float64],
    model: type[SmileModel],
    x_obs: NDArray[np.float64],
    y_obs: NDArray[np.float64],
    context: dict[str, Any],
) -> NDArray[np.float64]:
    """Residual function for least_squares: model - observed."""
    fitted = model.from_array(x, **context)
    y_model = np.asarray(fitted.evaluate(x_obs), dtype=np.float64)
    return y_model - y_obs


def fit(
    chain: SmileData,
    model: type[M],
    initial_guess: M | None = None,
) -> SmileResult[M]:
    """Fit a smile model to market data.

    Parameters
    ----------
    chain : SmileData
        Market data to fit. Uses mid values for fitting.
        Internally transforms to the model's native coordinates.
    model : type[M]
        A model class (e.g. ``SVIModel``) that defines native coordinates,
        bounds, evaluation, and initial-guess heuristic.
    initial_guess : M, optional
        Initial parameter guess (e.g. an ``SVIModel(...)`` instance).
        If None, the model's heuristic initial guess is computed from data.

    Returns:
    -------
    SmileResult[M]
        Fitted parameters, residuals, RMSE, and convergence status.
    """
    sd = chain.transform(model.native_x_coord, model.native_y_coord)
    x_obs = sd.x
    y_obs = sd.y_mid

    x0 = initial_guess.to_array() if initial_guess is not None else model.initial_guess(x_obs, y_obs)

    lower, upper = model.bounds
    context = _context_for_model(model, sd)

    result = least_squares(
        _residuals,
        x0,
        args=(model, x_obs, y_obs, context),
        bounds=(lower, upper),
        method="trf",
        max_nfev=10_000,
    )

    fitted_params = model.from_array(result.x, **context)
    residuals = result.fun
    rmse = float(np.sqrt(np.mean(residuals**2)))

    return SmileResult(
        params=fitted_params,
        residuals=residuals,
        rmse=rmse,
        success=bool(result.success),
    )
