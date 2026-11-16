from __future__ import annotations

import argparse
from pathlib import Path

from vcb.surface.report_figures import generate_report_figures


def main() -> int:
    parser = argparse.ArgumentParser(prog="vcb")
    subparsers = parser.add_subparsers(dest="command", required=True)
    figures = subparsers.add_parser("figures", help="generate report figures")
    figures.add_argument("--ledger", type=Path, required=True)
    figures.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "figures":
        for path in generate_report_figures(args.ledger, args.output_dir):
            print(path)
    return 0
