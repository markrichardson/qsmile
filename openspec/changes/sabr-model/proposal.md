## Why

The fitting framework currently supports only the SVI model. Adding a second model (SABR) will validate the `SmileModel` protocol's generality and expose any boilerplate that should be factored into a shared base class. Both SVI and SABR models share identical patterns — `ClassVar` metadata, `to_array`/`from_array` round-tripping, `__post_init__` validation — that can be extracted into an `AbstractSmileModel` base class, reducing per-model implementation to just the model-specific fields, constraints, evaluation, and initial-guess heuristic.

## What Changes

- Introduce `AbstractSmileModel` — an abstract dataclass base in `protocol.py` that provides default implementations of `to_array()` and `from_array()` derived from dataclass fields, so concrete models only need to define fields, `ClassVar` metadata, validation, `evaluate()`, and `initial_guess()`.
- Introduce `SABRModel` — a new SABR (Stochastic Alpha Beta Rho) normal implied-volatility model in `src/qsmile/models/sabr.py` with parameters `(alpha, beta, rho, nu)`, operating in `(LogMoneynessStrike, Volatility)` native coordinates, using Hagan's 2002 approximation formula for evaluation.
- Refactor `SVIModel` to inherit from `AbstractSmileModel`, removing the boilerplate `to_array()` and `from_array()` implementations.
- Export `SABRModel` and `AbstractSmileModel` from `qsmile.models` and `qsmile`.

## Capabilities

### New Capabilities
- `sabr-model`: SABR model dataclass with parameters `(alpha, beta, rho, nu)`, Hagan approximation evaluation, validation, and initial-guess heuristic.
- `abstract-smile-model`: Shared abstract dataclass base providing default `to_array()`, `from_array()`, and `param_names` derived from dataclass fields.

### Modified Capabilities
- `svi-model`: SVIModel refactored to inherit from `AbstractSmileModel`, removing duplicated `to_array()` and `from_array()`.

## Impact

- **New files**: `src/qsmile/models/sabr.py`, `tests/models/test_sabr.py`
- **Modified files**: `src/qsmile/models/protocol.py` (add `AbstractSmileModel`), `src/qsmile/models/svi.py` (inherit from base), `src/qsmile/models/__init__.py`, `src/qsmile/__init__.py` (exports)
- **Dependencies**: No new external dependencies — SABR uses only numpy/scipy already present.
- **API**: Additive only. Existing `fit(sd, SVIModel)` usage is unchanged. New usage: `fit(sd, SABRModel)`.
