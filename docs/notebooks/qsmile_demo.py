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
# path = "../.."
# editable = true
# ///

import marimo

__generated_with = "0.21.1"
app = marimo.App(width="medium")

with app.setup:
    import marimo as mo
    import numpy as np
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    from qsmile import (
        SABRModel,
        SampleDataReader,
        SVIModel,
        XCoord,
        YCoord,
        fit,
    )


@app.cell(hide_code=True)
def cell_intro():
    """Notebook introduction."""
    mo.md(
        r"""
        # qsmile demo

        This notebook walks through the **qsmile calculaition flow** using real
        S&P 500 (SPX) option-chain data.

        | # | Layer | Key classes / functions |
        |---|-------|------------------------|
        | 1 | **Option chain** | `OptionChain` — load, filter, calibrate $F$, $D$ |
        | 2 | **VolData** | `to_vols()`, coordinate transforms |
        | 3 | **Model fitting** | `fit(sd, SVIModel)`, `fit(sd, SABRModel)` |
        | 4 | **Ancillary** | volume / open interest passthrough |
        """
    )
    return


@app.cell(hide_code=True)
def cell_chain_intro():
    """Introduce the option-chain section."""
    mo.md(
        r"""
        ---
        ## 1 · OptionChain — Real SPX Data

        We load a real SPX chain from parquet, then **filter first** to
        remove arbitrageable quotes before calibrating forward and
        discount factor.

        The filtering pipeline applies five sequential checks:

        1. **Zero-bid** — remove strikes where either bid is zero
        2. **Put-call parity monotonicity** — enforce $C_\text{mid} - P_\text{mid}$ decreasing in $K$
        3. **Call/put mid monotonicity** — calls decreasing, puts increasing
        4. **Sub-intrinsic** — drop strikes priced below intrinsic value
        5. **Parity residual** — trim large deviations from calibrated parity

        After filtering, forward $F$ and discount factor $D$ are
        **calibrated from put-call parity** on the clean data:

        $$C_{\mathrm{mid}} - P_{\mathrm{mid}} \approx D(F - K)$$
        """
    )
    return


@app.cell(hide_code=True)
def cell_load_data():
    """Load real SPX option chain from parquet."""
    reader = SampleDataReader()
    chain_raw = reader.get_chain("SPX", "2026-04-03", "2026-06-30")
    return (chain_raw,)


@app.cell(hide_code=True)
def cell_build_and_filter(chain_raw):
    """Filter the raw chain, then show before/after comparison."""
    chain = chain_raw.filter()

    _n_raw = len(chain_raw.strikes)
    _n_clean = len(chain.strikes)
    _vol_raw = "Yes" if chain_raw.volume is not None else "No"
    _vol_cln = "Yes" if chain.volume is not None else "No"
    _oi_raw = "Yes" if chain_raw.open_interest is not None else "No"
    _oi_cln = "Yes" if chain.open_interest is not None else "No"

    _filter_table = f"""\
    ### Before & after filtering

    | Metric | Raw | Filtered |
    |--------|----:|---------:|
    | Strikes | {_n_raw} | {_n_clean} |
    | Removed | — | {_n_raw - _n_clean} |
    | Volume attached | {_vol_raw} | {_vol_cln} |
    | OI attached | {_oi_raw} | {_oi_cln} |
    """
    _meta_table = f"""\
    ### Metadata

    | Field | Value |
    |-------|------:|
    | Date | {chain.metadata.date.strftime("%Y-%m-%d")} |
    | Expiry | {chain.metadata.expiry.strftime("%Y-%m-%d")} |
    | Day count | {chain.metadata.daycount.value} |
    | $T$ (years) | {chain.metadata.texpiry:.4f} |
    | Forward $F$ | {chain.metadata.forward:,.2f} |
    | Discount factor $D$ | {chain.metadata.discount_factor:.6f} |
    """
    mo.hstack(
        [mo.md(_filter_table), mo.md(_meta_table)],
        justify="start",
        gap=2,
    )
    return chain, chain_raw


