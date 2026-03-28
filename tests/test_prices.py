"""Tests for qsmile.prices."""

from __future__ import annotations

import numpy as np
import pytest

from qsmile.black76 import black76_call, black76_put
from qsmile.prices import OptionChainPrices, _calibrate_forward_df


def _make_prices(
    forward: float = 100.0,
    discount_factor: float = 0.98,
    vol: float = 0.2,
    expiry: float = 0.5,
    spread: float = 0.005,
) -> dict:
    """Generate synthetic bid/ask prices from known parameters."""
    strikes = np.array([85.0, 90.0, 95.0, 100.0, 105.0, 110.0, 115.0])
    vols = np.full_like(strikes, vol)
    vol_bid = vols - spread
    vol_ask = vols + spread

    call_bid = np.array(
        [float(black76_call(forward, K, discount_factor, vb, expiry)) for K, vb in zip(strikes, vol_bid, strict=False)]
    )
    call_ask = np.array(
        [float(black76_call(forward, K, discount_factor, va, expiry)) for K, va in zip(strikes, vol_ask, strict=False)]
    )
    put_bid = np.array(
        [float(black76_put(forward, K, discount_factor, vb, expiry)) for K, vb in zip(strikes, vol_bid, strict=False)]
    )
    put_ask = np.array(
        [float(black76_put(forward, K, discount_factor, va, expiry)) for K, va in zip(strikes, vol_ask, strict=False)]
    )

    return {
        "strikes": strikes,
        "call_bid": call_bid,
        "call_ask": call_ask,
        "put_bid": put_bid,
        "put_ask": put_ask,
        "expiry": expiry,
        "forward": forward,
        "discount_factor": discount_factor,
    }


class TestOptionChainPricesConstruction:
    def test_from_arrays(self):
        data = _make_prices()
        chain = OptionChainPrices(**data)
        assert isinstance(chain.strikes, np.ndarray)
        assert chain.forward == 100.0
        assert chain.discount_factor == 0.98

    def test_from_lists(self):
        data = _make_prices()
        chain = OptionChainPrices(
            strikes=list(data["strikes"]),
            call_bid=list(data["call_bid"]),
            call_ask=list(data["call_ask"]),
            put_bid=list(data["put_bid"]),
            put_ask=list(data["put_ask"]),
            expiry=data["expiry"],
            forward=data["forward"],
            discount_factor=data["discount_factor"],
        )
        assert chain.strikes.dtype == np.float64


class TestOptionChainPricesValidation:
    def test_mismatched_lengths(self):
        data = _make_prices()
        with pytest.raises(ValueError, match="same length"):
            OptionChainPrices(**{**data, "call_bid": data["call_bid"][:-1]})

    def test_non_positive_strikes(self):
        data = _make_prices()
        bad_strikes = data["strikes"].copy()
        bad_strikes[0] = 0.0
        with pytest.raises(ValueError, match="strikes must be positive"):
            OptionChainPrices(**{**data, "strikes": bad_strikes})

    def test_negative_prices(self):
        data = _make_prices()
        bad = data["call_bid"].copy()
        bad[0] = -1.0
        with pytest.raises(ValueError, match="non-negative"):
            OptionChainPrices(**{**data, "call_bid": bad})

    def test_bid_exceeds_ask(self):
        data = _make_prices()
        with pytest.raises(ValueError, match="must not exceed"):
            OptionChainPrices(**{**data, "call_bid": data["call_ask"] + 1.0})

    def test_non_positive_expiry(self):
        data = _make_prices()
        with pytest.raises(ValueError, match="expiry must be positive"):
            OptionChainPrices(**{**data, "expiry": 0.0})

    def test_fewer_than_three_strikes(self):
        with pytest.raises(ValueError, match="at least 3"):
            OptionChainPrices(
                strikes=[100.0, 110.0],
                call_bid=[5.0, 2.0],
                call_ask=[6.0, 3.0],
                put_bid=[2.0, 5.0],
                put_ask=[3.0, 6.0],
                expiry=0.5,
                forward=100.0,
                discount_factor=1.0,
            )


class TestCalibration:
    def test_calibrated_forward_accuracy(self):
        data = _make_prices(forward=100.0, discount_factor=0.98)
        F_cal, D_cal = _calibrate_forward_df(
            data["strikes"],
            (data["call_bid"] + data["call_ask"]) / 2,
            (data["put_bid"] + data["put_ask"]) / 2,
        )
        assert F_cal == pytest.approx(100.0, rel=1e-3)
        assert D_cal == pytest.approx(0.98, rel=1e-2)

    def test_calibrated_values_positive(self):
        data = _make_prices()
        F_cal, D_cal = _calibrate_forward_df(
            data["strikes"],
            (data["call_bid"] + data["call_ask"]) / 2,
            (data["put_bid"] + data["put_ask"]) / 2,
        )
        assert F_cal > 0
        assert 0 < D_cal <= 1.0

    def test_auto_calibration_on_construction(self):
        data = _make_prices(forward=100.0, discount_factor=0.98)
        chain = OptionChainPrices(
            strikes=data["strikes"],
            call_bid=data["call_bid"],
            call_ask=data["call_ask"],
            put_bid=data["put_bid"],
            put_ask=data["put_ask"],
            expiry=data["expiry"],
        )
        assert chain.forward == pytest.approx(100.0, rel=1e-3)
        assert chain.discount_factor == pytest.approx(0.98, rel=1e-2)


class TestMidPrices:
    def test_call_mid(self):
        data = _make_prices()
        chain = OptionChainPrices(**data)
        expected = (data["call_bid"] + data["call_ask"]) / 2
        np.testing.assert_allclose(chain.call_mid, expected)

    def test_put_mid(self):
        data = _make_prices()
        chain = OptionChainPrices(**data)
        expected = (data["put_bid"] + data["put_ask"]) / 2
        np.testing.assert_allclose(chain.put_mid, expected)


class TestToVols:
    def test_price_to_vol_round_trip(self):
        data = _make_prices(vol=0.25, spread=0.01)
        chain = OptionChainPrices(**data)
        vols = chain.to_vols()
        # Mid vols should be close to 0.25
        np.testing.assert_allclose(vols.vol_mid, 0.25, atol=0.002)
        # Spread should be preserved
        assert np.all(vols.vol_ask >= vols.vol_bid)
