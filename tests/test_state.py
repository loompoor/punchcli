from __future__ import annotations

import json
from pathlib import Path

from punchcli.core import state


def test_read_missing_returns_inactive(punch_dir: Path) -> None:
    assert state.read() == {"active": False}


def test_write_then_read_roundtrip(punch_dir: Path) -> None:
    payload = {
        "active": True,
        "started_at": "2026-04-30T10:00:00+02:00",
        "message": "parser fix",
        "tags": ["backend", "bug"],
    }
    state.write(payload)
    assert state.read() == payload


def test_clear(punch_dir: Path) -> None:
    state.write({"active": True, "started_at": "2026-04-30T10:00:00+02:00"})
    state.clear()
    assert state.read() == {"active": False}


def test_no_leftover_tmp_files(punch_dir: Path) -> None:
    state.write({"active": True, "started_at": "2026-04-30T10:00:00+02:00"})
    leftovers = [p for p in punch_dir.iterdir() if p.name.startswith(".state-")]
    assert leftovers == []


def test_file_is_utf8_json(punch_dir: Path) -> None:
    state.write({"active": True, "started_at": "2026-04-30T10:00:00+02:00"})
    with (punch_dir / "state.json").open("r", encoding="utf-8") as f:
        assert json.load(f)["active"] is True


def test_creates_dir_if_missing(punch_dir: Path) -> None:
    for p in punch_dir.iterdir():
        p.unlink()
    punch_dir.rmdir()
    state.write({"active": False})
    assert (punch_dir / "state.json").exists()
