"""SmileModel abstract base class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, ClassVar, Self, TypeVar

import numpy as np
from numpy.typing import ArrayLike, NDArray

from qsmile.core.coords import XCoord, YCoord

if TYPE_CHECKING:
    import matplotlib.figure

    from qsmile.data.meta import SmileMetadata


@dataclass
class SmileModel(ABC):
    """Abstract base for dataclass-based smile models.

    Provides coordinate-aware evaluation, transformation, plotting,
    and default serialisation.  Subclasses must define:

    - Dataclass fields for the fitted parameters
    - ``native_x_coord``, ``native_y_coord``, ``param_names``, ``bounds`` ClassVars
    - ``_evaluate(x)`` instance method (raw formula in native coordinates)
    - ``initial_guess(x, y)`` static method
    - ``__post_init__()`` for validation (optional)
    """

    native_x_coord: ClassVar[XCoord]
    native_y_coord: ClassVar[YCoord]
    param_names: ClassVar[tuple[str, ...]]
    bounds: ClassVar[tuple[list[float], list[float]]]

    metadata: SmileMetadata = field(repr=False)
    current_x_coord: XCoord = field(init=False)
    current_y_coord: YCoord = field(init=False)

    def __post_init__(self) -> None:
        """Set current coords to native if not already set."""
        if not hasattr(self, "_coords_set"):
            self.current_x_coord = self.__class__.native_x_coord
            self.current_y_coord = self.__class__.native_y_coord

    @property
    def params(self) -> dict[str, float]:
        """Parameter name-to-value mapping."""
        return {name: getattr(self, name) for name in self.param_names}

    def to_array(self) -> NDArray[np.float64]:
        """Pack fitted parameters into a flat array using ``param_names`` order."""
        return np.array([getattr(self, name) for name in self.param_names])

    @classmethod
    def from_array(cls, x: NDArray[np.float64], *, metadata: SmileMetadata) -> Self:
        """Reconstruct an instance from a flat parameter array.

        Fitted parameters are mapped from *x* using ``param_names``.
        """
        params = {name: float(x[i]) for i, name in enumerate(cls.param_names)}
        return cls(**params, metadata=metadata)

    @abstractmethod
    def _evaluate(self, x: ArrayLike) -> NDArray[np.float64] | np.float64:
        """Compute model output at x values in native coordinates."""
        ...

    @staticmethod
    @abstractmethod
    def initial_guess(x: NDArray[np.float64], y: NDArray[np.float64]) -> NDArray[np.float64]:
        """Compute a heuristic initial guess from observed data."""
        ...

    def evaluate(self, x: ArrayLike) -> NDArray[np.float64] | np.float64:
        """Evaluate at *x* in current coordinates, transforming as needed."""
        from qsmile.core.maps import (
            apply_x_chain,
            apply_y_chain,
            compose_x_maps,
            compose_y_maps,
        )

        x_arr = np.asarray(x, dtype=np.float64)

        # If already in native coords, skip transforms
        if (
            self.current_x_coord == self.__class__.native_x_coord
            and self.current_y_coord == self.__class__.native_y_coord
        ):
            return self._evaluate(x_arr)

        # Transform x: current → native
        x_chain = compose_x_maps(self.current_x_coord, self.__class__.native_x_coord)
        native_x = apply_x_chain(x_arr, x_chain, self.metadata)

        # Evaluate in native coords
        native_y = np.asarray(self._evaluate(native_x), dtype=np.float64)

        # Transform y: native → current
        y_chain = compose_y_maps(self.__class__.native_y_coord, self.current_y_coord)
        return apply_y_chain(
            native_y,
            native_x,
            y_chain,
            self.metadata,
            self.__class__.native_x_coord,
            self.current_x_coord,
        )

    def transform(self, target_x: XCoord, target_y: YCoord) -> Self:
        """Return a copy expressed in the target coordinate system."""
        new = replace(self)
        object.__setattr__(new, "current_x_coord", target_x)
        object.__setattr__(new, "current_y_coord", target_y)
        return new

    def plot(
        self,
        *,
        title: str = "Smile Model",
        n_points: int = 200,
    ) -> matplotlib.figure.Figure:
        """Plot the model curve in current coordinates."""
        from qsmile.core.maps import apply_x_chain, compose_x_maps
        from qsmile.core.plot import plot_line

        # Generate grid in current x-coords
        compose_x_maps(self.current_x_coord, self.__class__.native_x_coord)
        # Build native-space grid, then convert to current
        native_lo, native_hi = -0.5, 0.5  # log-moneyness default range
        native_grid = np.linspace(native_lo, native_hi, n_points)

        inv_chain = compose_x_maps(self.__class__.native_x_coord, self.current_x_coord)
        x_grid = apply_x_chain(native_grid, inv_chain, self.metadata)

        y_grid = np.asarray(self.evaluate(x_grid), dtype=np.float64)

        return plot_line(
            x_grid,
            y_grid,
            xlabel=self.current_x_coord.name,
            ylabel=self.current_y_coord.name,
            title=title,
        )


M = TypeVar("M", bound=SmileModel)
