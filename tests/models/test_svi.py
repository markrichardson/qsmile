"""Tests for qsmile.models.svi."""

from __future__ import annotations

import numpy as np
import pytest

from qsmile.core.coords import XCoord, YCoord
from qsmile.models.protocol import SmileModel
from qsmile.models.svi import SVIModel


class TestSVIModel:
    def test_create_valid(self):
        p = SVIModel(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.2)
        assert p.a == 0.04
        assert p.b == 0.1
        assert p.rho == -0.3
        assert p.m == 0.0
        assert p.sigma == 0.2

    def test_negative_b(self):
        with pytest.raises(ValueError, match="b must be non-negative"):
            SVIModel(a=0.04, b=-0.1, rho=-0.3, m=0.0, sigma=0.2)

    def test_rho_out_of_range_positive(self):
        with pytest.raises(ValueError, match="rho must be in"):
            SVIModel(a=0.04, b=0.1, rho=1.0, m=0.0, sigma=0.2)

    def test_rho_out_of_range_negative(self):
        with pytest.raises(ValueError, match="rho must be in"):
            SVIModel(a=0.04, b=0.1, rho=-1.0, m=0.0, sigma=0.2)

    def test_non_positive_sigma(self):
        with pytest.raises(ValueError, match="sigma must be positive"):
            SVIModel(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.0)

    def test_b_zero_is_valid(self):
        p = SVIModel(a=0.04, b=0.0, rho=0.0, m=0.0, sigma=0.2)
        assert p.b == 0.0


class TestSVITotalVariance:
    def test_scalar_k(self):
        params = SVIModel(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.2)
        result = params.evaluate(0.0)
        expected = 0.04 + 0.1 * ((-0.3) * 0.0 + np.sqrt(0.0 + 0.04))
        assert abs(float(result) - expected) < 1e-12

    def test_array_k(self):
        params = SVIModel(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.2)
        k = np.array([-0.1, 0.0, 0.1])
        result = params.evaluate(k)
        assert result.shape == (3,)

    def test_symmetry_when_rho_zero(self):
        params = SVIModel(a=0.04, b=0.1, rho=0.0, m=0.0, sigma=0.2)
        delta = 0.15
        w_pos = params.evaluate(params.m + delta)
        w_neg = params.evaluate(params.m - delta)
        np.testing.assert_allclose(w_pos, w_neg)

    def test_known_formula(self):
        params = SVIModel(a=0.02, b=0.15, rho=-0.5, m=0.01, sigma=0.3)
        k = 0.05
        d = k - params.m
        expected = params.a + params.b * (params.rho * d + np.sqrt(d**2 + params.sigma**2))
        np.testing.assert_allclose(params.evaluate(k), expected)


class TestSVIImpliedVol:
    def test_basic(self):
        params = SVIModel(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.2)
        expiry = 0.5
        k = np.array([-0.1, 0.0, 0.1])
        iv = params.implied_vol(k, expiry)
        w = params.evaluate(k)
        np.testing.assert_allclose(iv, np.sqrt(w / expiry))

    def test_non_positive_expiry(self):
        params = SVIModel(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.2)
        with pytest.raises(ValueError, match="expiry must be positive"):
            params.implied_vol(0.0, 0.0)

    def test_negative_expiry(self):
        params = SVIModel(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.2)
        with pytest.raises(ValueError, match="expiry must be positive"):
            params.implied_vol(0.0, -1.0)


class TestSVIModelProtocol:
    """SVIModel satisfies the SmileModel protocol."""

    def test_isinstance_check(self):
        p = SVIModel(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.2)
        assert isinstance(p, SmileModel)

    def test_round_trip_serialisation(self):
        p = SVIModel(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.2)
        arr = p.to_array()
        recovered = SVIModel.from_array(arr)
        np.testing.assert_allclose(recovered.to_array(), p.to_array())


class TestSVIModelMetadata:
    """SVIModel provides model-level metadata."""

    def test_bounds_length_matches_param_names(self):
        lower, upper = SVIModel.bounds
        assert len(lower) == len(SVIModel.param_names)
        assert len(upper) == len(SVIModel.param_names)

    def test_native_coords(self):
        assert SVIModel.native_x_coord == XCoord.LogMoneynessStrike
        assert SVIModel.native_y_coord == YCoord.TotalVariance

    def test_initial_guess_length(self):
        k = np.linspace(-0.2, 0.2, 10)
        w = 0.04 + 0.1 * np.sqrt(k**2 + 0.04)
        guess = SVIModel.initial_guess(k, w)
        assert len(guess) == 5
