## Why

`SmileData.from_mid_vols` currently takes `forward`, `date`, `expiry`, `discount_factor`, and `daycount` as individual parameters and internally assembles a `SmileMetadata`. This duplicates information that `SmileMetadata` already encapsulates and forces every call site to unpack/repack metadata fields. Adding a `SmileMetadata`-accepting overload (or making it the primary API) reduces coupling, simplifies call sites, and makes the factory consistent with the rest of the data model where `SmileMetadata` is the standard metadata carrier (e.g. `OptionChain`).

## What Changes

- Add an alternative `SmileData.from_mid_vols` signature that accepts a `SmileMetadata` object directly instead of separate `forward`/`date`/`expiry`/`discount_factor`/`daycount` parameters.
- Keep the existing scalar-parameter signature as a convenience overload for backwards compatibility.
- Update the README quickstart example to showcase the `SmileMetadata`-based construction.
- Update tests and notebooks to prefer the `SmileMetadata`-based construction where appropriate.

## Capabilities

### New Capabilities
- `metadata-factory-overload`: `SmileData.from_mid_vols` accepts a `SmileMetadata` object as an alternative to individual scalar parameters.

### Modified Capabilities
- `smile-data-factories`: `from_mid_vols` gains a metadata-based overload alongside the existing scalar-parameter signature.

## Impact

- **Code**: `src/qsmile/data/vols.py` (`from_mid_vols` method).
- **Tests**: `tests/data/test_vols.py`, `tests/models/test_fitting.py`, `tests/models/test_sabr_fitting.py` — call sites updated to use `SmileMetadata` where appropriate.
- **Docs**: `README.md` quickstart example updated.
- **Notebooks**: `book/marimo/notebooks/qsmile_demo.py` updated.
- **APIs**: No breaking changes — existing scalar-parameter signature remains supported.
- **Dependencies**: None.
