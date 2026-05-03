from __future__ import annotations

from pathlib import Path
from typing import Callable


def test_init_creates_dir_and_db(
    cli_bare: Callable[..., tuple[int, str]], fresh_repo: Path
) -> None:
    rc, out = cli_bare("init")
    assert rc == 0
    assert "Initialized" in out
    assert (fresh_repo / ".punch").is_dir()
    assert (fresh_repo / ".punch" / "punch.db").is_file()


def test_init_idempotent(
    cli_bare: Callable[..., tuple[int, str]], fresh_repo: Path
) -> None:
    cli_bare("init")
    rc, out = cli_bare("init")
    assert rc == 0
    assert "already exists" in out


def test_init_writes_gitignore(
    cli_bare: Callable[..., tuple[int, str]], fresh_repo: Path
) -> None:
    cli_bare("init")
    gi = fresh_repo / ".punch" / ".gitignore"
    assert gi.is_file()
    assert "state.json" in gi.read_text(encoding="utf-8")


def test_init_writes_default_config(
    cli_bare: Callable[..., tuple[int, str]], fresh_repo: Path
) -> None:
    cli_bare("init")
    cfg = fresh_repo / ".punch" / "config.toml"
    assert cfg.is_file()
    text = cfg.read_text(encoding="utf-8")
    assert "[charts]" in text
    assert "style" in text


def test_init_backfills_gitignore_on_existing_dir(
    cli_bare: Callable[..., tuple[int, str]], fresh_repo: Path
) -> None:
    (fresh_repo / ".punch").mkdir()
    cli_bare("init")
    gi = fresh_repo / ".punch" / ".gitignore"
    assert gi.is_file()
    assert "state.json" in gi.read_text(encoding="utf-8")


def test_init_preserves_existing_gitignore(
    cli_bare: Callable[..., tuple[int, str]], fresh_repo: Path
) -> None:
    cli_bare("init")
    gi = fresh_repo / ".punch" / ".gitignore"
    gi.write_text("custom\n", encoding="utf-8")
    cli_bare("init")
    assert gi.read_text(encoding="utf-8") == "custom\n"


def test_other_command_fails_without_init(
    cli_bare: Callable[..., tuple[int, str]], fresh_repo: Path
) -> None:
    rc, out = cli_bare("status")
    assert rc == 1
    assert "No .punch/" in out
    assert "punch init" in out


def test_in_works_after_init(
    cli_bare: Callable[..., tuple[int, str]], fresh_repo: Path
) -> None:
    cli_bare("init")
    rc, out = cli_bare("in", "-m", "post-init")
    assert rc == 0
    assert "Started tracking" in out
    rc, _ = cli_bare("out")
    assert rc == 0


def test_init_discovered_from_subdir(
    cli_bare: Callable[..., tuple[int, str]],
    fresh_repo: Path,
    monkeypatch,
) -> None:
    cli_bare("init")
    sub = fresh_repo / "src" / "deep"
    sub.mkdir(parents=True)
    monkeypatch.chdir(sub)
    rc, out = cli_bare("status")
    assert rc == 0
    assert "No active session" in out
