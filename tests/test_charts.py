from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Callable

import pytest

from punchcli.core import charts
from punchcli.core.charts.stats import _streaks


def _seed(cli: Callable[..., tuple[int, str]]) -> None:
    cli("init")
    cli("add", "--from", "yesterday 09:00", "--to", "yesterday 10:30",
        "-m", "work", "-t", "backend")
    cli("add", "--from", "yesterday 14:00", "--to", "yesterday 15:00",
        "-t", "meetings")


@pytest.mark.parametrize("name", list(charts.REGISTRY.keys()))
def test_chart_renders_clean(
    cli: Callable[..., tuple[int, str]], punch_dir: Path, name: str
) -> None:
    _seed(cli)
    rc, _ = cli("chart", name)
    assert rc == 0
    svg = (punch_dir / "charts" / f"{name}.svg").read_text(encoding="utf-8")
    assert svg.startswith("<?xml")
    assert "<svg" in svg
    assert "<script" not in svg
    assert "kozea.github.io" not in svg


@pytest.mark.parametrize("name", list(charts.REGISTRY.keys()))
def test_chart_empty_state(
    cli: Callable[..., tuple[int, str]], punch_dir: Path, name: str
) -> None:
    cli("init")
    rc, _ = cli("chart", name)
    assert rc == 0
    assert (punch_dir / "charts" / f"{name}.svg").is_file()


def test_chart_list(cli: Callable[..., tuple[int, str]]) -> None:
    cli("init")
    rc, out = cli("chart", "--list")
    assert rc == 0
    for name in charts.names():
        assert name in out


def test_chart_all_writes_every_svg(
    cli: Callable[..., tuple[int, str]], punch_dir: Path
) -> None:
    _seed(cli)
    rc, _ = cli("chart", "--all")
    assert rc == 0
    for name in charts.names():
        assert (punch_dir / "charts" / f"{name}.svg").is_file()


def test_chart_unknown_rejected(cli: Callable[..., tuple[int, str]]) -> None:
    cli("init")
    rc, out = cli("chart", "nonexistent")
    assert rc != 0
    assert "invalid choice" in out.lower()


def test_chart_stdout(cli: Callable[..., tuple[int, str]]) -> None:
    _seed(cli)
    rc, out = cli("chart", "heatmap", "--stdout")
    assert rc == 0
    assert "<svg" in out


def test_chart_no_arg(cli: Callable[..., tuple[int, str]]) -> None:
    cli("init")
    rc, out = cli("chart")
    assert rc != 0
    assert "Specify a chart name" in out


def test_streaks_empty() -> None:
    assert _streaks({}, date(2026, 5, 2)) == (0, 0)


def test_streaks_single_day() -> None:
    today = date(2026, 5, 2)
    assert _streaks({today: 3600}, today) == (1, 1)


def test_streaks_current_and_longest() -> None:
    today = date(2026, 5, 2)
    daily = {
        today - timedelta(days=10): 1,
        today - timedelta(days=9): 1,
        today - timedelta(days=8): 1,  # 3-day run
        today - timedelta(days=2): 1,
        today - timedelta(days=1): 1,
        today: 1,  # current 3-day run
    }
    cur, longest = _streaks(daily, today)
    assert cur == 3
    assert longest == 3


def test_streaks_no_current_when_today_missing() -> None:
    today = date(2026, 5, 2)
    daily = {today - timedelta(days=2): 1, today - timedelta(days=1): 1}
    cur, longest = _streaks(daily, today)
    assert cur == 0
    assert longest == 2


def test_config_enabled_filter(
    cli: Callable[..., tuple[int, str]], punch_dir: Path
) -> None:
    cli("init")
    (punch_dir / "config.toml").write_text(
        '[charts]\nenabled = ["heatmap"]\nstyle = "github"\n', encoding="utf-8"
    )
    from punchcli.core import config_file
    config_file.reset_cache()
    assert charts.enabled_names() == ["heatmap"]


def test_config_unknown_chart_warns(
    cli: Callable[..., tuple[int, str]], punch_dir: Path
) -> None:
    cli("init")
    (punch_dir / "config.toml").write_text(
        '[charts]\nenabled = ["heatmap", "bogus"]\n', encoding="utf-8"
    )
    from punchcli.core import config_file
    config_file.reset_cache()
    names = charts.enabled_names()
    assert "heatmap" in names
    assert "bogus" not in names


def test_chart_list_styles(cli: Callable[..., tuple[int, str]]) -> None:
    cli("init")
    rc, out = cli("chart", "--list-styles")
    assert rc == 0
    assert "github" in out
    assert "dark" in out


def test_unknown_style_falls_back(
    cli: Callable[..., tuple[int, str]], punch_dir: Path
) -> None:
    cli("init")
    (punch_dir / "config.toml").write_text(
        '[charts]\nstyle = "doesnotexist"\n', encoding="utf-8"
    )
    from punchcli.core import config_file
    config_file.reset_cache()
    rc, _ = cli("chart", "weekly")
    assert rc == 0


def test_report_write_creates_enabled_charts(
    cli: Callable[..., tuple[int, str]], punch_dir: Path
) -> None:
    _seed(cli)
    cli("report", "--write")
    enabled = charts.enabled_names()
    assert enabled, "default config should enable at least one chart"
    for name in enabled:
        assert (punch_dir / "charts" / f"{name}.svg").is_file()
    disabled = set(charts.names()) - set(enabled)
    for name in disabled:
        assert not (punch_dir / "charts" / f"{name}.svg").is_file()
