# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo==0.18.4",
#     "numpy>=1.24.0",
#     "plotly>=5.18.0",
#     "pandas>=2.0.0",
#     "scipy>=1.14.0",
#     "qsmile",
# ]
#
# [tool.uv.sources.qsmile]
# path = "../../.."
# editable = true
# ///

import marimo

__generated_with = "0.21.1"
app = marimo.App(width="medium")

with app.setup:
    import marimo as mo
    import numpy as np
    import pandas as pd
    import plotly.graph_objects as go

    from qsmile import OptionChain, SVIParams, fit_svi, svi_implied_vol


@app.cell(hide_code=True)
def cell_02():
    """Render the notebook introduction."""
    mo.md(
        r"""
        # Volatility Smile Modelling with qsmile

        This notebook demonstrates **qsmile**, a library for fitting parametric
        volatility smile models to option chain data.

        We'll walk through the core workflow:
        1. Construct an `OptionChain` from market data
        2. Fit the **SVI** (Stochastic Volatility Inspired) model
        3. Inspect fit quality and explore parameter sensitivity

        The SVI raw parameterisation models total implied variance as:

        $$w(k) = a + b\left(\rho(k - m) + \sqrt{(k - m)^2 + \sigma^2}\right)$$

        where $k = \ln(K/F)$ is log-moneyness.
        """
    )
    return


@app.cell(hide_code=True)
def cell_04():
    """Introduce the market data section."""
    mo.md(
        r"""
        ## Market Data

        We'll start with a synthetic option chain that exhibits a realistic skew —
        lower strikes (puts) have higher implied volatility than higher strikes (calls).
        """
    )
    return


@app.cell(hide_code=True)
def cell_05():
    """Create synthetic market data with realistic skew."""
    # Synthetic market data with realistic equity skew
    forward = 100.0
    expiry = 0.5  # 6 months

    strikes = np.array([80, 85, 90, 95, 100, 105, 110, 115, 120])
    # Generated from SVI(a=0.008, b=0.08, rho=-0.6, m=-0.02, sigma=0.10), rounded to 4dp
    ivs = np.array([0.2678, 0.2399, 0.2127, 0.1891, 0.1743, 0.1698, 0.1713, 0.1756, 0.1808])

    chain = OptionChain(strikes=strikes, ivs=ivs, forward=forward, expiry=expiry)
    return chain, expiry, ivs, strikes


@app.cell(hide_code=True)
def cell_06(chain, ivs, strikes):
    """Display the option chain as an interactive table."""
    df = pd.DataFrame(
        {
            "Strike": strikes,
            "IV (%)": (ivs * 100).round(1),
            "Log-Moneyness": chain.log_moneyness.round(4),
            "Total Variance": chain.total_variance.round(6),
        }
    )
    mo.vstack([mo.md("### Option Chain Data"), mo.ui.table(df)])
    return


@app.cell(hide_code=True)
def cell_07():
    """Render a section divider."""
    mo.md(r"""---""")
    return


@app.cell(hide_code=True)
def cell_08():
    """Introduce the SVI fitting section."""
    mo.md(
        r"""
        ## SVI Fitting

        We fit the SVI raw parameterisation to the market data using
        `fit_svi`, which minimises the sum of squared residuals in
        total-variance space via `scipy.optimize.least_squares`.
        """
    )
    return


@app.cell(hide_code=True)
def cell_09(chain):
    """Fit SVI to the option chain and display results."""
    result = fit_svi(chain)
    p = result.params

    mo.vstack(
        [
            mo.md("### Fitted SVI Parameters"),
            mo.md(
                f"""
    | Parameter | Value | Description |
    |-----------|-------|-------------|
    | $a$ | {p.a:.6f} | Vertical translation |
    | $b$ | {p.b:.6f} | Wing slope |
    | $\\rho$ | {p.rho:.6f} | Skew (correlation) |
    | $m$ | {p.m:.6f} | Horizontal shift |
    | $\\sigma$ | {p.sigma:.6f} | ATM curvature |

    **RMSE:** {result.rmse:.2e} &nbsp;&nbsp; **Converged:** {"Yes" if result.success else "No"}
    """
            ),
        ]
    )
    return p, result


@app.cell(hide_code=True)
def cell_10(chain, expiry, result):
    """Plot market data vs fitted SVI smile."""
    _k_market = chain.log_moneyness
    k_fine = np.linspace(_k_market.min() - 0.05, _k_market.max() + 0.05, 200)
    iv_fitted = svi_implied_vol(k_fine, result.params, expiry)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=_k_market,
            y=chain.ivs * 100,
            mode="markers",
            marker={"size": 10, "color": "#E74C3C"},
            name="Market",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=k_fine,
            y=iv_fitted * 100,
            mode="lines",
            line={"color": "#2FA4A9", "width": 2.5},
            name="SVI Fit",
        )
    )
    fig.update_layout(
        title="Implied Volatility Smile: Market vs SVI Fit",
        xaxis_title="Log-Moneyness  k = ln(K/F)",
        yaxis_title="Implied Volatility (%)",
        template="plotly_white",
        height=450,
        legend={"x": 0.02, "y": 0.98},
    )
    mo.ui.plotly(fig)
    return iv_fitted, k_fine


