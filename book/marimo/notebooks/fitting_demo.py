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
    import matplotlib.pyplot as plt


@app.cell
def _():
    from qsmile import SampleDataReader, SVIModel, XCoord, YCoord, fit

    reader = SampleDataReader()
    return SVIModel, XCoord, YCoord, fit, reader


@app.cell
def _(reader):
    chain_dirty = reader.get_chain("SPX", "2026-04-03", "2026-06-30")
    chain_dirty
    return (chain_dirty,)


@app.cell
def _(chain_dirty):
    chain_clean = chain_dirty.filter()
    chain_clean
    return (chain_clean,)


@app.cell
def _(chain_clean):
    _fig, _ax = plt.subplots(figsize=(10, 5))
    chain_clean.plot(ax=_ax)
    return


@app.cell
def _(chain_clean):
    fixed_strike_vols = chain_clean.to_vols()
    return (fixed_strike_vols,)


@app.cell
def _(fixed_strike_vols):
    _fig, _ax = plt.subplots(figsize=(10, 5))
    fixed_strike_vols.plot(ax=_ax)
    return


@app.cell
def _(SVIModel, fit, fixed_strike_vols):
    # fixed_strike_vols = chain.filter().to_vols()
    result = fit(fixed_strike_vols, model=SVIModel)
    return (result,)


@app.cell
def _(XCoord, YCoord, fixed_strike_vols, result):
    _fig, _ax = plt.subplots(figsize=(10, 5))
    fixed_strike_vols.plot(ax=_ax)
    result.model.transform(XCoord.FixedStrike, YCoord.Volatility).plot(ax=_ax, std_range=[-5, 2])
    return


@app.cell
def _(result):
    result.model.metadata
    return


if __name__ == "__main__":
    app.run()
