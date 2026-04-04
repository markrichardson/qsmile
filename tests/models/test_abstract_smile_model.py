"""Tests for qsmile.models.protocol.AbstractSmileModel."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

import numpy as np
import pytest
from numpy.typing import ArrayLike, NDArray

from qsmile.core.coords import XCoord, YCoord
from qsmile.models.protocol import AbstractSmileModel, SmileModel


@dataclass
class _ConcreteModel(AbstractSmileModel):
    """Minimal concrete subclass for testing."""

    p1: float
    p2: float

    native_x_coord: ClassVar[XCoord] = XCoord.LogMoneynessStrike
    native_y_coord: ClassVar[YCoord] = YCoord.TotalVariance
    param_names: ClassVar[tuple[str, ...]] = ("p1", "p2")
    bounds: ClassVar[tuple[list[float], list[float]]] = ([-1.0, -1.0], [1.0, 1.0])

    def evaluate(self, x: ArrayLike) -> NDArray[np.float64] | np.float64:
        k = np.asarray(x, dtype=np.float64)
        return self.p1 + self.p2 * k

    @staticmethod
    def initial_guess(x: NDArray[np.float64], y: NDArray[np.float64]) -> NDArray[np.float64]:
        return np.array([0.0, 0.0])


class TestAbstractSmileModelCannotInstantiate:
    def test_direct_instantiation_raises(self):
        with pytest.raises(TypeError):
            AbstractSmileModel()


class TestAbstractSmileModelToArray:
    def test_to_array_uses_param_names(self):
        m = _ConcreteModel(p1=0.5, p2=-0.3)
        arr = m.to_array()
        np.testing.assert_array_equal(arr, [0.5, -0.3])

    def test_to_array_dtype(self):
        m = _ConcreteModel(p1=0.5, p2=-0.3)
        arr = m.to_array()
        assert arr.dtype == np.float64


class TestAbstractSmileModelFromArray:
    def test_from_array_reconstructs(self):
        arr = np.array([0.5, -0.3])
        m = _ConcreteModel.from_array(arr)
        assert isinstance(m, _ConcreteModel)
        assert m.p1 == pytest.approx(0.5)
        assert m.p2 == pytest.approx(-0.3)

    def test_from_array_returns_self_type(self):
        arr = np.array([0.5, -0.3])
        m = _ConcreteModel.from_array(arr)
        assert type(m) is _ConcreteModel

    def test_round_trip(self):
        original = _ConcreteModel(p1=0.123, p2=-0.456)
        recovered = _ConcreteModel.from_array(original.to_array())
        np.testing.assert_allclose(recovered.to_array(), original.to_array())

    def test_from_array_with_kwargs(self):
        """from_array forwards extra kwargs to the constructor."""

        @dataclass
        class _ModelWithContext(AbstractSmileModel):
            p1: float
            context_field: float

            native_x_coord: ClassVar[XCoord] = XCoord.LogMoneynessStrike
            native_y_coord: ClassVar[YCoord] = YCoord.Volatility
            param_names: ClassVar[tuple[str, ...]] = ("p1",)
            bounds: ClassVar[tuple[list[float], list[float]]] = ([0.0], [1.0])

            def evaluate(self, x: ArrayLike) -> NDArray[np.float64] | np.float64:
                return np.asarray(x, dtype=np.float64) * self.p1

            @staticmethod
            def initial_guess(x: NDArray[np.float64], y: NDArray[np.float64]) -> NDArray[np.float64]:
                return np.array([0.5])

        m = _ModelWithContext.from_array(np.array([0.7]), context_field=42.0)
        assert m.p1 == pytest.approx(0.7)
        assert m.context_field == pytest.approx(42.0)


class TestAbstractSmileModelProtocolConformance:
    def test_isinstance_check(self):
        m = _ConcreteModel(p1=0.5, p2=-0.3)
        assert isinstance(m, SmileModel)
