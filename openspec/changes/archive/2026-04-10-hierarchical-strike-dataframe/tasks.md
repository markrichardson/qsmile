## 1. StrikeArray Core

- [x] 1.1 Create `src/qsmile/data/strikes.py` with `StrikeArray` class: hierarchical `pd.DataFrame` with two-level `MultiIndex` columns, `__init__`, `set(name, series)`, adaptive union reindexing
- [x] 1.2 Add named setters: `set_call_bid`, `set_call_ask`, `set_put_bid`, `set_put_ask`, `set_volume`, `set_open_interest`
- [x] 1.3 Add read accessors: `strikes` property, `columns`, `values(name)`, `get_values(name)`, `has(name)`, `__len__`
- [x] 1.4 Add `to_dataframe()` and `filter(mask)` methods
- [x] 1.5 Add per-column validation (positive strikes, no duplicates)
- [x] 1.6 Export `StrikeArray` from `src/qsmile/data/__init__.py` and `src/qsmile/__init__.py`

## 2. StrikeArray Tests

- [x] 2.1 Write tests for `StrikeArray` construction, setters, adaptive reindexing, and read accessors
- [x] 2.2 Write tests for `to_dataframe()`, `filter()`, and validation (positive strikes, duplicates)

## 3. OptionChain Refactor

- [x] 3.1 Replace `OptionChain` NDArray fields with `strikedata: StrikeArray` and `metadata: SmileMetadata`
- [x] 3.2 Update `__post_init__` validation to read from `StrikeArray` (min 3 strikes, non-negative prices, bid ≤ ask, volume/open_interest checks)
- [x] 3.3 Update `call_mid`, `put_mid` properties and forward/DF calibration to use `StrikeArray`
- [x] 3.4 Update `to_smile_data()` to build `SmileData` with `StrikeArray`
- [x] 3.5 Update `filter()` method to delegate to `StrikeArray.filter()`

## 4. SmileData Refactor

- [x] 4.1 Replace `SmileData` `x`/`y_bid`/`y_ask`/`volume`/`open_interest` fields with `strikearray: StrikeArray`
- [x] 4.2 Update `__post_init__` validation to read from `StrikeArray`
- [x] 4.3 Update `y_mid` property to read from `StrikeArray`
- [x] 4.4 Update `transform()` to build new `StrikeArray` for the returned `SmileData`
- [x] 4.5 Update `from_mid_vols()` factory to build a `StrikeArray`
- [x] 4.6 Update `plot()` to read from `StrikeArray`

## 5. Consumer Updates

- [x] 5.1 Update `src/qsmile/models/fitting.py` to read from `StrikeArray` API
- [x] 5.2 Update `src/qsmile/data/__init__.py` exports if needed

## 6. Test Updates

- [x] 6.1 Update `tests/data/test_prices.py` — all `OptionChain` construction and assertion code
- [x] 6.2 Update `tests/data/test_vols.py` — all `SmileData` construction and assertion code
- [x] 6.3 Update `tests/models/test_fitting.py` — `SmileData` construction via `from_mid_vols()`
- [x] 6.4 Update `tests/models/test_sabr_fitting.py` — `SmileData` construction via `from_mid_vols()`
- [x] 6.5 Update `tests/core/test_plot.py` — `OptionChain` and `SmileData` construction for plot tests

## 7. Verify

- [x] 7.1 Run `make test` — all tests pass
- [x] 7.2 Run `make fmt` — no lint errors
