from __future__ import annotations

import argparse
from pathlib import Path

from punchcli import console
from punchcli.core import config_file, db
from punchcli.core.discovery import DIRNAME

_GITIGNORE = "state.json\n"


def _write_gitignore(target: Path) -> None:
    gi = target / ".gitignore"
    if not gi.exists():
        gi.write_text(_GITIGNORE, encoding="utf-8")


def _write_config(target: Path) -> None:
    config_file.write_default(target / config_file.FILENAME)
    config_file.reset_cache()


def run(_args: argparse.Namespace) -> int:
    target = Path.cwd() / DIRNAME
    if target.exists():
        _write_gitignore(target)
        _write_config(target)
        console.info(f".punch/ already exists at {target}")
        return 0
    target.mkdir(parents=True)
    db.connect(target / "punch.db").close()
    _write_gitignore(target)
    _write_config(target)
    console.success(f"✓ Initialized .punch/ at {target}")
    return 0
