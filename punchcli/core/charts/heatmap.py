from __future__ import annotations

from datetime import date, timedelta

from punchcli.core import config_file, timeutil
from punchcli.core.charts.base import Rows, empty_svg

NAME = "heatmap"
DESC = "GitHub-style contribution heatmap (last ~52 weeks)"

DEFAULT_WEEKS = 53
CELL = 12
GAP = 2
PAD_TOP = 26
PAD_LEFT = 28


def _level(hours: float) -> int:
    if hours <= 0:
        return 0
    if hours < 1:
        return 1
    if hours < 2:
        return 2
    if hours < 4:
        return 3
    return 4


_PALETTE = ["#1f1f23", "#0e4429", "#006d32", "#26a641", "#39d353"]


def render(rows: Rows) -> str:
    cfg = config_file.load().get("charts", {}).get("heatmap", {})
    weeks = int(cfg.get("weeks", DEFAULT_WEEKS))

    if not rows:
        return empty_svg("No sessions yet — heatmap fills in as you log time.", width=800)

    today = timeutil.now().date()
    end = today + timedelta(days=(6 - today.weekday()))
    start = end - timedelta(days=weeks * 7 - 1)

    daily_s: dict[date, int] = {}
    for r in rows:
        d = timeutil.from_iso(r["started_at"]).date()
        if start <= d <= end:
            daily_s[d] = daily_s.get(d, 0) + r["duration_s"]

    width = PAD_LEFT + weeks * (CELL + GAP) + 20
    height = PAD_TOP + 7 * (CELL + GAP) + 30

    cells: list[str] = []
    for w in range(weeks):
        for dow in range(7):
            d = start + timedelta(days=w * 7 + dow)
            if d > today:
                continue
            h = daily_s.get(d, 0) / 3600
            lvl = _level(h)
            x = PAD_LEFT + w * (CELL + GAP)
            y = PAD_TOP + dow * (CELL + GAP)
            tip = f"{d.isoformat()}: {h:.1f}h"
            cells.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" '
                f'fill="{_PALETTE[lvl]}"><title>{tip}</title></rect>'
            )

    dow_labels = []
    for i, lbl in enumerate(("Mon", "Wed", "Fri")):
        y = PAD_TOP + (i * 2 + 1) * (CELL + GAP) + CELL - 2
        dow_labels.append(
            f'<text x="{PAD_LEFT - 6}" y="{y}" text-anchor="end" '
            f'font-size="10" fill="#888">{lbl}</text>'
        )

    month_labels = []
    seen: set[str] = set()
    for w in range(weeks):
        d = start + timedelta(days=w * 7)
        m = d.strftime("%b")
        if d.day <= 7 and m not in seen:
            x = PAD_LEFT + w * (CELL + GAP)
            month_labels.append(
                f'<text x="{x}" y="{PAD_TOP - 8}" font-size="10" fill="#888">{m}</text>'
            )
            seen.add(m)

    legend_y = PAD_TOP + 7 * (CELL + GAP) + 16
    legend_x = width - 200
    legend = [f'<text x="{legend_x - 30}" y="{legend_y + 10}" font-size="10" fill="#888">Less</text>']
    for i, color in enumerate(_PALETTE):
        x = legend_x + i * (CELL + GAP)
        legend.append(
            f'<rect x="{x}" y="{legend_y}" width="{CELL}" height="{CELL}" rx="2" fill="{color}"/>'
        )
    legend.append(
        f'<text x="{legend_x + len(_PALETTE) * (CELL + GAP) + 4}" y="{legend_y + 10}" '
        f'font-size="10" fill="#888">More</text>'
    )

    total_h = sum(daily_s.values()) / 3600
    title = f'<text x="{PAD_LEFT}" y="16" font-size="13" fill="#ccc" font-weight="600">' \
            f'{total_h:.0f} hours in the last year</text>'

    body = "\n".join(month_labels + dow_labels + cells + legend)
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" '
        'font-family="system, -apple-system, sans-serif">\n'
        f'  {title}\n'
        f'  {body}\n'
        '</svg>\n'
    )
