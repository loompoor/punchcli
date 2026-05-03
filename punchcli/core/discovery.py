from __future__ import annotations

from pathlib import Path

DIRNAME = ".punch"


def find_punch_dir(start: Path | None = None) -> Path | None:
    """Walk up from start (default: cwd) looking for a .punch/ directory."""
    cur = (start or Path.cwd()).resolve()
    while True:
        candidate = cur / DIRNAME
        if candidate.is_dir():
            return candidate
        if cur.parent == cur:
            return None
        cur = cur.parent
