"""Tests for SABR model fitting via the generic fit() engine."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from qsmile.data.meta import SmileMetadata
from qsmile.data.vols import SmileData
from qsmile.models.fitting import SmileResult, fit
from qsmile.models.sabr import SABRModel

# Known-good SABR parameters for synthetic round-trip tests
_DATE = pd.Timestamp("2024-01-01")
_EXPIRY = pd.Timestamp("2025-01-01")
_TEXPIRY = (_EXPIRY - _DATE).days / 365.0
_SABR_META = SmileMetadata(date=_DATE, expiry=_EXPIRY, forward=100.0, sigma_atm=0.2)
_TRUE_PARAMS = SABRModel(alpha=0.2, beta=0.5, rho=-0.3, nu=0.4, metadata=_SABR_META)


def _make_synthetic_sabr_sd(
    params: SABRModel = _TRUE_PARAMS,
    n_strikes: int = 20,
    strike_lo: float = 80.0,
    strike_hi: float = 120.0,
) -> SmileData:
    """Generate SmileData from known SABR parameters (noiseless)."""
    strikes = np.linspace(strike_lo, strike_hi, n_strikes)
    k = np.log(strikes / params.metadata.forward)
    ivs = params.evaluate(k)
    # Ensure ivs is an array
    ivs = np.asarray(ivs, dtype=np.float64)
    meta = SmileMetadata(date=_DATE, expiry=_EXPIRY, forward=params.metadata.forward)
    return SmileData.from_mid_vols(strikes=strikes, ivs=ivs, metadata=meta)


class TestFitSABRSyntheticRoundTrip:
    """Fit SABR to noiseless data generated from known parameters."""

    def test_recover_known_params(self):
        sd = _make_synthetic_sabr_sd()
        result = fit(sd, SABRModel)

        assert result.success
        assert result.rmse < 1e-6
        assert isinstance(result.params, SABRModel)
        assert isinstance(result, SmileResult)

    def test_fitted_params_close_to_true(self):
        sd = _make_synthetic_sabr_sd()
        result = fit(sd, SABRModel)

        np.testing.assert_allclose(result.params.alpha, _TRUE_PARAMS.alpha, rtol=0.05)
        np.testing.assert_allclose(result.params.beta, _TRUE_PARAMS.beta, atol=0.1)
        np.testing.assert_allclose(result.params.rho, _TRUE_PARAMS.rho, atol=0.1)
        np.testing.assert_allclose(result.params.nu, _TRUE_PARAMS.nu, rtol=0.1)

    def test_context_fields_preserved(self):
        """Metadata should be on the fitted result."""
        sd = _make_synthetic_sabr_sd()
        result = fit(sd, SABRModel)

        assert result.params.metadata.texpiry == pytest.approx(_SABR_META.texpiry)
        assert result.params.metadata.forward == _SABR_META.forward


class TestFitSABRNoisyData:
    def test_noisy_fit_succeeds(self):
        sd = _make_synthetic_sabr_sd()
        # Add noise to simulated market data
        rng = np.random.default_rng(42)
        noisy_ivs = np.asarray(_TRUE_PARAMS.evaluate(np.log(sd.x / _TRUE_PARAMS.metadata.forward))) + rng.normal(
            0, 0.002, size=sd.x.shape
        )
        meta = SmileMetadata(date=_DATE, expiry=_EXPIRY, forward=_TRUE_PARAMS.metadata.forward)
        sd_noisy = SmileData.from_mid_vols(
            strikes=sd.x,
            ivs=noisy_ivs,
            metadata=meta,
        )
        result = fit(sd_noisy, SABRModel)

        assert result.success
        assert result.rmse < 0.01


class TestFitSABRCustomInitialGuess:
    def test_custom_initial_params(self):
        sd = _make_synthetic_sabr_sd(n_strikes=15, strike_lo=85.0, strike_hi=115.0)
        guess = SABRModel(alpha=0.15, beta=0.4, rho=-0.2, nu=0.3, metadata=_SABR_META)
        result = fit(sd, SABRModel, initial_guess=guess)

        assert result.success
        assert result.rmse < 1e-4
