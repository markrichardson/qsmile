"""Tests for qsmile.chain."""

from __future__ import annotations

import numpy as np
import pytest

from qsmile.chain import OptionChain


class TestOptionChainConstruction:
    def test_from_arrays(self):
        strikes = np.array([90.0, 100.0, 110.0])
        ivs = np.array([0.25, 0.20, 0.22])
        chain = OptionChain(strikes=strikes, ivs=ivs, forward=100.0, expiry=0.5)
        np.testing.assert_array_equal(chain.strikes, strikes)
        np.testing.assert_array_equal(chain.ivs, ivs)
        assert chain.forward == 100.0
        assert chain.expiry == 0.5

    def test_from_lists(self):
        chain = OptionChain(strikes=[90, 100, 110], ivs=[0.25, 0.20, 0.22], forward=100.0, expiry=0.5)
        assert isinstance(chain.strikes, np.ndarray)
        assert isinstance(chain.ivs, np.ndarray)
        assert chain.strikes.dtype == np.float64


class TestOptionChainValidation:
    def test_mismatched_lengths(self):
        with pytest.raises(ValueError, match="same length"):
            OptionChain(strikes=[90, 100, 110], ivs=[0.25, 0.20], forward=100.0, expiry=0.5)

    def test_non_positive_forward(self):
        with pytest.raises(ValueError, match="forward must be positive"):
            OptionChain(strikes=[90, 100, 110], ivs=[0.25, 0.20, 0.22], forward=0.0, expiry=0.5)

    def test_negative_forward(self):
        with pytest.raises(ValueError, match="forward must be positive"):
            OptionChain(strikes=[90, 100, 110], ivs=[0.25, 0.20, 0.22], forward=-1.0, expiry=0.5)

    def test_non_positive_expiry(self):
        with pytest.raises(ValueError, match="expiry must be positive"):
            OptionChain(strikes=[90, 100, 110], ivs=[0.25, 0.20, 0.22], forward=100.0, expiry=0.0)

    def test_negative_expiry(self):
        with pytest.raises(ValueError, match="expiry must be positive"):
            OptionChain(strikes=[90, 100, 110], ivs=[0.25, 0.20, 0.22], forward=100.0, expiry=-0.5)

    def test_negative_iv(self):
        with pytest.raises(ValueError, match="non-negative"):
            OptionChain(strikes=[90, 100, 110], ivs=[0.25, -0.01, 0.22], forward=100.0, expiry=0.5)

    def test_non_positive_strike(self):
        with pytest.raises(ValueError, match="positive"):
            OptionChain(strikes=[0, 100, 110], ivs=[0.25, 0.20, 0.22], forward=100.0, expiry=0.5)

    def test_fewer_than_three_points(self):
        with pytest.raises(ValueError, match="at least 3"):
            OptionChain(strikes=[100, 110], ivs=[0.20, 0.22], forward=100.0, expiry=0.5)


class TestOptionChainProperties:
    def test_log_moneyness(self):
        chain = OptionChain(strikes=[90, 100, 110], ivs=[0.25, 0.20, 0.22], forward=100.0, expiry=0.5)
        expected = np.log(np.array([90.0, 100.0, 110.0]) / 100.0)
        np.testing.assert_allclose(chain.log_moneyness, expected)

    def test_total_variance(self):
        chain = OptionChain(strikes=[90, 100, 110], ivs=[0.25, 0.20, 0.22], forward=100.0, expiry=0.5)
        expected = np.array([0.25, 0.20, 0.22]) ** 2 * 0.5
        np.testing.assert_allclose(chain.total_variance, expected)
