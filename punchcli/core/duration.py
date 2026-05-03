from __future__ import annotations

import re

_DURATION_RE = re.compile(r"^\s*(?:(\d+)h)?\s*(?:(\d+)m)?\s*$", re.IGNORECASE)


def format_duration(seconds: int) -> str:
    if seconds < 60:
        return "< 1m"
    minutes = seconds // 60
    h, m = divmod(minutes, 60)
    if h == 0:
        return f"{m}m"
    return f"{h}h {m:02d}m"


def parse_duration(s: str) -> int:
    """Parse '45m', '2h', '1h30m' → seconds. Raises ValueError."""
    if s is None or not s.strip():
        raise ValueError("Empty duration")
    m = _DURATION_RE.match(s)
    if not m or (m.group(1) is None and m.group(2) is None):
        raise ValueError(f"Invalid duration '{s}': expected forms like '45m', '2h', '1h30m'")
    h = int(m.group(1) or 0)
    mn = int(m.group(2) or 0)
    total = h * 3600 + mn * 60
    if total <= 0:
        raise ValueError(f"Duration must be positive: '{s}'")
    return total
