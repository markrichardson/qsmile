## 1. Dependencies and project setup

- [x] 1.1 Add `numpy` and `scipy` as runtime dependencies in `pyproject.toml`
- [x] 1.2 Update `[tool.deptry.package_module_name_map]` for new dependencies
- [x] 1.3 Run `make install` to sync the environment

## 2. OptionChain data model

- [x] 2.1 Create `src/qsmile/chain.py` with the `OptionChain` dataclass (strikes, ivs, forward, expiry)
- [x] 2.2 Implement `__post_init__` validation (lengths, positivity, minimum data points)
- [x] 2.3 Implement `log_moneyness` property returning `ln(K/F)` array
- [x] 2.4 Implement `total_variance` property returning `iv^2 * T` array
- [x] 2.5 Write tests for `OptionChain` construction, validation, and computed properties in `tests/test_chain.py`

## 3. SVI model

- [x] 3.1 Create `src/qsmile/svi.py` with the `SVIParams` dataclass (a, b, rho, m, sigma)
- [x] 3.2 Implement `__post_init__` validation for SVI parameter constraints
- [x] 3.3 Implement `svi_total_variance(k, params)` evaluation function
- [x] 3.4 Implement `svi_implied_vol(k, params, expiry)` convenience function
- [x] 3.5 Write tests for `SVIParams`, `svi_total_variance`, and `svi_implied_vol` in `tests/test_svi.py`

## 4. Fitting engine

- [x] 4.1 Create `src/qsmile/fitting.py` with the `SmileResult` dataclass
- [x] 4.2 Implement heuristic initial guess computation from option chain data
- [x] 4.3 Implement `fit_svi(chain, initial_params=None)` using `scipy.optimize.least_squares` with box constraints
- [x] 4.4 Implement `SmileResult.evaluate(k)` method
- [x] 4.5 Write tests for `fit_svi` (synthetic round-trip, noisy data, custom initial guess, failed convergence) in `tests/test_fitting.py`

## 5. Public API and cleanup

- [x] 5.1 Update `src/qsmile/__init__.py` to export `OptionChain`, `SVIParams`, `SmileResult`, `fit_svi`, `svi_total_variance`, `svi_implied_vol`
- [x] 5.2 Remove placeholder functions (`greet`, `approximate`) from `src/qsmile/core.py`
- [x] 5.3 Remove or update `tests/test_core.py` to remove tests for deleted functions
- [x] 5.4 Remove `chebfun` dependency from `pyproject.toml` if no longer used
- [x] 5.5 Run `make test` and `make fmt` to verify all tests pass and code is formatted
