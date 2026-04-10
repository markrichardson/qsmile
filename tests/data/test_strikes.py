"""Tests for StrikeArray."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from qsmile.data.strikes import StrikeArray

# ── helpers ───────────────────────────────────────────────────────


def _make_series(values: list[float], strikes: list[float]) -> pd.Series:
    return pd.Series(values, index=strikes, dtype=np.float64)


# ── construction & setters ────────────────────────────────────────


class TestStrikeArrayConstruction:
    def test_empty(self):
        sa = StrikeArray()
        assert len(sa) == 0
        assert sa.columns == []
        np.testing.assert_array_equal(sa.strikes, np.array([], dtype=np.float64))

    def test_single_column(self):
        sa = StrikeArray()
        sa.set_call_bid(_make_series([5.0, 3.0, 1.0], [100.0, 110.0, 120.0]))
        assert len(sa) == 3
        np.testing.assert_array_equal(sa.strikes, [100.0, 110.0, 120.0])
        np.testing.assert_array_equal(sa.values("call_bid"), [5.0, 3.0, 1.0])

    def test_multiple_same_strikes(self):
        sa = StrikeArray()
        sa.set_call_bid(_make_series([5.0, 3.0, 1.0], [100.0, 110.0, 120.0]))
        sa.set_call_ask(_make_series([6.0, 4.0, 2.0], [100.0, 110.0, 120.0]))
        assert len(sa) == 3
        np.testing.assert_array_equal(sa.values("call_bid"), [5.0, 3.0, 1.0])
        np.testing.assert_array_equal(sa.values("call_ask"), [6.0, 4.0, 2.0])

    def test_unsorted_strikes_sorted_on_set(self):
        sa = StrikeArray()
        sa.set_call_bid(_make_series([1.0, 5.0, 3.0], [120.0, 100.0, 110.0]))
        np.testing.assert_array_equal(sa.strikes, [100.0, 110.0, 120.0])
        np.testing.assert_array_equal(sa.values("call_bid"), [5.0, 3.0, 1.0])

    def test_replace_column(self):
        sa = StrikeArray()
        sa.set_call_bid(_make_series([5.0, 3.0], [100.0, 110.0]))
        sa.set_call_bid(_make_series([10.0, 8.0], [100.0, 110.0]))
        np.testing.assert_array_equal(sa.values("call_bid"), [10.0, 8.0])


class TestAdaptiveReindexing:
    def test_union_extends_index(self):
        sa = StrikeArray()
        sa.set_call_bid(_make_series([5.0, 3.0, 1.0], [100.0, 110.0, 120.0]))
        sa.set_put_bid(_make_series([0.5, 2.0, 4.0], [105.0, 110.0, 115.0]))
        np.testing.assert_array_equal(sa.strikes, [100.0, 105.0, 110.0, 115.0, 120.0])
        # Original call_bid reindexed — NaN at new strikes
        cb = sa.values("call_bid")
        assert cb[0] == 5.0  # 100
        assert np.isnan(cb[1])  # 105 — new
        assert cb[2] == 3.0  # 110
        assert np.isnan(cb[3])  # 115 — new
        assert cb[4] == 1.0  # 120

    def test_identical_strikes_no_change(self):
        sa = StrikeArray()
        sa.set_call_bid(_make_series([5.0, 3.0], [100.0, 110.0]))
        sa.set_call_ask(_make_series([6.0, 4.0], [100.0, 110.0]))
        assert len(sa) == 2
        assert not np.any(np.isnan(sa.values("call_bid")))


class TestReadAccessors:
    def test_columns(self):
        sa = StrikeArray()
        sa.set_call_bid(_make_series([5.0], [100.0]))
        sa.set_put_ask(_make_series([6.0], [100.0]))
        assert "call_bid" in sa.columns
        assert "put_ask" in sa.columns

    def test_values_missing_raises(self):
        sa = StrikeArray()
        with pytest.raises(KeyError):
            sa.values("nonexistent")

    def test_get_values_missing_returns_none(self):
        sa = StrikeArray()
        assert sa.get_values("nonexistent") is None

    def test_has(self):
        sa = StrikeArray()
        assert not sa.has("call_bid")
        sa.set_call_bid(_make_series([5.0], [100.0]))
        assert sa.has("call_bid")
        assert not sa.has("put_bid")

    def test_generic_set(self):
        sa = StrikeArray()
        sa.set("custom_col", _make_series([1.0, 2.0], [100.0, 110.0]))
        np.testing.assert_array_equal(sa.values("custom_col"), [1.0, 2.0])


class TestToDataFrame:
    def test_returns_hierarchical_df(self):
        sa = StrikeArray()
        sa.set_call_bid(_make_series([5.0, 3.0], [100.0, 110.0]))
        sa.set_put_ask(_make_series([6.0, 4.0], [100.0, 110.0]))
        df = sa.to_dataframe()
        assert isinstance(df.columns, pd.MultiIndex)
        assert ("call", "bid") in df.columns
        assert ("put", "ask") in df.columns
        np.testing.assert_array_equal(df.index.to_numpy(), [100.0, 110.0])

    def test_to_dataframe_is_copy(self):
        sa = StrikeArray()
        sa.set_call_bid(_make_series([5.0], [100.0]))
        df = sa.to_dataframe()
        df.iloc[0, 0] = 999.0
        assert sa.values("call_bid")[0] == 5.0


class TestFilter:
    def test_filter_subsets(self):
        sa = StrikeArray()
        sa.set_call_bid(_make_series([5.0, 3.0, 1.0], [100.0, 110.0, 120.0]))
        sa.set_put_bid(_make_series([1.0, 3.0, 5.0], [100.0, 110.0, 120.0]))
        mask = np.array([True, False, True])
        filtered = sa.filter(mask)
        assert len(filtered) == 2
        np.testing.assert_array_equal(filtered.strikes, [100.0, 120.0])
        np.testing.assert_array_equal(filtered.values("call_bid"), [5.0, 1.0])
        np.testing.assert_array_equal(filtered.values("put_bid"), [1.0, 5.0])

    def test_filter_preserves_columns(self):
        sa = StrikeArray()
        sa.set_call_bid(_make_series([5.0, 3.0], [100.0, 110.0]))
        sa.set_volume(_make_series([10.0, 20.0], [100.0, 110.0]))
        mask = np.array([True, False])
        filtered = sa.filter(mask)
        assert filtered.has("call_bid")
        assert filtered.has("volume")


class TestValidation:
    def test_duplicate_strikes_rejected(self):
        sa = StrikeArray()
        with pytest.raises(ValueError, match="duplicate"):
            sa.set_call_bid(_make_series([5.0, 3.0], [100.0, 100.0]))
