from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta


def now() -> datetime:
    return datetime.now().astimezone()


def to_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.astimezone()
    return dt.isoformat()


def from_iso(s: str) -> datetime:
    return datetime.fromisoformat(s)


def parse_local_date(s: str) -> date:
    return date.fromisoformat(s)


def local_midnight(d: date) -> datetime:
    return datetime.combine(d, time.min).astimezone()


def today_bounds(reference: datetime | None = None) -> tuple[datetime, datetime]:
    today = (reference or now()).date()
    return local_midnight(today), local_midnight(today + timedelta(days=1))


def week_bounds(reference: datetime | None = None) -> tuple[datetime, datetime]:
    ref = (reference or now()).date()
    monday = ref - timedelta(days=ref.weekday())
    return local_midnight(monday), local_midnight(monday + timedelta(days=7))


def month_bounds(reference: datetime | None = None) -> tuple[datetime, datetime]:
    ref = (reference or now()).date()
    start = local_midnight(date(ref.year, ref.month, 1))
    next_month = (
        date(ref.year + 1, 1, 1)
        if ref.month == 12
        else date(ref.year, ref.month + 1, 1)
    )
    return start, local_midnight(next_month)


_HHMM_RE = re.compile(r"^(\d{1,2}):(\d{2})$")
_DATE_TIME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\s+(\d{1,2}):(\d{2})$")
_RELATIVE_RE = re.compile(r"^(today|yesterday)\s+(\d{1,2}):(\d{2})$", re.IGNORECASE)


def _attach_local_tz(dt: datetime) -> datetime:
    return dt.astimezone() if dt.tzinfo is not None else dt.astimezone()


def parse_timestamp(s: str, *, reference: datetime | None = None) -> datetime:
    """Parse user-supplied timestamp. Accepts:
    - ISO 8601 (with or without offset)
    - 'YYYY-MM-DD HH:MM' (local tz applied)
    - 'HH:MM' (today, local tz)
    - 'today HH:MM' / 'yesterday HH:MM' (local tz)
    Raises ValueError on bad input.
    """
    if s is None:
        raise ValueError("Empty timestamp")
    raw = s.strip()
    if not raw:
        raise ValueError("Empty timestamp")
    today = (reference or now()).date()

    m = _RELATIVE_RE.match(raw)
    if m:
        word, hh, mm = m.group(1).lower(), int(m.group(2)), int(m.group(3))
        d = today if word == "today" else today - timedelta(days=1)
        return datetime.combine(d, time(hh, mm)).astimezone()

    m = _DATE_TIME_RE.match(raw)
    if m:
        d = date.fromisoformat(m.group(1))
        return datetime.combine(d, time(int(m.group(2)), int(m.group(3)))).astimezone()

    m = _HHMM_RE.match(raw)
    if m:
        return datetime.combine(today, time(int(m.group(1)), int(m.group(2)))).astimezone()

    # ISO 8601 fallback
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError as e:
        raise ValueError(f"Invalid timestamp '{s}': {e}") from None
    return dt.astimezone() if dt.tzinfo is None else dt
