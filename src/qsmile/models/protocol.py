"""SmileModel protocol and AbstractSmileModel base class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar, Protocol, Self, TypeVar, runtime_checkable

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
    def from_array(cls, x: NDArray[np.float64], **kwargs: Any) -> Self:
        """Reconstruct an instance from a flat parameter array."""
        ...

    @staticmethod
    def initial_guess(x: NDArray[np.float64], y: NDArray[np.float64]) -> NDArray[np.float64]:
        """Compute a heuristic initial guess from observed data."""
        ...


@dataclass
class AbstractSmileModel(ABC):
    """Abstract base for dataclass-based smile models.

    Provides default ``to_array()`` and ``from_array()`` implementations
    that derive serialisation from ``param_names``.  Subclasses must define:

    - Dataclass fields for the fitted parameters
    - ``native_x_coord``, ``native_y_coord``, ``param_names``, ``bounds`` ClassVars
    - ``evaluate(x)`` instance method
    - ``initial_guess(x, y)`` static method
    - ``__post_init__()`` for validation (optional)
    """

    native_x_coord: ClassVar[XCoord]
    native_y_coord: ClassVar[YCoord]
    param_names: ClassVar[tuple[str, ...]]
    bounds: ClassVar[tuple[list[float], list[float]]]

    def to_array(self) -> NDArray[np.float64]:
        """Pack fitted parameters into a flat array using ``param_names`` order."""
        return np.array([getattr(self, name) for name in self.param_names])

    @classmethod
    def from_array(cls, x: NDArray[np.float64], **kwargs: Any) -> Self:
        """Reconstruct an instance from a flat parameter array.

        Fitted parameters are mapped from *x* using ``param_names``.
        Additional keyword arguments (e.g. ``expiry``, ``forward``)
        are forwarded to the constructor for context fields.
        """
        params = {name: float(x[i]) for i, name in enumerate(cls.param_names)}
        return cls(**params, **kwargs)

    @abstractmethod
    def evaluate(self, x: ArrayLike) -> NDArray[np.float64] | np.float64:
        """Compute model output at x values in native coordinates."""
        ...

    @staticmethod
    @abstractmethod
    def initial_guess(x: NDArray[np.float64], y: NDArray[np.float64]) -> NDArray[np.float64]:
        """Compute a heuristic initial guess from observed data."""
        ...


M = TypeVar("M", bound=SmileModel)
