"""Tests for to_smile_data() methods on existing classes."""

from __future__ import annotations

import numpy as np

from qsmile.black76 import black76_call
from qsmile.coords import XCoord, YCoord
from qsmile.prices import OptionChain


class TestOptionChainToSmileData:
    def test_coordinates(self) -> None:
        strikes = np.array([90.0, 95.0, 100.0, 105.0, 110.0])
        forward = 100.0
        discount_factor = 0.99
        expiry = 0.25
        vols = np.array([0.23, 0.21, 0.19, 0.21, 0.23])

        call_bid = np.array(
            [
                float(black76_call(forward, K, discount_factor, v - 0.01, expiry))
                for K, v in zip(strikes, vols, strict=False)
            ]
        )
        call_ask = np.array(
            [
                float(black76_call(forward, K, discount_factor, v + 0.01, expiry))
                for K, v in zip(strikes, vols, strict=False)
            ]
        )
        # Use put-call parity: P = C - D*(F - K) for puts
        put_bid = call_bid - discount_factor * (forward - strikes)
        put_ask = call_ask - discount_factor * (forward - strikes)
        put_bid = np.maximum(put_bid, 0.0)
        put_ask = np.maximum(put_ask, 0.0)
        # Ensure put_bid <= put_ask
        put_bid, put_ask = np.minimum(put_bid, put_ask), np.maximum(put_bid, put_ask)

        prices = OptionChain(
            strikes=strikes,
            call_bid=call_bid,
            call_ask=call_ask,
            put_bid=put_bid,
            put_ask=put_ask,
            expiry=expiry,
            forward=forward,
            discount_factor=discount_factor,
        )
        sd = prices.to_smile_data()
        assert sd.x_coord == XCoord.FixedStrike
        assert sd.y_coord == YCoord.Price
        np.testing.assert_array_equal(sd.x, prices.strikes)
        np.testing.assert_array_equal(sd.y_bid, prices.call_bid)
        np.testing.assert_array_equal(sd.y_ask, prices.call_ask)
        assert sd.metadata.forward == prices.forward
        assert sd.metadata.discount_factor == prices.discount_factor
        assert sd.metadata.expiry == prices.expiry
