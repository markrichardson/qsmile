## Context

`OptionChain` and `SmileData` currently store parallel `NDArray` fields that must be manually kept in sync. There is no shared abstraction for strike-indexed columnar data. The goal is to introduce a new `StrikeArray` class as the single storage primitive for both containers, backed by a hierarchical `pd.DataFrame`, and eliminate the parallel-array fields entirely — no backward compatibility shims.

## Goals / Non-Goals

**Goals:**
- Replace all parallel `NDArray` fields in `OptionChain` with a single `strikedata: StrikeArray` field.
- Replace `x`, `y_bid`, `y_ask`, `volume`, `open_interest` in `SmileData` with a single `strikearray: StrikeArray` field plus the existing coordinate/metadata fields.
- Back `StrikeArray` with a `pd.DataFrame` whose columns use a two-level `MultiIndex`: level-0 = option type (`call`, `put`), level-1 = quote field (`bid`, `ask`, `volume`, `open_interest`).
- Preserve all existing validation rules (positive strikes, bid ≤ ask, non-negative prices, min 3 points, etc.).
- Update all consumers: `to_smile_data()`, `transform()`, `from_mid_vols()`, `plot()`, fitting code, and tests.

**Non-Goals:**
- Adding new analytical capabilities beyond the storage refactor.
- Changing the coordinate transform algebra or fitting logic.
- Supporting non-strike-based x-axes in `SmileData` (it keeps `x_coord`/`y_coord` for coordinate semantics).
- Supporting arbitrary user-defined column hierarchies beyond the fixed two-level schema.

## Decisions

### 1. Hierarchical MultiIndex on columns

**Decision**: Use `pd.MultiIndex.from_tuples` with `(option_type, field)` pairs as column keys.

**Rationale**: A MultiIndex gives natural `.loc[:, ("call", "bid")]` slicing, enables `xs("call", level=0)` for all call data, and maps directly to the domain semantics. The alternative — flat string keys like `"call_bid"` (current approach) — loses the grouping structure and requires string parsing to extract type/field.

**Trade-off**: MultiIndex adds complexity to `StrikeArray` internals, but all access goes through the named setters/getters so the complexity is encapsulated.

### 2. `StrikeArray` becomes the single internal store

**Decision**: `OptionChain` holds `strikedata: StrikeArray` and `metadata: SmileMetadata`. `SmileData` holds `strikearray: StrikeArray`, `x_coord: XCoord`, `y_coord: YCoord`, and `metadata: SmileMetadata`.

**Rationale**: A single container eliminates the length-sync invariant at the field level — it is handled once inside `StrikeArray`. Builder-style construction via named setters is clearer than positional array arguments.

**Alternative considered**: Keep `SmileData` array-based and only change `OptionChain`. Rejected because the same length-sync problem exists in `SmileData` and the user explicitly wants both simplified.

### 3. No backward-compatible NDArray accessors

**Decision**: Remove the old `strikes`, `call_bid`, etc. dataclass fields entirely. Consumers access data through `StrikeArray` methods (`values("call_bid")`, `strikes` property) or through convenience properties that delegate to the `StrikeArray`.

**Rationale**: Maintaining shims adds surface area and confusion. This is a clean break; all tests and consumers will be updated in the same change.

### 4. SmileData column mapping

**Decision**: `SmileData` maps its current fields to `StrikeArray` columns as follows:
- `x` → `StrikeArray.strikes` (the index)
- `y_bid` → column `("y", "bid")`
- `y_ask` → column `("y", "ask")`
- `volume` → column `("y", "volume")` (optional)
- `open_interest` → column `("y", "open_interest")` (optional)

**Rationale**: `SmileData` is not option-type-aware (it works in abstract coordinates), so level-0 is `"y"` rather than `"call"`/`"put"`. This keeps the MultiIndex convention consistent while reflecting that `SmileData` holds blended/transformed data.

### 5. Validation stays in `__post_init__`

**Decision**: `OptionChain.__post_init__` and `SmileData.__post_init__` continue to validate after construction, reading from the `StrikeArray`. `StrikeArray` itself validates per-column (positive strikes, no duplicates) but does not enforce cross-column invariants like bid ≤ ask — those remain in the dataclass.

**Rationale**: Cross-column validation is domain-specific (option chains care about bid ≤ ask; other uses of `StrikeArray` might not). Keeping it in the dataclass avoids coupling `StrikeArray` to option pricing semantics.

## Risks / Trade-offs

- **Breaking change breadth** → Every test and consumer that constructs `OptionChain` or `SmileData` must be rewritten. Mitigation: do it in one atomic change with comprehensive test updates.
- **Performance** — `pd.DataFrame` with MultiIndex is heavier than raw NDArrays for small arrays. Mitigation: the data sizes are small (tens to hundreds of strikes); the ergonomic benefit outweighs the overhead.
- **MultiIndex learning curve** — Contributors unfamiliar with `pd.MultiIndex` may find column access less obvious. Mitigation: all access is through named methods on `StrikeArray`; direct DataFrame manipulation is internal only.
