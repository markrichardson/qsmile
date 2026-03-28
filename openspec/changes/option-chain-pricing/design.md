## Context

The `qsmile` library currently models option chains as mid implied volatilities via the `OptionChain` dataclass. In practice, options market data arrives as bid/ask prices, and quants need to:

1. Calibrate forwards and discount factors when not externally provided.
2. Convert prices to implied volatilities (and back) using Black76.
3. Work in a unitised (normalised) strike/variance coordinate system for stable SVI fitting.

The existing `OptionChain` → `fit_svi` pipeline remains intact. The new classes sit upstream, transforming raw market prices into the vol-space representation that `OptionChain` already expects, while adding bid/ask awareness throughout.

## Goals / Non-Goals

**Goals:**
- Provide a clean pipeline: `OptionChainPrices` → `OptionChainVols` → `UnitisedSpaceVols`.
- Support bid/ask spreads as first-class data through all representations.
- Implement Black76 pricing and implied vol inversion.
- Calibrate forward and discount factor from put-call parity when not user-supplied, using a delta-blend weighted least-squares fit (cvxpy).
- Provide `.plot()` on each class showing bid/ask as error bars.
- Use `cvxpy` for the new optimisation problems.

**Non-Goals:**
- Replacing the existing `OptionChain` / `fit_svi` pipeline (they remain as-is).
- Supporting American options or early exercise.
- Multi-expiry surface fitting (this remains single-expiry).
- Real-time streaming or live market data integration.
- Replacing `scipy` in the existing SVI fitting code.

## Decisions

### 1. Three-class pipeline: Prices → Vols → UnitisedSpace

**Decision**: Introduce three separate dataclasses rather than a single monolithic class.

**Rationale**: Each representation has distinct invariants and use cases. `OptionChainPrices` validates price-level constraints (non-negative prices, call/put parity structure). `OptionChainVols` validates vol-level constraints (non-negative vols, requires forward). `UnitisedSpaceVols` normalises coordinates for fitting. Conversion methods on each class produce the next representation in the chain.

**Alternatives considered**: A single class with mode flags was rejected—it conflates validation logic and makes the API harder to reason about.

### 2. Black76 as a standalone module

**Decision**: Create `src/qsmile/black76.py` with pure functions for call/put pricing and implied vol inversion.

**Rationale**: Black76 is a general-purpose tool used by the price→vol conversion but also useful independently. Keeping it in its own module follows the existing pattern (e.g., `svi.py` for SVI evaluation). Implied vol inversion will use Brent's method from `scipy.optimize.brentq`, which is standard and robust.

### 3. Forward/DF calibration via put-call parity with delta-blend weighting

**Decision**: When the user does not supply forward and discount factor, fit them from put-call parity $C - P = D \cdot (F - K)$ using weighted least squares. The weighting scheme is "delta blend": strikes near the ATM forward receive higher weight, decaying for deep OTM/ITM strikes.

**Rationale**: Put-call parity is model-free and gives a linear relationship between $C - P$ and $K$, so the forward $F$ and discount factor $D$ can be recovered via linear regression. Delta-blend weighting emphasises the most liquid strikes (ATM), which have the tightest spreads and most reliable prices. This is implemented as a convex optimisation in `cvxpy` for clarity and extensibility (e.g., adding constraints like $D \in (0, 1]$ or $F > 0$).

**Weight function**: $w_i = \exp(-\alpha \cdot |K_i - F_0|^2 / \bar{K}^2)$ where $F_0$ is an initial forward estimate (mid of tightest spread strike) and $\alpha$ controls the blend rate. This approximates a delta-based weighting without needing vols upfront.

**Alternatives considered**: Unweighted OLS (gives too much influence to illiquid wings); using Black76 deltas for weights (requires vols, creating a chicken-and-egg problem).

### 4. cvxpy for new optimisations

**Decision**: Use `cvxpy` for the forward/DF calibration problem. Future fitting work will also use cvxpy.

**Rationale**: The forward/DF calibration is a constrained weighted least-squares problem ($D > 0$, $F > 0$). `cvxpy` makes constraints declarative and supports a range of solvers. This aligns with the user's direction for the library.

### 5. Plotting with matplotlib

**Decision**: Each class provides a `.plot()` method returning a `matplotlib.figure.Figure`. Bid/ask shown as error bars (vertical bars from bid to ask at each strike).

**Rationale**: `matplotlib` is the standard for static quant plots. Returning the `Figure` object lets users customise further. `plotly` is already a dev dependency but `matplotlib` is more appropriate for library-level plotting where static output suffices.

### 6. Unitised space definition

**Decision**: Use the normalised coordinates $\tilde{k} = \log(K/F) / (\sigma_{\text{ATM}} \sqrt{t})$ and $v = \sigma_k^2 \, t$ where $\sigma_{\text{ATM}}$ is the at-the-money implied volatility.

**Rationale**: This normalisation removes the scale dependence on ATM vol level and time to expiry, making SVI parameters comparable across expiries and underliers. It is standard in the SVI literature (Gatheral & Jacquier).

### 7. File layout

New source files under `src/qsmile/`:
- `black76.py` — Black76 pricing and implied vol inversion
- `prices.py` — `OptionChainPrices` class and forward/DF calibration
- `vols.py` — `OptionChainVols` class with price→vol conversion
- `unitised.py` — `UnitisedSpaceVols` class
- `plot.py` — shared plotting utilities (error bar rendering)

## Risks / Trade-offs

- **cvxpy dependency weight** → cvxpy is a large dependency. Mitigation: it brings significant value for constrained optimisation and the user has explicitly requested it. Pin to a stable version range.
- **Black76 implied vol inversion convergence** → Brent's method can fail for extreme prices. Mitigation: validate input prices are within no-arbitrage bounds before inversion; return NaN for prices outside bounds with a warning.
- **Delta-blend weight function sensitivity** → The weighting parameter $\alpha$ affects forward/DF calibration quality. Mitigation: provide a sensible default and allow user override.
- **matplotlib as a new dependency** → Adds to install size. Mitigation: make it an optional dependency; `.plot()` raises `ImportError` with a helpful message if not installed.
