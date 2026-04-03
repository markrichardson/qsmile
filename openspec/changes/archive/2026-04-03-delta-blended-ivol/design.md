## Context

`OptionChain` holds bid/ask prices for both calls and puts at every strike. The current `to_smile_data()` converts to `SmileData` in Price coordinates using call prices only. When transformed to vol space via `SmileData.transform()`, the `_price_to_vol` map inverts Black76 with `is_call=True` at every strike — including deep ITM calls where bid-ask spreads are wide and the vol inversion is ill-conditioned.

Market practitioners typically use OTM options for smile construction because they are more liquid. A hard OTM cutoff (puts below forward, calls above) introduces a discontinuity at the forward. The standard remedy is a delta-weighted blend that smoothly transitions from put-implied vol in the left wing to call-implied vol in the right wing.

## Goals / Non-Goals

**Goals:**
- Provide a method on `OptionChain` that returns a `SmileData` in `(FixedStrike, Volatility)` coordinates using delta-blended implied vols.
- The blending must be smooth (no discontinuity at the forward) and converge to pure OTM vol in each wing.
- Preserve bid/ask structure in the output — blend bid vols and ask vols independently.

**Non-Goals:**
- Replacing the existing `to_smile_data()` method — it remains as-is for users who want raw call prices.
- Supporting blending strategies other than Black76 call-delta weighting (e.g., vega-weighted, or custom user-supplied weights).
- Changing the coordinate transform pipeline in `maps.py` — the blending happens before the data enters `SmileData`.

## Decisions

### 1. Blending weight: Black76 undiscounted call delta

The blending weight at each strike $K$ is the undiscounted Black76 call delta:

$$w(K) = \Phi(d_1), \qquad d_1 = \frac{ \ln(F/K) + \tfrac{1}{2}\sigma^2 t }{ \sigma \sqrt{t} }$$

where $\sigma$ is the _mid_ call-implied vol (or an initial ATM estimate for bootstrapping). The blended mid vol is:

$$\sigma_{\text{blend}}(K) = w(K)\,\sigma_C(K) + (1 - w(K))\,\sigma_P(K)$$

**Why undiscounted delta?** The undiscounted call delta $\Phi(d_1)$ is the natural probability-like weight that runs from ≈1 for deep ITM calls (≈0 for puts) to ≈0 for deep OTM calls (≈1 for puts), crossing 0.5 near the forward. It is the standard market convention.

**Alternative considered:** Hard OTM cutoff — simpler but introduces a discontinuity at the forward. Rejected because the user explicitly requested smooth blending.

**Alternative considered:** Vega weighting — also smooth but adds complexity without clear benefit over delta weighting for vanilla smile construction.

### 2. Bootstrap the delta weights from call-implied vol

Computing $d_1$ requires a vol, creating a circular dependency. We break it by using the call-implied mid vol $\sigma_C(K)$ for the delta computation. This is well-defined at every strike (we already compute it) and provides a good approximation since the blend is most sensitive near the forward where call and put vols are close.

**Alternative considered:** Use a flat ATM vol for all delta weights. Simpler but less accurate in the wings where skew shifts the effective delta.

### 3. New method name: `to_smile_data_blended()`

A new method `to_smile_data_blended()` on `OptionChain` returns `SmileData` in `(FixedStrike, Volatility)` coordinates. This keeps the existing `to_smile_data()` unchanged (returns Price-coordinate call data).

**Alternative considered:** Adding a `blended=False` parameter to `to_smile_data()`. Rejected because the two methods return different Y-coordinate types (Price vs Volatility), which would be confusing with a flag.

### 4. Bid/ask blending

Bid and ask vols are blended independently using the same delta weights (computed from mid vol). This ensures the output spread reflects the actual market spread at each strike, weighted by the option type that dominates.

### 5. Implementation location

The blending logic lives in `OptionChain` (in `prices.py`) because it needs access to both call and put prices, which only `OptionChain` holds. The implied vol inversion uses the existing `black76_implied_vol` function.

## Risks / Trade-offs

- **[Implied vol inversion failure for deep ITM options]** → Deep ITM prices may be below intrinsic (after calibration adjustments) causing `black76_implied_vol` to raise. Mitigation: the `denoise()` method already removes sub-intrinsic quotes; document that `denoise()` should be called first, or handle inversion failures gracefully by falling back to the other option type's vol at that strike.
- **[Performance]** → Two implied vol inversions per strike instead of one. Mitigation: for typical chain sizes (50-200 strikes) the overhead is negligible (< 100ms). No change to the hot fitting path.
- **[Circular vol dependency for delta]** → Using call-implied vol for delta weights is an approximation. The error is small and confined to strikes near the forward where call and put vols are close anyway.
