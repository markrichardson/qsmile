## 1. SmileData Validation

- [x] 1.1 Add minimum-3-points validation to `SmileData.__post_init__`
- [x] 1.2 Add `y_bid <= y_ask` validation to `SmileData.__post_init__`
- [x] 1.3 Add `FixedStrike` and `MoneynessStrike` positivity checks to `SmileData.__post_init__`
- [x] 1.4 Add `Volatility`, `Variance`, `TotalVariance` non-negativity checks to `SmileData.__post_init__`
- [x] 1.5 Write tests for all new SmileData validation rules

## 2. SmileData Factory Methods

- [x] 2.1 Add `SmileData.from_mid_vols(strikes, ivs, forward, expiry, discount_factor=1.0)` classmethod
- [x] 2.2 Write tests for `from_mid_vols` (construction, sigma_atm derivation, default discount_factor)

## 3. SmileData Plot Method

- [x] 3.1 Add `SmileData.plot(title=...)` method using `plot_bid_ask` with axis labels from coord names
- [x] 3.2 Write tests for `SmileData.plot()`

## 4. Simplify fit_svi

- [x] 4.1 Remove `OptionChainVols` branch from `fit_svi()` — accept `SmileData` only
- [x] 4.2 Update `test_fitting.py` to pass `SmileData` instead of `OptionChainVols`

## 5. Remove OptionChainVols

- [x] 5.1 Delete `src/qsmile/vols.py`
- [x] 5.2 Remove `OptionChainVols` from `src/qsmile/__init__.py` exports
- [x] 5.3 Rewrite `tests/test_vols.py` — keep SmileData-based vol tests, remove OptionChainVols tests
- [x] 5.4 Update `tests/test_to_smile_data.py` to remove OptionChainVols SmileData tests

## 6. Remove UnitisedSpaceVols

- [x] 6.1 Delete `src/qsmile/unitised.py`
- [x] 6.2 Remove `UnitisedSpaceVols` from `src/qsmile/__init__.py` exports
- [x] 6.3 Rewrite `tests/test_unitised.py` — keep SmileData-based unitised tests, remove UnitisedSpaceVols tests
- [x] 6.4 Update `tests/test_to_smile_data.py` to remove UnitisedSpaceVols SmileData tests

## 7. Update Notebooks

- [x] 7.1 Update `book/marimo/notebooks/example.py` to use `SmileData.from_mid_vols` instead of `OptionChainVols.from_mid_vols`
- [x] 7.2 Update `book/marimo/notebooks/chain_demo.py` to remove all `OptionChainVols` / `UnitisedSpaceVols` references

## 8. Update Documentation

- [x] 8.1 Update `README.md` to remove `OptionChainVols` / `UnitisedSpaceVols` references
- [x] 8.2 Update `__init__.py` docstring if present

## 9. Final Validation

- [x] 9.1 Run `make fmt` and fix any formatting issues
- [x] 9.2 Run `make test` and verify all tests pass
- [x] 9.3 Run `make deptry` and verify no dependency issues
