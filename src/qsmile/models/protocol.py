"""SmileModel protocol for pluggable smile models."""

from __future__ import annotations

from typing import Protocol, Self, TypeVar, runtime_checkable

import numpy as np
from numpy.typing import ArrayLike, NDArray

from qsmile.core.coords import XCoord, YCoord


@runtime_checkable
class SmileModel(Protocol):
    """Protocol that every smile model class must satisfy.

    A conforming class acts as both a model definition (class-level
    metadata such as native coordinates and bounds) and a fitted
    parameter container (instance-level evaluation and serialisation).

    Example::

        result = fit(sd, SVIModel)  # result.params is an SVIModel instance
        result.params.evaluate(k)
    """

    native_x_coord: XCoord
    native_y_coord: YCoord
    param_names: tuple[str, ...]
    bounds: tuple[list[float], list[float]]

    def evaluate(self, x: ArrayLike) -> NDArray[np.float64] | np.float64:
        """Compute model output at x values in native coordinates."""
        ...

    def to_array(self) -> NDArray[np.float64]:
        """Pack parameters into a flat array."""
        ...

    @classmethod
    def from_array(cls, x: NDArray[np.float64]) -> Self:
        """Reconstruct an instance from a flat parameter array."""
        ...

    @staticmethod
    def initial_guess(x: NDArray[np.float64], y: NDArray[np.float64]) -> NDArray[np.float64]:
        """Compute a heuristic initial guess from observed data."""
        ...


M = TypeVar("M", bound=SmileModel)
