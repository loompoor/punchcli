from __future__ import annotations

import os
import re
import sqlite3
import tempfile
from pathlib import Path

from pygal.style import Style

from punchcli.core import config_file
from punchcli.core.charts import styles


def pygal_style() -> Style:
    cfg = config_file.load().get("charts", {})
    return styles.get(cfg.get("style"))

_SCRIPT_RE = re.compile(r"<script\b[^>]*>.*?</script>", re.DOTALL)


def strip_pygal_extras(svg: str) -> str:
    if svg.startswith("<?xml"):
        svg = svg.split("?>", 1)[1].lstrip()
    return _SCRIPT_RE.sub("", svg)


def split_tags(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [t for t in raw.split(",") if t]


def hours(seconds: int) -> float:
    return round(seconds / 3600, 2)


def empty_svg(message: str = "No sessions yet.", width: int = 600, height: int = 120) -> str:
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n'
        '  <rect width="100%" height="100%" fill="transparent"/>\n'
        f'  <text x="{width // 2}" y="{height // 2 + 5}" text-anchor="middle" '
        'font-family="system, -apple-system, sans-serif" font-size="16" '
        f'fill="#888">{message}</text>\n'
        "</svg>\n"
    )


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".chart-", suffix=".svg", dir=str(path.parent))
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


Rows = list[sqlite3.Row]
