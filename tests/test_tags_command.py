from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Callable

from punchcli.core import db, timeutil


def _seed() -> None:
    now = timeutil.now()
    with db.connect() as conn:
        # backend: 2 entries, last today
        for offset_h, dur, tags in [
            (24 * 5, 3600, "backend"),
            (1, 1800, "backend,bug"),
            # docs: 1 entry yesterday
            (24, 3600, "docs"),
            # untagged
            (48, 600, None),
        ]:
            started = now - timedelta(hours=offset_h)
            ended = started + timedelta(seconds=dur)
            conn.execute(
                "INSERT INTO entries (started_at, ended_at, duration_s, message, tags) "
                "VALUES (?, ?, ?, ?, ?)",
                (started.isoformat(), ended.isoformat(), dur, None, tags),
            )
        conn.commit()


def test_empty(cli: Callable[..., tuple[int, str]]) -> None:
    rc, out = cli("tags")
    assert rc == 0
    assert "No tags yet" in out


def test_aggregation(cli: Callable[..., tuple[int, str]]) -> None:
    _seed()
    rc, out = cli("tags")
    assert rc == 0
    # backend total = 3600 + 1800 = 5400 → 1h 30m
    assert "backend" in out
    assert "1h 30m" in out
    # bug total = 1800 → 30m
    assert "bug" in out
    assert "30m" in out


def test_includes_untagged(cli: Callable[..., tuple[int, str]]) -> None:
    _seed()
    rc, out = cli("tags")
    assert rc == 0
    assert "(untagged)" in out


def test_no_untagged_row_when_all_tagged(cli: Callable[..., tuple[int, str]]) -> None:
    now = timeutil.now()
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO entries (started_at, ended_at, duration_s, message, tags) "
            "VALUES (?, ?, ?, ?, ?)",
            (now.isoformat(), now.isoformat(), 60, None, "x"),
        )
        conn.commit()
    rc, out = cli("tags")
    assert "(untagged)" not in out


def test_last_used_date_per_tag(cli: Callable[..., tuple[int, str]]) -> None:
    _seed()
    rc, out = cli("tags")
    today = timeutil.now().strftime("%Y-%m-%d")
    yesterday = (timeutil.now() - timedelta(hours=24)).strftime("%Y-%m-%d")
    # backend last entry is 1h ago → today; docs last entry is 24h ago → yesterday
    backend_line = next(l for l in out.splitlines() if l.startswith("backend"))
    docs_line = next(l for l in out.splitlines() if l.startswith("docs"))
    assert today in backend_line
    assert yesterday in docs_line


def test_sorted_by_total_desc(cli: Callable[..., tuple[int, str]]) -> None:
    _seed()
    rc, out = cli("tags")
    # backend (1h 30m) > docs (1h 00m) > bug (30m)
    assert out.index("backend") < out.index("docs") < out.index("bug")
