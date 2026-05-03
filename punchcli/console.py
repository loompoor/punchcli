from __future__ import annotations

import sys
from typing import Any, TextIO

_quiet = False


def set_quiet(value: bool) -> None:
    global _quiet
    _quiet = value


def info(msg: str = "", **kwargs: Any) -> None:
    if _quiet:
        return
    print(msg, **kwargs)


def success(msg: str = "", **kwargs: Any) -> None:
    if _quiet:
        return
    print(msg, **kwargs)


def warn(msg: str = "", **kwargs: Any) -> None:
    print(msg, file=sys.stderr, **kwargs)


def error(msg: str = "", **kwargs: Any) -> None:
    print(msg, file=sys.stderr, **kwargs)


def data(text: str = "", *, stream: TextIO | None = None, end: str = "\n") -> None:
    out = stream if stream is not None else sys.stdout
    out.write(text)
    if end:
        out.write(end)
