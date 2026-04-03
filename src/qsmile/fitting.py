"""Backward-compatible re-export — use ``qsmile.models.fitting`` instead."""

from qsmile.models.fitting import SmileResult, fit_svi

__all__ = ["SmileResult", "fit_svi"]
