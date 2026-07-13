#!/usr/bin/env python3

"""Generate Stage 3A publication-quality layer-wise figures."""

from __future__ import annotations

import argparse
from pathlib import Path

from torch2pc_thesis.stage3_figures import generate_stage3a_figures

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIRMATORY_DIR = REPO_ROOT / "results/stage3/layerwise/confirmatory"
DEFAULT_STATISTICS_DIR = DEFAULT_CONFIRMATORY_DIR / "statistics"
DEFAULT_SUMMARIES_DIR = DEFAULT_CONFIRMATORY_DIR / "summaries"
DEFAULT_OUTPUT_DIR = DEFAULT_CONFIRMATORY_DIR / "figures"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--statistics-dir", type=Path, default=DEFAULT_STATISTICS_DIR)
    parser.add_argument("--summaries-dir", type=Path, default=DEFAULT_SUMMARIES_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--source-commit")
    parser.add_argument("--generated-at-utc")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    counts = generate_stage3a_figures(
        args.statistics_dir,
        args.summaries_dir,
        args.output_dir,
        repo_root=args.repo_root,
        source_commit=args.source_commit,
        generated_at_utc=args.generated_at_utc,
    )
    for filename, count in counts.items():
        print(f"{filename}: files={count}")
    print("Stage 3A publication figures: PASS")


if __name__ == "__main__":
    main()
