"""Tests for qsmile.models.fitting."""

from __future__ import annotations

import numpy as np
import pandas as pd

from qsmile.core.coords import XCoord, YCoord
from qsmile.data.meta import SmileMetadata
from qsmile.data.vols import SmileData
from qsmile.models.result import fit
from qsmile.models.svi import SVIModel

# Reusable known-good parameters for synthetic round-trip tests
_FIT_META = SmileMetadata(
    date=pd.Timestamp("2024-01-01"),
    expiry=pd.Timestamp("2024-07-01"),
    forward=100.0,
    sigma_atm=0.2,
)
_TRUE_PARAMS = SVIModel(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.2, metadata=_FIT_META)


def _make_synthetic_sd(
    params: SVIModel = _TRUE_PARAMS,
    forward: float = 100.0,
    n_strikes: int = 20,
    strike_lo: float = 80.0,
    strike_hi: float = 120.0,
) -> SmileData:
    """Generate SmileData from known SVI parameters (noiseless)."""
    meta = SmileMetadata(
        date=pd.Timestamp("2024-01-01"),
        expiry=pd.Timestamp("2024-07-01"),
        forward=forward,
    )
    strikes = np.linspace(strike_lo, strike_hi, n_strikes)
    k = np.log(strikes / forward)
    ivs = params.transform(XCoord.LogMoneynessStrike, YCoord.Volatility).evaluate(k)
    return SmileData.from_mid_vols(strikes=strikes, ivs=ivs, metadata=meta)


class TestFitSyntheticRoundTrip:
    """Fit SVI to data generated from known parameters and recover them."""

    def test_recover_known_params(self):
        sd = _make_synthetic_sd()
        result = fit(sd, SVIModel)

        assert result.success
        assert result.rmse < 1e-10
        np.testing.assert_allclose(result.model.a, _TRUE_PARAMS.a, atol=1e-6)
        np.testing.assert_allclose(result.model.b, _TRUE_PARAMS.b, atol=1e-6)
        np.testing.assert_allclose(result.model.rho, _TRUE_PARAMS.rho, atol=1e-6)
        np.testing.assert_allclose(result.model.m, _TRUE_PARAMS.m, atol=1e-6)
        np.testing.assert_allclose(result.model.sigma, _TRUE_PARAMS.sigma, atol=1e-6)

    def test_non_native_coords_accepted(self):
        """SmileData in (FixedStrike, Volatility) — non-native for SVI — still fits."""
        sd = _make_synthetic_sd()
        result = fit(sd, SVIModel)

        assert result.success
        assert result.rmse < 1e-10


class TestFitNoisyData:
    """Fit to market-like noisy data."""

    def test_noisy_fit_succeeds(self):
        date = pd.Timestamp("2024-01-01")
        expiry_ts = pd.Timestamp("2025-01-01")
        noisy_meta = SmileMetadata(date=date, expiry=expiry_ts, forward=100.0, sigma_atm=0.2)
        true_params = SVIModel(a=0.04, b=0.12, rho=-0.4, m=0.01, sigma=0.25, metadata=noisy_meta)
        strikes = np.linspace(80, 120, 15)
        forward = 100.0
        k = np.log(strikes / forward)
        ivs_clean = true_params.transform(XCoord.LogMoneynessStrike, YCoord.Volatility).evaluate(k)

        rng = np.random.default_rng(42)
        noise = rng.normal(0, 0.002, size=ivs_clean.shape)
        ivs_noisy = ivs_clean + noise

        sd = SmileData.from_mid_vols(
            strikes=strikes,
            ivs=ivs_noisy,
            metadata=noisy_meta,
        )
        result = fit(sd, SVIModel)

        assert result.success
        assert result.rmse < 0.01


class TestFitCustomInitialGuess:
    """Test that a custom initial guess is used."""

    def test_custom_initial_params(self):
        sd = _make_synthetic_sd(n_strikes=12, strike_lo=85.0, strike_hi=115.0)
        guess = SVIModel(a=0.03, b=0.08, rho=-0.2, m=0.01, sigma=0.15, metadata=_FIT_META)
        result = fit(sd, SVIModel, initial_guess=guess)

        assert result.success
        assert result.rmse < 1e-6


class TestSmileResult:
    """SmileResult properties: residuals, rmse, evaluate, param bounds."""

    def test_residuals_shape(self):
        sd = _make_synthetic_sd(n_strikes=10, strike_lo=85.0, strike_hi=115.0)
        result = fit(sd, SVIModel)

        assert result.residuals.shape == (10,)
        assert isinstance(result.rmse, float)
        assert isinstance(result.model, SVIModel)

    def test_fitted_params_within_bounds(self):
        sd = _make_synthetic_sd()
        result = fit(sd, SVIModel)

        assert result.model.b >= 0
        assert -1 < result.model.rho < 1
        assert result.model.sigma > 0
