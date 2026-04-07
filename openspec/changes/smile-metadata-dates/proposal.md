## Why

`SmileMetadata.expiry` is currently a bare `float` (time-to-expiry in years), forcing every caller to compute the year fraction externally and discarding the original dates. This loses information (valuation date, expiry date) that downstream analytics — Greeks, term-structure interpolation, roll analysis — need. It also leaves the day-count convention implicit, making it impossible to reproduce the float from first principles or switch conventions.

## What Changes

- **BREAKING**: `SmileMetadata.expiry` changes from `float` (year fraction) to `pd.Timestamp` (expiry date).
- Add `date: pd.Timestamp` field — the valuation/pricing date.
- Add `texpiry: float` — derived year fraction, computed from `(date, expiry, daycount)`. This replaces the old `expiry: float` semantics. Read-only, computed in `__post_init__`.
- Add `daycount: DayCount` field — day-count convention enum with a sensible default (`ACT365`).
- Introduce a `DayCount` enum with `year_fraction(start, end) -> float` method. Initial variants: `ACT365`, `ACT360`.
- All internal code currently reading `meta.expiry` (float) migrates to `meta.texpiry`.
- `pandas` moves from dev-only to a production dependency.

## Capabilities

### New Capabilities
- `daycount`: `DayCount` enum defining day-count conventions with a `year_fraction(start, end)` method. Initial variants `ACT365` (default) and `ACT360`.

### Modified Capabilities
- `smile-metadata`: Fields change — `date` and `expiry` become `pd.Timestamp`, `texpiry` is a derived `float`, `daycount: DayCount` added with default `ACT365`. Validation updated.
- `smile-data-factories`: `from_mid_vols` signature changes — `expiry` parameter replaced by `date`/`expiry` timestamps (or accepts the new SmileMetadata directly).
- `option-chain`: SmileMetadata construction changes — callers must supply `date` and `expiry` timestamps.
- `option-chain-prices`: References to `meta.expiry` in requirement text update to `meta.texpiry`.
- `coordinate-maps`: References to `meta.expiry` in transformation formulae update to `meta.texpiry`.

## Impact

- **Production dependency**: `pandas` added to `project.dependencies` in `pyproject.toml`.
- **Source code** (`src/qsmile/`): Every file reading `meta.expiry` as a float must switch to `meta.texpiry`. New `DayCount` enum module created under `src/qsmile/core/`.
- **Tests** (`tests/`): ~30 `SmileMetadata(...)` constructions across test files must supply `date` and `expiry` as Timestamps.
- **Notebooks/docs**: `README.md`, `qsmile_demo.py`, `sabr_demo.py` updated.
- **SABRModel**: Has its own `expiry: float` field (independent of SmileMetadata) — out of scope for this change.
