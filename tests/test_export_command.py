from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Callable

from punchcli.core import db


def _seed(cli: Callable[..., tuple[int, str]]) -> None:
    cli("add", "--from", "yesterday 09:00", "--to", "yesterday 10:00",
        "-m", "alpha", "-t", "backend")
    cli("add", "--from", "yesterday 11:00", "--to", "yesterday 12:30",
        "-m", "beta", "-t", "frontend,docs")


def test_csv_format_and_rows(cli: Callable[..., tuple[int, str]]) -> None:
    _seed(cli)
    rc, out = cli("export", "--csv")
    assert rc == 0
    rows = list(csv.DictReader(io.StringIO(out)))
    assert len(rows) == 2
    assert set(rows[0].keys()) == {
        "id", "started_at", "ended_at", "duration_s", "message", "tags"
    }
    assert rows[0]["message"] == "alpha"
    assert rows[1]["tags"] == "frontend,docs"


def test_md_format(cli: Callable[..., tuple[int, str]]) -> None:
    _seed(cli)
    rc, out = cli("export", "--md")
    assert rc == 0
    assert "| Date | Start | End |" in out
    assert "alpha" in out
    assert "frontend,docs" in out


def test_filter_by_tag(cli: Callable[..., tuple[int, str]]) -> None:
    _seed(cli)
    rc, out = cli("export", "--csv", "--tag", "backend")
    rows = list(csv.DictReader(io.StringIO(out)))
    assert len(rows) == 1
    assert rows[0]["message"] == "alpha"


def test_format_required(cli: Callable[..., tuple[int, str]]) -> None:
    _seed(cli)
    rc, _ = cli("export")
    assert rc != 0


def test_empty_db(cli: Callable[..., tuple[int, str]]) -> None:
    cli("init")
    rc, out = cli("export", "--csv")
    assert rc == 0
    rows = list(csv.DictReader(io.StringIO(out)))
    assert rows == []


def test_csv_roundtrip_via_import(
    cli: Callable[..., tuple[int, str]], punch_dir: Path
) -> None:
    _seed(cli)
    _, out = cli("export", "--csv")
    csv_path = punch_dir / "dump.csv"
    csv_path.write_text(out, encoding="utf-8")

    with db.connect() as conn:
        conn.execute("DELETE FROM entries")
        conn.commit()

    rc, msg = cli("import", str(csv_path))
    assert rc == 0
    assert "2 inserted" in msg
    with db.connect() as conn:
        (count,) = conn.execute("SELECT COUNT(*) FROM entries").fetchone()
    assert count == 2
