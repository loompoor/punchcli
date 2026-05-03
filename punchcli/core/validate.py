from __future__ import annotations

import re

_TAG_RE = re.compile(r"^[a-z0-9_-]{1,32}$")
MAX_MESSAGE_LEN = 256
MAX_TAGS = 5


class ValidationError(ValueError):
    pass


def parse_tags(raw: str | None) -> list[str]:
    if not raw:
        return []
    parts = [t.strip().lower() for t in raw.split(",")]
    parts = [t for t in parts if t]
    for t in parts:
        if not _TAG_RE.match(t):
            raise ValidationError(
                f"Invalid tag '{t}': must match [a-z0-9_-], 1-32 chars"
            )
    seen: set[str] = set()
    out: list[str] = []
    for t in parts:
        if t not in seen:
            seen.add(t)
            out.append(t)
    if len(out) > MAX_TAGS:
        raise ValidationError(
            f"Too many tags ({len(out)}): max {MAX_TAGS} per entry"
        )
    return out


def validate_message(msg: str | None) -> str | None:
    if msg is None:
        return None
    if "\n" in msg:
        raise ValidationError("Message must not contain newlines")
    if len(msg) > MAX_MESSAGE_LEN:
        raise ValidationError(f"Message exceeds {MAX_MESSAGE_LEN} chars")
    return msg
