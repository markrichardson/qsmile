## Context

The model layer in `src/qsmile/models/` currently has two parallel abstractions:

1. `SmileModel` — a `@runtime_checkable` Protocol defining the model interface
2. `AbstractSmileModel` — an ABC dataclass providing default implementations

Every concrete model (`SVIModel`, `SABRModel`) subclasses `AbstractSmileModel`. The Protocol is only used for type annotations in `fitting.py` and `isinstance` checks in tests — both of which work identically with the ABC. The two-class design adds indirection without value.

Additionally, the public API surface has redundancy:
- `evaluate(x)` — native coords only, abstract (subclasses implement)
- `__call__(x)` — coordinate-aware wrapper around `evaluate`
- `SVIModel.implied_vol(k, t)` — convenience for `sqrt(w/T)`, absent from SABR

The intended workflow `model.transform(x, y).evaluate(x)` currently doesn't work because `evaluate` ignores coordinate state. Users must use `__call__` instead, which is non-obvious.

## Goals / Non-Goals

**Goals:**
- Single base class `SmileModel` (no Protocol + ABC split)
- `evaluate()` is the one public evaluation method, coordinate-aware
- Remove `__call__` — models are not callable
- Remove `implied_vol` — use `transform()` instead
- Minimal files touched, straightforward rename/collapse

**Non-Goals:**
- Changing the coordinate system or transform machinery
- Changing the fitting engine logic
- Adding new model types
- Backward compatibility

## Decisions

### 1. Collapse Protocol + ABC into a single ABC named `SmileModel`

**Choice**: Delete the Protocol. Rename `AbstractSmileModel` → `SmileModel`. Keep it as `@dataclass` + `ABC`.

**Rationale**: The Protocol exists only because "you might want a model that doesn't use dataclasses." In practice, every model is a dataclass, and the Protocol duplicates every signature from the ABC. One class eliminates the duplication.

**Alternative considered**: Keep Protocol, remove ABC. Rejected — the ABC provides `to_array`, `from_array`, `evaluate` (coordinate-aware), `transform`, `plot`, and `params`. These are substantial shared implementations that subclasses should not reimplement.

### 2. Rename `evaluate` → `_evaluate` (native), move `__call__` logic into `evaluate`

**Choice**: The abstract method subclasses implement becomes `_evaluate(x)` (private, native coords). The public `evaluate(x)` gains the coordinate-transform logic currently in `__call__`.

**Rationale**: Users expect `evaluate` to be the primary API. Making it coordinate-aware means `model.transform(x, y).evaluate(x_values)` works as intended, which is the natural reading.

**Alternative considered**: Keep both `evaluate` and `__call__`. Rejected — two evaluation methods with different coordinate semantics is confusing.

### 3. Remove `__call__` entirely

**Choice**: Models are not callable. Use `model.evaluate(x)`.

**Rationale**: `__call__` is syntactic sugar that obscures what coordinate system is being used. Explicit `evaluate()` is clearer. `model(x)` is ambiguous — is it native or current coords? `model.evaluate(x)` with documented coordinate-aware semantics is unambiguous.

### 4. Remove `SVIModel.implied_vol`

**Choice**: Delete it. The equivalent is `svi.transform(XCoord.LogMoneynessStrike, YCoord.Volatility).evaluate(k)`.

**Rationale**: `implied_vol` was an SVI-specific convenience that broke the symmetry with SABR. The coordinate transform system already handles this conversion generically.

### 5. TypeVar update

**Choice**: `M = TypeVar("M", bound=SmileModel)` stays, but now bound to the ABC instead of the deleted Protocol. No functional change.

## Risks / Trade-offs

- **[Risk] Notebook breakage** → The demo notebook calls `svi_result.params.implied_vol(...)` in two places and uses `__call__` syntax. Both will be updated in tasks. The notebook is a marimo script; changes are mechanical.
- **[Risk] External consumers** → No backward compatibility. This is an internal library. Breaking changes are acceptable.
- **[Trade-off] `_evaluate` naming** → Private prefix signals "don't call directly" but subclass authors must override it. This is a standard Python pattern (e.g., `collections.abc` uses `__getitem__` for the same purpose). Documented in the class docstring.
