"""Load option chain data from parquet files."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import numpy as np
import pandas as pd

from qsmile.data.meta import SmileMetadata
from qsmile.data.prices import OptionChain
from qsmile.data.strikes import StrikeArray

_CHAINS_COLS = ["strike", "bid", "ask", "volume", "openInterest"]


class SampleDataReader:
    """Read option chain parquet files from a directory.

    Parameters
    ----------
    root : str | Path | None
        Directory containing ``chains/*.parquet`` files.
        Defaults to ``<project_root>/parquet``.
    """

    def __init__(self, root: str | Path | None = None) -> None:
        """Create a reader backed by a parquet directory.

        Parameters
        ----------
        root : str | Path | None
            Directory containing ``chains/*.parquet`` files.
            Defaults to ``<project_root>/parquet``.
        """
        if root is None:
            root = Path(__file__).resolve().parent.parent.parent.parent / "parquet"
        self._root = Path(root)

    def get_chain(
        self,
        underlying: str,
        fetch_date: str,
        expiry_date: str,
    ) -> OptionChain:
        """Load an option chain from parquet and return an ``OptionChain``.

        Parameters
        ----------
        underlying : str
            Ticker symbol, e.g. ``"SPX"``.
        fetch_date : str
            Fetch / pricing date in ``YYYY-MM-DD`` format.
        expiry_date : str
            Expiry date in ``YYYY-MM-DD`` format.

        Returns:
        -------
        OptionChain
            Fully constructed option chain with metadata and strike data.
        """
        path = self._resolve_path(underlying, fetch_date, expiry_date)
        df_raw = pd.read_parquet(path)
        return self._build_chain(df_raw)

    # ------------------------------------------------------------------

    def _resolve_path(
        self,
        underlying: str,
        fetch_date: str,
        expiry_date: str,
    ) -> Path:
        """Resolve the parquet file path for given parameters.

        Parameters
        ----------
        underlying : str
            Ticker symbol.
        fetch_date : str
            Fetch date in YYYY-MM-DD format.
        expiry_date : str
            Expiry date in YYYY-MM-DD format.

        Returns:
        -------
        Path
            Full path to the parquet file.

        Raises:
        ------
        FileNotFoundError
            If the parquet file does not exist.
        """
        fd = pd.Timestamp(fetch_date).strftime("%Y%m%d")
        ed = pd.Timestamp(expiry_date).strftime("%Y%m%d")
        filename = f"{underlying}_{fd}_{ed}.parquet"
        path = self._root / "chains" / filename
        if not path.exists():
            msg = f"parquet file not found: {path}"
            raise FileNotFoundError(msg)
        return path

    @staticmethod
    def _build_chain(df_raw: pd.DataFrame) -> OptionChain:
        """Build an OptionChain from raw parquet DataFrame.

        Parameters
        ----------
        df_raw : pd.DataFrame
            Raw parquet data with fetchDate, expiryDate, optionType, and chain columns.

        Returns:
        -------
        OptionChain
            Constructed option chain with metadata.

        Raises:
        ------
        ValueError
            If date or expiry are NaT.
        """
        date_raw = pd.Timestamp(df_raw["fetchDate"].iloc[0])
        expiry_raw = pd.Timestamp(df_raw["expiryDate"].iloc[0])

        # Ensure valid timestamps (not NaT)
        if pd.isna(date_raw) or pd.isna(expiry_raw):
            msg = "Invalid date or expiry: cannot be NaT"
            raise ValueError(msg)

        # Type narrowing: after the check above, these are guaranteed to be Timestamp
        date = cast(pd.Timestamp, date_raw)
        expiry_date = cast(pd.Timestamp, expiry_raw)

        calls = df_raw[df_raw["optionType"] == "call"][_CHAINS_COLS].set_index("strike")
        puts = df_raw[df_raw["optionType"] == "put"][_CHAINS_COLS].set_index("strike")
        merged = calls.join(puts, lsuffix="_call", rsuffix="_put", how="inner").sort_index()

        strike_idx = pd.Index(merged.index.values.astype(np.float64), name="strike")

        sd = StrikeArray()
        sd.set(("call", "bid"), pd.Series(merged["bid_call"].values.astype(np.float64), index=strike_idx))
        sd.set(("call", "ask"), pd.Series(merged["ask_call"].values.astype(np.float64), index=strike_idx))
        sd.set(("put", "bid"), pd.Series(merged["bid_put"].values.astype(np.float64), index=strike_idx))
        sd.set(("put", "ask"), pd.Series(merged["ask_put"].values.astype(np.float64), index=strike_idx))
        sd.set(
            ("market", "volume"),
            pd.Series(
                (merged["volume_call"].fillna(0).values + merged["volume_put"].fillna(0).values).astype(np.float64),
                index=strike_idx,
            ),
        )
        sd.set(
            ("market", "open_interest"),
            pd.Series(
                (merged["openInterest_call"].fillna(0).values + merged["openInterest_put"].fillna(0).values).astype(
                    np.float64
                ),
                index=strike_idx,
            ),
        )

        meta = SmileMetadata(date=date, expiry=expiry_date)
        return OptionChain(strikedata=sd, metadata=meta)
