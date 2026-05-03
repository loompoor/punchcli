from __future__ import annotations

from pathlib import Path

from punchcli.core import db


def test_connect_creates_schema(punch_dir: Path) -> None:
    with db.connect() as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    assert "entries" in tables
    assert "schema_version" in tables


def test_migrations_idempotent(punch_dir: Path) -> None:
    with db.connect() as conn:
        (v1,) = conn.execute("SELECT version FROM schema_version").fetchone()
    with db.connect() as conn:
        (count,) = conn.execute("SELECT COUNT(*) FROM schema_version").fetchone()
        (v2,) = conn.execute("SELECT version FROM schema_version").fetchone()
    assert count == 1
    assert v1 == v2


def test_entries_columns(punch_dir: Path) -> None:
    with db.connect() as conn:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(entries)")}
    assert cols == {"id", "started_at", "ended_at", "duration_s", "message", "tags"}


def test_index_exists(punch_dir: Path) -> None:
    with db.connect() as conn:
        idx = {
            r[0]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
        }
    assert "idx_started_at" in idx


def test_wal_mode(punch_dir: Path) -> None:
    with db.connect() as conn:
        (mode,) = conn.execute("PRAGMA journal_mode").fetchone()
    assert mode.lower() == "wal"


def test_row_factory_is_row(punch_dir: Path) -> None:
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO entries (started_at, ended_at, duration_s, message, tags) "
            "VALUES (?, ?, ?, ?, ?)",
            ("2026-04-30T10:00:00+02:00", "2026-04-30T11:00:00+02:00", 3600, "x", "a"),
        )
        row = conn.execute("SELECT * FROM entries").fetchone()
    assert row["message"] == "x"
    assert row["duration_s"] == 3600
