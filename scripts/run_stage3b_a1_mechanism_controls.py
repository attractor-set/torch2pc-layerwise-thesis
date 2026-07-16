#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
from pathlib import Path
from typing import Any

import torch

from torch2pc_thesis.models import build_model
from torch2pc_thesis.stage3b_a1_mechanism_controls import (
    CONTRACT_ID,
    IMPLEMENTATION_SCHEMA_ID,
    TORCH2PC_COMMIT,
    ExecutionScope,
    Provenance,
    build_summary,
    contract_digests,
    expected_counts,
    load_contract,
    model_seeds,
    run_geometry_controls,
    run_lenet_block_probe,
    run_materialized_block_probe,
    run_pnz_controls,
    run_temporal_controls,
    run_transport_controls,
)

OUTPUT_FILES = {
    "geometry": "mechanism_geometry_records.csv",
    "transport": "mechanism_transport_records.csv",
    "temporal_events": "mechanism_temporal_events.csv",
    "temporal_summary": "mechanism_temporal_summary.csv",
    "block_probe": "mechanism_block_probe_records.csv",
    "pnz": "mechanism_pnz_records.csv",
    "contract": "mechanism_controls_contract.json",
    "summary": "mechanism_controls_summary.json",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run deterministic Stage 3B A1 PC-CATM mechanism controls."
    )
    parser.add_argument("device", choices=["cpu", "gpu"])
    parser.add_argument(
        "--execution-scope",
        choices=["smoke", "confirmatory"],
        default="smoke",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path(
            "experiments/planned/"
            "STAGE3B-A1-MECHANISM-CONTROLS-CONTRACT.json"
        ),
    )
    return parser.parse_args()


def git_output(path: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(path), *args],
        text=True,
    ).strip()


