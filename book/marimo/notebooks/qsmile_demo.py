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
        SmileMetadata,
        SVIModel,
        XCoord,
        YCoord,
        black76_call,
        black76_implied_vol,
        black76_put,
        fit,
    )


@app.cell(hide_code=True)
def cell_intro():
    """Notebook introduction."""
    mo.md(
        r"""
        # qsmile — Full Functionality Demo

        This notebook walks through the **entire qsmile stack** using real
        S&P 500 (SPX) option-chain data.

        | # | Layer | Key classes / functions |
        |---|-------|------------------------|
        | 1 | **Black-76** | `black76_call`, `black76_put`, `black76_implied_vol` |
        | 2 | **Option chain** | `OptionChain` — auto-calibrates $F$, $D$ from put-call parity |
        | 3 | **Denoising** | `OptionChain.filter()` — 5-filter cleaning pipeline |
        | 4 | **SmileData** | `to_smile_data()`, coordinate transforms |
        | 5 | **Model fitting** | `fit(sd, SVIModel)`, `fit(sd, SABRModel)` |
        | 6 | **Ancillary** | volume / open interest passthrough, `SmileData.plot()` |
        """
    )
    return


@app.cell(hide_code=True)
def cell_b76_intro():
    """Introduce Black-76 section."""
    mo.md(
        r"""
        ---
        ## 1 · Black-76 Pricing

        Black-76 prices European options on a forward:

        $$
        C = D\bigl[F\,\Phi(d_1) - K\,\Phi(d_2)\bigr],
        \quad
        P = D\bigl[K\,\Phi(-d_2) - F\,\Phi(-d_1)\bigr]
        $$

        where $d_{1,2} = \frac{\ln(F/K) \pm \tfrac12 \sigma^2 T}{\sigma\sqrt{T}}$.
        """
    )
    return


@app.cell(hide_code=True)
def cell_b76_scalar():
    """Scalar Black-76 pricing."""
    F, K, D, sigma, T = 5500.0, 5500.0, 0.98, 0.20, 0.25

    call_price = black76_call(F, K, D, sigma, T)
    put_price = black76_put(F, K, D, sigma, T)

    mo.md(
        f"""
    ### Scalar example

    | Input | Value |
    |-------|-------|
    | Forward $F$ | {F:,.0f} |
    | Strike $K$ | {K:,.0f} |
    | Discount factor $D$ | {D} |
    | Vol $\\sigma$ | {sigma:.0%} |
    | Expiry $T$ | {T} yr |

    | Output | Value |
    |--------|------:|
    | Call | {float(call_price):.4f} |
    | Put  | {float(put_price):.4f} |
    | Put-call parity check $C - P$ | {float(call_price - put_price):.4f} |
    | $D(F - K)$ | {D * (F - K):.4f} |
    """
    )
    return D, F, T, sigma


@app.cell(hide_code=True)
def cell_b76_vector(D, F, T, sigma):
    """Vectorised pricing and implied-vol round-trip."""
    _strikes = np.linspace(4500, 6500, 41)
    _prices = black76_call(F, _strikes, D, sigma, T)

    # Invert back to implied vol
    _recovered = np.array(
        [black76_implied_vol(float(p), F, float(k), D, T, is_call=True) for p, k in zip(_prices, _strikes, strict=True)]
    )
    _max_err = float(np.max(np.abs(_recovered - sigma)))

    _fig = go.Figure()
    _fig.add_trace(
        go.Scatter(x=_strikes, y=_prices, mode="lines+markers", name="Call price"),
    )
    _fig.update_layout(
        title="Black-76 Call Prices (vectorised)",
        xaxis_title="Strike",
        yaxis_title="Price",
        template="plotly_white",
        height=350,
    )
    mo.vstack(
        [
            mo.ui.plotly(_fig),
            mo.md(f"**Implied-vol round-trip** — max |σ_recovered − σ_input| = `{_max_err:.2e}`"),
        ]
    )
    return


@app.cell(hide_code=True)
def cell_chain_intro():
    """Introduce the option-chain section."""
    mo.md(
        r"""
        ---
        ## 2 · OptionChain — Real SPX Data

        We load a real SPX chain from parquet. The constructor
        **auto-calibrates forward and discount factor** via quasi-delta
        weighted least squares on put-call parity:

        $$C_{\mathrm{mid}} - P_{\mathrm{mid}} \approx D(F - K)$$
        """
    )
    return


