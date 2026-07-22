#!/usr/bin/env python3
"""Execute Stage 3B matched analysis only from the frozen authorization package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from torch2pc_thesis.stage3b_matched_analysis_runtime import (
    execute_authorized_matched_analysis,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--project-root", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = execute_authorized_matched_analysis(
        args.project_root,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
