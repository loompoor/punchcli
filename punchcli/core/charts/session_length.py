from __future__ import annotations

import pygal

from punchcli.core.charts.base import (
    Rows,
    empty_svg,
    pygal_style,
    strip_pygal_extras,
)

NAME = "session_length"
DESC = "Histogram of session durations — timeless"

BUCKETS = (
    ("<15m", 0, 15 * 60),
    ("15–30m", 15 * 60, 30 * 60),
    ("30m–1h", 30 * 60, 60 * 60),
    ("1–2h", 60 * 60, 2 * 60 * 60),
    ("2–4h", 2 * 60 * 60, 4 * 60 * 60),
    ("4h+", 4 * 60 * 60, None),
)


def render(rows: Rows) -> str:
    if not rows:
        return empty_svg("No sessions yet.", width=900)

    counts = [0] * len(BUCKETS)
    for r in rows:
        d = r["duration_s"]
        for i, (_, lo, hi) in enumerate(BUCKETS):
            if d >= lo and (hi is None or d < hi):
                counts[i] += 1
                break

    chart = pygal.Bar(
        style=pygal_style(),
        js=[],
        show_legend=False,
        title="Session length distribution",
        height=320,
        width=900,
        margin_bottom=40,
    )
    chart.x_labels = [label for label, _, _ in BUCKETS]
    chart.add("Sessions", counts)
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        + strip_pygal_extras(chart.render(is_unicode=True))
    )
