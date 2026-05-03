from __future__ import annotations

from typing import Callable


def test_version_flag(cli: Callable[..., tuple[int, str]]) -> None:
    rc, out = cli("--version")
    assert rc == 0
    assert "punchcli" in out


def test_no_subcommand_rejected(cli: Callable[..., tuple[int, str]]) -> None:
    rc, _ = cli()
    assert rc != 0
