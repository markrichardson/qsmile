## Context

The qsmile library currently represents option smile data through three separate dataclasses:

- `OptionChainPrices` — strikes + call/put bid/ask prices  
- `OptionChainVols` — strikes + bid/ask implied volatilities  
- `UnitisedSpaceVols` — standardised log-moneyness + bid/ask total variance  

Each class has bespoke `to_X()` methods for pairwise conversion. This hard-codes a specific chain of coordinate systems and makes it expensive to add new ones (moneyness, variance-without-totalising, etc.). The transforms themselves are simple — most are element-wise arithmetic parameterised by forward, discount factor, expiry, and ATM vol — but are scattered across the three modules with no shared abstraction.

## Goals / Non-Goals

**Goals:**
- A single, composable coordinate-transform framework that supports the full matrix of X × Y coordinate pairs.
- X-coordinates: `FixedStrike`, `MoneynessStrike` ($K/F$), `LogMoneynessStrike` ($\ln K/F$), `StandardisedStrike` ($\ln(K/F) / (\sigma_{\text{ATM}} \sqrt{T})$).
- Y-coordinates: `Price`, `Volatility`, `Variance` ($\sigma^2$), `TotalVariance` ($\sigma^2 T$).
- A `SmileMetadata` value object carrying the parameters the maps depend on.
- A unified `SmileData` container that holds arrays + coordinate labels + metadata to enable `data.transform(target_x, target_y)`.
- Backward-compatible convenience methods on the existing classes during transition.

**Non-Goals:**
- Multi-expiry / term-structure containers — out of scope (single-expiry only).
- Stochastic or model-dependent coordinate transforms (e.g. local-vol grids).
- GUI / interactive plotting changes — existing `plot()` methods remain unchanged.
- Removing `OptionChainPrices` / `OptionChainVols` / `UnitisedSpaceVols` in this change — they stay as user-facing entry points.

## Decisions

### 1. Coordinate labels as enums

**Decision**: Use `enum.Enum` subclasses `XCoord` and `YCoord` for the coordinate taxonomy.

**Rationale**: Enums give exhaustive pattern matching, IDE auto-complete, and clear error messages. Strings are error-prone; sentinel objects add no value over enums.

**Alternatives considered**: String literals with validation — rejected because they offer no static-analysis benefit and require manual error messages everywhere.

### 2. SmileMetadata as a frozen dataclass

**Decision**: `SmileMetadata(forward, discount_factor, expiry, sigma_atm)` as a `@dataclass(frozen=True)`.

**Rationale**: These four values parameterise every transform. Freezing prevents accidental mutation. `sigma_atm` is optional (only needed for standardised-strike transforms) and defaults to `None`; the map will raise if it's needed but absent.

### 3. Chain-of-maps architecture for transforms

**Decision**: Define ordered "ladders" for X and Y coordinates:

```
X-ladder: FixedStrike ↔ MoneynessStrike ↔ LogMoneynessStrike ↔ StandardisedStrike
Y-ladder: Price ↔ Volatility ↔ Variance ↔ TotalVariance
```

Each adjacent pair has a forward map and inverse. To go from any X to any other X, walk the ladder (composing adjacent maps). Same for Y. `SmileData.transform(target_x, target_y)` composes the required X-chain and Y-chain independently.

**Rationale**: This avoids implementing $O(n^2)$ direct maps. Each new coordinate type requires only one new adjacent map pair. The ladder is well-ordered (each step is a monotone, invertible arithmetic operation).

**Alternatives considered**:
- Direct pairwise maps — $O(n^2)$ implementations, fragile to extend.
- Graph-based routing with arbitrary edges — over-engineered for a linear coordinate progression.

### 4. Map functions as plain functions (not classes)

**Decision**: Each step is a pair of functions: `forward_fn(x, meta) -> x'` and `inverse_fn(x', meta) -> x`. Registered in a module-level dictionary keyed by `(source, target)` coordinate pairs.

**Rationale**: The transforms are stateless one-liners (divide by forward, take log, etc.). Class wrappers add no value. A registry dictionary makes composition trivial: look up the path, compose the functions.

**Alternatives considered**: Strategy-pattern classes — rejected as over-engineering for pure arithmetic operations.

### 5. SmileData as a thin container

**Decision**: `SmileData` holds:
- `x: NDArray[np.float64]` — X-coordinate values
- `y_bid, y_ask: NDArray[np.float64]` — Y-coordinate bid/ask
- `x_coord: XCoord` — which X-coordinate system
- `y_coord: YCoord` — which Y-coordinate system
- `metadata: SmileMetadata`

It provides `y_mid` as a property and `transform(target_x, target_y) -> SmileData`.

**Rationale**: Keeps the data + its coordinate semantics together. The transform method returns a new `SmileData` (immutable style), so the user can hold multiple views simultaneously.

### 6. Price ↔ Volatility transform requires Black76

**Decision**: The `Price ↔ Volatility` Y-map is the only non-trivial transform — it calls Black76 pricing (forward) and Black76 implied-vol inversion (inverse). It also requires the X-data to be in `FixedStrike` coordinates (needs absolute strikes). If the current X-coord is not `FixedStrike`, the transform will first walk the X-ladder back to `FixedStrike`, perform the Y-step, then walk X forward to the target.

**Rationale**: Black76 takes `(F, K, D, σ, T)` — absolute strike is essential. Delegating to the existing `black76_call`/`black76_put`/`black76_implied_vol` functions avoids duplication.

### 7. Backward compatibility via delegation

**Decision**: Existing `to_vols()`, `to_prices()`, `to_unitised()` methods on the current classes will be reimplemented as thin wrappers that:
1. Construct `SmileData` from the class's fields.
2. Call `transform(...)` with the appropriate target coordinates.
3. Unpack the result back into the legacy class.

**Rationale**: Zero user-facing breakage. Existing tests continue to pass unchanged.

### 8. Module layout

**Decision**: New modules under `src/qsmile/`:
- `coords.py` — `XCoord`, `YCoord` enums
- `metadata.py` — `SmileMetadata` dataclass
- `maps.py` — map registry + individual map functions
- `smile_data.py` — `SmileData` container + `transform()`

**Rationale**: Small, focused modules. No circular imports (dependency flows: `coords` ← `metadata` ← `maps` ← `smile_data`).

## Risks / Trade-offs

- **Numerical round-trip drift**: Chaining multiple ladder steps (e.g. `FixedStrike → StandardisedStrike` = 3 hops) accumulates floating-point error. → *Mitigation*: Each step is a simple arithmetic op (multiply, divide, log, exp); error is negligible for 64-bit floats. Property tests will verify round-trip fidelity.

- **Price ↔ Vol step is expensive**: Black76 implied-vol inversion is iterative. → *Mitigation*: Already paid in the current `to_vols()` path; no regression. Cache-friendly vectorised implementation already exists.

- **API surface growth**: New enums, metadata, SmileData add public symbols. → *Mitigation*: They are additive and the existing classes remain the primary entry points. SmileData is an opt-in power-user API.

- **sigma_atm dependency for StandardisedStrike**: If sigma_atm is None in metadata and user requests StandardisedStrike, get a runtime error. → *Mitigation*: Clear error message. `OptionChainVols.to_smile_data()` will auto-populate sigma_atm.
