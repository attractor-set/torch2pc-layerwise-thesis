#!/usr/bin/env python3
"""Plan, verify or execute the authorized 288-cell matched Stage 3B lane."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import cast

from torch2pc_thesis.stage3b_execution import (
    STAGE3B_MANIFEST_RELATIVE_PATH,
    atomic_write_json,
    load_manifest,
    validated_plan_output_path,
)
from torch2pc_thesis.stage3b_matched_execution import (
    MATCHED_EXECUTION_DEFAULT_MAX_ATTEMPTS,
    execute_matched_authorized_lane,
    plan_matched_authorized_lane,
    verify_matched_authorized_lane,
)

DEFAULT_MATCHED_MANIFEST = Path("experiments/frozen/stage3b-matched-profiling-v2/manifest.json")
DEFAULT_OPENING_REQUEST = Path("experiments/frozen/stage3b-matched-profiling-v2/request.json")


def _load_json_object(path: Path) -> dict[str, object]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return cast(dict[str, object], raw)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--verify-authorization-only", action="store_true")
    mode.add_argument("--execute-authorized-lane", action="store_true")
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument(
        "--matched-manifest",
        type=Path,
        default=DEFAULT_MATCHED_MANIFEST,
    )
    parser.add_argument(
        "--opening-request",
        type=Path,
        default=DEFAULT_OPENING_REQUEST,
    )
    parser.add_argument(
        "--base-manifest",
        type=Path,
        default=STAGE3B_MANIFEST_RELATIVE_PATH,
    )
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("/tmp/torch2pc-stage3b-matched-rocm-authorized-v1"),
    )
    parser.add_argument("--plan-output", type=Path)
    parser.add_argument("--device", required=True, choices=("rocm",))
    parser.add_argument("--dtype", required=True, choices=("float32",))
    parser.add_argument("--torch2pc-dir", type=Path, default=Path("external/Torch2PC"))
    parser.add_argument(
        "--source-commit",
        default=os.environ.get("TORCH2PC_SOURCE_COMMIT", ""),
    )
    parser.add_argument(
        "--image-digest",
        default=os.environ.get("EXPERIMENT_IMAGE_DIGEST", ""),
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=MATCHED_EXECUTION_DEFAULT_MAX_ATTEMPTS,
    )
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--retry-failed", action="store_true")
    args = parser.parse_args()
    if not args.source_commit:
        parser.error("--source-commit or TORCH2PC_SOURCE_COMMIT is required")
    if not args.image_digest:
        parser.error("--image-digest or EXPERIMENT_IMAGE_DIGEST is required")
    if args.plan_output is not None and not args.dry_run:
        parser.error("--plan-output is available only with --dry-run")
    if args.verify_authorization_only and (args.resume or args.retry_failed):
        parser.error("verification-only mode does not accept resume flags")
    return args


def main() -> None:
    args = parse_args()
    authorization = _load_json_object(args.authorization)
    matched_manifest = _load_json_object(args.matched_manifest)
    opening_request = _load_json_object(args.opening_request)
    base_manifest = load_manifest(args.base_manifest)
    common = {
        "base_manifest_path": args.base_manifest,
        "project_root": args.project_root,
        "torch2pc_dir": args.torch2pc_dir,
        "output_root": args.output_root,
        "source_commit": args.source_commit,
        "device": args.device,
        "dtype": args.dtype,
        "image_digest": args.image_digest,
    }
    if args.verify_authorization_only:
        payload = verify_matched_authorized_lane(
            authorization,
            matched_manifest,
            opening_request,
            base_manifest,
            **common,
        )
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    if args.dry_run:
        plan = plan_matched_authorized_lane(
            authorization,
            matched_manifest,
            opening_request,
            base_manifest,
            max_attempts=args.max_attempts,
            resume=args.resume,
            retry_failed=args.retry_failed,
            **common,
        )
        payload = plan.to_record()
        if args.plan_output is not None:
            output = validated_plan_output_path(
                args.plan_output,
                output_root=args.output_root,
            )
            atomic_write_json(output, payload)
            payload = {**payload, "plan_output": str(output)}
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    payload = execute_matched_authorized_lane(
        authorization,
        matched_manifest,
        opening_request,
        base_manifest,
        max_attempts=args.max_attempts,
        resume=args.resume,
        retry_failed=args.retry_failed,
        **common,
    )
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
