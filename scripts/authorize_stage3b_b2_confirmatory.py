#!/usr/bin/env python3
"""Freeze, preflight, authorize, and verify confirmatory EQ-B2 execution."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Mapping
from pathlib import Path

from torch2pc_thesis.stage3b_b1_equivalence import atomic_write_json
from torch2pc_thesis.stage3b_b2_confirmatory import (
    load_and_validate_confirmatory_request,
    load_json_object,
)
from torch2pc_thesis.stage3b_b2_confirmatory_authorization import (
    B2_CONFIRMATORY_DEFAULT_MINIMUM_FREE_BYTES,
    B2_CONFIRMATORY_EXECUTION_MODES,
    capture_b2_confirmatory_lane_preflight,
    freeze_b2_confirmatory_project,
    issue_b2_confirmatory_authorization,
    validate_authorization,
    verify_b2_confirmatory_authorization_for_lane,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--freeze-project", action="store_true")
    mode.add_argument("--preflight-lane", action="store_true")
    mode.add_argument("--issue-authorization", action="store_true")
    mode.add_argument("--verify-authorization", action="store_true")
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--torch2pc-dir", type=Path, default=Path("external/Torch2PC"))
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("/tmp/torch2pc-stage3b-b2-confirmatory-v1"),
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--freeze-record", type=Path)
    parser.add_argument("--lane-preflight", type=Path, action="append", default=[])
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--lane", choices=("cpu_float64", "rocm_float32"))
    parser.add_argument("--image-digest")
    parser.add_argument(
        "--source-commit",
        default=os.environ.get("PROJECT_SOURCE_COMMIT", ""),
    )
    parser.add_argument(
        "--minimum-free-bytes",
        type=int,
        default=B2_CONFIRMATORY_DEFAULT_MINIMUM_FREE_BYTES,
    )
    parser.add_argument("--operator-acknowledgement")
    parser.add_argument(
        "--execution-mode",
        choices=B2_CONFIRMATORY_EXECUTION_MODES,
        default="confirmatory",
    )
    args = parser.parse_args()
    if args.freeze_project:
        _require(parser, args.output, "--freeze-project requires --output")
        _require(parser, args.source_commit, "--freeze-project requires --source-commit")
        _require(parser, args.image_digest, "--freeze-project requires --image-digest")
    elif args.preflight_lane:
        _require(parser, args.freeze_record, "--preflight-lane requires --freeze-record")
        _require(parser, args.output, "--preflight-lane requires --output")
        _require(parser, args.lane, "--preflight-lane requires --lane")
        _require(parser, args.image_digest, "--preflight-lane requires --image-digest")
        _require(parser, args.source_commit, "--preflight-lane requires --source-commit")
    elif args.issue_authorization:
        _require(parser, args.freeze_record, "--issue-authorization requires --freeze-record")
        _require(parser, args.output, "--issue-authorization requires --output")
        if len(args.lane_preflight) != 2:
            parser.error("--issue-authorization requires exactly two --lane-preflight values")
        _require(
            parser,
            args.operator_acknowledgement,
            "--issue-authorization requires --operator-acknowledgement",
        )
    else:
        _require(parser, args.authorization, "--verify-authorization requires --authorization")
        _require(parser, args.lane, "--verify-authorization requires --lane")
        _require(parser, args.image_digest, "--verify-authorization requires --image-digest")
        _require(parser, args.source_commit, "--verify-authorization requires --source-commit")
    return args


def main() -> int:
    args = parse_args()
    request = load_and_validate_confirmatory_request(args.request)
    if args.freeze_project:
        payload = freeze_b2_confirmatory_project(
            request,
            request_path=args.request,
            project_root=args.project_root,
            torch2pc_dir=args.torch2pc_dir,
            output_root=args.output_root,
            source_commit=args.source_commit,
            image_digest=args.image_digest,
            execution_mode=args.execution_mode,
            minimum_free_bytes=args.minimum_free_bytes,
        )
        _write_output(args.output, args.output_root, payload)
        print(
            json.dumps(
                _summary(
                    payload,
                    (
                        "campaign_id",
                        "freeze_scope",
                        "freeze_digest",
                        "project_source_commit",
                        "request_digest",
                        "torch2pc_commit",
                        "execution_mode",
                        "authorized_triple_count",
                        "authorized_comparison_count",
                        "canonical_lanes",
                        "output_root",
                        "source_image_digest",
                        "evidence",
                        "test_dataset_access",
                    ),
                ),
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.preflight_lane:
        freeze = load_json_object(args.freeze_record)
        payload = capture_b2_confirmatory_lane_preflight(
            freeze,
            request,
            project_root=args.project_root,
            torch2pc_dir=args.torch2pc_dir,
            output_root=args.output_root,
            source_commit=args.source_commit,
            lane=args.lane,
            image_digest=args.image_digest,
        )
        _write_output(args.output, args.output_root, payload)
        print(
            json.dumps(
                _summary(
                    payload,
                    (
                        "campaign_id",
                        "preflight_scope",
                        "freeze_digest",
                        "lane_preflight_digest",
                        "execution_mode",
                        "lane",
                        "image_digest",
                        "runtime",
                        "output_root",
                        "evidence",
                        "test_dataset_access",
                    ),
                ),
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.issue_authorization:
        freeze = load_json_object(args.freeze_record)
        preflights = [load_json_object(path) for path in args.lane_preflight]
        payload = issue_b2_confirmatory_authorization(
            freeze,
            preflights,
            operator_acknowledgement=args.operator_acknowledgement,
        )
        _write_output(args.output, args.output_root, payload)
        print(
            json.dumps(
                _summary(
                    payload,
                    (
                        "campaign_id",
                        "authorization_scope",
                        "authorization_token",
                        "project_source_commit",
                        "request_digest",
                        "torch2pc_commit",
                        "image_digest",
                        "execution_mode",
                        "authorized_triple_count",
                        "authorized_comparison_count",
                        "authorized_lanes",
                        "output_root",
                        "execution_permitted",
                        "measurements_allowed",
                        "evidence",
                        "test_dataset_access",
                    ),
                ),
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    authorization = load_json_object(args.authorization)
    validate_authorization(authorization)
    payload = verify_b2_confirmatory_authorization_for_lane(
        authorization,
        request,
        project_root=args.project_root,
        torch2pc_dir=args.torch2pc_dir,
        output_root=args.output_root,
        source_commit=args.source_commit,
        lane=args.lane,
        image_digest=args.image_digest,
        execution_mode=args.execution_mode,
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _write_output(path: Path, output_root: Path, payload: Mapping[str, object]) -> None:
    root = output_root.expanduser().resolve()
    resolved = path.expanduser().resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ValueError(f"output path must be under output root: {resolved}") from error
    atomic_write_json(resolved, payload)


def _summary(payload: Mapping[str, object], keys: tuple[str, ...]) -> dict[str, object]:
    return {key: payload[key] for key in keys}


def _require(parser: argparse.ArgumentParser, value: object, message: str) -> None:
    if value is None or value == "":
        parser.error(message)


if __name__ == "__main__":
    raise SystemExit(main())
