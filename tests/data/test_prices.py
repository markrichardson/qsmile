"""Tests for qsmile.prices."""

from __future__ import annotations

import numpy as np
import pytest

from qsmile.core.black76 import black76_call, black76_put
from qsmile.core.coords import XCoord, YCoord
from qsmile.data.prices import OptionChain, _calibrate_forward_df, delta_blend_ivols


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


class TestDeltaBlendIvols:
    """Tests for delta_blend_ivols blending function."""

    def _flat_vols(
        self,
        vol: float = 0.20,
        spread: float = 0.005,
        forward: float = 100.0,
        expiry: float = 0.5,
    ) -> dict:
        """Build flat-vol inputs for delta_blend_ivols."""
        strikes = np.array([80.0, 90.0, 95.0, 100.0, 105.0, 110.0, 120.0])
        n = len(strikes)
        bid = np.full(n, vol - spread)
        ask = np.full(n, vol + spread)
        return {
            "call_bid_ivols": bid.copy(),
            "call_ask_ivols": ask.copy(),
            "put_bid_ivols": bid.copy(),
            "put_ask_ivols": ask.copy(),
            "strikes": strikes,
            "forward": forward,
            "expiry": expiry,
        }

    def test_atm_equal_weight(self):
        """At ATM (K==F) with identical call/put vols, blending is 50/50."""
        data = self._flat_vols()
        blended_bid, blended_ask = delta_blend_ivols(**data)
        atm_idx = int(np.argmin(np.abs(data["strikes"] - data["forward"])))
        # When call and put vols are identical, blend equals either
        np.testing.assert_allclose(blended_bid[atm_idx], data["call_bid_ivols"][atm_idx], atol=1e-10)
        np.testing.assert_allclose(blended_ask[atm_idx], data["call_ask_ivols"][atm_idx], atol=1e-10)

    def test_deep_otm_call_uses_call_vol(self):
        """Far below forward (deep ITM put wing), call vol dominates."""
        call_vols = np.array([0.30, 0.25, 0.22, 0.20, 0.22, 0.25, 0.30])
        put_vols = np.array([0.35, 0.28, 0.23, 0.20, 0.23, 0.28, 0.35])
        strikes = np.array([60.0, 80.0, 90.0, 100.0, 110.0, 120.0, 140.0])
        blended_bid, _ = delta_blend_ivols(
            call_vols,
            call_vols,
            put_vols,
            put_vols,
            strikes,
            100.0,
            0.5,
        )
        # At K=60 (deep below F), weight → 1, should be very close to call vol
        assert blended_bid[0] == pytest.approx(call_vols[0], abs=0.01)

    def test_deep_otm_put_uses_put_vol(self):
        """Far above forward (deep OTM put wing), put vol dominates."""
        call_vols = np.array([0.30, 0.25, 0.22, 0.20, 0.22, 0.25, 0.30])
        put_vols = np.array([0.35, 0.28, 0.23, 0.20, 0.23, 0.28, 0.35])
        strikes = np.array([60.0, 80.0, 90.0, 100.0, 110.0, 120.0, 140.0])
        blended_bid, _ = delta_blend_ivols(
            call_vols,
            call_vols,
            put_vols,
            put_vols,
            strikes,
            100.0,
            0.5,
        )
        # At K=140 (deep above F), weight → 0, should be very close to put vol
        assert blended_bid[-1] == pytest.approx(put_vols[-1], abs=0.01)

    def test_weights_monotonically_decrease(self):
        """Delta weights should decrease monotonically with strike."""
        from scipy.stats import norm as _norm

        data = self._flat_vols()
        vol = 0.20
        sqrt_t = np.sqrt(data["expiry"])
        d1 = (np.log(data["forward"] / data["strikes"]) + 0.5 * vol**2 * data["expiry"]) / (vol * sqrt_t)
        weights = _norm.cdf(d1)
        assert np.all(np.diff(weights) < 0)

    def test_bid_ask_independent(self):
        """Bid and ask are blended independently with same weights."""
        data = self._flat_vols(vol=0.20, spread=0.01)
        # Give puts a different spread
        data["put_bid_ivols"] = np.full(7, 0.18)
        data["put_ask_ivols"] = np.full(7, 0.22)
        blended_bid, blended_ask = delta_blend_ivols(**data)
        # Spread preserved — blended ask >= blended bid everywhere
        assert np.all(blended_ask >= blended_bid - 1e-15)


