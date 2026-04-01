# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo==0.18.4",
#     "numpy>=1.24.0",
#     "plotly>=5.18.0",
#     "pandas>=2.0.0",
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
    import marimo as mo
    import numpy as np
    import pandas as pd
    import plotly.graph_objects as go

    from qsmile import (
        OptionChainPrices,
        SVIParams,
        XCoord,
        YCoord,
        fit_svi,
        svi_implied_vol,
    )
    from qsmile.black76 import black76_call, black76_put


@app.cell(hide_code=True)
def cell_intro():
    """Render the notebook introduction."""
    mo.md(
        r"""
        # Option Chain Pipeline — From Prices to Smile Fit

        This notebook demonstrates the **qsmile** option chain pipeline:

        1. **`OptionChainPrices`** — raw bid/ask option prices, with forward & discount
           factor calibrated automatically from put-call parity
        2. **`SmileData`** — unified coordinate-labelled container with
           `.transform(x, y)` to freely move between strike/moneyness/log-moneyness/standardised
           X-coordinates and price/vol/variance/total-variance Y-coordinates
        3. **`fit_svi`** — SVI parametric smile fit

        $$
        \text{Prices} \xrightarrow{\texttt{to\_smile\_data()}} \text{SmileData}
        \xrightarrow{\texttt{transform()}} \text{any coords}
        \quad\big|\quad
        \text{SmileData} \xrightarrow{\texttt{fit\_svi()}} \text{SVI}
        $$
        """
    )
    return


@app.cell(hide_code=True)
def cell_market_intro():
    """Introduce the market data section."""
    mo.md(
        r"""
        ## Stage 0 — Synthetic Market Data

        We generate realistic bid/ask option prices from known SVI parameters
        so we can verify round-trip accuracy later. Bid/ask spreads widen
        monotonically for in-the-money options, reflecting real-world liquidity.
        """
    )
    return


@app.cell
def cell_market_data():
    """Generate synthetic bid/ask option prices."""
    # True parameters — we will try to recover these via SVI fit
    true_params = SVIParams(a=0.008, b=0.08, rho=-0.6, m=-0.02, sigma=0.10)
    forward = 100.0
    expiry = 0.5
    discount_factor = 0.98

    strikes = np.array([80, 85, 90, 95, 97.5, 100, 102.5, 105, 110, 115, 120], dtype=np.float64)
    k = np.log(strikes / forward)
    ivs_mid = svi_implied_vol(k, true_params, expiry)

    # Generate clean mid prices via Black76
    call_mid = black76_call(forward, strikes, discount_factor, ivs_mid, expiry)
    put_mid = black76_put(forward, strikes, discount_factor, ivs_mid, expiry)

    # Add a realistic spread: ITM options are wider (harder to hedge)
    # Calls are ITM for K < F, puts are ITM for K > F
    call_itm = np.maximum(forward - strikes, 0.0) / forward  # deeper ITM → larger
    put_itm = np.maximum(strikes - forward, 0.0) / forward
    call_spread_pct = 0.02 + 0.08 * call_itm  # 2% base, up to ~10% deep ITM
    put_spread_pct = 0.02 + 0.08 * put_itm
    call_spread = np.maximum(call_mid * call_spread_pct, 0.01)
    put_spread = np.maximum(put_mid * put_spread_pct, 0.01)

    call_bid = np.maximum(call_mid - call_spread / 2, 0.0)
    call_ask = call_mid + call_spread / 2
    put_bid = np.maximum(put_mid - put_spread / 2, 0.0)
    put_ask = put_mid + put_spread / 2
    return (
        call_ask,
        call_bid,
        discount_factor,
        expiry,
        forward,
        put_ask,
        put_bid,
        strikes,
        true_params,
    )


