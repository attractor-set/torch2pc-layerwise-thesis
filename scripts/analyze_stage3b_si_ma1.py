#!/usr/bin/env python3
"""Validate and aggregate frozen Stage 3B SI-MA1 confirmatory evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from torch2pc_thesis.stage3b_si_ma1_aggregation import (
    DEFAULT_INPUT_ROOT,
    DEFAULT_OUTPUT_ROOT,
    aggregate_confirmatory,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate the frozen ten-seed SI-MA1 confirmatory cohort.",
    )
    parser.add_argument(
        "--input-root",
        type=Path,
        default=DEFAULT_INPUT_ROOT,
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo = Path(__file__).resolve().parents[1]
    summary = aggregate_confirmatory(
        repo=repo,
        input_root=args.input_root,
        output_root=args.output_root,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
