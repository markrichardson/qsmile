## 1. Dependencies & New Module

- [x] 1.1 Add `pandas` to production dependencies in `pyproject.toml`
- [x] 1.2 Create `src/qsmile/core/daycount.py` with `DayCount` enum (`ACT365`, `ACT360`) and `year_fraction` method
- [x] 1.3 Export `DayCount` from `src/qsmile/__init__.py`
- [x] 1.4 Write tests for `DayCount` in `tests/core/test_daycount.py`

## 2. SmileMetadata Refactor

- [x] 2.1 Update `src/qsmile/data/meta.py`: change `expiry: float` to `date: pd.Timestamp` and `expiry: pd.Timestamp`, add `daycount: DayCount = DayCount.ACT365`, add `texpiry` property, update validation
- [x] 2.2 Update `tests/data/test_metadata.py`: all SmileMetadata constructions use Timestamps, add tests for `texpiry`, date ordering, daycount variants

## 3. Downstream Source Migration (`meta.expiry` → `meta.texpiry`)

- [x] 3.1 Update `src/qsmile/core/maps.py`: all `meta.expiry` → `meta.texpiry`
- [x] 3.2 Update `src/qsmile/data/prices.py`: all `meta.expiry` → `meta.texpiry`, update `SmileMetadata` constructions in `filter()`, update `to_smile_data()` assert style
- [x] 3.3 Update `src/qsmile/data/vols.py`: `from_mid_vols` signature change (`expiry` → `date`/`expiry`/`daycount`), all `meta.expiry` → `meta.texpiry` internally
- [x] 3.4 Update `src/qsmile/core/black76.py` if any SmileMetadata references exist (verify)
- [x] 3.5 Update `src/qsmile/__init__.py` exports if needed

## 4. Test Migration

- [x] 4.1 Update `tests/core/test_maps.py`: all SmileMetadata constructions use Timestamps
- [x] 4.2 Update `tests/core/test_coords.py`: all SmileMetadata constructions use Timestamps
- [x] 4.3 Update `tests/data/test_vols.py`: all SmileMetadata constructions use Timestamps, update `from_mid_vols` calls
- [x] 4.4 Update `tests/data/test_prices.py`: all SmileMetadata constructions use Timestamps
- [x] 4.5 Update `tests/core/test_plot.py`: SmileMetadata construction uses Timestamps
- [x] 4.6 Update `tests/models/test_*.py`: all SmileMetadata constructions use Timestamps
- [x] 4.7 Update `tests/benchmarks/` and `tests/stress/`: all SmileMetadata constructions use Timestamps

## 5. Docs & Notebooks

- [x] 5.1 Update `README.md`: SmileMetadata examples use Timestamps and DayCount
- [x] 5.2 Update `book/marimo/notebooks/qsmile_demo.py`: SmileMetadata construction with Timestamps
- [x] 5.3 Update `book/marimo/notebooks/sabr_demo.py` if SmileMetadata is used

## 6. Validation

- [x] 6.1 Run `make fmt` and fix any issues
- [x] 6.2 Run `make test` and verify all tests pass
- [x] 6.3 Run `make typecheck` and fix any type errors
