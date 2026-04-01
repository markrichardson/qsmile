"""Tests for qsmile.vols."""

from __future__ import annotations

import numpy as np
import pytest

from qsmile.coords import XCoord, YCoord
from qsmile.vols import OptionChainVols


def _make_vols(
    forward: float = 100.0,
    discount_factor: float = 0.98,
    expiry: float = 0.5,
) -> OptionChainVols:
    """Create a sample OptionChainVols for testing."""
    strikes = np.array([85.0, 90.0, 95.0, 100.0, 105.0, 110.0, 115.0])
    # Typical smile shape
    vol_mid = np.array([0.28, 0.25, 0.22, 0.20, 0.21, 0.23, 0.26])
    spread = 0.005
    return OptionChainVols(
        strikes=strikes,
        vol_bid=vol_mid - spread,
        vol_ask=vol_mid + spread,
        forward=forward,
        discount_factor=discount_factor,
        expiry=expiry,
    )


class TestOptionChainVolsConstruction:
    def test_from_arrays(self):
        vols = _make_vols()
        assert isinstance(vols.strikes, np.ndarray)
        assert vols.forward == 100.0

    def test_from_lists(self):
        vols = OptionChainVols(
            strikes=[90.0, 100.0, 110.0],
            vol_bid=[0.19, 0.18, 0.20],
            vol_ask=[0.21, 0.20, 0.22],
            forward=100.0,
            discount_factor=1.0,
            expiry=0.5,
        )
        assert vols.strikes.dtype == np.float64


class TestOptionChainVolsValidation:
    def test_mismatched_lengths(self):
        with pytest.raises(ValueError, match="same length"):
            OptionChainVols(
                strikes=[90.0, 100.0, 110.0],
                vol_bid=[0.19, 0.18],
                vol_ask=[0.21, 0.20, 0.22],
                forward=100.0,
                discount_factor=1.0,
                expiry=0.5,
            )

    def test_negative_vol(self):
        with pytest.raises(ValueError, match="non-negative"):
            OptionChainVols(
                strikes=[90.0, 100.0, 110.0],
                vol_bid=[-0.01, 0.18, 0.20],
                vol_ask=[0.21, 0.20, 0.22],
                forward=100.0,
                discount_factor=1.0,
                expiry=0.5,
            )

    def test_bid_exceeds_ask(self):
        with pytest.raises(ValueError, match="must not exceed"):
            OptionChainVols(
                strikes=[90.0, 100.0, 110.0],
                vol_bid=[0.25, 0.20, 0.22],
                vol_ask=[0.21, 0.20, 0.22],
                forward=100.0,
                discount_factor=1.0,
                expiry=0.5,
            )

    def test_non_positive_forward(self):
        with pytest.raises(ValueError, match="forward must be positive"):
            OptionChainVols(
                strikes=[90.0, 100.0, 110.0],
                vol_bid=[0.19, 0.18, 0.20],
                vol_ask=[0.21, 0.20, 0.22],
                forward=0.0,
                discount_factor=1.0,
                expiry=0.5,
            )

    def test_non_positive_discount_factor(self):
        with pytest.raises(ValueError, match="discount_factor must be positive"):
            OptionChainVols(
                strikes=[90.0, 100.0, 110.0],
                vol_bid=[0.19, 0.18, 0.20],
                vol_ask=[0.21, 0.20, 0.22],
                forward=100.0,
                discount_factor=0.0,
                expiry=0.5,
            )

    def test_non_positive_expiry(self):
        with pytest.raises(ValueError, match="expiry must be positive"):
            OptionChainVols(
                strikes=[90.0, 100.0, 110.0],
                vol_bid=[0.19, 0.18, 0.20],
                vol_ask=[0.21, 0.20, 0.22],
                forward=100.0,
                discount_factor=1.0,
                expiry=0.0,
            )

    def test_fewer_than_three_strikes(self):
        with pytest.raises(ValueError, match="at least 3"):
            OptionChainVols(
                strikes=[90.0, 100.0],
                vol_bid=[0.19, 0.18],
                vol_ask=[0.21, 0.20],
                forward=100.0,
                discount_factor=1.0,
                expiry=0.5,
            )


class TestOptionChainVolsProperties:
    def test_vol_mid(self):
        vols = _make_vols()
        expected = (vols.vol_bid + vols.vol_ask) / 2
        np.testing.assert_allclose(vols.vol_mid, expected)

    def test_log_moneyness(self):
        vols = _make_vols()
        expected = np.log(vols.strikes / vols.forward)
        np.testing.assert_allclose(vols.log_moneyness, expected)

    def test_sigma_atm(self):
        vols = _make_vols(forward=100.0)
        # ATM strike is 100.0, vol_mid at that strike is 0.20
        assert vols.sigma_atm == pytest.approx(0.20, abs=1e-10)


class TestOptionChainVolsConversions:
    def test_to_unitised_via_smile_data(self):
        vols = _make_vols()
        sd = vols.to_smile_data()
        sd_u = sd.transform(XCoord.StandardisedStrike, YCoord.TotalVariance)
        # k_unitised = log(K/F) / (sigma_atm * sqrt(T))
        expected_k = vols.log_moneyness / (vols.sigma_atm * np.sqrt(vols.expiry))
        np.testing.assert_allclose(sd_u.x, expected_k)
        # variance = vol^2 * T
        np.testing.assert_allclose(sd_u.y_bid, vols.vol_bid**2 * vols.expiry)
        np.testing.assert_allclose(sd_u.y_ask, vols.vol_ask**2 * vols.expiry)

    def test_vol_price_round_trip_via_smile_data(self):
        vols = _make_vols()
        sd = vols.to_smile_data()
        sd_prices = sd.transform(XCoord.FixedStrike, YCoord.Price)
        sd_vols2 = sd_prices.transform(XCoord.FixedStrike, YCoord.Volatility)
        np.testing.assert_allclose(sd_vols2.y_mid, sd.y_mid, atol=1e-6)

    def test_unitised_round_trip_via_smile_data(self):
        vols = _make_vols()
        sd = vols.to_smile_data()
        sd_u = sd.transform(XCoord.StandardisedStrike, YCoord.TotalVariance)
        sd_back = sd_u.transform(XCoord.FixedStrike, YCoord.Volatility)
        np.testing.assert_allclose(sd_back.y_mid, sd.y_mid, atol=1e-10)
