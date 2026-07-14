#!/usr/bin/env python3
"""Validate and dry-run the preregistered Stage 3B execution manifest."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from torch2pc_thesis.stage3b_execution import (
    STAGE3B_MANIFEST_RELATIVE_PATH,
    atomic_write_json,
    execute_single_cell_smoke,
    load_manifest,
    plan_dry_run,
    validated_plan_output_path,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        allow_abbrev=False,
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=STAGE3B_MANIFEST_RELATIVE_PATH,
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("/tmp/torch2pc-stage3b-execution-readiness"),
    )
    parser.add_argument("--cell-id", action="append", default=[])
    parser.add_argument("--plan-output", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute-smoke", action="store_true")
    parser.add_argument("--device", choices=("cpu", "gpu", "cuda", "rocm"))
    parser.add_argument("--dtype", choices=("float32", "float64"))
    parser.add_argument(
        "--torch2pc-dir",
        type=Path,
        default=Path("external/Torch2PC"),
    )
    parser.add_argument(
        "--source-commit",
        default=os.environ.get("TORCH2PC_SOURCE_COMMIT", ""),
    )
    parser.add_argument(
        "--image-id",
        default=os.environ.get("EXPERIMENT_IMAGE"),
    )
    args = parser.parse_args()
    if args.execute_smoke:
        if len(args.cell_id) != 1:
            parser.error("--execute-smoke requires exactly one --cell-id")
        if args.device is None or args.dtype is None:
            parser.error("--execute-smoke requires --device and --dtype")
        if not args.source_commit:
            parser.error(
                "--execute-smoke requires --source-commit or "
                "TORCH2PC_SOURCE_COMMIT"
            )
        if args.plan_output is not None:
            parser.error("--plan-output is available only with --dry-run")
    return args


def main() -> None:
    args = parse_args()
    manifest = load_manifest(args.manifest)
    if args.execute_smoke:
        payload = execute_single_cell_smoke(
            manifest,
            output_root=args.output_root,
            cell_id=args.cell_id[0],
            device=args.device,
            dtype=args.dtype,
            torch2pc_dir=args.torch2pc_dir,
            source_commit=args.source_commit,
            image_id=args.image_id,
        )
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    plan = plan_dry_run(
        manifest,
        output_root=args.output_root,
        selected_cell_ids=args.cell_id,
    )
    payload = plan.to_record()
    if args.plan_output is not None:
        plan_output = validated_plan_output_path(
            args.plan_output, output_root=args.output_root
        )
        atomic_write_json(plan_output, payload)
    summary_payload = {
        key: payload[key]
        for key in (
            "schema_version",
            "campaign_id",
            "evidence",
            "dry_run",
            "execution_performed",
            "manifest_digest",
            "output_root",
            "selected_cell_count",
            "summary",
        )
    }
    print(json.dumps(summary_payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
