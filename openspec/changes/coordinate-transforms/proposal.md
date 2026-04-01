## Why

The current codebase has separate `OptionChainPrices`, `OptionChainVols`, and `UnitisedSpaceVols` classes with ad-hoc conversion methods (`to_vols()`, `to_prices()`, `to_unitised()`). This design does not scale: adding new X-coordinates (moneyness, standardised strike) or Y-coordinates (variance, total variance as first-class) requires proliferating more classes and more pairwise conversion methods. Users need a clean, composable way to work with option smile data across a matrix of coordinate systems — without an explosion of types.

## What Changes

- Introduce a `SmileMetadata` dataclass encapsulating the parameters that coordinate transforms depend on: forward, discount factor, expiry, and ATM vol.
- Define an enum-based coordinate system taxonomy:
  - **X-coordinates**: `FixedStrike`, `MoneynessStrike`, `LogMoneynessStrike`, `StandardisedStrike`
  - **Y-coordinates**: `Price`, `Volatility`, `Variance`, `TotalVariance`
- Create a unified `SmileData` container that holds X/Y arrays (bid, ask, mid) together with their coordinate labels and smile metadata, enabling introspection and transformation.
- Implement a coordinate transform framework with composable, invertible maps:
  - X-maps: strike ↔ moneyness ↔ log-moneyness ↔ standardised strike
  - Y-maps: price ↔ volatility ↔ variance ↔ total variance
  - Each map is parameterised by `SmileMetadata` where needed.
- Provide a top-level `transform(data, target_x, target_y)` function (or method on `SmileData`) that chains the necessary maps to move from any source coordinate pair to any target coordinate pair.
- **BREAKING**: `OptionChainPrices`, `OptionChainVols`, and `UnitisedSpaceVols` will be refactored. Their existing public APIs (`to_vols()`, `to_prices()`, `to_unitised()`) will be preserved as convenience wrappers around the new transform system during a transition period, but the classes themselves may be simplified or replaced.

## Capabilities

### New Capabilities
- `smile-metadata`: Dataclass encapsulating forward, discount factor, expiry, and ATM vol — the parameters needed by coordinate transforms.
- `coordinate-enums`: Enum types for X-coordinates (strike representations) and Y-coordinates (value representations) that label data unambiguously.
- `smile-data`: A unified container holding X/Y bid/ask/mid arrays, coordinate labels, and smile metadata, with a `transform()` method to re-express the data in different coordinates.
- `coordinate-maps`: Composable, invertible map functions for X and Y coordinate transforms, parameterised by smile metadata.

### Modified Capabilities
- `option-chain-prices`: Refactored to construct/expose `SmileData` with `(FixedStrike, Price)` coordinates; `to_vols()` becomes a convenience wrapper.
- `option-chain-vols`: Refactored to construct/expose `SmileData` with `(FixedStrike, Volatility)` coordinates; `to_prices()` and `to_unitised()` become convenience wrappers.
- `unitised-space-vols`: Refactored to construct/expose `SmileData` with `(StandardisedStrike, TotalVariance)` coordinates; `to_vols()` becomes a convenience wrapper.

## Impact

- **Code**: `src/qsmile/prices.py`, `src/qsmile/vols.py`, `src/qsmile/unitised.py` will gain imports from / delegation to the new transform module(s). New files for metadata, enums, maps, and the unified container.
- **Public API**: Existing conversion methods preserved as wrappers initially. New `SmileData.transform()` API added.
- **Dependencies**: No new external dependencies expected (transforms are pure NumPy + Black76 already in the project).
- **Tests**: New tests for coordinate maps (round-trip, identity, composition). Existing tests remain valid and serve as regression coverage.
