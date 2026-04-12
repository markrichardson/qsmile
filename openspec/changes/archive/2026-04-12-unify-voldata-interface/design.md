## Context

`SmileModel` and `VolData` both represent volatility smiles with coordinate awareness, but their internal patterns diverge:

| Aspect | SmileModel | VolData (current) |
|--------|-----------|-------------------|
| Data storage | Native coords only (parametric) | Whatever coords it was constructed/transformed to |
| `transform()` | Lightweight — just relabels `current_x_coord`/`current_y_coord` | Heavyweight — physically transforms all arrays |
| Coord fields | `current_x_coord`, `current_y_coord` | `x_coord`, `y_coord` |
| `evaluate(x)` | Yes (via `_evaluate` + coord chain) | No |
| `plot()` | Uses `std_range`, `n_points` for domain | Plots whatever x range the data covers |

The existing `SmileModel` pattern is cleaner: store data in one canonical form, present it in whatever coordinates are requested. `VolData` should follow the same pattern.

## Goals / Non-Goals

**Goals:**
- Unify the public interface of `VolData` and `SmileModel` so both can be used polymorphically.
- `VolData.transform()` becomes lightweight (just relabels), matching `SmileModel.transform()`.
- `VolData` exposes `evaluate(x)` for mid-curve interpolation at arbitrary points.
- Field names align: `current_x_coord`, `current_y_coord`, `native_x_coord`, `native_y_coord`.

**Non-Goals:**
- Creating a formal protocol/ABC that both types inherit from (can be done later).
- Changing `SmileModel` internals — it's already the target pattern.
- Adding fitting or calibration methods to `VolData`.
- Changing the `StrikeArray` data structure itself.

## Decisions

### 1. Lazy transform via native storage

**Decision**: `VolData` stores data in its original ("native") coordinates. `transform()` returns a shallow copy with updated `current_x_coord`/`current_y_coord`. Property accessors (`x`, `y_bid`, `y_ask`, `y_mid`) apply coordinate transforms on access.

**Rationale**: This mirrors `SmileModel` exactly. Chained transforms (`data.transform(A, B).transform(C, D)`) compose cleanly without repeated array allocation. The native data is never mutated.

**Alternative considered**: Keep eager transform but rename fields. Rejected because it leaves the fundamental interface asymmetry in place.

### 2. Interpolation strategy for evaluate()

**Decision**: `evaluate(x)` uses `scipy.interpolate.CubicSpline` on `y_mid` in current coordinates. It returns `NaN` outside the data domain (no extrapolation).

**Rationale**: Cubic spline is smooth and standard. No-extrapolation is safer than linear/flat extrapolation for market data. Users who want extrapolation can fit a model.

**Alternative considered**: Linear interpolation — simpler but produces kinked vol surfaces. Rejected.

### 3. Field renaming approach

**Decision**: Rename `x_coord` → `current_x_coord`, `y_coord` → `current_y_coord` in the dataclass. Add `native_x_coord` and `native_y_coord` as read-only properties derived from the stored native data. Construction sets both native and current to the same values.

**Rationale**: Direct alignment with `SmileModel` field names. `native_*` as properties rather than stored fields avoids redundancy since native coords never change after construction.

## Risks / Trade-offs

- **[Performance]** Lazy transforms mean every `.x`, `.y_bid` access re-runs the transform chain. → Mitigated by memoisation / caching on `(current_x_coord, current_y_coord)` if profiling shows it matters. Transform chains are cheap (a few NumPy vectorised ops on ~50 points).
- **[Breaking change]** Renaming `x_coord`/`y_coord` breaks all downstream code. → Accept as a clean break. Use find-and-replace across tests and notebooks. The rename is mechanical.
- **[Interpolation edge cases]** `evaluate()` on very sparse data (3 points) may produce cubic oscillation. → Acceptable; VolData already requires ≥3 points, and users should fit a model for production use.
