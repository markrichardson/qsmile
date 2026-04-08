## 1. Core Implementation

- [x] 1.1 Update `src/qsmile/data/vols.py`: add `metadata: SmileMetadata | None = None` parameter to `from_mid_vols`, implement dispatch logic (metadata takes precedence, derive `sigma_atm` from data, raise `TypeError` if `metadata.forward is None`)
- [x] 1.2 Make scalar params (`forward`, `date`, `expiry`, `discount_factor`, `daycount`) default to `None` so they are truly optional when `metadata` is provided

## 2. Tests

- [x] 2.1 Add tests in `tests/data/test_vols.py` for the new `metadata=` overload: construction, `sigma_atm` recomputation, `forward=None` rejection, precedence over scalar params
- [x] 2.2 Update existing `from_mid_vols` call sites in `tests/models/test_fitting.py` and `tests/models/test_sabr_fitting.py` to use `SmileMetadata` where appropriate

## 3. Documentation and Examples

- [x] 3.1 Update `README.md` quickstart example to show both scalar-param and `SmileMetadata`-based `from_mid_vols` usage
- [x] 3.2 Update `book/marimo/notebooks/qsmile_demo.py` to use `SmileMetadata`-based construction (no changes needed — notebook uses `chain.to_smile_data()`, not `from_mid_vols`)

## 4. Validation

- [x] 4.1 Run `make test` — all tests pass
- [x] 4.2 Run `make fmt` — formatting clean