@app.cell(hide_code=True)
def cell_chain_plot(chain, chain_raw):
    """Plot raw vs filtered bid/ask prices."""
    _fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=["Raw (all strikes)", "Filtered (clean)"],
        shared_yaxes=True,
    )
    for _col, src, title in [(1, chain_raw, "Raw"), (2, chain, "Filtered")]:
        for label, mid, bid, ask, color in [
            ("Calls", src.call_mid, src.call_bid, src.call_ask, "#2196F3"),
            ("Puts", src.put_mid, src.put_bid, src.put_ask, "#E88D7D"),
        ]:
            _fig.add_trace(
                go.Scatter(
                    x=src.strikes,
                    y=mid,
                    mode="markers+lines",
                    error_y={
                        "type": "data",
                        "symmetric": False,
                        "array": (ask - mid).tolist(),
                        "arrayminus": (mid - bid).tolist(),
                    },
                    name=f"{label} ({title})",
                    marker={"color": color, "size": 4},
                    line={"color": color},
                    showlegend=(_col == 1),
                ),
                row=1,
                col=_col,
            )
    _x_lo = min(float(chain_raw.strikes.min()), float(chain.strikes.min()))
    _x_hi = max(float(chain_raw.strikes.max()), float(chain.strikes.max()))
    _y_lo = min(
        float(chain_raw.call_bid.min()),
        float(chain_raw.put_bid.min()),
        float(chain.call_bid.min()),
        float(chain.put_bid.min()),
    )
    _y_hi = max(
        float(chain_raw.call_ask.max()),
        float(chain_raw.put_ask.max()),
        float(chain.call_ask.max()),
        float(chain.put_ask.max()),
    )
    _x_pad = (_x_hi - _x_lo) * 0.05
    _y_pad = (_y_hi - _y_lo) * 0.05
    _fig.update_xaxes(
        title_text="Strike",
        range=[_x_lo - _x_pad, _x_hi + _x_pad],
    )
    _fig.update_yaxes(
        title_text="Price",
        range=[_y_lo - _y_pad, _y_hi + _y_pad],
    )
    _fig.update_layout(
        title="Option Prices — Raw vs Filtered",
        template="plotly_white",
        height=400,
    )
    mo.ui.plotly(_fig)
    return


@app.cell(hide_code=True)
def cell_sd_intro():
    """Introduce VolData section."""
    _x_table = (
        "| X-coordinate | Formula |\n"
        "|-------------|---------|\n"
        "| FixedStrike | $K$ |\n"
        "| MoneynessStrike | $K / F$ |\n"
        r"| LogMoneynessStrike | $\ln(K/F)$ |"
        "\n"
        r"| StandardisedStrike | $\ln(K/F) / (\sigma_\text{ATM}\sqrt{T})$ |"
    )
    _y_table = (
        "| Y-coordinate | Formula |\n"
        "|-------------|---------|\n"
        "| Price | option price |\n"
        r"| Volatility | $\sigma$ |"
        "\n"
        r"| Variance | $\sigma^2$ |"
        "\n"
        r"| TotalVariance | $\sigma^2 T$ |"
    )
    mo.md(
        r"""
        ---
        ## 2 · VolData & Coordinate Transforms

        `.to_vols()` delta-blends call/put implied vols into
        **(FixedStrike, Volatility)** using Black-76 call-delta weights.

        From there, `.transform(x, y)` moves freely between any combination:
        """
    )
    mo.hstack(
        [mo.md(_x_table), mo.md(_y_table)],
        justify="start",
        gap=2,
    )
    return


@app.cell(hide_code=True)
def cell_smile_data(chain):
    """Create VolData in price and vol coordinates."""
    sd_vols = chain.to_vols()

    mo.md(
        f"""
    ### VolData containers

    | Container | X coord | Y coord | Points |
    |-----------|---------|---------|-------:|
    | `sd_vols` | {sd_vols.current_x_coord.name} | {sd_vols.current_y_coord.name} | {len(sd_vols.x)} |
    | Volume attached | {"Yes" if sd_vols.volume is not None else "No"} |
    | Open interest attached | {"Yes" if sd_vols.open_interest is not None else "No"} |
    """
    )
    return (sd_vols,)


