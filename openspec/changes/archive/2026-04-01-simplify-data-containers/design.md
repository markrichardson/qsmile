## Context

The qsmile library currently has three domain-specific data containers (`OptionChainPrices`, `OptionChainVols`, `UnitisedSpaceVols`) plus the coordinate-agnostic `SmileData`. After the coordinate-transforms work, all three domain classes do little beyond validating inputs, providing a `to_smile_data()` gateway, and offering a `plot()` method. `SmileData.transform()` handles all conversions.

`OptionChainPrices` is structurally unique (4 Y-arrays for calls/puts) and performs non-trivial calibration. The other two are thin wrappers around what `SmileData` already represents: `OptionChainVols` ≡ `SmileData(FixedStrike, Volatility)` and `UnitisedSpaceVols` ≡ `SmileData(StandardisedStrike, TotalVariance)`.

## Goals / Non-Goals

**Goals:**
- Remove `OptionChainVols` and `UnitisedSpaceVols` without loss of functionality.
- Preserve ergonomics via factory methods on `SmileData` (e.g. `from_mid_vols`).
- Add coordinate-aware validation to `SmileData` to retain the domain checks the removed classes provided.
- Keep `OptionChainPrices` as the sole domain-specific ingestion class.

**Non-Goals:**
- Removing `OptionChainPrices` (different data shape; irreplaceable).
- Adding new coordinate systems or transform logic.
- Changing the internal representation of `SmileData` or `SmileMetadata`.

## Decisions

### 1. Remove both `OptionChainVols` and `UnitisedSpaceVols`

**Rationale:** Both classes are now structurally equivalent to a `SmileData` with specific coordinate tags. Keeping them means users must learn two types that do the same thing. Removing them makes `SmileData` the single post-ingestion type.

**Alternative considered:** Keep `OptionChainVols` for its `from_mid_vols()` factory and `sigma_atm` property. Rejected because these can live on `SmileData` with less conceptual overhead.

### 2. Add `SmileData.from_mid_vols()` classmethod

```python
@classmethod
def from_mid_vols(cls, strikes, ivs, forward, expiry, discount_factor=1.0) -> SmileData:
    ...
```

Replaces `OptionChainVols.from_mid_vols()`. Constructs a `SmileData(FixedStrike, Volatility)` with `sigma_atm` auto-derived in metadata. Sets `y_bid = y_ask = ivs` (zero spread).

### 3. Add `SmileData.plot()` method

Generic bid/ask plot using the existing `plot_bid_ask` helper. Axis labels derived from `x_coord` / `y_coord` names. Replaces `OptionChainVols.plot()` and `UnitisedSpaceVols.plot()`.

### 4. Coordinate-aware validation in `SmileData.__post_init__`

Add optional domain checks based on coordinate types:
- `FixedStrike`: x values must be positive
- `MoneynessStrike`: x values must be positive
- `Volatility`: y values must be non-negative
- `Variance` / `TotalVariance`: y values must be non-negative
- `y_bid <= y_ask` for all coordinate types
- Minimum 3 data points (matching the ≥3-strikes rule from the removed classes)

SmileData currently only validates array lengths. These additions are safe because they are universal invariants for the coordinate types, not domain-specific.

### 5. `fit_svi()` accepts `SmileData` only

Drop the `OptionChainVols` branch. The function already handles `SmileData` by transforming to `(LogMoneynessStrike, TotalVariance)` internally. Callers previously passing `OptionChainVols` use `SmileData.from_mid_vols()` or `chain.to_smile_data()` instead.

### 6. File removal strategy

- Delete `src/qsmile/vols.py` and `src/qsmile/unitised.py`.
- Remove exports from `src/qsmile/__init__.py`.
- Rewrite/remove tests that depend on the deleted classes.
- Update notebooks and README.

## Risks / Trade-offs

- **[Breaking change]** → Documented in proposal. No external consumers yet (pre-release library). Migration path is straightforward: `OptionChainVols(...)` → `SmileData(x_coord=FixedStrike, y_coord=Volatility, ...)` or `SmileData.from_mid_vols(...)`.
- **[Verbose construction]** → `SmileData` constructor is more verbose than `OptionChainVols`. Mitigated by `from_mid_vols()` factory for the common case.
- **[Lost domain naming]** → Users no longer see "OptionChainVols" as a type name, which was self-documenting. Mitigated by coordinate enum names (`FixedStrike`, `Volatility`) being equally descriptive, and `SmileData` being the one type to learn.
- **[Validation gaps]** → SmileData's validation is currently minimal. Adding coordinate-aware checks closes this gap. Risk: over-constraining SmileData for edge-case transforms. Mitigation: only validate universal invariants (positive strikes, non-negative vols).
