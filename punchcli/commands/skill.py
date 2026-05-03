from __future__ import annotations

import argparse
import sys
from pathlib import Path

from punchcli import console

_SKILL_MD = Path(__file__).resolve().parent.parent / "SKILL.md"


def run(_args: argparse.Namespace) -> int:
    if not _SKILL_MD.is_file():
        console.error("✗ SKILL.md not found in package")
        return 2
    sys.stdout.write(_SKILL_MD.read_text(encoding="utf-8"))
    return 0
