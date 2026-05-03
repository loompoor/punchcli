from __future__ import annotations

import pygal

from punchcli.core import timeutil
from punchcli.core.charts.base import (
    Rows,
    empty_svg,
    pygal_style,
    strip_pygal_extras,
)

NAME = "dow_bars"
DESC = "Average hours per day-of-week (Mon–Sun) — timeless"

DOW = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def render(rows: Rows) -> str:
    if not rows:
        return empty_svg("No sessions yet.", width=900)

    by_dow_total: dict[int, int] = {i: 0 for i in range(7)}
    by_dow_days: dict[int, set] = {i: set() for i in range(7)}
    for r in rows:
        d = timeutil.from_iso(r["started_at"]).date()
        dow = d.weekday()
        by_dow_total[dow] += r["duration_s"]
        by_dow_days[dow].add(d)

    averages = []
    for i in range(7):
        n = len(by_dow_days[i])
        avg = (by_dow_total[i] / n / 3600) if n else 0
        averages.append(round(avg, 2))

    chart = pygal.Bar(
        style=pygal_style(),
        js=[],
        show_legend=False,
        title="Average hours by day of week",
        height=320,
        width=900,
        margin_bottom=40,
    )
    chart.x_labels = list(DOW)
    chart.add("Avg hours", averages)
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        + strip_pygal_extras(chart.render(is_unicode=True))
    )
