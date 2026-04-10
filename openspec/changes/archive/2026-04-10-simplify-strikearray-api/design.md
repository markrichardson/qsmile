## Context

`StrikeArray` is a mutable columnar store indexed by strike price, backed by a `pd.DataFrame` with a two-level `MultiIndex` on columns. It was introduced to replace parallel NDArray fields in `OptionChain` and `SmileData`.

Currently, `StrikeArray` maintains a `_COLUMN_MAP` dictionary that maps flat string names (e.g. `"call_bid"`) to hierarchical tuple keys (e.g. `("call", "bid")`). It also provides six named setter methods (`set_call_bid`, etc.) that delegate to the generic `set()` method. This mapping layer exists because the previous change was designed to provide a convenience API over the MultiIndex. However, in practice the mapping adds indirection and hides the natural pandas tuple-key access that the DataFrame already supports.

All consumers (`OptionChain`, `SmileData`) already use `StrikeArray` through convenience properties that encapsulate column access, so the flat-name layer is not exposed to end users of those classes.

## Goals / Non-Goals

**Goals:**
- Remove `_COLUMN_MAP`, `_resolve_key`, and all six named setters from `StrikeArray`.
- Change `set()`, `values()`, `get_values()`, `has()`, and `columns` to accept/return `tuple[str, str]` keys directly.
- Update all call sites in `OptionChain`, `SmileData`, test helpers, and test assertions to use tuple keys.
- Maintain all existing behaviour; only the access syntax changes.

**Non-Goals:**
- Changing `OptionChain` or `SmileData` public APIs (their convenience properties remain unchanged).
- Altering the internal DataFrame structure or MultiIndex design.
- Adding new functionality to `StrikeArray`.

## Decisions

### 1. Tuple keys throughout

**Decision**: All `StrikeArray` methods that currently accept a flat `str` name will accept `tuple[str, str]` instead.

**Rationale**: The DataFrame already uses `(category, field)` tuples. Passing tuples directly eliminates the mapping layer and makes the column structure explicit at every call site. This is the natural pandas idiom for MultiIndex columns.

**Alternative considered**: Keep `set()` accepting strings and parse them (e.g. split on `"_"`). Rejected because it is ambiguous (e.g. `"open_interest"` would split incorrectly) and still requires a mapping table.

### 2. Remove named setters entirely

**Decision**: Remove `set_call_bid`, `set_call_ask`, `set_put_bid`, `set_put_ask`, `set_volume`, `set_open_interest`. Callers use `sa.set(("call", "bid"), series)` instead.

**Rationale**: Named setters are thin wrappers that add six methods purely for syntactic convenience. With tuple keys, the call site is already concise and self-documenting. Removing them reduces the class surface area from ~12 public methods to ~6.

### 3. `columns` returns `list[tuple[str, str]]`

**Decision**: The `columns` property returns the raw MultiIndex tuples rather than reverse-mapped flat strings.

**Rationale**: Returning tuples is consistent with the rest of the API and avoids needing a reverse mapping. Code that checks column membership can use `("call", "bid") in sa.columns`.

### 4. Convenience properties on OptionChain and SmileData are unchanged

**Decision**: Properties like `OptionChain.call_bid`, `SmileData.y_bid` continue to exist and internally call `self.strikedata.values(("call", "bid"))` etc. The public API of these dataclasses does not change.

**Rationale**: End users should not need to know about StrikeArray internals. The convenience properties provide a clean, flat API.

## Risks / Trade-offs

- **Breaking change breadth** — Every call site that constructs a `StrikeArray` must update. Mitigation: all such sites are internal (production code + tests); no external consumers.
- **Verbosity** — `sa.set(("call", "bid"), series)` is slightly more verbose than `sa.set_call_bid(series)`. Acceptable because construction sites are few and the tuple makes the column structure explicit.
- **Discoverability** — Without named setters, users need to know the tuple key convention. Mitigation: `OptionChain` and `SmileData` hide this; direct `StrikeArray` use is internal.
