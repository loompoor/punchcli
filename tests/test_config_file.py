from __future__ import annotations

from pathlib import Path

from punchcli.core import config_file


def test_load_returns_defaults_when_missing(punch_dir: Path) -> None:
    # no config.toml written
    cfg = config_file.load()
    assert cfg["charts"]["style"] == "github"
    assert "heatmap" in cfg["charts"]["enabled"]


def test_load_merges_user_overrides(punch_dir: Path) -> None:
    (punch_dir / "config.toml").write_text(
        '[charts]\nstyle = "dark"\n', encoding="utf-8"
    )
    config_file.reset_cache()
    cfg = config_file.load()
    assert cfg["charts"]["style"] == "dark"
    # default key not overridden remains present
    assert "enabled" in cfg["charts"]


def test_load_is_cached(punch_dir: Path) -> None:
    (punch_dir / "config.toml").write_text(
        '[charts]\nstyle = "dark"\n', encoding="utf-8"
    )
    config_file.reset_cache()
    first = config_file.load()
    # mutate file; cached result should not change until reset
    (punch_dir / "config.toml").write_text(
        '[charts]\nstyle = "github"\n', encoding="utf-8"
    )
    second = config_file.load()
    assert first is second
    assert second["charts"]["style"] == "dark"


def test_reset_cache_picks_up_changes(punch_dir: Path) -> None:
    (punch_dir / "config.toml").write_text(
        '[charts]\nstyle = "dark"\n', encoding="utf-8"
    )
    config_file.reset_cache()
    config_file.load()
    (punch_dir / "config.toml").write_text(
        '[charts]\nstyle = "github"\n', encoding="utf-8"
    )
    config_file.reset_cache()
    assert config_file.load()["charts"]["style"] == "github"


def test_malformed_toml_falls_back_to_defaults(
    punch_dir: Path, capsys
) -> None:
    (punch_dir / "config.toml").write_text(
        "this is = not valid = toml [[[\n", encoding="utf-8"
    )
    config_file.reset_cache()
    cfg = config_file.load()
    assert cfg["charts"]["style"] == "github"
    err = capsys.readouterr().err
    assert "parse error" in err


def test_write_default_does_not_overwrite(punch_dir: Path) -> None:
    target = punch_dir / "config.toml"
    target.write_text("custom", encoding="utf-8")
    config_file.write_default(target)
    assert target.read_text(encoding="utf-8") == "custom"


def test_write_default_creates_when_missing(punch_dir: Path) -> None:
    target = punch_dir / "config.toml"
    config_file.write_default(target)
    assert target.is_file()
    assert "[charts]" in target.read_text(encoding="utf-8")
