## Why

The fitting infrastructure is currently hard-wired to the SVI model: `fit_svi()` internally transforms to `(LogMoneynessStrike, TotalVariance)`, uses SVI-specific residuals, box constraints, and initial-guess heuristics, and returns `SmileResult` whose `evaluate()` delegates to `svi_total_variance`. This makes it impossible to add alternative smile models (e.g. SABR, polynomial, cubic spline) without duplicating the entire fitting pipeline. A generic model protocol would let each model declare its own native coordinates, parameters, constraints, and evaluation function while the fitting engine, result container, and SmileData integration remain shared.

## What Changes

- Introduce a `SmileModel` protocol (or ABC) that every smile model must satisfy: native X/Y coordinates, parameter names/bounds, evaluation function, and initial-guess heuristic.
- Make `SmileResult` model-agnostic: store generic params alongside the model reference so `evaluate()` works for any model.
- Add a generic `fit(chain: SmileData, model: SmileModel)` entry point that transforms the data to the model's native coordinates, runs the optimiser, and returns a `SmileResult`.
- Refactor `SVIParams` / `svi_total_variance` to implement the new `SmileModel` protocol, keeping existing public API (`fit_svi`, `SVIParams`) as thin wrappers.
- **BREAKING**: `SmileResult.params` changes from `SVIParams` to a generic type; callers that type-annotate against `SVIParams` will need updating.

## Capabilities

### New Capabilities
- `smile-model-protocol`: Defines the `SmileModel` protocol — native coordinates, parameter schema, evaluation, initial guess, and box constraints.
- `generic-fitting`: Generic `fit(chain, model)` function that transforms data, delegates to the model, and returns a model-agnostic `SmileResult`.

### Modified Capabilities
- `smile-fitting`: `SmileResult` becomes model-agnostic; `fit_svi` becomes a convenience wrapper around `fit` + SVI model.
- `svi-model`: `SVIParams` / SVI functions conform to the new `SmileModel` protocol.

## Impact

- **Code**: `src/qsmile/models/fitting.py` (major refactor), `src/qsmile/models/svi.py` (protocol conformance), `src/qsmile/__init__.py` (new exports).
- **API**: New `SmileModel` protocol, new `fit()` function. Existing `fit_svi()` preserved as convenience wrapper. `SmileResult.params` type widens.
- **Tests**: Existing `test_fitting.py` and `test_svi.py` updated; new tests for protocol conformance and generic fitting.
- **Dependencies**: No new external dependencies.
