## Context

`OptionChain` is the market-data entry point. It holds per-strike bid/ask prices and converts to `SmileData` for fitting. Exchange data typically includes volume and open interest alongside prices, but these fields are currently discarded at ingestion. Downstream consumers — the fitting engine, denoising, and plotting — have no access to liquidity context.

`SmileData` is the unified data container that flows through coordinate transforms and into the fitting stack. It currently holds `x`, `y_bid`, `y_ask`, coordinate labels, and `SmileMetadata`. There are no provisions for auxiliary per-strike arrays.

`SmileMetadata` is a frozen scalar-parameter container (forward, DF, expiry, sigma_atm). Per-strike data does not belong here.

## Goals / Non-Goals

**Goals:**

- Carry optional per-strike `volume` and `open_interest` arrays from `OptionChain` through to `SmileData`
- Preserve these arrays through `denoise()` filtering (subset to surviving strikes)
- Preserve these arrays through `SmileData.transform()` (they are strike-indexed metadata, not coordinate-dependent values)
- Remain fully backward-compatible — both fields default to `None`

**Non-Goals:**

- Liquidity-weighted fitting objectives (future work — this change only provides the data)
- Aggregating volume/OI across multiple expiries or chains
- Adding volume/OI to `SmileMetadata` (these are per-strike arrays, not scalar parameters)
- Modifying `OptionChainVols` or `UnitisedSpaceVols` (out of scope for this change)

## Decisions

### D1: Optional `NDArray | None` fields defaulting to `None`

Both `volume` and `open_interest` are optional `NDArray[np.float64] | None` fields with default `None`. This preserves backward compatibility — no existing constructor call needs to change.

**Alternative considered**: Separate `MarketContext` dataclass. Rejected — adds indirection for two simple arrays and complicates the dataclass interface.

### D2: Validation only when provided

When non-`None`, the arrays must have the same length as `strikes` (or `x`) and contain non-negative values. No validation occurs when `None`.

### D3: Passthrough on `SmileData.transform()`

Volume and open interest are strike-indexed quantities unrelated to the coordinate system. During `transform()`, they are copied through unchanged (the arrays have the same length as `x` before and after since transforms do not filter strikes).

### D4: Subset on `denoise()` and `to_smile_data_blended()`

When strikes are filtered (in `denoise()` or `to_smile_data_blended()`), the volume/OI arrays are subset with the same boolean mask, keeping alignment.

## Risks / Trade-offs

- **[Memory overhead]** → Negligible: two optional float64 arrays per chain, only allocated when provided.
- **[Frozen SmileMetadata unchanged]** → By placing arrays on `SmileData` rather than `SmileMetadata`, we avoid breaking the frozen contract. Trade-off: `SmileData` gains two more fields, but this is the natural home for per-point data.
- **[Transform copy cost]** → Transforms already copy all arrays; adding two more optional copies is negligible.
