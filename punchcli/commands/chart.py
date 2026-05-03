from __future__ import annotations

import argparse
import sys

from punchcli import console
from punchcli.core import charts
from punchcli.core.charts import styles


def run(args: argparse.Namespace) -> int:
    if args.list_styles:
        for name in styles.names():
            marker = " (default)" if name == styles.DEFAULT_STYLE else ""
            console.info(f"  {name}{marker}")
        return 0

    if args.list:
        enabled = set(charts.enabled_names())
        for name, desc in charts.describe():
            mark = "*" if name in enabled else " "
            console.info(f"  {mark} {name:<14} {desc}")
        console.info()
        console.info("  * = enabled in config.toml (regenerated on `punch out`)")
        return 0

    if args.all:
        paths = charts.write_all()
        for p in paths:
            console.info(str(p))
        return 0

    if not args.name:
        console.error("✗ Specify a chart name, --all, or --list.")
        console.error(f"  Available: {', '.join(charts.names())}")
        return 1

    if args.name not in charts.REGISTRY:
        console.error(f"✗ Unknown chart: {args.name}")
        console.error(f"  Available: {', '.join(charts.names())}")
        return 1

    if args.stdout:
        sys.stdout.write(charts.render(args.name))
        return 0

    path = charts.write(args.name)
    console.info(str(path))
    return 0
