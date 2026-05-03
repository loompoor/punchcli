from __future__ import annotations

import argparse
from datetime import datetime

from punchcli import console
from punchcli.core import db, report, state, timeutil, validate
from punchcli.core.duration import format_duration, parse_duration


def _resolve_window(args) -> tuple[datetime, datetime]:
    have = sum(x is not None for x in (args.from_, args.to, args.duration))
    if have != 2:
        raise ValueError(
            "Provide exactly two of --from, --to, --duration"
        )
    start = timeutil.parse_timestamp(args.from_) if args.from_ else None
    end = timeutil.parse_timestamp(args.to) if args.to else None
    if args.duration:
        dur_s = parse_duration(args.duration)
        if start is not None and end is None:
            end = start + _seconds(dur_s)
        elif end is not None and start is None:
            start = end - _seconds(dur_s)
    if start is None or end is None:
        raise ValueError("Could not resolve start and end")
    if end <= start:
        raise ValueError("End must be after start")
    if start > timeutil.now() or end > timeutil.now():
        raise ValueError("Future timestamps not allowed")
    return start, end


def _seconds(s: int):
    from datetime import timedelta
    return timedelta(seconds=s)


def _find_overlaps(conn, start: datetime, end: datetime) -> list:
    rows = list(conn.execute("SELECT * FROM entries"))
    out = []
    for r in rows:
        s = timeutil.from_iso(r["started_at"])
        e = timeutil.from_iso(r["ended_at"])
        if not (e <= start or s >= end):
            out.append(r)
    return out


def _active_overlaps(start: datetime, end: datetime) -> bool:
    cur = state.read()
    if not cur.get("active"):
        return False
    s = timeutil.from_iso(cur["started_at"])
    return s < end


def _confirm(prompt: str) -> bool:
    try:
        ans = input(prompt).strip().lower()
    except EOFError:
        return False
    return ans in ("y", "yes")


def run(args: argparse.Namespace) -> int:
    try:
        start, end = _resolve_window(args)
        tags = validate.parse_tags(args.tags)
        message = validate.validate_message(args.message)
    except (ValueError, validate.ValidationError) as e:
        console.error(f"✗ {e}")
        return 1

    if not args.force:
        with db.connect() as conn:
            overlaps = _find_overlaps(conn, start, end)
        warnings = []
        if overlaps:
            warnings.append(f"{len(overlaps)} existing entry overlap(s)")
        if _active_overlaps(start, end):
            warnings.append("active session overlaps")
        if warnings:
            console.warn(f"⚠ Overlap: {', '.join(warnings)}")
            if not _confirm("Continue? [y/N]: "):
                console.error("Aborted.")
                return 1

    duration_s = int((end - start).total_seconds())
    tags_csv = ",".join(tags) if tags else None

    with db.connect() as conn:
        conn.execute(
            "INSERT INTO entries (started_at, ended_at, duration_s, message, tags) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                timeutil.to_iso(start),
                timeutil.to_iso(end),
                duration_s,
                message,
                tags_csv,
            ),
        )
        conn.commit()

    report.regenerate()

    parts = [
        f"✓ Added {format_duration(duration_s)} on {start.strftime('%Y-%m-%d')}",
        f"({start.strftime('%H:%M')} → {end.strftime('%H:%M')})",
    ]
    if message:
        parts.append(f'— "{message}"')
    if tags:
        parts.append(f"[{', '.join(tags)}]")
    console.success(" ".join(parts))
    return 0
