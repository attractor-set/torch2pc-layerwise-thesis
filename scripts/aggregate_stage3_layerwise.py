#!/usr/bin/env python3
"""Aggregate Stage 3 layer-wise probe outputs with seed provenance."""

from __future__ import annotations

import argparse
from pathlib import Path

from torch2pc_thesis.stage3_aggregation import aggregate_tables


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    row_counts = aggregate_tables(args.root, args.output)
    for filename, rows in row_counts.items():
        print(f"{filename}: rows={rows}")


if __name__ == "__main__":
    main()
