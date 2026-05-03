from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Callable

import pytest

from punchcli.core import db, state, timeutil


def test_explicit_from_to(cli: Callable[..., tuple[int, str]], punch_dir: Path) -> None:
    rc, out = cli(
        "add",
        "--from", "yesterday 09:00",
        "--to", "yesterday 10:30",
        "-m", "morning standup",
        "-t", "meetings",
    )
    assert rc == 0
    assert "1h 30m" in out
    with db.connect() as conn:
        rows = list(conn.execute("SELECT * FROM entries"))
    assert len(rows) == 1
    assert rows[0]["duration_s"] == 90 * 60
    assert rows[0]["message"] == "morning standup"
    assert rows[0]["tags"] == "meetings"


def test_duration_with_to_now(cli: Callable[..., tuple[int, str]]) -> None:
    rc, out = cli("add", "--duration", "30m", "--to", "yesterday 14:00")
    assert rc == 0
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM entries").fetchone()
    assert row["duration_s"] == 30 * 60


def test_duration_with_from(cli: Callable[..., tuple[int, str]]) -> None:
    rc, _ = cli("add", "--from", "yesterday 09:00", "--duration", "1h30m")
    assert rc == 0
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM entries").fetchone()
    assert row["duration_s"] == 90 * 60


def test_only_one_arg_rejected(cli: Callable[..., tuple[int, str]]) -> None:
    rc, out = cli("add", "--duration", "30m")
    assert rc == 1
    assert "exactly two" in out


def test_all_three_args_rejected(cli: Callable[..., tuple[int, str]]) -> None:
    rc, out = cli(
        "add", "--from", "yesterday 09:00", "--to", "yesterday 10:00", "--duration", "1h"
    )
    assert rc == 1
    assert "exactly two" in out


def test_end_before_start_rejected(cli: Callable[..., tuple[int, str]]) -> None:
    rc, out = cli("add", "--from", "yesterday 10:00", "--to", "yesterday 09:00")
    assert rc == 1
    assert "End must be after start" in out


def test_future_rejected(cli: Callable[..., tuple[int, str]]) -> None:
    rc, out = cli(
        "add",
        "--from", "2999-01-01 00:00",
        "--to", "2999-01-01 01:00",
    )
    assert rc == 1
    assert "Future" in out


def test_invalid_tag_rejected(cli: Callable[..., tuple[int, str]]) -> None:
    rc, out = cli(
        "add", "--from", "yesterday 09:00", "--to", "yesterday 10:00", "-t", "BAD!!"
    )
    assert rc == 1
    assert "Invalid tag" in out


def test_force_skips_overlap_prompt(
    cli: Callable[..., tuple[int, str]], punch_dir: Path
) -> None:
    cli("add", "--from", "yesterday 09:00", "--to", "yesterday 10:00")
    rc, out = cli(
        "add",
        "--from", "yesterday 09:30",
        "--to", "yesterday 10:30",
        "--force",
    )
    assert rc == 0
    with db.connect() as conn:
        (count,) = conn.execute("SELECT COUNT(*) FROM entries").fetchone()
    assert count == 2


def test_overlap_prompts_and_aborts_on_no(
    cli: Callable[..., tuple[int, str]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cli("add", "--from", "yesterday 09:00", "--to", "yesterday 10:00")
    monkeypatch.setattr("builtins.input", lambda _: "n")
    rc, out = cli("add", "--from", "yesterday 09:30", "--to", "yesterday 10:30")
    assert rc == 1
    assert "Aborted" in out
    with db.connect() as conn:
        (count,) = conn.execute("SELECT COUNT(*) FROM entries").fetchone()
    assert count == 1


def test_overlap_prompts_and_inserts_on_yes(
    cli: Callable[..., tuple[int, str]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cli("add", "--from", "yesterday 09:00", "--to", "yesterday 10:00")
    monkeypatch.setattr("builtins.input", lambda _: "y")
    rc, _ = cli("add", "--from", "yesterday 09:30", "--to", "yesterday 10:30")
    assert rc == 0
    with db.connect() as conn:
        (count,) = conn.execute("SELECT COUNT(*) FROM entries").fetchone()
    assert count == 2


def test_active_session_overlap_warns(
    cli: Callable[..., tuple[int, str]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # active session started 2h ago; window in last 30min must overlap it
    started = (timeutil.now() - timedelta(hours=2)).isoformat()
    state.write({"active": True, "started_at": started})
    monkeypatch.setattr("builtins.input", lambda _: "n")
    start = (timeutil.now() - timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M")
    end = (timeutil.now() - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M")
    rc, out = cli("add", "--from", start, "--to", end)
    assert rc == 1
    assert "active session" in out


def test_does_not_touch_state(
    cli: Callable[..., tuple[int, str]], punch_dir: Path
) -> None:
    cli("add", "--from", "yesterday 09:00", "--to", "yesterday 10:00")
    assert state.read() == {"active": False}


def test_regenerates_report_md(
    cli: Callable[..., tuple[int, str]], punch_dir: Path
) -> None:
    cli("add", "--from", "yesterday 09:00", "--to", "yesterday 10:00", "-m", "x")
    report_md = punch_dir / "REPORT.md"
    assert report_md.exists()
    assert "x" in report_md.read_text(encoding="utf-8")
