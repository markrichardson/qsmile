## Context

`OptionChain` currently accepts three scalar parameters — `expiry: float`, `forward: float | None`, `discount_factor: float | None` — and echoes the same triple into `SmileMetadata` inside `to_smile_data()`. The rest of the codebase (`SmileData`, coordinate transforms, fitting) already passes metadata as a single `SmileMetadata` object. This change closes the gap so that `SmileMetadata` is the uniform metadata carrier from construction through conversion.

`SmileMetadata` is currently frozen with all-required positive fields (except optional `sigma_atm`). To support "calibrate if not provided" semantics, `forward` and `discount_factor` must become optional on `SmileMetadata`.

## Goals / Non-Goals

**Goals:**

- Replace `expiry`, `forward`, `discount_factor` on `OptionChain` with a single `metadata: SmileMetadata` field.
- Preserve the existing "calibrate if not given" behavior for forward and discount factor.
- Keep `SmileMetadata` frozen — calibration produces a new instance stored on `OptionChain`.
- Keep `expiry` always-required (it cannot be calibrated).

**Non-Goals:**

- Changing calibration logic in `_calibrate_forward_df`.
- Modifying `SmileData`, coordinate transforms, or model fitting code.
- Adding convenience properties for `chain.forward` etc. — callers use `chain.metadata.forward`.

## Decisions

### 1. SmileMetadata gets optional forward/discount_factor

`forward` and `discount_factor` become `float | None = None`. `expiry` remains required and positive. Validation adjusts: positive checks only fire when the value is not `None`. This lets callers write `SmileMetadata(expiry=0.25)` and leave calibration to `OptionChain`.

**Alternative**: Create a separate `PartialMetadata` type — rejected because it doubles the surface area for no real benefit.

### 2. OptionChain stores metadata as a regular field (not InitVar)

`metadata` is a normal dataclass field of type `SmileMetadata`. In `__post_init__`, if `forward` or `discount_factor` is `None`, calibrate them and replace `self.metadata` with a new `SmileMetadata` instance containing the calibrated values (using `dataclasses.replace`). The field is mutable on the dataclass despite `SmileMetadata` itself being frozen.

**Alternative**: Use `InitVar` for the three scalars and synthesise `metadata` in `__post_init__` — rejected because it splits the API: constructor takes scalars, instance holds metadata. The user should think in terms of metadata at all layers.

### 3. No convenience properties

Callers access `chain.metadata.forward`, `chain.metadata.discount_factor`, `chain.metadata.expiry`. No shortcut properties are added — they would be redundant indirection.

## Risks / Trade-offs

- **Breaking API** → All call-sites must change from `OptionChain(..., expiry=T, forward=F, discount_factor=D)` to `OptionChain(..., metadata=SmileMetadata(expiry=T, forward=F, discount_factor=D))`. Mitigated by: the codebase is small and all sites are known.
- **SmileMetadata relaxation** → `forward`/`discount_factor` can now be `None`, which widens the type. Mitigated by: downstream consumers (coordinate maps, fitting) still require non-`None` values and will fail fast if given incomplete metadata.
- **Frozen metadata with mutable host** → `OptionChain.__post_init__` replaces `self.metadata` via object.__setattr__ or by not being frozen itself. No issue — `OptionChain` is not frozen.
