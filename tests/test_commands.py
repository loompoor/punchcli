from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path
from typing import Callable

from punchcli.core import db, state, timeutil


class TestPunchInOutStatus:
    def test_status_when_idle(self, cli: Callable[..., tuple[int, str]]) -> None:
        rc, out = cli("status")
        assert rc == 0
        assert "No active session" in out

    def test_in_then_status_then_out(
        self, cli: Callable[..., tuple[int, str]], punch_dir: Path
    ) -> None:
        rc, out = cli("in", "-m", "smoke", "-t", "backend,bug")
        assert rc == 0
        assert "Started tracking" in out

        s = state.read()
        assert s["active"] is True
        assert s["message"] == "smoke"
        assert s["tags"] == ["backend", "bug"]

        rc, out = cli("status")
        assert rc == 0
        assert "Active session" in out
        assert "smoke" in out
        assert "backend" in out

        rc, out = cli("out")
        assert rc == 0
        assert "Stopped" in out

        assert state.read() == {"active": False}
        with db.connect() as conn:
            (count,) = conn.execute("SELECT COUNT(*) FROM entries").fetchone()
        assert count == 1

    def test_in_without_message_or_tags(
        self, cli: Callable[..., tuple[int, str]]
    ) -> None:
        rc, _ = cli("in")
        assert rc == 0
        s = state.read()
        assert s["active"] is True
        assert "message" not in s
        assert "tags" not in s

    def test_double_in_rejected(self, cli: Callable[..., tuple[int, str]]) -> None:
        cli("in")
        rc, out = cli("in")
        assert rc == 1
        assert "Already tracking" in out

    def test_out_without_session_rejected(
        self, cli: Callable[..., tuple[int, str]]
    ) -> None:
        rc, out = cli("out")
        assert rc == 1
        assert "No active session" in out

    def test_in_with_invalid_tag_rejected(
        self, cli: Callable[..., tuple[int, str]]
    ) -> None:
        rc, out = cli("in", "-t", "BAD!!")
        assert rc == 1
        assert "Invalid tag" in out
        assert state.read() == {"active": False}

    def test_in_with_too_many_tags_rejected(
        self, cli: Callable[..., tuple[int, str]]
    ) -> None:
        rc, out = cli("in", "-t", "a,b,c,d,e,f")
        assert rc == 1
        assert "Too many tags" in out

    def test_in_with_long_message_rejected(
        self, cli: Callable[..., tuple[int, str]]
    ) -> None:
        rc, out = cli("in", "-m", "x" * 257)
        assert rc == 1
        assert "exceeds" in out

    def test_out_regenerates_report_md(
        self, cli: Callable[..., tuple[int, str]], punch_dir: Path
    ) -> None:
        cli("in", "-m", "x")
        cli("out")
        report_md = punch_dir / "REPORT.md"
        assert report_md.exists()
        assert "# Time Report" in report_md.read_text(encoding="utf-8")

    def test_out_logs_elapsed_duration(
        self, cli: Callable[..., tuple[int, str]], punch_dir: Path
    ) -> None:
        # rewind started_at by 45 minutes via state, then `out` should log ~45m
        started = (timeutil.now() - timedelta(minutes=45)).isoformat()
        state.write({"active": True, "started_at": started, "message": "long task"})
        rc, out = cli("out")
        assert rc == 0
        assert "45m" in out
        with db.connect() as conn:
            row = conn.execute("SELECT * FROM entries").fetchone()
        # tolerate ±2s scheduling jitter between state.write and out command
        assert abs(row["duration_s"] - 45 * 60) <= 2
        assert row["message"] == "long task"


class TestPunchReportCommand:
    def _seed(self) -> None:
        now = timeutil.now()
        with db.connect() as conn:
            for offset_h, dur, tags in [
                (1, 3600, "backend"),
                (2, 1800, "backend,bug"),
                (24, 3600, "docs"),
                (240, 1200, None),  # 10 days ago, untagged
            ]:
                started = now - timedelta(hours=offset_h)
                ended = started + timedelta(seconds=dur)
                conn.execute(
                    "INSERT INTO entries (started_at, ended_at, duration_s, message, tags) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (started.isoformat(), ended.isoformat(), dur, None, tags),
                )
            conn.commit()

    def test_empty_db(self, cli: Callable[..., tuple[int, str]]) -> None:
        rc, out = cli("report")
        assert rc == 0
        assert "No sessions found" in out

    def test_all_time(self, cli: Callable[..., tuple[int, str]]) -> None:
        self._seed()
        rc, out = cli("report")
        assert rc == 0
        assert "All Time" in out
        assert "backend" in out
        assert "Total" in out
        assert "(4 sessions)" in out

    def test_today_filter(self, cli: Callable[..., tuple[int, str]]) -> None:
        self._seed()
        rc, out = cli("report", "--today")
        assert rc == 0
        assert "Today" in out
        assert "(2 sessions)" in out

    def test_week_filter(self, cli: Callable[..., tuple[int, str]]) -> None:
        self._seed()
        rc, out = cli("report", "--week")
        assert rc == 0
        assert "This Week" in out
        # seed has 3 entries within the past week (1h, 2h, 24h ago); 240h is 10d ago
        assert "(3 sessions)" in out

    def test_month_filter(self, cli: Callable[..., tuple[int, str]]) -> None:
        self._seed()
        rc, out = cli("report", "--month")
        assert rc == 0
        # label is "<Month> <Year>" — verify by checking current month name
        month_name = timeutil.now().strftime("%B %Y")
        assert month_name in out

    def test_explicit_date_range(
        self, cli: Callable[..., tuple[int, str]]
    ) -> None:
        self._seed()
        yesterday = (timeutil.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        rc, out = cli("report", "--from", yesterday, "--to", yesterday)
        assert rc == 0
        assert f"{yesterday} to {yesterday}" in out
        # only the 24h-ago entry falls on yesterday
        assert "(1 session)" in out

    def test_from_only(self, cli: Callable[..., tuple[int, str]]) -> None:
        self._seed()
        today = timeutil.now().strftime("%Y-%m-%d")
        rc, out = cli("report", "--from", today)
        assert rc == 0
        assert f"from {today}" in out
        assert "(2 sessions)" in out

    def test_tag_filter(self, cli: Callable[..., tuple[int, str]]) -> None:
        self._seed()
        rc, out = cli("report", "--tag", "backend")
        assert rc == 0
        assert "tag: backend" in out
        assert "(2 sessions)" in out

    def test_invalid_date_rejected(self, cli: Callable[..., tuple[int, str]]) -> None:
        rc, out = cli("report", "--from", "not-a-date")
        assert rc == 1
        assert "Invalid date" in out

    def test_write_regenerates_report_md(
        self, cli: Callable[..., tuple[int, str]], punch_dir: Path
    ) -> None:
        self._seed()
        rc, _ = cli("report", "--write")
        assert rc == 0
        text = (punch_dir / "REPORT.md").read_text(encoding="utf-8")
        assert "All-Time by Tag" in text
        assert "Recent Sessions" in text


def test_inactive_state_json_is_minimal(
    cli: Callable[..., tuple[int, str]], punch_dir: Path
) -> None:
    cli("in")
    cli("out")
    with (punch_dir / "state.json").open() as f:
        assert json.load(f) == {"active": False}
