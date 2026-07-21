#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from torch2pc_thesis.stage3b_matched_release import (
    MATCHED_RELEASE_TAG,
    package_matched_release,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a draft-only Stage 3B matched-profiling release package."
    )
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--tag", default=MATCHED_RELEASE_TAG)
    parser.add_argument("--mode", choices=("repository", "full"), default="repository")
    parser.add_argument("--release-commit")
    parser.add_argument("--release-source-record", type=Path)
    args = parser.parse_args()

    result = package_matched_release(
        args.project_root,
        args.output_root,
        tag=args.tag,
        mode=args.mode,
        release_commit=args.release_commit,
        release_source_record=args.release_source_record,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
