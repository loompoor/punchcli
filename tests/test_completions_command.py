from __future__ import annotations

from typing import Callable

import pytest


@pytest.mark.parametrize(
    "shell,token",
    [
        ("bash", "complete"),
        ("zsh", "compdef"),
        ("fish", "complete"),
    ],
)
def test_prints_shell_snippet(
    cli: Callable[..., tuple[int, str]], shell: str, token: str
) -> None:
    rc, out = cli("completions", shell)
    assert rc == 0
    assert token in out
    assert "punch" in out


def test_unknown_shell_rejected(cli: Callable[..., tuple[int, str]]) -> None:
    rc, _ = cli("completions", "tcsh")
    assert rc != 0
