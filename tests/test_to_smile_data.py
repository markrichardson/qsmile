"""Tests for to_smile_data() methods on existing classes."""

from __future__ import annotations

import numpy as np

from qsmile.coords import XCoord, YCoord
from qsmile.vols import OptionChainVols


class TestOptionChainVolsToSmileData:
    def test_coordinates(self) -> None:
        chain = OptionChainVols(
            strikes=np.array([90.0, 95.0, 100.0, 105.0, 110.0]),
            vol_bid=np.array([0.22, 0.20, 0.18, 0.20, 0.22]),
            vol_ask=np.array([0.24, 0.22, 0.20, 0.22, 0.24]),
            forward=100.0,
            discount_factor=0.99,
            expiry=0.25,
        )
        sd = chain.to_smile_data()
        assert sd.x_coord == XCoord.FixedStrike
        assert sd.y_coord == YCoord.Volatility
        np.testing.assert_array_equal(sd.x, chain.strikes)
        np.testing.assert_array_equal(sd.y_bid, chain.vol_bid)
        np.testing.assert_array_equal(sd.y_ask, chain.vol_ask)
        assert sd.metadata.forward == chain.forward
        assert sd.metadata.discount_factor == chain.discount_factor
        assert sd.metadata.expiry == chain.expiry
        assert sd.metadata.sigma_atm == chain.sigma_atm


class TestOptionChainPricesToSmileData:
    def test_coordinates(self) -> None:
        chain = OptionChainVols(
            strikes=np.array([90.0, 95.0, 100.0, 105.0, 110.0]),
            vol_bid=np.array([0.22, 0.20, 0.18, 0.20, 0.22]),
            vol_ask=np.array([0.24, 0.22, 0.20, 0.22, 0.24]),
            forward=100.0,
            discount_factor=0.99,
            expiry=0.25,
        )
        prices = chain.to_prices()
        sd = prices.to_smile_data()
        assert sd.x_coord == XCoord.FixedStrike
        assert sd.y_coord == YCoord.Price
        np.testing.assert_array_equal(sd.x, prices.strikes)
        np.testing.assert_array_equal(sd.y_bid, prices.call_bid)
        np.testing.assert_array_equal(sd.y_ask, prices.call_ask)
        assert sd.metadata.forward == prices.forward
        assert sd.metadata.discount_factor == prices.discount_factor
        assert sd.metadata.expiry == prices.expiry


class TestUnitisedSpaceVolsToSmileData:
    def test_coordinates(self) -> None:
        chain = OptionChainVols(
            strikes=np.array([90.0, 95.0, 100.0, 105.0, 110.0]),
            vol_bid=np.array([0.22, 0.20, 0.18, 0.20, 0.22]),
            vol_ask=np.array([0.24, 0.22, 0.20, 0.22, 0.24]),
            forward=100.0,
            discount_factor=0.99,
            expiry=0.25,
        )
        unitised = chain.to_unitised()
        sd = unitised.to_smile_data()
        assert sd.x_coord == XCoord.StandardisedStrike
        assert sd.y_coord == YCoord.TotalVariance
        np.testing.assert_array_equal(sd.x, unitised.k_unitised)
        np.testing.assert_array_equal(sd.y_bid, unitised.variance_bid)
        np.testing.assert_array_equal(sd.y_ask, unitised.variance_ask)
        assert sd.metadata.sigma_atm == unitised.sigma_atm
        assert sd.metadata.expiry == unitised.expiry
