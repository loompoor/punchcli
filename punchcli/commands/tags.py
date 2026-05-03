from __future__ import annotations

import argparse

from punchcli import console
from punchcli.core import db, timeutil
from punchcli.core.duration import format_duration


def run(_args: argparse.Namespace) -> int:
    with db.connect() as conn:
        rows = list(conn.execute("SELECT started_at, duration_s, tags FROM entries"))

    if not rows:
        console.info("No tags yet.")
        return 0

    totals: dict[str, int] = {}
    last_used: dict[str, str] = {}  # YYYY-MM-DD per tag
    untagged_total = 0
    untagged_last = ""

    for r in rows:
        started = timeutil.from_iso(r["started_at"])
        date_str = started.strftime("%Y-%m-%d")
        tags = [t for t in (r["tags"] or "").split(",") if t]
        if not tags:
            untagged_total += r["duration_s"]
            if date_str > untagged_last:
                untagged_last = date_str
        else:
            for t in tags:
                totals[t] = totals.get(t, 0) + r["duration_s"]
                if date_str > last_used.get(t, ""):
                    last_used[t] = date_str

    rows_out: list[tuple[str, str, str]] = [
        (name, format_duration(s), f"(last: {last_used[name]})")
        for name, s in sorted(totals.items(), key=lambda x: (-x[1], x[0]))
    ]
    if untagged_total:
        rows_out.append(
            ("(untagged)", format_duration(untagged_total), f"(last: {untagged_last})")
        )

    name_w = max(len(r[0]) for r in rows_out)
    dur_w = max(len(r[1]) for r in rows_out)

    console.info("Tags")
    console.info()
    for name, dur, last in rows_out:
        console.info(f"{name:<{name_w}}  {dur:>{dur_w}}   {last}")
    return 0
