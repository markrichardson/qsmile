## Why

`OptionChain` and `SmileData` store six separate `NDArray` fields (`strikes`, `call_bid`, `call_ask`, `put_bid`, `put_ask`) plus optional `volume` and `open_interest`, all of which must share the same length and strike axis. This parallel-array design makes construction error-prone (mismatched lengths, wrong ordering) and adds boilerplate to every consumer. There is no shared abstraction for strike-indexed columnar data, and the data lacks a hierarchical organisation that separates option type (`call`/`put`) from quote side (`bid`/`ask`/`volume`/`open_interest`).

## What Changes

- **BREAKING** — `OptionChain` replaces its six `NDArray` fields with a single `StrikeArray`-backed store (`strikedata: StrikeArray`). Construction shifts from positional arrays to builder-style `set_call_bid(series)` / `set_call_ask(series)` / … calls. No backward-compatible NDArray accessors are provided.
- **BREAKING** — `SmileData` replaces its `x`, `y_bid`, `y_ask`, `volume`, and `open_interest` fields with a single `strikearray: StrikeArray` field alongside `metadata: SmileMetadata`. All consumers must update to use the `StrikeArray` API.
- `StrikeArray` gains an internal `pd.DataFrame` with a hierarchical `MultiIndex` on columns: level-0 = option type (`call`, `put`), level-1 = quote field (`bid`, `ask`, `volume`, `open_interest`).
- `OptionChain.__post_init__` validation logic is preserved but reads from the `StrikeArray` rather than raw fields.
- `to_smile_data()` and calibration paths are updated to pull arrays from the `StrikeArray`.
- `SmileData.transform()`, `from_mid_vols()`, and `plot()` are updated to work with the `StrikeArray` store.

## Capabilities

### New Capabilities
- `hierarchical-strike-store`: Internal `StrikeArray` storage with a `pd.DataFrame` backed by a `(option_type, field)` hierarchical `MultiIndex`, adaptive union reindexing, and builder-style column setters.

### Modified Capabilities
- `option-chain`: Construction changes from parallel NDArrays to `StrikeArray`-backed builder; old NDArray fields removed.
- `smile-data`: Replaces `x`/`y_bid`/`y_ask`/`volume`/`open_interest` fields with `strikearray: StrikeArray`.

## Impact

- **Code** — `src/qsmile/data/strikes.py` (major: hierarchical DataFrame internals), `src/qsmile/data/prices.py` (major: `OptionChain` fields & `__post_init__`), `src/qsmile/data/vols.py` (major: `SmileData` fields & methods), all test files under `tests/data/` and `tests/models/` that construct `OptionChain` or `SmileData`.
- **APIs** — `OptionChain` and `SmileData` construction signatures change (**breaking**). All downstream code (fitting, coordinate transforms, plotting) must adopt the `StrikeArray` API.
- **Dependencies** — `pandas` is already a project dependency; no new packages required.
