from __future__ import annotations

import argparse

from punchcli import console
from punchcli.core import db, report, timeutil, validate
from punchcli.core.duration import format_duration


def run(args: argparse.Namespace) -> int:
    if (
        args.start is None
        and args.end is None
        and args.message is None
        and args.tags is None
    ):
        console.error("✗ Provide at least one of --start, --end, --message, --tags")
        return 1

    with db.connect() as conn:
        row = conn.execute(
            "SELECT * FROM entries WHERE id = ?", (args.entry_id,)
        ).fetchone()
        if row is None:
            console.error(f"✗ No entry with id {args.entry_id}")
            return 1

        try:
            started = (
                timeutil.parse_timestamp(args.start)
                if args.start is not None
                else timeutil.from_iso(row["started_at"])
            )
            ended = (
                timeutil.parse_timestamp(args.end)
                if args.end is not None
                else timeutil.from_iso(row["ended_at"])
            )
        except ValueError as e:
            console.error(f"✗ {e}")
            return 1

        if ended <= started:
            console.error("✗ End must be after start")
            return 1
        now = timeutil.now()
        if started > now or ended > now:
            console.error("✗ Future timestamps not allowed")
            return 1

        try:
            if args.message is None:
                message = row["message"]
            elif args.message == "":
                message = None
            else:
                message = validate.validate_message(args.message)

            if args.tags is None:
                tags_csv = row["tags"]
            elif args.tags == "":
                tags_csv = None
            else:
                tags_list = validate.parse_tags(args.tags)
                tags_csv = ",".join(tags_list) if tags_list else None
        except validate.ValidationError as e:
            console.error(f"✗ {e}")
            return 1

        duration_s = int((ended - started).total_seconds())

        conn.execute(
            "UPDATE entries SET started_at=?, ended_at=?, duration_s=?, "
            "message=?, tags=? WHERE id=?",
            (
                timeutil.to_iso(started),
                timeutil.to_iso(ended),
                duration_s,
                message,
                tags_csv,
                args.entry_id,
            ),
        )
        conn.commit()

    report.regenerate()

    parts = [
        f"✓ Updated entry {args.entry_id} — {format_duration(duration_s)}",
        f"({started.strftime('%H:%M')} → {ended.strftime('%H:%M')})",
    ]
    if message:
        parts.append(f'— "{message}"')
    if tags_csv:
        parts.append(f"[{tags_csv}]")
    console.success(" ".join(parts))
    return 0
