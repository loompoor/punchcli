from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest

from punchcli.core import timeutil


def test_now_returns_aware_datetime() -> None:
    n = timeutil.now()
    assert n.tzinfo is not None
    assert n.utcoffset() is not None


def test_iso_roundtrip() -> None:
    n = timeutil.now()
    assert timeutil.from_iso(timeutil.to_iso(n)) == n


def test_to_iso_naive_becomes_local() -> None:
    naive = datetime(2026, 4, 30, 10, 0, 0)
    parsed = timeutil.from_iso(timeutil.to_iso(naive))
    assert parsed.tzinfo is not None


def test_parse_local_date_iso() -> None:
    assert timeutil.parse_local_date("2026-04-30") == date(2026, 4, 30)


def test_parse_local_date_invalid() -> None:
    with pytest.raises(ValueError):
        timeutil.parse_local_date("nope")


def test_local_midnight() -> None:
    d = date(2026, 4, 30)
    m = timeutil.local_midnight(d)
    assert m.tzinfo is not None
    assert (m.hour, m.minute, m.second) == (0, 0, 0)
    assert m.date() == d


def test_today_bounds_24h_span() -> None:
    ref = datetime(2026, 4, 30, 14, 30, 0).astimezone()
    start, end = timeutil.today_bounds(ref)
    assert start.date() == date(2026, 4, 30)
    assert end.date() == date(2026, 5, 1)
    assert end - start == timedelta(days=1)


class TestWeekBounds:
    def test_starts_monday_from_thursday(self) -> None:
        # 2026-04-30 is Thursday → Monday is 2026-04-27
        ref = datetime(2026, 4, 30, 14, 30, 0).astimezone()
        start, end = timeutil.week_bounds(ref)
        assert start.date() == date(2026, 4, 27)
        assert end.date() == date(2026, 5, 4)
        assert start.weekday() == 0

    def test_already_monday(self) -> None:
        ref = datetime(2026, 4, 27, 9, 0, 0).astimezone()
        start, _ = timeutil.week_bounds(ref)
        assert start.date() == date(2026, 4, 27)

    def test_sunday_belongs_to_prior_week(self) -> None:
        # ISO Monday-start: Sunday belongs to the week that started Monday
        ref = datetime(2026, 5, 3, 9, 0, 0).astimezone()
        start, _ = timeutil.week_bounds(ref)
        assert start.date() == date(2026, 4, 27)


class TestParseTimestamp:
    def test_iso_with_offset(self) -> None:
        dt = timeutil.parse_timestamp("2026-04-30T10:00:00+02:00")
        assert dt.year == 2026 and dt.hour == 10
        assert dt.utcoffset().total_seconds() == 2 * 3600

    def test_iso_naive_attaches_local(self) -> None:
        dt = timeutil.parse_timestamp("2026-04-30T10:00:00")
        assert dt.tzinfo is not None

    def test_date_time(self) -> None:
        dt = timeutil.parse_timestamp("2026-04-30 10:00")
        assert dt.date() == date(2026, 4, 30)
        assert (dt.hour, dt.minute) == (10, 0)
        assert dt.tzinfo is not None

    def test_hhmm_uses_today(self) -> None:
        ref = datetime(2026, 4, 30, 12, 0, 0).astimezone()
        dt = timeutil.parse_timestamp("09:30", reference=ref)
        assert dt.date() == date(2026, 4, 30)
        assert (dt.hour, dt.minute) == (9, 30)

    def test_yesterday(self) -> None:
        ref = datetime(2026, 4, 30, 12, 0, 0).astimezone()
        dt = timeutil.parse_timestamp("yesterday 14:00", reference=ref)
        assert dt.date() == date(2026, 4, 29)
        assert (dt.hour, dt.minute) == (14, 0)

    def test_today_word(self) -> None:
        ref = datetime(2026, 4, 30, 12, 0, 0).astimezone()
        dt = timeutil.parse_timestamp("today 09:00", reference=ref)
        assert dt.date() == date(2026, 4, 30)

    @pytest.mark.parametrize("bad", ["", "   ", "not-a-date", "tomorrow 10:00", "25:99"])
    def test_invalid(self, bad: str) -> None:
        with pytest.raises(ValueError):
            timeutil.parse_timestamp(bad)


class TestMonthBounds:
    def test_first_to_first(self) -> None:
        ref = datetime(2026, 4, 30, 14, 30, 0).astimezone()
        start, end = timeutil.month_bounds(ref)
        assert start.date() == date(2026, 4, 1)
        assert end.date() == date(2026, 5, 1)

    def test_december_wraps_year(self) -> None:
        ref = datetime(2026, 12, 15, 9, 0, 0).astimezone()
        start, end = timeutil.month_bounds(ref)
        assert start.date() == date(2026, 12, 1)
        assert end.date() == date(2027, 1, 1)
