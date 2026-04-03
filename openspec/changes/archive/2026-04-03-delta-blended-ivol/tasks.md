## 1. Delta-blend core function

- [x] 1.1 Implement `delta_blend_ivols(call_bid_ivols, call_ask_ivols, put_bid_ivols, put_ask_ivols, strikes, forward, expiry)` in `src/qsmile/data/prices.py` that computes delta weights from mid call-implied vol and returns blended bid/ask vol arrays, handling inversion failures gracefully
- [x] 1.2 Export `delta_blend_ivols` from `src/qsmile/__init__.py`

## 2. OptionChain integration

- [x] 2.1 Add `to_smile_data_blended()` method on `OptionChain` that inverts both call and put prices to bid/ask vols, calls `delta_blend_ivols`, and returns a `SmileData` with `(FixedStrike, Volatility)` coordinates and auto-derived `sigma_atm`
- [x] 2.2 Update `option-chain-prices` spec description to note `to_smile_data()` is not the sole conversion method (it now has a blended sibling)

## 3. Tests

- [x] 3.1 Add tests for `delta_blend_ivols`: ATM equal-weighting, deep OTM convergence to pure call/put vol, smooth monotonic weights, bid/ask independence
- [x] 3.2 Add tests for `to_smile_data_blended()`: correct coordinates and metadata, sigma_atm derivation, precondition error when uncalibrated
- [x] 3.3 Add tests for inversion failure fallback: call-only, put-only, and neither-available scenarios
- [x] 3.4 Run `make fmt` and `make test` to verify everything passes
