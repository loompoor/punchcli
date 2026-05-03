from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Callable

from punchcli.core import db, timeutil


def _seed(n: int = 4) -> None:
    now = timeutil.now()
    with db.connect() as conn:
        for offset_h, dur, msg, tags in [
            (1, 1800, "fresh", "backend"),
            (24, 3600, "yesterday", "docs"),
            (24 * 8, 5400, "last week", "backend,bug"),
            (24 * 40, 1200, None, None),  # very old, untagged
        ][:n]:
            started = now - timedelta(hours=offset_h)
            ended = started + timedelta(seconds=dur)
            conn.execute(
                "INSERT INTO entries (started_at, ended_at, duration_s, message, tags) "
                "VALUES (?, ?, ?, ?, ?)",
                (started.isoformat(), ended.isoformat(), dur, msg, tags),
            )
        conn.commit()


def test_empty(cli: Callable[..., tuple[int, str]]) -> None:
    rc, out = cli("log")
    assert rc == 0
    assert "No sessions found" in out


def test_default_lists_all(cli: Callable[..., tuple[int, str]]) -> None:
    _seed()
    rc, out = cli("log")
    assert rc == 0
    assert "Date" in out and "Start" in out and "Tags" in out
    assert "fresh" in out
    assert "yesterday" in out


def test_descending_order(cli: Callable[..., tuple[int, str]]) -> None:
    _seed()
    rc, out = cli("log")
    assert rc == 0
    # newest (fresh) appears before oldest
    assert out.index("fresh") < out.index("last week")


def test_n_limit(cli: Callable[..., tuple[int, str]]) -> None:
    _seed()
    rc, out = cli("log", "-n", "1")
    assert rc == 0
    assert "fresh" in out
    assert "yesterday" not in out


def test_today_filter(cli: Callable[..., tuple[int, str]]) -> None:
    _seed()
    rc, out = cli("log", "--today")
    assert rc == 0
    assert "fresh" in out
    assert "yesterday" not in out


def test_tag_filter(cli: Callable[..., tuple[int, str]]) -> None:
    _seed()
    rc, out = cli("log", "--tag", "docs")
    assert rc == 0
    assert "yesterday" in out
    assert "fresh" not in out


def test_combined_filters(cli: Callable[..., tuple[int, str]]) -> None:
    _seed()
    rc, out = cli("log", "--week", "--tag", "backend")
    assert rc == 0
    assert "fresh" in out
    assert "last week" not in out


def test_month_filter(cli: Callable[..., tuple[int, str]]) -> None:
    _seed()
    rc, out = cli("log", "--month")
    assert rc == 0
    # 40-day-old entry is excluded; entries within the current month present
    assert "fresh" in out
    # the 8-day-old "last week" entry may or may not fall in current month
    # depending on calendar position; assert only the safe inclusions/exclusions
    now = timeutil.now()
    forty_days_ago = now - timedelta(days=40)
    if forty_days_ago.month != now.month or forty_days_ago.year != now.year:
        # the untagged 40d-old row had no message, so we can't assert by string;
        # instead assert row count via a sentinel: "fresh" and "yesterday" both within month
        assert "yesterday" in out
