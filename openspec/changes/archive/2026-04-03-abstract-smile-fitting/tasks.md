## 1. SmileModel Protocol

- [x] 1.1 Create `src/qsmile/models/protocol.py` with `SmileModel` protocol (native coords, param_names, bounds, evaluate, to_array, from_array, initial_guess)
- [x] 1.2 Export `SmileModel` from `src/qsmile/__init__.py`

## 2. SVIParams Protocol Conformance

- [x] 2.1 Add `native_x_coord`, `native_y_coord`, `param_names` properties to `SVIParams`
- [x] 2.2 Add `bounds` property to `SVIParams`
- [x] 2.3 Add `to_array()` and `from_array()` methods to `SVIParams`
- [x] 2.4 Add `evaluate(x)` method to `SVIParams` (delegates to `svi_total_variance`)
- [x] 2.5 Move `_initial_guess` from `fitting.py` to `SVIParams.initial_guess()` static method

## 3. Generic Fitting

- [x] 3.1 Implement generic `fit(chain: SmileData, model: SmileModel, initial_params: SmileModel | None) -> SmileResult` in `fitting.py`
- [x] 3.2 Refactor `fit_svi()` to delegate to `fit()` with an SVI model instance
- [x] 3.3 Update `SmileResult` — `params` field becomes `SmileModel`, `evaluate()` delegates to `params.evaluate()`
- [x] 3.4 Export `fit` from `src/qsmile/__init__.py`

## 4. Tests

- [x] 4.1 Add protocol conformance tests for `SVIParams` (isinstance, round-trip serialisation, bounds length)
- [x] 4.2 Add tests for generic `fit()` — fit SVI data via generic path, non-native coords, custom initial params
- [x] 4.3 Verify existing `test_fitting.py` and `test_svi.py` still pass (update as needed for API changes)

## 5. Cleanup

- [x] 5.1 Update notebook imports if needed
- [x] 5.2 Run `make fmt` and `make test` to verify everything passes
