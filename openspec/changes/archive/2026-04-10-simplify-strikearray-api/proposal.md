## Why

`StrikeArray` maintains a redundant dual-access layer: an internal `pd.DataFrame` with hierarchical `MultiIndex` columns like `("call", "bid")`, plus a `_COLUMN_MAP` dictionary and six named setters (`set_call_bid`, `set_call_ask`, etc.) that translate flat strings back to tuples. This mapping adds complexity, hides the natural MultiIndex API from callers, and forces every new column name to be registered in the map. Consumers should work directly with the tuple column keys that the DataFrame already uses.

## What Changes

- **BREAKING** — Remove `_COLUMN_MAP`, all named setters (`set_call_bid`, `set_call_ask`, `set_put_bid`, `set_put_ask`, `set_volume`, `set_open_interest`), and the `_resolve_key` helper from `StrikeArray`.
- **BREAKING** — The `set(name, series)` method changes signature to `set(key: tuple[str, str], series)`, accepting `("call", "bid")` style tuple keys directly.
- **BREAKING** — `values(name)` and `get_values(name)` change to accept `tuple[str, str]` keys instead of flat strings.
- **BREAKING** — `has(name)` changes to accept `tuple[str, str]` keys.
- **BREAKING** — The `columns` property returns `list[tuple[str, str]]` instead of `list[str]`.
- All consumers (`OptionChain`, `SmileData`, test helpers) update to use tuple column keys: `sa.set(("call", "bid"), series)`, `sa.values(("call", "bid"))`, etc.

## Capabilities

### New Capabilities

_(none)_

### Modified Capabilities

- `hierarchical-strike-store`: Remove flat-name mapping layer; `set`, `values`, `get_values`, `has`, and `columns` all use `tuple[str, str]` keys directly.
- `option-chain`: Update all `StrikeArray` access to use tuple keys (`("call", "bid")` instead of `"call_bid"`).
- `smile-data`: Update all `StrikeArray` access to use tuple keys (`("y", "bid")` instead of `"y_bid"`).

## Impact

- **Code** — `src/qsmile/data/strikes.py` (major: remove mapping layer, simplify class), `src/qsmile/data/prices.py` (moderate: update all `StrikeArray` access in `OptionChain`), `src/qsmile/data/vols.py` (moderate: update all `StrikeArray` access in `SmileData`).
- **Tests** — `tests/data/test_strikes.py` (major: rewrite all tests), `tests/data/test_prices.py` (moderate: update helpers), `tests/data/test_vols.py` (moderate: update helpers), `tests/core/test_plot.py` (minor: update helpers).
- **APIs** — All `StrikeArray` method signatures change from `str` to `tuple[str, str]`. `OptionChain` and `SmileData` convenience properties are unaffected (they encapsulate the access pattern).
- **Dependencies** — None; no new packages required.
