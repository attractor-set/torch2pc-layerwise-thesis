#!/usr/bin/env python3
"""Run one controlled SI-MA0 model-level implementation cell."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import math
import os
import subprocess
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal, cast

import torch
from torch import Tensor, nn

from torch2pc_thesis.data import build_dataloaders
from torch2pc_thesis.models import build_model
from torch2pc_thesis.pc_methods import load_pc_infer
from torch2pc_thesis.reproducibility import configure_threads, set_global_seed
from torch2pc_thesis.stage3b_si_ma0 import (
    CONTRACT_ID,
    IMPLEMENTATION_SCHEMA_ID,
    OBSERVER_MODES,
    TORCH2PC_COMMIT,
    ModeRunResult,
    NumericalThresholds,
    ObserverMode,
    SIMA0Error,
    canonical_json_digest,
    compare_mode_results,
    expected_record_counts,
    load_contract,
    materialize_output_error_records,
    materialize_state_update_records,
    run_observer_mode,
    tensor_digest,
    thresholds_for,
    validate_event_order,
)

OUTPUT_NAMES = (
    "si_ma0_contract.json",
    "si_ma0_attempts.jsonl",
    "si_ma0_environment.json",
    "si_ma0_event_records.csv",
    "si_ma0_output_error_records.csv",
    "si_ma0_mode_comparisons.csv",
    "si_ma0_total_timing_records.csv",
    "si_ma0_region_timing_records.csv",
    "si_ma0_vjp_records.csv",
    "si_ma0_saved_tensor_records.csv",
    "si_ma0_graph_lifetime_records.csv",
    "si_ma0_batch_summaries.csv",
    "si_ma0_model_region_summaries.csv",
    "si_ma0_summary.json",
    "si_ma0_decision.json",
    "SHA256SUMS",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("device", choices=["cpu", "gpu"])
    parser.add_argument(
        "--execution-scope",
        choices=["smoke"],
        default="smoke",
    )
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--model-seed", type=int, required=True)
    parser.add_argument("--max-batches", type=int, default=1)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path(
            "experiments/planned/STAGE3B-SI-MA0-CONTRACT.json"
        ),
    )
    return parser.parse_args()


def require_environment(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SIMA0Error(f"missing controlled provenance variable: {name}")
    return value


def git_output(path: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(path), *args],
        text=True,
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


def write_records(path: Path, records: list[dict[str, Any]]) -> None:
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
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    key: normalize_csv_value(record.get(key))
                    for key in fieldnames
                }
            )


def load_checkpoint(path: Path) -> tuple[dict[str, Any], dict[str, Tensor]]:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    if not isinstance(payload, dict):
        raise SIMA0Error("checkpoint must contain a dictionary")
    config = payload.get("config")
    state_dict = payload.get("state_dict")
    if not isinstance(config, dict) or not isinstance(state_dict, dict):
        raise SIMA0Error("checkpoint must contain config and state_dict")
    if not all(isinstance(value, Tensor) for value in state_dict.values()):
        raise SIMA0Error("checkpoint state_dict contains non-tensor values")
    return (
        cast(dict[str, Any], config),
        cast(dict[str, Tensor], state_dict),
    )


def verify_prerequisites(repo: Path) -> dict[str, Any]:
    evidence_root = (
        repo
        / "results/stage-3/a1-mechanism-controls/confirmatory"
    )
    decision_path = evidence_root / "mechanism-controls-decision.json"
    checksum_path = evidence_root / "SHA256SUMS"
    if not decision_path.is_file() or not checksum_path.is_file():
        raise SIMA0Error("sealed A1 mechanism-control evidence is missing")
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    if not isinstance(decision, dict):
        raise SIMA0Error("A1 decision must be a JSON object")
    decision_fields = decision.get("decision")
    if not isinstance(decision_fields, dict):
        raise SIMA0Error("A1 decision fields are missing")
    for key in (
        "mechanism_controls_confirmatory_passed",
        "core_controls_passed",
        "si_ma0_open",
    ):
        if decision_fields.get(key) is not True:
            raise SIMA0Error(f"A1 prerequisite is not satisfied: {key}")
    subprocess.run(
        ["sha256sum", "-c", "SHA256SUMS"],
        cwd=evidence_root,
        check=True,
        stdout=subprocess.DEVNULL,
    )
    prereg_commit = git_output(
        repo,
        "rev-list",
        "-n",
        "1",
        "stage3b-si-ma0-prereg-v2",
    )
    head = git_output(repo, "rev-parse", "HEAD")
    ancestry = subprocess.run(
        ["git", "-C", str(repo), "merge-base", "--is-ancestor",
         prereg_commit, head],
        check=False,
    )
    if ancestry.returncode != 0:
        raise SIMA0Error("SI-MA0 preregistration v2 is absent from HEAD")
    return {
        "a1_decision_sha256": sha256_file(decision_path),
        "a1_sha256_manifest_sha256": sha256_file(checksum_path),
        "si_ma0_prereg_v2_commit": prereg_commit,
    }


def prepare_runtime(
    device_name: str,
    *,
    configured_threads: int,
) -> tuple[
    torch.device,
    torch.dtype,
    Literal["cpu", "rocm"],
    int,
]:
    controlled = os.environ.get("TORCH2PC_CONTROLLED_CONTAINER") == "1"
    if not controlled:
        raise SIMA0Error("SI-MA0 requires a controlled container")

    raw_lane = require_environment("TORCH2PC_EXECUTION_LANE")
    if raw_lane == "cpu":
        lane: Literal["cpu", "rocm"] = "cpu"
    elif raw_lane == "rocm":
        lane = "rocm"
    else:
        raise SIMA0Error(
            "TORCH2PC_EXECUTION_LANE must be either 'cpu' or 'rocm'"
        )

    if device_name == "cpu":
        if lane != "cpu":
            raise SIMA0Error("CPU execution requires the cpu lane")
        thread_count = 1
        device = torch.device("cpu")
        dtype = torch.float64
    else:
        if lane != "rocm":
            raise SIMA0Error("GPU execution requires the rocm lane")
        if not torch.cuda.is_available():
            raise SIMA0Error("ROCm device is unavailable")
        if getattr(torch.version, "hip", None) is None:
            raise SIMA0Error("PyTorch was not built with ROCm")
        thread_count = configured_threads
        device = torch.device("cuda")
        dtype = torch.float32

    configure_threads(thread_count)
    torch.use_deterministic_algorithms(True)
    return device, dtype, lane, thread_count


def build_probe_model(
    config: dict[str, Any],
    state_dict: dict[str, Tensor],
    *,
    device: torch.device,
    dtype: torch.dtype,
) -> nn.Module:
    model_cfg = config.get("model")
    if not isinstance(model_cfg, dict):
        raise SIMA0Error("checkpoint model configuration is missing")
    model = build_model(
        str(model_cfg["architecture"]),
        int(model_cfg["num_classes"]),
    )
    if len(model) != 6:
        raise SIMA0Error(
            f"SI-MA0 requires six model modules, observed {len(model)}"
        )
    model.load_state_dict(state_dict, strict=True)
    model.to(device=device, dtype=dtype)
    model.eval()
    return model


def materialize_validation_batches(
    config: dict[str, Any],
    *,
    count: int,
) -> list[tuple[Tensor, Tensor, list[int]]]:
    probe_config = copy.deepcopy(config)
    probe_config.setdefault("evaluation", {})["use_test"] = False
    runtime = probe_config.setdefault("runtime", {})
    runtime["loader_workers"] = 0
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
            for value in bundle.validation_indices[
                cursor : cursor + batch_size
            ]
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
        raise SIMA0Error(
            f"requested {count} validation batches, observed {len(batches)}"
        )
    return batches


def capture_rng_state(
    device: torch.device,
) -> tuple[Tensor, Tensor | None]:
    cpu_state = torch.get_rng_state().clone()
    cuda_state = (
        torch.cuda.get_rng_state(device).clone()
        if device.type == "cuda"
        else None
    )
    return cpu_state, cuda_state


def restore_rng_state(
    device: torch.device,
    state: tuple[Tensor, Tensor | None],
) -> None:
    torch.set_rng_state(state[0])
    if device.type == "cuda":
        if state[1] is None:
            raise SIMA0Error("CUDA RNG snapshot is missing")
        torch.cuda.set_rng_state(state[1], device)


def run_modes_for_batch(
    *,
    pc_infer: Callable[..., Any],
    config: dict[str, Any],
    state_dict: dict[str, Tensor],
    inputs: Tensor,
    targets: Tensor,
    device: torch.device,
    dtype: torch.dtype,
    thresholds: NumericalThresholds,
    metadata: dict[str, Any],
    eta: float,
    inference_steps: int,
    updated_state_layers: int,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    loss_function = nn.CrossEntropyLoss()
    initial_rng = capture_rng_state(device)
    results: dict[ObserverMode, ModeRunResult] = {}
    for mode in OBSERVER_MODES:
        restore_rng_state(device, initial_rng)
        model = build_probe_model(
            config,
            state_dict,
            device=device,
            dtype=dtype,
        )
        results[mode] = run_observer_mode(
            pc_infer=pc_infer,
            model=model,
            loss_function=loss_function,
            inputs=inputs,
            targets=targets,
            eta=eta,
            inference_steps=inference_steps,
            mode=mode,
            thresholds=thresholds,
            metadata=metadata,
        )
    reference = results["no_hooks"]
    comparison_records = [
        compare_mode_results(
            reference,
            results[mode],
            thresholds,
            metadata=metadata,
        )
        for mode in OBSERVER_MODES
        if mode != "no_hooks"
    ]
    full = results["full_attribution"].recorder
    if full is None:
        raise SIMA0Error("full_attribution recorder is missing")
    state_records = materialize_state_update_records(full, eta=eta)
    output_records = materialize_output_error_records(full)
    validate_event_order(
        state_records,
        output_records,
        inference_steps=inference_steps,
        updated_state_layers=updated_state_layers,
    )
    region_records: list[dict[str, Any]] = []
    total_records: list[dict[str, Any]] = []
    for mode in OBSERVER_MODES:
        recorder = results[mode].recorder
        if recorder is None:
            continue
        region_records.extend(recorder.region_records)
        total_records.extend(recorder.total_records)
    return (
        comparison_records,
        state_records,
        output_records,
        region_records,
        total_records,
    )


def make_derived_records(
    state_records: list[dict[str, Any]],
    output_records: list[dict[str, Any]],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    combined = state_records + output_records
    vjp = [
        {
            "model_seed": record["model_seed"],
            "batch_id": record["batch_id"],
            "record_type": record["record_type"],
            "sweep_index": record["sweep_index"],
            "layer_index": record.get("layer_index"),
            "vjp_call_count": record.get(
                "vjp_call_count",
                record.get("output_error_vjp_call_count"),
            ),
        }
        for record in combined
    ]
    saved = [
        {
            "model_seed": record["model_seed"],
            "batch_id": record["batch_id"],
            "record_type": record["record_type"],
            "sweep_index": record["sweep_index"],
            "layer_index": record.get("layer_index"),
            "saved_tensor_count": record["saved_tensor_count"],
            "saved_tensor_bytes": record["saved_tensor_bytes"],
        }
        for record in combined
    ]
    graph = [
        {
            "model_seed": record["model_seed"],
            "batch_id": record["batch_id"],
            "record_type": record["record_type"],
            "sweep_index": record["sweep_index"],
            "layer_index": record.get("layer_index"),
            "graph_birth_event": record["graph_birth_event"],
            "graph_release_event": record["graph_release_event"],
            "graph_lifetime_event_units": (
                int(record["graph_release_event"])
                - int(record["graph_birth_event"])
            ),
        }
        for record in combined
    ]
    return vjp, saved, graph


def summarize_regions(
    region_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    totals: dict[tuple[str, str], float] = {}
    for record in region_records:
        key = (str(record["observer_mode"]), str(record["region"]))
        totals[key] = totals.get(key, 0.0) + float(record["duration_ms"])
    return [
        {
            "observer_mode": mode,
            "region": region,
            "duration_ms": duration,
        }
        for (mode, region), duration in sorted(totals.items())
    ]


def write_sha256_manifest(output_dir: Path) -> None:
    lines = []
    for path in sorted(output_dir.iterdir(), key=lambda item: item.name):
        if not path.is_file() or path.name == "SHA256SUMS":
            continue
        lines.append(f"{sha256_file(path)}  {path.name}")
    (output_dir / "SHA256SUMS").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    if args.max_batches < 1:
        raise ValueError("--max-batches must be positive")
    scope = str(args.execution_scope)
    repo = Path(__file__).resolve().parents[1]
    source_commit = require_environment("SOURCE_GIT_COMMIT")
    source_branch = require_environment("SOURCE_GIT_BRANCH")
    experiment_image = require_environment("EXPERIMENT_IMAGE")
    image_revision = require_environment("IMAGE_REVISION")
    if source_commit != image_revision:
        raise SIMA0Error("controlled image revision differs from source")
    if git_output(repo, "rev-parse", "HEAD") != source_commit:
        raise SIMA0Error("container source commit differs from provenance")
    contract_path = repo / args.contract
    contract = load_contract(contract_path)
    prerequisites = verify_prerequisites(repo)
    checkpoint_path = repo / args.checkpoint
    if not checkpoint_path.is_file():
        raise SIMA0Error(f"checkpoint is missing: {args.checkpoint}")
    config, state_dict = load_checkpoint(checkpoint_path)
    reproducibility = config.get("reproducibility")
    runtime = config.get("runtime")
    data_cfg = config.get("data")
    model_cfg = config.get("model")
    method_cfg = config.get("method")
    if not all(
        isinstance(value, dict)
        for value in (
            reproducibility,
            runtime,
            data_cfg,
            model_cfg,
            method_cfg,
        )
    ):
        raise SIMA0Error("checkpoint configuration is incomplete")
    assert isinstance(reproducibility, dict)
    assert isinstance(runtime, dict)
    assert isinstance(data_cfg, dict)
    assert isinstance(model_cfg, dict)
    assert isinstance(method_cfg, dict)
    if int(reproducibility["model_seed"]) != args.model_seed:
        raise SIMA0Error("checkpoint model seed differs from --model-seed")
    if str(data_cfg["dataset"]).lower() != "fashionmnist":
        raise SIMA0Error("SI-MA0 requires FashionMNIST")
    if str(model_cfg["architecture"]) != "lenet_classic":
        raise SIMA0Error("SI-MA0 requires lenet_classic")
    if str(method_cfg.get("name", "")).lower() != "strict":
        raise SIMA0Error("SI-MA0 requires a Strict checkpoint")
    if float(method_cfg.get("eta", math.nan)) != float(
        contract["scope"]["eta"]
    ):
        raise SIMA0Error("checkpoint eta differs from the SI-MA0 contract")
    if int(method_cfg.get("inference_steps", -1)) != int(
        contract["scope"]["inference_steps"]
    ):
        raise SIMA0Error(
            "checkpoint inference_steps differs from the SI-MA0 contract"
        )
    configured_threads = int(runtime.get("torch_threads", 4))
    device, dtype, lane, thread_count = prepare_runtime(
        args.device,
        configured_threads=configured_threads,
    )
    thresholds = thresholds_for(contract, lane=lane)
    set_global_seed(
        args.model_seed,
        deterministic=True,
        warn_only=False,
    )
    torch2pc_path = repo / str(config["torch2pc"]["local_path"])
    if git_output(torch2pc_path, "rev-parse", "HEAD") != TORCH2PC_COMMIT:
        raise SIMA0Error("Torch2PC checkout differs from the frozen commit")
    if git_output(torch2pc_path, "status", "--porcelain"):
        raise SIMA0Error("Torch2PC worktree is dirty")
    pc_infer = load_pc_infer(torch2pc_path)
    batches = materialize_validation_batches(
        config,
        count=args.max_batches,
    )
    checkpoint_sha256 = sha256_file(checkpoint_path)
    config_sha256 = canonical_json_digest(config)
    all_comparisons: list[dict[str, Any]] = []
    all_states: list[dict[str, Any]] = []
    all_outputs: list[dict[str, Any]] = []
    all_regions: list[dict[str, Any]] = []
    all_totals: list[dict[str, Any]] = []
    batch_summaries: list[dict[str, Any]] = []
    for batch_id, (cpu_inputs, cpu_targets, indices) in enumerate(batches):
        if int(cpu_inputs.shape[0]) != int(contract["scope"]["batch_size"]):
            raise SIMA0Error("validation batch size differs from contract")
        inputs = cpu_inputs.to(device=device, dtype=dtype)
        targets = cpu_targets.to(device=device)
        metadata = {
            "contract_id": CONTRACT_ID,
            "source_git_commit": source_commit,
            "source_git_branch": source_branch,
            "experiment_image": experiment_image,
            "image_revision": image_revision,
            "torch_version": torch.__version__,
            "torch_hip_version": getattr(torch.version, "hip", None),
            "torch2pc_commit": TORCH2PC_COMMIT,
            "checkpoint_sha256": checkpoint_sha256,
            "config_sha256": config_sha256,
            "split_manifest_sha256": source_indices_digest(indices),
            "input_sha256": tensor_digest(cpu_inputs),
            "target_sha256": tensor_digest(cpu_targets),
            "model_seed": args.model_seed,
            "batch_id": batch_id,
            "execution_scope": scope,
            "lane": lane,
        }
        (
            comparisons,
            state_records,
            output_records,
            region_records,
            total_records,
        ) = run_modes_for_batch(
            pc_infer=pc_infer,
            config=config,
            state_dict=state_dict,
            inputs=inputs,
            targets=targets,
            device=device,
            dtype=dtype,
            thresholds=thresholds,
            metadata=metadata,
            eta=float(contract["scope"]["eta"]),
            inference_steps=int(contract["scope"]["inference_steps"]),
            updated_state_layers=int(
                contract["scope"]["updated_state_layers_per_sweep"]
            ),
        )
        all_comparisons.extend(comparisons)
        all_states.extend(state_records)
        all_outputs.extend(output_records)
        all_regions.extend(region_records)
        all_totals.extend(total_records)
        batch_summaries.append(
            {
                "model_seed": args.model_seed,
                "batch_id": batch_id,
                "state_update_events": len(state_records),
                "output_error_records": len(output_records),
                "mode_comparisons": len(comparisons),
                "all_state_updates_passed": all(
                    bool(record["passed"]) for record in state_records
                ),
                "all_output_errors_passed": all(
                    bool(record["passed"]) for record in output_records
                ),
                "all_mode_comparisons_passed": all(
                    bool(record["passed"]) for record in comparisons
                ),
            }
        )
    counts = expected_record_counts(
        model_count=1,
        batch_count=args.max_batches,
        inference_steps=int(contract["scope"]["inference_steps"]),
        updated_state_layers=int(
            contract["scope"]["updated_state_layers_per_sweep"]
        ),
    )
    observed_counts = {
        "state_update_events": len(all_states),
        "output_error_records": len(all_outputs),
        "diagnostic_records": len(all_states) + len(all_outputs),
        "mode_comparisons": len(all_comparisons),
    }
    if observed_counts != counts:
        raise SIMA0Error(
            f"SI-MA0 count mismatch: {observed_counts} != {counts}"
        )
    accounting_limit = float(
        contract["thresholds"]["timing_accounting"][
            "max_relative_residual"
        ]
    )
    timer_operational = all(
        bool(record["finite"]) and bool(record["nonnegative"])
        for record in all_totals
    ) and bool(all_totals)
    accounting_threshold_passed = all(
        float(record["accounting_residual"]) <= accounting_limit
        for record in all_totals
    )
    rec_passed = all(bool(record["passed"]) for record in all_states)
    obs_passed = all(
        bool(record["passed"]) for record in all_comparisons
    )
    ver_passed = all(
        int(record["state_version_after"])
        == int(record["state_version_before"]) + 1
        for record in all_states
    )
    cmp_passed = (
        observed_counts == counts
        and all(bool(record["passed"]) for record in all_outputs)
    )
    smoke_passed = (
        rec_passed
        and obs_passed
        and ver_passed
        and timer_operational
        and cmp_passed
    )
    output_dir = repo / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    contract_text = contract_path.read_text(encoding="utf-8")
    (output_dir / "si_ma0_contract.json").write_text(
        contract_text,
        encoding="utf-8",
    )
    environment = {
        "contract_id": CONTRACT_ID,
        "implementation_schema_id": IMPLEMENTATION_SCHEMA_ID,
        "scope": scope,
        "lane": lane,
        "source_git_commit": source_commit,
        "source_git_branch": source_branch,
        "experiment_image": experiment_image,
        "image_revision": image_revision,
        "torch_version": torch.__version__,
        "torch_hip_version": getattr(torch.version, "hip", None),
        "device_name": (
            torch.cuda.get_device_name(0) if device.type == "cuda" else "cpu"
        ),
        "visible_rocm_devices": os.environ.get("ROCR_VISIBLE_DEVICES"),
        "cpu_thread_count": thread_count,
        "deterministic_algorithms_enabled": (
            torch.are_deterministic_algorithms_enabled()
        ),
        "dataset_loader_used": True,
        "test_split_access": False,
        "checkpoint": str(args.checkpoint),
        "checkpoint_sha256": checkpoint_sha256,
        "model_seed": args.model_seed,
        "batches": args.max_batches,
        **prerequisites,
    }
    (output_dir / "si_ma0_environment.json").write_text(
        json.dumps(environment, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    attempt = {
        "attempt_id": (
            f"{source_commit[:12]}-{lane}-seed-{args.model_seed}-"
            f"{scope}-{uuid.uuid4().hex}"
        ),
        "scope": scope,
        "lane": lane,
        "model_seed": args.model_seed,
        "checkpoint_sha256": checkpoint_sha256,
        "status": "passed" if smoke_passed else "failed",
        "replacement_of": None,
    }
    (output_dir / "si_ma0_attempts.jsonl").write_text(
        json.dumps(attempt, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    vjp_records, saved_records, graph_records = make_derived_records(
        all_states,
        all_outputs,
    )
    write_records(output_dir / "si_ma0_event_records.csv", all_states)
    write_records(
        output_dir / "si_ma0_output_error_records.csv",
        all_outputs,
    )
    write_records(
        output_dir / "si_ma0_mode_comparisons.csv",
        all_comparisons,
    )
    write_records(
        output_dir / "si_ma0_total_timing_records.csv",
        all_totals,
    )
    write_records(
        output_dir / "si_ma0_region_timing_records.csv",
        all_regions,
    )
    write_records(output_dir / "si_ma0_vjp_records.csv", vjp_records)
    write_records(
        output_dir / "si_ma0_saved_tensor_records.csv",
        saved_records,
    )
    write_records(
        output_dir / "si_ma0_graph_lifetime_records.csv",
        graph_records,
    )
    write_records(
        output_dir / "si_ma0_batch_summaries.csv",
        batch_summaries,
    )
    write_records(
        output_dir / "si_ma0_model_region_summaries.csv",
        summarize_regions(all_regions),
    )
    summary = {
        "contract_id": CONTRACT_ID,
        "implementation_schema_id": IMPLEMENTATION_SCHEMA_ID,
        "scope": scope,
        "lane": lane,
        "source_git_commit": source_commit,
        "source_git_branch": source_branch,
        "experiment_image": experiment_image,
        "image_revision": image_revision,
        "model_seed": args.model_seed,
        "expected_counts": counts,
        "observed_counts": observed_counts,
        "rec_ma0_smoke_passed": rec_passed,
        "obs_ma0_smoke_passed": obs_passed,
        "ver_ma0_smoke_passed": ver_passed,
        "cost_ma0_timer_operational": timer_operational,
        "cost_ma0_accounting_threshold_passed": (
            accounting_threshold_passed
        ),
        "cmp_ma0_smoke_passed": cmp_passed,
        "confirmatory_decision_made": False,
        "si_ma0_passed": None,
        "passed": smoke_passed,
        "dataset_loader_used": True,
        "test_split_access": False,
    }
    (output_dir / "si_ma0_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    decision = {
        "contract_id": CONTRACT_ID,
        "scope": scope,
        "smoke_passed": smoke_passed,
        "confirmatory_decision_made": False,
        "si_ma0_passed": None,
        "authorized_next_step": (
            "controlled implementation smoke review"
            if smoke_passed
            else "inspect failed smoke records"
        ),
    }
    (output_dir / "si_ma0_decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_sha256_manifest(output_dir)
    missing = [
        name for name in OUTPUT_NAMES if not (output_dir / name).is_file()
    ]
    if missing:
        raise SIMA0Error(f"SI-MA0 outputs are missing: {missing}")
    print(json.dumps(summary, indent=2, sort_keys=True))
    if not smoke_passed:
        raise SystemExit("SI-MA0 implementation cell failed")
    print("OK: SI-MA0 implementation cell passed")


if __name__ == "__main__":
    main()
