# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo==0.18.4",
#     "numpy>=1.24.0",
#     "plotly>=5.18.0",
#     "pandas>=2.0.0",
#     "pyarrow>=17.0.0",
#     "scipy>=1.14.0",
#     "cvxpy>=1.6.0",
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
    from pathlib import Path

    import marimo as mo
    import numpy as np
    import pandas as pd
    import plotly.graph_objects as go

    from qsmile import SVIParams, fit_svi, svi_implied_vol
    from qsmile.core.coords import XCoord, YCoord
    from qsmile.data.prices import OptionChain


@app.cell(hide_code=True)
def cell_02():
    """Render the notebook introduction."""
    mo.md(
        r"""
        # Volatility Smile Modelling with qsmile

        This notebook demonstrates **qsmile**, a library for fitting parametric
        volatility smile models to option chain data.

        We'll walk through the core workflow:
        1. Construct a `SmileData` from mid implied volatilities
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

        We load a real S&P 500 (SPX) option chain from parquet and build
        an `OptionChain` to calibrate a consistent forward and discount
        factor from put-call parity. The resulting implied volatilities are
        then extracted via `to_smile_data()`, giving a clean smile with the
        characteristic equity skew.
        """
    )
    return


@app.cell(hide_code=True)
def cell_05():
    """Load real SPX market data from parquet."""
    _root = Path(__file__).resolve().parent.parent.parent.parent
    _pq = sorted(_root.glob("parquet/chains/*.parquet"))[-1]
    df_raw = pd.read_parquet(_pq)

    expiry = float(df_raw["daysToExpiry"].iloc[0]) / 365.0

    # Merge calls/puts on common strikes
    _cols = ["strike", "bid", "ask"]
    calls = df_raw[df_raw["optionType"] == "call"][_cols].set_index("strike")
    puts = df_raw[df_raw["optionType"] == "put"][_cols].set_index("strike")
    merged = calls.join(puts, lsuffix="_c", rsuffix="_p", how="inner").sort_index()

    # Build OptionChain → denoise → calibrate F, DF → extract vols
    _strikes = merged.index.values.astype(np.float64)
    raw_prices = OptionChain(
        strikes=_strikes,
        call_bid=merged["bid_c"].values.astype(np.float64),
        call_ask=merged["ask_c"].values.astype(np.float64),
        put_bid=merged["bid_p"].values.astype(np.float64),
        put_ask=merged["ask_p"].values.astype(np.float64),
        expiry=expiry,
    )
    prices = raw_prices.denoise()

    # Convert to SmileData in vol coordinates (consistent F and DF)
    sd = prices.to_smile_data().transform(XCoord.FixedStrike, YCoord.Volatility)
    strikes = sd.x
    ivs = sd.y_mid
    return expiry, ivs, sd, strikes


@app.cell(hide_code=True)
def cell_06(ivs, sd, strikes):
    """Display the option chain as an interactive table."""
    _sd_lm = sd.transform(XCoord.LogMoneynessStrike, YCoord.TotalVariance)
    df = pd.DataFrame(
        {
            "Strike": strikes,
            "IV (%)": (ivs * 100).round(1),
            "Log-Moneyness": _sd_lm.x.round(4),
            "Total Variance": _sd_lm.y_mid.round(6),
        }
    )
    mo.vstack([mo.md("### Option Chain Data"), df])
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
def cell_09(sd):
    """Fit SVI to the SmileData and display results."""
    result = fit_svi(sd)
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
def cell_10(expiry, result, sd):
    """Plot market data vs fitted SVI smile."""
    _sd_lm = sd.transform(XCoord.LogMoneynessStrike, YCoord.Volatility)
    _k_market = _sd_lm.x
    k_fine = np.linspace(_k_market.min() - 0.05, _k_market.max() + 0.05, 200)
    iv_fitted = svi_implied_vol(k_fine, result.params, expiry)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=_k_market,
            y=_sd_lm.y_mid * 100,
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
def cell_11(result, sd):
    """Plot fit residuals."""
    _sd_lm = sd.transform(XCoord.LogMoneynessStrike, YCoord.Volatility)
    _k_market = _sd_lm.x

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
    # Ranges are data-adaptive: centred on the fitted value with room to explore
    sl_a = mo.ui.slider(
        start=min(-1.0, p.a * 3),
        stop=max(1.0, p.a * 3),
        value=round(p.a, 4),
        step=0.005,
        label="a (level):",
        show_value=True,
    )
    sl_b = mo.ui.slider(
        start=0.001,
        stop=max(2.0, p.b * 2),
        value=round(p.b, 4),
        step=max(0.01, p.b * 0.01),
        label="b (wings):",
        show_value=True,
    )
    sl_rho = mo.ui.slider(
        start=-0.999,
        stop=0.999,
        value=round(min(max(p.rho, -0.999), 0.999), 4),
        step=0.001,
        label="\u03c1 (skew):",
        show_value=True,
    )
    sl_m = mo.ui.slider(
        start=min(-1.0, p.m * 3),
        stop=max(1.0, p.m * 3),
        value=round(p.m, 4),
        step=0.01,
        label="m (shift):",
        show_value=True,
    )
    sl_sigma = mo.ui.slider(
        start=min(0.001, p.sigma / 2),
        stop=max(2.0, p.sigma * 4),
        value=round(p.sigma, 4),
        step=max(0.001, p.sigma * 0.05),
        label="\u03c3 (curvature):",
        show_value=True,
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
def cell_18(k_fine, result, sd):
    """Plot total variance: market vs SVI."""
    _sd_lm = sd.transform(XCoord.LogMoneynessStrike, YCoord.TotalVariance)
    _w_market = _sd_lm.y_mid
    _w_fit = result.evaluate(k_fine)

    fig_w = go.Figure()
    fig_w.add_trace(
        go.Scatter(
            x=_sd_lm.x,
            y=_w_market,
            mode="markers",
            marker={"size": 10, "color": "#E74C3C"},
            name="Market",
        )
    )
    fig_w.add_trace(
        go.Scatter(
            x=k_fine,
            y=_w_fit,
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

        This notebook demonstrated the core **qsmile** SVI fitting workflow:

        - **`SmileData.from_mid_vols`** — construct a validated smile container from mid IVs
        - **`fit_svi`** — least-squares calibration of the SVI raw parameterisation
        - **`SmileResult`** — fitted parameters, residuals, RMSE, and `evaluate(k)`
        - **`svi_total_variance` / `svi_implied_vol`** — direct model evaluation

        ### Full Option Chain Pipeline

        For a complete bid/ask workflow starting from raw option prices, see the
        **Chain Demo** notebook which walks through:

        1. `OptionChain` — bid/ask prices with auto-calibrated forward & discount factor
        2. `SmileData` — unified container with **coordinate transforms** between
           any combination of X-coords (Strike, Moneyness, Log-Moneyness, Standardised)
           and Y-coords (Price, Volatility, Variance, Total Variance)
        3. `fit_svi(sd)` — SVI fit directly from a `SmileData`

        **Next steps** — future versions will add SVI-JW parameterisation,
        multi-expiry surface fitting, and arbitrage-free enforcement.
        """
    )
    return


if __name__ == "__main__":
    app.run()
