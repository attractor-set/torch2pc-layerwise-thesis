#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import torch

from torch2pc_thesis.config import resolve_config
from torch2pc_thesis.data import build_dataloaders
from torch2pc_thesis.models import build_model
from torch2pc_thesis.reproducibility import configure_threads, set_global_seed
from torch2pc_thesis.stage3b_a1_controls import (
    EquivalenceThresholds,
    validate_execution_lane,
)
from torch2pc_thesis.stage3b_a1_obs_ni0 import ObserverArm, evaluate_obs_ni0
from torch2pc_thesis.stage3b_a1_obs_oh0 import (
    BENCHMARK_SCHEMA_ID,
    TimingPairRecord,
    TimingPhase,
    aggregate_timing_records,
    benchmark_schema_manifest,
    execution_order_for,
    run_timing_pair,
)
from torch2pc_thesis.stage3b_a1_obs_oh0_memory import (
    MemoryExecutionResult,
    MemoryPairRecord,
    MemoryWorkerRequest,
    aggregate_memory_records,
)
from torch2pc_thesis.stage3b_a1_observer import OBSERVER_SCHEMA_ID


def git_output(path: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(path), *args],
        text=True,
    ).strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Stage 3B OBS-OH0 passive-observer overhead controls."
    )
    parser.add_argument("device", choices=["cpu", "gpu"])
    parser.add_argument(
        "--execution-scope",
        choices=["smoke", "confirmatory", "development"],
        default="smoke",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "results/stage-3/a1-shortcut-observer-controls/working/obs-oh0"
        ),
    )
    parser.add_argument("--optimizer-lr", type=float, default=1e-3)
    parser.add_argument("--max-batches", type=int, default=1)
    parser.add_argument("--timing-repeats", type=int, default=3)
    parser.add_argument("--warmup-pairs", type=int, default=1)
    parser.add_argument("--rss-sampler-interval-ms", type=float, default=1.0)
    return parser.parse_args()


def validate_execution_scope(args: argparse.Namespace) -> None:
    registered = {
        "smoke": (1, 3, 1),
        "confirmatory": (10, 3, 3),
    }
    expected = registered.get(args.execution_scope)
    observed = (args.max_batches, args.timing_repeats, args.warmup_pairs)
    if expected is not None and observed != expected:
        raise ValueError(
            f"OBS-OH0 {args.execution_scope} requires "
            f"max_batches/timing_repeats/warmup_pairs={expected}; "
            f"observed {observed}"
        )


