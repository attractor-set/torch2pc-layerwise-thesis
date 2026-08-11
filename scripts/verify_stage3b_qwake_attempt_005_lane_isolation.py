#!/usr/bin/env python3
"""Verify prospective Attempt-005 lane-isolation authoring invariants."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
from typing import Final, cast

from torch2pc_thesis.stage3b_qwake_attempt_005_contract import (
    ATTEMPT_005_ID,
    ATTEMPT_005_OUTPUT_ROOT,
    EXPECTED_GENERIC_RUNTIME_BACKEND_SHA256,
    GENERIC_RUNTIME_BACKEND_RELATIVE,
)
from torch2pc_thesis.stage3b_qwake_attempt_005_lane_isolation import (
    INTERNAL_LANE_WORKER_COUNT,
    attempt005_lane_isolation_evidence,
)

PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/stage3b-qwake-attempt-005-lane-isolation-authoring-v1"
)
CONTRACT_RELATIVE: Final = PACKAGE_RELATIVE / "contract.json"
SOURCE_SUMS_RELATIVE: Final = PACKAGE_RELATIVE / "source-SHA256SUMS"
PACKAGE_SUMS_RELATIVE: Final = PACKAGE_RELATIVE / "SHA256SUMS"
HOST_RELATIVE: Final = Path(
    "scripts/run_stage3b_qwake_attempt_005_host_one_shot.py"
)
PROFILE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/stage3b_qwake_attempt_005_lane_isolation.py"
)


class VerificationError(RuntimeError):
    """Raised when the prospective Attempt-005 authoring state differs."""


def _sha256(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise VerificationError(f"regular file required: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise VerificationError(f"JSON object required: {path}")
    return cast(dict[str, object], value)


def _verify_registry(root: Path, registry: Path, base: Path) -> int:
    count = 0
    for line in registry.read_text(encoding="utf-8").splitlines():
        digest, separator, relative = line.partition("  ")
        if separator != "  " or len(digest) != 64 or not relative:
            raise VerificationError(f"malformed registry line: {registry}")
        target = base / relative
        if _sha256(target) != digest:
            raise VerificationError(f"registry digest differs: {relative}")
        count += 1
    if count == 0:
        raise VerificationError(f"empty registry: {registry}")
    return count


def _call_count(path: Path, attribute: str) -> int:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == attribute
    )


def verify(root: Path) -> None:
    contract = _load_json(root / CONTRACT_RELATIVE)
    expected_contract = {
        "schema_version": 1,
        "attempt_id": ATTEMPT_005_ID,
        "status": "prospective_lane_isolated_integration_confirmation_execution_closed",
        "lane_process_isolation": True,
        "internal_lane_worker_count": 2,
        "automatic_retry_permitted": False,
        "measured_authorized_cell_count": 168,
        "measured_pair_count_per_candidate": 12,
        "reserve_probe_count": 28,
        "aggregate_count": 14,
        "order_effect_tolerance_unchanged": True,
        "cross_lane_comparison_permitted": False,
        "single_combined_runtime_report_required": True,
        "warmup_included_in_measured_matrix": False,
        "scientific_execution_open": False,
        "test_dataset_access": False,
        "publication_permitted": False,
        "generic_runtime_backend_modified": False,
    }
    for key, expected in expected_contract.items():
        if contract.get(key) != expected:
            raise VerificationError(f"authoring contract differs: {key}")

    cpu_profile = contract.get("cpu_profile")
    rocm_profile = contract.get("rocm_profile")
    if cpu_profile != {
        "affinity": [0],
        "torch_num_interop_threads": 1,
        "torch_num_threads": 1,
        "warmup_cell_count": 14,
        "warmup_repeat_indices": [2, 3],
    }:
        raise VerificationError("CPU profile differs")
    if rocm_profile != {
        "affinity": list(range(8)),
        "hip_visible_devices": "0",
        "thread_env": 8,
        "warmup_cell_count": 14,
        "warmup_repeat_indices": [2, 3],
    }:
        raise VerificationError("ROCm profile differs")

    evidence = attempt005_lane_isolation_evidence()
    for key in (
        "lane_process_isolation",
        "internal_lane_worker_count",
        "measured_authorized_cell_count",
        "measured_pair_count_per_candidate",
        "reserve_probe_count",
        "aggregate_count",
        "order_effect_tolerance_unchanged",
        "cross_lane_comparison_permitted",
        "single_combined_runtime_report_required",
        "warmup_included_in_measured_matrix",
        "generic_runtime_backend_modified",
    ):
        if evidence.get(key) != contract.get(key):
            raise VerificationError(f"profile evidence differs: {key}")

    if INTERNAL_LANE_WORKER_COUNT != 2:
        raise VerificationError("internal lane-worker count differs")

    generic_sha = "sha256:" + _sha256(root / GENERIC_RUNTIME_BACKEND_RELATIVE)
    if generic_sha != EXPECTED_GENERIC_RUNTIME_BACKEND_SHA256:
        raise VerificationError("historical generic runtime backend differs")

    host_text = (root / HOST_RELATIVE).read_text(encoding="utf-8")
    profile_text = (root / PROFILE_RELATIVE).read_text(encoding="utf-8")
    if _call_count(root / HOST_RELATIVE, "Popen") != 1:
        raise VerificationError("host Popen call count differs")
    if 'CPUSET_CPUS: Final = "0-7"' not in host_text:
        raise VerificationError("host parent cpuset differs")
    if "LANE_ISOLATION_ENABLE_ENV" not in host_text:
        raise VerificationError("lane-isolation host activation is absent")
    if profile_text.count("_run_worker(RuntimeLane.") != 2:
        raise VerificationError("lane-worker invocation count differs")
    if "BoundedTorchMatrixExecutor" in profile_text:
        raise VerificationError("generic matrix executor was duplicated")
    if "generic_runtime._build_snapshot" not in profile_text or "generic_runtime._run_matched_cell" not in profile_text:
        raise VerificationError("generic runtime primitives are not reused")

    source_count = _verify_registry(
        root,
        root / SOURCE_SUMS_RELATIVE,
        root,
    )
    package_count = _verify_registry(
        root,
        root / PACKAGE_SUMS_RELATIVE,
        root / PACKAGE_RELATIVE,
    )

    print("ATTEMPT005_LANE_ISOLATION_VERIFIER=PASS")
    print(f"ATTEMPT_ID={ATTEMPT_005_ID}")
    print(f"OUTPUT_ROOT={ATTEMPT_005_OUTPUT_ROOT.as_posix()}")
    print("LANE_PROCESS_ISOLATION=true")
    print("INTERNAL_LANE_WORKER_COUNT=2")
    print("CPU_WORKER_AFFINITY=0")
    print("CPU_WORKER_THREADS=1")
    print("ROCM_WORKER_AFFINITY=0-7")
    print("ROCM_WORKER_THREADS=8")
    print("CPU_WARMUP_CELL_COUNT=14")
    print("ROCM_WARMUP_CELL_COUNT=14")
    print("MEASURED_AUTHORIZED_CELL_COUNT=168")
    print("RESERVE_PROBE_COUNT=28")
    print("AGGREGATE_COUNT=14")
    print("ORDER_EFFECT_TOLERANCE_UNCHANGED=true")
    print("GENERIC_RUNTIME_BACKEND_MODIFIED=false")
    print(f"SOURCE_REGISTRY_PATH_COUNT={source_count}")
    print(f"PACKAGE_REGISTRY_PATH_COUNT={package_count}")
    print("RUNTIME_EXECUTION_PERMITTED=false")
    print("SCIENTIFIC_EXECUTION_OPEN=false")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path("."))
    args = parser.parse_args()
    verify(args.project_root.expanduser().resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
