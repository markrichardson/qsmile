"""Tests for qsmile.prices."""

from __future__ import annotations

import numpy as np
import pytest

from qsmile.black76 import black76_call, black76_put
from qsmile.coords import XCoord, YCoord
from qsmile.prices import OptionChain, _calibrate_forward_df


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


class TestOptionChainConstruction:
    def test_from_arrays(self):
        data = _make_prices()
        chain = OptionChain(**data)
        assert isinstance(chain.strikes, np.ndarray)
        assert chain.forward == 100.0
        assert chain.discount_factor == 0.98

    def test_from_lists(self):
        data = _make_prices()
        chain = OptionChain(
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


class TestOptionChainValidation:
    def test_mismatched_lengths(self):
        data = _make_prices()
        with pytest.raises(ValueError, match="same length"):
            OptionChain(**{**data, "call_bid": data["call_bid"][:-1]})

    def test_non_positive_strikes(self):
        data = _make_prices()
        bad_strikes = data["strikes"].copy()
        bad_strikes[0] = 0.0
        with pytest.raises(ValueError, match="strikes must be positive"):
            OptionChain(**{**data, "strikes": bad_strikes})

    def test_negative_prices(self):
        data = _make_prices()
        bad = data["call_bid"].copy()
        bad[0] = -1.0
        with pytest.raises(ValueError, match="non-negative"):
            OptionChain(**{**data, "call_bid": bad})

    def test_bid_exceeds_ask(self):
        data = _make_prices()
        with pytest.raises(ValueError, match="must not exceed"):
            OptionChain(**{**data, "call_bid": data["call_ask"] + 1.0})

    def test_non_positive_expiry(self):
        data = _make_prices()
        with pytest.raises(ValueError, match="expiry must be positive"):
            OptionChain(**{**data, "expiry": 0.0})

    def test_fewer_than_three_strikes(self):
        with pytest.raises(ValueError, match="at least 3"):
            OptionChain(
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
        chain = OptionChain(
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
        chain = OptionChain(**data)
        expected = (data["call_bid"] + data["call_ask"]) / 2
        np.testing.assert_allclose(chain.call_mid, expected)

    def test_put_mid(self):
        data = _make_prices()
        chain = OptionChain(**data)
        expected = (data["put_bid"] + data["put_ask"]) / 2
        np.testing.assert_allclose(chain.put_mid, expected)


class TestToSmileDataPriceToVol:
    def test_price_to_vol_via_smile_data(self):
        data = _make_prices(vol=0.25, spread=0.01)
        chain = OptionChain(**data)
        sd = chain.to_smile_data()
        sd_vols = sd.transform(XCoord.FixedStrike, YCoord.Volatility)
        # Mid vols should be close to 0.25
        np.testing.assert_allclose(sd_vols.y_mid, 0.25, atol=0.002)
        # Spread should be preserved
        assert np.all(sd_vols.y_ask >= sd_vols.y_bid)


class TestDenoise:
    """Tests for OptionChain.denoise()."""

    def test_clean_data_unchanged(self):
        """Denoise on clean synthetic data should keep all strikes."""
        data = _make_prices()
        chain = OptionChain(**data)
        clean = chain.denoise()
        assert len(clean.strikes) == len(chain.strikes)
        np.testing.assert_array_equal(clean.strikes, chain.strikes)

    def test_returns_new_instance(self):
        """Denoise must return a new OptionChain, not mutate in place."""
        data = _make_prices()
        chain = OptionChain(**data)
        clean = chain.denoise()
        assert clean is not chain

    def test_removes_zero_bid_call(self):
        """Strikes where call bid is zero should be removed."""
        data = _make_prices()
        data["call_bid"][0] = 0.0
        data["call_ask"][0] = data["call_bid"][0] + 0.01
        chain = OptionChain(**data)
        clean = chain.denoise()
        assert data["strikes"][0] not in clean.strikes

    def test_removes_zero_bid_put(self):
        """Strikes where put bid is zero should be removed."""
        data = _make_prices()
        data["put_bid"][-1] = 0.0
        chain = OptionChain(**data)
        clean = chain.denoise()
        assert data["strikes"][-1] not in clean.strikes

    def test_removes_parity_violation(self):
        """Strikes where put-call parity is non-monotone should be removed."""
        data = _make_prices()
        OptionChain(**data)
        # Inflate a call mid in the middle to break parity monotonicity
        bad_idx = 3
        data2 = {k: v.copy() if isinstance(v, np.ndarray) else v for k, v in data.items()}
        data2["call_bid"][bad_idx] += 50.0
        data2["call_ask"][bad_idx] += 50.0
        chain2 = OptionChain(**data2)
        clean2 = chain2.denoise()
        assert data["strikes"][bad_idx] not in clean2.strikes

    def test_removes_non_monotone_call(self):
        """Strikes where call mid increases should be removed."""
        data = _make_prices()
        # Make call price at index 4 higher than at index 3
        data["call_bid"][4] = data["call_bid"][3] + 5.0
        data["call_ask"][4] = data["call_ask"][3] + 5.0
        chain = OptionChain(**data)
        clean = chain.denoise()
        assert data["strikes"][4] not in clean.strikes

    def test_monotonicity_after_denoise(self):
        """After denoise, all monotonicity properties must hold."""
        data = _make_prices()
        # Inject multiple kinds of noise
        data["call_bid"][1] += 20.0
        data["call_ask"][1] += 20.0
        data["put_bid"][-2] += 20.0
        data["put_ask"][-2] += 20.0
        chain = OptionChain(**data)
        clean = chain.denoise()
        parity = clean.call_mid - clean.put_mid
        assert np.all(np.diff(parity) <= 0), "parity not monotone"
        assert np.all(np.diff(clean.call_mid) <= 0), "call mid not monotone"
        assert np.all(np.diff(clean.put_mid) >= 0), "put mid not monotone"

    def test_recalibrates_forward(self):
        """The returned chain should have a freshly calibrated forward."""
        data = _make_prices()
        chain = OptionChain(**data)
        clean = chain.denoise()
        # Forward should still be approximately correct
        assert clean.forward == pytest.approx(data["forward"], rel=1e-2)

    def test_at_least_three_strikes_remain(self):
        """Denoise on a chain that's too noisy should still produce ≥3 strikes."""
        data = _make_prices()
        chain = OptionChain(**data)
        clean = chain.denoise()
        assert len(clean.strikes) >= 3

    def test_removes_parity_residual_outlier(self):
        """Strike whose C-P deviates far from D*(F-K) should be removed.

        This catches stale deep-ITM quotes whose bid-ask spread is tight
        but whose mid is biased (e.g. the K=4000 SPX pattern).
        """
        data = _make_prices()
        OptionChain(**data)
        # Inflate the lowest-strike call price so C-P >> D*(F-K) at that strike,
        # but keep the spread tight so the ratio is large.
        bad_idx = 0
        data2 = {k: v.copy() if isinstance(v, np.ndarray) else v for k, v in data.items()}
        # Add a large bias to both bid and ask (keeps spread unchanged)
        data2["call_bid"][bad_idx] += 10.0
        data2["call_ask"][bad_idx] += 10.0
        chain2 = OptionChain(**data2)
        clean2 = chain2.denoise()
        assert data["strikes"][bad_idx] not in clean2.strikes
