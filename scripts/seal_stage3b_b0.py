#!/usr/bin/env python3
"""Validate and seal an immutable Stage 3B B0 ROCm canonical archive."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from torch2pc_thesis.stage3b_sealing import seal_b0_archive, validate_b0_archive


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--expected-source-commit", required=True)
    parser.add_argument("--expected-image-digest", required=True)
    parser.add_argument("--expected-archive-inventory-sha256", required=True)
    parser.add_argument("--sealing-source-commit")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only and args.output_root is not None:
        parser.error("--validate-only cannot be combined with --output-root")
    if not args.validate_only and args.output_root is None:
        parser.error("sealing requires --output-root")
    if not args.validate_only and args.sealing_source_commit is None:
        parser.error("sealing requires --sealing-source-commit")
    return args


def main() -> None:
    args = parse_args()
    common = {
        "expected_source_commit": args.expected_source_commit,
        "expected_image_digest": args.expected_image_digest,
        "expected_archive_inventory_sha256": (
            args.expected_archive_inventory_sha256
        ),
    }
    if args.validate_only:
        validated = validate_b0_archive(args.archive_root, **common)
        print(json.dumps(validated.validation_record, indent=2, sort_keys=True))
        return
    bundle = seal_b0_archive(
        args.archive_root,
        args.output_root,
        sealing_source_commit=args.sealing_source_commit,
        **common,
    )
    print(json.dumps(bundle.to_record(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