@app.cell(hide_code=True)
def cell_prices_intro():
    """Introduce the prices stage."""
    mo.md(
        r"""
        ## Stage 1 — `OptionChainPrices`

        Construct an `OptionChainPrices` from raw bid/ask prices. The forward
        and discount factor are **calibrated from put-call parity** using
        quasi-delta weighted least squares (we intentionally omit them to show
        the calibration in action).
        """
    )
    return


@app.cell
def cell_prices(call_ask, call_bid, expiry, put_ask, put_bid, strikes):
    """Build OptionChainPrices — forward/DF calibrated automatically."""
    prices = OptionChainPrices(
        strikes=strikes,
        call_bid=call_bid,
        call_ask=call_ask,
        put_bid=put_bid,
        put_ask=put_ask,
        expiry=expiry,
        # forward and discount_factor omitted → calibrated from put-call parity
    )
    return (prices,)


@app.cell(hide_code=True)
def cell_prices_result(discount_factor, forward, prices):
    """Display calibrated forward/DF and compare to true values."""
    df_prices = pd.DataFrame(
        {
            "Strike": prices.strikes,
            "Call Bid": prices.call_bid.round(4),
            "Call Ask": prices.call_ask.round(4),
            "Put Bid": prices.put_bid.round(4),
            "Put Ask": prices.put_ask.round(4),
        }
    )
    mo.vstack(
        [
            mo.md("### Calibrated Forward & Discount Factor"),
            mo.md(
                f"""
    | Quantity | Calibrated | True |
    |----------|-----------|------|
    | Forward  | {prices.forward:.4f} | {forward:.4f} |
    | Discount Factor | {prices.discount_factor:.4f} | {discount_factor:.4f} |
    """
            ),
            mo.md("### Price Data"),
            mo.ui.table(df_prices),
        ]
    )
    return


@app.cell(hide_code=True)
def cell_prices_plot(prices):
    """Plot bid/ask prices."""
    _fig = go.Figure()
    _fig.add_trace(
        go.Scatter(
            x=prices.strikes,
            y=prices.call_mid,
            mode="markers+lines",
            error_y={
                "type": "data",
                "symmetric": False,
                "array": (prices.call_ask - prices.call_mid).tolist(),
                "arrayminus": (prices.call_mid - prices.call_bid).tolist(),
            },
            name="Calls",
            marker={"color": "#2196F3"},
        )
    )
    _fig.add_trace(
        go.Scatter(
            x=prices.strikes,
            y=prices.put_mid,
            mode="markers+lines",
            error_y={
                "type": "data",
                "symmetric": False,
                "array": (prices.put_ask - prices.put_mid).tolist(),
                "arrayminus": (prices.put_mid - prices.put_bid).tolist(),
            },
            name="Puts",
            marker={"color": "#E74C3C"},
        )
    )
    _fig.update_layout(
        title="Stage 1: Bid/Ask Option Prices",
        xaxis_title="Strike",
        yaxis_title="Price",
        template="plotly_white",
        height=420,
        legend={"x": 0.02, "y": 0.98},
    )
    mo.ui.plotly(_fig)
    return


@app.cell(hide_code=True)
def cell_divider_1():
    """Section divider."""
    mo.md(r"""---""")
    return


@app.cell(hide_code=True)
def cell_transforms_intro():
    """Introduce the SmileData coordinate transforms section."""
    mo.md(
        r"""
        ## Stage 2 — `SmileData` & Coordinate Transforms

        Call `prices.to_smile_data()` to create a `SmileData` container in
        **(FixedStrike, Price)** coordinates. From there, `.transform(x, y)`
        moves freely between any combination of X and Y coordinates:

        | X-coordinate | Definition |
        |--------------|------------|
        | `FixedStrike` | $K$ |
        | `MoneynessStrike` | $K / F$ |
        | `LogMoneynessStrike` | $\ln(K / F)$ |
        | `StandardisedStrike` | $\ln(K / F) / (\sigma_{\mathrm{ATM}} \sqrt{T})$ |

        | Y-coordinate | Definition |
        |--------------|------------|
        | `Price` | Black76 option price |
        | `Volatility` | $\sigma$ |
        | `Variance` | $\sigma^2$ |
        | `TotalVariance` | $\sigma^2 T$ |
        """
    )
    return


