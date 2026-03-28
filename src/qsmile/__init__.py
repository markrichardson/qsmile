"""Quantitative Smile Modelling."""

from __future__ import annotations

from qsmile.black76 import black76_call, black76_implied_vol, black76_put
from qsmile.chain import OptionChain
from qsmile.fitting import SmileResult, fit_svi
from qsmile.prices import OptionChainPrices
from qsmile.svi import SVIParams, svi_implied_vol, svi_total_variance
from qsmile.unitised import UnitisedSpaceVols
from qsmile.vols import OptionChainVols

__version__ = "0.8.16"

__all__ = [
    "OptionChain",
    "OptionChainPrices",
    "OptionChainVols",
    "SVIParams",
    "SmileResult",
    "UnitisedSpaceVols",
    "black76_call",
    "black76_implied_vol",
    "black76_put",
    "fit_svi",
    "svi_implied_vol",
    "svi_total_variance",
]
