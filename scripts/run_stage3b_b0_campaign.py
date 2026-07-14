#!/usr/bin/env python3
"""Plan, verify or execute one authorized Stage 3B B0 canonical lane."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import cast

from torch2pc_thesis.stage3b_canonical import (
    B0_CANONICAL_DEFAULT_MAX_ATTEMPTS,
    execute_authorized_lane,
    plan_authorized_lane,
    verify_authorized_lane,
)
from torch2pc_thesis.stage3b_execution import (
    STAGE3B_MANIFEST_RELATIVE_PATH,
    atomic_write_json,
    load_manifest,
    validated_plan_output_path,
)


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
        "--manifest",
        type=Path,
        default=STAGE3B_MANIFEST_RELATIVE_PATH,
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("/tmp/torch2pc-stage3b-b0-rocm-authorized-v2"),
    )
    parser.add_argument("--plan-output", type=Path)
    parser.add_argument("--device", required=True, choices=("cpu", "rocm"))
    parser.add_argument("--dtype", required=True, choices=("float32", "float64"))
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
        default=B0_CANONICAL_DEFAULT_MAX_ATTEMPTS,
    )
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--retry-failed", action="store_true")
    args = parser.parse_args()
    if (args.device, args.dtype) != ("rocm", "float32"):
        parser.error(
            "canonical B0 runner is limited to --device rocm --dtype float32; "
            "use single-cell or bounded-batch smoke tooling for CPU controls"
        )
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
    manifest = load_manifest(args.manifest)
    if args.verify_authorization_only:
        payload = verify_authorized_lane(
            authorization,
            manifest,
            torch2pc_dir=args.torch2pc_dir,
            output_root=args.output_root,
            source_commit=args.source_commit,
            device=args.device,
            dtype=args.dtype,
            image_digest=args.image_digest,
        )
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    if args.dry_run:
        plan = plan_authorized_lane(
            authorization,
            manifest,
            output_root=args.output_root,
            device=args.device,
            dtype=args.dtype,
            torch2pc_dir=args.torch2pc_dir,
            source_commit=args.source_commit,
            image_digest=args.image_digest,
            max_attempts=args.max_attempts,
            resume=args.resume,
            retry_failed=args.retry_failed,
        )
        payload = plan.to_record()
        if args.plan_output is not None:
            output = validated_plan_output_path(
                args.plan_output,
                output_root=args.output_root,
            )
            atomic_write_json(output, payload)
        summary = {
            key: payload[key]
            for key in (
                "schema_version",
                "campaign_id",
                "authorization_scope",
                "execution_scope",
                "authorization_verified",
                "execution_permitted",
                "execution_performed",
                "evidence",
                "full_lane_complete",
                "full_campaign_complete",
                "results_publication_permitted",
                "test_dataset_access",
                "authorization_token",
                "manifest_digest",
                "source_commit",
                "device",
                "dtype",
                "image_digest",
                "canonical_protocol",
                "b0_cell_count",
                "summary",
                "selected_cell_ids",
            )
        }
        print(json.dumps(summary, indent=2, sort_keys=True))
        return
    payload = execute_authorized_lane(
        authorization,
        manifest,
        output_root=args.output_root,
        device=args.device,
        dtype=args.dtype,
        torch2pc_dir=args.torch2pc_dir,
        source_commit=args.source_commit,
        image_digest=args.image_digest,
        max_attempts=args.max_attempts,
        resume=args.resume,
        retry_failed=args.retry_failed,
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    if payload["status"] != "lane_complete":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
