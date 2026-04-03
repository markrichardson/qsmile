"""SmileModel protocol for pluggable smile models."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import numpy as np
from numpy.typing import ArrayLike, NDArray

from qsmile.core.coords import XCoord, YCoord


@runtime_checkable
class SmileModel(Protocol):
    """Protocol that every smile model must satisfy.

    A conforming model declares its native coordinate system, parameter
    schema, evaluation function, serialisation helpers, and box constraints
    so that the generic ``fit()`` engine can calibrate it to market data.
    """

    @property
    def native_x_coord(self) -> XCoord:
        """Native X-coordinate system for this model."""
        ...

    @property
    def native_y_coord(self) -> YCoord:
        """Native Y-coordinate system for this model."""
        ...

    @property
    def param_names(self) -> tuple[str, ...]:
        """Parameter names in array order."""
        ...

    @property
    def bounds(self) -> tuple[list[float], list[float]]:
        """Box constraints as (lower, upper) lists for the optimiser."""
        ...

    def evaluate(self, x: ArrayLike) -> NDArray[np.float64] | np.float64:
        """Compute model output at x values in native coordinates."""
        ...

    def to_array(self) -> NDArray[np.float64]:
        """Pack parameters into a flat array."""
        ...

    @staticmethod
    def from_array(x: NDArray[np.float64]) -> SmileModel:
        """Reconstruct a model instance from a flat parameter array."""
        ...

    @staticmethod
    def initial_guess(x: NDArray[np.float64], y: NDArray[np.float64]) -> NDArray[np.float64]:
        """Compute a heuristic initial guess from observed data."""
        ...
