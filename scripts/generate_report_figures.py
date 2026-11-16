from __future__ import annotations

import argparse
from pathlib import Path

from vcb.surface.report_figures import generate_report_figures


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate VCB report figures")
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    paths = generate_report_figures(args.ledger, args.output_dir)
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
