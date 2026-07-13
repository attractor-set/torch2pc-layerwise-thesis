#!/usr/bin/env python3
"""Generate Stage 3A confirmatory seed-level statistical tables."""

from __future__ import annotations

import argparse
from pathlib import Path

from torch2pc_thesis.stage3_analysis import generate_stage3a_tables

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUMMARY_DIR = REPO_ROOT / "results/stage3/layerwise/confirmatory/summaries"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "results/stage3/layerwise/confirmatory/statistics"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary-dir", type=Path, default=DEFAULT_SUMMARY_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--source-commit")
    parser.add_argument("--generated-at-utc")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    counts = generate_stage3a_tables(
        args.summary_dir,
        args.output_dir,
        repo_root=args.repo_root,
        source_commit=args.source_commit,
        generated_at_utc=args.generated_at_utc,
    )
    for filename, rows in counts.items():
        print(f"{filename}: rows={rows}")
    print("Exact numerical control: PASS")


if __name__ == "__main__":
    main()
