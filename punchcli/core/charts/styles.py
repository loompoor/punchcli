from __future__ import annotations

from punchcli import console
from pygal.style import (
    CleanStyle,
    DarkColorizedStyle,
    DarkSolarizedStyle,
    DarkStyle,
    DefaultStyle,
    LightColorizedStyle,
    LightSolarizedStyle,
    LightStyle,
    NeonStyle,
    RedBlueStyle,
    SolidColorStyle,
    Style,
    TurquoiseStyle,
)

GitHubStyle = Style(
    background="transparent",
    plot_background="transparent",
    foreground="#cccccc",
    foreground_strong="#ffffff",
    foreground_subtle="#7d8590",
    opacity=".9",
    opacity_hover=".5",
    transition="200ms",
    colors=("#39d353", "#26a641", "#006d32", "#0e4429", "#3b82f6", "#8b5cf6"),
    font_family="system, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    label_font_size=11,
    major_label_font_size=12,
    title_font_size=14,
    legend_font_size=12,
)

PunchStyle = Style(
    background="transparent",
    plot_background="transparent",
    foreground="#1f2328",
    foreground_strong="#0d1117",
    foreground_subtle="#656d76",
    opacity=".9",
    opacity_hover=".5",
    transition="200ms",
    colors=("#0969da", "#1a7f37", "#bf8700", "#cf222e", "#8250df", "#bf3989"),
    font_family="system, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    label_font_size=11,
    major_label_font_size=12,
    title_font_size=14,
    legend_font_size=12,
)

STYLES: dict[str, Style] = {
    "github": GitHubStyle,
    "punch": PunchStyle,
    "default": DefaultStyle,
    "dark": DarkStyle,
    "neon": NeonStyle,
    "light": LightStyle,
    "clean": CleanStyle,
    "red_blue": RedBlueStyle,
    "dark_solarized": DarkSolarizedStyle,
    "light_solarized": LightSolarizedStyle,
    "dark_colorized": DarkColorizedStyle,
    "light_colorized": LightColorizedStyle,
    "solid_color": SolidColorStyle,
    "turquoise": TurquoiseStyle,
}

DEFAULT_STYLE = "github"


def names() -> list[str]:
    return list(STYLES.keys())


def get(name: str | None) -> Style:
    if name is None:
        return STYLES[DEFAULT_STYLE]
    style = STYLES.get(name)
    if style is None:
        console.warn(
            f"⚠ Unknown style '{name}', falling back to '{DEFAULT_STYLE}'. "
            f"Available: {', '.join(STYLES.keys())}"
        )
        return STYLES[DEFAULT_STYLE]
    return style
