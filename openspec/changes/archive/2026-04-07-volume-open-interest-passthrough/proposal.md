## Why

Market volume and open interest are essential context for assessing data quality and liquidity when fitting volatility smiles. Currently, `OptionChain` discards this information, so downstream consumers (filtering, fitting, visualization) cannot use it for liquidity-weighted fitting, filtering illiquid strikes, or diagnostic plots. Adding optional passthrough avoids lossy conversions and lets users carry exchange-provided liquidity signals through the entire pipeline.

## What Changes

- Add optional `volume` and `open_interest` per-strike arrays to `OptionChain`
- Add optional `volume` and `open_interest` per-point arrays to `SmileData`
- Propagate these arrays through `OptionChain.to_smile_data()`, `to_smile_data_blended()`, and `denoise()`
- Carry arrays through `SmileData.transform()` (passthrough — re-indexed when strikes are filtered but values unchanged)
- Ensure the fitting stack (`fit()`) preserves them on input `SmileData` but does not use them in the objective (no behavioural change to fitting)

## Capabilities

### New Capabilities

_(none)_

### Modified Capabilities

- `option-chain`: Add optional `volume` and `open_interest` array fields with validation
- `option-chain-prices`: Pass `volume`/`open_interest` through `to_smile_data()` and `to_smile_data_blended()` conversions
- `smile-data`: Add optional `volume` and `open_interest` array fields, propagate through `transform()`

## Impact

- **Code**: `src/qsmile/data/prices.py` (OptionChain), `src/qsmile/data/vols.py` (SmileData)
- **APIs**: New optional keyword arguments on `OptionChain` and `SmileData` constructors — fully backward-compatible
- **Dependencies**: None — uses existing NumPy arrays
- **Tests**: New test cases for passthrough, filtering, and transform propagation; existing tests unaffected (fields default to `None`)
