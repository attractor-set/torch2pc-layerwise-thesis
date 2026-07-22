#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from torch2pc_thesis.stage3b_matched_publication import (
    PUBLICATION_ACTION_TAG,
    package_publication_assets,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the Stage 3B matched-analysis publication gate and "
            "build publication assets without mutating sealed evidence."
        )
    )
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--publication-tag", default=PUBLICATION_ACTION_TAG)
    parser.add_argument("--publication-commit", required=True)
    args = parser.parse_args()

    result = package_publication_assets(
        args.project_root,
        args.output_root,
        publication_tag=args.publication_tag,
        publication_commit=args.publication_commit,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
