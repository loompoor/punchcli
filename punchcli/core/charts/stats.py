from __future__ import annotations

from datetime import date, timedelta

from punchcli.core import timeutil
from punchcli.core.charts.base import Rows, empty_svg

NAME = "stats"
DESC = "Big-number stat block: total, streak, this week, top day"


def _streaks(daily: dict[date, int], today: date) -> tuple[int, int]:
    if not daily:
        return 0, 0
    days = sorted(daily.keys())
    longest = 0
    cur = 0
    prev: date | None = None
    for d in days:
        if prev is not None and (d - prev).days == 1:
            cur += 1
        else:
            cur = 1
        longest = max(longest, cur)
        prev = d
    current = 0
    d = today
    while d in daily:
        current += 1
        d -= timedelta(days=1)
    return current, longest


def render(rows: Rows) -> str:
    if not rows:
        return empty_svg("No stats yet — start tracking with `punch in`.", width=900, height=140)

    today = timeutil.now().date()
    daily: dict[date, int] = {}
    for r in rows:
        d = timeutil.from_iso(r["started_at"]).date()
        daily[d] = daily.get(d, 0) + r["duration_s"]

    total_s = sum(r["duration_s"] for r in rows)
    week_start = today - timedelta(days=today.weekday())
    week_s = sum(s for d, s in daily.items() if d >= week_start)
    top_day, top_s = max(daily.items(), key=lambda x: x[1])
    cur_streak, max_streak = _streaks(daily, today)
    sessions = len(rows)

    width, height = 900, 160
    pad = 24
    cols = 5
    col_w = (width - pad * 2) / cols

    cells = [
        ("Total", f"{total_s / 3600:.0f}h", f"{sessions} sessions"),
        ("This week", f"{week_s / 3600:.1f}h", week_start.strftime("week of %b %d")),
        ("Current streak", f"{cur_streak}d", f"longest {max_streak}d"),
        ("Top day", f"{top_s / 3600:.1f}h", top_day.strftime("%b %d, %Y")),
        ("Avg / active day", f"{(total_s / len(daily)) / 3600:.1f}h", f"{len(daily)} days logged"),
    ]

    body: list[str] = []
    body.append(
        f'<rect x="0" y="0" width="{width}" height="{height}" rx="12" fill="#0d1117"/>'
    )
    for i, (label, value, sub) in enumerate(cells):
        cx = pad + col_w * (i + 0.5)
        body.append(
            f'<text x="{cx:.1f}" y="48" text-anchor="middle" font-size="12" '
            f'fill="#888" font-weight="500">{label.upper()}</text>'
        )
        body.append(
            f'<text x="{cx:.1f}" y="92" text-anchor="middle" font-size="36" '
            f'fill="#39d353" font-weight="700">{value}</text>'
        )
        body.append(
            f'<text x="{cx:.1f}" y="120" text-anchor="middle" font-size="11" '
            f'fill="#888">{sub}</text>'
        )

    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" '
        'font-family="system, -apple-system, sans-serif">\n'
        + "\n".join("  " + b for b in body) + "\n"
        '</svg>\n'
    )
