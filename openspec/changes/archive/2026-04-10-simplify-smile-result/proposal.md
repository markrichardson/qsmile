## Why

`SmileResult` uses `Generic[M]` with `M = TypeVar("M", bound=SmileModel)` to preserve the concrete model type on `result.params`. This adds complexity (TypeVar in protocol.py, Generic import, parameterised return types) for minimal practical benefit — callers always know which model they passed to `fit()` and can cast if needed. Renaming `params` to `model` also better communicates what the field holds.

## What Changes

- **BREAKING**: Rename `SmileResult.params` field to `SmileResult.model` with type `SmileModel`
- **BREAKING**: Remove `Generic[M]` from `SmileResult` — it becomes a plain dataclass
- Delete `M = TypeVar("M", bound=SmileModel)` from `protocol.py`
- Simplify `fit()` signature: `model: type[SmileModel]` parameter, returns `SmileResult`
- Update all call sites accessing `result.params` to use `result.model`

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `smile-fitting`: `SmileResult` loses generic type parameter; `params` field renamed to `model` with type `SmileModel`

## Impact

- `src/qsmile/models/protocol.py` — remove `M` TypeVar
- `src/qsmile/models/fitting.py` — simplify `SmileResult` and `fit()` signatures
- All tests referencing `result.params` — rename to `result.model`
- `book/marimo/notebooks/qsmile_demo.py` — rename `result.params` to `result.model`
