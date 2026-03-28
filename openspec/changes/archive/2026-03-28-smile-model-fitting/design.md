## Context

qsmile is a Python library for volatility smile modelling. The codebase currently contains only placeholder functionality (`greet`, `approximate`) with no domain logic. The project already depends on `chebpy` and has `numpy` as a dev dependency. The goal is to introduce the foundational layer: ingesting option chain data, representing the SVI model, and fitting it to market observations.

The SVI (Stochastic Volatility Inspired) model, introduced by Gatheral (2004), parameterises total implied variance $w(k)$ as a function of log-moneyness $k = \ln(K/F)$:

$$w(k) = a + b \left( \rho (k - m) + \sqrt{(k - m)^2 + \sigma^2} \right)$$

where $a, b, \rho, m, \sigma$ are the five raw SVI parameters. This is the most widely used smile parameterisation in equity derivatives.

## Goals / Non-Goals

**Goals:**
- Provide a clean data model for option chain inputs (strikes, implied vols, forward, expiry).
- Implement SVI raw parameterisation with parameter evaluation and constraint checking.
- Build a least-squares fitting engine that calibrates SVI parameters to market data.
- Return structured results with fitted parameters, residuals, and goodness-of-fit metrics.
- Ensure the API is simple enough for a single-expiry fitting workflow in < 5 lines of user code.

**Non-Goals:**
- Multi-expiry / surface fitting (future work).
- SVI-JW or other alternative SVI parameterisations (can be added later).
- Real-time or streaming data ingestion.
- Visualisation or plotting utilities (users can use plotly/matplotlib directly).
- Arbitrage-free enforcement (e.g. butterfly arbitrage checks) — future enhancement.
- Support for other model families (SABR, Heston) in this change.

## Decisions

### 1. Module structure

Introduce three new modules under `src/qsmile/`:

| Module | Responsibility |
|---|---|
| `chain.py` | `OptionChain` dataclass — validated container for market data |
| `svi.py` | `SVIParams` dataclass + `svi_total_variance(k, params)` evaluation function |
| `fitting.py` | `fit_svi(chain) -> SmileResult` — calibration entry point |

`core.py` will be repurposed as the public re-export surface (or removed if `__init__.py` suffices).

**Rationale**: Separation by domain concern keeps each module focused and testable. A single-file approach would become unwieldy as more models are added.

### 2. Use dataclasses, not Pydantic

Option chain and SVI parameters will use `@dataclass` with explicit validation in `__post_init__`.

**Alternatives considered**: Pydantic would give richer validation but adds a heavyweight dependency for what are fundamentally numeric containers. `NamedTuple` is too restrictive (immutable, no methods). Plain dataclasses with targeted validation strike the right balance.

### 3. NumPy arrays as the core data type

Strikes, implied volatilities, and computed values will be `numpy.ndarray`. The `OptionChain` will store arrays, not lists.

**Rationale**: All downstream computation (SVI evaluation, least-squares fitting) operates on arrays. Converting at the boundary avoids repeated conversions and makes the API natural for quant users.

### 4. SVI raw parameterisation only

Implement only the raw parameterisation $(a, b, \rho, m, \sigma)$ initially.

**Rationale**: Raw SVI is the most common form and maps directly to the optimisation. SVI-JW and other forms can be added as transformations later without changing the fitting engine.

### 5. scipy.optimize for fitting

Use `scipy.optimize.least_squares` (Trust Region Reflective) with box constraints on the SVI parameters.

**Alternatives considered**:
- `scipy.optimize.minimize` with scalar objective: `least_squares` is purpose-built for residual-based problems and provides Jacobian-based convergence.
- Custom gradient descent: unnecessary complexity; scipy is well-tested and handles bounds natively.

Parameter bounds:
- $b \geq 0$ (variance must be non-negative in the wings)
- $-1 < \rho < 1$ (correlation)
- $\sigma > 0$ (curvature)
- $a + b\sigma\sqrt{1 - \rho^2} \geq 0$ (non-negative variance at the vertex) — enforced as a post-fit check

### 6. SmileResult as the return type

`fit_svi` returns a `SmileResult` dataclass containing:
- `params: SVIParams` — fitted parameters
- `residuals: ndarray` — per-strike residuals
- `rmse: float` — root mean square error
- `success: bool` — whether optimisation converged
- An `evaluate(k)` method to compute implied variance at arbitrary log-moneyness

**Rationale**: Bundling parameters with diagnostics and evaluation in one object gives users everything they need from a single call.

## Risks / Trade-offs

- **Initial parameter guess sensitivity** → Use a heuristic initialisation (ATM variance for $a$, slope estimate for $b \cdot \rho$, etc.) and document that users can supply custom initial guesses.
- **No arbitrage checks** → Fitted SVI may admit butterfly arbitrage for extreme strikes. Accepted for v1; document as a known limitation.
- **Breaking existing API** → `greet()` and `approximate()` are removed. Acceptable since qsmile has no external consumers yet (pre-release v0.0.1-rc.2).
- **New runtime dependencies** → Adding `numpy` and `scipy` as runtime deps increases install footprint. Both are standard in quantitative Python and expected by the target audience.
