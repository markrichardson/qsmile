## 1. Dependencies and project setup

- [x] 1.1 Add `cvxpy` to project dependencies in `pyproject.toml`
- [x] 1.2 Add `matplotlib` as an optional dependency in `pyproject.toml`
- [x] 1.3 Run `make install` to verify dependencies resolve

## 2. Black76 module

- [x] 2.1 Create `src/qsmile/black76.py` with `black76_call` and `black76_put` functions (vectorised, with input validation)
- [x] 2.2 Implement `black76_implied_vol` using `scipy.optimize.brentq` with no-arbitrage bound checks
- [x] 2.3 Write tests in `tests/test_black76.py` covering call/put pricing, put-call parity, edge cases, and implied vol round-trips

## 3. OptionChainPrices

- [x] 3.1 Create `src/qsmile/prices.py` with `OptionChainPrices` dataclass (strikes, call_bid, call_ask, put_bid, put_ask, expiry, optional forward/discount_factor)
- [x] 3.2 Implement input validation in `__post_init__` (array lengths, non-negative prices, bid ≤ ask, positive strikes/expiry)
- [x] 3.3 Implement `call_mid` and `put_mid` properties
- [x] 3.4 Implement delta-blend weighted least-squares forward/DF calibration via cvxpy in a private `_calibrate_forward_df` function
- [x] 3.5 Implement `to_vols()` method converting prices to `OptionChainVols` via Black76 implied vol inversion
- [x] 3.6 Write tests in `tests/test_prices.py` covering construction, validation, calibration accuracy, and price-to-vol conversion

## 4. OptionChainVols

- [x] 4.1 Create `src/qsmile/vols.py` with `OptionChainVols` dataclass (strikes, vol_bid, vol_ask, forward, discount_factor, expiry)
- [x] 4.2 Implement input validation in `__post_init__`
- [x] 4.3 Implement `vol_mid`, `log_moneyness`, and `sigma_atm` properties
- [x] 4.4 Implement `to_unitised()` method producing `UnitisedSpaceVols`
- [x] 4.5 Implement `to_prices()` method converting vols back to `OptionChainPrices` via Black76 pricing
- [x] 4.6 Implement `to_option_chain()` method producing the existing `OptionChain` from mid vols
- [x] 4.7 Write tests in `tests/test_vols.py` covering construction, validation, conversions, and round-trips

## 5. UnitisedSpaceVols

- [x] 5.1 Create `src/qsmile/unitised.py` with `UnitisedSpaceVols` dataclass (k_unitised, variance_bid, variance_ask, sigma_atm, expiry)
- [x] 5.2 Implement input validation in `__post_init__`
- [x] 5.3 Implement `variance_mid` property
- [x] 5.4 Implement `to_vols(forward, strikes)` method for inverse transformation
- [x] 5.5 Write tests in `tests/test_unitised.py` covering construction, validation, and round-trip conversion

## 6. Plotting

- [x] 6.1 Create `src/qsmile/plot.py` with shared error-bar plotting utility
- [x] 6.2 Add `.plot()` method to `OptionChainPrices` (calls and puts as separate series with error bars)
- [x] 6.3 Add `.plot()` method to `OptionChainVols` (bid/ask vol error bars vs strike)
- [x] 6.4 Add `.plot()` method to `UnitisedSpaceVols` (bid/ask variance error bars vs unitised k)
- [x] 6.5 Handle missing matplotlib gracefully with `ImportError`
- [x] 6.6 Write tests in `tests/test_plot.py` verifying figure creation and matplotlib-missing error handling

## 7. Public API and integration

- [x] 7.1 Export new classes and functions from `src/qsmile/__init__.py`
- [x] 7.2 Run `make test` to verify all tests pass
- [x] 7.3 Run `make fmt` to format all new code
- [x] 7.4 Run `make deptry` to verify dependency declarations
