"""Strike-indexed columnar data with hierarchical MultiIndex columns."""

from __future__ import annotations

from typing import ClassVar

import numpy as np
import pandas as pd
from numpy.typing import NDArray


class StrikeArray:
    """A mutable collection of named columns indexed by strike price.

    Columns are stored in a ``pd.DataFrame`` with a two-level ``MultiIndex``
    on columns (level-0 = category, level-1 = field).  Named setters map
    convenience names like ``"call_bid"`` to ``("call", "bid")``.

    When a new column is added whose strike index differs from the current
    global index, all columns are reindexed to the sorted union of strikes.
    """

    # canonical mapping from flat name → (level0, level1)
    _COLUMN_MAP: ClassVar[dict[str, tuple[str, str]]] = {
        "call_bid": ("call", "bid"),
        "call_ask": ("call", "ask"),
        "put_bid": ("put", "bid"),
        "put_ask": ("put", "ask"),
        "volume": ("meta", "volume"),
        "open_interest": ("meta", "open_interest"),
        # SmileData uses these
        "y_bid": ("y", "bid"),
        "y_ask": ("y", "ask"),
        "y_volume": ("y", "volume"),
        "y_open_interest": ("y", "open_interest"),
    }

    __slots__ = ("_df",)

    def __init__(self) -> None:
        """Create an empty StrikeArray."""
        idx = pd.Index([], dtype=np.float64, name="strike")
        cols = pd.MultiIndex.from_tuples([], names=["category", "field"])
        self._df: pd.DataFrame = pd.DataFrame(index=idx, columns=cols, dtype=np.float64)

    # ── internal helpers ──────────────────────────────────────────

    @staticmethod
    def _resolve_key(name: str) -> tuple[str, str]:
        """Map a flat column name to a hierarchical key."""
        key = StrikeArray._COLUMN_MAP.get(name)
        if key is not None:
            return key
        # Fallback: treat as (name, name) for arbitrary columns
        return (name, name)

    # ── setters ───────────────────────────────────────────────────

    def set(self, name: str, series: pd.Series) -> None:
        """Add or replace a column, updating the global strike index."""
        idx = series.index.astype(np.float64)
        vals = series.values.astype(np.float64)

        if len(idx) > 0 and idx.has_duplicates:
            msg = "strikes must not contain duplicates"
            raise ValueError(msg)

        # Sort by strike
        order = np.argsort(idx)
        sorted_idx = pd.Index(idx[order], dtype=np.float64, name="strike")
        sorted_vals = vals[order]

        key = self._resolve_key(name)

        if len(self._df.index) == 0:
            new_index = sorted_idx
        else:
            new_index = self._df.index.union(sorted_idx).astype(np.float64)
            new_index.name = "strike"

        # Reindex existing columns if the index changed
        if not self._df.index.equals(new_index):
            self._df = self._df.reindex(new_index)

        # Create a series aligned to the new index
        col_series = pd.Series(sorted_vals, index=sorted_idx, dtype=np.float64)
        col_aligned = col_series.reindex(new_index)

        # Add as a hierarchical column
        self._df[key] = col_aligned.values

    def set_call_bid(self, series: pd.Series) -> None:
        """Set the call bid column."""
        self.set("call_bid", series)

    def set_call_ask(self, series: pd.Series) -> None:
        """Set the call ask column."""
        self.set("call_ask", series)

    def set_put_bid(self, series: pd.Series) -> None:
        """Set the put bid column."""
        self.set("put_bid", series)

    def set_put_ask(self, series: pd.Series) -> None:
        """Set the put ask column."""
        self.set("put_ask", series)

    def set_volume(self, series: pd.Series) -> None:
        """Set the volume column."""
        self.set("volume", series)

    def set_open_interest(self, series: pd.Series) -> None:
        """Set the open interest column."""
        self.set("open_interest", series)

    # ── read accessors ────────────────────────────────────────────

    @property
    def strikes(self) -> NDArray[np.float64]:
        """Common strike index as a sorted NDArray."""
        return self._df.index.to_numpy(dtype=np.float64)

    @property
    def columns(self) -> list[str]:
        """Flat column names in insertion order."""
        reverse_map = {v: k for k, v in self._COLUMN_MAP.items()}
        result = []
        for col_tuple in self._df.columns:
            flat = reverse_map.get(col_tuple, f"{col_tuple[0]}_{col_tuple[1]}")
            result.append(flat)
        return result

    def values(self, name: str) -> NDArray[np.float64]:
        """Get column values as an NDArray. Raises KeyError if absent."""
        key = self._resolve_key(name)
        if key not in self._df.columns:
            raise KeyError(name)
        return self._df[key].to_numpy(dtype=np.float64)

    def get_values(self, name: str) -> NDArray[np.float64] | None:
        """Get column values as an NDArray, or None if absent."""
        key = self._resolve_key(name)
        if key not in self._df.columns:
            return None
        return self._df[key].to_numpy(dtype=np.float64)

    def has(self, name: str) -> bool:
        """Check whether a column exists."""
        key = self._resolve_key(name)
        return key in self._df.columns

    def __len__(self) -> int:
        """Return the number of strikes."""
        return len(self._df.index)

    # ── operations ────────────────────────────────────────────────

    def filter(self, mask: NDArray[np.bool_]) -> StrikeArray:
        """Apply a boolean mask to all columns, returning a new StrikeArray."""
        sa = StrikeArray()
        filtered = self._df.iloc[mask].copy()
        filtered.index.name = "strike"
        # Ensure columns retain MultiIndex
        if not isinstance(filtered.columns, pd.MultiIndex):
            filtered.columns = self._df.columns
        sa._df = filtered
        return sa

    def to_dataframe(self) -> pd.DataFrame:
        """Return a copy of the internal DataFrame with hierarchical columns."""
        return self._df.copy()
