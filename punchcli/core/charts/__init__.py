from __future__ import annotations

from pathlib import Path
from typing import Callable, Protocol

from punchcli import console
from punchcli.config import punch_dir
from punchcli.core import config_file, db
from punchcli.core.charts import (
    base,
    cumulative,
    dow_bars,
    heatmap,
    hour_of_day,
    lifetime,
    session_length,
    stats,
    tag_donut,
    weekly,
)


class _ChartModule(Protocol):
    NAME: str
    DESC: str
    render: Callable[[base.Rows], str]


_MODULES: tuple[_ChartModule, ...] = (
    heatmap,
    lifetime,
    stats,
    cumulative,
    weekly,
    tag_donut,
    dow_bars,
    session_length,
    hour_of_day,
)

REGISTRY: dict[str, _ChartModule] = {m.NAME: m for m in _MODULES}


def names() -> list[str]:
    return list(REGISTRY.keys())


def describe() -> list[tuple[str, str]]:
    return [(m.NAME, m.DESC) for m in _MODULES]


CHARTS_DIRNAME = "charts"


def charts_dir() -> Path:
    return punch_dir() / CHARTS_DIRNAME


def _load_rows() -> base.Rows:
    with db.connect() as conn:
        return list(conn.execute("SELECT * FROM entries ORDER BY started_at ASC"))


def render(name: str, rows: base.Rows | None = None) -> str:
    mod = REGISTRY[name]
    return mod.render(_load_rows() if rows is None else rows)


def write(name: str, path: Path | None = None) -> Path:
    rows = _load_rows()
    svg = REGISTRY[name].render(rows)
    target = path or (charts_dir() / f"{name}.svg")
    base.atomic_write(target, svg)
    return target


def write_all() -> list[Path]:
    rows = _load_rows()
    out: list[Path] = []
    cdir = charts_dir()
    for name, mod in REGISTRY.items():
        target = cdir / f"{name}.svg"
        base.atomic_write(target, mod.render(rows))
        out.append(target)
    return out


def enabled_names() -> list[str]:
    raw = config_file.load().get("charts", {}).get("enabled", [])
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for n in raw:
        if n in REGISTRY:
            out.append(n)
        else:
            console.warn(
                f"⚠ config.toml: unknown chart '{n}' in charts.enabled (skipped)"
            )
    return out


def write_enabled() -> list[Path]:
    names = enabled_names()
    if not names:
        return []
    rows = _load_rows()
    out: list[Path] = []
    cdir = charts_dir()
    for name in names:
        target = cdir / f"{name}.svg"
        base.atomic_write(target, REGISTRY[name].render(rows))
        out.append(target)
    return out