@app.cell
def cell_smile_data(prices):
    """Create SmileData from OptionChainPrices and transform to vols."""
    sd_prices = prices.to_smile_data()
    sd = sd_prices.transform(XCoord.FixedStrike, YCoord.Volatility)
    return (sd,)


@app.cell(hide_code=True)
def cell_transforms_table(sd):
    """Show the original data and several coordinate views."""
    views = {
        "(FixedStrike, Vol)": sd,
        "(Moneyness, Vol)": sd.transform(XCoord.MoneynessStrike, YCoord.Volatility),
        "(LogMoneyness, TotalVar)": sd.transform(XCoord.LogMoneynessStrike, YCoord.TotalVariance),
        "(Standardised, TotalVar)": sd.transform(XCoord.StandardisedStrike, YCoord.TotalVariance),
        "(FixedStrike, Price)": sd.transform(XCoord.FixedStrike, YCoord.Price),
    }
    tables = []
    for label, v in views.items():
        df = pd.DataFrame(
            {
                "X": v.x.round(4),
                "Y Bid": v.y_bid.round(6),
                "Y Mid": v.y_mid.round(6),
                "Y Ask": v.y_ask.round(6),
            }
        )
        tables.append(mo.md(f"**{label}** — `x_coord={v.x_coord.name}`, `y_coord={v.y_coord.name}`"))
        tables.append(mo.ui.table(df))
    mo.vstack(tables)
    return


