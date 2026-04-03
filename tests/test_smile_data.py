"""Tests for SmileData container and transform."""

from __future__ import annotations

import numpy as np
import pytest

from qsmile.core.coords import XCoord, YCoord
from qsmile.data.meta import SmileMetadata
from qsmile.data.vols import SmileData

META = SmileMetadata(forward=100.0, discount_factor=0.99, expiry=0.25, sigma_atm=0.20)
STRIKES = np.array([90.0, 95.0, 100.0, 105.0, 110.0])
VOLS_BID = np.array([0.22, 0.20, 0.18, 0.20, 0.22])
VOLS_ASK = np.array([0.24, 0.22, 0.20, 0.22, 0.24])


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
        np.testing.assert_allclose(result.y_bid, VOLS_BID**2 * META.expiry)
        np.testing.assert_allclose(result.y_ask, VOLS_ASK**2 * META.expiry)

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
        meta_no_atm = SmileMetadata(forward=100.0, discount_factor=0.99, expiry=0.25)
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
