## Why

`VolData` and `SmileModel` represent the same concept — a volatility smile in some coordinate system — but expose different public interfaces. `SmileModel` has a clean lazy-transform pattern (`transform()` just relabels, `evaluate()` and `plot()` handle conversion on the fly), while `VolData` eagerly transforms data arrays and uses differently-named coordinate fields (`x_coord`/`y_coord` vs `current_x_coord`/`current_y_coord`). This forces calling code to know which type it's working with and prevents polymorphic usage (e.g. overlaying data and model on the same axes with one code path).

## What Changes

- **BREAKING**: Rename `VolData.x_coord` → `current_x_coord` and `VolData.y_coord` → `current_y_coord` to match `SmileModel`.
- Add `native_x_coord` and `native_y_coord` to `VolData` to record the coordinate system data was originally constructed in.
- Make `VolData.transform()` lightweight (just update current coord labels), storing data internally in native coordinates and transforming lazily via property accessors.
- Add `VolData.evaluate(x)` method that interpolates the mid-smile at arbitrary x values in the current coordinate system.
- Unify `VolData.plot()` signature to accept `std_range` and `n_points` parameters like `SmileModel.plot()`, using standardised-strike space to define the plot domain.

## Capabilities

### New Capabilities
- `voldata-lazy-transform`: VolData stores data in native coordinates and transforms lazily via accessors, analogous to SmileModel's transform pattern.
- `voldata-evaluate`: VolData exposes an `evaluate(x)` interpolation method matching SmileModel's evaluate signature.

### Modified Capabilities
- `smile-data`: VolData field names change (`x_coord` → `current_x_coord`, `y_coord` → `current_y_coord`) and transform becomes lazy.

## Impact

- **src/qsmile/data/vols.py**: Major refactor of `VolData` internals — native storage, lazy transform, new `evaluate()`.
- **src/qsmile/models/base.py**: No changes (SmileModel is the target interface).
- **tests/data/**: Tests that reference `x_coord`/`y_coord` fields or assume eager transform need updating.
- **src/qsmile/data/prices.py**: `to_vols()` constructs VolData — may need to set native coords.
- **book/marimo/notebooks/**: Notebooks referencing `.x_coord`/`.y_coord` need updating.
- **No new dependencies**.
