"""Tests for qsmile.unitised."""

from __future__ import annotations

import numpy as np
import pytest

from qsmile.unitised import UnitisedSpaceVols
from qsmile.vols import OptionChainVols


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
    def test_round_trip_via_vols(self):
        """OptionChainVols → UnitisedSpaceVols → OptionChainVols preserves data."""
        strikes = np.array([85.0, 90.0, 95.0, 100.0, 105.0, 110.0, 115.0])
        vol_mid = np.array([0.28, 0.25, 0.22, 0.20, 0.21, 0.23, 0.26])
        spread = 0.005
        forward = 100.0
        discount_factor = 0.98
        expiry = 0.5

        vols1 = OptionChainVols(
            strikes=strikes,
            vol_bid=vol_mid - spread,
            vol_ask=vol_mid + spread,
            forward=forward,
            discount_factor=discount_factor,
            expiry=expiry,
        )

        u = vols1.to_unitised()
        vols2 = u.to_vols(forward=forward, strikes=strikes, discount_factor=discount_factor)

        np.testing.assert_allclose(vols2.vol_bid, vols1.vol_bid, atol=1e-10)
        np.testing.assert_allclose(vols2.vol_ask, vols1.vol_ask, atol=1e-10)
