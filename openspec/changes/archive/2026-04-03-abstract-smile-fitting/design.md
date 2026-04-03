## Context

The current fitting infrastructure in `src/qsmile/models/fitting.py` is a single monolithic function (`fit_svi`) that hard-codes every aspect of the SVI model: native coordinates (`LogMoneynessStrike`, `TotalVariance`), parameter vector layout (a, b, rho, m, sigma), box constraints, initial-guess heuristic, and the residual function. `SmileResult` is equally SVI-specific — its `params` field is typed `SVIParams` and `evaluate()` delegates to `svi_total_variance`.

Adding a second smile model (e.g. SABR, polynomial, cubic spline) today would require duplicating the entire fitting function, result class, and all tests. The `SmileData.transform()` infrastructure already supports arbitrary coordinate conversions, so the missing piece is a model abstraction that declares "I work in these coordinates, here are my parameters and constraints, here is how to evaluate me."

## Goals / Non-Goals

**Goals:**
- Define a `SmileModel` protocol that any smile model can implement.
- Provide a generic `fit(chain, model)` entry point that transforms data to the model's native coordinates, runs the optimiser, and returns a model-agnostic result.
- Refactor SVI to conform to the protocol without breaking existing tests or notebooks.
- Keep `fit_svi()` and `SVIParams` in the public API as convenience wrappers.

**Non-Goals:**
- Implementing additional smile models (SABR, polynomial, etc.) — that's follow-on work.
- Changing the optimiser backend (scipy `least_squares` stays for now).
- Weighted fitting, regularisation, or multi-expiry surface fitting.
- Arbitrage-free constraint enforcement at the protocol level.

## Decisions

### Decision 1: `typing.Protocol` over ABC

Use a `typing.Protocol` (structural subtyping) rather than an `abc.ABC`. Models opt in by implementing the required methods — no inheritance hierarchy needed. This keeps `SVIParams` as a plain dataclass that also satisfies the protocol.

*Alternative considered*: ABC with `register()`. Rejected because it forces SVI (and future models) into an inheritance chain and adds boilerplate.

### Decision 2: Model declares native coordinates

Each `SmileModel` exposes `native_x_coord` and `native_y_coord` properties. The generic `fit()` function calls `chain.transform(model.native_x_coord, model.native_y_coord)` before fitting. This keeps coordinate knowledge inside the model where it belongs.

### Decision 3: Model provides parameter packing/unpacking

The protocol requires `to_array() -> NDArray` and `from_array(x) -> Self` methods plus `bounds() -> tuple[list, list]` for box constraints and `initial_guess(x, y) -> NDArray` for the heuristic. This lets the generic fitter work with a flat `NDArray` while the model owns the semantic meaning of each element.

### Decision 4: `SmileResult` becomes generic

`SmileResult` stores a `model: SmileModel` reference and `params: SmileModel` (the fitted instance). `evaluate(x)` delegates to `model.evaluate(x)` using the fitted params. Callers that need SVI-specific access use `result.params` with a type narrowing check or call `fit_svi()` which returns `SmileResult` with `params` already typed as the SVI model.

*Alternative considered*: Generic `SmileResult[M]` with type parameter. Rejected as over-engineering at this stage — the protocol is enough.

### Decision 5: File layout

- New file `src/qsmile/models/protocol.py` for the `SmileModel` protocol.
- `fitting.py` gets the generic `fit()` alongside the existing `fit_svi()` wrapper.
- `svi.py` adds protocol conformance methods to a new `SVI` class (or module-level object) that wraps `SVIParams`.
- No new subpackages needed.

## Risks / Trade-offs

- **[API surface width]** Adding `SmileModel`, `SVI`, and `fit()` alongside existing `SVIParams`, `fit_svi` increases the public API. → Mitigation: `fit_svi` and `SVIParams` remain the recommended entry points for SVI users; the generic API is opt-in.
- **[Type narrowing]** `SmileResult.params` widening from `SVIParams` to `SmileModel` is a breaking change for type-checked callers. → Mitigation: `fit_svi()` return type can be `SmileResult` with a documented `.params` type; users who need the typed params use `fit_svi()`.
- **[Protocol compliance burden]** Future model authors must implement ~6 methods/properties. → Mitigation: keep the protocol minimal; provide a test helper or base mixin if adoption proves painful.
