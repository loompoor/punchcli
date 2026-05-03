from __future__ import annotations

import pytest

from punchcli.core.duration import format_duration, parse_duration


@pytest.mark.parametrize(
    "seconds,expected",
    [
        (0, "< 1m"),
        (-5, "< 1m"),
        (45, "< 1m"),
        (59, "< 1m"),
        (60, "1m"),
        (90, "1m"),
        (3599, "59m"),
        (3600, "1h 00m"),
        (5400, "1h 30m"),
        (7245, "2h 00m"),
        (36000, "10h 00m"),
    ],
)
def test_format_duration(seconds: int, expected: str) -> None:
    assert format_duration(seconds) == expected


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("45m", 45 * 60),
        ("2h", 2 * 3600),
        ("1h30m", 3600 + 30 * 60),
        ("1h 30m", 3600 + 30 * 60),
        (" 1H30M ", 3600 + 30 * 60),
        ("90m", 90 * 60),
    ],
)
def test_parse_duration_ok(raw: str, expected: int) -> None:
    assert parse_duration(raw) == expected


@pytest.mark.parametrize("raw", ["", "   ", "abc", "5", "0m", "0h", "1.5h", "-1h"])
def test_parse_duration_invalid(raw: str) -> None:
    with pytest.raises(ValueError):
        parse_duration(raw)
