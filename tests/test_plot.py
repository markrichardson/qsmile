"""Tests for qsmile plotting."""

from __future__ import annotations

import unittest.mock

import numpy as np
import pytest

from qsmile.unitised import UnitisedSpaceVols
from qsmile.vols import OptionChainVols


@pytest.fixture
def sample_vols():
    """Create sample OptionChainVols for testing."""
    strikes = np.array([90.0, 100.0, 110.0])
    return OptionChainVols(
        strikes=strikes,
        vol_bid=np.array([0.24, 0.19, 0.21]),
        vol_ask=np.array([0.26, 0.21, 0.23]),
        forward=100.0,
        discount_factor=1.0,
        expiry=0.5,
    )


@pytest.fixture
def sample_unitised():
    """Create sample UnitisedSpaceVols for testing."""
    k = np.array([-1.0, 0.0, 1.0])
    return UnitisedSpaceVols(
        k_unitised=k,
        variance_bid=np.array([0.019, 0.018, 0.019]),
        variance_ask=np.array([0.021, 0.020, 0.021]),
        sigma_atm=0.2,
        expiry=0.5,
    )


class TestVolsPlot:
    def test_returns_figure(self, sample_vols):
        import matplotlib.figure

        fig = sample_vols.plot()
        assert isinstance(fig, matplotlib.figure.Figure)

    def test_custom_title(self, sample_vols):
        fig = sample_vols.plot(title="Custom Title")
        assert fig.axes[0].get_title() == "Custom Title"


class TestUnitisedPlot:
    def test_returns_figure(self, sample_unitised):
        import matplotlib.figure

        fig = sample_unitised.plot()
        assert isinstance(fig, matplotlib.figure.Figure)

    def test_custom_title(self, sample_unitised):
        fig = sample_unitised.plot(title="Unit Plot")
        assert fig.axes[0].get_title() == "Unit Plot"


class TestPricesPlot:
    def test_returns_figure(self):
        from qsmile.black76 import black76_call, black76_put
        from qsmile.prices import OptionChainPrices

        strikes = np.array([90.0, 100.0, 110.0])
        F, D, vol, T = 100.0, 1.0, 0.2, 0.5
        call_mid = np.array([float(black76_call(F, K, D, vol, T)) for K in strikes])
        put_mid = np.array([float(black76_put(F, K, D, vol, T)) for K in strikes])

        chain = OptionChainPrices(
            strikes=strikes,
            call_bid=call_mid - 0.1,
            call_ask=call_mid + 0.1,
            put_bid=put_mid - 0.1,
            put_ask=put_mid + 0.1,
            expiry=T,
            forward=F,
            discount_factor=D,
        )
        import matplotlib.figure

        fig = chain.plot()
        assert isinstance(fig, matplotlib.figure.Figure)


class TestMatplotlibMissing:
    def test_import_error_raised(self):
        from qsmile.plot import _require_matplotlib

        with (
            unittest.mock.patch.dict("sys.modules", {"matplotlib": None}),
            pytest.raises(ImportError, match="matplotlib is required"),
        ):
            _require_matplotlib()
