## Why

qsmile is intended to be a volatility smile modelling library, but currently only contains placeholder code (a greeting function and a generic Chebyshev approximation helper). The core domain functionality — representing volatility smiles, fitting parametric models such as SVI to market option chain data, and evaluating fitted smiles — does not yet exist. Building this foundational layer is the essential next step to make qsmile useful as a quantitative finance library.

## What Changes

- Introduce a data model for option chain market data (strikes, implied volatilities, expiry, forward price).
- Implement the SVI (Stochastic Volatility Inspired) parametric smile model with its raw parameterisation.
- Build a fitting engine that calibrates SVI parameters to observed market data via least-squares optimisation.
- Provide smile evaluation: given fitted parameters, compute implied volatility for arbitrary strikes/moneyness values.
- Add a `SmileResult` object that bundles fitted parameters, goodness-of-fit metrics, and evaluation methods.
- Remove the placeholder `greet` function and repurpose `core.py` for domain-relevant code.

## Capabilities

### New Capabilities
- `option-chain`: Data model for ingesting and validating option chain market data (strikes, IVs, expiry, forward).
- `svi-model`: SVI raw parameterisation — representation, evaluation, and parameter constraints.
- `smile-fitting`: Calibration engine that fits smile model parameters to option chain data via optimisation.

### Modified Capabilities

_None — no existing specs to modify._

## Impact

- **Code**: `src/qsmile/core.py` will be replaced with domain modules. New modules under `src/qsmile/` for data models, SVI model, and fitting.
- **Tests**: Existing tests for `greet` and `approximate` will be removed; new tests for all three capabilities.
- **Dependencies**: Will add `numpy` and `scipy` as runtime dependencies (currently `numpy` is dev-only; `scipy` is new).
- **APIs**: This is the first real public API surface for qsmile — no breaking changes since no consumers exist yet.
