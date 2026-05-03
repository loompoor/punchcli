# PYTHON_ARGCOMPLETE_OK
from __future__ import annotations

import argparse
import sys
from importlib.metadata import PackageNotFoundError, version

import argcomplete

from punchcli.commands import (
    add,
    chart,
    completions,
    edit,
    export,
    import_,
    in_,
    init,
    log,
    out,
    report,
    skill,
    status,
    tags,
)
from punchcli.core import charts
from punchcli import console
from punchcli.config import PunchDirNotFound


def _version() -> str:
    try:
        return version("punchcli")
    except PackageNotFoundError:
        return "0.0.0+unknown"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="punch",
        description="Minimal CLI time tracker.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"punchcli {_version()}",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Create .punch/ in current directory")
    p_init.set_defaults(func=init.run)

    p_in = sub.add_parser("in", help="Start tracking time")
    p_in.add_argument("-m", "--message", help="Optional free-text message")
    p_in.add_argument("-t", "--tags", help="Comma-separated tags")
    p_in.set_defaults(func=in_.run)

    p_out = sub.add_parser("out", help="Stop tracking and log session")
    p_out.set_defaults(func=out.run)

    p_status = sub.add_parser("status", help="Show active session info")
    p_status.set_defaults(func=status.run)

    p_report = sub.add_parser("report", help="Summary of logged time")
    p_report.add_argument("--today", action="store_true")
    p_report.add_argument("--week", action="store_true")
    p_report.add_argument("--month", action="store_true")
    p_report.add_argument("--from", dest="from_", metavar="YYYY-MM-DD")
    p_report.add_argument("--to", dest="to", metavar="YYYY-MM-DD")
    p_report.add_argument("--tag", help="Filter by tag")
    p_report.add_argument("--write", action="store_true", help="Regenerate REPORT.md")
    p_report.set_defaults(func=report.run)

    p_log = sub.add_parser("log", help="Recent sessions table")
    p_log.add_argument("--today", action="store_true")
    p_log.add_argument("--week", action="store_true")
    p_log.add_argument("--month", action="store_true")
    p_log.add_argument("--tag")
    p_log.add_argument("-n", type=int, default=20)
    p_log.set_defaults(func=log.run)

    p_tags = sub.add_parser("tags", help="List tags with totals")
    p_tags.set_defaults(func=tags.run)

    p_edit = sub.add_parser("edit", help="Edit an entry by id")
    p_edit.add_argument("entry_id", type=int, metavar="ID")
    p_edit.add_argument("--start", help="New start timestamp")
    p_edit.add_argument("--end", help="New end timestamp")
    p_edit.add_argument("-m", "--message", help='New message (use "" to clear)')
    p_edit.add_argument("-t", "--tags", help='New tags csv (use "" to clear)')
    p_edit.set_defaults(func=edit.run)

    p_export = sub.add_parser("export", help="Export sessions")
    fmt = p_export.add_mutually_exclusive_group(required=True)
    fmt.add_argument("--csv", action="store_true")
    fmt.add_argument("--md", action="store_true")
    p_export.add_argument("--from", dest="from_")
    p_export.add_argument("--to", dest="to")
    p_export.add_argument("--tag")
    p_export.set_defaults(func=export.run)

    p_add = sub.add_parser("add", help="Manually log a past session")
    p_add.add_argument("--from", dest="from_")
    p_add.add_argument("--to", dest="to")
    p_add.add_argument("--duration")
    p_add.add_argument("-m", "--message")
    p_add.add_argument("-t", "--tags")
    p_add.add_argument("--force", action="store_true")
    p_add.set_defaults(func=add.run)

    p_skill = sub.add_parser("skill", help="Print SKILL.md for agent runners")
    p_skill.set_defaults(func=skill.run)

    p_completions = sub.add_parser(
        "completions", help="Print shell completion script"
    )
    p_completions.add_argument(
        "shell", choices=["bash", "zsh", "fish"], help="Shell name"
    )
    p_completions.set_defaults(func=completions.run)

    p_import = sub.add_parser("import", help="Bulk-import sessions from CSV")
    p_import.add_argument("file", help="Path to CSV file")
    p_import.add_argument("--dry-run", action="store_true", dest="dry_run")
    p_import.add_argument("--force", action="store_true")
    p_import.set_defaults(func=import_.run)

    p_chart = sub.add_parser(
        "chart", help="Render a chart SVG (use --list to browse)"
    )
    p_chart.add_argument(
        "name", nargs="?", choices=charts.names(), help="Chart name"
    )
    p_chart.add_argument("--list", action="store_true", help="List available charts")
    p_chart.add_argument(
        "--list-styles", action="store_true", dest="list_styles",
        help="List available pygal styles",
    )
    p_chart.add_argument("--all", action="store_true", help="Render every chart")
    p_chart.add_argument(
        "--stdout", action="store_true", help="Write SVG to stdout instead of file"
    )
    p_chart.set_defaults(func=chart.run)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    argcomplete.autocomplete(parser)
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except PunchDirNotFound as e:
        console.error(f"✗ {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
