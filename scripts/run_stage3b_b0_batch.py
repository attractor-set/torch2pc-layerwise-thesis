#!/usr/bin/env python3

"""Plan or execute a bounded Stage 3B B0 batch smoke lane."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from torch2pc_thesis.stage3b_batch import (
    B0_BATCH_DEFAULT_MAX_ATTEMPTS,
    B0_BATCH_MAX_CELLS,
    execute_b0_batch_smoke,
    plan_b0_batch_smoke,
)
from torch2pc_thesis.stage3b_execution import (
    STAGE3B_MANIFEST_RELATIVE_PATH,
    atomic_write_json,
    load_manifest,
    validated_plan_output_path,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--manifest", type=Path, default=STAGE3B_MANIFEST_RELATIVE_PATH)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("/tmp/torch2pc-stage3b-b0-batch-readiness"),
    )
    parser.add_argument("--plan-output", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute-batch-smoke", action="store_true")
    parser.add_argument("--device", required=True, choices=("cpu", "rocm"))
    parser.add_argument("--dtype", required=True, choices=("float32", "float64"))
    parser.add_argument("--max-cells", type=int, default=B0_BATCH_MAX_CELLS)
    parser.add_argument("--max-attempts", type=int, default=B0_BATCH_DEFAULT_MAX_ATTEMPTS)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--torch2pc-dir", type=Path, default=Path("external/Torch2PC"))
    parser.add_argument(
        "--source-commit",
        default=os.environ.get("TORCH2PC_SOURCE_COMMIT", ""),
    )
    parser.add_argument("--image-id", default=os.environ.get("EXPERIMENT_IMAGE"))
    args = parser.parse_args()

    if not args.source_commit:
        parser.error("--source-commit or TORCH2PC_SOURCE_COMMIT is required")
    if args.execute_batch_smoke and args.plan_output is not None:
        parser.error("--plan-output is available only with --dry-run")
    if args.execute_batch_smoke and not 1 <= args.max_cells <= B0_BATCH_MAX_CELLS:
        parser.error(
            f"--execute-batch-smoke requires 1 <= --max-cells <= {B0_BATCH_MAX_CELLS}"
        )
    return args


def main() -> None:
    args = parse_args()
    manifest = load_manifest(args.manifest)

    if args.execute_batch_smoke:
        payload = execute_b0_batch_smoke(
            manifest,
            output_root=args.output_root,
            device=args.device,
            dtype=args.dtype,
            source_commit=args.source_commit,
            max_cells=args.max_cells,
            max_attempts=args.max_attempts,
            resume=args.resume,
            retry_failed=args.retry_failed,
            torch2pc_dir=args.torch2pc_dir,
            image_id=args.image_id,
        )
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    plan = plan_b0_batch_smoke(
        manifest,
        output_root=args.output_root,
        device=args.device,
        dtype=args.dtype,
        source_commit=args.source_commit,
        max_cells=args.max_cells,
        max_attempts=args.max_attempts,
        resume=args.resume,
        retry_failed=args.retry_failed,
    )
    payload = plan.to_record()
    if args.plan_output is not None:
        plan_output = validated_plan_output_path(args.plan_output, output_root=args.output_root)
        atomic_write_json(plan_output, payload)

    summary = {
        key: payload[key]
        for key in (
            "schema_version",
            "campaign_id",
            "execution_scope",
            "evidence",
            "full_campaign_complete",
            "full_campaign_execution_enabled",
            "manifest_digest",
            "output_root",
            "source_commit",
            "device",
            "dtype",
            "b0_cell_count",
            "max_cells",
            "hard_max_cells",
            "summary",
            "selected_cell_ids",
        )
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
