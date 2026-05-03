from __future__ import annotations

from pathlib import Path

import pytest

from punchcli.config import PunchDirNotFound, punch_dir
from punchcli.core.discovery import find_punch_dir


def test_find_in_cwd(fresh_repo: Path) -> None:
    (fresh_repo / ".punch").mkdir()
    assert find_punch_dir(fresh_repo) == fresh_repo / ".punch"


def test_find_in_parent(fresh_repo: Path) -> None:
    (fresh_repo / ".punch").mkdir()
    nested = fresh_repo / "src" / "deep"
    nested.mkdir(parents=True)
    assert find_punch_dir(nested) == fresh_repo / ".punch"


def test_returns_none_when_missing(fresh_repo: Path) -> None:
    nested = fresh_repo / "no-punch-here"
    nested.mkdir()
    # walk could find one in a parent of tmp; protect by ensuring none up the tree
    # — pytest tmp_path lives under /private/var/.../pytest-of-* with no .punch
    found = find_punch_dir(nested)
    # accept None or a parent-level hit not under fresh_repo
    if found is not None:
        assert fresh_repo not in found.parents


def test_punch_dir_raises_without_init(fresh_repo: Path) -> None:
    with pytest.raises(PunchDirNotFound):
        punch_dir()


def test_punch_dir_uses_env_override(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("PUNCH_DIR", str(tmp_path))
    assert punch_dir() == tmp_path


def test_punch_dir_returns_discovered(fresh_repo: Path) -> None:
    (fresh_repo / ".punch").mkdir()
    assert punch_dir() == fresh_repo / ".punch"
