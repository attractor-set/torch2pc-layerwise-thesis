#!/usr/bin/env python3
"""Freeze and verify Stage 3B B0 campaign authorization inputs."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import cast

from torch2pc_thesis.stage3b_authorization import (
    B0_DEFAULT_MINIMUM_FREE_BYTES,
    B0_OPERATOR_ACKNOWLEDGEMENT,
    capture_lane_preflight,
    freeze_project_environment,
    issue_campaign_authorization,
    validate_campaign_authorization,
    verify_authorization_for_lane,
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
    mode.add_argument("--freeze-project", action="store_true")
    mode.add_argument("--preflight-lane", action="store_true")
    mode.add_argument("--issue-authorization", action="store_true")
    mode.add_argument("--verify-authorization", action="store_true")

    parser.add_argument("--manifest", type=Path, default=STAGE3B_MANIFEST_RELATIVE_PATH)
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--torch2pc-dir", type=Path, default=Path("external/Torch2PC"))
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("/tmp/torch2pc-stage3b-b0-authorized"),
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--freeze-record", type=Path)
    parser.add_argument("--lane-preflight", type=Path, action="append", default=[])
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--device", choices=("cpu", "rocm"))
    parser.add_argument("--dtype", choices=("float32", "float64"))
    parser.add_argument("--image-digest")
    parser.add_argument(
        "--source-commit",
        default=os.environ.get("TORCH2PC_SOURCE_COMMIT", ""),
    )
    parser.add_argument(
        "--minimum-free-bytes",
        type=int,
        default=B0_DEFAULT_MINIMUM_FREE_BYTES,
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
        if args.device is None or args.dtype is None or args.image_digest is None:
            parser.error(
                "--preflight-lane requires --device, --dtype and --image-digest"
            )
    elif args.issue_authorization:
        if args.freeze_record is None or args.output is None:
            parser.error("--issue-authorization requires --freeze-record and --output")
        if len(args.lane_preflight) != 2:
            parser.error("--issue-authorization requires two --lane-preflight files")
        if args.operator_acknowledgement != B0_OPERATOR_ACKNOWLEDGEMENT:
            parser.error(
                "--operator-acknowledgement must exactly match the documented phrase"
            )
    else:
        if args.authorization is None:
            parser.error("--verify-authorization requires --authorization")
        if not args.source_commit:
            parser.error("--verify-authorization requires --source-commit")
        if args.device is None or args.dtype is None or args.image_digest is None:
            parser.error(
                "--verify-authorization requires --device, --dtype and --image-digest"
            )
    return args


def _summary(payload: Mapping[str, object], keys: tuple[str, ...]) -> dict[str, object]:
    return {key: payload[key] for key in keys}


def main() -> None:
    args = parse_args()
    manifest = load_manifest(args.manifest)

    if args.freeze_project:
        payload = freeze_project_environment(
            manifest,
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
        summary = _summary(
            payload,
            (
                "campaign_id",
                "freeze_scope",
                "freeze_digest",
                "project_source_commit",
                "manifest_digest",
                "torch2pc_commit",
                "torch2pc_source_sha256",
                "b0_cell_count",
                "canonical_protocol",
                "output_root",
                "minimum_free_bytes",
                "evidence",
                "full_campaign_complete",
            ),
        )
        print(json.dumps(summary, indent=2, sort_keys=True))
        return

    if args.preflight_lane:
        freeze_record = _load_json_object(args.freeze_record)
        payload = capture_lane_preflight(
            freeze_record,
            manifest,
            torch2pc_dir=args.torch2pc_dir,
            source_commit=args.source_commit,
            device=args.device,
            dtype=args.dtype,
            image_digest=args.image_digest,
        )
        output_path = validated_plan_output_path(
            args.output,
            output_root=Path(str(freeze_record["output_root"])),
        )
        atomic_write_json(output_path, payload)
        summary = _summary(
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
                "output_root",
                "minimum_free_bytes",
                "evidence",
                "full_campaign_complete",
            ),
        )
        print(json.dumps(summary, indent=2, sort_keys=True))
        return

    if args.issue_authorization:
        freeze_record = _load_json_object(args.freeze_record)
        lane_preflights = [_load_json_object(path) for path in args.lane_preflight]
        payload = issue_campaign_authorization(
            freeze_record,
            lane_preflights,
            operator_acknowledgement=args.operator_acknowledgement,
        )
        output_path = validated_plan_output_path(
            args.output,
            output_root=Path(str(freeze_record["output_root"])),
        )
        atomic_write_json(output_path, payload)
        summary = _summary(
            payload,
            (
                "campaign_id",
                "authorization_scope",
                "authorization_token",
                "project_source_commit",
                "manifest_digest",
                "torch2pc_commit",
                "authorized_cell_count",
                "canonical_protocol",
                "output_root",
                "execution_permitted",
                "evidence",
                "full_campaign_complete",
                "results_publication_permitted",
                "test_dataset_access",
            ),
        )
        print(json.dumps(summary, indent=2, sort_keys=True))
        return

    authorization = _load_json_object(args.authorization)
    validate_campaign_authorization(authorization)
    payload = verify_authorization_for_lane(
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


if __name__ == "__main__":
    main()
