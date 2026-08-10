#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

GENERIC_BACKEND = Path(
    "src/torch2pc_thesis/stage3b_qwake_lc4_runtime_backend.py"
)
GENERIC_BACKEND_SHA256 = (
    "d9ad10efe959e19d7f1b6d61d8eddd1228cb9753fa9191823d5d1ded68e9fd72"
)
PROFILE = Path(
    "src/torch2pc_thesis/"
    "stage3b_qwake_attempt_004_cpu_measurement_stabilization.py"
)
BOUNDED = Path("src/torch2pc_thesis/stage3b_qwake_lc4_bounded.py")
PACKAGE = Path(
    "experiments/frozen/"
    "stage3b-qwake-attempt-004-cpu-measurement-stabilization-authoring-v1"
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def registry(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        digest, sep, relative = line.partition("  ")
        if sep != "  " or not relative:
            raise RuntimeError(f"malformed registry: {path}")
        result[relative] = digest
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.project_root.expanduser().resolve()

    if sha(root / GENERIC_BACKEND) != GENERIC_BACKEND_SHA256:
        raise RuntimeError("historical generic runtime backend changed")

    generic = (root / GENERIC_BACKEND).read_text(encoding="utf-8")
    profile = (root / PROFILE).read_text(encoding="utf-8")
    bounded = (root / BOUNDED).read_text(encoding="utf-8")

    if "attempt004_cpu_stabilization" in generic:
        raise RuntimeError("Attempt-004 hook leaked into generic backend")

    required_profile = (
        "class Attempt004CPUStabilizedMatrixExecutor",
        "BoundedTorchMatrixExecutor",
        "execute_bounded_runtime_cell",
        "configure_attempt004_cpu_measurement()",
        "attempt004_warmup_cells(authorization.cells)",
        "WARMUP_REPEAT_INDICES = (2, 3)",
        "WARMUP_CELL_COUNT = 14",
        "MEASURED_PAIR_COUNT_PER_CANDIDATE = 12",
        "CPU_AFFINITY = frozenset({0})",
        '"OMP_NUM_THREADS": "1"',
        '"MKL_NUM_THREADS": "1"',
        '"OPENBLAS_NUM_THREADS": "1"',
        '"NUMEXPR_NUM_THREADS": "1"',
        "torch.set_num_threads(1)",
        "torch.set_num_interop_threads(1)",
    )
    for token in required_profile:
        if token not in profile:
            raise RuntimeError(f"profile invariant absent: {token}")

    if '"time_ns": (50000, 0.1)' not in bounded:
        raise RuntimeError("CPU order-effect tolerance changed")
    if "def pair_schedule()" not in bounded:
        raise RuntimeError("measured pair schedule changed")

    package = root / PACKAGE
    package_registry = registry(package / "SHA256SUMS")
    if set(package_registry) != {
        "authoring.json",
        "contract.json",
        "source-SHA256SUMS",
    }:
        raise RuntimeError("package registry path set differs")
    for relative, digest in package_registry.items():
        if sha(package / relative) != digest:
            raise RuntimeError(f"package digest differs: {relative}")

    source_registry = registry(package / "source-SHA256SUMS")
    for relative, digest in source_registry.items():
        if sha(root / relative) != digest:
            raise RuntimeError(f"source digest differs: {relative}")

    contract = json.loads((package / "contract.json").read_text())
    expected = {
        "generic_runtime_backend_modified": False,
        "generic_runtime_backend_sha256": GENERIC_BACKEND_SHA256,
        "integration_mode": "separate_runtime_matrix_executor_wrapper",
        "cpu_affinity": [0],
        "torch_num_threads": 1,
        "torch_num_interop_threads": 1,
        "cpu_warmup_cell_count": 14,
        "warmup_reserve_probes": 0,
        "warmup_result_retained": False,
        "warmup_included_in_measured_matrix": False,
        "measured_pair_count_per_candidate": 12,
        "order_effect_tolerance_unchanged": True,
        "legacy_frozen_registries_modified": False,
        "runtime_execution_permitted": False,
        "authorization_consumption_permitted": False,
    }
    for name, value in expected.items():
        if contract.get(name) != value:
            raise RuntimeError(f"contract field differs: {name}")

    print("ATTEMPT004_CPU_STABILIZATION_VERIFIER=PASS")
    print(f"GENERIC_RUNTIME_BACKEND_SHA256={GENERIC_BACKEND_SHA256}")
    print("GENERIC_RUNTIME_BACKEND_MODIFIED=false")
    print("LEGACY_FROZEN_REGISTRIES_MODIFIED=false")
    print("INTEGRATION_MODE=separate_runtime_matrix_executor_wrapper")
    print("CPU_AFFINITY=0")
    print("TORCH_NUM_THREADS=1")
    print("TORCH_NUM_INTEROP_THREADS=1")
    print("CPU_WARMUP_CELL_COUNT=14")
    print("CPU_WARMUP_PAIR_COUNT_PER_CANDIDATE=2")
    print("WARMUP_RESERVE_PROBES=0")
    print("WARMUP_RESULT_RETAINED=false")
    print("MEASURED_PAIR_COUNT_PER_CANDIDATE=12")
    print("ORDER_EFFECT_TOLERANCE_UNCHANGED=true")
    print("CPU_PRIMARY_CLOCK=time_process_time_ns")
    print("RUNTIME_EXECUTION_PERMITTED=false")
    print("AUTHORIZATION_CONSUMPTION_PERMITTED=false")


if __name__ == "__main__":
    main()
