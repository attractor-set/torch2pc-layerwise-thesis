#!/usr/bin/env python3
"""Freeze and verify matched Stage 3B B0/B1/B2 runtime authorization."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Mapping
from pathlib import Path

from torch2pc_thesis.stage3b_execution import (
    STAGE3B_MANIFEST_RELATIVE_PATH,
    atomic_write_json,
    load_manifest,
    validated_plan_output_path,
)
from torch2pc_thesis.stage3b_matched_authorization import (
    MATCHED_DEFAULT_MINIMUM_FREE_BYTES,
    MATCHED_OPERATOR_ACKNOWLEDGEMENT,
    capture_matched_lane_preflight,
    freeze_matched_project_environment,
    issue_matched_campaign_authorization,
    validate_matched_campaign_authorization,
    verify_matched_authorization_for_lane,
)
from torch2pc_thesis.stage3b_matched_profiling import load_json_object

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MATCHED_MANIFEST = (
    PROJECT_ROOT
    / "experiments/planned/STAGE3B-B1-B2-MATCHED-PROFILING-MANIFEST.json"
)
DEFAULT_MATCHED_REQUEST = (
    PROJECT_ROOT
    / "experiments/planned/STAGE3B-B1-B2-MATCHED-PROFILING-REQUEST.json"
)
DEFAULT_OUTPUT_ROOT = Path(
    "/tmp/torch2pc-stage3b-b1-b2-matched-rocm-authorization-v1"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--freeze-project", action="store_true")
    mode.add_argument("--preflight-lane", action="store_true")
    mode.add_argument("--issue-authorization", action="store_true")
    mode.add_argument("--verify-authorization", action="store_true")

    parser.add_argument("--matched-manifest", type=Path, default=DEFAULT_MATCHED_MANIFEST)
    parser.add_argument("--matched-request", type=Path, default=DEFAULT_MATCHED_REQUEST)
    parser.add_argument("--base-manifest", type=Path, default=STAGE3B_MANIFEST_RELATIVE_PATH)
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--torch2pc-dir", type=Path, default=Path("external/Torch2PC"))
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--freeze-record", type=Path)
    parser.add_argument("--lane-preflight", type=Path)
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--image-digest")
    parser.add_argument(
        "--source-commit",
        default=os.environ.get("TORCH2PC_SOURCE_COMMIT", ""),
    )
    parser.add_argument(
        "--minimum-free-bytes",
        type=int,
        default=MATCHED_DEFAULT_MINIMUM_FREE_BYTES,
    )
    parser.add_argument("--operator-acknowledgement")
    args = parser.parse_args()

    if args.freeze_project:
        if args.output is None:
            parser.error("--freeze-project requires --output")
        if not args.source_commit:
            parser.error("--freeze-project requires --source-commit")
    elif args.preflight_lane:
        if args.freeze_record is None or args.output is None:
            parser.error("--preflight-lane requires --freeze-record and --output")
        if not args.source_commit:
            parser.error("--preflight-lane requires --source-commit")
        if args.image_digest is None:
            parser.error("--preflight-lane requires --image-digest")
    elif args.issue_authorization:
        if args.freeze_record is None or args.lane_preflight is None:
            parser.error(
                "--issue-authorization requires --freeze-record and --lane-preflight"
            )
        if args.output is None:
            parser.error("--issue-authorization requires --output")
        if args.operator_acknowledgement != MATCHED_OPERATOR_ACKNOWLEDGEMENT:
            parser.error(
                "--operator-acknowledgement must exactly match the documented phrase"
            )
    else:
        if args.authorization is None:
            parser.error("--verify-authorization requires --authorization")
        if not args.source_commit:
            parser.error("--verify-authorization requires --source-commit")
        if args.image_digest is None:
            parser.error("--verify-authorization requires --image-digest")
    return args


def _summary(payload: Mapping[str, object], keys: tuple[str, ...]) -> dict[str, object]:
    return {key: payload[key] for key in keys}


def main() -> int:
    args = parse_args()
    matched_manifest = load_json_object(args.matched_manifest)
    request = load_json_object(args.matched_request)
    base_manifest = load_manifest(args.base_manifest)

    if args.freeze_project:
        payload = freeze_matched_project_environment(
            matched_manifest,
            request,
            base_manifest,
            base_manifest_path=args.base_manifest,
            project_root=args.project_root,
            torch2pc_dir=args.torch2pc_dir,
            output_root=args.output_root,
            source_commit=args.source_commit,
            minimum_free_bytes=args.minimum_free_bytes,
        )
        output_path = validated_plan_output_path(
            args.output,
            output_root=args.output_root,
        )
        atomic_write_json(output_path, payload)
        print(
            json.dumps(
                _summary(
                    payload,
                    (
                        "campaign_id",
                        "freeze_scope",
                        "freeze_digest",
                        "project_source_commit",
                        "matched_manifest_digest",
                        "opening_request_digest",
                        "source_manifest_digest",
                        "torch2pc_commit",
                        "authorized_cell_count",
                        "candidate_dispatch_contract_digest",
                        "output_root",
                        "evidence",
                        "full_stage3b_campaign_complete",
                    ),
                ),
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    if args.preflight_lane:
        freeze_record = load_json_object(args.freeze_record)
        payload = capture_matched_lane_preflight(
            freeze_record,
            matched_manifest,
            request,
            base_manifest,
            base_manifest_path=args.base_manifest,
            project_root=args.project_root,
            torch2pc_dir=args.torch2pc_dir,
            source_commit=args.source_commit,
            image_digest=args.image_digest,
        )
        output_path = validated_plan_output_path(
            args.output,
            output_root=Path(str(freeze_record["output_root"])),
        )
        atomic_write_json(output_path, payload)
        print(
            json.dumps(
                _summary(
                    payload,
                    (
                        "campaign_id",
                        "preflight_scope",
                        "freeze_digest",
                        "lane_preflight_digest",
                        "device",
                        "dtype",
                        "image_digest",
                        "runtime",
                        "dispatch_verified_symbols",
                        "output_root",
                        "evidence",
                    ),
                ),
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    if args.issue_authorization:
        freeze_record = load_json_object(args.freeze_record)
        lane_preflight = load_json_object(args.lane_preflight)
        payload = issue_matched_campaign_authorization(
            freeze_record,
            lane_preflight,
            operator_acknowledgement=args.operator_acknowledgement,
        )
        output_path = validated_plan_output_path(
            args.output,
            output_root=Path(str(freeze_record["output_root"])),
        )
        atomic_write_json(output_path, payload)
        print(
            json.dumps(
                _summary(
                    payload,
                    (
                        "campaign_id",
                        "authorization_scope",
                        "authorization_token",
                        "project_source_commit",
                        "matched_manifest_digest",
                        "opening_request_digest",
                        "authorized_cell_count",
                        "canonical_execution_count",
                        "canonical_lanes",
                        "output_root",
                        "runtime_authorization",
                        "measurements_allowed",
                        "execution_permitted",
                        "evidence",
                        "results_publication_permitted",
                        "test_dataset_access",
                    ),
                ),
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    authorization = load_json_object(args.authorization)
    validate_matched_campaign_authorization(authorization)
    payload = verify_matched_authorization_for_lane(
        authorization,
        matched_manifest,
        request,
        base_manifest,
        base_manifest_path=args.base_manifest,
        project_root=args.project_root,
        torch2pc_dir=args.torch2pc_dir,
        output_root=args.output_root,
        source_commit=args.source_commit,
        image_digest=args.image_digest,
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
