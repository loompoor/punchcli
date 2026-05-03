from __future__ import annotations

from typing import Callable


def test_prints_skill_md(cli: Callable[..., tuple[int, str]]) -> None:
    rc, out = cli("skill")
    assert rc == 0
    assert out.startswith("---")
    assert "name: punchcli" in out
    assert "## Commands" in out
    assert "punch in" in out
