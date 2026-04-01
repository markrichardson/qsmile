"""Tests for qsmile.unitised."""

from __future__ import annotations

import numpy as np
import pytest

from qsmile.coords import XCoord, YCoord
from qsmile.unitised import UnitisedSpaceVols


def _make_unitised() -> UnitisedSpaceVols:
    """Create a sample UnitisedSpaceVols for testing."""
    k = np.array([-1.0, -0.5, 0.0, 0.5, 1.0])
    sigma_atm = 0.2
    expiry = 0.5
    # Parabolic smile: v_mid = sigma_atm^2 * T * (1 + 0.1 * k^2)
    v_mid = sigma_atm**2 * expiry * (1 + 0.1 * k**2)
    spread = 0.001
    return UnitisedSpaceVols(
        k_unitised=k,
        variance_bid=v_mid - spread,
        variance_ask=v_mid + spread,
        sigma_atm=sigma_atm,
        expiry=expiry,
    )


class TestUnitisedSpaceVolsConstruction:
    def test_from_arrays(self):
        u = _make_unitised()
        assert isinstance(u.k_unitised, np.ndarray)
        assert u.sigma_atm == 0.2
        assert u.expiry == 0.5

    def test_from_lists(self):
        u = UnitisedSpaceVols(
            k_unitised=[-1.0, 0.0, 1.0],
            variance_bid=[0.019, 0.020, 0.019],
            variance_ask=[0.021, 0.020, 0.021],
            sigma_atm=0.2,
            expiry=0.5,
        )
        assert u.k_unitised.dtype == np.float64


class TestUnitisedSpaceVolsValidation:
    def test_mismatched_lengths(self):
        with pytest.raises(ValueError, match="same length"):
            UnitisedSpaceVols(
                k_unitised=[0.0, 1.0],
                variance_bid=[0.02],
                variance_ask=[0.02, 0.02],
                sigma_atm=0.2,
                expiry=0.5,
            )

    def test_negative_variance(self):
        with pytest.raises(ValueError, match="non-negative"):
            UnitisedSpaceVols(
                k_unitised=[0.0, 0.5, 1.0],
                variance_bid=[-0.01, 0.02, 0.02],
                variance_ask=[0.02, 0.02, 0.02],
                sigma_atm=0.2,
                expiry=0.5,
            )

    def test_bid_exceeds_ask(self):
        with pytest.raises(ValueError, match="must not exceed"):
            UnitisedSpaceVols(
                k_unitised=[0.0, 0.5, 1.0],
                variance_bid=[0.03, 0.02, 0.02],
                variance_ask=[0.02, 0.02, 0.02],
                sigma_atm=0.2,
                expiry=0.5,
            )

    def test_non_positive_sigma_atm(self):
        with pytest.raises(ValueError, match="sigma_atm must be positive"):
            UnitisedSpaceVols(
                k_unitised=[0.0, 0.5, 1.0],
                variance_bid=[0.01, 0.02, 0.02],
                variance_ask=[0.02, 0.02, 0.02],
                sigma_atm=0.0,
                expiry=0.5,
            )

    def test_non_positive_expiry(self):
        with pytest.raises(ValueError, match="expiry must be positive"):
            UnitisedSpaceVols(
                k_unitised=[0.0, 0.5, 1.0],
                variance_bid=[0.01, 0.02, 0.02],
                variance_ask=[0.02, 0.02, 0.02],
                sigma_atm=0.2,
                expiry=0.0,
            )


class TestUnitisedSpaceVolsProperties:
    def test_variance_mid(self):
        u = _make_unitised()
        expected = (u.variance_bid + u.variance_ask) / 2
        np.testing.assert_allclose(u.variance_mid, expected)


class TestUnitisedSpaceVolsConversions:
    def test_round_trip_via_smile_data(self):
        """UnitisedSpaceVols → SmileData → transform → back preserves data."""
        u = _make_unitised()
        sd = u.to_smile_data()
        # Round-trip: StandardisedStrike/TotalVariance → LogMoneyness/Variance → back
        sd_log = sd.transform(XCoord.LogMoneynessStrike, YCoord.Variance)
        sd_back = sd_log.transform(XCoord.StandardisedStrike, YCoord.TotalVariance)

        np.testing.assert_allclose(sd_back.y_bid, sd.y_bid, atol=1e-10)
        np.testing.assert_allclose(sd_back.y_ask, sd.y_ask, atol=1e-10)
        np.testing.assert_allclose(sd_back.x, sd.x, atol=1e-10)
