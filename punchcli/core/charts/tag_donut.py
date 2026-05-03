from __future__ import annotations

import pygal

from punchcli.core.charts.base import (
    Rows,
    empty_svg,
    pygal_style,
    split_tags,
    strip_pygal_extras,
)

NAME = "tag_donut"
DESC = "Tag breakdown as donut chart"

MAX_TAGS = 8


def render(rows: Rows) -> str:
    if not rows:
        return empty_svg("No sessions yet.", width=600, height=400)

    by_tag: dict = {}
    untagged = 0
    for r in rows:
        tags = split_tags(r["tags"])
        if tags:
            for t in tags:
                by_tag[t] = by_tag.get(t, 0) + r["duration_s"]
        else:
            untagged += r["duration_s"]

    items = sorted(by_tag.items(), key=lambda x: -x[1])
    top = items[:MAX_TAGS]
    other = sum(s for _, s in items[MAX_TAGS:])

    chart = pygal.Pie(
        style=pygal_style(),
        js=[],
        inner_radius=0.55,
        title="Hours by tag",
        height=420,
        width=720,
        legend_at_bottom=True,
        truncate_legend=20,
    )
    if not top and not untagged and not other:
        return empty_svg("No tagged sessions.", width=600, height=400)

    for name, s in top:
        chart.add(name, round(s / 3600, 2))
    if other:
        chart.add("other", round(other / 3600, 2))
    if untagged:
        chart.add("(untagged)", round(untagged / 3600, 2))

    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        + strip_pygal_extras(chart.render(is_unicode=True))
    )
