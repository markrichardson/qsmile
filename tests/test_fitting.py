"""Tests for qsmile.fitting."""

from __future__ import annotations

import numpy as np

from qsmile.data.smile_data import SmileData
from qsmile.models.fitting import SmileResult, fit_svi
from qsmile.models.svi import SVIParams, svi_implied_vol, svi_total_variance


class TestFitSVISyntheticRoundTrip:
    """Fit SVI to data generated from known parameters and recover them."""

    def test_recover_known_params(self):
        true_params = SVIParams(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.2)
        expiry = 0.5
        strikes = np.linspace(80, 120, 20)
        forward = 100.0
        k = np.log(strikes / forward)
        ivs = svi_implied_vol(k, true_params, expiry)

        sd = SmileData.from_mid_vols(strikes=strikes, ivs=ivs, forward=forward, expiry=expiry)
        result = fit_svi(sd)

        assert result.success
        assert result.rmse < 1e-10
        np.testing.assert_allclose(result.params.a, true_params.a, atol=1e-6)
        np.testing.assert_allclose(result.params.b, true_params.b, atol=1e-6)
        np.testing.assert_allclose(result.params.rho, true_params.rho, atol=1e-6)
        np.testing.assert_allclose(result.params.m, true_params.m, atol=1e-6)
        np.testing.assert_allclose(result.params.sigma, true_params.sigma, atol=1e-6)


class TestFitSVINoisyData:
    """Fit to market-like noisy data."""

    def test_noisy_fit_succeeds(self):
        true_params = SVIParams(a=0.04, b=0.12, rho=-0.4, m=0.01, sigma=0.25)
        expiry = 1.0
        strikes = np.linspace(80, 120, 15)
        forward = 100.0
        k = np.log(strikes / forward)
        ivs_clean = svi_implied_vol(k, true_params, expiry)

        rng = np.random.default_rng(42)
        noise = rng.normal(0, 0.002, size=ivs_clean.shape)
        ivs_noisy = ivs_clean + noise

        sd = SmileData.from_mid_vols(strikes=strikes, ivs=ivs_noisy, forward=forward, expiry=expiry)
        result = fit_svi(sd)

        assert result.success
        assert result.rmse < 0.01


class TestFitSVICustomInitialGuess:
    """Test that a custom initial guess is used."""

    def test_custom_initial_params(self):
        true_params = SVIParams(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.2)
        expiry = 0.5
        strikes = np.linspace(85, 115, 12)
        forward = 100.0
        k = np.log(strikes / forward)
        ivs = svi_implied_vol(k, true_params, expiry)

        sd = SmileData.from_mid_vols(strikes=strikes, ivs=ivs, forward=forward, expiry=expiry)
        guess = SVIParams(a=0.03, b=0.08, rho=-0.2, m=0.01, sigma=0.15)
        result = fit_svi(sd, initial_params=guess)

        assert result.success
        assert result.rmse < 1e-6


class TestSmileResult:
    def test_residuals_shape(self):
        true_params = SVIParams(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.2)
        expiry = 0.5
        strikes = np.linspace(85, 115, 10)
        forward = 100.0
        k = np.log(strikes / forward)
        ivs = svi_implied_vol(k, true_params, expiry)

        sd = SmileData.from_mid_vols(strikes=strikes, ivs=ivs, forward=forward, expiry=expiry)
        result = fit_svi(sd)

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
        expected = svi_total_variance(k_test, params)
        np.testing.assert_allclose(w, expected)

    def test_fitted_params_within_bounds(self):
        true_params = SVIParams(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.2)
        expiry = 0.5
        strikes = np.linspace(80, 120, 20)
        forward = 100.0
        k = np.log(strikes / forward)
        ivs = svi_implied_vol(k, true_params, expiry)

        sd = SmileData.from_mid_vols(strikes=strikes, ivs=ivs, forward=forward, expiry=expiry)
        result = fit_svi(sd)

        assert result.params.b >= 0
        assert -1 < result.params.rho < 1
        assert result.params.sigma > 0


class TestFitSVIFromSmileData:
    """fit_svi should accept SmileData in various coordinate systems."""

    def test_smile_data_from_mid_vols(self):
        true_params = SVIParams(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.2)
        expiry = 0.5
        strikes = np.linspace(80, 120, 20)
        forward = 100.0
        k = np.log(strikes / forward)
        ivs = svi_implied_vol(k, true_params, expiry)

        # Fit via SmileData.from_mid_vols
        sd = SmileData.from_mid_vols(strikes=strikes, ivs=ivs, forward=forward, expiry=expiry)
        result = fit_svi(sd)

        assert result.success
        np.testing.assert_allclose(result.params.a, true_params.a, atol=1e-6)
        np.testing.assert_allclose(result.params.b, true_params.b, atol=1e-6)
        np.testing.assert_allclose(result.params.rho, true_params.rho, atol=1e-6)
