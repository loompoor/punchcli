from __future__ import annotations

from datetime import timedelta

from punchcli.core import timeutil
from punchcli.core.charts.base import Rows, empty_svg

NAME = "hour_of_day"
DESC = "When-do-I-work heatmap (7 days × 24 hours)"

CELL = 28
GAP = 3
PAD_LEFT = 50
PAD_TOP = 36

DOW = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
_PALETTE = ["#1f1f23", "#0e4429", "#006d32", "#26a641", "#39d353"]


def _level(seconds: int, max_s: int) -> int:
    if max_s == 0 or seconds == 0:
        return 0
    ratio = seconds / max_s
    if ratio < 0.25:
        return 1
    if ratio < 0.5:
        return 2
    if ratio < 0.75:
        return 3
    return 4


def render(rows: Rows) -> str:
    if not rows:
        return empty_svg("No sessions yet.", width=900, height=300)

    grid: dict[tuple[int, int], int] = {}
    for r in rows:
        s = timeutil.from_iso(r["started_at"])
        e = timeutil.from_iso(r["ended_at"])
        cur = s
        while cur < e:
            next_hour = cur.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            slice_end = min(next_hour, e)
            secs = int((slice_end - cur).total_seconds())
            grid[(cur.weekday(), cur.hour)] = grid.get((cur.weekday(), cur.hour), 0) + secs
            cur = slice_end

    max_s = max(grid.values()) if grid else 0
    width = PAD_LEFT + 24 * (CELL + GAP) + 20
    height = PAD_TOP + 7 * (CELL + GAP) + 20

    body: list[str] = []
    for h in range(24):
        if h % 3 == 0:
            x = PAD_LEFT + h * (CELL + GAP) + CELL // 2
            body.append(
                f'<text x="{x}" y="{PAD_TOP - 8}" text-anchor="middle" '
                f'font-size="10" fill="#888">{h:02d}</text>'
            )
    for d in range(7):
        y = PAD_TOP + d * (CELL + GAP) + CELL - 8
        body.append(
            f'<text x="{PAD_LEFT - 8}" y="{y}" text-anchor="end" '
            f'font-size="10" fill="#888">{DOW[d]}</text>'
        )
    for d in range(7):
        for h in range(24):
            secs = grid.get((d, h), 0)
            lvl = _level(secs, max_s)
            x = PAD_LEFT + h * (CELL + GAP)
            y = PAD_TOP + d * (CELL + GAP)
            mins = secs // 60
            tip = f"{DOW[d]} {h:02d}:00 — {mins} min"
            body.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="3" '
                f'fill="{_PALETTE[lvl]}"><title>{tip}</title></rect>'
            )

    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" '
        'font-family="system, -apple-system, sans-serif">\n'
        + "\n".join("  " + b for b in body) + "\n"
        '</svg>\n'
    )
