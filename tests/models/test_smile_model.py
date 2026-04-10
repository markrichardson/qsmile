"""Tests for qsmile.models.protocol.SmileModel."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

import numpy as np
import pandas as pd
import pytest
from numpy.typing import ArrayLike, NDArray

from qsmile.core.coords import XCoord, YCoord
from qsmile.data.meta import SmileMetadata
from qsmile.models.protocol import SmileModel

_META = SmileMetadata(
    date=pd.Timestamp("2024-01-01"),
    expiry=pd.Timestamp("2024-07-01"),
    forward=100.0,
    sigma_atm=0.2,
)


@dataclass
class _ConcreteModel(SmileModel):
    """Minimal concrete subclass for testing."""

    p1: float
    p2: float

    native_x_coord: ClassVar[XCoord] = XCoord.LogMoneynessStrike
    native_y_coord: ClassVar[YCoord] = YCoord.TotalVariance
    param_names: ClassVar[tuple[str, ...]] = ("p1", "p2")
    bounds: ClassVar[tuple[list[float], list[float]]] = ([-1.0, -1.0], [1.0, 1.0])

    def _evaluate(self, x: ArrayLike) -> NDArray[np.float64] | np.float64:
        k = np.asarray(x, dtype=np.float64)
        return self.p1 + self.p2 * k

    @staticmethod
    def initial_guess(x: NDArray[np.float64], y: NDArray[np.float64]) -> NDArray[np.float64]:
        return np.array([0.0, 0.0])


class TestSmileModelCannotInstantiate:
    def test_direct_instantiation_raises(self):
        with pytest.raises(TypeError):
            SmileModel(metadata=_META)


class TestSmileModelToArray:
    def test_to_array_uses_param_names(self):
        m = _ConcreteModel(p1=0.5, p2=-0.3, metadata=_META)
        arr = m.to_array()
        np.testing.assert_array_equal(arr, [0.5, -0.3])

    def test_to_array_dtype(self):
        m = _ConcreteModel(p1=0.5, p2=-0.3, metadata=_META)
        arr = m.to_array()
        assert arr.dtype == np.float64


class TestSmileModelFromArray:
    def test_from_array_reconstructs(self):
        arr = np.array([0.5, -0.3])
        m = _ConcreteModel.from_array(arr, metadata=_META)
        assert isinstance(m, _ConcreteModel)
        assert m.p1 == pytest.approx(0.5)
        assert m.p2 == pytest.approx(-0.3)

    def test_from_array_returns_self_type(self):
        arr = np.array([0.5, -0.3])
        m = _ConcreteModel.from_array(arr, metadata=_META)
        assert type(m) is _ConcreteModel

    def test_round_trip(self):
        original = _ConcreteModel(p1=0.123, p2=-0.456, metadata=_META)
        recovered = _ConcreteModel.from_array(original.to_array(), metadata=_META)
        np.testing.assert_allclose(recovered.to_array(), original.to_array())

    def test_from_array_attaches_metadata(self):
        arr = np.array([0.5, -0.3])
        m = _ConcreteModel.from_array(arr, metadata=_META)
        assert m.metadata is _META


class TestSmileModelProtocolConformance:
    def test_isinstance_check(self):
        m = _ConcreteModel(p1=0.5, p2=-0.3, metadata=_META)
        assert isinstance(m, SmileModel)


class TestSmileModelParams:
    def test_params_returns_dict(self):
        m = _ConcreteModel(p1=0.5, p2=-0.3, metadata=_META)
        p = m.params
        assert p == {"p1": 0.5, "p2": -0.3}

    def test_params_keys_match_param_names(self):
        m = _ConcreteModel(p1=0.5, p2=-0.3, metadata=_META)
        assert tuple(m.params.keys()) == m.param_names


class TestSmileModelCurrentCoords:
    def test_defaults_to_native(self):
        m = _ConcreteModel(p1=0.5, p2=-0.3, metadata=_META)
        assert m.current_x_coord == XCoord.LogMoneynessStrike
        assert m.current_y_coord == YCoord.TotalVariance

    def test_transform_updates_current_coords(self):
        m = _ConcreteModel(p1=0.5, p2=-0.3, metadata=_META)
        t = m.transform(XCoord.FixedStrike, YCoord.Volatility)
        assert t.current_x_coord == XCoord.FixedStrike
        assert t.current_y_coord == YCoord.Volatility

    def test_transform_preserves_params(self):
        m = _ConcreteModel(p1=0.5, p2=-0.3, metadata=_META)
        t = m.transform(XCoord.FixedStrike, YCoord.Volatility)
        assert t.params == m.params

    def test_transform_does_not_mutate_original(self):
        m = _ConcreteModel(p1=0.5, p2=-0.3, metadata=_META)
        m.transform(XCoord.FixedStrike, YCoord.Volatility)
        assert m.current_x_coord == XCoord.LogMoneynessStrike
        assert m.current_y_coord == YCoord.TotalVariance


class TestSmileModelEvaluate:
    def test_evaluate_in_native_coords_equals_raw(self):
        m = _ConcreteModel(p1=0.5, p2=-0.3, metadata=_META)
        x = np.array([-0.1, 0.0, 0.1])
        np.testing.assert_allclose(m.evaluate(x), m._evaluate(x))

    def test_evaluate_transforms_coords(self):
        m = _ConcreteModel(p1=0.04, p2=0.1, metadata=_META)
        t = m.transform(XCoord.MoneynessStrike, YCoord.TotalVariance)
        # Should not raise and should return finite values
        moneyness = np.array([0.9, 1.0, 1.1])
        y = t.evaluate(moneyness)
        assert np.all(np.isfinite(y))


class TestSmileModelMetadata:
    def test_metadata_available(self):
        m = _ConcreteModel(p1=0.5, p2=-0.3, metadata=_META)
        assert m.metadata is _META

    def test_metadata_preserved_by_transform(self):
        m = _ConcreteModel(p1=0.5, p2=-0.3, metadata=_META)
        t = m.transform(XCoord.FixedStrike, YCoord.Volatility)
        assert t.metadata is _META


class TestSmileModelPlot:
    def test_plot_returns_figure(self):
        m = _ConcreteModel(p1=0.04, p2=0.1, metadata=_META)
        fig = m.plot()
        import matplotlib.figure

        assert isinstance(fig, matplotlib.figure.Figure)
