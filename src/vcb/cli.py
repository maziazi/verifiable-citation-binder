from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from vcb.surface.report_figures import generate_report_figures


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="vcb")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("demo", "verify", "attack", "eval"):
        subparsers.add_parser(command, help=f"{command} command (coming soon)")
    figures = subparsers.add_parser("figures", help="generate report figures")
    figures.add_argument("--ledger", type=Path, required=True)
    figures.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "figures":
        for path in generate_report_figures(args.ledger, args.output_dir):
            print(path)
    else:
        parser.error(f"vcb {args.command} is not implemented yet")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
