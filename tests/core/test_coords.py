"""Tests for coordinate enums."""

from __future__ import annotations

from qsmile.core.coords import XCoord, YCoord


class TestXCoord:
    def test_member_count(self) -> None:
        assert len(XCoord) == 4

    def test_members_exist(self) -> None:
        assert XCoord.FixedStrike is not None
        assert XCoord.MoneynessStrike is not None
        assert XCoord.LogMoneynessStrike is not None
        assert XCoord.StandardisedStrike is not None

    def test_members_distinct(self) -> None:
        members = list(XCoord)
        for i, a in enumerate(members):
            for b in members[i + 1 :]:
                assert a != b


class TestYCoord:
    def test_member_count(self) -> None:
        assert len(YCoord) == 4

    def test_members_exist(self) -> None:
        assert YCoord.Price is not None
        assert YCoord.Volatility is not None
        assert YCoord.Variance is not None
        assert YCoord.TotalVariance is not None

    def test_members_distinct(self) -> None:
        members = list(YCoord)
        for i, a in enumerate(members):
            for b in members[i + 1 :]:
                assert a != b
