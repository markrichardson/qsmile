## 1. Refactor VolData internals to native storage

- [x] 1.1 Add `_native_x_coord` and `_native_y_coord` private fields to `VolData`; set them from constructor args. Add `native_x_coord` and `native_y_coord` read-only properties.
- [x] 1.2 Rename `x_coord` → `current_x_coord` and `y_coord` → `current_y_coord` in the `VolData` dataclass definition.
- [x] 1.3 Rewrite `transform()` to be lightweight: return a shallow copy with updated `current_x_coord`/`current_y_coord`, sharing the same `StrikeArray`.
- [x] 1.4 Rewrite `x`, `y_bid`, `y_ask`, `y_mid` property accessors to apply coordinate transforms lazily from native to current coords.

## 2. Add evaluate() method

- [x] 2.1 Implement `evaluate(x)` method using `scipy.interpolate.CubicSpline` on `y_mid` in current coordinates, returning `NaN` outside the data domain.
- [x] 2.2 Ensure `evaluate()` accepts array-like input and returns `NDArray[np.float64]`.

## 3. Update all references to renamed fields

- [x] 3.1 Update `src/qsmile/data/prices.py` (`to_vols()` and any other code referencing `x_coord`/`y_coord`).
- [x] 3.2 Update `src/qsmile/data/io.py` if it references `x_coord`/`y_coord`.
- [x] 3.3 Update `src/qsmile/models/` files that interact with VolData coord fields.
- [x] 3.4 Update all test files referencing `x_coord`/`y_coord` on VolData instances.
- [x] 3.5 Update notebook files (`fitting_demo.py`, `qsmile_demo.py`) for renamed fields.

## 4. Update tests

- [x] 4.1 Add tests for native coord storage: verify `native_x_coord`/`native_y_coord` are set at construction and unchanged after transform.
- [x] 4.2 Add tests for lightweight transform: verify `transform()` shares the same `StrikeArray` and only updates current coord labels.
- [x] 4.3 Add tests for lazy accessor transforms: verify `x`, `y_bid`, `y_ask` return transformed values matching the old eager-transform output.
- [x] 4.4 Add tests for `evaluate()`: at data points, between points, outside domain (NaN), and in transformed coordinates.
- [x] 4.5 Update existing VolData tests that assumed eager transform semantics.

## 5. Validation

- [x] 5.1 Run `make test` — all tests pass with ≥90% coverage.
- [x] 5.2 Run `make fmt` — no formatting issues.
