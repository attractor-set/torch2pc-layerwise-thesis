#!/usr/bin/env python3
"""Plan or execute one authorized lane of confirmatory Stage 3B B2."""

from __future__ import annotations

import argparse
import json
import os
import uuid
from pathlib import Path

from torch2pc_thesis.models import build_model
from torch2pc_thesis.stage3b_b1_equivalence import atomic_write_json, canonical_json_digest
from torch2pc_thesis.stage3b_b2_confirmatory import (
    B2_CONFIRMATORY_RECONCILE_ACKNOWLEDGEMENT,
    B2ConfirmatoryError,
    B2ConfirmatoryOperatorInterruption,
    B2ConfirmatoryScientificError,
    build_triple_specs,
    load_and_validate_confirmatory_request,
    load_json_object,
    plan_confirmatory_lane,
    reconcile_orphaned_running_attempts,
    run_confirmatory_triple_attempt,
    select_specs,
)
from torch2pc_thesis.stage3b_b2_confirmatory_authorization import (
    validate_authorization,
    verify_b2_confirmatory_authorization_for_lane,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--verify-authorization-only", action="store_true")
    mode.add_argument("--execute-authorized-lane", action="store_true")
    mode.add_argument("--execute-engineering-smoke", action="store_true")
    mode.add_argument("--reconcile-running", action="store_true")
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--torch2pc-dir", type=Path, default=Path("external/Torch2PC"))
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--image-digest", required=True)
    parser.add_argument("--lane", choices=("cpu_float64", "rocm_float32"), required=True)
    parser.add_argument("--engineering-smoke", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--plan-output", type=Path)
    parser.add_argument("--operator-acknowledgement")
    args = parser.parse_args()
    if args.reconcile_running and (
        args.operator_acknowledgement != B2_CONFIRMATORY_RECONCILE_ACKNOWLEDGEMENT
    ):
        parser.error("orphan reconciliation requires the exact acknowledgement phrase")
    if args.retry_failed and not args.resume:
        parser.error("--retry-failed requires --resume")
    if args.execute_engineering_smoke:
        args.engineering_smoke = True
    if args.execute_authorized_lane and args.engineering_smoke:
        parser.error("--execute-authorized-lane cannot be combined with --engineering-smoke")
    return args


def main() -> int:
    args = parse_args()
    request = load_and_validate_confirmatory_request(args.request)
    authorization = load_json_object(args.authorization)
    validate_authorization(authorization)
    execution_mode = "engineering_smoke" if args.engineering_smoke else "confirmatory"
    verification = verify_b2_confirmatory_authorization_for_lane(
        authorization,
        request,
        project_root=args.project_root,
        torch2pc_dir=args.torch2pc_dir,
        output_root=args.output_root,
        source_commit=args.source_commit,
        lane=args.lane,
        image_digest=args.image_digest,
        execution_mode=execution_mode,
    )
    if args.verify_authorization_only:
        print(json.dumps(verification, indent=2, sort_keys=True))
        return 0
    if args.reconcile_running:
        reconciled = reconcile_orphaned_running_attempts(
            request,
            output_root=args.output_root,
            lane=args.lane,
            authorization_token=str(authorization["authorization_token"]),
            project_source_commit=str(authorization["project_source_commit"]),
            source_image_digest=str(authorization["image_digest"]),
            operator_acknowledgement=args.operator_acknowledgement,
        )
        print(
            json.dumps(
                {
                    "status": "reconciled",
                    "lane": args.lane,
                    "reconciled_attempts": reconciled,
                    "reconciled_count": len(reconciled),
                    "evidence": False,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    plan = plan_confirmatory_lane(
        request,
        output_root=args.output_root,
        lane=args.lane,
        engineering_smoke=args.engineering_smoke,
        resume=args.resume,
        retry_failed=args.retry_failed,
    )
    plan_record = {
        **plan.to_record(),
        "authorization_verified": True,
        "execution_permitted": True,
        "source_commit": args.source_commit,
        "image_digest": args.image_digest,
        "output_root": str(args.output_root.expanduser().resolve()),
        "request_digest": canonical_json_digest(request),
    }
    if args.plan_output is not None:
        _write_plan(args.plan_output, args.output_root, plan_record)
    print(json.dumps(plan_record, indent=2, sort_keys=True))
    if args.dry_run:
        return 0

    if not plan.selected_triple_ids:
        print("INFO: no triples selected for execution")
        return 0
    triples_by_id = {
        spec.pair_id: spec
        for spec in select_specs(
            build_triple_specs(request),
            lane=args.lane,
            engineering_smoke=args.engineering_smoke,
        )
    }
    run_id = f"run-{uuid.uuid4().hex}"
    output_root = args.output_root.expanduser().resolve()
    run_root = output_root / "runs" / args.lane / run_id
    lock_path = output_root / "locks" / f"{args.lane}.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_fd = _acquire_lock(lock_path, run_id)
    started = {
        "run_id": run_id,
        "lane": args.lane,
        "request_id": request["request_id"],
        "request_digest": canonical_json_digest(request),
        "authorization_token": authorization["authorization_token"],
        "selected_triple_count": len(plan.selected_triple_ids),
        "selected_triple_ids": list(plan.selected_triple_ids),
        "resume": args.resume,
        "retry_failed": args.retry_failed,
        "engineering_smoke": args.engineering_smoke,
        "evidence": False,
        "test_dataset_access": False,
    }
    completed_count = 0
    try:
        run_root.mkdir(parents=True, exist_ok=False)
        atomic_write_json(run_root / "started.json", started)
        for triple_id in plan.selected_triple_ids:
            emergency_stop = Path(str(authorization["emergency_stop_path"]))
            if emergency_stop.exists():
                raise B2ConfirmatoryOperatorInterruption(
                    f"operator emergency stop is active: {emergency_stop}"
                )
            run_confirmatory_triple_attempt(
                triples_by_id[triple_id],
                project_root=args.project_root,
                torch2pc_dir=args.torch2pc_dir,
                output_root=output_root,
                request_digest=canonical_json_digest(request),
                authorization_token=str(authorization["authorization_token"]),
                model_builder=build_model,
                project_source_commit=str(authorization["project_source_commit"]),
                source_image_digest=str(authorization["image_digest"]),
            )
            completed_count += 1
            print(f"COMPLETED_TRIPLE={triple_id}")
        completed = {
            **started,
            "status": "completed",
            "completed_triple_count": completed_count,
        }
        atomic_write_json(run_root / "completed.json", completed)
        return 0
    except (B2ConfirmatoryOperatorInterruption, KeyboardInterrupt) as error:
        failed = {
            **started,
            "status": "failed",
            "failure_class": "operator_interruption",
            "retry_eligible": True,
            "completed_triple_count": completed_count,
            "error": str(error) or type(error).__name__,
        }
        atomic_write_json(run_root / "failed.json", failed)
        print(f"ERROR: {failed['error']}")
        return 130
    except B2ConfirmatoryScientificError as error:
        failed = {
            **started,
            "status": "failed",
            "failure_class": "scientific",
            "retry_eligible": False,
            "completed_triple_count": completed_count,
            "error": str(error),
        }
        atomic_write_json(run_root / "failed.json", failed)
        print(f"ERROR: {error}")
        return 3
    except (B2ConfirmatoryError, OSError) as error:
        failed = {
            **started,
            "status": "failed",
            "failure_class": "infrastructure",
            "retry_eligible": True,
            "completed_triple_count": completed_count,
            "error": str(error),
        }
        atomic_write_json(run_root / "failed.json", failed)
        print(f"ERROR: {error}")
        return 4
    except Exception as error:
        failed = {
            **started,
            "status": "failed",
            "failure_class": "unknown",
            "retry_eligible": False,
            "completed_triple_count": completed_count,
            "error_type": type(error).__name__,
            "error": str(error),
        }
        atomic_write_json(run_root / "failed.json", failed)
        print(f"ERROR: {error}")
        return 5
    finally:
        os.close(lock_fd)
        lock_path.unlink(missing_ok=True)


def _acquire_lock(path: Path, run_id: str) -> int:
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise B2ConfirmatoryError(f"lane lock is active: {path}") from error
    os.write(fd, (run_id + "\n").encode("utf-8"))
    return fd


def _write_plan(path: Path, output_root: Path, payload: dict[str, object]) -> None:
    root = output_root.expanduser().resolve()
    resolved = path.expanduser().resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise B2ConfirmatoryError(f"plan output must be under output root: {resolved}") from error
    atomic_write_json(resolved, payload)


if __name__ == "__main__":
    raise SystemExit(main())