@app.cell(hide_code=True)
def cell_transform_grid(sd_vols):
    """Plot the same smile in four coordinate systems."""
    views = [
        ("FixedStrike / Volatility", XCoord.FixedStrike, YCoord.Volatility, "Strike", "σ"),
        ("MoneynessStrike / Volatility", XCoord.MoneynessStrike, YCoord.Volatility, "K/F", "σ"),
        (
            "LogMoneyness / TotalVariance",
            XCoord.LogMoneynessStrike,
            YCoord.TotalVariance,
            "ln(K/F)",
            "σ²T",
        ),
        (
            "Standardised / TotalVariance",
            XCoord.StandardisedStrike,
            YCoord.TotalVariance,
            "k̃",
            "σ²T",
        ),
    ]

    _fig = make_subplots(rows=2, cols=2, subplot_titles=[v[0] for v in views])
    colors = ["#2196F3", "#E88D7D", "#2FA4A9", "#9B59B6"]

    for idx, (_title, xc, yc, xlabel, ylabel) in enumerate(views):
        v = sd_vols.transform(xc, yc)
        _row, _col = divmod(idx, 2)
        _fig.add_trace(
            go.Scatter(
                x=v.x,
                y=v.y_mid,
                mode="markers+lines",
                marker={"color": colors[idx], "size": 5},
                line={"color": colors[idx]},
                showlegend=False,
            ),
            row=_row + 1,
            col=_col + 1,
        )
        _fig.update_xaxes(title_text=xlabel, row=_row + 1, col=_col + 1)
        _fig.update_yaxes(title_text=ylabel, row=_row + 1, col=_col + 1)

    _fig.update_layout(
        title="Same Smile — Four Coordinate Systems",
        template="plotly_white",
        height=620,
    )
    mo.ui.plotly(_fig)
    return


@app.cell(hide_code=True)
def cell_svi_intro():
    """Introduce SVI fitting."""
    mo.md(
        r"""
        ---
        ## 3 · SVI Model Fit

        Stochastic Volatility Inspired parametrisation (Gatheral, 2004):

        $$
        w(k) = a + b\bigl[\rho\,(k - m) + \sqrt{(k - m)^2 + \sigma^2}\bigr]
        $$

        where $k = \ln(K/F)$ is log-moneyness and $w = \sigma^2 T$ is
        total implied variance.

        `fit(sd, SVIModel)` transforms data to the model's native
        **(LogMoneynessStrike, TotalVariance)** coordinates automatically.
        """
    )
    return


@app.cell(hide_code=True)
def cell_svi_fit(sd_vols):
    """Fit SVI to the market smile."""
    svi_result = fit(sd_vols, SVIModel)
    p = svi_result.model

    _params_table = f"""
    ### SVI Parameters

    | Parameter | Value | Meaning |
    |-----------|------:|--------|
    | $a$ | {p.a:.6f} | Vertical shift |
    | $b$ | {p.b:.6f} | Wing slope |
    | $\\rho$ | {p.rho:.6f} | Skew |
    | $m$ | {p.m:.6f} | Horizontal shift |
    | $\\sigma$ | {p.sigma:.6f} | ATM curvature |
    """
    _diag_table = f"""
    ### Fit Diagnostics

    | Metric | Value |
    |--------|------:|
    | **RMSE** | {svi_result.rmse:.2e} |
    | **Converged** | {"Yes" if svi_result.success else "No"} |
    """
    mo.hstack(
        [mo.md(_params_table), mo.md(_diag_table)],
        justify="start",
        gap=2,
    )
    return (svi_result,)


@app.cell(hide_code=True)
def cell_svi_plot(sd_vols, svi_result):
    """Overlay SVI fit on market vols."""
    _fwd = sd_vols.metadata.forward
    _k_fine = np.linspace(sd_vols.x.min() * 0.95, sd_vols.x.max() * 1.05, 300)
    _log_k = np.log(_k_fine / _fwd)
    _iv_svi = svi_result.model.transform(XCoord.LogMoneynessStrike, YCoord.Volatility).evaluate(_log_k)

    _fig = go.Figure()
    _fig.add_trace(
        go.Scatter(
            x=sd_vols.x,
            y=sd_vols.y_mid * 100,
            mode="markers",
            error_y={
                "type": "data",
                "symmetric": False,
                "array": ((sd_vols.y_ask - sd_vols.y_mid) * 100).tolist(),
                "arrayminus": ((sd_vols.y_mid - sd_vols.y_bid) * 100).tolist(),
            },
            marker={"size": 8, "color": "#E88D7D"},
            name="Market (bid/ask)",
        )
    )
    _fig.add_trace(
        go.Scatter(
            x=_k_fine,
            y=_iv_svi * 100,
            mode="lines",
            line={"color": "#2FA4A9", "width": 2.5},
            name="SVI fit",
        )
    )
    _fig.update_layout(
        title="SVI Fit vs Market Implied Vols",
        xaxis_title="Strike",
        yaxis_title="Implied Volatility (%)",
        template="plotly_white",
        height=400,
    )
    mo.ui.plotly(_fig)
    return


