#!/usr/bin/env python3
"""Validate and dry-run the preregistered Stage 3B execution manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from torch2pc_thesis.stage3b_execution import (
    STAGE3B_MANIFEST_RELATIVE_PATH,
    atomic_write_json,
    load_manifest,
    plan_dry_run,
    validated_plan_output_path,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
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
    parser.add_argument("--dry-run", action="store_true", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = load_manifest(args.manifest)
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
