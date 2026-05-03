from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from punchcli.config import state_path


def read(path: Path | None = None) -> dict[str, Any]:
    p = path or state_path()
    if not p.exists():
        return {"active": False}
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def write(data: dict[str, Any], path: Path | None = None) -> None:
    p = path or state_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".state-", suffix=".json", dir=str(p.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        os.replace(tmp, p)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def clear(path: Path | None = None) -> None:
    write({"active": False}, path)
