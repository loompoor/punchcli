from __future__ import annotations

import argparse

from punchcli import console
from punchcli.core import db, report, timeutil
from punchcli.core.duration import format_duration


def _resolve_period(args):
    if args.today:
        s, e = timeutil.today_bounds()
        return s, e
    if args.week:
        s, e = timeutil.week_bounds()
        return s, e
    if args.month:
        s, e = timeutil.month_bounds()
        return s, e
    return None, None


def run(args: argparse.Namespace) -> int:
    start, end = _resolve_period(args)

    with db.connect() as conn:
        rows = list(conn.execute("SELECT * FROM entries ORDER BY started_at DESC"))

    rows = report.filter_entries(rows, start=start, end=end, tag=args.tag)
    rows = rows[: args.n]

    if not rows:
        console.info("No sessions found.")
        return 0

    parsed = []
    for r in rows:
        s = timeutil.from_iso(r["started_at"])
        e = timeutil.from_iso(r["ended_at"])
        parsed.append(
            (
                s.strftime("%Y-%m-%d"),
                s.strftime("%H:%M"),
                e.strftime("%H:%M"),
                format_duration(r["duration_s"]),
                r["message"] or "",
                r["tags"] or "",
            )
        )

    headers = ("Date", "Start", "End", "Duration", "Message", "Tags")
    widths = [
        max(len(h), max(len(row[i]) for row in parsed)) for i, h in enumerate(headers)
    ]

    def fmt_row(row):
        return "  ".join(str(v).ljust(widths[i]) for i, v in enumerate(row))

    console.data(fmt_row(headers))
    console.data("─" * (sum(widths) + 2 * (len(headers) - 1)))
    for row in parsed:
        console.data(fmt_row(row))
    return 0
