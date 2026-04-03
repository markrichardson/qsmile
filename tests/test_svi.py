"""Tests for qsmile.svi."""

from __future__ import annotations

import numpy as np
import pytest

from qsmile.models.svi import SVIParams, svi_implied_vol, svi_total_variance


class TestSVIParams:
    def test_create_valid(self):
        p = SVIParams(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.2)
        assert p.a == 0.04
        assert p.b == 0.1
        assert p.rho == -0.3
        assert p.m == 0.0
        assert p.sigma == 0.2

    def test_negative_b(self):
        with pytest.raises(ValueError, match="b must be non-negative"):
            SVIParams(a=0.04, b=-0.1, rho=-0.3, m=0.0, sigma=0.2)

    def test_rho_out_of_range_positive(self):
        with pytest.raises(ValueError, match="rho must be in"):
            SVIParams(a=0.04, b=0.1, rho=1.0, m=0.0, sigma=0.2)

    def test_rho_out_of_range_negative(self):
        with pytest.raises(ValueError, match="rho must be in"):
            SVIParams(a=0.04, b=0.1, rho=-1.0, m=0.0, sigma=0.2)

    def test_non_positive_sigma(self):
        with pytest.raises(ValueError, match="sigma must be positive"):
            SVIParams(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.0)

    def test_b_zero_is_valid(self):
        p = SVIParams(a=0.04, b=0.0, rho=0.0, m=0.0, sigma=0.2)
        assert p.b == 0.0


class TestSVITotalVariance:
    def test_scalar_k(self):
        params = SVIParams(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.2)
        result = svi_total_variance(0.0, params)
        expected = 0.04 + 0.1 * ((-0.3) * 0.0 + np.sqrt(0.0 + 0.04))
        assert abs(float(result) - expected) < 1e-12

    def test_array_k(self):
        params = SVIParams(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.2)
        k = np.array([-0.1, 0.0, 0.1])
        result = svi_total_variance(k, params)
        assert result.shape == (3,)

    def test_symmetry_when_rho_zero(self):
        params = SVIParams(a=0.04, b=0.1, rho=0.0, m=0.0, sigma=0.2)
        delta = 0.15
        w_pos = svi_total_variance(params.m + delta, params)
        w_neg = svi_total_variance(params.m - delta, params)
        np.testing.assert_allclose(w_pos, w_neg)

    def test_known_formula(self):
        params = SVIParams(a=0.02, b=0.15, rho=-0.5, m=0.01, sigma=0.3)
        k = 0.05
        d = k - params.m
        expected = params.a + params.b * (params.rho * d + np.sqrt(d**2 + params.sigma**2))
        np.testing.assert_allclose(svi_total_variance(k, params), expected)


class TestSVIImpliedVol:
    def test_basic(self):
        params = SVIParams(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.2)
        expiry = 0.5
        k = np.array([-0.1, 0.0, 0.1])
        iv = svi_implied_vol(k, params, expiry)
        w = svi_total_variance(k, params)
        np.testing.assert_allclose(iv, np.sqrt(w / expiry))

    def test_non_positive_expiry(self):
        params = SVIParams(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.2)
        with pytest.raises(ValueError, match="expiry must be positive"):
            svi_implied_vol(0.0, params, 0.0)

    def test_negative_expiry(self):
        params = SVIParams(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.2)
        with pytest.raises(ValueError, match="expiry must be positive"):
            svi_implied_vol(0.0, params, -1.0)
