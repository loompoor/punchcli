from __future__ import annotations

import tomllib
from functools import lru_cache
from pathlib import Path
from typing import Any

from punchcli import console
from punchcli.config import punch_dir

FILENAME = "config.toml"

DEFAULT_TEXT = """# punchcli configuration — committed to git, edit freely.
# Run `punch chart --list` for available chart names.
# Run `punch chart --list-styles` for available style names.

[charts]
# Charts regenerated on `punch out` and `punch report --write`.
# `punch chart --all` ignores this list.
# Defaults below are README-safe (timeless or monotonic) — they don't go
# stale between commits. Add "stats" / "weekly" if you regen often.
enabled = ["heatmap", "lifetime", "tag_donut", "dow_bars"]

# Style applied to pygal charts (heatmap/stats use their own palette).
style = "github"

# Per-chart options are optional. Defaults shown.
# [charts.heatmap]
# weeks = 53
"""

DEFAULTS: dict[str, Any] = {
    "charts": {
        "enabled": ["heatmap", "lifetime", "tag_donut", "dow_bars"],
        "style": "github",
    },
}


def path() -> Path:
    return punch_dir() / FILENAME


def write_default(target: Path) -> None:
    if not target.exists():
        target.write_text(DEFAULT_TEXT, encoding="utf-8")


@lru_cache(maxsize=1)
def load() -> dict[str, Any]:
    try:
        p = path()
    except Exception:
        return DEFAULTS
    if not p.is_file():
        return DEFAULTS
    try:
        with p.open("rb") as f:
            data = tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError) as e:
        console.warn(f"⚠ {FILENAME}: parse error, using defaults — {e}")
        return DEFAULTS
    merged = {k: dict(v) for k, v in DEFAULTS.items()}
    for section, body in data.items():
        if isinstance(body, dict) and section in merged:
            merged[section] = {**merged[section], **body}
        else:
            merged[section] = body
    return merged


def reset_cache() -> None:
    load.cache_clear()