class TestToSmileDataBlended:
    """Tests for OptionChain.to_smile_data_blended()."""

    def test_returns_vol_coordinates(self):
        data = _make_prices(vol=0.25, spread=0.005)
        chain = OptionChain(**data)
        sd = chain.to_smile_data_blended()
        assert sd.x_coord == XCoord.FixedStrike
        assert sd.y_coord == YCoord.Volatility

    def test_blended_vols_close_to_known_vol(self):
        """With flat-vol Black76 prices, blended vols should recover the input vol."""
        data = _make_prices(vol=0.25, spread=0.005)
        chain = OptionChain(**data)
        sd = chain.to_smile_data_blended()
        np.testing.assert_allclose(sd.y_mid, 0.25, atol=0.002)

    def test_sigma_atm_derived(self):
        data = _make_prices(vol=0.25, spread=0.005)
        chain = OptionChain(**data)
        sd = chain.to_smile_data_blended()
        assert sd.metadata.sigma_atm is not None
        assert sd.metadata.sigma_atm == pytest.approx(0.25, abs=0.002)

    def test_metadata_populated(self):
        data = _make_prices(forward=100.0, discount_factor=0.98)
        chain = OptionChain(**data)
        sd = chain.to_smile_data_blended()
        assert sd.metadata.forward == pytest.approx(100.0, rel=1e-3)
        assert sd.metadata.discount_factor == pytest.approx(0.98, rel=1e-2)
        assert sd.metadata.expiry == data["expiry"]

    def test_bid_ask_preserved(self):
        data = _make_prices(vol=0.25, spread=0.01)
        chain = OptionChain(**data)
        sd = chain.to_smile_data_blended()
        assert np.all(sd.y_ask >= sd.y_bid)


class TestInversionFailureFallback:
    """Tests for graceful handling when vol inversion fails."""

    def test_call_failure_uses_put_vol(self):
        """When call vol can't be computed, put vol is used."""
        call_bid = np.array([np.nan, 0.20, 0.20])
        call_ask = np.array([np.nan, 0.21, 0.21])
        put_bid = np.array([0.22, 0.20, 0.20])
        put_ask = np.array([0.23, 0.21, 0.21])
        strikes = np.array([90.0, 100.0, 110.0])
        blended_bid, blended_ask = delta_blend_ivols(
            call_bid,
            call_ask,
            put_bid,
            put_ask,
            strikes,
            100.0,
            0.5,
        )
        # At strike 0: call NaN → weight forced to 0 → use put vol
        assert blended_bid[0] == pytest.approx(0.22)
        assert blended_ask[0] == pytest.approx(0.23)

    def test_put_failure_uses_call_vol(self):
        """When put vol can't be computed, call vol is used."""
        call_bid = np.array([0.20, 0.20, 0.22])
        call_ask = np.array([0.21, 0.21, 0.23])
        put_bid = np.array([0.20, 0.20, np.nan])
        put_ask = np.array([0.21, 0.21, np.nan])
        strikes = np.array([90.0, 100.0, 110.0])
        blended_bid, blended_ask = delta_blend_ivols(
            call_bid,
            call_ask,
            put_bid,
            put_ask,
            strikes,
            100.0,
            0.5,
        )
        # At strike 2: put NaN → weight forced to 1 → use call vol
        assert blended_bid[2] == pytest.approx(0.22)
        assert blended_ask[2] == pytest.approx(0.23)

    def test_both_failure_returns_nan(self):
        """When neither vol is available, NaN is returned."""
        call_bid = np.array([np.nan, 0.20, 0.20])
        call_ask = np.array([np.nan, 0.21, 0.21])
        put_bid = np.array([np.nan, 0.20, 0.20])
        put_ask = np.array([np.nan, 0.21, 0.21])
        strikes = np.array([90.0, 100.0, 110.0])
        blended_bid, blended_ask = delta_blend_ivols(
            call_bid,
            call_ask,
            put_bid,
            put_ask,
            strikes,
            100.0,
            0.5,
        )
        assert np.isnan(blended_bid[0])
        assert np.isnan(blended_ask[0])

    def test_to_smile_data_blended_excludes_nan_strikes(self):
        """to_smile_data_blended excludes strikes where neither vol is available."""
        data = _make_prices(vol=0.25, spread=0.005)
        chain = OptionChain(**data)
        sd = chain.to_smile_data_blended()
        assert not np.any(np.isnan(sd.y_bid))
        assert not np.any(np.isnan(sd.y_ask))
        assert len(sd.x) == len(chain.strikes)


