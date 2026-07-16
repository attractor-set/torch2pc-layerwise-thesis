#!/usr/bin/env python3
"""Run one controlled SI-MA1 model-seed attempt."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import math
import os
import subprocess
import time
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

import torch
from torch import Tensor, nn

from torch2pc_thesis.data import build_dataloaders
from torch2pc_thesis.models import build_model
from torch2pc_thesis.pc_methods import load_pc_infer
from torch2pc_thesis.reproducibility import configure_threads, set_global_seed
from torch2pc_thesis.stage3b_si_ma0 import (
    ModeRunResult,
    ObserverMode,
    SIMA0Recorder,
    canonical_json_digest,
    run_observer_mode,
    tensor_digest,
)
from torch2pc_thesis.stage3b_si_ma1 import (
    CONTRACT_ID,
    IMPLEMENTATION_SCHEMA_ID,
    PREREGISTRATION_COMMIT,
    TORCH2PC_COMMIT,
    ArmLabel,
    DeferredArmTimer,
    SIMA1Error,
    aggregate_numerical_comparisons,
    balanced_orders,
    build_order_seed_values,
    build_seed_summary,
    compare_topologies,
    compute_block_estimand,
    expected_attempt_counts,
    finalize_recorders_after_block_sync,
    load_contract,
    thresholds_for_si_ma1,
    topology_from_recorders,
    validate_attempt_counts,
    validate_balanced_orders,
)

ExecutionScope = Literal["smoke", "confirmatory"]
Lane = Literal["cpu", "rocm"]

OUTPUT_NAMES = (
    "si_ma1_contract.json",
    "si_ma1_attempts.jsonl",
    "si_ma1_environment.json",
    "si_ma1_arm_timing_records.csv",
    "si_ma1_region_timing_records.csv",
    "si_ma1_numerical_comparisons.csv",
    "si_ma1_topology_comparisons.csv",
    "si_ma1_block_summaries.csv",
    "si_ma1_seed_summaries.csv",
    "si_ma1_order_seed_values.csv",
    "si_ma1_summary.json",
    "si_ma1_decision.json",
    "SHA256SUMS",
)


@dataclass(frozen=True)
class ArmBlockResult:
    arm: ArmLabel
    order: str
    position: int
    device_times_ms: tuple[float, ...]
    wall_times_ms: tuple[float, ...]
    numerical_results: tuple[ModeRunResult, ...]
    recorders: tuple[SIMA0Recorder, ...]
    published_region_records: tuple[dict[str, Any], ...]
    block_synchronization_count: int

    @property
    def device_total_ms(self) -> float:
        return float(sum(self.device_times_ms))

    @property
    def wall_total_ms(self) -> float:
        return float(sum(self.wall_times_ms))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("device", choices=["cpu", "gpu"])
    parser.add_argument(
        "--execution-scope",
        choices=["smoke", "confirmatory"],
        default="smoke",
    )
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--model-seed", type=int, required=True)
    parser.add_argument("--max-batches", type=int, default=1)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--attempt-id")
    parser.add_argument("--replacement-of")
    parser.add_argument(
        "--replacement-reason",
        choices=["infrastructure_failure"],
    )
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path("experiments/planned/STAGE3B-SI-MA1-CONTRACT.json"),
    )
    return parser.parse_args()


def require_environment(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SIMA1Error(f"missing controlled provenance variable: {name}")
    return value


def require_commit_environment(name: str) -> str:
    value = require_environment(name)
    if len(value) != 40 or any(char not in "0123456789abcdef" for char in value):
        raise SIMA1Error(f"{name} must be a lowercase 40-character commit")
    return value


def git_output(path: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", *args],
        cwd=path,
        text=True,
        stderr=subprocess.STDOUT,
    ).strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_indices_digest(indices: list[int]) -> str:
    payload = ",".join(str(value) for value in indices).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def normalize_csv_value(value: Any) -> Any:
    if isinstance(value, dict | list | tuple):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return value


def write_records(path: Path, records: Sequence[Mapping[str, Any]]) -> None:
    fieldnames: list[str] = []
    seen: set[str] = set()
    for record in records:
        for key in record:
            if key not in seen:
                fieldnames.append(key)
                seen.add(key)
    if not fieldnames:
        fieldnames = ["empty"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            lineterminator="\n",
        )
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    key: normalize_csv_value(record.get(key))
                    for key in fieldnames
                }
            )


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def write_sha256_manifest(output_dir: Path) -> None:
    lines = [
        f"{sha256_file(path)}  {path.name}"
        for path in sorted(output_dir.iterdir(), key=lambda item: item.name)
        if path.is_file() and path.name != "SHA256SUMS"
    ]
    (output_dir / "SHA256SUMS").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def verify_sha256_manifest(root: Path) -> dict[str, Any]:
    manifest = root / "SHA256SUMS"
    if not manifest.is_file():
        raise SIMA1Error(f"missing SHA256SUMS: {root}")
    count = 0
    for raw_line in manifest.read_text(encoding="utf-8").splitlines():
        expected, separator, name = raw_line.partition("  ")
        if separator != "  " or len(expected) != 64:
            raise SIMA1Error("invalid SHA256SUMS line")
        path = root / name
        if not path.is_file() or sha256_file(path) != expected:
            raise SIMA1Error(f"checksum mismatch: {path}")
        count += 1
    return {
        "manifest_sha256": sha256_file(manifest),
        "verified_file_count": count,
    }


def verify_si_ma0_prerequisites(repo: Path) -> dict[str, Any]:
    root = repo / "results/stage-3/si-ma0/confirmatory"
    decision_path = root / "si_ma0_decision.json"
    summary_path = root / "si_ma0_summary.json"
    if not decision_path.is_file() or not summary_path.is_file():
        raise SIMA1Error("sealed SI-MA0 evidence is missing")
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    expected_gates = {
        "prerequisites_verified": True,
        "REC-MA0": True,
        "OBS-MA0": True,
        "VER-MA0": True,
        "COST-MA0": False,
        "CMP-MA0": True,
    }
    if decision.get("gates") != expected_gates or summary.get("gates") != expected_gates:
        raise SIMA1Error("SI-MA0 gate prerequisites differ from sealed evidence")
    if decision.get("si_ma0_passed") is not False:
        raise SIMA1Error("historical SI-MA0 failure was not retained")
    manifest = verify_sha256_manifest(root)
    return {
        "si_ma0_decision_sha256": sha256_file(decision_path),
        "si_ma0_summary_sha256": sha256_file(summary_path),
        **manifest,
    }


def load_checkpoint(path: Path) -> tuple[dict[str, Any], dict[str, Tensor]]:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    if not isinstance(payload, dict):
        raise SIMA1Error("checkpoint must contain a dictionary")
    config = payload.get("config")
    state_dict = payload.get("state_dict")
    if not isinstance(config, dict) or not isinstance(state_dict, dict):
        raise SIMA1Error("checkpoint must contain config and state_dict")
    if not all(isinstance(value, Tensor) for value in state_dict.values()):
        raise SIMA1Error("checkpoint state_dict contains non-tensor values")
    return cast(dict[str, Any], config), cast(dict[str, Tensor], state_dict)


def validate_checkpoint_scope(
    config: Mapping[str, Any],
    *,
    model_seed: int,
    contract: Mapping[str, Any],
) -> None:
    reproducibility = config.get("reproducibility")
    data_cfg = config.get("data")
    model_cfg = config.get("model")
    method_cfg = config.get("method")
    if not all(
        isinstance(value, Mapping)
        for value in (reproducibility, data_cfg, model_cfg, method_cfg)
    ):
        raise SIMA1Error("checkpoint configuration is incomplete")
    assert isinstance(reproducibility, Mapping)
    assert isinstance(data_cfg, Mapping)
    assert isinstance(model_cfg, Mapping)
    assert isinstance(method_cfg, Mapping)
    scope = cast(Mapping[str, Any], contract["scope"])
    if int(reproducibility["model_seed"]) != model_seed:
        raise SIMA1Error("checkpoint seed differs from --model-seed")
    if str(data_cfg["dataset"]).lower() != "fashionmnist":
        raise SIMA1Error("SI-MA1 requires FashionMNIST")
    if str(model_cfg["architecture"]) != scope["architecture"]:
        raise SIMA1Error("checkpoint architecture differs from contract")
    if str(method_cfg.get("name", "")).lower() != "strict":
        raise SIMA1Error("SI-MA1 requires Strict")
    if float(method_cfg.get("eta", math.nan)) != float(scope["eta"]):
        raise SIMA1Error("checkpoint eta differs from contract")
    if int(method_cfg.get("inference_steps", -1)) != int(scope["inference_steps"]):
        raise SIMA1Error("checkpoint inference steps differ from contract")


def prepare_runtime(
    device_name: str,
    *,
    configured_threads: int,
) -> tuple[torch.device, torch.dtype, Lane, int]:
    if os.environ.get("TORCH2PC_CONTROLLED_CONTAINER") != "1":
        raise SIMA1Error("SI-MA1 requires a controlled container")
    raw_lane = require_environment("TORCH2PC_EXECUTION_LANE")
    if raw_lane not in {"cpu", "rocm"}:
        raise SIMA1Error("execution lane must be cpu or rocm")
    lane = cast(Lane, raw_lane)
    if device_name == "cpu":
        if lane != "cpu":
            raise SIMA1Error("CPU execution requires the cpu lane")
        device = torch.device("cpu")
        thread_count = 1
    else:
        if lane != "rocm":
            raise SIMA1Error("GPU execution requires the rocm lane")
        if not torch.cuda.is_available() or getattr(torch.version, "hip", None) is None:
            raise SIMA1Error("ROCm device is unavailable")
        device = torch.device("cuda")
        thread_count = configured_threads
    configure_threads(thread_count)
    torch.use_deterministic_algorithms(True)
    return device, torch.float32, lane, thread_count


def build_probe_model(
    config: Mapping[str, Any],
    state_dict: Mapping[str, Tensor],
    *,
    device: torch.device,
    dtype: torch.dtype,
) -> nn.Module:
    model_cfg = config.get("model")
    if not isinstance(model_cfg, Mapping):
        raise SIMA1Error("checkpoint model configuration is missing")
    model = build_model(
        str(model_cfg["architecture"]),
        int(model_cfg["num_classes"]),
    )
    if len(model) != 6:
        raise SIMA1Error(f"SI-MA1 requires six model modules, observed {len(model)}")
    model.load_state_dict(state_dict, strict=True)
    model.to(device=device, dtype=dtype)
    model.eval()
    return model


def materialize_validation_batches(
    config: Mapping[str, Any],
    *,
    count: int,
) -> list[tuple[Tensor, Tensor, list[int]]]:
    probe_config = copy.deepcopy(dict(config))
    probe_config.setdefault("evaluation", {})["use_test"] = False
    probe_config.setdefault("runtime", {})["loader_workers"] = 0
    bundle = build_dataloaders(
        probe_config,
        include_test=False,
        download=False,
    )
    batches: list[tuple[Tensor, Tensor, list[int]]] = []
    cursor = 0
    for batch_index, (inputs, targets) in enumerate(bundle.validation):
        if batch_index >= count:
            break
        batch_size = int(inputs.shape[0])
        indices = [
            int(value)
            for value in bundle.validation_indices[cursor : cursor + batch_size]
        ]
        cursor += batch_size
        batches.append(
            (
                inputs.detach().cpu().clone(),
                targets.detach().cpu().clone(),
                indices,
            )
        )
    if len(batches) != count:
        raise SIMA1Error(f"requested {count} batches, observed {len(batches)}")
    return batches


def capture_rng_state(device: torch.device) -> tuple[Tensor, Tensor | None]:
    cpu_state = torch.get_rng_state().clone()
    cuda_state = torch.cuda.get_rng_state(device).clone() if device.type == "cuda" else None
    return cpu_state, cuda_state


def restore_rng_state(
    device: torch.device,
    state: tuple[Tensor, Tensor | None],
) -> None:
    torch.set_rng_state(state[0])
    if device.type == "cuda":
        if state[1] is None:
            raise SIMA1Error("CUDA RNG snapshot is missing")
        torch.cuda.set_rng_state(state[1], device)


def warmup_arm(
    *,
    arm: ArmLabel,
    steps: int,
    pc_infer: Callable[..., Any],
    config: Mapping[str, Any],
    state_dict: Mapping[str, Tensor],
    inputs: Tensor,
    targets: Tensor,
    device: torch.device,
    dtype: torch.dtype,
    thresholds: Any,
    rng_state: tuple[Tensor, Tensor | None],
    eta: float,
    inference_steps: int,
    metadata: Mapping[str, Any],
) -> None:
    mode: ObserverMode = "no_hooks" if arm == "A" else "counters_only"
    model = build_probe_model(config, state_dict, device=device, dtype=dtype)
    for step_index in range(steps):
        restore_rng_state(device, rng_state)
        run_observer_mode(
            pc_infer=pc_infer,
            model=model,
            loss_function=nn.CrossEntropyLoss(),
            inputs=inputs,
            targets=targets,
            eta=eta,
            inference_steps=inference_steps,
            mode=mode,
            thresholds=thresholds,
            metadata={**metadata, "warmup_step_index": step_index},
            aggregate_regions=True,
            capture_external_timing=False,
        )
    if device.type == "cuda":
        torch.cuda.synchronize(device)


def run_arm_block(
    *,
    arm: ArmLabel,
    order: str,
    position: int,
    block_index: int,
    measured_steps: int,
    pc_infer: Callable[..., Any],
    config: Mapping[str, Any],
    state_dict: Mapping[str, Tensor],
    inputs: Tensor,
    targets: Tensor,
    device: torch.device,
    dtype: torch.dtype,
    thresholds: Any,
    rng_state: tuple[Tensor, Tensor | None],
    eta: float,
    inference_steps: int,
    recorder_metadata: Mapping[str, Any],
) -> ArmBlockResult:
    mode: ObserverMode = "no_hooks" if arm == "A" else "counters_only"
    model = build_probe_model(config, state_dict, device=device, dtype=dtype)
    timer = DeferredArmTimer(device)
    results: list[ModeRunResult] = []
    recorders: list[SIMA0Recorder] = []
    wall_times: list[float] = []

    for step_index in range(measured_steps):
        restore_rng_state(device, rng_state)
        step_metadata = {
            **recorder_metadata,
            "order": order,
            "block_index": block_index,
            "measured_step_index": step_index,
        }
        wall_start = time.perf_counter_ns()
        with timer.step():
            result = run_observer_mode(
                pc_infer=pc_infer,
                model=model,
                loss_function=nn.CrossEntropyLoss(),
                inputs=inputs,
                targets=targets,
                eta=eta,
                inference_steps=inference_steps,
                mode=mode,
                thresholds=thresholds,
                metadata=step_metadata,
                aggregate_regions=True,
                defer_timing_resolution=arm != "A",
                capture_external_timing=False,
            )
        wall_times.append((time.perf_counter_ns() - wall_start) / 1_000_000.0)
        results.append(result)
        if arm != "A":
            if result.recorder is None:
                raise SIMA1Error(f"SI-MA1 arm {arm} did not create a recorder")
            recorders.append(result.recorder)

    device_times = timer.finalize()
    if arm != "A":
        finalize_recorders_after_block_sync(
            recorders,
            block_synchronization_count=timer.synchronization_count,
        )
    published: list[dict[str, Any]] = []
    if arm == "C":
        for recorder in recorders:
            for record in recorder.region_records:
                published.append({**record, "arm": arm, "arm_position": position})
    return ArmBlockResult(
        arm=arm,
        order=order,
        position=position,
        device_times_ms=tuple(device_times),
        wall_times_ms=tuple(wall_times),
        numerical_results=tuple(results),
        recorders=tuple(recorders),
        published_region_records=tuple(published),
        block_synchronization_count=timer.synchronization_count,
    )


def main() -> None:
    args = parse_args()
    if args.max_batches < 1:
        raise ValueError("--max-batches must be positive")
    if (args.replacement_of is None) != (args.replacement_reason is None):
        raise SIMA1Error("replacement fields must be provided together")

    repo = Path(__file__).resolve().parents[1]
    source_commit = require_commit_environment("SOURCE_GIT_COMMIT")
    source_branch = require_environment("SOURCE_GIT_BRANCH")
    experiment_image = require_environment("EXPERIMENT_IMAGE")
    image_revision = require_commit_environment("IMAGE_REVISION")
    prereg_commit = require_commit_environment("SI_MA1_PREREG_COMMIT")
    if source_commit != image_revision:
        raise SIMA1Error("controlled image revision differs from source")
    if prereg_commit != PREREGISTRATION_COMMIT:
        raise SIMA1Error("SI-MA1 preregistration commit differs")

    contract_path = repo / args.contract
    contract = load_contract(contract_path)
    prerequisites = verify_si_ma0_prerequisites(repo)
    checkpoint_path = repo / args.checkpoint
    if not checkpoint_path.is_file():
        raise SIMA1Error(f"checkpoint is missing: {args.checkpoint}")
    config, state_dict = load_checkpoint(checkpoint_path)
    validate_checkpoint_scope(config, model_seed=args.model_seed, contract=contract)
    runtime = config.get("runtime")
    if not isinstance(runtime, Mapping):
        raise SIMA1Error("checkpoint runtime configuration is missing")
    device, dtype, lane, thread_count = prepare_runtime(
        args.device,
        configured_threads=int(runtime.get("torch_threads", 4)),
    )
    scope_name = cast(ExecutionScope, args.execution_scope)
    if scope_name == "confirmatory":
        confirmatory = cast(Mapping[str, Any], contract["execution_scopes"])[
            "confirmatory"
        ]
        if lane != "rocm" or args.model_seed not in confirmatory["model_seeds"]:
            raise SIMA1Error("attempt is outside confirmatory scope")
        if args.max_batches != len(confirmatory["validation_batch_ids"]):
            raise SIMA1Error("confirmatory SI-MA1 requires all three batches")

    set_global_seed(args.model_seed, deterministic=True, warn_only=False)
    torch2pc_path = repo / str(config["torch2pc"]["local_path"])
    if git_output(torch2pc_path, "rev-parse", "HEAD") != TORCH2PC_COMMIT:
        raise SIMA1Error("Torch2PC checkout differs from frozen commit")
    if git_output(torch2pc_path, "status", "--porcelain"):
        raise SIMA1Error("Torch2PC worktree is dirty")
    pc_infer = load_pc_infer(torch2pc_path)

    batches = materialize_validation_batches(config, count=args.max_batches)
    checkpoint_sha256 = sha256_file(checkpoint_path)
    config_sha256 = canonical_json_digest(config)
    timing = cast(Mapping[str, Any], contract["timing_protocol"])
    warmup_steps = int(timing["warmup_steps_per_arm_before_measured_blocks"])
    measured_steps = int(timing["measured_steps_per_arm_block"])
    epsilon = float(timing["epsilon"])
    scope = cast(Mapping[str, Any], contract["scope"])
    eta = float(scope["eta"])
    inference_steps = int(scope["inference_steps"])
    thresholds = thresholds_for_si_ma1(contract)

    attempt_id = args.attempt_id or (
        f"si-ma1-{scope_name}-seed-{args.model_seed}-{uuid.uuid4().hex}"
    )
    output_dir = repo / args.output_dir
    if output_dir.exists() and any(output_dir.iterdir()):
        raise SIMA1Error("SI-MA1 output directory must be new and empty")
    output_dir.mkdir(parents=True, exist_ok=True)

    arm_timing_records: list[dict[str, Any]] = []
    region_timing_records: list[dict[str, Any]] = []
    numerical_records: list[dict[str, Any]] = []
    topology_records: list[dict[str, Any]] = []
    block_summaries: list[dict[str, Any]] = []
    observed_orders: dict[int, tuple[str, ...]] = {}

    for batch_id, (cpu_inputs, cpu_targets, indices) in enumerate(batches):
        if int(cpu_inputs.shape[0]) != int(scope["batch_size"]):
            raise SIMA1Error("validation batch size differs from contract")
        inputs = cpu_inputs.to(device=device, dtype=dtype)
        targets = cpu_targets.to(device=device)
        common_metadata = {
            "contract_id": CONTRACT_ID,
            "implementation_schema_id": IMPLEMENTATION_SCHEMA_ID,
            "source_git_commit": source_commit,
            "source_git_branch": source_branch,
            "experiment_image": experiment_image,
            "image_revision": image_revision,
            "si_ma1_prereg_commit": prereg_commit,
            "torch2pc_commit": TORCH2PC_COMMIT,
            "checkpoint_sha256": checkpoint_sha256,
            "config_sha256": config_sha256,
            "split_manifest_sha256": source_indices_digest(indices),
            "input_sha256": tensor_digest(cpu_inputs),
            "target_sha256": tensor_digest(cpu_targets),
            "model_seed": args.model_seed,
            "batch_id": batch_id,
            "execution_scope": scope_name,
            "lane": lane,
            "attempt_id": attempt_id,
        }
        rng_state = capture_rng_state(device)
        for arm in cast(tuple[ArmLabel, ...], ("A", "B", "C")):
            warmup_arm(
                arm=arm,
                steps=warmup_steps,
                pc_infer=pc_infer,
                config=config,
                state_dict=state_dict,
                inputs=inputs,
                targets=targets,
                device=device,
                dtype=dtype,
                thresholds=thresholds,
                rng_state=rng_state,
                eta=eta,
                inference_steps=inference_steps,
                metadata=common_metadata,
            )

        orders = balanced_orders(args.model_seed, batch_id)
        observed_orders[batch_id] = orders
        if not validate_balanced_orders(
            orders,
            model_seed=args.model_seed,
            batch_id=batch_id,
        ):
            raise SIMA1Error("registered balanced order validation failed")

        for block_index, order in enumerate(orders):
            results: dict[ArmLabel, ArmBlockResult] = {}
            for position, raw_arm in enumerate(order):
                arm = cast(ArmLabel, raw_arm)
                results[arm] = run_arm_block(
                    arm=arm,
                    order=order,
                    position=position,
                    block_index=block_index,
                    measured_steps=measured_steps,
                    pc_infer=pc_infer,
                    config=config,
                    state_dict=state_dict,
                    inputs=inputs,
                    targets=targets,
                    device=device,
                    dtype=dtype,
                    thresholds=thresholds,
                    rng_state=rng_state,
                    eta=eta,
                    inference_steps=inference_steps,
                    recorder_metadata=common_metadata,
                )
                for step_index, (device_ms, wall_ms) in enumerate(
                    zip(
                        results[arm].device_times_ms,
                        results[arm].wall_times_ms,
                        strict=True,
                    )
                ):
                    arm_timing_records.append(
                        {
                            **common_metadata,
                            "order": order,
                            "block_index": block_index,
                            "arm": arm,
                            "arm_position": position,
                            "measured_step_index": step_index,
                            "device_time_ms": device_ms,
                            "wall_time_ms": wall_ms,
                            "finite": math.isfinite(device_ms) and math.isfinite(wall_ms),
                            "nonnegative": device_ms >= 0.0 and wall_ms >= 0.0,
                            "block_synchronization_count": results[arm].block_synchronization_count,
                        }
                    )
                region_timing_records.extend(results[arm].published_region_records)

            comparison_metadata = {
                **common_metadata,
                "order": order,
                "block_index": block_index,
            }
            numerical_records.append(
                aggregate_numerical_comparisons(
                    results["A"].numerical_results,
                    results["B"].numerical_results,
                    thresholds,
                    candidate_arm="B",
                    metadata=comparison_metadata,
                )
            )
            numerical_records.append(
                aggregate_numerical_comparisons(
                    results["A"].numerical_results,
                    results["C"].numerical_results,
                    thresholds,
                    candidate_arm="C",
                    metadata=comparison_metadata,
                )
            )
            b_topology = topology_from_recorders(
                results["B"].recorders,
                outer_step_event_pair_count=measured_steps,
                block_synchronization_count=results["B"].block_synchronization_count,
            )
            c_topology = topology_from_recorders(
                results["C"].recorders,
                outer_step_event_pair_count=measured_steps,
                block_synchronization_count=results["C"].block_synchronization_count,
            )
            topology_records.append(
                compare_topologies(
                    b_topology,
                    c_topology,
                    metadata=comparison_metadata,
                )
            )
            live_region_time_ms = sum(
                float(record["duration_ms"])
                for record in results["C"].published_region_records
            )
            estimand = compute_block_estimand(
                baseline_time_ms=results["A"].device_total_ms,
                calibration_time_ms=results["B"].device_total_ms,
                live_time_ms=results["C"].device_total_ms,
                live_region_time_ms=live_region_time_ms,
                epsilon=epsilon,
            )
            block_summaries.append(
                {
                    **comparison_metadata,
                    **estimand.to_record(),
                    "baseline_wall_time_ms": results["A"].wall_total_ms,
                    "calibration_wall_time_ms": results["B"].wall_total_ms,
                    "live_wall_time_ms": results["C"].wall_total_ms,
                }
            )

    seed_summary = build_seed_summary(
        block_summaries,
        model_seed=args.model_seed,
        expected_block_count=args.max_batches * 6,
    )
    order_seed_values = build_order_seed_values(
        block_summaries,
        model_seed=args.model_seed,
        expected_batch_count=args.max_batches,
    )
    observed_counts = {
        "model_seed_batch_pairs": args.max_batches,
        "matched_blocks": len(block_summaries),
        "arm_blocks": len(block_summaries) * 3,
        "arm_timing_records": len(arm_timing_records),
        "live_region_timing_records": len(region_timing_records),
        "numerical_comparison_rows": len(numerical_records),
        "topology_comparison_rows": len(topology_records),
        "block_summary_rows": len(block_summaries),
        "seed_summary_rows": 1,
        "order_seed_value_rows": len(order_seed_values),
    }
    validate_attempt_counts(
        observed_counts,
        batch_count=args.max_batches,
        measured_steps_per_arm_block=measured_steps,
    )
    expected_counts = expected_attempt_counts(
        batch_count=args.max_batches,
        measured_steps_per_arm_block=measured_steps,
    )
    num_passed = all(bool(row["passed"]) for row in numerical_records)
    topo_passed = all(bool(row["passed"]) for row in topology_records)
    bal_passed = all(
        validate_balanced_orders(
            orders,
            model_seed=args.model_seed,
            batch_id=batch_id,
        )
        for batch_id, orders in observed_orders.items()
    )
    cmp_passed = observed_counts == expected_counts

    environment = {
        "contract_id": CONTRACT_ID,
        "implementation_schema_id": IMPLEMENTATION_SCHEMA_ID,
        "source_git_commit": source_commit,
        "source_git_branch": source_branch,
        "experiment_image": experiment_image,
        "image_revision": image_revision,
        "si_ma1_prereg_commit": prereg_commit,
        "torch_version": torch.__version__,
        "torch_hip_version": getattr(torch.version, "hip", None),
        "torch2pc_commit": TORCH2PC_COMMIT,
        "lane": lane,
        "dtype": str(dtype),
        "thread_count": thread_count,
        "checkpoint_sha256": checkpoint_sha256,
        "config_sha256": config_sha256,
        "test_split_accessed": False,
        "ecz_evaluator_executed": False,
        "prerequisites": prerequisites,
    }
    gates = {
        "prerequisites_verified": True,
        "NUM-MA1-cell": num_passed,
        "TOPO-MA1-cell": topo_passed,
        "BAL-MA1-cell": bal_passed,
        "CMP-MA1-cell": cmp_passed,
        "CAL-COST-MA1": None,
    }
    summary = {
        **environment,
        "scope": scope_name,
        "attempt_id": attempt_id,
        "model_seed": args.model_seed,
        "batch_count": args.max_batches,
        "expected_counts": expected_counts,
        "observed_counts": observed_counts,
        "seed_summary": seed_summary,
        "gates": gates,
        "confirmatory_decision_made": False,
        "si_ma1_passed": None,
        "decision_state": None,
    }
    attempt_record = {
        "attempt_id": attempt_id,
        "contract_id": CONTRACT_ID,
        "implementation_schema_id": IMPLEMENTATION_SCHEMA_ID,
        "scope": scope_name,
        "lane": lane,
        "model_seed": args.model_seed,
        "status": "completed",
        "cell_valid": num_passed and topo_passed and bal_passed and cmp_passed,
        "replacement_of": args.replacement_of,
        "replacement_reason": args.replacement_reason,
        "source_git_commit": source_commit,
        "image_revision": image_revision,
        "checkpoint_sha256": checkpoint_sha256,
    }
    decision = {
        "contract_id": CONTRACT_ID,
        "implementation_schema_id": IMPLEMENTATION_SCHEMA_ID,
        "decision_scope": "model_seed_attempt",
        "attempt_id": attempt_id,
        "model_seed": args.model_seed,
        "attempt_complete": True,
        "attempt_valid": attempt_record["cell_valid"],
        "CAL-COST-MA1": None,
        "confirmatory_decision_made": False,
        "si_ma1_passed": None,
        "decision_state": None,
        "cohort_aggregation_required": True,
        "historical_si_ma0_result_retained": True,
        "ecz_evaluator_cost_included": False,
    }

    (output_dir / "si_ma1_contract.json").write_bytes(contract_path.read_bytes())
    (output_dir / "si_ma1_attempts.jsonl").write_text(
        json.dumps(attempt_record, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    write_json(output_dir / "si_ma1_environment.json", environment)
    write_records(output_dir / "si_ma1_arm_timing_records.csv", arm_timing_records)
    write_records(output_dir / "si_ma1_region_timing_records.csv", region_timing_records)
    write_records(output_dir / "si_ma1_numerical_comparisons.csv", numerical_records)
    write_records(output_dir / "si_ma1_topology_comparisons.csv", topology_records)
    write_records(output_dir / "si_ma1_block_summaries.csv", block_summaries)
    write_records(output_dir / "si_ma1_seed_summaries.csv", [seed_summary])
    write_records(output_dir / "si_ma1_order_seed_values.csv", order_seed_values)
    write_json(output_dir / "si_ma1_summary.json", summary)
    write_json(output_dir / "si_ma1_decision.json", decision)
    write_sha256_manifest(output_dir)

    missing = [name for name in OUTPUT_NAMES if not (output_dir / name).is_file()]
    if missing:
        raise SIMA1Error(f"SI-MA1 output files are missing: {missing}")
    verify_sha256_manifest(output_dir)
    print(
        f"OK: SI-MA1 {scope_name} attempt completed "
        f"seed={args.model_seed} d_seed={seed_summary['d_seed']:.9f}"
    )


if __name__ == "__main__":
    main()
