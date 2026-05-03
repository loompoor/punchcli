from __future__ import annotations

import argparse
import sys

import argcomplete


def run(args: argparse.Namespace) -> int:
    sys.stdout.write(argcomplete.shellcode(["punch"], shell=args.shell))
    return 0
