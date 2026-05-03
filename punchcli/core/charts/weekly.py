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

NAME = "weekly"
DESC = "Weekly totals — last 12 weeks (bar chart)"

WEEKS = 12


def render(rows: Rows) -> str:
    if not rows:
        return empty_svg("No sessions yet.", width=900)

    today = timeutil.now().date()
    monday_this = today - timedelta(days=today.weekday())
    start = monday_this - timedelta(weeks=WEEKS - 1)

    buckets: dict = {start + timedelta(weeks=i): 0 for i in range(WEEKS)}
    for r in rows:
        d = timeutil.from_iso(r["started_at"]).date()
        if d < start:
            continue
        wk = d - timedelta(days=d.weekday())
        if wk in buckets:
            buckets[wk] += r["duration_s"]

    weeks = sorted(buckets.items())
    chart = pygal.Bar(
        style=pygal_style(),
        js=[],
        show_legend=False,
        title=f"Weekly totals — last {WEEKS} weeks",
        x_label_rotation=30,
        height=320,
        width=900,
        margin_bottom=40,
    )
    chart.x_labels = [w.strftime("%b %d") for w, _ in weeks]
    chart.add("Hours", [round(s / 3600, 2) for _, s in weeks])
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        + strip_pygal_extras(chart.render(is_unicode=True))
    )
