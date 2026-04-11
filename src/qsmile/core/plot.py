"""Plotting utilities for option chain representations."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import matplotlib.figure


def _require_matplotlib():
    """Import matplotlib or raise a helpful error."""
    try:
        import matplotlib as mpl  # noqa: F401
    except ImportError:
        msg = "matplotlib is required for plotting. Install it with: pip install qsmile[plot]"
        raise ImportError(msg) from None


def plot_bid_ask(
    x,
    mid,
    lower,
    upper,
    *,
    xlabel: str = "",
    ylabel: str = "",
    title: str = "",
    label: str | None = None,
    color: str | None = None,
    fmt: str = "none",
    ax=None,
) -> matplotlib.figure.Figure:
    """Plot bid/ask as error bars around mid values.

    Parameters
    ----------
    x : array-like
        X-axis values (e.g., strikes or unitised k).
    mid : array-like
        Mid values.
    lower : array-like
        Lower bound (bid).
    upper : array-like
        Upper bound (ask).
    xlabel, ylabel, title : str
        Axis labels and title.
    label : str, optional
        Legend label.
    color : str, optional
        Color for the series.
    ax : matplotlib Axes, optional
        Axes to plot on. If None, creates a new figure.

    Returns:
    -------
    matplotlib.figure.Figure
    """
    _require_matplotlib()
    import matplotlib.pyplot as plt
    import numpy as np

    x = np.asarray(x)
    mid = np.asarray(mid)
    lower = np.asarray(lower)
    upper = np.asarray(upper)

    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.get_figure()

    yerr_lower = mid - lower
    yerr_upper = upper - mid

    ax.errorbar(x, mid, yerr=[yerr_lower, yerr_upper], fmt=fmt, capsize=3, label=label, color=color)

    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    if label:
        ax.legend()
    ax.grid(True, alpha=0.3)

    return fig


def plot_line(
    x,
    y,
    *,
    xlabel: str = "",
    ylabel: str = "",
    title: str = "",
    label: str | None = None,
    color: str | None = None,
    ax=None,
) -> matplotlib.figure.Figure:
    """Plot a single curve.

    Parameters
    ----------
    x : array-like
        X-axis values.
    y : array-like
        Y-axis values.
    xlabel, ylabel, title : str
        Axis labels and title.
    label : str, optional
        Legend label.
    color : str, optional
        Color for the line.
    ax : matplotlib Axes, optional
        Axes to plot on. If None, creates a new figure.

    Returns:
    -------
    matplotlib.figure.Figure
    """
    _require_matplotlib()
    import matplotlib.pyplot as plt
    import numpy as np

    x = np.asarray(x)
    y = np.asarray(y)

    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.get_figure()

    ax.plot(x, y, label=label, color=color)

    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    if label:
        ax.legend()
    ax.grid(True, alpha=0.3)

    return fig