@app.cell(hide_code=True)
def cell_11(chain, result):
    """Plot fit residuals."""
    _k_market = chain.log_moneyness

    fig_resid = go.Figure()
    fig_resid.add_trace(
        go.Bar(
            x=_k_market,
            y=result.residuals * 1e4,
            marker_color="#2FA4A9",
            name="Residual",
        )
    )
    fig_resid.add_hline(y=0, line_dash="dash", line_color="grey")
    fig_resid.update_layout(
        title="Fit Residuals (Total Variance × 10⁴)",
        xaxis_title="Log-Moneyness",
        yaxis_title="Residual (bps of total var)",
        template="plotly_white",
        height=350,
        showlegend=False,
    )
    mo.ui.plotly(fig_resid)
    return


@app.cell(hide_code=True)
def cell_13():
    """Introduce the parameter explorer section."""
    mo.md(
        r"""
        ## Parameter Explorer

        Use the sliders below to see how each SVI parameter shapes the smile.
        The **blue** curve is the fitted smile from above; the **orange** curve
        shows the effect of your parameter changes.
        """
    )
    return


@app.cell(hide_code=True)
def cell_14(p):
    """Create sliders for SVI parameters."""
    sl_a = mo.ui.slider(start=-1.0, stop=1.0, value=round(p.a, 4), step=0.005, label="a (level):", show_value=True)
    sl_b = mo.ui.slider(start=0.01, stop=2.0, value=round(p.b, 4), step=0.01, label="b (wings):", show_value=True)
    sl_rho = mo.ui.slider(start=-0.99, stop=0.99, value=round(p.rho, 4), step=0.01, label="ρ (skew):", show_value=True)
    sl_m = mo.ui.slider(start=-1.0, stop=1.0, value=round(p.m, 4), step=0.01, label="m (shift):", show_value=True)
    sl_sigma = mo.ui.slider(
        start=0.01, stop=2.0, value=round(p.sigma, 4), step=0.01, label="σ (curvature):", show_value=True
    )
    mo.vstack([sl_a, sl_b, sl_rho, sl_m, sl_sigma])
    return sl_a, sl_b, sl_m, sl_rho, sl_sigma


@app.cell(hide_code=True)
def cell_15(expiry, iv_fitted, k_fine, sl_a, sl_b, sl_m, sl_rho, sl_sigma):
    """Plot fitted vs explorer smile side by side."""
    explorer_params = SVIParams(a=sl_a.value, b=sl_b.value, rho=sl_rho.value, m=sl_m.value, sigma=sl_sigma.value)
    iv_explorer = svi_implied_vol(k_fine, explorer_params, expiry)

    fig_explore = go.Figure()
    fig_explore.add_trace(
        go.Scatter(
            x=k_fine,
            y=iv_fitted * 100,
            mode="lines",
            line={"color": "#2FA4A9", "width": 2, "dash": "dash"},
            name="Fitted",
        )
    )
    fig_explore.add_trace(
        go.Scatter(
            x=k_fine,
            y=iv_explorer * 100,
            mode="lines",
            line={"color": "#E67E22", "width": 2.5},
            name="Explorer",
        )
    )
    fig_explore.update_layout(
        title="SVI Parameter Explorer",
        xaxis_title="Log-Moneyness",
        yaxis_title="Implied Volatility (%)",
        template="plotly_white",
        height=450,
        legend={"x": 0.02, "y": 0.98},
    )
    mo.ui.plotly(fig_explore)
    return


@app.cell(hide_code=True)
def cell_16():
    """Render a section divider."""
    mo.md(r"""---""")
    return


@app.cell(hide_code=True)
def cell_17():
    """Introduce the total variance view section."""
    mo.md(
        r"""
        ## Total Variance View

        Practitioners often work in total-variance space $w(k) = \sigma_{IV}^2 \cdot T$
        because the SVI formula is linear in that domain. Below we plot the fitted
        total variance curve alongside the market observations.
        """
    )
    return


@app.cell(hide_code=True)
def cell_18(chain, k_fine, result):
    """Plot total variance: market vs SVI."""
    w_market = chain.total_variance
    w_fit = result.evaluate(k_fine)

    fig_w = go.Figure()
    fig_w.add_trace(
        go.Scatter(
            x=chain.log_moneyness,
            y=w_market,
            mode="markers",
            marker={"size": 10, "color": "#E74C3C"},
            name="Market",
        )
    )
    fig_w.add_trace(
        go.Scatter(
            x=k_fine,
            y=w_fit,
            mode="lines",
            line={"color": "#2FA4A9", "width": 2.5},
            name="SVI Fit",
        )
    )
    fig_w.update_layout(
        title="Total Implied Variance",
        xaxis_title="Log-Moneyness  k",
        yaxis_title="w(k) = σ² · T",
        template="plotly_white",
        height=400,
        legend={"x": 0.02, "y": 0.98},
    )
    mo.ui.plotly(fig_w)
    return


@app.cell(hide_code=True)
def cell_23():
    """Render the conclusion."""
    mo.md(
        r"""
        ## Summary

        This notebook demonstrated the core **qsmile** workflow:

        - **`OptionChain`** — validated container for strikes, IVs, forward, and expiry
        - **`fit_svi`** — least-squares calibration of the SVI raw parameterisation
        - **`SmileResult`** — fitted parameters, residuals, RMSE, and `evaluate(k)`
        - **`svi_total_variance` / `svi_implied_vol`** — direct model evaluation

        **Next steps** — future versions will add SVI-JW parameterisation,
        multi-expiry surface fitting, and arbitrage-free enforcement.
        """
    )
    return


if __name__ == "__main__":
    app.run()
