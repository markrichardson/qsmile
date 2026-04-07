"""Tests for SmileMetadata."""

from __future__ import annotations

import dataclasses

import pytest

from qsmile.data.meta import SmileMetadata


class TestSmileMetadataConstruction:
    def test_all_fields(self) -> None:
        meta = SmileMetadata(forward=100.0, discount_factor=0.99, expiry=0.25, sigma_atm=0.20)
        assert meta.forward == 100.0
        assert meta.discount_factor == 0.99
        assert meta.expiry == 0.25
        assert meta.sigma_atm == 0.20

    def test_without_sigma_atm(self) -> None:
        meta = SmileMetadata(forward=100.0, discount_factor=0.99, expiry=0.25)
        assert meta.sigma_atm is None

    def test_with_only_expiry(self) -> None:
        meta = SmileMetadata(expiry=0.25)
        assert meta.forward is None
        assert meta.discount_factor is None
        assert meta.sigma_atm is None

    def test_none_forward_accepted(self) -> None:
        meta = SmileMetadata(expiry=0.25, discount_factor=0.99)
        assert meta.forward is None

    def test_none_discount_factor_accepted(self) -> None:
        meta = SmileMetadata(expiry=0.25, forward=100.0)
        assert meta.discount_factor is None


class TestSmileMetadataValidation:
    def test_non_positive_forward(self) -> None:
        with pytest.raises(ValueError, match="forward must be positive"):
            SmileMetadata(forward=0.0, discount_factor=0.99, expiry=0.25)
        with pytest.raises(ValueError, match="forward must be positive"):
            SmileMetadata(forward=-1.0, discount_factor=0.99, expiry=0.25)

    def test_non_positive_discount_factor(self) -> None:
        with pytest.raises(ValueError, match="discount_factor must be positive"):
            SmileMetadata(forward=100.0, discount_factor=0.0, expiry=0.25)
        with pytest.raises(ValueError, match="discount_factor must be positive"):
            SmileMetadata(forward=100.0, discount_factor=-0.5, expiry=0.25)

    def test_non_positive_expiry(self) -> None:
        with pytest.raises(ValueError, match="expiry must be positive"):
            SmileMetadata(forward=100.0, discount_factor=0.99, expiry=0.0)
        with pytest.raises(ValueError, match="expiry must be positive"):
            SmileMetadata(forward=100.0, discount_factor=0.99, expiry=-1.0)

    def test_non_positive_sigma_atm(self) -> None:
        with pytest.raises(ValueError, match="sigma_atm must be positive"):
            SmileMetadata(forward=100.0, discount_factor=0.99, expiry=0.25, sigma_atm=0.0)
        with pytest.raises(ValueError, match="sigma_atm must be positive"):
            SmileMetadata(forward=100.0, discount_factor=0.99, expiry=0.25, sigma_atm=-0.1)


class TestSmileMetadataImmutability:
    def test_frozen(self) -> None:
        meta = SmileMetadata(forward=100.0, discount_factor=0.99, expiry=0.25)
        with pytest.raises(dataclasses.FrozenInstanceError):
            meta.forward = 200.0  # type: ignore[misc]
