from __future__ import annotations

from pathlib import Path
from typing import Callable

from punchcli.core import db


def _seed(cli: Callable[..., tuple[int, str]]) -> int:
    cli(
        "add",
        "--from", "yesterday 09:00",
        "--to", "yesterday 10:00",
        "-m", "orig",
        "-t", "backend",
    )
    with db.connect() as conn:
        row = conn.execute("SELECT id FROM entries").fetchone()
    return row["id"]


def test_missing_id_rejected(cli: Callable[..., tuple[int, str]]) -> None:
    rc, _ = cli("edit", "--end", "yesterday 11:00")
    assert rc != 0


def test_no_fields_rejected(cli: Callable[..., tuple[int, str]]) -> None:
    eid = _seed(cli)
    rc, out = cli("edit", str(eid))
    assert rc == 1
    assert "Provide at least one" in out


def test_unknown_id_rejected(cli: Callable[..., tuple[int, str]]) -> None:
    _seed(cli)
    rc, out = cli("edit", "999", "-m", "x")
    assert rc == 1
    assert "No entry with id 999" in out


def test_extends_end_recomputes_duration(
    cli: Callable[..., tuple[int, str]],
) -> None:
    eid = _seed(cli)
    rc, out = cli("edit", str(eid), "--end", "yesterday 12:00")
    assert rc == 0
    assert "3h 00m" in out
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM entries WHERE id=?", (eid,)).fetchone()
    assert row["duration_s"] == 3 * 3600


def test_changes_start_keeps_other_fields(
    cli: Callable[..., tuple[int, str]],
) -> None:
    eid = _seed(cli)
    cli("edit", str(eid), "--start", "yesterday 08:30")
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM entries WHERE id=?", (eid,)).fetchone()
    assert row["duration_s"] == 90 * 60
    assert row["message"] == "orig"
    assert row["tags"] == "backend"


def test_message_update(cli: Callable[..., tuple[int, str]]) -> None:
    eid = _seed(cli)
    cli("edit", str(eid), "-m", "new msg")
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM entries WHERE id=?", (eid,)).fetchone()
    assert row["message"] == "new msg"
    assert row["tags"] == "backend"


def test_message_clear(cli: Callable[..., tuple[int, str]]) -> None:
    eid = _seed(cli)
    cli("edit", str(eid), "-m", "")
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM entries WHERE id=?", (eid,)).fetchone()
    assert row["message"] is None


def test_tags_replace(cli: Callable[..., tuple[int, str]]) -> None:
    eid = _seed(cli)
    cli("edit", str(eid), "-t", "frontend,docs")
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM entries WHERE id=?", (eid,)).fetchone()
    assert row["tags"] == "frontend,docs"


def test_tags_clear(cli: Callable[..., tuple[int, str]]) -> None:
    eid = _seed(cli)
    cli("edit", str(eid), "-t", "")
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM entries WHERE id=?", (eid,)).fetchone()
    assert row["tags"] is None


def test_invalid_tag_rejected(cli: Callable[..., tuple[int, str]]) -> None:
    eid = _seed(cli)
    rc, out = cli("edit", str(eid), "-t", "BAD!!")
    assert rc == 1
    assert "Invalid tag" in out


def test_end_before_start_rejected(cli: Callable[..., tuple[int, str]]) -> None:
    eid = _seed(cli)
    rc, out = cli("edit", str(eid), "--end", "yesterday 08:00")
    assert rc == 1
    assert "End must be after start" in out


def test_future_rejected(cli: Callable[..., tuple[int, str]]) -> None:
    eid = _seed(cli)
    rc, out = cli(
        "edit",
        str(eid),
        "--start", "2999-01-01 00:00",
        "--end", "2999-01-01 01:00",
    )
    assert rc == 1
    assert "Future" in out


def test_regenerates_report(
    cli: Callable[..., tuple[int, str]], punch_dir: Path
) -> None:
    eid = _seed(cli)
    cli("edit", str(eid), "-m", "afterward")
    text = (punch_dir / "REPORT.md").read_text(encoding="utf-8")
    assert "afterward" in text


def test_combined_edit_all_fields_at_once(
    cli: Callable[..., tuple[int, str]],
) -> None:
    eid = _seed(cli)
    rc, _ = cli(
        "edit",
        str(eid),
        "--start", "yesterday 08:00",
        "--end", "yesterday 09:15",
        "-m", "",
        "-t", "",
    )
    assert rc == 0
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM entries WHERE id=?", (eid,)).fetchone()
    assert row["duration_s"] == 75 * 60
    assert row["message"] is None
    assert row["tags"] is None
