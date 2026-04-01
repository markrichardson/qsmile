"""Tests for SmileData with volatility coordinates (replaces OptionChainVols tests)."""

from __future__ import annotations

import numpy as np

from qsmile.coords import XCoord, YCoord
from qsmile.metadata import SmileMetadata
from qsmile.smile_data import SmileData


def _make_vol_smile_data(
    forward: float = 100.0,
    discount_factor: float = 0.98,
    expiry: float = 0.5,
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
            forward=forward,
            discount_factor=discount_factor,
            expiry=expiry,
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
        expected_k = log_m / (sd.metadata.sigma_atm * np.sqrt(sd.metadata.expiry))
        np.testing.assert_allclose(sd_u.x, expected_k)
        np.testing.assert_allclose(sd_u.y_bid, sd.y_bid**2 * sd.metadata.expiry)
        np.testing.assert_allclose(sd_u.y_ask, sd.y_ask**2 * sd.metadata.expiry)

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