@app.cell(hide_code=True)
def cell_load_data():
    """Load real SPX option chain from parquet."""
    _root = Path(__file__).resolve().parent.parent.parent.parent
    _pq = sorted(_root.glob("parquet/chains/*.parquet"))[-1]
    df_raw = pd.read_parquet(_pq)

    expiry_days = float(df_raw["daysToExpiry"].iloc[0])
    expiry = expiry_days / 365.0

    # Pivot calls/puts onto common strikes
    _cols = ["strike", "bid", "ask", "volume", "openInterest"]
    calls = df_raw[df_raw["optionType"] == "call"][_cols].set_index("strike")
    puts = df_raw[df_raw["optionType"] == "put"][_cols].set_index("strike")
    merged = calls.join(puts, lsuffix="_call", rsuffix="_put", how="inner").sort_index()

    strikes = merged.index.values.astype(np.float64)
    call_bid = merged["bid_call"].values.astype(np.float64)
    call_ask = merged["ask_call"].values.astype(np.float64)
    put_bid = merged["bid_put"].values.astype(np.float64)
    put_ask = merged["ask_put"].values.astype(np.float64)
    volume = (merged["volume_call"].fillna(0).values + merged["volume_put"].fillna(0).values).astype(np.float64)
    oi = (merged["openInterest_call"].fillna(0).values + merged["openInterest_put"].fillna(0).values).astype(np.float64)
    return call_ask, call_bid, expiry, oi, put_ask, put_bid, strikes, volume


@app.cell(hide_code=True)
def cell_build_chain(
    call_ask,
    call_bid,
    expiry,
    oi,
    put_ask,
    put_bid,
    strikes,
    volume,
):
    """Build an OptionChain — forward / DF calibrated automatically."""
    chain_raw = OptionChain(
        strikes=strikes,
        call_bid=call_bid,
        call_ask=call_ask,
        put_bid=put_bid,
        put_ask=put_ask,
        metadata=SmileMetadata(expiry=expiry),
        volume=volume,
        open_interest=oi,
    )

    mo.md(
        f"""
    ### Calibrated from put-call parity

    | Quantity | Value |
    |----------|------:|
    | Strikes loaded | {len(strikes)} |
    | Expiry | {expiry:.4f} yr ({expiry * 365:.0f} days) |
    | Forward $F$ | {chain_raw.metadata.forward:,.2f} |
    | Discount factor $D$ | {chain_raw.metadata.discount_factor:.6f} |
    """
    )
    return (chain_raw,)


@app.cell(hide_code=True)
def cell_chain_plot(chain_raw):
    """Plot raw bid/ask prices with error bars."""
    _fig = go.Figure()
    for label, mid, bid, ask, color in [
        ("Calls", chain_raw.call_mid, chain_raw.call_bid, chain_raw.call_ask, "#2196F3"),
        ("Puts", chain_raw.put_mid, chain_raw.put_bid, chain_raw.put_ask, "#E74C3C"),
    ]:
        _fig.add_trace(
            go.Scatter(
                x=chain_raw.strikes,
                y=mid,
                mode="markers+lines",
                error_y={
                    "type": "data",
                    "symmetric": False,
                    "array": (ask - mid).tolist(),
                    "arrayminus": (mid - bid).tolist(),
                },
                name=label,
                marker={"color": color},
            )
        )
    _fig.update_layout(
        title="Raw Bid/Ask Option Prices",
        xaxis_title="Strike",
        yaxis_title="Price",
        template="plotly_white",
        height=400,
    )
    mo.ui.plotly(_fig)
    return


@app.cell(hide_code=True)
def cell_filter_intro():
    """Introduce the denoising section."""
    mo.md(
        r"""
        ---
        ## 3 · Denoising

        `OptionChain.filter()` applies five sequential filters to remove
        arbitrageable or noisy quotes:

        1. **Zero-bid** — remove strikes where either bid is zero
        2. **Put-call parity monotonicity** — enforce $C_\text{mid} - P_\text{mid}$ decreasing in $K$
        3. **Call/put mid monotonicity** — calls decreasing, puts increasing
        4. **Sub-intrinsic** — drop strikes priced below intrinsic value
        5. **Parity residual** — trim large deviations from calibrated parity
        """
    )
    return


@app.cell(hide_code=True)
def cell_filter(chain_raw):
    """Denoise the option chain."""
    chain = chain_raw.filter()

    mo.md(
        f"""
    ### Denoising result

    | Metric | Value |
    |--------|------:|
    | Strikes before | {len(chain_raw.strikes)} |
    | Strikes after  | {len(chain.strikes)} |
    | Removed | {len(chain_raw.strikes) - len(chain.strikes)} |
    | Volume preserved | {"Yes" if chain.volume is not None else "No"} |
    | Open interest preserved | {"Yes" if chain.open_interest is not None else "No"} |
    """
    )
    return (chain,)


