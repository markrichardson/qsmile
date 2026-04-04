## Context

The `SmileModel` protocol defines the contract for pluggable smile models. Currently `SVIModel` is the sole implementation — a `@dataclass` with `ClassVar` metadata, instance-level `evaluate()`/`to_array()`, `@classmethod from_array()`, and `@staticmethod initial_guess()`. The fitting engine (`fit()`) works generically with any `type[M]` where `M` is bound to `SmileModel`.

Adding `SABRModel` reveals that `to_array()`, `from_array()`, and `param_names` follow an identical pattern across all dataclass-based models: pack/unpack fields in declaration order. This boilerplate should be extracted.

### Current module layout

| File | Contents |
|---|---|
| `protocol.py` | `SmileModel` Protocol + `M` TypeVar |
| `svi.py` | `SVIModel` dataclass (5 params, evaluate, initial_guess) |
| `fitting.py` | `SmileResult`, `fit()` |

## Goals / Non-Goals

**Goals:**
- Introduce `AbstractSmileModel` base class that provides default `to_array()`, `from_array()`, and `param_names` derived from dataclass fields.
- Implement `SABRModel` using Hagan et al. (2002) lognormal implied volatility approximation with parameters `(alpha, beta, rho, nu)`.
- Refactor `SVIModel` to inherit from `AbstractSmileModel`, eliminating duplicated serialisation code.
- Validate the framework by fitting SABR to synthetic and real-like data via `fit(sd, SABRModel)`.

**Non-Goals:**
- Alternative SABR formulations (normal vol, free-boundary, etc.) — follow-on work.
- Arbitrage-free calibration or calendar-spread constraints.
- Changes to the `SmileModel` protocol itself — it remains a structural typing contract.
- Changes to the fitting engine — `fit()` already works generically.

## Decisions

### 1. AbstractSmileModel as an abstract dataclass

**Decision**: Create `AbstractSmileModel` as an abstract `@dataclass` base class in `protocol.py`.

**Rationale**: Both `SVIModel` and `SABRModel` are dataclasses with the same serialisation pattern. An abstract base:
- Derives `param_names` from `dataclasses.fields()` automatically.
- Provides `to_array()` and `from_array()` using field order — no manual indexing.
- Leaves `evaluate()`, `initial_guess()`, `__post_init__()`, bounds, and native coords to subclasses.
- Satisfies the `SmileModel` protocol via structural typing (no explicit Protocol inheritance needed).

**Alternatives considered**:
- *Mixin*: Would work but less conventional for dataclass hierarchies.
- *Keep duplication*: Two models is fine, but three+ makes the cost clear. Better to DRY now.

### 2. SABR native coordinates: LogMoneynessStrike × Volatility

**Decision**: SABR operates in `(XCoord.LogMoneynessStrike, YCoord.Volatility)` — the fitting engine transforms market data to log-moneyness and implied vol before calling `evaluate()`.

**Rationale**: Hagan's formula maps `(forward, strike, expiry, alpha, beta, rho, nu) → implied vol`. The model receives log-moneyness `k = ln(K/F)` and returns implied volatility directly, unlike SVI which returns total variance. The fitting engine handles coordinate transforms automatically.

### 3. Hagan (2002) lognormal approximation

**Decision**: Use the standard Hagan et al. lognormal implied vol formula as the evaluation function.

**Rationale**: This is the industry-standard SABR approximation. It's well-understood, fast to evaluate, and sufficient for model fitting. More sophisticated approaches (Obloj correction, exact integration) can be added as alternative SABR variants later.

### 4. SABR requires expiry in evaluate

**Decision**: `SABRModel` will store `expiry` and `forward` as metadata fields (not fitted parameters) set during fitting, since Hagan's formula requires them. The fitting engine already provides this context via `SmileData`.

**Alternative approach**: Pass `expiry` and `forward` through `evaluate()` signature. Rejected because it would change the `SmileModel` protocol contract.

**Chosen approach**: `SABRModel` stores `expiry` and `forward` as dataclass fields that are NOT part of the fitted parameter vector. The `from_array()` classmethod and `initial_guess()` will need access to these values. This is handled by making `evaluate()` use `self.expiry` and `self.forward`, and having the fitting engine pass them through a model-level configuration mechanism.

**Revised decision**: Since `evaluate(x)` receives log-moneyness values and must return implied vol, and Hagan's formula needs `F` and `T` — these will be stored as non-fitted fields on the instance. The fitting residual function already has access to `SmileData` which contains `expiry` and `forward`. We'll add an optional `context` dict to `from_array()` or store `expiry`/`forward` as class-level state set before fitting. The simplest approach: `fit()` sets `SABRModel._expiry` and `SABRModel._forward` as class variables before the optimisation loop, and `evaluate()` reads them. This keeps the protocol unchanged.

**Simplest approach**: Add `expiry: float` and `forward: float` as regular dataclass fields on `SABRModel`, excluded from the parameter vector via a `_fitted_fields` ClassVar or by convention (they come after the fitted params). `to_array()` and `from_array()` in `AbstractSmileModel` will use a `param_names` ClassVar (explicitly listed) rather than all fields, so non-parameter fields are excluded.

### 5. param_names as explicit ClassVar (not derived from all fields)

**Decision**: Keep `param_names` as an explicit `ClassVar[tuple[str, ...]]` on each model, and derive `to_array()`/`from_array()` from `param_names` rather than from all dataclass fields.

**Rationale**: SABR needs non-parameter fields (`expiry`, `forward`) on the instance. Deriving from all fields would incorrectly include them. Explicit `param_names` is already the convention and gives full control.

## Risks / Trade-offs

- **Hagan approximation breaks down** for extreme parameters (very low strikes, beta near 0 with high vol-of-vol). → Mitigation: tight bounds on parameters, document limitations.
- **SABR fitting is less stable than SVI** — the Hagan formula can produce negative implied vol for extreme inputs. → Mitigation: clamp negative values in `evaluate()`, use sensible initial guess.
- **expiry/forward on SABRModel** adds fields that don't exist on SVIModel, creating asymmetry. → Acceptable trade-off: different models have different context requirements. The protocol doesn't mandate field homogeneity.
- **AbstractSmileModel** adds an inheritance layer. → Minimal risk: it's a thin convenience with no complex behaviour. Models can still satisfy the protocol without inheriting from it.
