"""Tests for qsmile.fitting."""

from __future__ import annotations

import numpy as np

from qsmile.data.vols import SmileData
from qsmile.models.fitting import SmileResult, fit, fit_svi
from qsmile.models.protocol import SmileModel
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


class TestSVIParamsProtocolConformance:
    """SVIParams satisfies the SmileModel protocol."""

    def test_isinstance_check(self):
        p = SVIParams(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.2)
        assert isinstance(p, SmileModel)

    def test_round_trip_serialisation(self):
        p = SVIParams(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.2)
        arr = p.to_array()
        recovered = SVIParams.from_array(arr)
        np.testing.assert_allclose(recovered.to_array(), p.to_array())

    def test_bounds_length_matches_param_names(self):
        p = SVIParams(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.2)
        lower, upper = p.bounds
        assert len(lower) == len(p.param_names)
        assert len(upper) == len(p.param_names)

    def test_native_coords(self):
        from qsmile.core.coords import XCoord, YCoord

        p = SVIParams(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.2)
        assert p.native_x_coord == XCoord.LogMoneynessStrike
        assert p.native_y_coord == YCoord.TotalVariance

    def test_evaluate_matches_svi_total_variance(self):
        p = SVIParams(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.2)
        k = np.array([-0.2, 0.0, 0.2])
        np.testing.assert_allclose(p.evaluate(k), svi_total_variance(k, p))

    def test_initial_guess_length(self):
        k = np.linspace(-0.2, 0.2, 10)
        w = 0.04 + 0.1 * np.sqrt(k**2 + 0.04)
        guess = SVIParams.initial_guess(k, w)
        assert len(guess) == 5


class TestGenericFit:
    """Generic fit() function works with SVI model."""

    def test_fit_svi_via_generic(self):
        true_params = SVIParams(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.2)
        expiry = 0.5
        strikes = np.linspace(80, 120, 20)
        forward = 100.0
        k = np.log(strikes / forward)
        ivs = svi_implied_vol(k, true_params, expiry)

        sd = SmileData.from_mid_vols(strikes=strikes, ivs=ivs, forward=forward, expiry=expiry)
        model = SVIParams(a=0.0, b=0.01, rho=0.0, m=0.0, sigma=0.1)
        result = fit(sd, model)

        assert result.success
        assert result.rmse < 1e-10
        assert isinstance(result.params, SVIParams)

    def test_fit_with_non_native_coords(self):
        true_params = SVIParams(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.2)
        expiry = 0.5
        strikes = np.linspace(80, 120, 20)
        forward = 100.0
        k = np.log(strikes / forward)
        ivs = svi_implied_vol(k, true_params, expiry)

        # SmileData in (FixedStrike, Volatility) — non-native for SVI
        sd = SmileData.from_mid_vols(strikes=strikes, ivs=ivs, forward=forward, expiry=expiry)
        model = SVIParams(a=0.0, b=0.01, rho=0.0, m=0.0, sigma=0.1)
        result = fit(sd, model)

        assert result.success
        assert result.rmse < 1e-10

    def test_fit_with_custom_initial_params(self):
        true_params = SVIParams(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.2)
        expiry = 0.5
        strikes = np.linspace(85, 115, 12)
        forward = 100.0
        k = np.log(strikes / forward)
        ivs = svi_implied_vol(k, true_params, expiry)

        sd = SmileData.from_mid_vols(strikes=strikes, ivs=ivs, forward=forward, expiry=expiry)
        guess = SVIParams(a=0.03, b=0.08, rho=-0.2, m=0.01, sigma=0.15)
        result = fit(sd, guess, initial_params=guess)

        assert result.success
        assert result.rmse < 1e-6

    def test_fitted_params_within_bounds(self):
        true_params = SVIParams(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.2)
        expiry = 0.5
        strikes = np.linspace(80, 120, 20)
        forward = 100.0
        k = np.log(strikes / forward)
        ivs = svi_implied_vol(k, true_params, expiry)

        sd = SmileData.from_mid_vols(strikes=strikes, ivs=ivs, forward=forward, expiry=expiry)
        model = SVIParams(a=0.0, b=0.01, rho=0.0, m=0.0, sigma=0.1)
        result = fit(sd, model)

        assert result.params.b >= 0
        assert -1 < result.params.rho < 1
        assert result.params.sigma > 0