@app.cell(hide_code=True)
def cell_transforms_plot(sd):
    """Plot the same smile in four coordinate systems."""
    coords = [
        ("FixedStrike / Volatility", XCoord.FixedStrike, YCoord.Volatility, "Strike", "σ"),
        ("MoneynessStrike / Volatility", XCoord.MoneynessStrike, YCoord.Volatility, "K/F", "σ"),
        ("LogMoneynessStrike / TotalVariance", XCoord.LogMoneynessStrike, YCoord.TotalVariance, "ln(K/F)", "σ²T"),
        (
            "StandardisedStrike / TotalVariance",
            XCoord.StandardisedStrike,
            YCoord.TotalVariance,
            "k̃",
            "σ²T",
        ),
    ]
    from plotly.subplots import make_subplots

    _fig = make_subplots(rows=2, cols=2, subplot_titles=[c[0] for c in coords])
    colors = ["#2196F3", "#E74C3C", "#2FA4A9", "#9B59B6"]
    for idx, (title, xc, yc, xlabel, ylabel) in enumerate(coords):
        view = sd.transform(xc, yc)
        row, col = divmod(idx, 2)
        _fig.add_trace(
            go.Scatter(
                x=view.x,
                y=view.y_mid,
                mode="markers+lines",
                marker={"color": colors[idx], "size": 6},
                line={"color": colors[idx]},
                name=title,
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
        height=650,
    )
    mo.ui.plotly(_fig)
    return


@app.cell(hide_code=True)
def cell_roundtrip(sd):
    """Demonstrate round-trip fidelity."""
    # Go FixedStrike/Vol → Standardised/TotalVar → back
    there = sd.transform(XCoord.StandardisedStrike, YCoord.TotalVariance)
    back = there.transform(XCoord.FixedStrike, YCoord.Volatility)
    max_x_err = float(np.max(np.abs(back.x - sd.x)))
    max_y_err = float(np.max(np.abs(back.y_mid - sd.y_mid)))
    mo.md(
        f"""
    ### Round-Trip Fidelity

    Transform **FixedStrike / Volatility → StandardisedStrike / TotalVariance → back**:

    | Metric | Value |
    |--------|-------|
    | Max X error (strikes) | {max_x_err:.2e} |
    | Max Y error (mid vol) | {max_y_err:.2e} |

    Round-trip is exact to within floating-point precision.
    """
    )
    return


@app.cell(hide_code=True)
def cell_divider_3():
    """Section divider."""
    mo.md(r"""---""")
    return


@app.cell(hide_code=True)
def cell_svi_intro():
    """Introduce the SVI fitting stage."""
    mo.md(
        r"""
        ## Stage 3 — SVI Fit

        We pass the `SmileData` (in volatility coordinates) directly to `fit_svi`,
        which transforms to log-moneyness / total-variance internally.
        The fitted SVI curve is overlaid on the market data.
        """
    )
    return


@app.cell
def cell_svi_fit(sd):
    """Fit SVI directly from SmileData."""
    result = fit_svi(sd)
    p = result.params
    return p, result


@app.cell(hide_code=True)
def cell_svi_params(p, result, true_params):
    """Display fitted vs true SVI parameters."""
    tp = true_params
    mo.vstack(
        [
            mo.md("### Fitted vs True SVI Parameters"),
            mo.md(
                f"""
    | Parameter | Fitted | True | Δ |
    |-----------|--------|------|---|
    | $a$ | {p.a:.6f} | {tp.a:.6f} | {p.a - tp.a:+.6f} |
    | $b$ | {p.b:.6f} | {tp.b:.6f} | {p.b - tp.b:+.6f} |
    | $\\rho$ | {p.rho:.6f} | {tp.rho:.6f} | {p.rho - tp.rho:+.6f} |
    | $m$ | {p.m:.6f} | {tp.m:.6f} | {p.m - tp.m:+.6f} |
    | $\\sigma$ | {p.sigma:.6f} | {tp.sigma:.6f} | {p.sigma - tp.sigma:+.6f} |

    **RMSE:** {result.rmse:.2e} &nbsp;&nbsp; **Converged:** {"Yes" if result.success else "No"}
    """
            ),
        ]
    )
    return


@app.cell(hide_code=True)
def cell_svi_plot(forward, expiry, result, sd):
    """Plot market vols with SVI fitted curve in strike space."""
    _strikes_fine = np.linspace(sd.x.min() - 5, sd.x.max() + 5, 200)
    _k_fine = np.log(_strikes_fine / forward)
    _iv_fitted = svi_implied_vol(_k_fine, result.params, expiry)

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
            marker={"size": 9, "color": "#E74C3C"},
            name="Market (bid/ask)",
        )
    )
    _fig.add_trace(
        go.Scatter(
            x=_strikes_fine,
            y=_iv_fitted * 100,
            mode="lines",
            line={"color": "#2FA4A9", "width": 2.5},
            name="SVI Fit",
        )
    )
    _fig.update_layout(
        title="Market Implied Vols vs SVI Fit",
        xaxis_title="Strike",
        yaxis_title="Implied Volatility (%)",
        template="plotly_white",
        height=450,
        legend={"x": 0.02, "y": 0.98},
    )
    mo.ui.plotly(_fig)
    return


@app.cell(hide_code=True)
def cell_divider_4():
    """Section divider."""
    mo.md(r"""---""")
    return


@app.cell(hide_code=True)
def cell_summary():
    """Render the conclusion."""
    mo.md(
        r"""
        ## Summary

        This notebook demonstrated the **qsmile** option chain pipeline:

        | Step | Class | Method |
        |------|-------|--------|
        | Raw prices with bid/ask | `OptionChainPrices` | *constructor* — auto-calibrates F, D |
        | → Any coordinate system | `SmileData` | `.to_smile_data().transform(x, y)` |
        | → SVI smile fit | `SmileResult` | `fit_svi(sd)` |

        The **coordinate transform framework** lets you freely move between
        any combination of X-coordinates (Strike, Moneyness, Log-Moneyness,
        Standardised) and Y-coordinates (Price, Volatility, Variance, Total
        Variance) via composable, invertible maps.
        """
    )
    return


if __name__ == "__main__":
    app.run()
