from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from punchcli.core import db, report, timeutil


def _insert(
    conn: sqlite3.Connection,
    started: datetime,
    dur_s: int,
    message: str | None = None,
    tags: str | None = None,
) -> None:
    ended = started + timedelta(seconds=dur_s)
    conn.execute(
        "INSERT INTO entries (started_at, ended_at, duration_s, message, tags) "
        "VALUES (?, ?, ?, ?, ?)",
        (started.isoformat(), ended.isoformat(), dur_s, message, tags),
    )


@pytest.fixture
def seeded_rows(punch_dir: Path) -> list[sqlite3.Row]:
    now = timeutil.now()
    with db.connect() as conn:
        _insert(conn, now - timedelta(hours=1), 1800, "today", "a")
        _insert(conn, now - timedelta(days=1), 3600, "yesterday", "b")
        _insert(conn, now - timedelta(days=8), 5400, "last week", "a,c")
        _insert(conn, now - timedelta(days=2), 900, None, None)
        conn.commit()
        return list(conn.execute("SELECT * FROM entries"))


class TestFilterEntries:
    def test_no_filter(self, seeded_rows: list[sqlite3.Row]) -> None:
        assert len(report.filter_entries(seeded_rows)) == 4

    def test_today_bounds(self, seeded_rows: list[sqlite3.Row]) -> None:
        start, end = timeutil.today_bounds()
        out = report.filter_entries(seeded_rows, start=start, end=end)
        assert len(out) == 1
        assert out[0]["message"] == "today"

    def test_tag_filter(self, seeded_rows: list[sqlite3.Row]) -> None:
        out = report.filter_entries(seeded_rows, tag="a")
        assert {r["message"] for r in out} == {"today", "last week"}

    def test_tag_filter_case_insensitive(self, seeded_rows: list[sqlite3.Row]) -> None:
        assert len(report.filter_entries(seeded_rows, tag="A")) == 2

    def test_combined_period_and_tag(self, seeded_rows: list[sqlite3.Row]) -> None:
        start, end = timeutil.today_bounds()
        out = report.filter_entries(seeded_rows, start=start, end=end, tag="b")
        assert out == []


class TestAggregate:
    def test_empty(self) -> None:
        data = report.aggregate([])
        assert data.total_s == 0
        assert data.session_count == 0
        assert data.by_tag == []
        assert data.untagged_s == 0

    def test_tags_and_untagged(self, punch_dir: Path) -> None:
        now = timeutil.now()
        with db.connect() as conn:
            _insert(conn, now - timedelta(hours=2), 3600, None, "backend")
            _insert(conn, now - timedelta(hours=1), 1800, None, "backend,bug")
            _insert(conn, now - timedelta(hours=4), 600, None, None)
            conn.commit()
            rows = list(conn.execute("SELECT * FROM entries"))

        data = report.aggregate(rows)
        assert data.session_count == 3
        assert data.total_s == 3600 + 1800 + 600
        assert data.untagged_s == 600
        by_tag = dict(data.by_tag)
        assert by_tag["backend"] == 5400
        assert by_tag["bug"] == 1800

    def test_by_tag_sorted_desc_then_alpha(self, punch_dir: Path) -> None:
        now = timeutil.now()
        with db.connect() as conn:
            _insert(conn, now, 100, None, "z")
            _insert(conn, now, 200, None, "a")
            _insert(conn, now, 200, None, "m")  # ties with a → alpha
            conn.commit()
            rows = list(conn.execute("SELECT * FROM entries"))
        names = [t for t, _ in report.aggregate(rows).by_tag]
        assert names == ["a", "m", "z"]


class TestRenderConsole:
    def test_empty(self) -> None:
        text = report.render_console(report.aggregate([], period_label="Today"))
        assert "Time Report — Today" in text
        assert "No sessions found." in text

    def test_with_data(self, punch_dir: Path) -> None:
        with db.connect() as conn:
            _insert(conn, timeutil.now(), 3600, "x", "backend")
            conn.commit()
            rows = list(conn.execute("SELECT * FROM entries"))
        text = report.render_console(report.aggregate(rows, "All Time"))
        assert "Time Report — All Time" in text
        assert "backend" in text
        assert "1h 00m" in text
        assert "Total" in text
        assert "(1 session)" in text

    def test_untagged_only(self, punch_dir: Path) -> None:
        with db.connect() as conn:
            _insert(conn, timeutil.now(), 3600, None, None)
            conn.commit()
            rows = list(conn.execute("SELECT * FROM entries"))
        text = report.render_console(report.aggregate(rows))
        assert "(untagged)" in text


class TestRegenerate:
    def test_empty_state(self, punch_dir: Path) -> None:
        report.regenerate()
        path = punch_dir / "REPORT.md"
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert "# Time Report" in text
        assert "No sessions logged yet" in text

    def test_with_data(self, punch_dir: Path) -> None:
        now = timeutil.now()
        with db.connect() as conn:
            _insert(conn, now - timedelta(hours=2), 5400, "parser fix", "backend,bug")
            _insert(conn, now - timedelta(days=1), 3600, None, "docs")
            conn.commit()

        report.regenerate()
        text = (punch_dir / "REPORT.md").read_text(encoding="utf-8")
        assert "# Time Report" in text
        assert "**Total**:" in text
        assert "All-Time by Tag" in text
        assert "backend" in text
        assert "Recent Sessions" in text
        assert "parser fix" in text

    def test_no_leftover_tmp_files(self, punch_dir: Path) -> None:
        report.regenerate()
        leftovers = [p for p in punch_dir.iterdir() if p.name.startswith(".report-")]
        assert leftovers == []

    def test_overwrites_existing(self, punch_dir: Path) -> None:
        path = punch_dir / "REPORT.md"
        path.write_text("STALE", encoding="utf-8")
        report.regenerate()
        assert "STALE" not in path.read_text(encoding="utf-8")
