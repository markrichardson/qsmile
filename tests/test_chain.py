"""Tests for OptionChainVols.from_mid_vols and total_variance."""

from __future__ import annotations

import numpy as np
import pytest

from qsmile.vols import OptionChainVols


class TestFromMidVolsConstruction:
    def test_from_arrays(self):
        strikes = np.array([90.0, 100.0, 110.0])
        ivs = np.array([0.25, 0.20, 0.22])
        chain = OptionChainVols.from_mid_vols(strikes=strikes, ivs=ivs, forward=100.0, expiry=0.5)
        np.testing.assert_array_equal(chain.strikes, strikes)
        np.testing.assert_array_equal(chain.vol_bid, ivs)
        np.testing.assert_array_equal(chain.vol_ask, ivs)
        assert chain.forward == 100.0
        assert chain.expiry == 0.5
        assert chain.discount_factor == 1.0

    def test_from_lists(self):
        chain = OptionChainVols.from_mid_vols(strikes=[90, 100, 110], ivs=[0.25, 0.20, 0.22], forward=100.0, expiry=0.5)
        assert isinstance(chain.strikes, np.ndarray)
        assert isinstance(chain.vol_bid, np.ndarray)
        assert chain.strikes.dtype == np.float64

    def test_custom_discount_factor(self):
        chain = OptionChainVols.from_mid_vols(
            strikes=[90, 100, 110], ivs=[0.25, 0.20, 0.22], forward=100.0, expiry=0.5, discount_factor=0.99
        )
        assert chain.discount_factor == 0.99


class TestFromMidVolsValidation:
    def test_mismatched_lengths(self):
        with pytest.raises(ValueError, match="same length"):
            OptionChainVols.from_mid_vols(strikes=[90, 100, 110], ivs=[0.25, 0.20], forward=100.0, expiry=0.5)

    def test_non_positive_forward(self):
        with pytest.raises(ValueError, match="forward must be positive"):
            OptionChainVols.from_mid_vols(strikes=[90, 100, 110], ivs=[0.25, 0.20, 0.22], forward=0.0, expiry=0.5)

    def test_negative_forward(self):
        with pytest.raises(ValueError, match="forward must be positive"):
            OptionChainVols.from_mid_vols(strikes=[90, 100, 110], ivs=[0.25, 0.20, 0.22], forward=-1.0, expiry=0.5)

    def test_non_positive_expiry(self):
        with pytest.raises(ValueError, match="expiry must be positive"):
            OptionChainVols.from_mid_vols(strikes=[90, 100, 110], ivs=[0.25, 0.20, 0.22], forward=100.0, expiry=0.0)

    def test_negative_expiry(self):
        with pytest.raises(ValueError, match="expiry must be positive"):
            OptionChainVols.from_mid_vols(strikes=[90, 100, 110], ivs=[0.25, 0.20, 0.22], forward=100.0, expiry=-0.5)

    def test_negative_iv(self):
        with pytest.raises(ValueError, match="non-negative"):
            OptionChainVols.from_mid_vols(strikes=[90, 100, 110], ivs=[0.25, -0.01, 0.22], forward=100.0, expiry=0.5)

    def test_non_positive_strike(self):
        with pytest.raises(ValueError, match="positive"):
            OptionChainVols.from_mid_vols(strikes=[0, 100, 110], ivs=[0.25, 0.20, 0.22], forward=100.0, expiry=0.5)

    def test_fewer_than_three_points(self):
        with pytest.raises(ValueError, match="at least 3"):
            OptionChainVols.from_mid_vols(strikes=[100, 110], ivs=[0.20, 0.22], forward=100.0, expiry=0.5)


class TestOptionChainVolsProperties:
    def test_log_moneyness(self):
        chain = OptionChainVols.from_mid_vols(strikes=[90, 100, 110], ivs=[0.25, 0.20, 0.22], forward=100.0, expiry=0.5)
        expected = np.log(np.array([90.0, 100.0, 110.0]) / 100.0)
        np.testing.assert_allclose(chain.log_moneyness, expected)

    def test_total_variance(self):
        chain = OptionChainVols.from_mid_vols(strikes=[90, 100, 110], ivs=[0.25, 0.20, 0.22], forward=100.0, expiry=0.5)
        expected = np.array([0.25, 0.20, 0.22]) ** 2 * 0.5
        np.testing.assert_allclose(chain.total_variance, expected)

    def test_vol_mid_equals_input(self):
        ivs = np.array([0.25, 0.20, 0.22])
        chain = OptionChainVols.from_mid_vols(strikes=[90, 100, 110], ivs=ivs, forward=100.0, expiry=0.5)
        np.testing.assert_allclose(chain.vol_mid, ivs)
