from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest

from punchcli.core import db


def _write_csv(path: Path, rows: list[str]) -> None:
    header = "id,started_at,ended_at,duration_s,message,tags"
    path.write_text("\n".join([header, *rows]) + "\n", encoding="utf-8")


def _yesterday_iso(hh: int, mm: int = 0) -> str:
    from punchcli.core import timeutil
    from datetime import timedelta
    d = (timeutil.now() - timedelta(days=1)).replace(
        hour=hh, minute=mm, second=0, microsecond=0
    )
    return d.isoformat()


def test_missing_file(cli: Callable[..., tuple[int, str]], punch_dir: Path) -> None:
    cli("init")
    rc, _ = cli("import", str(punch_dir / "nope.csv"))
    assert rc == 2


def test_missing_required_columns(
    cli: Callable[..., tuple[int, str]], punch_dir: Path
) -> None:
    cli("init")
    p = punch_dir / "bad.csv"
    p.write_text("foo,bar\n1,2\n", encoding="utf-8")
    rc, _ = cli("import", str(p))
    assert rc == 2


def test_inserts_valid_rows(
    cli: Callable[..., tuple[int, str]], punch_dir: Path
) -> None:
    cli("init")
    p = punch_dir / "ok.csv"
    _write_csv(p, [
        f",{_yesterday_iso(9)},{_yesterday_iso(10)},,morning,backend",
        f",{_yesterday_iso(11)},{_yesterday_iso(12, 30)},,afternoon,docs",
    ])
    rc, out = cli("import", str(p))
    assert rc == 0
    assert "2 inserted, 0 skipped" in out
    with db.connect() as conn:
        rows = list(conn.execute("SELECT * FROM entries ORDER BY started_at"))
    assert len(rows) == 2
    assert rows[0]["message"] == "morning"
    assert rows[0]["duration_s"] == 3600
    assert rows[1]["duration_s"] == 90 * 60


def test_recomputes_duration_from_timestamps(
    cli: Callable[..., tuple[int, str]], punch_dir: Path
) -> None:
    cli("init")
    p = punch_dir / "dur.csv"
    # provided duration_s=999 must be ignored
    _write_csv(p, [f",{_yesterday_iso(9)},{_yesterday_iso(10)},999,x,"])
    cli("import", str(p))
    with db.connect() as conn:
        row = conn.execute("SELECT duration_s FROM entries").fetchone()
    assert row["duration_s"] == 3600


def test_skips_invalid_rows(
    cli: Callable[..., tuple[int, str]], punch_dir: Path
) -> None:
    cli("init")
    p = punch_dir / "mixed.csv"
    _write_csv(p, [
        f",{_yesterday_iso(9)},{_yesterday_iso(10)},,ok,",
        ",not-a-time,nope,,bad,",
        f",{_yesterday_iso(11)},{_yesterday_iso(10)},,end-before-start,",  # invalid
    ])
    rc, out = cli("import", str(p))
    assert rc == 0
    assert "1 inserted" in out
    assert "2 skipped" in out


def test_dry_run_inserts_nothing(
    cli: Callable[..., tuple[int, str]], punch_dir: Path
) -> None:
    cli("init")
    p = punch_dir / "dry.csv"
    _write_csv(p, [f",{_yesterday_iso(9)},{_yesterday_iso(10)},,x,"])
    rc, out = cli("import", str(p), "--dry-run")
    assert rc == 0
    assert "Dry-run" in out
    with db.connect() as conn:
        (count,) = conn.execute("SELECT COUNT(*) FROM entries").fetchone()
    assert count == 0


def test_overlap_skipped_without_force(
    cli: Callable[..., tuple[int, str]],
    punch_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cli("add", "--from", "yesterday 09:00", "--to", "yesterday 10:00")
    p = punch_dir / "overlap.csv"
    _write_csv(p, [f",{_yesterday_iso(9, 30)},{_yesterday_iso(10, 30)},,x,"])
    monkeypatch.setattr("builtins.input", lambda _: "n")
    rc, out = cli("import", str(p))
    assert rc == 0
    assert "0 inserted" in out
    with db.connect() as conn:
        (count,) = conn.execute("SELECT COUNT(*) FROM entries").fetchone()
    assert count == 1


def test_force_skips_overlap_prompt(
    cli: Callable[..., tuple[int, str]], punch_dir: Path
) -> None:
    cli("add", "--from", "yesterday 09:00", "--to", "yesterday 10:00")
    p = punch_dir / "force.csv"
    _write_csv(p, [f",{_yesterday_iso(9, 30)},{_yesterday_iso(10, 30)},,x,"])
    rc, out = cli("import", str(p), "--force")
    assert rc == 0
    assert "1 inserted" in out
    with db.connect() as conn:
        (count,) = conn.execute("SELECT COUNT(*) FROM entries").fetchone()
    assert count == 2


def test_regenerates_report(
    cli: Callable[..., tuple[int, str]], punch_dir: Path
) -> None:
    cli("init")
    p = punch_dir / "ok.csv"
    _write_csv(p, [f",{_yesterday_iso(9)},{_yesterday_iso(10)},,signal,"])
    cli("import", str(p))
    text = (punch_dir / "REPORT.md").read_text(encoding="utf-8")
    assert "signal" in text


def test_id_column_ignored(
    cli: Callable[..., tuple[int, str]], punch_dir: Path
) -> None:
    cli("init")
    p = punch_dir / "ids.csv"
    _write_csv(p, [
        f"500,{_yesterday_iso(9)},{_yesterday_iso(10)},,a,",
        f"501,{_yesterday_iso(11)},{_yesterday_iso(12)},,b,",
    ])
    cli("import", str(p))
    with db.connect() as conn:
        ids = [r["id"] for r in conn.execute("SELECT id FROM entries ORDER BY id")]
    assert ids == [1, 2]
