from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path

from punchcli import console
from punchcli.core import db, report, state, timeutil, validate

REQUIRED_COLS = {"started_at", "ended_at"}


def _confirm(prompt: str) -> bool:
    try:
        return input(prompt).strip().lower() in ("y", "yes")
    except EOFError:
        return False


def _parse_row(row: dict[str, str]) -> tuple[datetime, datetime, str | None, str | None]:
    started = timeutil.parse_timestamp(row["started_at"])
    ended = timeutil.parse_timestamp(row["ended_at"])
    if ended <= started:
        raise ValueError("end <= start")
    now = timeutil.now()
    if started > now or ended > now:
        raise ValueError("future timestamp")
    raw_msg = (row.get("message") or "").strip() or None
    message = validate.validate_message(raw_msg)
    raw_tags = (row.get("tags") or "").strip()
    tags_list = validate.parse_tags(raw_tags) if raw_tags else []
    tags_csv = ",".join(tags_list) if tags_list else None
    return started, ended, message, tags_csv


def _has_overlap(conn, start: datetime, end: datetime) -> bool:
    for r in conn.execute("SELECT started_at, ended_at FROM entries"):
        s = timeutil.from_iso(r["started_at"])
        e = timeutil.from_iso(r["ended_at"])
        if not (e <= start or s >= end):
            return True
    cur = state.read()
    if cur.get("active"):
        s = timeutil.from_iso(cur["started_at"])
        if s < end:
            return True
    return False


def run(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.is_file():
        console.error(f"✗ File not found: {path}")
        return 2

    try:
        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames or not REQUIRED_COLS.issubset(reader.fieldnames):
                missing = REQUIRED_COLS - set(reader.fieldnames or [])
                console.error(
                    f"✗ CSV missing required columns: {','.join(sorted(missing))}"
                )
                return 2
            raw_rows = list(reader)
    except (OSError, csv.Error) as e:
        console.error(f"✗ Read failed: {e}")
        return 2

    parsed: list[tuple[int, datetime, datetime, str | None, str | None]] = []
    skipped = 0
    for i, row in enumerate(raw_rows, start=2):  # line 1 = header
        try:
            s, e, msg, tags_csv = _parse_row(row)
        except (ValueError, validate.ValidationError) as err:
            console.warn(f"⚠ line {i}: skipped — {err}")
            skipped += 1
            continue
        parsed.append((i, s, e, msg, tags_csv))

    if args.dry_run:
        console.info(f"Dry-run: {len(parsed)} would insert, {skipped} skipped.")
        return 0

    inserted = 0
    try:
        with db.connect() as conn:
            for line_no, s, e, msg, tags_csv in parsed:
                if not args.force and _has_overlap(conn, s, e):
                    console.warn(f"⚠ line {line_no}: overlaps existing entry")
                    if not _confirm("  Insert anyway? [y/N]: "):
                        skipped += 1
                        continue
                conn.execute(
                    "INSERT INTO entries (started_at, ended_at, duration_s, "
                    "message, tags) VALUES (?, ?, ?, ?, ?)",
                    (
                        timeutil.to_iso(s),
                        timeutil.to_iso(e),
                        int((e - s).total_seconds()),
                        msg,
                        tags_csv,
                    ),
                )
                inserted += 1
            conn.commit()
    except Exception as e:
        console.error(f"✗ Import failed, rolled back: {e}")
        return 2

    if inserted:
        report.regenerate()

    console.info(f"{inserted} inserted, {skipped} skipped.")
    return 0
