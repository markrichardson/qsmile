## Context

`SmileData.from_mid_vols` currently accepts `forward`, `date`, `expiry`, `discount_factor`, and `daycount` as separate scalar parameters and internally constructs a `SmileMetadata`. Meanwhile, `OptionChain` already accepts a `SmileMetadata` directly. This inconsistency creates unnecessary coupling: callers that already have a `SmileMetadata` must unpack it to call `from_mid_vols`, and callers constructing data ad-hoc must remember which individual parameters to pass.

The current `from_mid_vols` code constructs `SmileMetadata` internally, which means `sigma_atm` derivation (finding the ATM strike closest to `forward`) is always performed during construction.

## Goals / Non-Goals

**Goals:**
- Add a `metadata`-accepting overload to `SmileData.from_mid_vols` so callers can pass `SmileMetadata` directly.
- Preserve the existing scalar-parameter signature for convenience and backward compatibility.
- Update documentation, examples, and tests to showcase the metadata-based construction.

**Non-Goals:**
- Removing or deprecating the scalar-parameter overload.
- Changing the `SmileData` dataclass constructor itself (it already accepts `metadata: SmileMetadata`).
- Modifying `OptionChain`, `SmileMetadata`, or coordinate map APIs.
- Changing the fitting pipeline or `SmileModel` protocol.

## Decisions

### 1. Union-based overload with optional `metadata` parameter

Add an optional `metadata: SmileMetadata | None = None` parameter to `from_mid_vols`. When provided, `forward`/`date`/`expiry`/`discount_factor`/`daycount` become unnecessary. When `metadata` is `None` (default), the existing scalar parameters are used as before.

**Rationale**: A single method with optional `metadata` is simpler than `@overload` type stubs or a separate `from_mid_vols_with_metadata` method. It keeps the API surface minimal.

**Behaviour**:
- If `metadata` is provided, extract `forward` from `metadata.forward` for ATM derivation. The `forward`/`date`/`expiry`/`discount_factor`/`daycount` scalar parameters are ignored.
- If `metadata` is `None`, construct `SmileMetadata` from scalar parameters as before.
- `sigma_atm` is always derived from the data (ATM strike closest to `forward`), even when a `metadata` is passed — the passed `metadata.sigma_atm` is overwritten.

### 2. `metadata.forward` required when using metadata overload

When `metadata` is passed, `metadata.forward` must not be `None` because ATM derivation requires it. A `TypeError` is raised if `metadata.forward is None`.

**Rationale**: `forward` is essential for both ATM index computation and the FixedStrike coordinate system.

## Risks / Trade-offs

- [Overwriting `sigma_atm`] → Acceptable because `from_mid_vols` always derives `sigma_atm` from the data. Documented in the docstring that the value is recomputed.
- [Parameter ambiguity when both `metadata` and scalar params are passed] → Mitigated by documenting that `metadata` takes precedence; scalar params are ignored when `metadata` is given.
