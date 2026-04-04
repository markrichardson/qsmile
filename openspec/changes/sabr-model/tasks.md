## 1. AbstractSmileModel Base Class

- [ ] 1.1 Add `AbstractSmileModel` abstract dataclass to `src/qsmile/models/protocol.py` with default `to_array()`, `from_array()` using `param_names`
- [ ] 1.2 Export `AbstractSmileModel` from `src/qsmile/models/__init__.py` and `src/qsmile/__init__.py`

## 2. Refactor SVIModel

- [ ] 2.1 Refactor `SVIModel` to inherit from `AbstractSmileModel`, removing its `to_array()` and `from_array()` implementations
- [ ] 2.2 Run `make test` to verify all existing 168 tests still pass

## 3. SABRModel Implementation

- [ ] 3.1 Create `src/qsmile/models/sabr.py` with `SABRModel` dataclass: fields `(alpha, beta, rho, nu, expiry, forward)`, `ClassVar` metadata, `__post_init__` validation
- [ ] 3.2 Implement `evaluate(x)` using Hagan (2002) lognormal implied vol approximation
- [ ] 3.3 Implement `initial_guess(x, y)` static method with heuristic from market implied vols
- [ ] 3.4 Export `SABRModel` from `src/qsmile/models/__init__.py` and `src/qsmile/__init__.py`

## 4. Fitting Integration

- [ ] 4.1 Update `fit()` in `fitting.py` to pass `expiry` and `forward` context to `from_array()` for models that need it (e.g. SABR)
- [ ] 4.2 Verify `fit(sd, SABRModel)` works end-to-end with synthetic SABR data

## 5. Tests

- [ ] 5.1 Write tests for `AbstractSmileModel` (cannot instantiate directly, subclass inherits `to_array`/`from_array`)
- [ ] 5.2 Write tests for `SABRModel` validation, evaluate, implied vol, protocol conformance, serialisation
- [ ] 5.3 Write tests for `SABRModel` fitting: synthetic round-trip recovery, noisy data, custom initial guess
- [ ] 5.4 Run `make test` to verify all tests pass with coverage ≥ 90%

## 6. Documentation

- [ ] 6.1 Update README API reference table with `SABRModel` and `AbstractSmileModel`
- [ ] 6.2 Update `.github/agents/tests.md` with SABR test patterns
- [ ] 6.3 Run `make fmt` for final formatting