@app.cell(hide_code=True)
def cell_sabr_intro():
    """Introduce SABR fitting."""
    mo.md(
        r"""
        ---
        ## 4 · SABR Model Fit

        Hagan (2002) SABR lognormal implied volatility approximation.
        The SABR model describes the joint dynamics of a forward $F$
        and its stochastic volatility $\alpha$:

        $$
        \begin{aligned}
        dF &= \alpha\, F^\beta\, dW_1 \\
        d\alpha &= \nu\, \alpha\, dW_2 \\
        \langle dW_1, dW_2 \rangle &= \rho\, dt
        \end{aligned}
        $$

        Four fitted parameters: $\alpha$ (initial vol), $\beta$ (CEV exponent),
        $\rho$ (correlation), $\nu$ (vol-of-vol).

        `fit(sd, SABRModel)` transforms to the model's native
        **(LogMoneynessStrike, Volatility)** coordinates.
        """
    )
    return


@app.cell(hide_code=True)
def cell_sabr_fit(sd_vols):
    """Fit SABR to the market smile."""
    sabr_result = fit(sd_vols, SABRModel)
    sp = sabr_result.model

    _params_table = f"""
    ### SABR Parameters

    | Parameter | Value | Meaning |
    |-----------|------:|--------|
    | $\\alpha$ | {sp.alpha:.6f} | Initial vol |
    | $\\beta$ | {sp.beta:.6f} | CEV exponent |
    | $\\rho$ | {sp.rho:.6f} | Correlation |
    | $\\nu$ | {sp.nu:.6f} | Vol-of-vol |
    """
    _diag_table = f"""
    ### Fit Diagnostics

    | Metric | Value |
    |--------|------:|
    | **RMSE** | {sabr_result.rmse:.2e} |
    | **Converged** | {"Yes" if sabr_result.success else "No"} |
    """
    mo.hstack(
        [mo.md(_params_table), mo.md(_diag_table)],
        justify="start",
        gap=2,
    )
    return (sabr_result,)


@app.cell(hide_code=True)
def cell_sabr_plot(sabr_result, sd_vols):
    """Overlay SABR fit on market vols."""
    _fwd = sd_vols.metadata.forward
    _k_fine = np.linspace(sd_vols.x.min() * 0.95, sd_vols.x.max() * 1.05, 300)
    _log_k = np.log(_k_fine / _fwd)
    _iv_sabr = sabr_result.model.evaluate(_log_k)

    _fig = go.Figure()
    _fig.add_trace(
        go.Scatter(
            x=sd_vols.x,
            y=sd_vols.y_mid * 100,
            mode="markers",
            error_y={
                "type": "data",
                "symmetric": False,
                "array": ((sd_vols.y_ask - sd_vols.y_mid) * 100).tolist(),
                "arrayminus": ((sd_vols.y_mid - sd_vols.y_bid) * 100).tolist(),
            },
            marker={"size": 8, "color": "#E88D7D"},
            name="Market (bid/ask)",
        )
    )
    _fig.add_trace(
        go.Scatter(
            x=_k_fine,
            y=_iv_sabr * 100,
            mode="lines",
            line={"color": "#7E57C2", "width": 2.5},
            name="SABR fit",
        )
    )
    _fig.update_layout(
        title="SABR Fit vs Market Implied Vols",
        xaxis_title="Strike",
        yaxis_title="Implied Volatility (%)",
        template="plotly_white",
        height=400,
    )
    mo.ui.plotly(_fig)
    return


@app.cell(hide_code=True)
def cell_comparison_intro():
    """Introduce model comparison section."""
    mo.md(
        r"""
        ---
        ## 5 · Model Comparison

        Both SVI and SABR fits overlaid on the same market data for
        direct visual comparison.
        """
    )
    return


