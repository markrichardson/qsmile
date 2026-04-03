"""Tests for SmileData with unitised coordinates (replaces UnitisedSpaceVols tests)."""

from __future__ import annotations

import numpy as np

from qsmile.core.coords import XCoord, YCoord
from qsmile.data.metadata import SmileMetadata
from qsmile.data.smile_data import SmileData


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
            forward=1.0,
            discount_factor=1.0,
            expiry=expiry,
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
