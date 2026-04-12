## Why

The model layer has two overlapping abstractions — `SmileModel` (a runtime-checkable Protocol) and `AbstractSmileModel` (an ABC dataclass). Every concrete model inherits from the ABC, making the Protocol redundant. Additionally, the public API has a confusing split between `evaluate()` (native coords only) and `__call__()` (coordinate-aware), and `SVIModel` carries an ad-hoc `implied_vol()` method that SABR lacks. With `transform().evaluate(x)` as the intended workflow, these layers and asymmetries should be collapsed.

## What Changes

- **BREAKING** — Remove `SmileModel` Protocol entirely. `AbstractSmileModel` becomes the single base class (renamed to `SmileModel`).
- **BREAKING** — Rename current `evaluate()` (native-only) to `_evaluate()` (private). Make `evaluate()` the coordinate-aware public method (current `__call__` logic).
- **BREAKING** — Remove `__call__` from models. The public API is `evaluate()` and `transform().evaluate()`.
- **BREAKING** — Remove `SVIModel.implied_vol()`. Replaced by `svi.transform(XCoord.LogMoneynessStrike, YCoord.Volatility).evaluate(k)`.
- **BREAKING** — Remove `M = TypeVar("M", bound=SmileModel)` from `protocol.py`; replace with `TypeVar` bound to the new single `SmileModel` class.
- Update `fitting.py` type hints to use the renamed `SmileModel` ABC directly.
- Update all exports in `__init__.py` files — remove `AbstractSmileModel`, keep `SmileModel`.
- Update all tests and the demo notebook.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `smile-model-protocol`: Remove Protocol class; `SmileModel` becomes the ABC. Remove `__call__`, make `evaluate()` coordinate-aware.
- `abstract-smile-model`: Rename to `SmileModel`. `evaluate()` replaces `__call__` as coordinate-aware entry point. Raw formula moves to abstract `_evaluate()`.
- `model-callable`: Remove — `__call__` is deleted. `evaluate()` is the single public evaluation method.
- `svi-model`: Remove `implied_vol()`. Rename `evaluate()` to `_evaluate()`.
- `sabr-model`: Rename `evaluate()` to `_evaluate()`.
- `smile-fitting`: Update type hints from Protocol to ABC. Remove `M` TypeVar re-export if needed.

## Impact

- **Source**: `src/qsmile/models/protocol.py`, `svi.py`, `sabr.py`, `fitting.py`, `models/__init__.py`, `qsmile/__init__.py`
- **Tests**: All tests under `tests/models/` — constructor patterns unchanged, but `evaluate()` semantics change and `implied_vol` calls removed.
- **Notebook**: `book/marimo/notebooks/qsmile_demo.py` — replace `implied_vol(k, t)` with `transform().evaluate()`, remove `__call__` usage.
- **Specs**: 6 existing specs modified, 0 new, 1 removed (`model-callable`).
- **No dependency changes**.
