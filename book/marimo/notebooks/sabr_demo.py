# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo==0.18.4",
#     "numpy>=1.24.0",
#     "plotly>=5.18.0",
#     "pandas>=2.0.0",
#     "pyarrow>=17.0.0",
#     "scipy>=1.14.0",
#     "qsmile[plot]",
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
    from plotly.subplots import make_subplots

    from qsmile import (
        OptionChain,
        SABRModel,
        SVIModel,
        XCoord,
        YCoord,
        fit,
    )


@app.cell(hide_code=True)
def cell_intro():
    """Render the notebook introduction."""
    mo.md(
        r"""
        # SABR Model Demo

        This notebook demonstrates the **SABR** (Stochastic Alpha Beta Rho)
        model implemented in qsmile using the Hagan et al. (2002) lognormal
        implied volatility approximation.

        The SABR model describes the joint dynamics of a forward price $F$
        and its stochastic volatility $\alpha$:

        $$
        \begin{aligned}
        dF &= \alpha\, F^\beta\, dW_1 \\
        d\alpha &= \nu\, \alpha\, dW_2 \\
        \langle dW_1, dW_2 \rangle &= \rho\, dt
        \end{aligned}
        $$

        We cover:
        1. **Synthetic exploration** — how each parameter shapes the smile
        2. **Fitting to real SPX data** — `fit(sd, SABRModel)` end-to-end
        3. **Comparison with SVI** — overlay both fitted smiles
        """
    )
    return


# ---------------------------------------------------------------------------
# Part 1 — Parameter exploration
# ---------------------------------------------------------------------------


@app.cell(hide_code=True)
def cell_explore_intro():
    """Introduce parameter exploration."""
    mo.md(
        r"""
        ---
        ## 1. Parameter Exploration

        Explore how each SABR parameter affects the implied volatility smile.
        A reference model is shown alongside a varied parameter.

        | Parameter | Meaning | Range |
        |-----------|---------|-------|
        | $\alpha$ | Initial volatility level | $> 0$ |
        | $\beta$ | CEV exponent (backbone) | $[0, 1]$ |
        | $\rho$ | Fwd–vol correlation (skew) | $(-1, 1)$ |
        | $\nu$ | Vol-of-vol (smile curvature) | $\geq 0$ |
        """
    )
    return


@app.cell
def cell_reference_model():
    """Define reference SABR parameters and log-moneyness grid."""
    k_grid = np.linspace(-0.3, 0.3, 200)

    ref = SABRModel(alpha=0.2, beta=0.5, rho=-0.25, nu=0.4, expiry=1.0, forward=100.0)
    ref_iv = ref.evaluate(k_grid)
    return k_grid, ref, ref_iv


@app.cell(hide_code=True)
def cell_param_plots(k_grid, ref, ref_iv):
    """Plot the effect of varying each SABR parameter."""
    param_configs = [
        ("alpha", [0.10, 0.20, 0.35], "α — volatility level"),
        ("rho", [-0.6, -0.25, 0.1], "ρ — skew"),
        ("nu", [0.1, 0.4, 0.8], "ν — vol-of-vol (curvature)"),
        ("beta", [0.0, 0.5, 1.0], "β — CEV backbone"),
    ]
    colors = ["#2196F3", "#E74C3C", "#2FA4A9"]

    _fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=[c[2] for c in param_configs],
    )

    for idx, (param, values, _title) in enumerate(param_configs):
        row, col = divmod(idx, 2)
        for i, val in enumerate(values):
            kwargs = {
                "alpha": ref.alpha,
                "beta": ref.beta,
                "rho": ref.rho,
                "nu": ref.nu,
                "expiry": ref.expiry,
                "forward": ref.forward,
            }
            kwargs[param] = val
            m = SABRModel(**kwargs)
            iv = m.evaluate(k_grid)
            _fig.add_trace(
                go.Scatter(
                    x=k_grid,
                    y=np.asarray(iv) * 100,
                    mode="lines",
                    line={"color": colors[i], "width": 2},
                    name=f"{param}={val}",
                    showlegend=True,
                    legendgroup=param,
                ),
                row=row + 1,
                col=col + 1,
            )
        _fig.update_xaxes(title_text="log-moneyness k", row=row + 1, col=col + 1)
        _fig.update_yaxes(title_text="IV (%)", row=row + 1, col=col + 1)

    _fig.update_layout(
        title="SABR Parameter Sensitivity",
        template="plotly_white",
        height=700,
        legend={"x": 1.02, "y": 1.0},
    )
    mo.ui.plotly(_fig)
    return


# ---------------------------------------------------------------------------
# Part 2 — Fit SABR to real SPX data
# ---------------------------------------------------------------------------


