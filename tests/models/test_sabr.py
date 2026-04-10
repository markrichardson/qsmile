"""Tests for qsmile.models.sabr."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from qsmile.core.coords import XCoord, YCoord
from qsmile.data.meta import SmileMetadata
from qsmile.models.protocol import SmileModel
from qsmile.models.sabr import SABRModel

# -- Reusable fixtures --

_META = SmileMetadata(
    date=pd.Timestamp("2024-01-01"),
    expiry=pd.Timestamp("2025-01-01"),
    forward=100.0,
    sigma_atm=0.2,
)

_VALID_PARAMS = {"alpha": 0.2, "beta": 0.5, "rho": -0.3, "nu": 0.4, "metadata": _META}


class TestSABRModel:
    def test_create_valid(self):
        m = SABRModel(**_VALID_PARAMS)
        assert m.alpha == 0.2
        assert m.beta == 0.5
        assert m.rho == -0.3
        assert m.nu == 0.4

    def test_negative_alpha(self):
        with pytest.raises(ValueError, match="alpha"):
            SABRModel(**{**_VALID_PARAMS, "alpha": -0.1})

    def test_beta_below_range(self):
        with pytest.raises(ValueError, match="beta"):
            SABRModel(**{**_VALID_PARAMS, "beta": -0.1})

    def test_beta_above_range(self):
        with pytest.raises(ValueError, match="beta"):
            SABRModel(**{**_VALID_PARAMS, "beta": 1.5})

    def test_rho_at_boundary(self):
        with pytest.raises(ValueError, match="rho"):
            SABRModel(**{**_VALID_PARAMS, "rho": 1.0})

    def test_rho_at_negative_boundary(self):
        with pytest.raises(ValueError, match="rho"):
            SABRModel(**{**_VALID_PARAMS, "rho": -1.0})

    def test_negative_nu(self):
        with pytest.raises(ValueError, match="nu"):
            SABRModel(**{**_VALID_PARAMS, "nu": -0.1})

    def test_nu_zero_is_valid(self):
        m = SABRModel(**{**_VALID_PARAMS, "nu": 0.0})
        assert m.nu == 0.0

    def test_beta_zero_is_valid(self):
        m = SABRModel(**{**_VALID_PARAMS, "beta": 0.0})
        assert m.beta == 0.0

    def test_beta_one_is_valid(self):
        m = SABRModel(**{**_VALID_PARAMS, "beta": 1.0})
        assert m.beta == 1.0


class TestSABRModelMetadata:
    def test_native_coords(self):
        assert SABRModel.native_x_coord == XCoord.LogMoneynessStrike
        assert SABRModel.native_y_coord == YCoord.Volatility

    def test_param_names(self):
        assert SABRModel.param_names == ("alpha", "beta", "rho", "nu")

    def test_bounds_length_matches_param_names(self):
        lower, upper = SABRModel.bounds
        assert len(lower) == len(SABRModel.param_names)
        assert len(upper) == len(SABRModel.param_names)


class TestSABRModelSerialisation:
    def test_to_array_returns_4_elements(self):
        m = SABRModel(**_VALID_PARAMS)
        arr = m.to_array()
        assert arr.shape == (4,)
        np.testing.assert_array_equal(arr, [0.2, 0.5, -0.3, 0.4])

    def test_to_array_excludes_context_fields(self):
        m = SABRModel(**_VALID_PARAMS)
        arr = m.to_array()
        assert len(arr) == 4  # only alpha, beta, rho, nu

    def test_round_trip(self):
        m = SABRModel(**_VALID_PARAMS)
        recovered = SABRModel.from_array(m.to_array(), metadata=_META)
        np.testing.assert_allclose(recovered.to_array(), m.to_array())


class TestSABRModelEvaluate:
    def test_atm_returns_finite_positive(self):
        m = SABRModel(**_VALID_PARAMS)
        iv = m.evaluate(0.0)
        assert np.isfinite(iv)
        assert float(iv) > 0

    def test_array_of_strikes(self):
        m = SABRModel(**_VALID_PARAMS)
        k = np.linspace(-0.2, 0.2, 11)
        iv = m.evaluate(k)
        assert iv.shape == (11,)
        assert np.all(np.isfinite(iv))
        assert np.all(iv > 0)

    def test_negative_rho_gives_left_skew(self):
        """Negative rho should produce higher vol for low strikes (negative k)."""
        m = SABRModel(alpha=0.2, beta=0.5, rho=-0.5, nu=0.4, metadata=_META)
        iv_left = m.evaluate(-0.15)
        iv_right = m.evaluate(0.15)
        assert float(iv_left) > float(iv_right)

    def test_beta_one_lognormal(self):
        """beta=1 is the lognormal SABR case — should still produce finite vols."""
        m = SABRModel(alpha=0.2, beta=1.0, rho=-0.3, nu=0.3, metadata=_META)
        k = np.linspace(-0.1, 0.1, 5)
        iv = m.evaluate(k)
        assert np.all(np.isfinite(iv))
        assert np.all(iv > 0)

    def test_nu_zero_flat_smile(self):
        """When nu=0, the smile should be essentially flat (no vol-of-vol)."""
        m = SABRModel(alpha=0.2, beta=0.5, rho=0.0, nu=0.0, metadata=_META)
        k = np.linspace(-0.1, 0.1, 5)
        iv = m.evaluate(k)
        # All vols should be very close to ATM vol
        atm_iv = float(m.evaluate(0.0))
        np.testing.assert_allclose(iv, atm_iv, rtol=0.05)


class TestSABRModelInitialGuess:
    def test_returns_4_elements(self):
        k = np.linspace(-0.2, 0.2, 10)
        iv = 0.2 + 0.1 * k**2
        guess = SABRModel.initial_guess(k, iv)
        assert len(guess) == 4

    def test_within_bounds(self):
        k = np.linspace(-0.2, 0.2, 10)
        iv = 0.2 + 0.1 * k**2
        guess = SABRModel.initial_guess(k, iv)
        lower, upper = SABRModel.bounds
        for i, (lo, hi) in enumerate(zip(lower, upper, strict=False)):
            assert guess[i] >= lo, f"param {i}: {guess[i]} < {lo}"
            assert guess[i] <= hi, f"param {i}: {guess[i]} > {hi}"


class TestSABRModelProtocol:
    def test_isinstance_check(self):
        m = SABRModel(**_VALID_PARAMS)
        assert isinstance(m, SmileModel)


class TestSABRModelCoordAware:
    """SABRModel inherits coordinate-awareness from AbstractSmileModel."""

    def test_default_current_coords(self):
        m = SABRModel(**_VALID_PARAMS)
        assert m.current_x_coord == XCoord.LogMoneynessStrike
        assert m.current_y_coord == YCoord.Volatility

    def test_transform(self):
        m = SABRModel(**_VALID_PARAMS)
        t = m.transform(XCoord.FixedStrike, YCoord.TotalVariance)
        assert t.current_x_coord == XCoord.FixedStrike
        assert t.current_y_coord == YCoord.TotalVariance

    def test_evaluate_in_native_equals_raw(self):
        m = SABRModel(**_VALID_PARAMS)
        k = np.array([-0.1, 0.0, 0.1])
        np.testing.assert_allclose(m.evaluate(k), m._evaluate(k))

    def test_params_dict(self):
        m = SABRModel(**_VALID_PARAMS)
        d = m.params
        assert d == {"alpha": 0.2, "beta": 0.5, "rho": -0.3, "nu": 0.4}

    def test_metadata_accessible(self):
        m = SABRModel(**_VALID_PARAMS)
        assert m.metadata is _META
        assert m.metadata.forward == 100.0

    def test_plot_returns_figure(self):
        m = SABRModel(**_VALID_PARAMS)
        fig = m.plot()
        import matplotlib.figure

        assert isinstance(fig, matplotlib.figure.Figure)