@app.cell(hide_code=True)
def cell_sd_intro():
    """Introduce SmileData section."""
    mo.md(
        r"""
        ---
        ## 4 · SmileData & Coordinate Transforms

        `.to_smile_data()` delta-blends call/put implied vols into
        **(FixedStrike, Volatility)** using Black-76 call-delta weights.

        From there, `.transform(x, y)` moves freely between any combination:

        | X-coordinate | Formula |
        |-------------|---------|
        | FixedStrike | $K$ |
        | MoneynessStrike | $K / F$ |
        | LogMoneynessStrike | $\ln(K/F)$ |
        | StandardisedStrike | $\ln(K/F) / (\sigma_\text{ATM}\sqrt{T})$ |

        | Y-coordinate | Formula |
        |-------------|---------|
        | Price | option price |
        | Volatility | $\sigma$ |
        | Variance | $\sigma^2$ |
        | TotalVariance | $\sigma^2 T$ |
        """
    )
    return


@app.cell(hide_code=True)
def cell_smile_data(chain):
    """Create SmileData in price and vol coordinates."""
    sd_vols = chain.to_smile_data()

    mo.md(
        f"""
    ### SmileData containers

    | Container | X coord | Y coord | Points |
    |-----------|---------|---------|-------:|
    | `sd_vols` | {sd_vols.x_coord.name} | {sd_vols.y_coord.name} | {len(sd_vols.x)} |
    | Volume attached | {"Yes" if sd_vols.volume is not None else "No"} |
    | Open interest attached | {"Yes" if sd_vols.open_interest is not None else "No"} |

    **Metadata** — forward={sd_vols.metadata.forward:,.2f},
    DF={sd_vols.metadata.discount_factor:.6f},
    expiry={sd_vols.metadata.expiry:.4f}
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
    colors = ["#2196F3", "#E74C3C", "#2FA4A9", "#9B59B6"]

    for idx, (_title, xc, yc, xlabel, ylabel) in enumerate(views):
        v = sd_vols.transform(xc, yc)
        row, col = divmod(idx, 2)
        _fig.add_trace(
            go.Scatter(
                x=v.x,
                y=v.y_mid,
                mode="markers+lines",
                marker={"color": colors[idx], "size": 5},
                line={"color": colors[idx]},
                showlegend=False,
            ),
            row=row + 1,
            col=col + 1,
        )
        _fig.update_xaxes(title_text=xlabel, row=row + 1, col=col + 1)
        _fig.update_yaxes(title_text=ylabel, row=row + 1, col=col + 1)

    _fig.update_layout(
        title="Same Smile — Four Coordinate Systems",
        template="plotly_white",
        height=620,
    )
    mo.ui.plotly(_fig)
    return


@app.cell(hide_code=True)
def cell_roundtrip(sd_vols):
    """Demonstrate coordinate round-trip fidelity."""
    there = sd_vols.transform(XCoord.StandardisedStrike, YCoord.TotalVariance)
    back = there.transform(XCoord.FixedStrike, YCoord.Volatility)
    max_x_err = float(np.max(np.abs(back.x - sd_vols.x)))
    max_y_err = float(np.max(np.abs(back.y_mid - sd_vols.y_mid)))

    mo.md(
        f"""
    ### Round-trip fidelity

    Transform FixedStrike/Volatility → StandardisedStrike/TotalVariance → back:

    | Metric | Value |
    |--------|------:|
    | Max X error | {max_x_err:.2e} |
    | Max Y error | {max_y_err:.2e} |

    Exact to floating-point precision.
    """
    )
    return


@app.cell(hide_code=True)
def cell_svi_intro():
    """Introduce SVI fitting."""
    mo.md(
        r"""
        ---
        ## 5 · SVI Model Fit

        Stochastic Volatility Inspired parametrisation (Gatheral, 2004):

        $$w(k) = a + b\bigl[\rho\,(k - m) + \sqrt{(k - m)^2 + \sigma^2}\bigr]$$

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
    p = svi_result.params

    mo.md(
        f"""
    ### Fitted SVI parameters

    | Parameter | Value | Meaning |
    |-----------|------:|---------|
    | $a$ | {p.a:.6f} | Vertical shift |
    | $b$ | {p.b:.6f} | Wing slope |
    | $\\rho$ | {p.rho:.6f} | Skew |
    | $m$ | {p.m:.6f} | Horizontal shift |
    | $\\sigma$ | {p.sigma:.6f} | ATM curvature |
    | **RMSE** | {svi_result.rmse:.2e} | |
    | **Converged** | {"Yes" if svi_result.success else "No"} | |
    """
    )
    return (svi_result,)


@app.cell(hide_code=True)
def cell_svi_plot(sd_vols, svi_result):
    """Overlay SVI fit on market vols."""
    _fwd = sd_vols.metadata.forward
    _exp = sd_vols.metadata.expiry
    _k_fine = np.linspace(sd_vols.x.min() * 0.95, sd_vols.x.max() * 1.05, 300)
    _log_k = np.log(_k_fine / _fwd)
    _iv_svi = svi_result.params.implied_vol(_log_k, _exp)

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
            marker={"size": 8, "color": "#E74C3C"},
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
        ## 6 · SABR Model Fit

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
    sp = sabr_result.params

    mo.md(
        f"""
    ### Fitted SABR parameters

    | Parameter | Value | Meaning |
    |-----------|------:|---------|
    | $\\alpha$ | {sp.alpha:.6f} | Initial vol |
    | $\\beta$ | {sp.beta:.6f} | CEV exponent |
    | $\\rho$ | {sp.rho:.6f} | Correlation |
    | $\\nu$ | {sp.nu:.6f} | Vol-of-vol |
    | **RMSE** | {sabr_result.rmse:.2e} | |
    | **Converged** | {"Yes" if sabr_result.success else "No"} | |
    """
    )
    return (sabr_result,)


@app.cell(hide_code=True)
def cell_model_comparison(sabr_result, sd_vols, svi_result):
    """Compare SVI and SABR fits on the same plot."""
    _fwd = sd_vols.metadata.forward
    _exp = sd_vols.metadata.expiry
    _k_fine = np.linspace(sd_vols.x.min() * 0.95, sd_vols.x.max() * 1.05, 300)
    _log_k = np.log(_k_fine / _fwd)

    _iv_svi = svi_result.params.implied_vol(_log_k, _exp)
    _iv_sabr = sabr_result.params.evaluate(_log_k)

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
            marker={"size": 8, "color": "#999"},
            name="Market",
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
            line={"color": "#FF9800", "width": 2.5, "dash": "dot"},
            name=f"SABR (RMSE {sabr_result.rmse:.2e})",
        )
    )
    _fig.update_layout(
        title="SVI vs SABR — Model Comparison",
        xaxis_title="Strike",
        yaxis_title="Implied Volatility (%)",
        template="plotly_white",
        height=420,
        legend={"x": 0.02, "y": 0.98},
    )
    mo.ui.plotly(_fig)
    return


