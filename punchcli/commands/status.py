from __future__ import annotations

import argparse

from punchcli import console
from punchcli.core import duration, state, timeutil


def run(args: argparse.Namespace) -> int:
    current = state.read()
    if not current.get("active"):
        console.info("No active session.")
        return 0

    started_at = timeutil.from_iso(current["started_at"])
    elapsed_s = max(0, int((timeutil.now() - started_at).total_seconds()))

    console.info("Active session:")
    console.info(
        f"  Started  : {started_at.strftime('%H:%M')} "
        f"({duration.format_duration(elapsed_s)} ago)"
    )
    if current.get("message"):
        console.info(f"  Message  : {current['message']}")
    if current.get("tags"):
        console.info(f"  Tags     : {', '.join(current['tags'])}")
    return 0
