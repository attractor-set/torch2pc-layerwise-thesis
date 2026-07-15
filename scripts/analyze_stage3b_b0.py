#!/usr/bin/env python3
"""Generate Stage 3B B0 statistical and engineering analysis artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

from torch2pc_thesis.stage3b_b0_analysis import generate_stage3b_b0_analysis

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE_ROOT = REPO_ROOT / "results/stage-3/profiling/b0/sealed-v1"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "results/stage-3/profiling/b0/analysis-v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-root", type=Path, default=DEFAULT_EVIDENCE_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--source-commit")
    parser.add_argument("--generated-at-utc")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    counts = generate_stage3b_b0_analysis(
        args.evidence_root,
        args.output_root,
        repo_root=args.repo_root,
        source_commit=args.source_commit,
        generated_at_utc=args.generated_at_utc,
    )
    for filename, count in sorted(counts.items()):
        print(f"{filename}: rows_or_files={count}")
    print("Stage 3B B0 statistical and engineering analysis: PASS")


if __name__ == "__main__":
    main()
