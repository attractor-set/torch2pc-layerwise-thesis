#!/usr/bin/env python3
"""Build a blocked candidate-aware plan for matched Stage 3B profiling."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from torch2pc_thesis.stage3b_matched_profiling import load_json_object
from torch2pc_thesis.stage3b_matched_runner import (
    build_matched_runner_plan,
    validate_runner_plan,
    write_matched_runner_plan,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = (
    PROJECT_ROOT
    / "experiments/frozen/stage3b-matched-profiling-v2/manifest.json"
)
DEFAULT_REQUEST = (
    PROJECT_ROOT
    / "experiments/frozen/stage3b-matched-profiling-v2/request.json"
)
DEFAULT_OUTPUT_ROOT = Path("/tmp/torch2pc-stage3b-matched-runner")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate candidate dispatch and build a non-executable matched "
            "profiling plan. This command cannot run measurements."
        )
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--request", type=Path, default=DEFAULT_REQUEST)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument(
        "--write",
        action="store_true",
        help="write plan.json under the validated temporary output root",
    )
    parser.add_argument(
        "--skip-dispatch-import-check",
        action="store_true",
        help="build metadata without importing the three loader modules",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = load_json_object(args.manifest)
    request = load_json_object(args.request)
    plan = build_matched_runner_plan(
        manifest,
        request,
        output_root=args.output_root,
        verify_dispatch=not args.skip_dispatch_import_check,
    )
    record = plan.to_record()
    validate_runner_plan(record)

    written_path: str | None = None
    if args.write:
        path = write_matched_runner_plan(
            args.output_root / "plan.json",
            output_root=args.output_root,
            plan=plan,
        )
        written_path = str(path)

    summary = {
        "runner_id": record["runner_id"],
        "status": record["status"],
        "selected_cell_count": record["selected_cell_count"],
        "dispatch_verified": record["dispatch_verified"],
        "runtime_authorization": record["runtime_authorization"],
        "measurements_allowed": record["measurements_allowed"],
        "summary": record["summary"],
        "plan_digest": record["plan_digest"],
        "written_path": written_path,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
