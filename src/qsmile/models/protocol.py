"""SmileModel and SmileParams protocols for pluggable smile models."""

from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

import numpy as np
from numpy.typing import ArrayLike, NDArray

from qsmile.core.coords import XCoord, YCoord


@runtime_checkable
class SmileParams(Protocol):
    """Protocol for fitted smile model parameters.

    A conforming params object holds specific parameter values and
    can evaluate the model at arbitrary points.
    """

    def evaluate(self, x: ArrayLike) -> NDArray[np.float64] | np.float64:
        """Compute model output at x values in native coordinates."""
        ...

    def to_array(self) -> NDArray[np.float64]:
        """Pack parameters into a flat array."""
        ...


P = TypeVar("P", bound=SmileParams)


class SmileModel(Protocol[P]):
    """Protocol that every smile model type must satisfy.

    Generic over the params type ``P`` so that ``fit()`` preserves
    the concrete params type in its return value.

    Example::

        class SVIModel(SmileModel[SVIParams]):
            ...

        result = fit(sd, SVIModel)  # result.params is SVIParams
    """

    native_x_coord: XCoord
    native_y_coord: YCoord
    param_names: tuple[str, ...]
    bounds: tuple[list[float], list[float]]

    @staticmethod
    def from_array(x: NDArray[np.float64]) -> P:
        """Reconstruct a params instance from a flat parameter array."""
        ...

    @staticmethod
    def initial_guess(x: NDArray[np.float64], y: NDArray[np.float64]) -> NDArray[np.float64]:
        """Compute a heuristic initial guess from observed data."""
        ...
