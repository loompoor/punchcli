from __future__ import annotations

from datetime import date

from punchcli.core import timeutil
from punchcli.core.charts.base import Rows, empty_svg, split_tags

NAME = "lifetime"
DESC = "Timeless big-number block: total, sessions, longest streak, top day, top tag"


def _longest_streak(daily: dict[date, int]) -> int:
    if not daily:
        return 0
    days = sorted(daily.keys())
    longest = 0
    cur = 0
    prev: date | None = None
    for d in days:
        cur = cur + 1 if prev is not None and (d - prev).days == 1 else 1
        longest = max(longest, cur)
        prev = d
    return longest


def render(rows: Rows) -> str:
    if not rows:
        return empty_svg(
            "No stats yet — start tracking with `punch in`.",
            width=900,
            height=160,
        )

    daily: dict[date, int] = {}
    by_tag: dict[str, int] = {}
    for r in rows:
        d = timeutil.from_iso(r["started_at"]).date()
        daily[d] = daily.get(d, 0) + r["duration_s"]
        for t in split_tags(r["tags"]):
            by_tag[t] = by_tag.get(t, 0) + r["duration_s"]

    total_s = sum(r["duration_s"] for r in rows)
    sessions = len(rows)
    days_tracked = len(daily)
    longest = _longest_streak(daily)
    top_day, top_day_s = max(daily.items(), key=lambda x: x[1])
    if by_tag:
        top_tag, top_tag_s = max(by_tag.items(), key=lambda x: x[1])
        top_tag_value = f"#{top_tag}"
        top_tag_sub = f"{top_tag_s / 3600:.0f}h logged"
    else:
        top_tag_value = "—"
        top_tag_sub = "no tags yet"

    width, height = 900, 160
    pad = 24
    cols = 5
    col_w = (width - pad * 2) / cols

    cells = [
        ("Total", f"{total_s / 3600:.0f}h", f"{sessions} sessions"),
        ("Days tracked", f"{days_tracked}", f"avg {(total_s / days_tracked) / 3600:.1f}h/day"),
        ("Longest streak", f"{longest}d", "consecutive days"),
        ("Top day", f"{top_day_s / 3600:.1f}h", top_day.strftime("%b %d, %Y")),
        ("Top tag", top_tag_value, top_tag_sub),
    ]

    body: list[str] = [
        f'<rect x="0" y="0" width="{width}" height="{height}" rx="12" fill="#0d1117"/>'
    ]
    for i, (label, value, sub) in enumerate(cells):
        cx = pad + col_w * (i + 0.5)
        body.append(
            f'<text x="{cx:.1f}" y="48" text-anchor="middle" font-size="12" '
            f'fill="#888" font-weight="500">{label.upper()}</text>'
        )
        body.append(
            f'<text x="{cx:.1f}" y="92" text-anchor="middle" font-size="32" '
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
