"""Tests for SmileData with volatility coordinates (replaces OptionChainVols tests)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from qsmile.core.coords import XCoord, YCoord
from qsmile.data.meta import SmileMetadata
from qsmile.data.vols import SmileData


def _make_vol_smile_data(
    forward: float = 100.0,
    discount_factor: float = 0.98,
) -> SmileData:
    """Create a sample SmileData in (FixedStrike, Volatility) coords."""
    strikes = np.array([85.0, 90.0, 95.0, 100.0, 105.0, 110.0, 115.0])
    vol_mid = np.array([0.28, 0.25, 0.22, 0.20, 0.21, 0.23, 0.26])
    spread = 0.005
    atm_idx = int(np.argmin(np.abs(strikes - forward)))
    sigma_atm = float(vol_mid[atm_idx])
    return SmileData(
        x=strikes,
        y_bid=vol_mid - spread,
        y_ask=vol_mid + spread,
        x_coord=XCoord.FixedStrike,
        y_coord=YCoord.Volatility,
        metadata=SmileMetadata(
            date=pd.Timestamp("2024-01-01"),
            expiry=pd.Timestamp("2024-07-01"),
            forward=forward,
            discount_factor=discount_factor,
            sigma_atm=sigma_atm,
        ),
    )


class TestVolSmileDataProperties:
    def test_y_mid(self):
        sd = _make_vol_smile_data()
        expected = (sd.y_bid + sd.y_ask) / 2
        np.testing.assert_allclose(sd.y_mid, expected)

    def test_sigma_atm(self):
        sd = _make_vol_smile_data(forward=100.0)
        assert sd.metadata.sigma_atm == 0.20


class TestVolSmileDataConversions:
    def test_to_unitised_via_transform(self):
        sd = _make_vol_smile_data()
        sd_u = sd.transform(XCoord.StandardisedStrike, YCoord.TotalVariance)
        log_m = np.log(sd.x / sd.metadata.forward)
        expected_k = log_m / (sd.metadata.sigma_atm * np.sqrt(sd.metadata.texpiry))
        np.testing.assert_allclose(sd_u.x, expected_k)
        np.testing.assert_allclose(sd_u.y_bid, sd.y_bid**2 * sd.metadata.texpiry)
        np.testing.assert_allclose(sd_u.y_ask, sd.y_ask**2 * sd.metadata.texpiry)

    def test_vol_price_round_trip(self):
        sd = _make_vol_smile_data()
        sd_prices = sd.transform(XCoord.FixedStrike, YCoord.Price)
        sd_vols2 = sd_prices.transform(XCoord.FixedStrike, YCoord.Volatility)
        np.testing.assert_allclose(sd_vols2.y_mid, sd.y_mid, atol=1e-6)

    def test_unitised_round_trip(self):
        sd = _make_vol_smile_data()
        sd_u = sd.transform(XCoord.StandardisedStrike, YCoord.TotalVariance)
        sd_back = sd_u.transform(XCoord.FixedStrike, YCoord.Volatility)
        np.testing.assert_allclose(sd_back.y_mid, sd.y_mid, atol=1e-10)


# --- Tests merged from test_chain.py ---

META = SmileMetadata(
    date=pd.Timestamp("2024-01-01"),
    expiry=pd.Timestamp("2024-04-01"),
    forward=100.0,
    discount_factor=0.99,
    sigma_atm=0.20,
)
STRIKES = np.array([90.0, 95.0, 100.0, 105.0, 110.0])
VOLS_BID = np.array([0.22, 0.20, 0.18, 0.20, 0.22])
VOLS_ASK = np.array([0.24, 0.22, 0.20, 0.22, 0.24])


class TestFromMidVolsConstruction:
    def test_from_arrays(self):
        strikes = np.array([90.0, 100.0, 110.0])
        ivs = np.array([0.25, 0.20, 0.22])
        sd = SmileData.from_mid_vols(
            strikes=strikes, ivs=ivs, forward=100.0, date=pd.Timestamp("2024-01-01"), expiry=pd.Timestamp("2024-07-01")
        )
        np.testing.assert_array_equal(sd.x, strikes)
        np.testing.assert_array_equal(sd.y_bid, ivs)
        np.testing.assert_array_equal(sd.y_ask, ivs)
        assert sd.x_coord == XCoord.FixedStrike
        assert sd.y_coord == YCoord.Volatility
        assert sd.metadata.forward == 100.0
        assert sd.metadata.expiry == pd.Timestamp("2024-07-01")
        assert sd.metadata.discount_factor == 1.0

    def test_from_lists(self):
        sd = SmileData.from_mid_vols(
            strikes=[90, 100, 110],
            ivs=[0.25, 0.20, 0.22],
            forward=100.0,
            date=pd.Timestamp("2024-01-01"),
            expiry=pd.Timestamp("2024-07-01"),
        )
        assert isinstance(sd.x, np.ndarray)
        assert isinstance(sd.y_bid, np.ndarray)
        assert sd.x.dtype == np.float64

    def test_custom_discount_factor(self):
        sd = SmileData.from_mid_vols(
            strikes=[90, 100, 110],
            ivs=[0.25, 0.20, 0.22],
            forward=100.0,
            date=pd.Timestamp("2024-01-01"),
            expiry=pd.Timestamp("2024-07-01"),
            discount_factor=0.99,
        )
        assert sd.metadata.discount_factor == 0.99

    def test_sigma_atm_derived(self):
        sd = SmileData.from_mid_vols(
            strikes=np.array([90.0, 100.0, 110.0]),
            ivs=np.array([0.25, 0.20, 0.22]),
            forward=100.0,
            date=pd.Timestamp("2024-01-01"),
            expiry=pd.Timestamp("2024-07-01"),
        )
        # ATM strike is 100.0, vol at 100 is 0.20
        assert sd.metadata.sigma_atm == pytest.approx(0.20)


class TestFromMidVolsValidation:
    def test_negative_iv(self):
        with pytest.raises(ValueError, match=r"positive|non-negative"):
            SmileData.from_mid_vols(
                strikes=[90, 100, 110],
                ivs=[0.25, -0.01, 0.22],
                forward=100.0,
                date=pd.Timestamp("2024-01-01"),
                expiry=pd.Timestamp("2024-07-01"),
            )

    def test_non_positive_strike(self):
        with pytest.raises(ValueError, match="positive"):
            SmileData.from_mid_vols(
                strikes=[0, 100, 110],
                ivs=[0.25, 0.20, 0.22],
                forward=100.0,
                date=pd.Timestamp("2024-01-01"),
                expiry=pd.Timestamp("2024-07-01"),
            )

    def test_fewer_than_three_points(self):
        with pytest.raises(ValueError, match="at least 3"):
            SmileData.from_mid_vols(
                strikes=[100, 110],
                ivs=[0.20, 0.22],
                forward=100.0,
                date=pd.Timestamp("2024-01-01"),
                expiry=pd.Timestamp("2024-07-01"),
            )


class TestSmileDataValidation:
    def _meta(self) -> SmileMetadata:
        return SmileMetadata(
            date=pd.Timestamp("2024-01-01"), expiry=pd.Timestamp("2024-07-01"), forward=100.0, discount_factor=1.0
        )

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
                metadata=SmileMetadata(
                    date=pd.Timestamp("2024-01-01"),
                    expiry=pd.Timestamp("2024-07-01"),
                    forward=1.0,
                    discount_factor=1.0,
                    sigma_atm=0.2,
                ),
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


# --- Tests merged from test_smile_data.py ---


class TestSmileDataConstruction:
    def test_valid_construction(self) -> None:
        sd = SmileData(
            x=STRIKES,
            y_bid=VOLS_BID,
            y_ask=VOLS_ASK,
            x_coord=XCoord.FixedStrike,
            y_coord=YCoord.Volatility,
            metadata=META,
        )
        assert sd.x_coord == XCoord.FixedStrike
        assert sd.y_coord == YCoord.Volatility
        assert len(sd.x) == 5

    def test_mismatched_lengths(self) -> None:
        with pytest.raises(ValueError, match="same length"):
            SmileData(
                x=STRIKES,
                y_bid=VOLS_BID[:3],
                y_ask=VOLS_ASK,
                x_coord=XCoord.FixedStrike,
                y_coord=YCoord.Volatility,
                metadata=META,
            )

    def test_y_mid(self) -> None:
        sd = SmileData(
            x=STRIKES,
            y_bid=VOLS_BID,
            y_ask=VOLS_ASK,
            x_coord=XCoord.FixedStrike,
            y_coord=YCoord.Volatility,
            metadata=META,
        )
        np.testing.assert_allclose(sd.y_mid, (VOLS_BID + VOLS_ASK) / 2.0)


class TestSmileDataTransform:
    def test_identity(self) -> None:
        sd = SmileData(
            x=STRIKES,
            y_bid=VOLS_BID,
            y_ask=VOLS_ASK,
            x_coord=XCoord.FixedStrike,
            y_coord=YCoord.Volatility,
            metadata=META,
        )
        result = sd.transform(XCoord.FixedStrike, YCoord.Volatility)
        np.testing.assert_allclose(result.x, STRIKES)
        np.testing.assert_allclose(result.y_bid, VOLS_BID)
        np.testing.assert_allclose(result.y_ask, VOLS_ASK)

    def test_x_only_transform(self) -> None:
        sd = SmileData(
            x=STRIKES,
            y_bid=VOLS_BID,
            y_ask=VOLS_ASK,
            x_coord=XCoord.FixedStrike,
            y_coord=YCoord.Volatility,
            metadata=META,
        )
        result = sd.transform(XCoord.MoneynessStrike, YCoord.Volatility)
        np.testing.assert_allclose(result.x, STRIKES / META.forward)
        # Y unchanged
        np.testing.assert_allclose(result.y_bid, VOLS_BID)
        np.testing.assert_allclose(result.y_ask, VOLS_ASK)

    def test_y_only_transform(self) -> None:
        sd = SmileData(
            x=STRIKES,
            y_bid=VOLS_BID,
            y_ask=VOLS_ASK,
            x_coord=XCoord.FixedStrike,
            y_coord=YCoord.Volatility,
            metadata=META,
        )
        result = sd.transform(XCoord.FixedStrike, YCoord.Variance)
        np.testing.assert_allclose(result.x, STRIKES)
        np.testing.assert_allclose(result.y_bid, VOLS_BID**2)
        np.testing.assert_allclose(result.y_ask, VOLS_ASK**2)

    def test_combined_transform(self) -> None:
        sd = SmileData(
            x=STRIKES,
            y_bid=VOLS_BID,
            y_ask=VOLS_ASK,
            x_coord=XCoord.FixedStrike,
            y_coord=YCoord.Volatility,
            metadata=META,
        )
        result = sd.transform(XCoord.LogMoneynessStrike, YCoord.TotalVariance)
        np.testing.assert_allclose(result.x, np.log(STRIKES / META.forward))
        np.testing.assert_allclose(result.y_bid, VOLS_BID**2 * META.texpiry)
        np.testing.assert_allclose(result.y_ask, VOLS_ASK**2 * META.texpiry)

    def test_round_trip(self) -> None:
        sd = SmileData(
            x=STRIKES,
            y_bid=VOLS_BID,
            y_ask=VOLS_ASK,
            x_coord=XCoord.FixedStrike,
            y_coord=YCoord.Volatility,
            metadata=META,
        )
        transformed = sd.transform(XCoord.StandardisedStrike, YCoord.TotalVariance)
        recovered = transformed.transform(XCoord.FixedStrike, YCoord.Volatility)
        np.testing.assert_allclose(recovered.x, STRIKES, rtol=1e-12)
        np.testing.assert_allclose(recovered.y_bid, VOLS_BID, rtol=1e-12)
        np.testing.assert_allclose(recovered.y_ask, VOLS_ASK, rtol=1e-12)

    def test_sigma_atm_required_for_standardised(self) -> None:
        meta_no_atm = SmileMetadata(
            date=pd.Timestamp("2024-01-01"), expiry=pd.Timestamp("2024-04-01"), forward=100.0, discount_factor=0.99
        )
        sd = SmileData(
            x=STRIKES,
            y_bid=VOLS_BID,
            y_ask=VOLS_ASK,
            x_coord=XCoord.FixedStrike,
            y_coord=YCoord.Volatility,
            metadata=meta_no_atm,
        )
        with pytest.raises(ValueError, match="sigma_atm is required"):
            sd.transform(XCoord.StandardisedStrike, YCoord.Volatility)

    def test_vol_to_price_round_trip(self) -> None:
        sd = SmileData(
            x=STRIKES,
            y_bid=VOLS_BID,
            y_ask=VOLS_ASK,
            x_coord=XCoord.FixedStrike,
            y_coord=YCoord.Volatility,
            metadata=META,
        )
        prices = sd.transform(XCoord.FixedStrike, YCoord.Price)
        assert prices.y_coord == YCoord.Price
        assert np.all(prices.y_bid > 0)

        recovered = prices.transform(XCoord.FixedStrike, YCoord.Volatility)
        np.testing.assert_allclose(recovered.y_bid, VOLS_BID, atol=1e-10)
        np.testing.assert_allclose(recovered.y_ask, VOLS_ASK, atol=1e-10)


# --- Tests merged from test_unitised.py ---


def _make_unitised_smile_data() -> SmileData:
    """Create a sample SmileData in (StandardisedStrike, TotalVariance) coords."""
    k = np.array([-1.0, -0.5, 0.0, 0.5, 1.0])
    sigma_atm = 0.2
    expiry = 0.5
    v_mid = sigma_atm**2 * expiry * (1 + 0.1 * k**2)
    spread = 0.001
    return SmileData(
        x=k,
        y_bid=v_mid - spread,
        y_ask=v_mid + spread,
        x_coord=XCoord.StandardisedStrike,
        y_coord=YCoord.TotalVariance,
        metadata=SmileMetadata(
            date=pd.Timestamp("2024-01-01"),
            expiry=pd.Timestamp("2024-07-01"),
            forward=1.0,
            discount_factor=1.0,
            sigma_atm=sigma_atm,
        ),
    )


class TestUnitisedSmileDataProperties:
    def test_y_mid(self):
        sd = _make_unitised_smile_data()
        expected = (sd.y_bid + sd.y_ask) / 2
        np.testing.assert_allclose(sd.y_mid, expected)


class TestUnitisedSmileDataConversions:
    def test_round_trip_via_transform(self):
        """StandardisedStrike/TotalVariance → LogMoneyness/Variance → back preserves data."""
        sd = _make_unitised_smile_data()
        sd_log = sd.transform(XCoord.LogMoneynessStrike, YCoord.Variance)
        sd_back = sd_log.transform(XCoord.StandardisedStrike, YCoord.TotalVariance)

        np.testing.assert_allclose(sd_back.y_bid, sd.y_bid, atol=1e-10)
        np.testing.assert_allclose(sd_back.y_ask, sd.y_ask, atol=1e-10)
        np.testing.assert_allclose(sd_back.x, sd.x, atol=1e-10)


# --- Tests for volume / open_interest passthrough ---


class TestSmileDataVolumeOpenInterest:
    def _meta(self) -> SmileMetadata:
        return SmileMetadata(
            date=pd.Timestamp("2024-01-01"),
            expiry=pd.Timestamp("2024-07-01"),
            forward=100.0,
            discount_factor=1.0,
            sigma_atm=0.20,
        )

    def test_default_none(self):
        sd = _make_vol_smile_data()
        assert sd.volume is None
        assert sd.open_interest is None

    def test_with_volume_and_open_interest(self):
        sd = SmileData(
            x=np.array([90.0, 100.0, 110.0]),
            y_bid=np.array([0.19, 0.18, 0.20]),
            y_ask=np.array([0.21, 0.20, 0.22]),
            x_coord=XCoord.FixedStrike,
            y_coord=YCoord.Volatility,
            metadata=self._meta(),
            volume=np.array([100.0, 200.0, 150.0]),
            open_interest=np.array([1000.0, 2000.0, 1500.0]),
        )
        np.testing.assert_array_equal(sd.volume, [100.0, 200.0, 150.0])
        np.testing.assert_array_equal(sd.open_interest, [1000.0, 2000.0, 1500.0])

    def test_coerced_to_float64(self):
        sd = SmileData(
            x=np.array([90.0, 100.0, 110.0]),
            y_bid=np.array([0.19, 0.18, 0.20]),
            y_ask=np.array([0.21, 0.20, 0.22]),
            x_coord=XCoord.FixedStrike,
            y_coord=YCoord.Volatility,
            metadata=self._meta(),
            volume=[100, 200, 150],
            open_interest=[1000, 2000, 1500],
        )
        assert sd.volume.dtype == np.float64
        assert sd.open_interest.dtype == np.float64

    def test_volume_length_mismatch(self):
        with pytest.raises(ValueError, match="volume must have the same length"):
            SmileData(
                x=np.array([90.0, 100.0, 110.0]),
                y_bid=np.array([0.19, 0.18, 0.20]),
                y_ask=np.array([0.21, 0.20, 0.22]),
                x_coord=XCoord.FixedStrike,
                y_coord=YCoord.Volatility,
                metadata=self._meta(),
                volume=np.array([100.0, 200.0]),
            )

    def test_open_interest_length_mismatch(self):
        with pytest.raises(ValueError, match="open_interest must have the same length"):
            SmileData(
                x=np.array([90.0, 100.0, 110.0]),
                y_bid=np.array([0.19, 0.18, 0.20]),
                y_ask=np.array([0.21, 0.20, 0.22]),
                x_coord=XCoord.FixedStrike,
                y_coord=YCoord.Volatility,
                metadata=self._meta(),
                open_interest=np.array([1000.0]),
            )

    def test_negative_volume_rejected(self):
        with pytest.raises(ValueError, match="volume must be non-negative"):
            SmileData(
                x=np.array([90.0, 100.0, 110.0]),
                y_bid=np.array([0.19, 0.18, 0.20]),
                y_ask=np.array([0.21, 0.20, 0.22]),
                x_coord=XCoord.FixedStrike,
                y_coord=YCoord.Volatility,
                metadata=self._meta(),
                volume=np.array([100.0, -1.0, 150.0]),
            )

    def test_negative_open_interest_rejected(self):
        with pytest.raises(ValueError, match="open_interest must be non-negative"):
            SmileData(
                x=np.array([90.0, 100.0, 110.0]),
                y_bid=np.array([0.19, 0.18, 0.20]),
                y_ask=np.array([0.21, 0.20, 0.22]),
                x_coord=XCoord.FixedStrike,
                y_coord=YCoord.Volatility,
                metadata=self._meta(),
                open_interest=np.array([1000.0, 2000.0, -1.0]),
            )

    def test_transform_preserves_volume_and_oi(self):
        vol = np.array([100.0, 200.0, 150.0, 300.0, 250.0, 180.0, 120.0])
        oi = np.array([1000.0, 2000.0, 1500.0, 3000.0, 2500.0, 1800.0, 1200.0])
        sd = _make_vol_smile_data()
        sd.volume = vol
        sd.open_interest = oi
        sd_u = sd.transform(XCoord.StandardisedStrike, YCoord.TotalVariance)
        np.testing.assert_array_equal(sd_u.volume, vol)
        np.testing.assert_array_equal(sd_u.open_interest, oi)

    def test_transform_preserves_none(self):
        sd = _make_vol_smile_data()
        sd_u = sd.transform(XCoord.StandardisedStrike, YCoord.TotalVariance)
        assert sd_u.volume is None
        assert sd_u.open_interest is None
