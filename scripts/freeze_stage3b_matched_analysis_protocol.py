#!/usr/bin/env python3
"""Build or verify the Stage 3B matched descriptive-analysis protocol freeze."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from torch2pc_thesis.stage3b_matched_analysis_protocol import (
    PROTOCOL_ROOT_RELATIVE,
    write_protocol_package,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = args.project_root.expanduser().resolve()
    output_root = (
        args.output_root.expanduser().resolve()
        if args.output_root is not None
        else project_root / PROTOCOL_ROOT_RELATIVE
    )
    protocol = write_protocol_package(
        project_root,
        output_root,
        check=args.check,
    )
    print(json.dumps(protocol, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
