from __future__ import annotations

import io
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Callable

import pytest


@pytest.fixture
def punch_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Isolate each test in a fresh PUNCH_DIR via env var."""
    monkeypatch.setenv("PUNCH_DIR", str(tmp_path))
    from punchcli.core import config_file
    config_file.reset_cache()
    return tmp_path


def _make_runner() -> Callable[..., tuple[int, str]]:
    from punchcli.__main__ import main

    def run(*argv: str) -> tuple[int, str]:
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        try:
            with redirect_stdout(out_buf), redirect_stderr(err_buf):
                rc = main(list(argv))
        except SystemExit as e:
            code = e.code
            if isinstance(code, int):
                rc = code
            elif code is None:
                rc = 0
            else:
                rc = 1
        return rc, out_buf.getvalue() + err_buf.getvalue()

    return run


@pytest.fixture
def cli(punch_dir: Path) -> Callable[..., tuple[int, str]]:
    """Invoke the punch CLI in-process with PUNCH_DIR override."""
    return _make_runner()


@pytest.fixture
def cli_bare() -> Callable[..., tuple[int, str]]:
    """Invoke the punch CLI without setting PUNCH_DIR. Use with fresh_repo."""
    return _make_runner()


@pytest.fixture
def fresh_repo(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Tmp dir as cwd, no PUNCH_DIR env. Simulates a fresh project."""
    monkeypatch.delenv("PUNCH_DIR", raising=False)
    monkeypatch.chdir(tmp_path)
    return tmp_path
