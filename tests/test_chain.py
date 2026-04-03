"""Tests for SmileData.from_mid_vols and SmileData validation."""

from __future__ import annotations

import numpy as np
import pytest

from qsmile.core.coords import XCoord, YCoord
from qsmile.data.metadata import SmileMetadata
from qsmile.data.smile_data import SmileData


class TestFromMidVolsConstruction:
    def test_from_arrays(self):
        strikes = np.array([90.0, 100.0, 110.0])
        ivs = np.array([0.25, 0.20, 0.22])
        sd = SmileData.from_mid_vols(strikes=strikes, ivs=ivs, forward=100.0, expiry=0.5)
        np.testing.assert_array_equal(sd.x, strikes)
        np.testing.assert_array_equal(sd.y_bid, ivs)
        np.testing.assert_array_equal(sd.y_ask, ivs)
        assert sd.x_coord == XCoord.FixedStrike
        assert sd.y_coord == YCoord.Volatility
        assert sd.metadata.forward == 100.0
        assert sd.metadata.expiry == 0.5
        assert sd.metadata.discount_factor == 1.0

    def test_from_lists(self):
        sd = SmileData.from_mid_vols(strikes=[90, 100, 110], ivs=[0.25, 0.20, 0.22], forward=100.0, expiry=0.5)
        assert isinstance(sd.x, np.ndarray)
        assert isinstance(sd.y_bid, np.ndarray)
        assert sd.x.dtype == np.float64

    def test_custom_discount_factor(self):
        sd = SmileData.from_mid_vols(
            strikes=[90, 100, 110], ivs=[0.25, 0.20, 0.22], forward=100.0, expiry=0.5, discount_factor=0.99
        )
        assert sd.metadata.discount_factor == 0.99

    def test_sigma_atm_derived(self):
        sd = SmileData.from_mid_vols(
            strikes=np.array([90.0, 100.0, 110.0]),
            ivs=np.array([0.25, 0.20, 0.22]),
            forward=100.0,
            expiry=0.5,
        )
        # ATM strike is 100.0, vol at 100 is 0.20
        assert sd.metadata.sigma_atm == pytest.approx(0.20)


class TestFromMidVolsValidation:
    def test_negative_iv(self):
        with pytest.raises(ValueError, match=r"positive|non-negative"):
            SmileData.from_mid_vols(strikes=[90, 100, 110], ivs=[0.25, -0.01, 0.22], forward=100.0, expiry=0.5)

    def test_non_positive_strike(self):
        with pytest.raises(ValueError, match="positive"):
            SmileData.from_mid_vols(strikes=[0, 100, 110], ivs=[0.25, 0.20, 0.22], forward=100.0, expiry=0.5)

    def test_fewer_than_three_points(self):
        with pytest.raises(ValueError, match="at least 3"):
            SmileData.from_mid_vols(strikes=[100, 110], ivs=[0.20, 0.22], forward=100.0, expiry=0.5)


class TestSmileDataValidation:
    def _meta(self) -> SmileMetadata:
        return SmileMetadata(forward=100.0, discount_factor=1.0, expiry=0.5)

    def test_fewer_than_three_points(self):
        with pytest.raises(ValueError, match="at least 3"):
            SmileData(
                x=np.array([90.0, 100.0]),
                y_bid=np.array([0.19, 0.18]),
                y_ask=np.array([0.21, 0.20]),
                x_coord=XCoord.FixedStrike,
                y_coord=YCoord.Volatility,
                metadata=self._meta(),
            )

    def test_exactly_three_points_accepted(self):
        sd = SmileData(
            x=np.array([90.0, 100.0, 110.0]),
            y_bid=np.array([0.19, 0.18, 0.20]),
            y_ask=np.array([0.21, 0.20, 0.22]),
            x_coord=XCoord.FixedStrike,
            y_coord=YCoord.Volatility,
            metadata=self._meta(),
        )
        assert len(sd.x) == 3

    def test_bid_exceeds_ask(self):
        with pytest.raises(ValueError, match="must not exceed"):
            SmileData(
                x=np.array([90.0, 100.0, 110.0]),
                y_bid=np.array([0.25, 0.20, 0.22]),
                y_ask=np.array([0.21, 0.20, 0.22]),
                x_coord=XCoord.FixedStrike,
                y_coord=YCoord.Volatility,
                metadata=self._meta(),
            )

    def test_non_positive_fixed_strike(self):
        with pytest.raises(ValueError, match="positive"):
            SmileData(
                x=np.array([0.0, 100.0, 110.0]),
                y_bid=np.array([0.19, 0.18, 0.20]),
                y_ask=np.array([0.21, 0.20, 0.22]),
                x_coord=XCoord.FixedStrike,
                y_coord=YCoord.Volatility,
                metadata=self._meta(),
            )

    def test_non_positive_moneyness_strike(self):
        with pytest.raises(ValueError, match="positive"):
            SmileData(
                x=np.array([0.0, 1.0, 1.1]),
                y_bid=np.array([0.19, 0.18, 0.20]),
                y_ask=np.array([0.21, 0.20, 0.22]),
                x_coord=XCoord.MoneynessStrike,
                y_coord=YCoord.Volatility,
                metadata=self._meta(),
            )

    def test_negative_volatility(self):
        with pytest.raises(ValueError, match="non-negative"):
            SmileData(
                x=np.array([90.0, 100.0, 110.0]),
                y_bid=np.array([-0.01, 0.18, 0.20]),
                y_ask=np.array([0.21, 0.20, 0.22]),
                x_coord=XCoord.FixedStrike,
                y_coord=YCoord.Volatility,
                metadata=self._meta(),
            )

    def test_negative_variance(self):
        with pytest.raises(ValueError, match="non-negative"):
            SmileData(
                x=np.array([-0.1, 0.0, 0.1]),
                y_bid=np.array([-0.01, 0.02, 0.02]),
                y_ask=np.array([0.02, 0.02, 0.02]),
                x_coord=XCoord.LogMoneynessStrike,
                y_coord=YCoord.Variance,
                metadata=self._meta(),
            )

    def test_negative_total_variance(self):
        with pytest.raises(ValueError, match="non-negative"):
            SmileData(
                x=np.array([-1.0, 0.0, 1.0]),
                y_bid=np.array([-0.01, 0.02, 0.02]),
                y_ask=np.array([0.02, 0.03, 0.03]),
                x_coord=XCoord.StandardisedStrike,
                y_coord=YCoord.TotalVariance,
                metadata=SmileMetadata(forward=1.0, discount_factor=1.0, expiry=0.5, sigma_atm=0.2),
            )

    def test_log_moneyness_allows_negative_x(self):
        """LogMoneynessStrike can have negative x values (OTM puts)."""
        sd = SmileData(
            x=np.array([-0.1, 0.0, 0.1]),
            y_bid=np.array([0.19, 0.18, 0.20]),
            y_ask=np.array([0.21, 0.20, 0.22]),
            x_coord=XCoord.LogMoneynessStrike,
            y_coord=YCoord.Volatility,
            metadata=self._meta(),
        )
        assert len(sd.x) == 3

    def test_price_allows_negative_y(self):
        """Price Y-coord does not enforce non-negativity (deep OTM edge cases)."""
        sd = SmileData(
            x=np.array([90.0, 100.0, 110.0]),
            y_bid=np.array([-0.01, 4.0, 0.5]),
            y_ask=np.array([0.01, 4.5, 0.8]),
            x_coord=XCoord.FixedStrike,
            y_coord=YCoord.Price,
            metadata=self._meta(),
        )
        assert len(sd.x) == 3
