"""Tests for qsmile plotting."""

from __future__ import annotations

import unittest.mock

import numpy as np
import pandas as pd
import pytest

from qsmile.core.coords import XCoord, YCoord
from qsmile.data.meta import SmileMetadata
from qsmile.data.strikes import StrikeArray
from qsmile.data.vols import VolData


def _make_sa(strikes, y_bid, y_ask):
    """Build a StrikeArray from parallel arrays."""
    sa = StrikeArray()
    idx = pd.Index(np.asarray(strikes, dtype=np.float64), dtype=np.float64)
    sa.set(("y", "bid"), pd.Series(np.asarray(y_bid, dtype=np.float64), index=idx))
    sa.set(("y", "ask"), pd.Series(np.asarray(y_ask, dtype=np.float64), index=idx))
    return sa


@pytest.fixture
def sample_vol_smile():
    """Create sample SmileData in (FixedStrike, Volatility) coords."""
    strikes = np.array([90.0, 100.0, 110.0])
    return VolData(
        strikearray=_make_sa(strikes, np.array([0.24, 0.19, 0.21]), np.array([0.26, 0.21, 0.23])),
        current_x_coord=XCoord.FixedStrike,
        current_y_coord=YCoord.Volatility,
        metadata=SmileMetadata(
            date=pd.Timestamp("2024-01-01"),
            expiry=pd.Timestamp("2024-07-01"),
            forward=100.0,
            discount_factor=1.0,
            sigma_atm=0.20,
        ),
    )


@pytest.fixture
def sample_unitised_smile():
    """Create sample SmileData in (StandardisedStrike, TotalVariance) coords."""
    k = np.array([-1.0, 0.0, 1.0])
    return VolData(
        strikearray=_make_sa(k, np.array([0.019, 0.018, 0.019]), np.array([0.021, 0.020, 0.021])),
        current_x_coord=XCoord.StandardisedStrike,
        current_y_coord=YCoord.TotalVariance,
        metadata=SmileMetadata(
            date=pd.Timestamp("2024-01-01"),
            expiry=pd.Timestamp("2024-07-01"),
            forward=1.0,
            discount_factor=1.0,
            sigma_atm=0.2,
        ),
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

    def test_plot_on_existing_axes(self, sample_vol_smile):
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots()
        result = sample_vol_smile.plot(ax=ax)
        assert result is fig
        assert ax.get_ylabel() == "Volatility"


class TestPricesPlot:
    def test_returns_figure(self):
        from qsmile.core.black76 import black76_call, black76_put
        from qsmile.data.meta import SmileMetadata
        from qsmile.data.prices import OptionChain

        strikes = np.array([90.0, 100.0, 110.0])
        F, D, vol, T = 100.0, 1.0, 0.2, 0.5
        call_mid = np.array([float(black76_call(F, K, D, vol, T)) for K in strikes])
        put_mid = np.array([float(black76_put(F, K, D, vol, T)) for K in strikes])

        sa = StrikeArray()
        idx = pd.Index(strikes, dtype=np.float64)
        sa.set(("call", "bid"), pd.Series(call_mid - 0.1, index=idx))
        sa.set(("call", "ask"), pd.Series(call_mid + 0.1, index=idx))
        sa.set(("put", "bid"), pd.Series(put_mid - 0.1, index=idx))
        sa.set(("put", "ask"), pd.Series(put_mid + 0.1, index=idx))
        chain = OptionChain(
            strikedata=sa,
            metadata=SmileMetadata(
                date=pd.Timestamp("2024-01-01"), expiry=pd.Timestamp("2024-07-01"), forward=F, discount_factor=D
            ),
        )
        import matplotlib.figure

        fig = chain.plot()
        assert isinstance(fig, matplotlib.figure.Figure)

    def test_plot_on_existing_axes(self):
        from qsmile.core.black76 import black76_call, black76_put
        from qsmile.data.meta import SmileMetadata
        from qsmile.data.prices import OptionChain

        strikes = np.array([90.0, 100.0, 110.0])
        F, D, vol, T = 100.0, 1.0, 0.2, 0.5
        call_mid = np.array([float(black76_call(F, K, D, vol, T)) for K in strikes])
        put_mid = np.array([float(black76_put(F, K, D, vol, T)) for K in strikes])

        sa = StrikeArray()
        idx = pd.Index(strikes, dtype=np.float64)
        sa.set(("call", "bid"), pd.Series(call_mid - 0.1, index=idx))
        sa.set(("call", "ask"), pd.Series(call_mid + 0.1, index=idx))
        sa.set(("put", "bid"), pd.Series(put_mid - 0.1, index=idx))
        sa.set(("put", "ask"), pd.Series(put_mid + 0.1, index=idx))
        chain = OptionChain(
            strikedata=sa,
            metadata=SmileMetadata(
                date=pd.Timestamp("2024-01-01"), expiry=pd.Timestamp("2024-07-01"), forward=F, discount_factor=D
            ),
        )
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots()
        result = chain.plot(ax=ax)
        assert result is fig
        assert ax.get_xlabel() == "Strike"
        assert ax.get_ylabel() == "Price"


class TestMatplotlibMissing:
    def test_import_error_raised(self):
        from qsmile.core.plot import _require_matplotlib

        with (
            unittest.mock.patch.dict("sys.modules", {"matplotlib": None}),
            pytest.raises(ImportError, match="matplotlib is required"),
        ):
            _require_matplotlib()