def require_environment(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing controlled provenance variable: {name}")
    return value


def prepare_runtime(
    device_name: str,
) -> tuple[torch.device, torch.dtype, str, int]:
    controlled = os.environ.get("TORCH2PC_CONTROLLED_CONTAINER") == "1"
    if not controlled:
        raise RuntimeError("Mechanism controls require a controlled container")
    execution_lane = require_environment("TORCH2PC_EXECUTION_LANE")
    if device_name == "cpu":
        if execution_lane != "cpu":
            raise RuntimeError("CPU execution requires the cpu controlled lane")
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        return torch.device("cpu"), torch.float64, "cpu", 1
    if execution_lane != "rocm":
        raise RuntimeError("GPU execution requires the rocm controlled lane")
    if not torch.cuda.is_available() or getattr(torch.version, "hip", None) is None:
        raise RuntimeError("ROCm execution is unavailable")
    thread_count = int(os.environ.get("OMP_NUM_THREADS", "4"))
    torch.set_num_threads(thread_count)
    torch.set_num_interop_threads(1)
    return torch.device("cuda"), torch.float32, "rocm", thread_count


def normalize_csv_value(value: Any) -> Any:
    if isinstance(value, dict | list | tuple):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return value


def write_records(path: Path, records: list[dict[str, Any]]) -> None:
    if not records:
        raise RuntimeError(f"Refusing to write an empty record file: {path}")
    fieldnames: list[str] = []
    seen: set[str] = set()
    for record in records:
        for key in record:
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(
                {key: normalize_csv_value(record.get(key)) for key in fieldnames}
            )


def add_runtime_metadata(
    records: list[dict[str, Any]],
    *,
    metadata: dict[str, Any],
) -> None:
    for record in records:
        for key, value in metadata.items():
            record[key] = value


def main() -> None:
    args = parse_args()
    scope = args.execution_scope
    if scope not in {"smoke", "confirmatory"}:
        raise ValueError("Unsupported execution scope")
    execution_scope: ExecutionScope = scope

    repo = Path(__file__).resolve().parents[1]
    contract_path = repo / args.contract
    contract = load_contract(contract_path)
    contract_digest, construction_digest, threshold_digest = contract_digests(
        contract
    )

    source_git_commit = require_environment("SOURCE_GIT_COMMIT")
    source_git_branch = require_environment("SOURCE_GIT_BRANCH")
    experiment_image = require_environment("EXPERIMENT_IMAGE")
    image_revision = require_environment("IMAGE_REVISION")
    if source_git_commit != image_revision:
        raise RuntimeError("Controlled image revision differs from source commit")

    device, dtype, lane, thread_count = prepare_runtime(args.device)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    if hasattr(torch.backends, "cudnn"):
        torch.backends.cudnn.deterministic = True

    torch2pc_path = repo / "external" / "Torch2PC"
    if git_output(torch2pc_path, "rev-parse", "HEAD") != TORCH2PC_COMMIT:
        raise RuntimeError("Torch2PC checkout differs from the registered commit")
    if git_output(torch2pc_path, "status", "--porcelain"):
        raise RuntimeError("Torch2PC worktree is dirty")

    provenance = Provenance(
        lane=lane,
        device=args.device,
        dtype=str(dtype),
        source_git_commit=source_git_commit,
        source_git_branch=source_git_branch,
        experiment_image=experiment_image,
        image_revision=image_revision,
        torch2pc_commit=TORCH2PC_COMMIT,
    )

    geometry_records = run_geometry_controls(
        scope=execution_scope,
        provenance=provenance,
        device=device,
        dtype=dtype,
    )
    transport_records = run_transport_controls(
        scope=execution_scope,
        provenance=provenance,
        device=device,
        dtype=dtype,
    )
    temporal_events, temporal_summary = run_temporal_controls(
        scope=execution_scope,
        provenance=provenance,
        device=device,
        dtype=dtype,
    )
    block_probe_records = run_materialized_block_probe(
        scope=execution_scope,
        provenance=provenance,
        device=device,
        dtype=dtype,
    )

    def model_factory(seed: int) -> torch.nn.Sequential:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        return build_model("lenet_classic")

    block_probe_records.extend(
        run_lenet_block_probe(
            scope=execution_scope,
            provenance=provenance,
            device=device,
            dtype=dtype,
            model_factory=model_factory,
        )
    )
    pnz_records = run_pnz_controls(
        scope=execution_scope,
        provenance=provenance,
        device=device,
        dtype=dtype,
    )

    runtime_metadata = {
        "contract_digest": contract_digest,
        "construction_registry_digest": construction_digest,
        "threshold_registry_digest": threshold_digest,
        "torch_version": torch.__version__,
        "torch_hip_version": getattr(torch.version, "hip", None),
        "device_name": torch.cuda.get_device_name(0)
        if args.device == "gpu"
        else "cpu",
        "cpu_thread_count": thread_count,
        "visible_rocm_devices": os.environ.get(
            "ROCR_VISIBLE_DEVICES",
            os.environ.get("HIP_VISIBLE_DEVICES"),
        ),
        "deterministic_algorithms_enabled": (
            torch.are_deterministic_algorithms_enabled()
        ),
        "dataset_loader_used": False,
        "test_split_access": False,
    }
    record_groups = (
        geometry_records,
        transport_records,
        temporal_events,
        temporal_summary,
        block_probe_records,
        pnz_records,
    )
    for records in record_groups:
        add_runtime_metadata(records, metadata=runtime_metadata)

    summary = build_summary(
        scope=execution_scope,
        provenance=provenance,
        contract_digest=contract_digest,
        construction_registry_digest=construction_digest,
        threshold_registry_digest=threshold_digest,
        geometry_records=geometry_records,
        transport_records=transport_records,
        temporal_events=temporal_events,
        temporal_summary=temporal_summary,
        block_probe_records=block_probe_records,
        pnz_records=pnz_records,
    )
    summary.update(
        {
            "execution_environment": runtime_metadata,
            "construction_seeds": [0]
            if execution_scope == "smoke"
            else [0, 1, 2],
            "model_seeds": model_seeds(execution_scope),
        }
    )

    output_dir = repo / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    write_records(output_dir / OUTPUT_FILES["geometry"], geometry_records)
    write_records(output_dir / OUTPUT_FILES["transport"], transport_records)
    write_records(output_dir / OUTPUT_FILES["temporal_events"], temporal_events)
    write_records(output_dir / OUTPUT_FILES["temporal_summary"], temporal_summary)
    write_records(output_dir / OUTPUT_FILES["block_probe"], block_probe_records)
    write_records(output_dir / OUTPUT_FILES["pnz"], pnz_records)

    implementation_contract = {
        "contract_id": CONTRACT_ID,
        "implementation_schema_id": IMPLEMENTATION_SCHEMA_ID,
        "execution_scope": execution_scope,
        "contract_digest": contract_digest,
        "construction_registry_digest": construction_digest,
        "threshold_registry_digest": threshold_digest,
        "expected_counts": expected_counts(execution_scope),
        "output_files": OUTPUT_FILES,
        "provenance": {
            "source_git_commit": source_git_commit,
            "source_git_branch": source_git_branch,
            "experiment_image": experiment_image,
            "image_revision": image_revision,
            "torch2pc_commit": TORCH2PC_COMMIT,
            "lane": lane,
        },
        "frozen_preregistration": contract,
    }
    (output_dir / OUTPUT_FILES["contract"]).write_text(
        json.dumps(implementation_contract, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / OUTPUT_FILES["summary"]).write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if summary.get("passed") is not True:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
