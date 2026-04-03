"""Tests for coordinate maps and composition."""

from __future__ import annotations

import numpy as np
import pytest

from qsmile.core.coords import XCoord, YCoord
from qsmile.core.maps import (
    apply_x_chain,
    apply_y_chain,
    compose_x_maps,
    compose_y_maps,
)
from qsmile.data.metadata import SmileMetadata

META = SmileMetadata(forward=100.0, discount_factor=0.99, expiry=0.25, sigma_atm=0.20)
STRIKES = np.array([90.0, 95.0, 100.0, 105.0, 110.0])


class TestXMaps:
    def test_fixed_to_moneyness(self) -> None:
        chain = compose_x_maps(XCoord.FixedStrike, XCoord.MoneynessStrike)
        result = apply_x_chain(STRIKES, chain, META)
        np.testing.assert_allclose(result, STRIKES / META.forward)

    def test_moneyness_to_fixed(self) -> None:
        moneyness = STRIKES / META.forward
        chain = compose_x_maps(XCoord.MoneynessStrike, XCoord.FixedStrike)
        result = apply_x_chain(moneyness, chain, META)
        np.testing.assert_allclose(result, STRIKES)

    def test_moneyness_to_log_moneyness(self) -> None:
        moneyness = STRIKES / META.forward
        chain = compose_x_maps(XCoord.MoneynessStrike, XCoord.LogMoneynessStrike)
        result = apply_x_chain(moneyness, chain, META)
        np.testing.assert_allclose(result, np.log(moneyness))

    def test_log_moneyness_to_moneyness(self) -> None:
        log_m = np.log(STRIKES / META.forward)
        chain = compose_x_maps(XCoord.LogMoneynessStrike, XCoord.MoneynessStrike)
        result = apply_x_chain(log_m, chain, META)
        np.testing.assert_allclose(result, STRIKES / META.forward)

    def test_log_moneyness_to_standardised(self) -> None:
        log_m = np.log(STRIKES / META.forward)
        chain = compose_x_maps(XCoord.LogMoneynessStrike, XCoord.StandardisedStrike)
        result = apply_x_chain(log_m, chain, META)
        expected = log_m / (META.sigma_atm * np.sqrt(META.expiry))
        np.testing.assert_allclose(result, expected)

    def test_standardised_to_log_moneyness(self) -> None:
        log_m = np.log(STRIKES / META.forward)
        std = log_m / (META.sigma_atm * np.sqrt(META.expiry))
        chain = compose_x_maps(XCoord.StandardisedStrike, XCoord.LogMoneynessStrike)
        result = apply_x_chain(std, chain, META)
        np.testing.assert_allclose(result, log_m)

    def test_round_trip_fixed_to_standardised(self) -> None:
        fwd = compose_x_maps(XCoord.FixedStrike, XCoord.StandardisedStrike)
        inv = compose_x_maps(XCoord.StandardisedStrike, XCoord.FixedStrike)
        intermediate = apply_x_chain(STRIKES, fwd, META)
        recovered = apply_x_chain(intermediate, inv, META)
        np.testing.assert_allclose(recovered, STRIKES, rtol=1e-12)

    def test_standardised_requires_sigma_atm(self) -> None:
        meta_no_atm = SmileMetadata(forward=100.0, discount_factor=0.99, expiry=0.25)
        log_m = np.log(STRIKES / meta_no_atm.forward)
        chain = compose_x_maps(XCoord.LogMoneynessStrike, XCoord.StandardisedStrike)
        with pytest.raises(ValueError, match="sigma_atm is required"):
            apply_x_chain(log_m, chain, meta_no_atm)


class TestYMaps:
    def test_vol_to_variance(self) -> None:
        vols = np.array([0.15, 0.18, 0.20, 0.22, 0.25])
        chain = compose_y_maps(YCoord.Volatility, YCoord.Variance)
        result = apply_y_chain(vols, STRIKES, chain, META, XCoord.FixedStrike, XCoord.FixedStrike)
        np.testing.assert_allclose(result, vols**2)

    def test_variance_to_vol(self) -> None:
        variances = np.array([0.04, 0.05, 0.06, 0.07, 0.08])
        chain = compose_y_maps(YCoord.Variance, YCoord.Volatility)
        result = apply_y_chain(variances, STRIKES, chain, META, XCoord.FixedStrike, XCoord.FixedStrike)
        np.testing.assert_allclose(result, np.sqrt(variances))

    def test_variance_to_total_variance(self) -> None:
        variances = np.array([0.04, 0.05, 0.06, 0.07, 0.08])
        chain = compose_y_maps(YCoord.Variance, YCoord.TotalVariance)
        result = apply_y_chain(variances, STRIKES, chain, META, XCoord.FixedStrike, XCoord.FixedStrike)
        np.testing.assert_allclose(result, variances * META.expiry)

    def test_total_variance_to_variance(self) -> None:
        total_var = np.array([0.01, 0.012, 0.015, 0.018, 0.02])
        chain = compose_y_maps(YCoord.TotalVariance, YCoord.Variance)
        result = apply_y_chain(total_var, STRIKES, chain, META, XCoord.FixedStrike, XCoord.FixedStrike)
        np.testing.assert_allclose(result, total_var / META.expiry)

    def test_vol_to_price_and_back(self) -> None:
        vols = np.array([0.20, 0.20, 0.20, 0.20, 0.20])
        fwd = compose_y_maps(YCoord.Volatility, YCoord.Price)
        prices = apply_y_chain(vols, STRIKES, fwd, META, XCoord.FixedStrike, XCoord.FixedStrike)
        assert np.all(prices > 0)

        inv = compose_y_maps(YCoord.Price, YCoord.Volatility)
        recovered = apply_y_chain(prices, STRIKES, inv, META, XCoord.FixedStrike, XCoord.FixedStrike)
        np.testing.assert_allclose(recovered, vols, atol=1e-10)

    def test_round_trip_vol_to_total_variance(self) -> None:
        vols = np.array([0.15, 0.18, 0.20, 0.22, 0.25])
        fwd = compose_y_maps(YCoord.Volatility, YCoord.TotalVariance)
        inv = compose_y_maps(YCoord.TotalVariance, YCoord.Volatility)
        intermediate = apply_y_chain(vols, STRIKES, fwd, META, XCoord.FixedStrike, XCoord.FixedStrike)
        recovered = apply_y_chain(intermediate, STRIKES, inv, META, XCoord.FixedStrike, XCoord.FixedStrike)
        np.testing.assert_allclose(recovered, vols, rtol=1e-12)


class TestComposition:
    def test_identity(self) -> None:
        chain = compose_x_maps(XCoord.FixedStrike, XCoord.FixedStrike)
        assert len(chain) == 0

    def test_adjacent_one_step(self) -> None:
        chain = compose_x_maps(XCoord.FixedStrike, XCoord.MoneynessStrike)
        assert len(chain) == 1

    def test_multi_step(self) -> None:
        chain = compose_x_maps(XCoord.FixedStrike, XCoord.StandardisedStrike)
        assert len(chain) == 3

    def test_y_identity(self) -> None:
        chain = compose_y_maps(YCoord.Volatility, YCoord.Volatility)
        assert len(chain) == 0

    def test_y_adjacent(self) -> None:
        chain = compose_y_maps(YCoord.Volatility, YCoord.Variance)
        assert len(chain) == 1

    def test_y_multi_step(self) -> None:
        chain = compose_y_maps(YCoord.Price, YCoord.TotalVariance)
        assert len(chain) == 3
