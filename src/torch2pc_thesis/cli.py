from __future__ import annotations

import argparse
import json
import time
from typing import Any

from torch2pc_thesis.config import (
    TRAINING_STAGES,
    config_sha256,
    resolve_config,
    validate_config,
    write_resolved,
)


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="torch2pc-thesis")
    sub = root.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate")
    validate.add_argument("--config-root", default="configs")
    validate.add_argument("--stage", default="smoke")
    validate.add_argument("--method", default="bp")
    validate.add_argument("--hardware", default="rx7700xt_5700x3d")

    resolve = sub.add_parser("resolve")
    resolve.add_argument("--config-root", default="configs")
    resolve.add_argument("--stage", required=True)
    resolve.add_argument("--method", required=True)
    resolve.add_argument("--hardware", default="rx7700xt_5700x3d")
    resolve.add_argument("--experiment")
    resolve.add_argument("--dataset")
    resolve.add_argument("--model")
    resolve.add_argument("--seed", type=int)
    resolve.add_argument("--eta", type=float)
    resolve.add_argument("--inference-steps", type=int)
    resolve.add_argument("--output", required=True)

    run = sub.add_parser("run")
    run.add_argument("--config-root", default="configs")
    run.add_argument("--stage", required=True, choices=sorted(TRAINING_STAGES))
    run.add_argument("--method", required=True)
    run.add_argument("--hardware", default="rx7700xt_5700x3d")
    run.add_argument("--experiment")
    run.add_argument("--dataset")
    run.add_argument("--model")
    run.add_argument("--seed", type=int)
    run.add_argument("--eta", type=float)
    run.add_argument("--inference-steps", type=int)

    report = sub.add_parser("report")
    report.add_argument("--registry", default="experiments/registry.csv")
    report.add_argument("--stage", default="final")
    report.add_argument("--summary-dir", default="results/summaries")
    report.add_argument("--table-dir", default="results/tables")

    compare = sub.add_parser("compare")
    compare.add_argument(
        "--reference-registry", default="experiments/registry-final-80-completed.csv"
    )
    compare.add_argument(
        "--candidate-registry", default="experiments/registry-stage-2-80-completed.csv"
    )
    compare.add_argument("--output-dir", default="results/cross-version")

    manifest = sub.add_parser("manifest")
    manifest.add_argument("--directory", default="results")
    manifest.add_argument("--output", default="results/summaries/results_manifest.json")
    manifest.add_argument("--environment-lock")

    registry = sub.add_parser("registry")
    registry.add_argument("--path", default="experiments/registry.csv")

    stage3_check = sub.add_parser("stage3-check")
    stage3_check.add_argument("--root", default=".")
    stage3_check.add_argument("--design", default="configs/stage3/design.yaml")

    stage3_plan = sub.add_parser("stage3-plan")
    stage3_plan.add_argument("--design", default="configs/stage3/design.yaml")
    stage3_plan.add_argument(
        "--output", default="build/stage3/stage3_design_plan.json"
    )

    return root


def resolved_from_args(args: argparse.Namespace) -> dict[str, Any]:
    config = resolve_config(
        args.config_root,
        stage=args.stage,
        method=args.method,
        hardware=args.hardware,
        experiment=getattr(args, "experiment", None),
    )
    if getattr(args, "dataset", None):
        config["data"]["dataset"] = args.dataset
    if getattr(args, "model", None):
        config["model"]["architecture"] = args.model
    if getattr(args, "seed", None) is not None:
        config["reproducibility"]["model_seed"] = args.seed
    if getattr(args, "eta", None) is not None:
        config["method"]["eta"] = args.eta
    if getattr(args, "inference_steps", None) is not None:
        config["method"]["inference_steps"] = args.inference_steps
    validate_config(config)
    return config


def main() -> None:
    args = parser().parse_args()

    if args.command == "validate":
        config = resolved_from_args(args)
        print(json.dumps({"status": "ok", "config_sha256": config_sha256(config)}, indent=2))
        return

    if args.command == "resolve":
        config = resolved_from_args(args)
        print(write_resolved(config, args.output))
        return

    if args.command == "run":
        from torch2pc_thesis.experiment import execute

        config = resolved_from_args(args)
        identifier, run_id, metrics = execute(config)
        print(
            json.dumps(
                {"experiment_id": identifier, "run_id": run_id, "metrics": metrics},
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    if args.command == "report":
        from torch2pc_thesis.reporting import build_primary_assets

        print(
            json.dumps(
                build_primary_assets(
                    args.registry,
                    stage_name=args.stage,
                    summary_dir_path=args.summary_dir,
                    table_dir_path=args.table_dir,
                ),
                indent=2,
            )
        )
        return

    if args.command == "compare":
        from torch2pc_thesis.cross_version import build_cross_version_assets

        print(
            json.dumps(
                build_cross_version_assets(
                    args.reference_registry,
                    args.candidate_registry,
                    args.output_dir,
                ),
                indent=2,
            )
        )
        return

    if args.command == "manifest":
        from torch2pc_thesis.manifests import directory_manifest, environment_snapshot, write_json

        value = {
            "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "environment": environment_snapshot(args.environment_lock),
            "artifacts": directory_manifest(
                args.directory,
                exclude_paths=(args.output,),
            ),
        }
        print(write_json(value, args.output))
        return

    if args.command == "registry":
        from torch2pc_thesis.registry import initialize_registry, latest_by_run_id

        initialize_registry(args.path)
        print(json.dumps(latest_by_run_id(args.path), ensure_ascii=False, indent=2))
        return

    if args.command == "stage3-check":
        from torch2pc_thesis.stage3 import stage3_readiness_report

        report = stage3_readiness_report(args.root, args.design)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if report["status"] != "ready_for_stage3_implementation":
            raise SystemExit(1)
        return

    if args.command == "stage3-plan":
        from torch2pc_thesis.stage3 import load_stage3_design, write_stage3_design_plan

        design = load_stage3_design(args.design)
        print(write_stage3_design_plan(design, args.output))
        return

    raise RuntimeError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    main()