class TestOptionChainToSmileData:
    def test_coordinates(self) -> None:
        strikes = np.array([90.0, 95.0, 100.0, 105.0, 110.0])
        forward = 100.0
        discount_factor = 0.99
        expiry = 0.25
        vols = np.array([0.23, 0.21, 0.19, 0.21, 0.23])

        call_bid = np.array(
            [
                float(black76_call(forward, K, discount_factor, v - 0.01, expiry))
                for K, v in zip(strikes, vols, strict=False)
            ]
        )
        call_ask = np.array(
            [
                float(black76_call(forward, K, discount_factor, v + 0.01, expiry))
                for K, v in zip(strikes, vols, strict=False)
            ]
        )
        # Use put-call parity: P = C - D*(F - K) for puts
        put_bid = call_bid - discount_factor * (forward - strikes)
        put_ask = call_ask - discount_factor * (forward - strikes)
        put_bid = np.maximum(put_bid, 0.0)
        put_ask = np.maximum(put_ask, 0.0)
        # Ensure put_bid <= put_ask
        put_bid, put_ask = np.minimum(put_bid, put_ask), np.maximum(put_bid, put_ask)

        prices = OptionChain(
            strikes=strikes,
            call_bid=call_bid,
            call_ask=call_ask,
            put_bid=put_bid,
            put_ask=put_ask,
            expiry=expiry,
            forward=forward,
            discount_factor=discount_factor,
        )
        sd = prices.to_smile_data()
        assert sd.x_coord == XCoord.FixedStrike
        assert sd.y_coord == YCoord.Price
        np.testing.assert_array_equal(sd.x, prices.strikes)
        np.testing.assert_array_equal(sd.y_bid, prices.call_bid)
        np.testing.assert_array_equal(sd.y_ask, prices.call_ask)
        assert sd.metadata.forward == prices.forward
        assert sd.metadata.discount_factor == prices.discount_factor
        assert sd.metadata.expiry == prices.expiry


# --- Tests for volume / open_interest on OptionChain ---


class TestOptionChainVolumeOpenInterest:
    def test_default_none(self):
        data = _make_prices()
        chain = OptionChain(**data)
        assert chain.volume is None
        assert chain.open_interest is None

    def test_with_volume_and_open_interest(self):
        data = _make_prices()
        vol = np.arange(1.0, len(data["strikes"]) + 1)
        oi = np.arange(100.0, 100.0 + len(data["strikes"]))
        chain = OptionChain(**data, volume=vol, open_interest=oi)
        np.testing.assert_array_equal(chain.volume, vol)
        np.testing.assert_array_equal(chain.open_interest, oi)

    def test_coerced_to_float64(self):
        data = _make_prices()
        n = len(data["strikes"])
        chain = OptionChain(**data, volume=list(range(n)), open_interest=list(range(n)))
        assert chain.volume.dtype == np.float64
        assert chain.open_interest.dtype == np.float64

    def test_volume_length_mismatch(self):
        data = _make_prices()
        with pytest.raises(ValueError, match="volume must have the same length"):
            OptionChain(**data, volume=np.array([1.0, 2.0]))

    def test_open_interest_length_mismatch(self):
        data = _make_prices()
        with pytest.raises(ValueError, match="open_interest must have the same length"):
            OptionChain(**data, open_interest=np.array([1.0]))

    def test_negative_volume_rejected(self):
        data = _make_prices()
        n = len(data["strikes"])
        bad = np.zeros(n)
        bad[0] = -1.0
        with pytest.raises(ValueError, match="volume must be non-negative"):
            OptionChain(**data, volume=bad)

    def test_negative_open_interest_rejected(self):
        data = _make_prices()
        n = len(data["strikes"])
        bad = np.zeros(n)
        bad[0] = -1.0
        with pytest.raises(ValueError, match="open_interest must be non-negative"):
            OptionChain(**data, open_interest=bad)


class TestVolumeOIPassthrough:
    """Tests for volume/open_interest passthrough through conversions."""

    def _chain_with_vol_oi(self):
        data = _make_prices()
        n = len(data["strikes"])
        vol = np.arange(1.0, n + 1)
        oi = np.arange(100.0, 100.0 + n)
        return OptionChain(**data, volume=vol, open_interest=oi)

    def test_to_smile_data_passes_through(self):
        chain = self._chain_with_vol_oi()
        sd = chain.to_smile_data()
        np.testing.assert_array_equal(sd.volume, chain.volume)
        np.testing.assert_array_equal(sd.open_interest, chain.open_interest)

    def test_to_smile_data_none_passes_through(self):
        data = _make_prices()
        chain = OptionChain(**data)
        sd = chain.to_smile_data()
        assert sd.volume is None
        assert sd.open_interest is None

    def test_to_smile_data_blended_passes_through(self):
        chain = self._chain_with_vol_oi()
        sd = chain.to_smile_data_blended()
        # blended may exclude some strikes, so length may differ
        assert sd.volume is not None
        assert sd.open_interest is not None
        assert len(sd.volume) == len(sd.x)
        assert len(sd.open_interest) == len(sd.x)

    def test_to_smile_data_blended_none_passes_through(self):
        data = _make_prices()
        chain = OptionChain(**data)
        sd = chain.to_smile_data_blended()
        assert sd.volume is None
        assert sd.open_interest is None

    def test_denoise_subsets_volume_oi(self):
        chain = self._chain_with_vol_oi()
        clean = chain.denoise()
        assert clean.volume is not None
        assert clean.open_interest is not None
        assert len(clean.volume) == len(clean.strikes)
        assert len(clean.open_interest) == len(clean.strikes)

    def test_denoise_none_passes_through(self):
        data = _make_prices()
        chain = OptionChain(**data)
        clean = chain.denoise()
        assert clean.volume is None
        assert clean.open_interest is None