def run_memory_worker(
    *,
    request: MemoryWorkerRequest,
    output_dir: Path,
    serial: int,
) -> MemoryExecutionResult:
    temporary_dir = output_dir / ".obs_oh0_memory_workers"
    temporary_dir.mkdir(parents=True, exist_ok=True)
    request_path = temporary_dir / f"request-{serial:04d}.json"
    result_path = temporary_dir / f"result-{serial:04d}.json"
    request_path.write_text(
        json.dumps(request.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    subprocess.run(
        [
            sys.executable,
            "scripts/run_stage3b_a1_obs_oh0_memory_worker.py",
            "--request",
            str(request_path),
            "--output",
            str(result_path),
        ],
        check=True,
    )
    raw = json.loads(result_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError("OBS-OH0 memory worker output must be a JSON object")
    result = MemoryExecutionResult.from_dict(raw)
    if not result.valid:
        raise RuntimeError("OBS-OH0 memory worker returned an invalid result")
    return result


def main() -> None:
    args = parse_args()
    if args.optimizer_lr <= 0:
        raise ValueError("--optimizer-lr must be positive")
    if args.max_batches < 1:
        raise ValueError("--max-batches must be at least one")
    if args.timing_repeats < 1:
        raise ValueError("--timing-repeats must be at least one")
    if args.warmup_pairs < 1:
        raise ValueError("--warmup-pairs must be at least one")
    if not 0.0 < args.rss_sampler_interval_ms <= 1.0:
        raise ValueError("--rss-sampler-interval-ms must be within (0, 1]")
    validate_execution_scope(args)

    controlled_container = os.environ.get("TORCH2PC_CONTROLLED_CONTAINER") == "1"
    execution_lane = os.environ.get("TORCH2PC_EXECUTION_LANE")
    source_git_commit = os.environ.get("SOURCE_GIT_COMMIT")
    source_git_branch = os.environ.get("SOURCE_GIT_BRANCH")
    experiment_image = os.environ.get("EXPERIMENT_IMAGE")
    if not source_git_commit or not source_git_branch or not experiment_image:
        raise RuntimeError("OBS-OH0 controlled provenance environment is incomplete")

    execution_environment = validate_execution_lane(
        device=args.device,
        controlled_container=controlled_container,
        lane=execution_lane,
        source_git_commit=source_git_commit,
        hip_version=getattr(torch.version, "hip", None),
        cuda_available=torch.cuda.is_available(),
        torch_version=torch.__version__,
    )

    config: dict[str, Any] = resolve_config(
        "configs",
        stage="final_stage_2",
        method="exact",
    )
    config["runtime"]["device"] = args.device
    config["runtime"]["dtype"] = "float64" if args.device == "cpu" else "float32"

    device = torch.device("cpu" if args.device == "cpu" else "cuda")
    dtype = torch.float64 if args.device == "cpu" else torch.float32
    lane = "rocm" if args.device == "gpu" else "cpu"
    device_name = torch.cuda.get_device_name(0) if args.device == "gpu" else "cpu"
    execution_environment["experiment_image"] = experiment_image
    execution_environment["source_git_branch"] = source_git_branch
    execution_environment["device_name"] = device_name
    execution_environment["cpu_thread_count"] = (
        1 if args.device == "cpu" else int(config["runtime"]["torch_threads"])
    )
    execution_environment["visible_rocm_devices"] = os.environ.get(
        "ROCR_VISIBLE_DEVICES",
        os.environ.get("HIP_VISIBLE_DEVICES"),
    )

    configure_threads(int(execution_environment["cpu_thread_count"]))

    torch2pc_path = Path(config["torch2pc"]["local_path"])
    torch2pc_commit = str(config["torch2pc"]["commit"])
    if git_output(torch2pc_path, "rev-parse", "HEAD") != torch2pc_commit:
        raise RuntimeError("Torch2PC checkout differs from the pinned candidate commit")
    if git_output(torch2pc_path, "status", "--porcelain"):
        raise RuntimeError("Torch2PC worktree is dirty")

    thresholds_cfg = config["controls"]["thresholds"][args.device]
    thresholds = EquivalenceThresholds(
        min_cosine=float(thresholds_cfg["min_cosine"]),
        max_relative_l2=float(thresholds_cfg["max_relative_l2"]),
        zero_atol=1e-12 if args.device == "cpu" else 1e-7,
    )
    model_seeds = [int(value) for value in config["controls"]["model_seeds"]]
    if model_seeds != [0, 1, 2]:
        raise RuntimeError("OBS-OH0 requires registered model seeds [0, 1, 2]")

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    temporary_dir = output_dir / ".obs_oh0_memory_workers"
    if temporary_dir.exists():
        shutil.rmtree(temporary_dir)

    guard_records: list[dict[str, Any]] = []
    timing_records: list[TimingPairRecord] = []
    memory_records: list[MemoryPairRecord] = []
    registered_batches: dict[
        tuple[int, int],
        tuple[torch.nn.Sequential, torch.Tensor, torch.Tensor],
    ] = {}

    for model_seed in model_seeds:
        set_global_seed(model_seed, warn_only=False)
        bundle = build_dataloaders(config, include_test=False, download=False)
        base_model = build_model("lenet_classic").to(device=device, dtype=dtype)
        if not isinstance(base_model, torch.nn.Sequential):
            raise TypeError("OBS-OH0 requires a top-level nn.Sequential model")
        processed = 0
        for batch_index, (inputs, targets) in enumerate(bundle.train):
            if processed >= args.max_batches:
                break
            device_inputs = inputs.to(device=device, dtype=dtype)
            device_targets = targets.to(device=device)
            registered_batches[(model_seed, batch_index)] = (
                base_model,
                device_inputs,
                device_targets,
            )

            guard = evaluate_obs_ni0(
                base_model,
                device_inputs,
                device_targets,
                torch2pc_dir=torch2pc_path,
                seed=model_seed,
                thresholds=thresholds,
                optimizer_factory=lambda parameters: torch.optim.SGD(
                    parameters,
                    lr=args.optimizer_lr,
                    momentum=0.0,
                ),
            )
            for item in guard.to_summary_dicts():
                item["model_seed"] = model_seed
                item["batch_index"] = batch_index
                item["benchmark_schema_id"] = BENCHMARK_SCHEMA_ID
                guard_records.append(item)
            processed += 1
        if processed != args.max_batches:
            raise RuntimeError("The training loader produced too few OBS-OH0 batches")

    if not all(bool(record["passed"]) for record in guard_records):
        raise RuntimeError("OBS-OH0 correctness guard failed")

    warmup_model, warmup_inputs, warmup_targets = registered_batches[(0, 0)]
    for arm in ObserverArm:
        for repeat_index in range(args.warmup_pairs):
            timing_records.append(
                run_timing_pair(
                    warmup_model,
                    warmup_inputs,
                    warmup_targets,
                    phase=TimingPhase.WARMUP,
                    lane=lane,
                    arm=arm,
                    model_seed=0,
                    batch_index=0,
                    repeat_index=repeat_index,
                    torch2pc_dir=torch2pc_path,
                    device=device,
                )
            )

    for (model_seed, batch_index), (base_model, inputs, targets) in sorted(
        registered_batches.items()
    ):
        for arm in ObserverArm:
            for repeat_index in range(args.timing_repeats):
                timing_records.append(
                    run_timing_pair(
                        base_model,
                        inputs,
                        targets,
                        phase=TimingPhase.MEASURED,
                        lane=lane,
                        arm=arm,
                        model_seed=model_seed,
                        batch_index=batch_index,
                        repeat_index=repeat_index,
                        torch2pc_dir=torch2pc_path,
                        device=device,
                    )
                )

    timing_summaries = aggregate_timing_records(
        timing_records,
        model_seeds=model_seeds,
    )

    worker_serial = 0
    for model_seed, batch_index in sorted(registered_batches):
        for arm in ObserverArm:
            order = execution_order_for(
                arm=arm,
                model_seed=model_seed,
                batch_index=batch_index,
                repeat_index=0,
            )
            sequence = (
                (False, True)
                if order.value == "off_then_on"
                else (True, False)
            )
            results: dict[bool, MemoryExecutionResult] = {}
            for observer_enabled in sequence:
                request = MemoryWorkerRequest(
                    device=args.device,
                    lane=lane,
                    arm=arm,
                    observer_enabled=observer_enabled,
                    model_seed=model_seed,
                    batch_index=batch_index,
                    source_git_commit=source_git_commit,
                    source_git_branch=source_git_branch,
                    experiment_image=experiment_image,
                    rss_sampler_interval_ms=args.rss_sampler_interval_ms,
                )
                results[observer_enabled] = run_memory_worker(
                    request=request,
                    output_dir=output_dir,
                    serial=worker_serial,
                )
                worker_serial += 1
            memory_records.append(
                MemoryPairRecord(
                    order=order,
                    reference=results[False],
                    candidate=results[True],
                )
            )

    memory_summaries = aggregate_memory_records(
        memory_records,
        lane=lane,
        model_seeds=model_seeds,
    )
    if temporary_dir.exists():
        shutil.rmtree(temporary_dir)

    schema = benchmark_schema_manifest(
        execution_scope=args.execution_scope,
        top_level_layers=6,
        model_seeds=model_seeds,
        batches_per_seed=args.max_batches,
        timing_repeats=args.timing_repeats,
        warmup_pairs=args.warmup_pairs,
        rss_sampler_interval_ms=args.rss_sampler_interval_ms,
    )
    schema["provenance"] = {
        "source_git_commit": source_git_commit,
        "source_git_branch": source_git_branch,
        "experiment_image": experiment_image,
        "torch2pc_commit": torch2pc_commit,
        "execution_environment": execution_environment,
    }
    scope = str(args.execution_scope)
    runtime_budget_passed = all(item.passed for item in timing_summaries.values())
    memory_budget_passed = all(item.passed for item in memory_summaries.values())
    budget_enforced = scope == "confirmatory"
    structural_passed = (
        all(item.passed_structure for item in timing_records)
        and all(item.passed_structure for item in memory_records)
        and len({item.key for item in timing_records}) == len(timing_records)
        and len({item.key for item in memory_records}) == len(memory_records)
    )
    passed = (
        structural_passed
        and all(bool(record["passed"]) for record in guard_records)
        and (
            runtime_budget_passed and memory_budget_passed
            if budget_enforced
            else True
        )
    )

    guard_frame = pd.DataFrame.from_records(guard_records)
    timing_frame = pd.DataFrame.from_records(
        item.to_record() for item in timing_records
    )
    memory_frame = pd.DataFrame.from_records(
        item.to_record() for item in memory_records
    )
    provenance_columns = {
        "source_git_commit": source_git_commit,
        "source_git_branch": source_git_branch,
        "experiment_image": experiment_image,
        "torch2pc_commit": torch2pc_commit,
        "torch_version": execution_environment["torch_version"],
        "torch_hip_version": execution_environment["torch_hip_version"],
        "device_name": device_name,
        "dtype": str(dtype),
        "cpu_thread_count": execution_environment["cpu_thread_count"],
        "visible_rocm_devices": execution_environment["visible_rocm_devices"],
        "model_architecture": "lenet_classic",
        "batch_size": int(warmup_inputs.shape[0]),
    }
    for frame in (guard_frame, timing_frame, memory_frame):
        for name, value in reversed(tuple(provenance_columns.items())):
            if name not in frame.columns:
                frame.insert(0, name, value)

    timing_summary = {
        "benchmark_schema_id": BENCHMARK_SCHEMA_ID,
        "observer_schema_id": OBSERVER_SCHEMA_ID,
        "lane": lane,
        "scope": scope,
        "torch2pc_commit": torch2pc_commit,
        "execution_environment": execution_environment,
        "model_seeds": model_seeds,
        "batches_per_seed": args.max_batches,
        "timing_repeats": args.timing_repeats,
        "warmup_pairs_per_lane_arm": args.warmup_pairs,
        "arm_summaries": {
            arm.value: timing_summaries[arm].to_dict() for arm in ObserverArm
        },
        "budget_enforced": budget_enforced,
        "budget_passed": runtime_budget_passed,
    }
    memory_summary = {
        "benchmark_schema_id": BENCHMARK_SCHEMA_ID,
        "observer_schema_id": OBSERVER_SCHEMA_ID,
        "lane": lane,
        "scope": scope,
        "torch2pc_commit": torch2pc_commit,
        "execution_environment": execution_environment,
        "model_seeds": model_seeds,
        "batches_per_seed": args.max_batches,
        "memory_pairs_per_seed_batch_arm": 1,
        "rss_sampler_interval_ms": args.rss_sampler_interval_ms,
        "arm_summaries": {
            arm.value: memory_summaries[arm].to_dict() for arm in ObserverArm
        },
        "budget_enforced": budget_enforced,
        "budget_passed": memory_budget_passed,
    }
    measured_timing_pairs = sum(
        item.phase is TimingPhase.MEASURED for item in timing_records
    )
    warmup_timing_pairs = sum(
        item.phase is TimingPhase.WARMUP for item in timing_records
    )
    summary = {
        "control_id": "OBS-OH0",
        "benchmark_schema_id": BENCHMARK_SCHEMA_ID,
        "observer_schema_id": OBSERVER_SCHEMA_ID,
        "scope": scope,
        "device": args.device,
        "dtype": str(dtype),
        "torch2pc_commit": torch2pc_commit,
        "execution_environment": execution_environment,
        "correctness_guard_thresholds": {
            "min_cosine": thresholds.min_cosine,
            "max_relative_l2": thresholds.max_relative_l2,
            "zero_atol": thresholds.zero_atol,
        },
        "model_architecture": "lenet_classic",
        "batch_size": int(warmup_inputs.shape[0]),
        "model_seeds": model_seeds,
        "batches_per_seed": args.max_batches,
        "timing_repeats": args.timing_repeats,
        "warmup_pairs_per_lane_arm": args.warmup_pairs,
        "rss_sampler_interval_ms": args.rss_sampler_interval_ms,
        "guards": {
            "runs": len(guard_records),
            "passed": all(bool(record["passed"]) for record in guard_records),
        },
        "timing": timing_summary,
        "memory": memory_summary,
        "aggregate": {
            "warmup_timing_pairs": warmup_timing_pairs,
            "measured_timing_pairs": measured_timing_pairs,
            "timed_executions": measured_timing_pairs * 2,
            "memory_pairs": len(memory_records),
            "memory_workers": len(memory_records) * 2,
        },
        "structural_passed": structural_passed,
        "budget_enforced": budget_enforced,
        "passed": passed,
        "claim_boundary": (
            "This gate measures bounded runtime and retained-memory overhead for "
            "the sealed passive observer in the registered one-step FixedPred and "
            "joint-VJP paths. It does not establish zero overhead, full-training "
            "overhead, stateful-optimizer overhead, mechanistic validity, or "
            "universality outside the registered environment."
        ),
    }

    guard_frame.to_csv(output_dir / "obs_oh0_guard_records.csv", index=False)
    timing_frame.to_csv(output_dir / "obs_oh0_timing_records.csv", index=False)
    memory_frame.to_csv(output_dir / "obs_oh0_memory_records.csv", index=False)
    (output_dir / "obs_oh0_timing_summary.json").write_text(
        json.dumps(timing_summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "obs_oh0_memory_summary.json").write_text(
        json.dumps(memory_summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "obs_oh0_benchmark_schema.json").write_text(
        json.dumps(schema, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "obs_oh0_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
