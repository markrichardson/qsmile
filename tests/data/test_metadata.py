"""Tests for SmileMetadata."""

from __future__ import annotations

import dataclasses

import pandas as pd
import pytest

from qsmile.core.daycount import DayCount
from qsmile.data.meta import SmileMetadata

# Convenience dates used across tests
D = pd.Timestamp("2024-01-01")
E = pd.Timestamp("2024-04-01")  # 91 days after D


class TestSmileMetadataConstruction:
    def test_all_fields(self) -> None:
        meta = SmileMetadata(date=D, expiry=E, forward=100.0, discount_factor=0.99, sigma_atm=0.20)
        assert meta.forward == 100.0
        assert meta.discount_factor == 0.99
        assert meta.date == D
        assert meta.expiry == E
        assert meta.sigma_atm == 0.20

    def test_without_sigma_atm(self) -> None:
        meta = SmileMetadata(date=D, expiry=E, forward=100.0, discount_factor=0.99)
        assert meta.sigma_atm is None

    def test_with_only_dates(self) -> None:
        meta = SmileMetadata(date=D, expiry=E)
        assert meta.forward is None
        assert meta.discount_factor is None
        assert meta.sigma_atm is None
        assert meta.daycount == DayCount.ACT365

    def test_none_forward_accepted(self) -> None:
        meta = SmileMetadata(date=D, expiry=E, discount_factor=0.99)
        assert meta.forward is None

    def test_none_discount_factor_accepted(self) -> None:
        meta = SmileMetadata(date=D, expiry=E, forward=100.0)
        assert meta.discount_factor is None

    def test_texpiry_act365(self) -> None:
        meta = SmileMetadata(date=D, expiry=E)
        assert meta.texpiry == 91 / 365.0

    def test_texpiry_act360(self) -> None:
        meta = SmileMetadata(date=D, expiry=E, daycount=DayCount.ACT360)
        assert meta.texpiry == 91 / 360.0

    def test_texpiry_is_derived(self) -> None:
        meta = SmileMetadata(date=D, expiry=E)
        assert meta.texpiry == meta.daycount.year_fraction(meta.date, meta.expiry)


class TestSmileMetadataValidation:
    def test_non_positive_forward(self) -> None:
        with pytest.raises(ValueError, match="forward must be positive"):
            SmileMetadata(date=D, expiry=E, forward=0.0, discount_factor=0.99)
        with pytest.raises(ValueError, match="forward must be positive"):
            SmileMetadata(date=D, expiry=E, forward=-1.0, discount_factor=0.99)

    def test_non_positive_discount_factor(self) -> None:
        with pytest.raises(ValueError, match="discount_factor must be positive"):
            SmileMetadata(date=D, expiry=E, forward=100.0, discount_factor=0.0)
        with pytest.raises(ValueError, match="discount_factor must be positive"):
            SmileMetadata(date=D, expiry=E, forward=100.0, discount_factor=-0.5)

    def test_expiry_not_after_date(self) -> None:
        with pytest.raises(ValueError, match="expiry must be after date"):
            SmileMetadata(date=D, expiry=D)
        with pytest.raises(ValueError, match="expiry must be after date"):
            SmileMetadata(date=E, expiry=D)

    def test_non_positive_sigma_atm(self) -> None:
        with pytest.raises(ValueError, match="sigma_atm must be positive"):
            SmileMetadata(date=D, expiry=E, forward=100.0, discount_factor=0.99, sigma_atm=0.0)
        with pytest.raises(ValueError, match="sigma_atm must be positive"):
            SmileMetadata(date=D, expiry=E, forward=100.0, discount_factor=0.99, sigma_atm=-0.1)


class TestSmileMetadataImmutability:
    def test_frozen(self) -> None:
        meta = SmileMetadata(date=D, expiry=E, forward=100.0, discount_factor=0.99)
        with pytest.raises(dataclasses.FrozenInstanceError):
            meta.forward = 200.0  # type: ignore[misc]
