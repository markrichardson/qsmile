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

**qsmile** is a Python library for fitting parametric volatility smile models to option chain data. It provides validated data containers, model evaluation, and least-squares calibration out of the box.

The current implementation supports the **SVI** (Stochastic Volatility Inspired) raw parameterisation:

$$w(k) = a + b\left(\rho(k - m) + \sqrt{(k - m)^2 + \sigma^2}\right)$$

where $k = \ln(K/F)$ is log-moneyness and $w$ is total implied variance.

> **Note**: The API is under active development and will change significantly in upcoming releases.

---

## Installation

```bash
pip install qsmile
```

For development:

```bash
git clone https://github.com/markrichardson/qsmile.git
cd qsmile
make install
```

---

## Quick Start

```python +RHIZA_SKIP
import numpy as np
from qsmile import OptionChain, fit_svi

# Market data
chain = OptionChain(
    strikes=np.array([80, 90, 100, 110, 120], dtype=float),
    ivs=np.array([0.28, 0.22, 0.18, 0.17, 0.19]),
    forward=100.0,
    expiry=0.5,
)

# Fit SVI
result = fit_svi(chain)
print(result.params)   # Fitted SVIParams
print(result.rmse)     # Root mean square error
```

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

