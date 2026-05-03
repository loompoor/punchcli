from __future__ import annotations

import argparse
from datetime import datetime, timedelta

from punchcli import console
from punchcli.core import db, report, timeutil


class _PeriodError(ValueError):
    pass


def _resolve_period(args: argparse.Namespace) -> tuple[datetime | None, datetime | None, str]:
    if args.from_ or args.to:
        try:
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
        except ValueError as e:
            raise _PeriodError(str(e))
        if args.from_ and args.to:
            label = f"{args.from_} to {args.to}"
        elif args.from_:
            label = f"from {args.from_}"
        else:
            label = f"up to {args.to}"
        return start, end, label

    if args.today:
        start, end = timeutil.today_bounds()
        return start, end, f"Today ({start.strftime('%Y-%m-%d')})"

    if args.week:
        start, end = timeutil.week_bounds()
        iso = start.isocalendar()
        return start, end, f"This Week (W{iso.week:02d} {iso.year})"

    if args.month:
        start, end = timeutil.month_bounds()
        return start, end, start.strftime("%B %Y")

    return None, None, "All Time"


def run(args: argparse.Namespace) -> int:
    try:
        start, end, label = _resolve_period(args)
    except _PeriodError as e:
        console.error(f"✗ Invalid date: {e}")
        return 1

    with db.connect() as conn:
        rows = list(conn.execute("SELECT * FROM entries ORDER BY started_at ASC"))

    filtered = report.filter_entries(rows, start=start, end=end, tag=args.tag)
    if args.tag:
        label = f"{label} — tag: {args.tag.lower()}"

    data = report.aggregate(filtered, period_label=label)
    console.data(report.render_console(data), end="")

    if args.write:
        report.regenerate()
        console.info()
        console.info("REPORT.md regenerated.")

    return 0
