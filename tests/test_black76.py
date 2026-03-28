"""Tests for qsmile.black76."""

from __future__ import annotations

import numpy as np
import pytest

from qsmile.black76 import black76_call, black76_implied_vol, black76_put


class TestBlack76Call:
    def test_atm_call(self):
        price = black76_call(100.0, 100.0, 1.0, 0.2, 1.0)
        # ATM Black76 call ≈ F * D * 2 * Phi(sigma*sqrt(T)/2) - 1 ≈ 7.97
        assert float(price) == pytest.approx(7.9656, rel=1e-3)

    def test_deep_itm_call(self):
        price = black76_call(100.0, 50.0, 1.0, 0.2, 1.0)
        assert float(price) == pytest.approx(50.0, rel=1e-2)

    def test_deep_otm_call(self):
        price = black76_call(100.0, 200.0, 1.0, 0.2, 1.0)
        assert float(price) < 0.01

    def test_zero_vol_call_itm(self):
        price = black76_call(100.0, 90.0, 1.0, 0.0, 1.0)
        assert float(price) == pytest.approx(10.0)

    def test_zero_vol_call_otm(self):
        price = black76_call(100.0, 110.0, 1.0, 0.0, 1.0)
        assert float(price) == pytest.approx(0.0)

    def test_vectorised(self):
        strikes = np.array([90.0, 100.0, 110.0])
        prices = black76_call(100.0, strikes, 1.0, 0.2, 1.0)
        assert prices.shape == (3,)
        assert prices[0] > prices[1] > prices[2]


class TestBlack76Put:
    def test_atm_put(self):
        price = black76_put(100.0, 100.0, 1.0, 0.2, 1.0)
        assert float(price) == pytest.approx(7.9656, rel=1e-3)

    def test_vectorised(self):
        strikes = np.array([90.0, 100.0, 110.0])
        prices = black76_put(100.0, strikes, 1.0, 0.2, 1.0)
        assert prices.shape == (3,)
        assert prices[2] > prices[1] > prices[0]


class TestPutCallParity:
    @pytest.mark.parametrize("strike", [80.0, 90.0, 100.0, 110.0, 120.0])
    def test_parity(self, strike):
        F, D, vol, T = 100.0, 0.95, 0.25, 0.5
        call = float(black76_call(F, strike, D, vol, T))
        put = float(black76_put(F, strike, D, vol, T))
        assert call - put == pytest.approx(D * (F - strike), abs=1e-10)


class TestBlack76Validation:
    def test_negative_forward(self):
        with pytest.raises(ValueError, match="forward must be positive"):
            black76_call(-1.0, 100.0, 1.0, 0.2, 1.0)

    def test_zero_strike(self):
        with pytest.raises(ValueError, match="strike must be positive"):
            black76_call(100.0, 0.0, 1.0, 0.2, 1.0)

    def test_negative_vol(self):
        with pytest.raises(ValueError, match="non-negative"):
            black76_call(100.0, 100.0, 1.0, -0.1, 1.0)

    def test_zero_expiry(self):
        with pytest.raises(ValueError, match="expiry must be positive"):
            black76_call(100.0, 100.0, 1.0, 0.2, 0.0)

    def test_negative_discount_factor(self):
        with pytest.raises(ValueError, match="discount_factor must be positive"):
            black76_call(100.0, 100.0, -1.0, 0.2, 1.0)


class TestBlack76ImpliedVol:
    @pytest.mark.parametrize("vol", [0.1, 0.2, 0.3, 0.5, 1.0])
    def test_call_round_trip(self, vol):
        F, K, D, T = 100.0, 105.0, 0.98, 0.5
        price = float(black76_call(F, K, D, vol, T))
        recovered = black76_implied_vol(price, F, K, D, T, is_call=True)
        assert recovered == pytest.approx(vol, abs=1e-8)

    @pytest.mark.parametrize("vol", [0.1, 0.2, 0.3, 0.5, 1.0])
    def test_put_round_trip(self, vol):
        F, K, D, T = 100.0, 95.0, 0.98, 0.5
        price = float(black76_put(F, K, D, vol, T))
        recovered = black76_implied_vol(price, F, K, D, T, is_call=False)
        assert recovered == pytest.approx(vol, abs=1e-8)

    def test_price_below_intrinsic(self):
        with pytest.raises(ValueError, match="below intrinsic"):
            black76_implied_vol(5.0, 100.0, 90.0, 1.0, 1.0, is_call=True)

    def test_price_above_upper_bound(self):
        with pytest.raises(ValueError, match="exceeds upper bound"):
            black76_implied_vol(110.0, 100.0, 100.0, 1.0, 1.0, is_call=True)

    def test_intrinsic_price_returns_zero_vol(self):
        intrinsic = 0.95 * max(100.0 - 90.0, 0.0)
        vol = black76_implied_vol(intrinsic, 100.0, 90.0, 0.95, 1.0, is_call=True)
        assert vol == pytest.approx(0.0, abs=1e-10)
