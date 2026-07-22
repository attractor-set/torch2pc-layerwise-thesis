#!/usr/bin/env python3
"""Capture a non-computational Stage 3B matched-analysis runtime preflight."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from torch2pc_thesis.stage3b_matched_analysis_runtime import (
    build_runtime_preflight,
    write_runtime_preflight,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--captured-at-utc", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    preflight = build_runtime_preflight(
        args.project_root,
        source_commit=args.source_commit,
        captured_at_utc=args.captured_at_utc,
    )
    write_runtime_preflight(preflight, args.output)
    print(
        json.dumps(
            {
                "status": preflight["status"],
                "preflight_id": preflight["preflight_id"],
                "preflight_digest": preflight["preflight_digest"],
                "execution_authorization_present": False,
                "analysis_execution_permitted": False,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
