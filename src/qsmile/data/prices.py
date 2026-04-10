"""Bid/ask option price chain with forward/DF calibration."""

from __future__ import annotations

import contextlib
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

import cvxpy as cp
import numpy as np
from numpy.typing import NDArray
from scipy.stats import norm

from qsmile.data.meta import SmileMetadata
from qsmile.data.strikes import StrikeArray

if TYPE_CHECKING:
    import matplotlib.figure

    from qsmile.data.vols import SmileData


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


def delta_blend_ivols(
    call_bid_ivols: NDArray[np.float64],
    call_ask_ivols: NDArray[np.float64],
    put_bid_ivols: NDArray[np.float64],
    put_ask_ivols: NDArray[np.float64],
    strikes: NDArray[np.float64],
    forward: float,
    expiry: float,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Blend call and put implied vols using Black76 undiscounted call-delta weights.

    At each strike K, the blending weight is w(K) = Phi(d1) where
    d1 = [ln(F/K) + 0.5 * sigma_C^2 * t] / (sigma_C * sqrt(t))
    and sigma_C is the mid call-implied vol at that strike.

    The blended vol is: sigma = w * sigma_C + (1 - w) * sigma_P.
    Bid and ask are blended independently with the same weights.

    NaN values in input vols indicate inversion failures. At such strikes
    the blended vol falls back to the available option type. If neither
    is available, the strike is excluded (NaN in output).

    Parameters
    ----------
    call_bid_ivols : NDArray[np.float64]
        Call-implied bid vols (NaN where inversion failed).
    call_ask_ivols : NDArray[np.float64]
        Call-implied ask vols (NaN where inversion failed).
    put_bid_ivols : NDArray[np.float64]
        Put-implied bid vols (NaN where inversion failed).
    put_ask_ivols : NDArray[np.float64]
        Put-implied ask vols (NaN where inversion failed).
    strikes : NDArray[np.float64]
        Strike prices.
    forward : float
        Forward price.
    expiry : float
        Time to expiry in years.

    Returns:
    -------
    tuple[NDArray[np.float64], NDArray[np.float64]]
        (blended_bid_ivols, blended_ask_ivols). Strikes where neither
        call nor put vol is available will have NaN.
    """
    call_mid = (call_bid_ivols + call_ask_ivols) / 2.0
    sqrt_t = np.sqrt(expiry)

    # Compute delta weights from call mid vol
    # Where call vol is NaN, use put mid vol for delta calc; if both NaN, weight = NaN
    put_mid = (put_bid_ivols + put_ask_ivols) / 2.0
    sigma_for_delta = np.where(np.isnan(call_mid), put_mid, call_mid)
    safe_sigma = np.where(np.isnan(sigma_for_delta), 1.0, sigma_for_delta)
    safe_sigma = np.where(safe_sigma <= 0, 1e-8, safe_sigma)

    d1 = (np.log(forward / strikes) + 0.5 * safe_sigma**2 * expiry) / (safe_sigma * sqrt_t)
    w = norm.cdf(d1)

    # Mask NaN vols: if call is NaN, force weight to 0 (use put); if put is NaN, force to 1 (use call)
    call_available = ~np.isnan(call_bid_ivols)
    put_available = ~np.isnan(put_bid_ivols)

    # Both missing → NaN
    neither = ~call_available & ~put_available
    w = np.where(call_available & ~put_available, 1.0, w)
    w = np.where(~call_available & put_available, 0.0, w)
    w = np.where(neither, np.nan, w)

    # Replace NaN vols with 0 for arithmetic (masked by weight)
    cb = np.where(np.isnan(call_bid_ivols), 0.0, call_bid_ivols)
    ca = np.where(np.isnan(call_ask_ivols), 0.0, call_ask_ivols)
    pb = np.where(np.isnan(put_bid_ivols), 0.0, put_bid_ivols)
    pa = np.where(np.isnan(put_ask_ivols), 0.0, put_ask_ivols)

    blended_bid = w * cb + (1.0 - w) * pb
    blended_ask = w * ca + (1.0 - w) * pa

    return blended_bid, blended_ask


@dataclass
class OptionChain:
    """Bid/ask option price chain for a single expiry.

    Parameters
    ----------
    strikedata : StrikeArray
        Strike-indexed columnar data containing at least ``call_bid``,
        ``call_ask``, ``put_bid``, and ``put_ask`` columns.
        Optional ``volume`` and ``open_interest`` columns are supported.
    metadata : SmileMetadata
        Smile metadata. ``expiry`` must be provided.
        ``forward`` and ``discount_factor`` are calibrated from
        put-call parity if ``None``.
    """

    strikedata: StrikeArray
    metadata: SmileMetadata

    def __post_init__(self) -> None:
        """Validate inputs and calibrate forward/DF if needed."""
        sd = self.strikedata
        strikes = sd.strikes
        n = len(strikes)

        if n < 3:
            msg = f"at least 3 strikes required, got {n}"
            raise ValueError(msg)
        if np.any(strikes <= 0):
            msg = "all strikes must be positive"
            raise ValueError(msg)

        for key in (("call", "bid"), ("call", "ask"), ("put", "bid"), ("put", "ask")):
            arr = sd.get_values(key)
            if arr is not None and np.any(arr < 0):
                msg = f"{key[0]}_{key[1]} must be non-negative"
                raise ValueError(msg)

        call_bid = sd.get_values(("call", "bid"))
        call_ask = sd.get_values(("call", "ask"))
        put_bid = sd.get_values(("put", "bid"))
        put_ask = sd.get_values(("put", "ask"))

        if call_bid is not None and call_ask is not None and np.any(call_bid > call_ask):
            msg = "call_bid must not exceed call_ask"
            raise ValueError(msg)
        if put_bid is not None and put_ask is not None and np.any(put_bid > put_ask):
            msg = "put_bid must not exceed put_ask"
            raise ValueError(msg)

        for key in (("meta", "volume"), ("meta", "open_interest")):
            arr = sd.get_values(key)
            if arr is not None and np.any(arr < 0):
                msg = f"{key[1]} must be non-negative"
                raise ValueError(msg)

        # Calibrate forward and discount factor if not provided
        meta = self.metadata
        if meta.forward is None or meta.discount_factor is None:
            f_cal, d_cal = _calibrate_forward_df(strikes, self.call_mid, self.put_mid)
            self.metadata = replace(
                meta,
                forward=meta.forward if meta.forward is not None else f_cal,
                discount_factor=meta.discount_factor if meta.discount_factor is not None else d_cal,
            )

    # ── convenience accessors ─────────────────────────────────────

    @property
    def strikes(self) -> NDArray[np.float64]:
        """Strike prices."""
        return self.strikedata.strikes

    @property
    def call_bid(self) -> NDArray[np.float64]:
        """Call bid prices."""
        return self.strikedata.values(("call", "bid"))

    @property
    def call_ask(self) -> NDArray[np.float64]:
        """Call ask prices."""
        return self.strikedata.values(("call", "ask"))

    @property
    def put_bid(self) -> NDArray[np.float64]:
        """Put bid prices."""
        return self.strikedata.values(("put", "bid"))

    @property
    def put_ask(self) -> NDArray[np.float64]:
        """Put ask prices."""
        return self.strikedata.values(("put", "ask"))

    @property
    def volume(self) -> NDArray[np.float64] | None:
        """Per-strike traded volume, or None."""
        return self.strikedata.get_values(("meta", "volume"))

    @property
    def open_interest(self) -> NDArray[np.float64] | None:
        """Per-strike open interest, or None."""
        return self.strikedata.get_values(("meta", "open_interest"))

    @property
    def call_mid(self) -> NDArray[np.float64]:
        """Midpoint of call bid and ask prices."""
        return (self.call_bid + self.call_ask) / 2.0

    @property
    def put_mid(self) -> NDArray[np.float64]:
        """Midpoint of put bid and ask prices."""
        return (self.put_bid + self.put_ask) / 2.0

    def to_smile_data(self) -> SmileData:
        """Convert to a SmileData with (FixedStrike, Volatility) using delta-blended vols.

        Inverts both call and put prices to implied vols at every strike, then
        blends them using Black76 undiscounted call-delta weights. OTM options
        dominate in each wing; ATM is approximately equal-weighted.

        Strikes where neither call nor put vol can be computed are excluded.
        """
        from qsmile.core.black76 import black76_implied_vol
        from qsmile.core.coords import XCoord, YCoord
        from qsmile.data.vols import SmileData

        meta = self.metadata
        if meta.forward is None or meta.discount_factor is None:
            msg = "forward and discount_factor must be calibrated before to_smile_data()"
            raise TypeError(msg)

        n = len(self.strikes)

        # Invert call and put prices to implied vols (NaN on failure)
        call_bid_iv = np.full(n, np.nan)
        call_ask_iv = np.full(n, np.nan)
        put_bid_iv = np.full(n, np.nan)
        put_ask_iv = np.full(n, np.nan)

        for i in range(n):
            k = float(self.strikes[i])
            with contextlib.suppress(ValueError):
                call_bid_iv[i] = black76_implied_vol(
                    float(self.call_bid[i]), meta.forward, k, meta.discount_factor, meta.texpiry, is_call=True
                )
            with contextlib.suppress(ValueError):
                call_ask_iv[i] = black76_implied_vol(
                    float(self.call_ask[i]), meta.forward, k, meta.discount_factor, meta.texpiry, is_call=True
                )
            with contextlib.suppress(ValueError):
                put_bid_iv[i] = black76_implied_vol(
                    float(self.put_bid[i]), meta.forward, k, meta.discount_factor, meta.texpiry, is_call=False
                )
            with contextlib.suppress(ValueError):
                put_ask_iv[i] = black76_implied_vol(
                    float(self.put_ask[i]), meta.forward, k, meta.discount_factor, meta.texpiry, is_call=False
                )

        # Blend using delta weights
        blended_bid, blended_ask = delta_blend_ivols(
            call_bid_iv,
            call_ask_iv,
            put_bid_iv,
            put_ask_iv,
            self.strikes,
            meta.forward,
            meta.texpiry,
        )

        # Exclude strikes where neither vol is available
        valid = ~np.isnan(blended_bid) & ~np.isnan(blended_ask)
        strikes_out = self.strikes[valid]
        bid_out = blended_bid[valid]
        ask_out = blended_ask[valid]

        # Derive sigma_atm from blended mid at ATM strike
        mid_out = (bid_out + ask_out) / 2.0
        atm_idx = int(np.argmin(np.abs(strikes_out - meta.forward)))
        sigma_atm = float(mid_out[atm_idx])

        import pandas as pd

        sa = StrikeArray()
        idx = pd.Index(strikes_out, dtype=np.float64)
        sa.set(("y", "bid"), pd.Series(bid_out, index=idx))
        sa.set(("y", "ask"), pd.Series(ask_out, index=idx))
        if self.volume is not None:
            sa.set(("meta", "volume"), pd.Series(self.volume[valid], index=idx))
        if self.open_interest is not None:
            sa.set(("meta", "open_interest"), pd.Series(self.open_interest[valid], index=idx))

        return SmileData(
            strikearray=sa,
            x_coord=XCoord.FixedStrike,
            y_coord=YCoord.Volatility,
            metadata=replace(meta, sigma_atm=sigma_atm),
        )

    def filter(self) -> OptionChain:
        """Return a cleaned copy with stale and implausible quotes removed.

        Applies five filters in sequence:

        1. **Zero-bid filter** -- removes strikes where either the call or put
           bid is zero (no genuine two-sided market).
        2. **Put-call parity monotonicity** -- C_mid - P_mid must be strictly
           decreasing in strike (since it equals D*(F - K)).  Strikes that
           break monotonicity carry stale or mismarked quotes and are dropped.
        3. **Call- and put-mid monotonicity** -- call mids must be non-increasing
           and put mids non-decreasing in strike.  Any remaining violations are
           removed.
        4. **Sub-intrinsic filter** -- removes strikes where the call or put
           **bid** falls below intrinsic value (using the calibrated forward),
           which indicates illiquid deep-ITM or stale quotes.
        5. **Parity residual filter** -- removes strikes where the put-call
           parity residual |C_mid - P_mid - D*(F - K)| exceeds 3x the
           combined half bid-ask spread, indicating a stale or mispriced
           deep-ITM quote.

        Returns:
        -------
        OptionChain
            A new ``OptionChain`` with the noisy strikes removed and
            ``forward`` / ``discount_factor`` re-calibrated on the clean data.
        """
        keep = np.ones(len(self.strikes), dtype=bool)

        # 1. Both sides must quote a positive bid
        keep &= self.call_bid > 0
        keep &= self.put_bid > 0

        # Work on the surviving subset for the monotonicity checks
        def _non_monotone_mask(values: NDArray[np.float64], decreasing: bool) -> NDArray[np.bool_]:
            """Return a mask (True = keep) that removes non-monotone points.

            Iteratively drops the point at each violation until the sequence
            is monotone, working from the largest violation first.
            """
            mask = np.ones(len(values), dtype=bool)
            while True:
                vals = values[mask]
                diff = np.diff(vals)
                bad = diff > 0 if decreasing else diff < 0
                if not np.any(bad):
                    break
                # Find the worst violation in the filtered view
                magnitudes = np.abs(diff) * bad
                worst_idx = int(np.argmax(magnitudes))
                # Map back to the full-array index and remove the point
                # (remove the second element of the pair that violates)
                full_indices = np.where(mask)[0]
                mask[full_indices[worst_idx + 1]] = False
            return mask

        # 2. Put-call parity: C_mid - P_mid must be strictly decreasing
        parity = self.call_mid[keep] - self.put_mid[keep]
        parity_keep = _non_monotone_mask(parity, decreasing=True)
        keep_indices = np.where(keep)[0]
        keep[keep_indices[~parity_keep]] = False

        # 3a. Call mids must be non-increasing in strike
        call_keep = _non_monotone_mask(self.call_mid[keep], decreasing=True)
        keep_indices = np.where(keep)[0]
        keep[keep_indices[~call_keep]] = False

        # 3b. Put mids must be non-decreasing in strike
        put_keep = _non_monotone_mask(self.put_mid[keep], decreasing=False)
        keep_indices = np.where(keep)[0]
        keep[keep_indices[~put_keep]] = False

        # 4. Sub-intrinsic filter: calibrate F on clean data, then remove
        #    strikes where the bid price is below intrinsic value
        clean_strikes = self.strikes[keep]
        clean_c_mid = self.call_mid[keep]
        clean_p_mid = self.put_mid[keep]
        f_est, d_est = _calibrate_forward_df(clean_strikes, clean_c_mid, clean_p_mid)
        call_intrinsic = d_est * np.maximum(f_est - clean_strikes, 0.0)
        put_intrinsic = d_est * np.maximum(clean_strikes - f_est, 0.0)
        intrinsic_ok = (self.call_bid[keep] >= call_intrinsic) & (self.put_bid[keep] >= put_intrinsic)
        keep_indices = np.where(keep)[0]
        keep[keep_indices[~intrinsic_ok]] = False

        # 5. Parity residual filter (iterative): |C-P - D*(F-K)| must be
        #    within a small multiple of the combined half bid-ask spread.
        #    Iteratively remove the worst outlier and recalibrate F/DF,
        #    since a single stale deep-ITM quote can bias the calibration.
        while np.sum(keep) >= 3:
            ks = self.strikes[keep]
            cm = self.call_mid[keep]
            pm = self.put_mid[keep]
            f_est, d_est = _calibrate_forward_df(ks, cm, pm)
            parity_actual = cm - pm
            parity_predicted = d_est * (f_est - ks)
            half_spread = (
                (self.call_ask[keep] - self.call_bid[keep]) + (self.put_ask[keep] - self.put_bid[keep])
            ) / 2.0
            ratio = np.abs(parity_actual - parity_predicted) / np.maximum(half_spread, 1e-10)
            worst = int(np.argmax(ratio))
            if ratio[worst] <= 3.0:
                break
            keep_indices = np.where(keep)[0]
            keep[keep_indices[worst]] = False

        filtered_sd = self.strikedata.filter(keep)
        return OptionChain(
            strikedata=filtered_sd,
            metadata=SmileMetadata(
                date=self.metadata.date, expiry=self.metadata.expiry, daycount=self.metadata.daycount
            ),
        )

    def plot(self, *, title: str = "Option Chain Prices") -> matplotlib.figure.Figure:
        """Plot bid/ask prices as error bars for calls and puts."""
        from qsmile.core.plot import _require_matplotlib, plot_bid_ask

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
