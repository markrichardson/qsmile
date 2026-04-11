"""Tests for qsmile.data.parquet (SampleDataReader)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from qsmile.data.io import SampleDataReader
from qsmile.data.prices import OptionChain

# ── helpers ───────────────────────────────────────────────────────────


def _make_raw_df(
    strikes: list[float] | None = None,
    fetch_date: str = "2026-04-03",
    expiry_date: str = "2026-06-30",
    underlying: str = "SPX",
) -> pd.DataFrame:
    """Build a minimal raw DataFrame matching the parquet schema."""
    if strikes is None:
        strikes = [5000.0, 5500.0, 6000.0, 6500.0, 7000.0]
    rows = []
    for s in strikes:
        rows.append(
            {
                "underlying": underlying,
                "fetchDate": fetch_date,
                "expiryDate": expiry_date,
                "daysToExpiry": 88,
                "optionType": "call",
                "strike": s,
                "lastPrice": 100.0,
                "bid": max(6500.0 - s, 1.0) + 5.0,
                "ask": max(6500.0 - s, 1.0) + 15.0,
                "volume": 10.0,
                "openInterest": 100,
            }
        )
        rows.append(
            {
                "underlying": underlying,
                "fetchDate": fetch_date,
                "expiryDate": expiry_date,
                "daysToExpiry": 88,
                "optionType": "put",
                "strike": s,
                "lastPrice": 50.0,
                "bid": max(s - 6500.0, 1.0) + 5.0,
                "ask": max(s - 6500.0, 1.0) + 15.0,
                "volume": 20.0,
                "openInterest": 200,
            }
        )
    return pd.DataFrame(rows)


def _write_parquet(tmp_path, df, underlying="SPX", fetch="20260403", expiry="20260630"):
    """Write a DataFrame to the expected parquet directory structure."""
    chains_dir = tmp_path / "chains"
    chains_dir.mkdir(parents=True, exist_ok=True)
    path = chains_dir / f"{underlying}_{fetch}_{expiry}.parquet"
    df.to_parquet(path, index=False)
    return path


# ── TestSampleDataReaderInit ─────────────────────────────────────────


class TestSampleDataReaderInit:
    """Construction and default root resolution."""

    def test_default_root(self):
        reader = SampleDataReader()
        assert reader._root.name == "parquet"

    def test_custom_root_str(self, tmp_path):
        reader = SampleDataReader(root=str(tmp_path))
        assert reader._root == tmp_path

    def test_custom_root_path(self, tmp_path):
        reader = SampleDataReader(root=tmp_path)
        assert reader._root == tmp_path


# ── TestResolvePath ──────────────────────────────────────────────────


class TestResolvePath:
    """Path resolution and file-not-found handling."""

    def test_resolve_existing_file(self, tmp_path):
        df = _make_raw_df()
        _write_parquet(tmp_path, df)
        reader = SampleDataReader(root=tmp_path)
        path = reader._resolve_path("SPX", "2026-04-03", "2026-06-30")
        assert path.exists()
        assert path.name == "SPX_20260403_20260630.parquet"

    def test_file_not_found_raises(self, tmp_path):
        reader = SampleDataReader(root=tmp_path)
        with pytest.raises(FileNotFoundError, match="parquet file not found"):
            reader._resolve_path("SPX", "2099-01-01", "2099-12-31")

    def test_date_format_normalisation(self, tmp_path):
        """Dates with different separators resolve to the same filename."""
        df = _make_raw_df()
        _write_parquet(tmp_path, df)
        reader = SampleDataReader(root=tmp_path)
        path = reader._resolve_path("SPX", "2026-04-03", "2026-06-30")
        assert path.name == "SPX_20260403_20260630.parquet"


# ── TestBuildChain ───────────────────────────────────────────────────


class TestBuildChain:
    """_build_chain produces a valid OptionChain from raw DataFrame."""

    def test_returns_option_chain(self):
        df = _make_raw_df()
        chain = SampleDataReader._build_chain(df)
        assert isinstance(chain, OptionChain)

    def test_metadata_dates(self):
        df = _make_raw_df(fetch_date="2026-04-03", expiry_date="2026-06-30")
        chain = SampleDataReader._build_chain(df)
        assert chain.metadata.date == pd.Timestamp("2026-04-03")
        assert chain.metadata.expiry == pd.Timestamp("2026-06-30")

    def test_strikes_sorted(self):
        df = _make_raw_df(strikes=[7000.0, 5000.0, 6000.0])
        chain = SampleDataReader._build_chain(df)
        strikes = chain.strikedata.strikes
        np.testing.assert_array_equal(strikes, sorted(strikes))

    def test_strike_count_matches_inner_join(self):
        strikes = [5000.0, 5500.0, 6000.0, 6500.0, 7000.0]
        df = _make_raw_df(strikes=strikes)
        chain = SampleDataReader._build_chain(df)
        assert len(chain.strikedata.strikes) == len(strikes)

    def test_call_bid_ask_populated(self):
        df = _make_raw_df(strikes=[6000.0, 6500.0, 7000.0])
        chain = SampleDataReader._build_chain(df)
        sd = chain.strikedata
        assert np.all(np.isfinite(sd.values(("call", "bid"))))
        assert np.all(np.isfinite(sd.values(("call", "ask"))))
        assert np.all(sd.values(("call", "ask")) >= sd.values(("call", "bid")))

    def test_put_bid_ask_populated(self):
        df = _make_raw_df(strikes=[6000.0, 6500.0, 7000.0])
        chain = SampleDataReader._build_chain(df)
        sd = chain.strikedata
        assert np.all(np.isfinite(sd.values(("put", "bid"))))
        assert np.all(np.isfinite(sd.values(("put", "ask"))))
        assert np.all(sd.values(("put", "ask")) >= sd.values(("put", "bid")))

    def test_volume_aggregated(self):
        df = _make_raw_df(strikes=[6000.0, 6500.0, 7000.0])
        chain = SampleDataReader._build_chain(df)
        volume = chain.strikedata.values(("market", "volume"))
        # Each strike has call volume 10 + put volume 20 = 30
        np.testing.assert_array_equal(volume, 30.0)

    def test_open_interest_aggregated(self):
        df = _make_raw_df(strikes=[6000.0, 6500.0, 7000.0])
        chain = SampleDataReader._build_chain(df)
        oi = chain.strikedata.values(("market", "open_interest"))
        # Each strike has call OI 100 + put OI 200 = 300
        np.testing.assert_array_equal(oi, 300.0)

    def test_nan_volume_treated_as_zero(self):
        df = _make_raw_df(strikes=[5500.0, 6000.0, 6500.0])
        df.loc[df["optionType"] == "call", "volume"] = np.nan
        chain = SampleDataReader._build_chain(df)
        volume = chain.strikedata.values(("market", "volume"))
        # call NaN -> 0, put = 20 => total = 20
        np.testing.assert_array_equal(volume, 20.0)

    def test_inner_join_drops_unmatched_strikes(self):
        """Strikes only present in calls or puts are excluded."""
        df = _make_raw_df(strikes=[5000.0, 5500.0, 6000.0, 6500.0, 7000.0])
        # Remove the put at strike 5000
        df = df[~((df["strike"] == 5000.0) & (df["optionType"] == "put"))]
        chain = SampleDataReader._build_chain(df)
        assert 5000.0 not in chain.strikedata.strikes
        assert len(chain.strikedata.strikes) == 4


# ── TestGetChain ─────────────────────────────────────────────────────


class TestGetChain:
    """End-to-end get_chain via parquet round-trip."""

    def test_round_trip(self, tmp_path):
        df = _make_raw_df()
        _write_parquet(tmp_path, df)
        reader = SampleDataReader(root=tmp_path)
        chain = reader.get_chain("SPX", "2026-04-03", "2026-06-30")
        assert isinstance(chain, OptionChain)
        assert len(chain.strikedata.strikes) == 5

    def test_forward_calibrated(self, tmp_path):
        df = _make_raw_df()
        _write_parquet(tmp_path, df)
        reader = SampleDataReader(root=tmp_path)
        chain = reader.get_chain("SPX", "2026-04-03", "2026-06-30")
        # Forward should be calibrated (positive finite number)
        assert chain.metadata.forward is not None
        assert chain.metadata.forward > 0
        assert np.isfinite(chain.metadata.forward)

    def test_discount_factor_calibrated(self, tmp_path):
        df = _make_raw_df()
        _write_parquet(tmp_path, df)
        reader = SampleDataReader(root=tmp_path)
        chain = reader.get_chain("SPX", "2026-04-03", "2026-06-30")
        assert chain.metadata.discount_factor is not None
        assert 0 < chain.metadata.discount_factor <= 1.0


# ── TestRealParquet ──────────────────────────────────────────────────


class TestRealParquet:
    """Smoke tests against the real SPX parquet shipped with the repo."""

    _pq = SampleDataReader()._root / "chains" / "SPX_20260403_20260630.parquet"

    @pytest.mark.skipif(not _pq.exists(), reason="real parquet not available")
    def test_load_real_spx(self):
        reader = SampleDataReader()
        chain = reader.get_chain("SPX", "2026-04-03", "2026-06-30")
        assert isinstance(chain, OptionChain)
        assert len(chain.strikedata.strikes) > 100
        assert chain.metadata.date == pd.Timestamp("2026-04-03")
        assert chain.metadata.expiry == pd.Timestamp("2026-06-30")
        assert chain.metadata.forward > 0
