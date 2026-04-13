# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo==0.18.4",
#     "matplotlib>=3.8.0",
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
    vldta = chain_clean.to_vols()
    return (vldta,)


@app.cell
def _(vldta):
    _fig, _ax = plt.subplots(figsize=(10, 5))
    vldta.plot(ax=_ax)
    return


@app.cell
def _(SVIModel, fit, vldta):
    # fixed_strike_vols = chain.filter().to_vols()
    result = fit(vldta, model=SVIModel)
    model = result.model
    return (model,)


@app.cell
def _(XCoord, YCoord, model, vldta):
    _fig, _ax = plt.subplots(figsize=(10, 5))
    space = XCoord.StandardisedStrike, YCoord.TotalVariance
    space = XCoord.FixedStrike, YCoord.Volatility
    vldta.transform(*space).plot(ax=_ax)
    model.transform(*space).plot(ax=_ax)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
