<div align="center">

# qsmile

### Quantitative Smile Modelling

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python versions](https://img.shields.io/badge/Python-3.11%20•%203.12%20•%203.13-blue?logo=python)](https://www.python.org/)

![Github](https://img.shields.io/badge/GitHub-181717?style=flat&logo=github)
![Linux](https://img.shields.io/badge/Linux-FCC624?style=flat&logo=linux&logoColor=white)
![macOS](https://img.shields.io/badge/macOS-000000?style=flat&logo=apple&logoColor=white)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg?logo=ruff)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Hatch project](https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg)](https://github.com/pypa/hatch)

[![CI](https://github.com/markrichardson/qsmile/actions/workflows/rhiza_ci.yml/badge.svg?event=push)](https://github.com/markrichardson/qsmile/actions/workflows/rhiza_ci.yml)
[![PRE-COMMIT](https://github.com/markrichardson/qsmile/actions/workflows/rhiza_pre-commit.yml/badge.svg?event=push)](https://github.com/markrichardson/qsmile/actions/workflows/rhiza_pre-commit.yml)
[![DEPTRY](https://github.com/markrichardson/qsmile/actions/workflows/rhiza_deptry.yml/badge.svg?event=push)](https://github.com/markrichardson/qsmile/actions/workflows/rhiza_deptry.yml)
[![MARIMO](https://github.com/markrichardson/qsmile/actions/workflows/rhiza_marimo.yml/badge.svg?event=push)](https://github.com/markrichardson/qsmile/actions/workflows/rhiza_marimo.yml)

**Volatility smile fitting for quantitative finance**

</div>

---

## Overview

**qsmile** is a Python library for fitting parametric volatility smile models to option chain data. It provides bid/ask-aware data containers, Black76 pricing, forward/discount-factor calibration, and least-squares SVI calibration out of the box.

### Key capabilities

- **Bid/ask option prices** — `OptionChain` stores bid/ask call and put prices, and automatically calibrates the forward and discount factor from put-call parity using quasi-delta weighted least squares.
- **Coordinate transforms** — `SmileData` is a unified container with `.transform(x, y)` to freely convert between any combination of X-coordinates (Strike, Moneyness, Log-Moneyness, Standardised) and Y-coordinates (Price, Volatility, Variance, Total Variance) via composable, invertible maps.
- **SVI fitting** — Fit the SVI raw parameterisation to `SmileData`:

$$w(k) = a + b\left(\rho(k - m) + \sqrt{(k - m)^2 + \sigma^2}\right)$$

where $k = \ln(K/F)$ is log-moneyness and $w$ is total implied variance.

- **Black76 pricing** — Vectorised call/put pricing and implied vol inversion via `black76_call`, `black76_put`, and `black76_implied_vol`.
- **Plotting** — All chain types have a `.plot()` method for bid/ask error-bar charts (requires `qsmile[plot]`).

---

## Installation

```bash
pip install qsmile            # core
pip install "qsmile[plot]"    # with matplotlib plotting
```

For development:

```bash
git clone https://github.com/markrichardson/qsmile.git
cd qsmile
make install
```

---

## Quick Start

### From bid/ask prices (full pipeline)

```python +RHIZA_SKIP
import numpy as np
import pandas as pd
from qsmile import OptionChain, SmileData, SmileMetadata, SVIModel, XCoord, YCoord, fit

# Bid/ask prices — forward and DF are calibrated automatically
prices = OptionChain(
    strikes=np.array([80, 90, 95, 100, 105, 110, 120], dtype=float),
    call_bid=np.array([20.5, 11.8, 7.5, 4.2, 2.0, 0.8, 0.1]),
    call_ask=np.array([21.5, 12.4, 8.0, 4.6, 2.3, 1.0, 0.2]),
    put_bid=np.array([0.1, 0.6, 1.5, 3.1, 5.8, 9.6, 18.8]),
    put_ask=np.array([0.2, 0.8, 1.8, 3.5, 6.2, 10.2, 19.6]),
    metadata=SmileMetadata(date=pd.Timestamp("2024-01-01"), expiry=pd.Timestamp("2024-07-01")),
)
print(prices.metadata.forward)          # Calibrated forward
print(prices.metadata.discount_factor)  # Calibrated discount factor

# Enter the coordinate transform framework
sd = prices.to_smile_data()                               # (FixedStrike, Volatility)
sd_unit = sd.transform(XCoord.StandardisedStrike, YCoord.TotalVariance)  # → unitised

# Fit SVI directly from SmileData
result = fit(sd, model=SVIModel)
print(result.params)   # Fitted SVIModel
print(result.rmse)     # Root mean square error
```

### From mid implied vols

```python +RHIZA_SKIP
import numpy as np
import pandas as pd
from qsmile import SmileData, SVIModel, fit

sd = SmileData.from_mid_vols(
    strikes=np.array([80, 90, 100, 110, 120], dtype=float),
    ivs=np.array([0.28, 0.22, 0.18, 0.17, 0.19]),
    forward=100.0,
    date=pd.Timestamp("2024-01-01"),
    expiry=pd.Timestamp("2024-07-01"),
)

result = fit(sd, model=SVIModel)
print(result.params)   # Fitted SVIModel
print(result.rmse)     # Root mean square error
```

---

## API Reference

### Data containers

| Class | Description |
|---|---|
| `OptionChain` | Bid/ask call and put prices with automatic forward/DF calibration |
| `SmileData` | Unified coordinate-labelled container with `.transform(x, y)` and `.from_mid_vols()` factory |

### Coordinate transforms

```
OptionChain ─── .to_smile_data() ──→ SmileData ─── .transform(x, y) ──→ SmileData
SmileData.from_mid_vols(...)            ──→ SmileData ───────────────────────────┘
```

| Coordinate type | Values |
|---|---|
| X-coordinates | `FixedStrike`, `MoneynessStrike`, `LogMoneynessStrike`, `StandardisedStrike` |
| Y-coordinates | `Price`, `Volatility`, `Variance`, `TotalVariance` |

### Smile fitting

| Function / Class | Description |
|---|---|
| `fit(chain, model)` | Fit any `SmileModel` to `SmileData` — generic entry point |
| `SmileModel` | Protocol for pluggable smile models (native coords, bounds, evaluate, etc.) |
| `AbstractSmileModel` | Abstract base dataclass with default `to_array()`/`from_array()` derived from `param_names` |
| `SmileResult` | Fitted result with `.params`, `.residuals`, `.rmse`, `.success`, `.evaluate(x)` |
| `SVIModel` | SVI model and parameter values `(a, b, rho, m, sigma)` with `.evaluate(k)` and `.implied_vol(k, T)` |
| `SABRModel` | SABR model `(alpha, beta, rho, nu)` with Hagan (2002) lognormal implied vol `.evaluate(k)` |

### Black76 pricing

| Function | Description |
|---|---|
| `black76_call(F, K, D, σ, T)` | Vectorised Black76 call price |
| `black76_put(F, K, D, σ, T)` | Vectorised Black76 put price |
| `black76_implied_vol(price, F, K, D, T)` | Implied vol inversion via Brent's method |

---

## Development

```bash
make install   # Set up environment
make test      # Run tests with coverage
make fmt       # Format and lint
make marimo    # Launch interactive notebooks
```

---

## License

MIT — see [LICENSE](LICENSE) for details.

