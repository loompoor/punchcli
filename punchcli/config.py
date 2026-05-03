from __future__ import annotations

import os
from pathlib import Path

from punchcli.core.discovery import find_punch_dir


class PunchDirNotFound(Exception):
    pass


def punch_dir() -> Path:
    env = os.environ.get("PUNCH_DIR")
    if env:
        return Path(env).expanduser()
    found = find_punch_dir()
    if found is None:
        raise PunchDirNotFound(
            "No .punch/ found in current directory or any parent. "
            "Run `punch init` to create one."
        )
    return found


def db_path() -> Path:
    return punch_dir() / "punch.db"


def state_path() -> Path:
    return punch_dir() / "state.json"


def report_path() -> Path:
    return punch_dir() / "REPORT.md"