@app.cell(hide_code=True)
def cell_fit_intro():
    """Introduce the fitting section."""
    mo.md(
        r"""
        ---
        ## 2. Fit SABR to Real SPX Data

        We load the same real SPX option chain used in the chain demo,
        build a `SmileData` container, and calibrate SABR via
        `fit(sd, SABRModel)`.

        The fitting engine automatically:
        - transforms to SABR's native coordinates (log-moneyness, implied vol)
        - passes `expiry` and `forward` context from `SmileData.metadata`
        - runs least-squares optimisation with Hagan's formula
        """
    )
    return


@app.cell
def cell_load_data():
    """Load real SPX option chain and build SmileData."""
    _root = Path(__file__).resolve().parent.parent.parent.parent
    _pq = sorted(_root.glob("parquet/chains/*.parquet"))[-1]
    df_raw = pd.read_parquet(_pq)

    expiry = float(df_raw["daysToExpiry"].iloc[0]) / 365.0

    _cols = ["strike", "bid", "ask", "volume", "openInterest"]
    calls = df_raw[df_raw["optionType"] == "call"][_cols].set_index("strike")
    puts = df_raw[df_raw["optionType"] == "put"][_cols].set_index("strike")
    merged = calls.join(puts, lsuffix="_call", rsuffix="_put", how="inner").sort_index()

    strikes = merged.index.values.astype(np.float64)
    call_bid = merged["bid_call"].values.astype(np.float64)
    call_ask = merged["ask_call"].values.astype(np.float64)
    put_bid = merged["bid_put"].values.astype(np.float64)
    put_ask = merged["ask_put"].values.astype(np.float64)

    prices = OptionChain(
        strikes=strikes,
        call_bid=call_bid,
        call_ask=call_ask,
        put_bid=put_bid,
        put_ask=put_ask,
        expiry=expiry,
    ).denoise()

    sd = prices.to_smile_data().transform(XCoord.FixedStrike, YCoord.Volatility)
    return expiry, prices, sd


@app.cell
def cell_sabr_fit(sd):
    """Fit SABR to market data."""
    sabr_result = fit(sd, SABRModel)
    sabr_p = sabr_result.params
    return sabr_p, sabr_result


@app.cell(hide_code=True)
def cell_sabr_params(sabr_p, sabr_result):
    """Display fitted SABR parameters."""
    mo.vstack(
        [
            mo.md("### Fitted SABR Parameters"),
            mo.md(
                f"""
    | Parameter | Value | Description |
    |-----------|------:|-------------|
    | $\\alpha$ | {sabr_p.alpha:.6f} | Initial volatility |
    | $\\beta$ | {sabr_p.beta:.6f} | CEV exponent |
    | $\\rho$ | {sabr_p.rho:.6f} | Fwd–vol correlation |
    | $\\nu$ | {sabr_p.nu:.6f} | Vol-of-vol |

    **RMSE:** {sabr_result.rmse:.2e} &nbsp;&nbsp; **Converged:** {"Yes" if sabr_result.success else "No"}

    *Context:* expiry = {sabr_p.expiry:.4f}y, forward = {sabr_p.forward:.2f}
    """
            ),
        ]
    )
    return


@app.cell(hide_code=True)
def cell_sabr_fit_plot(expiry, sabr_result, sd):
    """Plot market vols with SABR fitted curve."""
    _fwd = sd.metadata.forward
    _strikes_fine = np.linspace(sd.x.min() * 0.95, sd.x.max() * 1.05, 300)
    _k_fine = np.log(_strikes_fine / _fwd)
    _iv_sabr = sabr_result.params.evaluate(_k_fine)

    _fig = go.Figure()
    _fig.add_trace(
        go.Scatter(
            x=sd.x,
            y=sd.y_mid * 100,
            mode="markers",
            error_y={
                "type": "data",
                "symmetric": False,
                "array": ((sd.y_ask - sd.y_mid) * 100).tolist(),
                "arrayminus": ((sd.y_mid - sd.y_bid) * 100).tolist(),
            },
            marker={"size": 8, "color": "#E74C3C"},
            name="Market (bid/ask)",
        )
    )
    _fig.add_trace(
        go.Scatter(
            x=_strikes_fine,
            y=np.asarray(_iv_sabr) * 100,
            mode="lines",
            line={"color": "#2196F3", "width": 2.5},
            name="SABR Fit",
        )
    )
    _fig.update_layout(
        title="Market Implied Vols vs SABR Fit",
        xaxis_title="Strike",
        yaxis_title="Implied Volatility (%)",
        template="plotly_white",
        height=450,
        legend={"x": 0.02, "y": 0.98},
    )
    mo.ui.plotly(_fig)
    return


# ---------------------------------------------------------------------------
# Part 3 — SVI vs SABR comparison
# ---------------------------------------------------------------------------


