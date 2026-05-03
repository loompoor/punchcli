from __future__ import annotations

import argparse

from punchcli import console
from punchcli.core import db, duration, report, state, timeutil


def run(args: argparse.Namespace) -> int:
    current = state.read()
    if not current.get("active"):
        console.error("✗ No active session. Run `punch in` to start.")
        return 1

    started_at = timeutil.from_iso(current["started_at"])
    ended_at = timeutil.now()
    duration_s = max(0, int((ended_at - started_at).total_seconds()))

    message = current.get("message")
    tags = current.get("tags") or []
    tags_csv = ",".join(tags) if tags else None

    with db.connect() as conn:
        conn.execute(
            "INSERT INTO entries (started_at, ended_at, duration_s, message, tags) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                timeutil.to_iso(started_at),
                timeutil.to_iso(ended_at),
                duration_s,
                message,
                tags_csv,
            ),
        )
        conn.commit()

    state.clear()
    report.regenerate()
    console.success(f"✓ Stopped — {duration.format_duration(duration_s)} logged")
    return 0
