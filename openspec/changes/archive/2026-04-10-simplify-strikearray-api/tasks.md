## 1. StrikeArray API Simplification

- [x] 1.1 Remove `_COLUMN_MAP`, `_resolve_key`, and all named setters from `StrikeArray`; change `set()` signature to accept `tuple[str, str]` key
- [x] 1.2 Update `values()`, `get_values()`, `has()` to accept `tuple[str, str]` key; update `columns` to return `list[tuple[str, str]]`
- [x] 1.3 Remove `ClassVar` import (no longer needed after `_COLUMN_MAP` removal)

## 2. OptionChain Consumer Updates

- [x] 2.1 Update `OptionChain.__post_init__` validation: replace flat-name `get_values`/`values` calls with tuple keys `("call", "bid")`, `("call", "ask")`, `("put", "bid")`, `("put", "ask")`, `("meta", "volume")`, `("meta", "open_interest")`
- [x] 2.2 Update `OptionChain` convenience properties (`call_bid`, `call_ask`, `put_bid`, `put_ask`, `volume`, `open_interest`) to use tuple keys
- [x] 2.3 Update `OptionChain.to_smile_data()` to build `StrikeArray` with tuple keys `("y", "bid")`, `("y", "ask")`, `("y", "volume")`, `("y", "open_interest")`

## 3. SmileData Consumer Updates

- [x] 3.1 Update `SmileData.__post_init__` validation: replace flat-name access with tuple keys `("y", "bid")`, `("y", "ask")`, `("y", "volume")`, `("y", "open_interest")`
- [x] 3.2 Update `SmileData` convenience properties (`y_bid`, `y_ask`, `volume`, `open_interest`) to use tuple keys
- [x] 3.3 Update `SmileData.transform()` to build new `StrikeArray` with tuple keys
- [x] 3.4 Update `SmileData.from_mid_vols()` to build `StrikeArray` with tuple keys

## 4. Test Updates

- [x] 4.1 Update `tests/data/test_strikes.py`: all `StrikeArray` construction and assertions to use tuple keys
- [x] 4.2 Update `tests/data/test_prices.py`: `_make_sd` helper and any direct `StrikeArray` access to use tuple keys
- [x] 4.3 Update `tests/data/test_vols.py`: `_make_sa` helper and any direct `StrikeArray` access to use tuple keys
- [x] 4.4 Update `tests/core/test_plot.py`: `_make_sa` helper to use tuple keys

## 5. Verify

- [x] 5.1 Run `make test` — all tests pass
- [x] 5.2 Run `make fmt` — no lint errors
