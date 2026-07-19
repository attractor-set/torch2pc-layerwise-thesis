#!/usr/bin/env python3
"""Validate and seal the authorized Stage 3B B0/B1/B2 matched runtime."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from torch2pc_thesis.stage3b_matched_profiling import load_json_object
from torch2pc_thesis.stage3b_matched_sealing import (
    seal_matched_runtime,
    validate_matched_runtime,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--matched-manifest", type=Path, required=True)
    parser.add_argument("--expected-source-commit", required=True)
    parser.add_argument("--expected-image-digest", required=True)
    parser.add_argument("--expected-authorization-token", required=True)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--sealing-source-commit")
    parser.add_argument("--sealed-at-utc")
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
    manifest = load_json_object(args.matched_manifest)
    common = {
        "expected_source_commit": args.expected_source_commit,
        "expected_image_digest": args.expected_image_digest,
        "expected_authorization_token": args.expected_authorization_token,
    }
    if args.validate_only:
        validated = validate_matched_runtime(args.runtime_root, manifest, **common)
        print(
            json.dumps(
                {
                    "status": "valid",
                    "cell_count": len(validated.cells),
                    "runtime_inventory_sha256": validated.runtime_inventory_sha256,
                    "evidence": False,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return
    seal = seal_matched_runtime(
        args.runtime_root,
        args.output_root,
        manifest,
        sealing_source_commit=args.sealing_source_commit,
        sealed_at_utc=args.sealed_at_utc,
        **common,
    )
    print(json.dumps(seal, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
