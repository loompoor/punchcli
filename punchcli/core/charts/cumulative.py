from __future__ import annotations

from datetime import timedelta

import pygal

from punchcli.core import timeutil
from punchcli.core.charts.base import (
    Rows,
    empty_svg,
    pygal_style,
    strip_pygal_extras,
)

NAME = "cumulative"
DESC = "Cumulative hours over time (line chart)"


def render(rows: Rows) -> str:
    if not rows:
        return empty_svg("No sessions yet — line will climb as you log time.", width=900)

    by_day: dict = {}
    for r in rows:
        d = timeutil.from_iso(r["started_at"]).date()
        by_day[d] = by_day.get(d, 0) + r["duration_s"]
    days = sorted(by_day.keys())
    if not days:
        return empty_svg(width=900)

    start, end = days[0], days[-1]
    span = (end - start).days + 1
    if span < 7:
        end = start + timedelta(days=6)
        span = 7

    cumulative = []
    total = 0
    for i in range(span):
        d = start + timedelta(days=i)
        total += by_day.get(d, 0)
        cumulative.append(round(total / 3600, 2))

    chart = pygal.Line(
        style=pygal_style(),
        js=[],
        show_legend=False,
        title="Cumulative hours tracked",
        x_label_rotation=30,
        height=320,
        width=900,
        fill=True,
        show_dots=False,
        margin_bottom=40,
    )
    step = max(1, span // 12)
    chart.x_labels = [
        (start + timedelta(days=i)).strftime("%b %d") if i % step == 0 else ""
        for i in range(span)
    ]
    chart.add("Hours", cumulative)
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        + strip_pygal_extras(chart.render(is_unicode=True))
    )
