"""Tests for qsmile.vols."""

from __future__ import annotations

import numpy as np
import pytest

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
    def test_to_unitised(self):
        vols = _make_vols()
        u = vols.to_unitised()
        # k_unitised = log(K/F) / (sigma_atm * sqrt(T))
        expected_k = vols.log_moneyness / (vols.sigma_atm * np.sqrt(vols.expiry))
        np.testing.assert_allclose(u.k_unitised, expected_k)
        # variance = vol^2 * T
        np.testing.assert_allclose(u.variance_bid, vols.vol_bid**2 * vols.expiry)
        np.testing.assert_allclose(u.variance_ask, vols.vol_ask**2 * vols.expiry)

    def test_to_option_chain(self):
        vols = _make_vols()
        chain = vols.to_option_chain()
        np.testing.assert_allclose(chain.ivs, vols.vol_mid)
        assert chain.forward == vols.forward
        assert chain.expiry == vols.expiry

    def test_to_prices_round_trip(self):
        vols = _make_vols()
        prices = vols.to_prices()
        vols2 = prices.to_vols()
        np.testing.assert_allclose(vols2.vol_mid, vols.vol_mid, atol=1e-6)

    def test_to_unitised_round_trip(self):
        vols = _make_vols()
        u = vols.to_unitised()
        vols2 = u.to_vols(forward=vols.forward, strikes=vols.strikes, discount_factor=vols.discount_factor)
        np.testing.assert_allclose(vols2.vol_mid, vols.vol_mid, atol=1e-10)
