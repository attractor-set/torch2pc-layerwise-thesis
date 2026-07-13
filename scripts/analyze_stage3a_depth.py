#!/usr/bin/env python3
"""Generate Stage 3A confirmatory depth-trend tables."""

from __future__ import annotations

import argparse
from pathlib import Path

from torch2pc_thesis.stage3_depth_analysis import generate_stage3a_depth_tables

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STATISTICS_DIR = REPO_ROOT / "results/stage3/layerwise/confirmatory/statistics"
DEFAULT_OUTPUT_DIR = DEFAULT_STATISTICS_DIR


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--statistics-dir", type=Path, default=DEFAULT_STATISTICS_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--source-commit")
    parser.add_argument("--generated-at-utc")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    counts = generate_stage3a_depth_tables(
        args.statistics_dir,
        args.output_dir,
        repo_root=args.repo_root,
        source_commit=args.source_commit,
        generated_at_utc=args.generated_at_utc,
    )
    for filename, rows in counts.items():
        print(f"{filename}: rows={rows}")
    print("Exact depth control: PASS")


if __name__ == "__main__":
    main()
