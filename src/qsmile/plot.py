"""Backward-compatible re-export — use ``qsmile.core.plot`` instead."""

from qsmile.core.plot import _require_matplotlib, plot_bid_ask

__all__ = ["_require_matplotlib", "plot_bid_ask"]
