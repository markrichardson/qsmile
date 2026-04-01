"""Tests for qsmile plotting."""

from __future__ import annotations

import unittest.mock

import numpy as np
import pytest

from qsmile.coords import XCoord, YCoord
from qsmile.metadata import SmileMetadata
from qsmile.smile_data import SmileData


@pytest.fixture
def sample_vol_smile():
    """Create sample SmileData in (FixedStrike, Volatility) coords."""
    strikes = np.array([90.0, 100.0, 110.0])
    return SmileData(
        x=strikes,
        y_bid=np.array([0.24, 0.19, 0.21]),
        y_ask=np.array([0.26, 0.21, 0.23]),
        x_coord=XCoord.FixedStrike,
        y_coord=YCoord.Volatility,
        metadata=SmileMetadata(forward=100.0, discount_factor=1.0, expiry=0.5, sigma_atm=0.20),
    )


@pytest.fixture
def sample_unitised_smile():
    """Create sample SmileData in (StandardisedStrike, TotalVariance) coords."""
    k = np.array([-1.0, 0.0, 1.0])
    return SmileData(
        x=k,
        y_bid=np.array([0.019, 0.018, 0.019]),
        y_ask=np.array([0.021, 0.020, 0.021]),
        x_coord=XCoord.StandardisedStrike,
        y_coord=YCoord.TotalVariance,
        metadata=SmileMetadata(forward=1.0, discount_factor=1.0, expiry=0.5, sigma_atm=0.2),
    )


class TestSmileDataPlot:
    def test_returns_figure(self, sample_vol_smile):
        import matplotlib.figure

        fig = sample_vol_smile.plot()
        assert isinstance(fig, matplotlib.figure.Figure)

    def test_custom_title(self, sample_vol_smile):
        fig = sample_vol_smile.plot(title="Custom Title")
        assert fig.axes[0].get_title() == "Custom Title"

    def test_axis_labels_from_coords(self, sample_vol_smile):
        fig = sample_vol_smile.plot()
        ax = fig.axes[0]
        assert ax.get_xlabel() == "FixedStrike"
        assert ax.get_ylabel() == "Volatility"

    def test_unitised_coords(self, sample_unitised_smile):
        import matplotlib.figure

        fig = sample_unitised_smile.plot()
        assert isinstance(fig, matplotlib.figure.Figure)
        ax = fig.axes[0]
        assert ax.get_xlabel() == "StandardisedStrike"
        assert ax.get_ylabel() == "TotalVariance"


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
