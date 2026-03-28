## Why

The current `OptionChain` only stores mid implied volatilities, ignoring the bid/ask spread that is fundamental in options markets. Real market data arrives as option prices (not vols), and users need to convert between price and vol space, calibrate forwards and discount factors from the market when not provided, and work in unitised (normalised) coordinates for robust fitting. This change introduces a richer set of representations that mirror the real quant workflow: prices → vols → unitised space.

## What Changes

- Introduce `OptionChainPrices` to hold bid/ask call and put prices per strike, with optional user-supplied forward and discount factor.
- When forward and discount factor are not provided, fit them from put-call parity using a least-squares optimisation with a "delta blend" weighting scheme that tilts towards ATM strikes.
- Introduce `OptionChainVols` to hold bid/ask implied volatilities per strike, converted from prices via Black76.
- Introduce `UnitisedSpaceVols` to represent the smile in normalised coordinates: $k = \log(K/F) / (\sigma_{\text{ATM}} \sqrt{t})$ and $v = \sigma_k^2 \, t$.
- Each of the three classes exposes a `.plot()` method that renders bid/ask as error bars.
- Add a Black76 pricing module for forward ↔ vol conversion (call/put prices given forward, strike, discount factor, vol, time to expiry).
- Switch optimisation backend to `cvxpy` (replacing `scipy.optimize` for new fitting work).

## Capabilities

### New Capabilities
- `option-chain-prices`: Bid/ask option price container with forward/DF calibration via put-call parity delta-blend least-squares.
- `option-chain-vols`: Bid/ask implied volatility container derived from prices via Black76 inversion.
- `unitised-space-vols`: Normalised coordinate vol surface representation ($k$, $v$ unitised space).
- `black76`: Black76 forward option pricing and implied vol inversion.
- `plotting`: `.plot()` methods for each chain representation showing bid/ask as error bars.

### Modified Capabilities
- `option-chain`: The existing `OptionChain` spec is not directly modified, but the new classes supersede its role for market data workflows that start from prices.

## Impact

- **New source files**: `black76.py`, `prices.py`, `vols.py`, `unitised.py`, `plot.py` (or similar) under `src/qsmile/`.
- **New dependency**: `cvxpy` added to `pyproject.toml` project dependencies. `matplotlib` added for plotting.
- **Existing code**: The current `OptionChain`, `SVIParams`, and `fit_svi` remain unchanged. New classes compose with them rather than replacing them.
- **Public API**: New classes and functions will be exported from `qsmile.__init__`.
