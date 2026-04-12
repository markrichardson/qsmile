## Context

`SmileResult` is currently `Generic[M]` where `M = TypeVar("M", bound=SmileModel)`. This preserves the concrete model type on the `params` field so that `fit(sd, SVIModel)` returns `SmileResult[SVIModel]`. In practice, callers always know which model they passed and the generic adds complexity across two files for no runtime benefit.

The `params` field name is also misleading — it holds a full model instance (with metadata, coordinates, evaluate), not just parameters.

## Goals / Non-Goals

**Goals:**
- Remove `M` TypeVar and `Generic[M]` from `SmileResult`
- Rename `SmileResult.params` → `SmileResult.model` with type `SmileModel`
- Simplify `fit()` type signature
- Update all call sites

**Non-Goals:**
- Changing `fit()` behaviour or API beyond type simplification
- Adding new functionality to `SmileResult`

## Decisions

### 1. Rename `params` to `model`

The field holds a coordinate-aware `SmileModel` instance, not a parameter dict. The `.params` property on `SmileModel` already provides the parameter dict. Renaming avoids the ambiguity: `result.model.params` reads clearly as "the fitted model's parameters".

### 2. Drop Generic rather than keeping it with a simpler bound

Alternatives: keep `Generic[SmileModel]` (pointless — same as concrete type). The TypeVar existed solely for type narrowing; without it the Generic serves no purpose.

### 3. Simplify `fit()` signature

`fit(chain, model: type[SmileModel], initial_guess: SmileModel | None = None) -> SmileResult`. The `type[SmileModel]` parameter still accepts any subclass at runtime; we just lose static narrowing of the return type, which is acceptable.

## Risks / Trade-offs

- **Lost type narrowing** → Callers accessing model-specific attributes (e.g. `result.model.a`) will need a cast or isinstance check for strict type checking. Acceptable: tests already access these without type checking, and the codebase doesn't use mypy strictly.
- **Breaking rename** → All `result.params` usages must update to `result.model`. Mitigated by comprehensive task list covering all call sites.