@app.cell(hide_code=True)
def cell_model_comparison(sabr_result, sd_vols, svi_result):
    """Compare SVI and SABR fits on the same plot."""
    _fwd = sd_vols.metadata.forward
    _k_fine = np.linspace(sd_vols.x.min() * 0.95, sd_vols.x.max() * 1.05, 300)
    _log_k = np.log(_k_fine / _fwd)

    _iv_svi = svi_result.model.transform(XCoord.LogMoneynessStrike, YCoord.Volatility).evaluate(_log_k)
    _iv_sabr = sabr_result.model.evaluate(_log_k)

    _fig = go.Figure()
    _fig.add_trace(
        go.Scatter(
            x=sd_vols.x,
            y=sd_vols.y_mid * 100,
            mode="markers",
            error_y={
                "type": "data",
                "symmetric": False,
                "array": ((sd_vols.y_ask - sd_vols.y_mid) * 100).tolist(),
                "arrayminus": ((sd_vols.y_mid - sd_vols.y_bid) * 100).tolist(),
            },
            marker={"size": 8, "color": "#E88D7D"},
            name="Market (bid/ask)",
        )
    )
    _fig.add_trace(
        go.Scatter(
            x=_k_fine,
            y=_iv_svi * 100,
            mode="lines",
            line={"color": "#2FA4A9", "width": 2.5},
            name=f"SVI  (RMSE {svi_result.rmse:.2e})",
        )
    )
    _fig.add_trace(
        go.Scatter(
            x=_k_fine,
            y=_iv_sabr * 100,
            mode="lines",
            line={"color": "#7E57C2", "width": 2.5},
            name=f"SABR (RMSE {sabr_result.rmse:.2e})",
        )
    )
    _fig.update_layout(
        title="SVI vs SABR — Model Comparison",
        xaxis_title="Strike",
        yaxis_title="Implied Volatility (%)",
        template="plotly_white",
        height=420,
        legend={
            "orientation": "h",
            "yanchor": "top",
            "y": -0.15,
            "xanchor": "center",
            "x": 0.5,
        },
    )
    mo.ui.plotly(_fig)
    return


@app.cell(hide_code=True)
def cell_vol_oi_intro():
    """Introduce volume / open interest section."""
    mo.md(
        r"""
        ---
        ## 6 · Volume & Open Interest Passthrough

        Optional `volume` and `open_interest` arrays flow through the
        entire pipeline — from `OptionChain` through `filter()`,
        `to_vols()`, and
        `VolData.transform()`.
        """
    )
    return


@app.cell(hide_code=True)
def cell_vol_oi_demo(chain):
    """Show volume / OI surviving the pipeline."""
    sd_with_vol = chain.to_vols()
    sd_transformed = sd_with_vol.transform(XCoord.LogMoneynessStrike, YCoord.TotalVariance)

    _fig = make_subplots(
        rows=2,
        cols=1,
        subplot_titles=["Volume by Strike", "Open Interest by Strike"],
        shared_xaxes=True,
    )
    _fig.add_trace(
        go.Bar(
            x=chain.strikes,
            y=chain.volume,
            marker_color="#2196F3",
            name="Volume",
            showlegend=False,
        ),
        row=1,
        col=1,
    )
    _fig.add_trace(
        go.Bar(
            x=chain.strikes,
            y=chain.open_interest,
            marker_color="#9B59B6",
            name="Open Interest",
            showlegend=False,
        ),
        row=2,
        col=1,
    )
    _fig.update_layout(
        title="Volume & Open Interest — Preserved Through Pipeline",
        template="plotly_white",
        height=450,
    )
    _fig.update_xaxes(title_text="Strike", row=2, col=1)
    _fig.update_yaxes(title_text="Volume", row=1, col=1)
    _fig.update_yaxes(title_text="Open Interest", row=2, col=1)

    _vol = lambda o: "✓" if o.volume is not None else "✗"  # noqa: E731
    _oi = lambda o: "✓" if o.open_interest is not None else "✗"  # noqa: E731

    mo.vstack(
        [
            mo.ui.plotly(_fig),
            mo.md(
                f"""
    | Pipeline stage | Volume? | OI? |
    |----------------|:-------:|:---:|
    | `OptionChain` (raw) | {_vol(chain)} | {_oi(chain)} |
    | `to_vols()` | {_vol(sd_with_vol)} | {_oi(sd_with_vol)} |
    | `transform(LogMoneyness, TotalVar)` | {_vol(sd_transformed)} | {_oi(sd_transformed)} |
    """
            ),
        ]
    )
    return


@app.cell(hide_code=True)
def cell_summary():
    """Conclude the notebook."""
    mo.md(
        r"""
        ---
        ## Summary

        | Step | API | What it does |
        |------|-----|-------------|
        | Load | `OptionChain(...)` | Stores bid/ask prices |
        | Clean | `.filter()` | 5-filter arbitrage removal |
        | Calibrate | automatic | Forward $F$ and discount factor $D$ from put-call parity |
        | Convert | `.to_vols()` | Delta-blended implied vols |
        | Transform | `.transform(x, y)` | Any $(X, Y)$ coordinate pair |
        | Fit | `fit(sd, SVIModel)` / `fit(sd, SABRModel)` | Parametric smile fit |
        | Ancillary | `volume`, `open_interest` | Optional data carried through pipeline |
        """
    )
    return


if __name__ == "__main__":
    app.run()
