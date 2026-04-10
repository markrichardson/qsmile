## Why

The current architecture separates "data" (`SmileData`) from "models" (`SVIModel`, `SABRModel`) at a fundamental level. `SmileData` carries coordinate-awareness (`x_coord`, `y_coord`) and rich methods (`transform`, `plot`), while fitted model instances are bare parameter containers that only know their native coordinates. After calibration, users get a `SmileResult` wrapping a model, but the model itself cannot plot, transform to arbitrary coordinates, or be constructed directly from parameters in a convenient way. This creates friction: to plot a fitted smile or evaluate it in non-native coordinates, users must manually orchestrate transforms. The model objects should be first-class smile representations — constructible either by calibration or by directly setting parameters — with the same coordinate-transform and plotting capabilities as `SmileData`. No backward compatibility is required, enabling a clean simplification.

## What Changes

- **BREAKING**: Merge coordinate-awareness into `AbstractSmileModel` — models gain `current_x_coord` / `current_y_coord` alongside their existing `native_x_coord` / `native_y_coord`, enabling expression in arbitrary coordinate spaces
- **BREAKING**: Add `__call__` to `AbstractSmileModel` as the primary evaluation interface, replacing the standalone `evaluate` method name
- **BREAKING**: Add a `plot` method to `AbstractSmileModel` so fitted models can self-plot
- **BREAKING**: Add a `transform` method to `AbstractSmileModel` for re-expressing a model's output in different coordinate systems
- **BREAKING**: Add a `params` property to `AbstractSmileModel` that returns the fitted parameters as a dict
- **BREAKING**: Simplify the `SmileModel` protocol to match the new `AbstractSmileModel` interface
- **BREAKING**: Update `fit()` to return model instances that carry coordinate context, potentially simplifying or removing `SmileResult`
- **BREAKING**: Update `SVIModel` and `SABRModel` to conform to the enriched base class
- Simplify or remove redundant abstractions where the refactoring creates opportunities

## Capabilities

### New Capabilities
- `model-coordinate-transform`: Models can express their output in arbitrary X/Y coordinate systems via `current_x_coord`/`current_y_coord` and a `transform` method
- `model-plotting`: Models can plot themselves with a `plot()` method, analogous to `SmileData.plot()`
- `model-callable`: Models support `__call__` as the primary evaluation interface

### Modified Capabilities
- `abstract-smile-model`: Enriched with coordinate-awareness, `__call__`, `plot`, `transform`, and `params`
- `smile-model-protocol`: Updated to reflect the new model interface
- `svi-model`: Updated to conform to enriched base class
- `sabr-model`: Updated to conform to enriched base class
- `smile-fitting`: Updated `fit()` return type and coordinate context handling

## Impact

- **Code**: All files under `src/qsmile/models/` (protocol, fitting, svi, sabr) and their tests
- **APIs**: `SmileModel` protocol, `AbstractSmileModel`, `SVIModel`, `SABRModel`, `fit()`, `SmileResult` — all public API surfaces change
- **Dependencies**: No new external dependencies; internal dependency on `qsmile.core.maps` and `qsmile.core.plot` from model layer
- **Tests**: All model and fitting tests require rewriting
