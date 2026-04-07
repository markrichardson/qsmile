## Why

`OptionChain` currently stores `expiry`, `forward`, and `discount_factor` as separate scalar fields, duplicating the same data that `SmileMetadata` already encapsulates. This forces `to_smile_data()` to reconstruct a `SmileMetadata` internally, and means callers access metadata through three disjoint attributes instead of one coherent object. Replacing the three fields with a single `metadata: SmileMetadata` field removes the duplication and makes the price→vol pipeline consistent — `SmileMetadata` flows through the entire stack as a first-class value.

## What Changes

- **BREAKING**: Remove `expiry: float`, `forward: float | None`, and `discount_factor: float | None` constructor parameters from `OptionChain`.
- Add a `metadata: SmileMetadata` constructor parameter. The caller constructs `SmileMetadata(expiry=..., forward=..., discount_factor=...)` and passes it in. `forward` and `discount_factor` remain optional on `SmileMetadata` (a new relaxation — see Modified Capabilities), but `expiry` is always required.
- `OptionChain.__post_init__` calibrates `forward` and/or `discount_factor` when they are `None` on the incoming metadata, then stores the completed `SmileMetadata` (possibly with calibrated values) as `self.metadata`.
- `to_smile_data()` uses `self.metadata` directly instead of reconstructing it.
- `filter()` passes `self.metadata.expiry` (and lets the returned chain re-calibrate forward/DF).

## Capabilities

### New Capabilities

_(none)_

### Modified Capabilities

- `option-chain`: Constructor signature changes — `expiry`/`forward`/`discount_factor` replaced by `metadata: SmileMetadata`.
- `option-chain-prices`: `to_smile_data()` sources metadata from `self.metadata` instead of individual fields.
- `smile-metadata`: `forward` and `discount_factor` become optional (`float | None`, default `None`) so that `SmileMetadata` can be constructed before calibration.

## Impact

- **API** (breaking): All call-sites that construct `OptionChain` must pass `metadata=SmileMetadata(...)` instead of `expiry=`, `forward=`, `discount_factor=`.
- **Code**: `src/qsmile/data/prices.py` (OptionChain), `src/qsmile/data/meta.py` (SmileMetadata).
- **Tests**: `tests/data/test_prices.py` — all fixtures that build an `OptionChain`.
- **Docs / notebooks**: `README.md`, `book/marimo/notebooks/qsmile_demo.py`, `book/marimo/notebooks/chain_demo.py`.
- **Specs**: `openspec/specs/option-chain/spec.md`, `openspec/specs/option-chain-prices/spec.md`, `openspec/specs/smile-metadata/spec.md`.
