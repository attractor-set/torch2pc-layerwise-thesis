#!/usr/bin/env python3
"""Generate descriptive paired analysis from sealed Stage 3B matched evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from torch2pc_thesis.stage3b_matched_analysis import generate_matched_analysis


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--generated-at-utc")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = generate_matched_analysis(
        args.evidence_root,
        args.output_root,
        generated_at_utc=args.generated_at_utc,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
