## 1. Collapse SmileModel Protocol + AbstractSmileModel into single SmileModel ABC

- [x] 1.1 In `src/qsmile/models/protocol.py`: delete the `SmileModel` Protocol class entirely
- [x] 1.2 Rename `AbstractSmileModel` to `SmileModel` in `protocol.py`
- [x] 1.3 Rename abstract method `evaluate()` to `_evaluate()` on `SmileModel`
- [x] 1.4 Move `__call__` coordinate-aware logic into a new concrete `evaluate()` method on `SmileModel`
- [x] 1.5 Delete `__call__` method from `SmileModel`
- [x] 1.6 Update `M = TypeVar("M", bound=SmileModel)` to reference the ABC

## 2. Update SVIModel

- [x] 2.1 Change `SVIModel` base class from `AbstractSmileModel` to `SmileModel`
- [x] 2.2 Rename `SVIModel.evaluate()` to `SVIModel._evaluate()`
- [x] 2.3 Delete `SVIModel.implied_vol()` method entirely

## 3. Update SABRModel

- [x] 3.1 Change `SABRModel` base class from `AbstractSmileModel` to `SmileModel`
- [x] 3.2 Rename `SABRModel.evaluate()` to `SABRModel._evaluate()`

## 4. Update Fitting

- [x] 4.1 In `fitting.py`: change `_residuals()` to call `fitted._evaluate(x_obs)` instead of `fitted.evaluate(x_obs)`
- [x] 4.2 Update imports in `fitting.py` — remove Protocol import, use `SmileModel` ABC

## 5. Update Exports

- [x] 5.1 Update `src/qsmile/models/__init__.py` — remove `AbstractSmileModel`, keep `SmileModel`
- [x] 5.2 Update `src/qsmile/__init__.py` — remove `AbstractSmileModel`, keep `SmileModel`

## 6. Update Tests

- [x] 6.1 Update `tests/models/test_abstract_smile_model.py` — rename to `test_smile_model.py`, update all imports and references from `AbstractSmileModel` to `SmileModel`, replace `__call__` tests with `evaluate()` tests, remove Protocol isinstance checks
- [x] 6.2 Update `tests/models/test_svi.py` — replace `AbstractSmileModel` → `SmileModel` references, remove `implied_vol` tests, replace `__call__` tests with `evaluate()`, update isinstance to check `SmileModel` ABC
- [x] 6.3 Update `tests/models/test_sabr.py` — replace `__call__` tests with `evaluate()`, update isinstance to check `SmileModel` ABC
- [x] 6.4 Update `tests/models/test_fitting.py` — replace `implied_vol()` calls with `transform().evaluate()` in synthetic data generation
- [x] 6.5 Update `tests/models/test_sabr_fitting.py` — no `implied_vol` usage, verify existing tests pass with renamed evaluate

## 7. Update Notebook

- [x] 7.1 Update `book/marimo/notebooks/qsmile_demo.py` — replace `implied_vol()` calls with `transform().evaluate()`, remove `__call__` usage if present

## 8. Validate

- [x] 8.1 Run `make test` and fix any failures
- [x] 8.2 Run `make fmt` to ensure formatting compliance
