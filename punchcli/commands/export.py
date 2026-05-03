from __future__ import annotations

import argparse
import csv
import sys
from datetime import timedelta

from punchcli import console
from punchcli.core import db, report, timeutil
from punchcli.core.duration import format_duration

CSV_HEADER = ["id", "started_at", "ended_at", "duration_s", "message", "tags"]


def _resolve_bounds(args: argparse.Namespace):
    start = (
        timeutil.local_midnight(timeutil.parse_local_date(args.from_))
        if args.from_
        else None
    )
    end = (
        timeutil.local_midnight(
            timeutil.parse_local_date(args.to) + timedelta(days=1)
        )
        if args.to
        else None
    )
    return start, end


def _emit_csv(rows) -> None:
    writer = csv.writer(sys.stdout)
    writer.writerow(CSV_HEADER)
    for r in rows:
        writer.writerow([
            r["id"],
            r["started_at"],
            r["ended_at"],
            r["duration_s"],
            r["message"] or "",
            r["tags"] or "",
        ])


def _emit_md(rows) -> None:
    console.data("| Date | Start | End | Duration | Message | Tags |")
    console.data("|------|-------|-----|----------|---------|------|")
    for r in rows:
        s = timeutil.from_iso(r["started_at"])
        e = timeutil.from_iso(r["ended_at"])
        msg = (r["message"] or "").replace("|", "\\|")
        tags = (r["tags"] or "").replace("|", "\\|")
        console.data(
            f"| {s.strftime('%Y-%m-%d')} | {s.strftime('%H:%M')} | "
            f"{e.strftime('%H:%M')} | {format_duration(r['duration_s'])} | "
            f"{msg} | {tags} |"
        )


def run(args: argparse.Namespace) -> int:
    try:
        start, end = _resolve_bounds(args)
    except ValueError as e:
        console.error(f"✗ Invalid date: {e}")
        return 1

    with db.connect() as conn:
        rows = list(conn.execute("SELECT * FROM entries ORDER BY started_at ASC"))

    filtered = report.filter_entries(rows, start=start, end=end, tag=args.tag)

    if args.csv:
        _emit_csv(filtered)
    else:
        _emit_md(filtered)
    return 0
