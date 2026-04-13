# qsmile

**Volatility smile fitting for quantitative finance**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/markrichardson/qsmile/blob/main/LICENSE)
[![Python versions](https://img.shields.io/badge/Python-3.11%20•%203.12%20•%203.13-blue?logo=python)](https://www.python.org/)
[![CI](https://github.com/markrichardson/qsmile/actions/workflows/rhiza_ci.yml/badge.svg?event=push)](https://github.com/markrichardson/qsmile/actions/workflows/rhiza_ci.yml)

---

**qsmile** is a Python library for fitting parametric volatility smile models to option chain data. It provides bid/ask-aware data containers, Black76 pricing, forward/discount-factor calibration, and least-squares SVI calibration out of the box.

## Features

- **Bid/ask option prices** — `OptionChain` stores bid/ask call and put prices, and automatically calibrates the forward and discount factor from put-call parity using quasi-delta weighted least squares.
- **Coordinate transforms** — `SmileData` is a unified container with `.transform(x, y)` to freely convert between any combination of X-coordinates (Strike, Moneyness, Log-Moneyness, Standardised) and Y-coordinates (Price, Volatility, Variance, Total Variance) via composable, invertible maps.
- **SVI fitting** — Fit the SVI raw parameterisation to `SmileData`:

$$w(k) = a + b\left(\rho(k - m) + \sqrt{(k - m)^2 + \sigma^2}\right)$$

where $k = \ln(K/F)$ is log-moneyness and $w$ is total implied variance.

- **SABR model** — Fit the SABR stochastic volatility model.
- **Black76 pricing** — Vectorised call/put pricing and implied vol inversion via `black76_call`, `black76_put`, and `black76_implied_vol`.
- **Plotting** — All chain types have a `.plot()` method for bid/ask error-bar charts (requires `qsmile[plot]`).

## Quick Example

```python
import numpy as np
import pandas as pd
from qsmile import SmileData, SmileMetadata, SVIModel, fit

meta = SmileMetadata(
    date=pd.Timestamp("2024-01-01"),
    expiry=pd.Timestamp("2024-07-01"),
    forward=100.0,
)

sd = SmileData.from_mid_vols(
    strikes=np.array([80, 90, 100, 110, 120], dtype=float),
    ivs=np.array([0.28, 0.22, 0.18, 0.17, 0.19]),
    metadata=meta,
)

result = fit(sd, model=SVIModel)
print(result.params)   # Fitted SVIModel
print(result.rmse)     # Root mean square error
```

## Getting Started

Install with pip:

```bash
pip install qsmile            # core
pip install "qsmile[plot]"    # with matplotlib plotting
```

Explore the [API Reference](api.md) for full documentation, or try the interactive [Marimo Notebooks](notebooks.md).

