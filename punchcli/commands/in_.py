from __future__ import annotations

import argparse

from punchcli import console
from punchcli.core import state, timeutil, validate


def run(args: argparse.Namespace) -> int:
    current = state.read()
    if current.get("active"):
        started = current.get("started_at", "?")
        try:
            t = timeutil.from_iso(started).strftime("%H:%M")
        except (ValueError, TypeError):
            t = started
        console.error(f"✗ Already tracking since {t}. Run `punch out` first.")
        return 1

    try:
        tags = validate.parse_tags(args.tags)
        message = validate.validate_message(args.message)
    except validate.ValidationError as e:
        console.error(f"✗ {e}")
        return 1

    started_at = timeutil.now()
    payload: dict = {
        "active": True,
        "started_at": timeutil.to_iso(started_at),
    }
    if message:
        payload["message"] = message
    if tags:
        payload["tags"] = tags

    state.write(payload)

    parts = [f"⏱  Started tracking at {started_at.strftime('%H:%M')}"]
    if message:
        parts.append(f'— "{message}"')
    if tags:
        parts.append(f"[{', '.join(tags)}]")
    console.success(" ".join(parts))
    return 0
