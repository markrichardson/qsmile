"""Tests for qsmile.models.fitting."""

from __future__ import annotations

import numpy as np

from qsmile.data.vols import SmileData
from qsmile.models.fitting import SmileResult, fit
from qsmile.models.svi import SVIParams

# Default SVI model instance for generic fit calls
_SVI = SVIParams(a=0.0, b=0.01, rho=0.0, m=0.0, sigma=0.1)

# Reusable known-good parameters for synthetic round-trip tests
_TRUE_PARAMS = SVIParams(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.2)


def _make_synthetic_sd(
    params: SVIParams = _TRUE_PARAMS,
    expiry: float = 0.5,
    forward: float = 100.0,
    n_strikes: int = 20,
    strike_lo: float = 80.0,
    strike_hi: float = 120.0,
) -> SmileData:
    """Generate SmileData from known SVI parameters (noiseless)."""
    strikes = np.linspace(strike_lo, strike_hi, n_strikes)
    k = np.log(strikes / forward)
    ivs = params.implied_vol(k, expiry)
    return SmileData.from_mid_vols(strikes=strikes, ivs=ivs, forward=forward, expiry=expiry)


class TestFitSyntheticRoundTrip:
    """Fit SVI to data generated from known parameters and recover them."""

    def test_recover_known_params(self):
        sd = _make_synthetic_sd()
        result = fit(sd, _SVI)

        assert result.success
        assert result.rmse < 1e-10
        np.testing.assert_allclose(result.params.a, _TRUE_PARAMS.a, atol=1e-6)
        np.testing.assert_allclose(result.params.b, _TRUE_PARAMS.b, atol=1e-6)
        np.testing.assert_allclose(result.params.rho, _TRUE_PARAMS.rho, atol=1e-6)
        np.testing.assert_allclose(result.params.m, _TRUE_PARAMS.m, atol=1e-6)
        np.testing.assert_allclose(result.params.sigma, _TRUE_PARAMS.sigma, atol=1e-6)

    def test_non_native_coords_accepted(self):
        """SmileData in (FixedStrike, Volatility) — non-native for SVI — still fits."""
        sd = _make_synthetic_sd()
        result = fit(sd, _SVI)

        assert result.success
        assert result.rmse < 1e-10


class TestFitNoisyData:
    """Fit to market-like noisy data."""

    def test_noisy_fit_succeeds(self):
        true_params = SVIParams(a=0.04, b=0.12, rho=-0.4, m=0.01, sigma=0.25)
        expiry = 1.0
        strikes = np.linspace(80, 120, 15)
        forward = 100.0
        k = np.log(strikes / forward)
        ivs_clean = true_params.implied_vol(k, expiry)

        rng = np.random.default_rng(42)
        noise = rng.normal(0, 0.002, size=ivs_clean.shape)
        ivs_noisy = ivs_clean + noise

        sd = SmileData.from_mid_vols(strikes=strikes, ivs=ivs_noisy, forward=forward, expiry=expiry)
        result = fit(sd, _SVI)

        assert result.success
        assert result.rmse < 0.01


class TestFitCustomInitialGuess:
    """Test that a custom initial guess is used."""

    def test_custom_initial_params(self):
        sd = _make_synthetic_sd(n_strikes=12, strike_lo=85.0, strike_hi=115.0)
        guess = SVIParams(a=0.03, b=0.08, rho=-0.2, m=0.01, sigma=0.15)
        result = fit(sd, guess, initial_params=guess)

        assert result.success
        assert result.rmse < 1e-6


class TestSmileResult:
    """SmileResult properties: residuals, rmse, evaluate, param bounds."""

    def test_residuals_shape(self):
        sd = _make_synthetic_sd(n_strikes=10, strike_lo=85.0, strike_hi=115.0)
        result = fit(sd, _SVI)

        assert result.residuals.shape == (10,)
        assert isinstance(result.rmse, float)
        assert isinstance(result.params, SVIParams)

    def test_evaluate(self):
        params = SVIParams(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.2)
        result = SmileResult(
            params=params,
            residuals=np.zeros(5),
            rmse=0.0,
            success=True,
        )
        k_test = np.array([-0.2, 0.0, 0.2])
        w = result.evaluate(k_test)
        expected = params.evaluate(k_test)
        np.testing.assert_allclose(w, expected)

    def test_fitted_params_within_bounds(self):
        sd = _make_synthetic_sd()
        result = fit(sd, _SVI)

        assert result.params.b >= 0
        assert -1 < result.params.rho < 1
        assert result.params.sigma > 0
