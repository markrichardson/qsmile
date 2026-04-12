## Context

The qsmile codebase currently separates "data containers" (`SmileData`) from "model parameter containers" (`SVIModel`, `SABRModel`). `SmileData` is coordinate-aware — it carries `x_coord`/`y_coord` and can `transform()` between arbitrary coordinate systems and `plot()` itself. By contrast, fitted model instances are bare parameter holders: they can `evaluate(x)` in their native coordinates only, and have no awareness of alternative coordinate representations, no plotting, and no convenient callable interface. The `SmileResult` wrapper returned by `fit()` provides some bridge functionality but adds indirection.

The user wants model objects to be first-class smile representations, constructible either by calibration or by directly setting parameters, with coordinate-transform and plotting capabilities analogous to `SmileData`. No backward compatibility is required.

**Current architecture**:
- `SmileModel` protocol: `native_x_coord`, `native_y_coord`, `param_names`, `bounds`, `evaluate()`, `to_array()`, `from_array()`, `initial_guess()`
- `AbstractSmileModel`: dataclass base with default `to_array()`/`from_array()`
- `SVIModel(AbstractSmileModel)`: 5 fitted params (`a, b, rho, m, sigma`), native in (LogMoneyness, TotalVariance)
- `SABRModel(AbstractSmileModel)`: 4 fitted + 2 context params (`alpha, beta, rho, nu` + `expiry, forward`), native in (LogMoneyness, Volatility)
- `fit()`: transforms data to native coords, runs `least_squares`, returns `SmileResult[M]`
- `SmileResult[M]`: holds `params: M`, `residuals`, `rmse`, `success`

**Coordinate transform infrastructure** (`qsmile.core.maps`): ladder-based composition already supports arbitrary X↔X and Y↔Y transforms. Models can reuse this machinery.

## Goals / Non-Goals

**Goals:**
- Model instances become coordinate-aware: carry `current_x_coord`/`current_y_coord` alongside native coords
- Models support `__call__(x)` for evaluation in current coordinates (transform under the hood if needed)
- Models support `transform(target_x, target_y)` returning a new model expressed in different coordinates
- Models support `plot()` for self-visualization
- Models expose a `params` property returning a dict of fitted parameter values
- `SmileModel` protocol reflects the enriched interface
- `fit()` returns models that are already coordinate-contextual
- Simplify or eliminate `SmileResult` if the enriched model subsumes its purpose
- Clean, simple API: model objects "just work" — construct, call, plot, transform

**Non-Goals:**
- Adding new model types (e.g., SSVI, Clark) — out of scope
- Changing `SmileData`, `StrikeArray`, or `SmileMetadata` — the data layer is untouched
- Altering the coordinate enum definitions (`XCoord`, `YCoord`)
- Changing the fitting algorithm (still `scipy.optimize.least_squares`)
- Performance optimization of transform chains

## Decisions

### 1. Enrich `AbstractSmileModel` rather than create a wrapper

**Decision**: Add `current_x_coord`, `current_y_coord`, `metadata`, `__call__`, `transform`, `plot`, and `params` directly to `AbstractSmileModel`.

**Alternatives considered**:
- *Wrapper class* (e.g., `SmileModelView` wrapping a model + coords): adds indirection, two objects to manage, and blurs ownership — rejected.
- *Mixin* for coordinate-awareness: unnecessary complexity when there's a single base class — rejected.

**Rationale**: A single enriched base class is the simplest approach. Models are already dataclasses inheriting from `AbstractSmileModel`, so adding fields and methods is natural.

### 2. `__call__` evaluates in current coordinates, `evaluate` stays as native-coordinate evaluation

**Decision**: `evaluate(x)` remains the abstract method subclasses implement — always operates in native coordinates. `__call__(x)` is a concrete method on the base class that: (1) transforms input x from `current_x_coord` to `native_x_coord`, (2) calls `evaluate`, (3) transforms output y from `native_y_coord` to `current_y_coord`.

**Alternatives considered**:
- *Replace `evaluate` with `__call__`*: forces subclasses to handle coordinate transforms themselves — rejected.
- *Have `evaluate` do the transform*: breaks the clean separation between "what the model computes" and "what coordinates it's expressed in" — rejected.