@app.cell(hide_code=True)
def cell_compare_intro():
    """Introduce the comparison section."""
    mo.md(
        r"""
        ---
        ## 3. SVI vs SABR Comparison

        Both models are fitted to the same market data. We overlay the
        fitted curves and compare fit quality.

        | Model | Native Y | Parameters |
        |-------|----------|------------|
        | SVI | Total Variance $w = \sigma^2 T$ | $a, b, \rho, m, \sigma$ |
        | SABR | Implied Volatility $\sigma$ | $\alpha, \beta, \rho, \nu$ |
        """
    )
    return


@app.cell
def cell_svi_fit(sd):
    """Fit SVI to the same market data."""
    svi_result = fit(sd, SVIModel)
    svi_p = svi_result.params
    return svi_p, svi_result


@app.cell(hide_code=True)
def cell_comparison_table(sabr_result, svi_result):
    """Compare fit quality metrics."""
    mo.md(
        f"""
    ### Fit Quality Comparison

    | Metric | SVI | SABR |
    |--------|----:|-----:|
    | RMSE | {svi_result.rmse:.2e} | {sabr_result.rmse:.2e} |
    | Converged | {"Yes" if svi_result.success else "No"} | {"Yes" if sabr_result.success else "No"} |
    | # Parameters | {len(SVIModel.param_names)} | {len(SABRModel.param_names)} |
    """
    )
    return


@app.cell(hide_code=True)
def cell_comparison_plot(expiry, sabr_result, sd, svi_result):
    """Overlay SVI and SABR fits on market data."""
    _fwd = sd.metadata.forward
    _strikes_fine = np.linspace(sd.x.min() * 0.95, sd.x.max() * 1.05, 300)
    _k_fine = np.log(_strikes_fine / _fwd)

    _iv_sabr = np.asarray(sabr_result.params.evaluate(_k_fine))
    _iv_svi = np.asarray(svi_result.params.implied_vol(_k_fine, expiry))

    _fig = go.Figure()
    # Market data
    _fig.add_trace(
        go.Scatter(
            x=sd.x,
            y=sd.y_mid * 100,
            mode="markers",
            error_y={
                "type": "data",
                "symmetric": False,
                "array": ((sd.y_ask - sd.y_mid) * 100).tolist(),
                "arrayminus": ((sd.y_mid - sd.y_bid) * 100).tolist(),
            },
            marker={"size": 8, "color": "#999999"},
            name="Market (bid/ask)",
        )
    )
    # SVI
    _fig.add_trace(
        go.Scatter(
            x=_strikes_fine,
            y=_iv_svi * 100,
            mode="lines",
            line={"color": "#2FA4A9", "width": 2.5},
            name="SVI",
        )
    )
    # SABR
    _fig.add_trace(
        go.Scatter(
            x=_strikes_fine,
            y=_iv_sabr * 100,
            mode="lines",
            line={"color": "#2196F3", "width": 2.5, "dash": "dash"},
            name="SABR",
        )
    )
    _fig.update_layout(
        title="SVI vs SABR — Implied Volatility Fit",
        xaxis_title="Strike",
        yaxis_title="Implied Volatility (%)",
        template="plotly_white",
        height=480,
        legend={"x": 0.02, "y": 0.98},
    )
    mo.ui.plotly(_fig)
    return


@app.cell(hide_code=True)
def cell_residuals_plot(sabr_result, sd, svi_result):
    """Plot fit residuals for both models."""
    _fig = go.Figure()
    _fig.add_trace(
        go.Bar(
            x=sd.x,
            y=svi_result.residuals * 1e4,
            name="SVI residuals",
            marker={"color": "#2FA4A9", "opacity": 0.7},
        )
    )
    _fig.add_trace(
        go.Bar(
            x=sd.x,
            y=sabr_result.residuals * 1e4,
            name="SABR residuals",
            marker={"color": "#2196F3", "opacity": 0.7},
        )
    )
    _fig.update_layout(
        title="Fit Residuals (native coordinates)",
        xaxis_title="Strike",
        yaxis_title="Residual (×10⁴)",
        template="plotly_white",
        height=380,
        barmode="group",
        legend={"x": 0.02, "y": 0.98},
    )
    mo.ui.plotly(_fig)
    return


# ---------------------------------------------------------------------------


@app.cell(hide_code=True)
def cell_summary():
    """Render the conclusion."""
    mo.md(
        r"""
        ---
        ## Summary

        | Step | Code |
        |------|------|
        | Construct SABR model | `SABRModel(alpha, beta, rho, nu, expiry, forward)` |
        | Evaluate smile | `model.evaluate(k)` — Hagan (2002) implied vol |
        | Fit to market data | `fit(sd, SABRModel)` — automatic coordinate transform |
        | Compare models | Both `SVIModel` and `SABRModel` work with `fit()` |

        The **SABR model** is a natural complement to SVI:
        - SVI operates in **total-variance** space — excellent for arbitrage-free interpolation
        - SABR operates in **implied-vol** space with stochastic-vol dynamics — links to hedging and risk
        """
    )
    return


if __name__ == "__main__":
    app.run()
