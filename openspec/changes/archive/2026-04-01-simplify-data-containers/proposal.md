## Why

The coordinate-transforms work introduced `SmileData` as a unified container with `transform()` for moving between any coordinate system. The legacy API (`to_vols()`, `to_prices()`, `to_unitised()`) has already been removed, so `OptionChainVols` and `UnitisedSpaceVols` are now thin wrappers that convert to `SmileData` and provide little beyond validation and a `plot()` method. Removing them reduces the public API surface, eliminates redundant types, and makes `SmileData` the single representation users learn and work with. `OptionChainPrices` must be kept because it owns put-call parity calibration over 4 Y-arrays — a fundamentally different data shape that `SmileData` cannot hold.

## What Changes

- **BREAKING** Remove `UnitisedSpaceVols` class entirely. Its role (StandardisedStrike/TotalVariance data) is served directly by `SmileData`.
- **BREAKING** Remove `OptionChainVols` class entirely. Its role (FixedStrike/Volatility data) is served directly by `SmileData`.
- Add `SmileData.from_mid_vols(strikes, ivs, forward, expiry, discount_factor=1.0)` factory classmethod to replace `OptionChainVols.from_mid_vols()`.
- Update `fit_svi()` to accept only `SmileData` (drop `OptionChainVols` branch).
- Add coordinate-aware validation to `SmileData` (e.g. positive strikes when FixedStrike, positive vols when Volatility) to replace domain validation previously owned by the removed classes.
- Update notebooks, tests, README, and `__init__.py` exports.

## Capabilities

### New Capabilities
- `smile-data-factories`: Factory classmethods on `SmileData` for common construction patterns (e.g. `from_mid_vols`).
- `smile-data-validation`: Coordinate-aware validation rules in `SmileData.__post_init__` that replace domain checks from removed classes.

### Modified Capabilities
- `smile-fitting`: `fit_svi` signature changes from `OptionChainVols | SmileData` to `SmileData` only.
- `smile-data`: SmileData gains factory methods and richer validation.
- `plotting`: Plot methods previously on `OptionChainVols` and `UnitisedSpaceVols` become a standalone `plot_smile(sd)` function or a `SmileData.plot()` method.
- `option-chain-prices`: `OptionChainPrices` remains but its docs/specs update to reflect that it is the only domain-specific ingestion class.

## Impact

- **Public API**: `OptionChainVols` and `UnitisedSpaceVols` are removed from `qsmile.__init__`. All downstream code that constructs or type-checks against these classes must migrate to `SmileData`.
- **`fit_svi()`**: Signature narrows to `SmileData` only. Callers previously passing `OptionChainVols` must call `.to_smile_data()` first or use `SmileData.from_mid_vols()`.
- **Tests**: `test_vols.py`, `test_unitised.py`, and `test_to_smile_data.py` will be heavily rewritten or removed. `test_fitting.py` updated for SmileData-only input.
- **Notebooks**: `chain_demo.py` and `example.py` updated — `OptionChainVols` / `UnitisedSpaceVols` references replaced with `SmileData` construction and transforms.
- **Files removed**: `src/qsmile/vols.py`, `src/qsmile/unitised.py`.
- **Dependencies**: No new external dependencies. `cvxpy` remains (used by `OptionChainPrices`).