@app.cell(hide_code=True)
def cell_vol_oi_intro():
    """Introduce volume / open interest section."""
    mo.md(
        r"""
        ---
        ## 7 · Volume & Open Interest Passthrough

        Optional `volume` and `open_interest` arrays flow through the
        entire pipeline — from `OptionChain` through `filter()`,
        `to_smile_data()`, and
        `SmileData.transform()`.
        """
    )
    return


@app.cell(hide_code=True)
def cell_vol_oi_demo(chain):
    """Show volume / OI surviving the pipeline."""
    sd_with_vol = chain.to_smile_data()
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
    | `to_smile_data()` | {_vol(sd_with_vol)} | {_oi(sd_with_vol)} |
    | `transform(LogMoneyness, TotalVar)` | {_vol(sd_transformed)} | {_oi(sd_transformed)} |
    """
            ),
        ]
    )
    return


@app.cell(hide_code=True)
def cell_plot_intro():
    """Introduce the built-in plot method."""
    mo.md(
        r"""
        ---
        ## 8 · Built-in `SmileData.plot()`

        `SmileData` includes a matplotlib-based `.plot()` method that
        auto-labels axes from the current coordinate system.
        """
    )
    return


@app.cell(hide_code=True)
def cell_matplotlib_plot(sd_vols):
    """Use the built-in SmileData.plot() method."""
    fig = sd_vols.plot(title="Market Smile (matplotlib)")
    fig
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
        | Pricing | `black76_call / put / implied_vol` | European option pricing & inversion |
        | Load | `OptionChain(...)` | Stores bid/ask + auto-calibrates $F$, $D$ |
        | Clean | `.filter()` | 5-filter arbitrage removal |
        | Convert | `.to_smile_data()` | Delta-blended implied vols |
        | Transform | `.transform(x, y)` | Any $(X, Y)$ coordinate pair |
        | Fit | `fit(sd, SVIModel)` / `fit(sd, SABRModel)` | Parametric smile fit |
        | Ancillary | `volume`, `open_interest` | Optional data carried through pipeline |
        | Visualise | `.plot()` | Built-in matplotlib rendering |
        """
    )
    return


if __name__ == "__main__":
    app.run()
