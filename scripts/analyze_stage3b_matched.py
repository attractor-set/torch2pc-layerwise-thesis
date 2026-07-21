#!/usr/bin/env python3
"""Validate the registered Stage 3B analysis engine on a synthetic fixture only."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from torch2pc_thesis.stage3b_matched_analysis import (
    generate_synthetic_matched_analysis,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--synthetic-fixture-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--generated-at-utc", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = generate_synthetic_matched_analysis(
        args.synthetic_fixture_root,
        args.output_root,
        generated_at_utc=args.generated_at_utc,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