**Rationale**: This preserves backward compatibility of the `evaluate` contract (native coords only) while giving users a convenient `model(x)` call that works in whatever coordinates the model is currently expressed in.

### 3. `transform()` returns a new model instance with updated current coords

**Decision**: `transform(target_x, target_y)` returns a shallow copy of the model with `current_x_coord` and `current_y_coord` updated. The underlying parameters and `evaluate` method are unchanged — the transform is applied lazily at `__call__` time.

**Alternatives considered**:
- *Eagerly re-parameterise*: would require inverting the model and re-fitting in new coordinates — mathematically complex and lossy — rejected.
- *Store a transform chain on the model*: over-engineered for the use case — rejected.

**Rationale**: Lazy transformation is correct because the model's native parameters are coordinate-specific (e.g., SVI's `a` is total variance). The transform is purely a presentation concern applied at evaluation time.

### 4. Models carry `SmileMetadata` for coordinate transforms

**Decision**: `AbstractSmileModel` gains a `metadata: SmileMetadata` field. This provides the `forward`, `sigma_atm`, `texpiry`, etc. needed by coordinate transform maps. For `SABRModel`, the existing `expiry` and `forward` context fields become redundant — they are absorbed into `metadata`.

**Alternatives considered**:
- *Pass metadata at transform/call time*: inconvenient, error-prone, breaks the "model as self-contained object" goal — rejected.
- *Derive metadata from model params only*: not possible — `forward`, `discount_factor`, etc. are market data, not model params — rejected.

**Rationale**: `SmileData` already carries `SmileMetadata` for the same reason. Models need the same information.

### 5. Simplify `SmileResult` but keep it

**Decision**: Keep `SmileResult` as a lightweight fit-diagnostics container (`params`, `residuals`, `rmse`, `success`). But `params` is now a fully coordinate-aware model instance, so `SmileResult.evaluate()` becomes unnecessary (just use `result.params(x)`).

**Alternatives considered**:
- *Eliminate `SmileResult` entirely*: loses fit diagnostics (residuals, rmse, success) — rejected.
- *Return a tuple*: not as ergonomic — rejected.

**Rationale**: `SmileResult` still has value as a fit-report container. It just becomes thinner because the model itself is now more capable.

### 6. `SABRModel` context fields replaced by metadata

**Decision**: Remove `expiry` and `forward` as direct fields on `SABRModel`. They live in `metadata` (which all models now carry). `SABRModel.evaluate()` reads `self.metadata.texpiry` and `self.metadata.forward` internally.

**Rationale**: Eliminates duplication and aligns with the unified model architecture. `from_array()` and `fit()` will pass metadata rather than individual context kwargs.

### 7. Default `current_x_coord`/`current_y_coord` to native coordinates

**Decision**: When constructing a model (either manually or from `fit()`), `current_x_coord` and `current_y_coord` default to `native_x_coord` and `native_y_coord`. Users call `transform()` to change.

**Rationale**: Sensible default — most evaluation happens in native coordinates. Transform is opt-in.

### 8. `plot()` evaluates the model over a range and plots the curve

**Decision**: `model.plot()` generates a grid of x-values in current coordinates, evaluates `__call__`, and plots using `matplotlib`. Uses the existing `plot_bid_ask` infrastructure or a simpler line plot (models produce a single curve, not bid/ask).

**Rationale**: Models produce a single mid curve, not bid/ask spreads. A simple line plot is appropriate, distinct from `SmileData.plot()` which shows error bars.

## Risks / Trade-offs

- **[Lazy transform correctness]** → Transforms at `__call__` time rely on the coordinate map infrastructure being correct for all X/Y combinations. Mitigation: the map infrastructure is already well-tested via `SmileData.transform()`.
- **[Metadata coupling]** → Models now depend on having correct `SmileMetadata` for coordinate transforms. If metadata is wrong, transforms silently produce wrong results. Mitigation: validation in `__post_init__`; `fit()` always populates metadata from the input data.
- **[SABRModel breaking change]** → Removing `expiry`/`forward` fields from `SABRModel` is a significant API break. Mitigation: no backward compatibility required per user directive.
- **[Protocol expansion]** → Adding more methods to `SmileModel` protocol makes it harder to satisfy. Mitigation: `AbstractSmileModel` provides all defaults; only `evaluate` and `initial_guess` remain abstract.
