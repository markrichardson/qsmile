"""Bid/ask option price chain with forward/DF calibration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import cvxpy as cp
import numpy as np
from numpy.typing import NDArray

from qsmile.black76 import black76_implied_vol

if TYPE_CHECKING:
    import matplotlib.figure

    from qsmile.vols import OptionChainVols


def _calibrate_forward_df(
    strikes: NDArray[np.float64],
    call_mid: NDArray[np.float64],
    put_mid: NDArray[np.float64],
) -> tuple[float, float]:
    """Calibrate forward and discount factor from put-call parity.

    Fits C_mid - P_mid = D * (F - K) using quasi-delta weighted least squares.
    The weighting approximates |D(1-D)| by a Gaussian centred at ATM whose
    width is inferred from the ATM call price via the Brenner-Subrahmanyam
    approximation, giving a characteristic strike-space scale of F0*sigma0*sqrt(T).

    Parameters
    ----------
    strikes : NDArray
        Strike prices.
    call_mid : NDArray
        Mid call prices.
    put_mid : NDArray
        Mid put prices.

    Returns:
    -------
    tuple[float, float]
        (forward, discount_factor)
    """
    y = call_mid - put_mid  # C - P = D*(F - K) = D*F - D*K

    # Initial forward estimate: strike where |C-P| is smallest
    atm_idx = int(np.argmin(np.abs(y)))
    f0 = float(strikes[atm_idx])

    # Quasi-delta weights: Gaussian width inferred from ATM call price
    # Brenner-Subrahmanyam: C_ATM ~ F*sigma*sqrt(T) / sqrt(2*pi)  (assuming D~1)
    # => sigma0 ~ C_ATM * sqrt(2*pi) / (F0*sqrt(T)) -- but we don't know T here,
    # so we use the strike-space width h = C_ATM * sqrt(2*pi) directly,
    # which equals F0*sigma0*sqrt(T) (the natural delta scale).
    c_atm = float(call_mid[atm_idx])
    h = c_atm * np.sqrt(2 * np.pi)
    # Guard against degenerate case (e.g. very deep ITM/OTM ATM estimate)
    h = max(h, 1e-8 * f0)
    weights = np.exp(-0.5 * ((strikes - f0) / h) ** 2)
    W = np.diag(np.sqrt(weights))

    # Variables: D*F and D (so the problem is linear)
    df = cp.Variable(pos=True, name="D")  # discount factor
    df_times_f = cp.Variable(pos=True, name="DF")  # D * F

    # y_i = D*F - D*K_i for each strike
    residuals = y - (df_times_f - df * strikes)
    objective = cp.Minimize(cp.sum_squares(W @ residuals))

    prob = cp.Problem(objective, [df <= 1.0])
    prob.solve(solver=cp.CLARABEL)

    if df.value is None or df_times_f.value is None:
        msg = "put-call parity calibration failed to converge"
        raise RuntimeError(msg)

    D_val = float(df.value)
    F_val = float(df_times_f.value) / D_val

    return F_val, D_val


@dataclass
class OptionChainPrices:
    """Bid/ask option price chain for a single expiry.

    Parameters
    ----------
    strikes : NDArray[np.float64]
        Strike prices. Must be positive.
    call_bid : NDArray[np.float64]
        Call bid prices. Must be non-negative.
    call_ask : NDArray[np.float64]
        Call ask prices. Must be >= call_bid.
    put_bid : NDArray[np.float64]
        Put bid prices. Must be non-negative.
    put_ask : NDArray[np.float64]
        Put ask prices. Must be >= put_bid.
    expiry : float
        Time to expiry in years. Must be positive.
    forward : float | None
        Forward price. Calibrated from put-call parity if not provided.
    discount_factor : float | None
        Discount factor. Calibrated from put-call parity if not provided.
    """

    strikes: NDArray[np.float64]
    call_bid: NDArray[np.float64]
    call_ask: NDArray[np.float64]
    put_bid: NDArray[np.float64]
    put_ask: NDArray[np.float64]
    expiry: float
    forward: float | None = field(default=None)
    discount_factor: float | None = field(default=None)

    def __post_init__(self) -> None:
        """Validate and convert inputs, calibrate forward/DF if needed."""
        self.strikes = np.asarray(self.strikes, dtype=np.float64)
        self.call_bid = np.asarray(self.call_bid, dtype=np.float64)
        self.call_ask = np.asarray(self.call_ask, dtype=np.float64)
        self.put_bid = np.asarray(self.put_bid, dtype=np.float64)
        self.put_ask = np.asarray(self.put_ask, dtype=np.float64)

        n = len(self.strikes)
        for name, arr in [
            ("call_bid", self.call_bid),
            ("call_ask", self.call_ask),
            ("put_bid", self.put_bid),
            ("put_ask", self.put_ask),
        ]:
            if len(arr) != n:
                msg = f"{name} must have the same length as strikes ({n}), got {len(arr)}"
                raise ValueError(msg)

        if n < 3:
            msg = f"at least 3 strikes required, got {n}"
            raise ValueError(msg)
        if np.any(self.strikes <= 0):
            msg = "all strikes must be positive"
            raise ValueError(msg)
        if self.expiry <= 0:
            msg = f"expiry must be positive, got {self.expiry}"
            raise ValueError(msg)

        for name, arr in [
            ("call_bid", self.call_bid),
            ("call_ask", self.call_ask),
            ("put_bid", self.put_bid),
            ("put_ask", self.put_ask),
        ]:
            if np.any(arr < 0):
                msg = f"{name} must be non-negative"
                raise ValueError(msg)

        if np.any(self.call_bid > self.call_ask):
            msg = "call_bid must not exceed call_ask"
            raise ValueError(msg)
        if np.any(self.put_bid > self.put_ask):
            msg = "put_bid must not exceed put_ask"
            raise ValueError(msg)

        # Calibrate forward and discount factor if not provided
        if self.forward is None or self.discount_factor is None:
            f_cal, d_cal = _calibrate_forward_df(self.strikes, self.call_mid, self.put_mid)
            if self.forward is None:
                self.forward = f_cal
            if self.discount_factor is None:
                self.discount_factor = d_cal

    @property
    def call_mid(self) -> NDArray[np.float64]:
        """Midpoint of call bid and ask prices."""
        return (self.call_bid + self.call_ask) / 2.0

    @property
    def put_mid(self) -> NDArray[np.float64]:
        """Midpoint of put bid and ask prices."""
        return (self.put_bid + self.put_ask) / 2.0

    def to_vols(self) -> OptionChainVols:
        """Convert prices to implied volatilities via Black76 inversion."""
        from qsmile.vols import OptionChainVols

        assert self.forward is not None  # noqa: S101
        assert self.discount_factor is not None  # noqa: S101

        n = len(self.strikes)
        vol_bid = np.empty(n)
        vol_ask = np.empty(n)

        for i in range(n):
            K = float(self.strikes[i])
            # Use call for strikes >= forward, put otherwise (more numerically stable)
            use_call = self.forward <= K

            vol_bid[i] = black76_implied_vol(
                float(self.call_bid[i] if use_call else self.put_bid[i]),
                self.forward,
                K,
                self.discount_factor,
                self.expiry,
                is_call=use_call,
            )
            vol_ask[i] = black76_implied_vol(
                float(self.call_ask[i] if use_call else self.put_ask[i]),
                self.forward,
                K,
                self.discount_factor,
                self.expiry,
                is_call=use_call,
            )

        return OptionChainVols(
            strikes=self.strikes.copy(),
            vol_bid=vol_bid,
            vol_ask=vol_ask,
            forward=self.forward,
            discount_factor=self.discount_factor,
            expiry=self.expiry,
        )

    def plot(self, *, title: str = "Option Chain Prices") -> matplotlib.figure.Figure:
        """Plot bid/ask prices as error bars for calls and puts."""
        from qsmile.plot import _require_matplotlib, plot_bid_ask

        _require_matplotlib()
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots()
        plot_bid_ask(
            self.strikes,
            self.call_mid,
            self.call_bid,
            self.call_ask,
            label="Calls",
            color="tab:blue",
            ax=ax,
        )
        plot_bid_ask(
            self.strikes,
            self.put_mid,
            self.put_bid,
            self.put_ask,
            label="Puts",
            color="tab:red",
            ax=ax,
        )
        ax.set_xlabel("Strike")
        ax.set_ylabel("Price")
        ax.set_title(title)
        ax.legend()
        return fig
