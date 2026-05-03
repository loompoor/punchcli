from __future__ import annotations

import os
import sqlite3
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable

from punchcli.config import report_path
from punchcli.core import charts, db, timeutil
from punchcli.core.duration import format_duration


@dataclass
class ReportData:
    period_label: str
    rows: list[sqlite3.Row]
    total_s: int = 0
    session_count: int = 0
    by_tag: list[tuple[str, int]] = field(default_factory=list)
    untagged_s: int = 0


def _split_tags(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [t for t in raw.split(",") if t]


def filter_entries(
    rows: Iterable[sqlite3.Row],
    *,
    start: datetime | None = None,
    end: datetime | None = None,
    tag: str | None = None,
) -> list[sqlite3.Row]:
    out: list[sqlite3.Row] = []
    tag_lc = tag.lower() if tag else None
    for r in rows:
        s = timeutil.from_iso(r["started_at"])
        if start and s < start:
            continue
        if end and s >= end:
            continue
        if tag_lc and tag_lc not in _split_tags(r["tags"]):
            continue
        out.append(r)
    return out


def aggregate(rows: list[sqlite3.Row], period_label: str = "All Time") -> ReportData:
    total = 0
    by_tag: dict[str, int] = {}
    untagged = 0
    for r in rows:
        d = r["duration_s"]
        total += d
        tags = _split_tags(r["tags"])
        if tags:
            for t in tags:
                by_tag[t] = by_tag.get(t, 0) + d
        else:
            untagged += d
    sorted_tags = sorted(by_tag.items(), key=lambda x: (-x[1], x[0]))
    return ReportData(
        period_label=period_label,
        rows=rows,
        total_s=total,
        session_count=len(rows),
        by_tag=sorted_tags,
        untagged_s=untagged,
    )


def render_console(data: ReportData) -> str:
    lines = [f"Time Report — {data.period_label}", ""]
    if data.session_count == 0:
        lines.append("No sessions found.")
        return "\n".join(lines) + "\n"

    pairs: list[tuple[str, str]] = [
        (name, format_duration(s)) for name, s in data.by_tag
    ]
    if data.untagged_s:
        pairs.append(("(untagged)", format_duration(data.untagged_s)))

    total_label = "Total"
    name_w = max([len(n) for n, _ in pairs] + [len(total_label)])
    dur_w = max([len(d) for _, d in pairs] + [len(format_duration(data.total_s))])

    if pairs:
        lines.append("By tag:")
        for name, dur in pairs:
            lines.append(f"  {name:<{name_w}}  {dur:>{dur_w}}")
        lines.append("─" * (name_w + dur_w + 4))

    sessions = "session" if data.session_count == 1 else "sessions"
    lines.append(
        f"{total_label:<{name_w}}  {format_duration(data.total_s):>{dur_w}}  "
        f"({data.session_count} {sessions})"
    )
    return "\n".join(lines) + "\n"


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".report-", suffix=".md", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _render_markdown(rows: list[sqlite3.Row]) -> str:
    updated = timeutil.now().strftime("%Y-%m-%d %H:%M")
    if not rows:
        return (
            "# Time Report\n\n"
            "_No sessions logged yet._\n\n"
            f"_Last updated: {updated}_\n"
        )

    total_s = sum(r["duration_s"] for r in rows)
    sessions = "session" if len(rows) == 1 else "sessions"

    out: list[str] = [
        "# Time Report",
        "",
        f"**Total**: {format_duration(total_s)} across {len(rows)} {sessions}",
        f"_Last updated: {updated}_",
        "",
    ]

    # This Month section
    m_start, m_end = timeutil.month_bounds()
    month_rows = filter_entries(rows, start=m_start, end=m_end)
    if month_rows:
        month_label = m_start.strftime("%B %Y")
        out += [f"## This Month — {month_label}", "", "| Week | Hours |", "|------|-------|"]
        weeks: dict[tuple[int, int], int] = {}
        for r in month_rows:
            iso_year, iso_week, _ = timeutil.from_iso(r["started_at"]).isocalendar()
            weeks[(iso_year, iso_week)] = weeks.get((iso_year, iso_week), 0) + r["duration_s"]
        for (_, wk), s in sorted(weeks.items(), key=lambda x: x[0], reverse=True):
            out.append(f"| W{wk:02d} | {format_duration(s)} |")
        out.append("")

    # All-Time by Tag
    data = aggregate(rows)
    if data.by_tag or data.untagged_s:
        out += ["## All-Time by Tag", "", "| Tag | Hours |", "|-----|-------|"]
        for tag, s in data.by_tag:
            out.append(f"| {tag} | {format_duration(s)} |")
        if data.untagged_s:
            out.append(f"| _untagged_ | {format_duration(data.untagged_s)} |")
        out.append("")

    # Recent Sessions
    recent = sorted(rows, key=lambda r: r["started_at"], reverse=True)[:10]
    out += [
        "## Recent Sessions (last 10)",
        "",
        "| Date | Start | End | Duration | Message | Tags |",
        "|------|-------|-----|----------|---------|------|",
    ]
    for r in recent:
        s = timeutil.from_iso(r["started_at"])
        e = timeutil.from_iso(r["ended_at"])
        msg = (r["message"] or "").replace("|", "\\|")
        tags = (r["tags"] or "").replace("|", "\\|")
        out.append(
            f"| {s.strftime('%Y-%m-%d')} | {s.strftime('%H:%M')} | "
            f"{e.strftime('%H:%M')} | {format_duration(r['duration_s'])} | "
            f"{msg} | {tags} |"
        )
    out.append("")

    return "\n".join(out)


def regenerate(path: Path | None = None) -> None:
    with db.connect() as conn:
        rows = list(conn.execute("SELECT * FROM entries ORDER BY started_at ASC"))
    text = _render_markdown(rows)
    _atomic_write(path or report_path(), text)
    charts.write_enabled()
