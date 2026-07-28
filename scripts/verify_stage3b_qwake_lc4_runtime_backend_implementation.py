#!/usr/bin/env python3
"""Verify the bounded QW-LC4-E backend without repository runtime effects."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
from pathlib import Path
from typing import Any, cast

from torch2pc_thesis.stage3b_qwake_lc4_execution_admission import (
    AUTHORIZED_OUTPUT_ROOT,
    EXECUTION_LEASE_RELATIVE,
)
from torch2pc_thesis.stage3b_qwake_lc4_execution_wrapper import (
    FROZEN_AUTHORIZATION_SHA256,
    FROZEN_TORCH2PC_COMMIT,
)
from torch2pc_thesis.stage3b_qwake_lc4_runtime_backend import (
    AUTHORING_HEAD_COMMIT,
    AUTHORING_MERGE_COMMIT,
    AUTHORING_REQUEST_SHA256,
    MATERIALIZED_EXECUTION_FREEZE_RELATIVE,
    MATERIALIZED_EXECUTION_FREEZE_ROOT,
    RUNTIME_BACKEND_IMPLEMENTATION_ID,
    RUNTIME_BACKEND_IMPLEMENTATION_STATUS,
    execute_bounded_runtime_cell,
    inspect_runtime_frontier_normalization,
)
from torch2pc_thesis.stage3b_qwake_lc4_runtime_freeze import (
    RUNTIME_CANDIDATE_INDICES,
    RuntimeLane,
    load_runtime_authorization,
    runtime_authorization_cells,
)

IMPLEMENTATION_ROOT_RELATIVE = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-runtime-backend-implementation-v1"
)
MODULE_RELATIVE = Path(
    "src/torch2pc_thesis/stage3b_qwake_lc4_runtime_backend.py"
)
ENTRYPOINT_RELATIVE = Path(
    "scripts/run_stage3b_qwake_lc4_authorized_runtime.py"
)
VALIDATOR_RELATIVE = Path(
    "scripts/verify_stage3b_qwake_lc4_runtime_backend_implementation.py"
)
TEST_RELATIVE = Path(
    "tests/unit/test_stage3b_qwake_lc4_runtime_backend_implementation.py"
)
AUTHORIZATION_RELATIVE = Path(
    "experiments/frozen/stage3b-qwake-lc4-f-runtime-freeze-v1/"
    "authorization.json"
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    return parser


def _sha256(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise RuntimeError(f"regular file is absent: {path}")
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON root is not an object: {path}")
    return cast(dict[str, Any], value)


def _verify_registry(root: Path) -> tuple[Path, Path]:
    package = root / IMPLEMENTATION_ROOT_RELATIVE
    manifest = package / "implementation.json"
    registry = package / "SHA256SUMS"
    if not package.is_dir() or package.is_symlink():
        raise RuntimeError("runtime-backend implementation package is absent")
    if not registry.is_file() or registry.is_symlink():
        raise RuntimeError("runtime-backend implementation registry is absent")
    lines = registry.read_text(encoding="utf-8").splitlines()
    if len(lines) != 1:
        raise RuntimeError("runtime-backend implementation registry differs")
    digest, separator, relative = lines[0].partition("  ")
    if not separator or relative != "implementation.json":
        raise RuntimeError("runtime-backend implementation registry path differs")
    if _sha256(manifest) != f"sha256:{digest}":
        raise RuntimeError("runtime-backend implementation registry digest differs")
    observed = {
        path.relative_to(package).as_posix()
        for path in package.iterdir()
        if path.is_file() and not path.is_symlink()
    }
    if observed != {"implementation.json", "SHA256SUMS"}:
        raise RuntimeError("runtime-backend implementation package file set differs")
    return manifest, registry


def _verify_entrypoint(path: Path) -> None:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    top_level_calls = [
        node
        for node in tree.body
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
    ]
    if top_level_calls:
        raise RuntimeError("one-shot entrypoint has a top-level call effect")
    guards = [node for node in tree.body if isinstance(node, ast.If)]
    if len(guards) != 1:
        raise RuntimeError("one-shot entrypoint main boundary differs")


def main() -> int:
    args = _parser().parse_args()
    root = args.project_root.expanduser().resolve()
    repository_lease = root / EXECUTION_LEASE_RELATIVE
    repository_output = root / AUTHORIZED_OUTPUT_ROOT
    future_freeze_root = root / MATERIALIZED_EXECUTION_FREEZE_ROOT
    future_freeze = root / MATERIALIZED_EXECUTION_FREEZE_RELATIVE

    for path, label in (
        (repository_lease, "repository execution lease"),
        (repository_output, "repository runtime output"),
        (future_freeze_root, "materialized execution-freeze package"),
        (future_freeze, "materialized execution freeze"),
    ):
        if path.exists() or path.is_symlink():
            raise RuntimeError(f"{label} is already present")

    manifest_path, registry_path = _verify_registry(root)
    manifest = _object(manifest_path)
    if manifest.get("schema_version") != 1:
        raise RuntimeError("runtime-backend implementation schema differs")
    if manifest.get("implementation_id") != RUNTIME_BACKEND_IMPLEMENTATION_ID:
        raise RuntimeError("runtime-backend implementation id differs")
    if manifest.get("status") != RUNTIME_BACKEND_IMPLEMENTATION_STATUS:
        raise RuntimeError("runtime-backend implementation status differs")
    if manifest.get("slice") != "QW-LC4-E-runtime-backend-implementation":
        raise RuntimeError("runtime-backend implementation slice differs")
    if manifest.get("next_slice") != (
        "QW-LC4-E-runtime-backend-implementation-commit"
    ):
        raise RuntimeError("runtime-backend next slice differs")
    if manifest.get("post_merge_next_slice") != (
        "QW-LC4-E-execution-freeze-materialization"
    ):
        raise RuntimeError("runtime-backend post-merge slice differs")

    source = cast(dict[str, Any], manifest.get("source"))
    expected_source = {
        "base_commit": AUTHORING_MERGE_COMMIT,
        "authoring_head_commit": AUTHORING_HEAD_COMMIT,
        "authoring_request_sha256": AUTHORING_REQUEST_SHA256,
        "torch2pc_commit": FROZEN_TORCH2PC_COMMIT,
    }
    for field, expected in expected_source.items():
        if source.get(field) != expected:
            raise RuntimeError(f"runtime-backend source differs: {field}")

    components = cast(dict[str, Any], manifest.get("components"))
    paths = {
        "backend_module_sha256": MODULE_RELATIVE,
        "entrypoint_sha256": ENTRYPOINT_RELATIVE,
        "validator_sha256": VALIDATOR_RELATIVE,
        "test_sha256": TEST_RELATIVE,
    }
    for field, relative in paths.items():
        if components.get(field) != _sha256(root / relative):
            raise RuntimeError(f"runtime-backend component differs: {field}")

    if components.get("authorized_cell_count") != 168:
        raise RuntimeError("runtime-backend authorized cell count differs")
    if components.get("reserve_probe_count") != 28:
        raise RuntimeError("runtime-backend reserve-probe count differs")
    if components.get("backend_output_file_count") != 7:
        raise RuntimeError("runtime-backend output file count differs")
    if components.get("frontier_normalization_rule") != (
        "completed_upper_errors_to_fixed_minus_beliefs_with_lane_tolerance"
    ):
        raise RuntimeError("runtime-backend normalization rule differs")
    if components.get("negative_validation_evidence_preserved") is not True:
        raise RuntimeError("negative validation preservation differs")

    gates = cast(dict[str, Any], manifest.get("gates"))
    for gate in (
        "execution_freeze_authoring_merged",
        "runtime_backend_branch_open",
        "concrete_runtime_backend_present",
        "one_shot_entrypoint_present",
        "runtime_execution_freeze_guard_present",
        "frontier_roundoff_canonicalization_present",
        "negative_validation_evidence_preserved",
    ):
        if gates.get(gate) is not True:
            raise RuntimeError(f"runtime-backend capability gate is closed: {gate}")
    for gate in (
        "immutable_execution_image_present",
        "execution_freeze_materialized",
        "execution_lease_materialized",
        "qw_lc4_e_execution_permitted",
        "authorization_consumed",
        "runtime_execution_started",
        "runtime_execution_performed",
        "engineering_evidence_present",
        "scientific_execution_open",
        "test_dataset_access",
        "publication_permitted",
        "local_compute_execution_open",
    ):
        if gates.get(gate) is not False:
            raise RuntimeError(f"runtime-backend effect gate is open: {gate}")

    _verify_entrypoint(root / ENTRYPOINT_RELATIVE)
    authorization = load_runtime_authorization(root / AUTHORIZATION_RELATIVE)
    if authorization.authorization_sha256 != FROZEN_AUTHORIZATION_SHA256:
        raise RuntimeError("frozen runtime authorization identity differs")
    if authorization.cells != runtime_authorization_cells():
        raise RuntimeError("frozen runtime authorization matrix differs")

    cpu_cells = {
        cell.candidate_index: cell
        for cell in authorization.cells
        if cell.lane is RuntimeLane.CPU_FLOAT64_ENGINEERING
        and cell.repeat_index == 0
    }
    if tuple(sorted(cpu_cells)) != RUNTIME_CANDIDATE_INDICES:
        raise RuntimeError("CPU control candidate set differs")

    defects: list[float] = []
    normalized_candidates: list[int] = []
    for candidate_index in RUNTIME_CANDIDATE_INDICES:
        normalization = inspect_runtime_frontier_normalization(
            RuntimeLane.CPU_FLOAT64_ENGINEERING,
            candidate_index,
        )
        normalization.require()
        if normalization.maximum_absolute_defect > 1.0e-12:
            raise RuntimeError("CPU frontier roundoff exceeds implementation bound")
        if normalization.normalization_applied:
            normalized_candidates.append(candidate_index)
        record = execute_bounded_runtime_cell(cpu_cells[candidate_index])
        record.require(cpu_cells[candidate_index])
        if not (
            record.response_passed
            and record.structural_equal
            and record.rng_post_match
        ):
            raise RuntimeError("CPU bounded runtime control failed")
        if not math.isfinite(record.response_defect):
            raise RuntimeError("CPU response defect is not finite")
        defects.append(record.response_defect)

    if tuple(normalized_candidates) != (2, 3, 4, 5, 6):
        raise RuntimeError("CPU frontier normalization candidate set differs")

    for path, label in (
        (repository_lease, "verifier materialized repository lease"),
        (repository_output, "verifier materialized repository output"),
        (future_freeze_root, "verifier materialized execution-freeze package"),
        (future_freeze, "verifier materialized execution freeze"),
    ):
        if path.exists() or path.is_symlink():
            raise RuntimeError(label)

    print(f"RUNTIME_BACKEND_IMPLEMENTATION_ID={RUNTIME_BACKEND_IMPLEMENTATION_ID}")
    print(f"RUNTIME_BACKEND_IMPLEMENTATION_STATUS={RUNTIME_BACKEND_IMPLEMENTATION_STATUS}")
    print(f"AUTHORING_MERGE_COMMIT={AUTHORING_MERGE_COMMIT}")
    print(f"AUTHORING_HEAD_COMMIT={AUTHORING_HEAD_COMMIT}")
    print(f"AUTHORING_REQUEST_SHA256={AUTHORING_REQUEST_SHA256}")
    print(f"IMPLEMENTATION_JSON_SHA256={_sha256(manifest_path)}")
    print(f"IMPLEMENTATION_REGISTRY_SHA256={_sha256(registry_path)}")
    print(f"CPU_CONTROL_CANDIDATE_COUNT={len(cpu_cells)}")
    print(f"CPU_NORMALIZED_CANDIDATES={','.join(map(str, normalized_candidates))}")
    print(f"CPU_MAX_RESPONSE_DEFECT={max(defects):.18g}")
    print("EXECUTION_FREEZE_AUTHORING_MERGED=true")
    print("RUNTIME_BACKEND_BRANCH_OPEN=true")
    print("CONCRETE_RUNTIME_BACKEND_PRESENT=true")
    print("ONE_SHOT_ENTRYPOINT_PRESENT=true")
    print("RUNTIME_EXECUTION_FREEZE_GUARD_PRESENT=true")
    print("FRONTIER_ROUNDOFF_CANONICALIZATION_PRESENT=true")
    print("NEGATIVE_VALIDATION_EVIDENCE_PRESERVED=true")
    print("IMMUTABLE_EXECUTION_IMAGE_PRESENT=false")
    print("EXECUTION_FREEZE_MATERIALIZED=false")
    print("EXECUTION_LEASE_MATERIALIZED=false")
    print("QW_LC4_E_EXECUTION_PERMITTED=false")
    print("AUTHORIZATION_CONSUMED=false")
    print("RUNTIME_EXECUTION_STARTED=false")
    print("RUNTIME_EXECUTION_PERFORMED=false")
    print("ENGINEERING_EVIDENCE_PRESENT=false")
    print("SCIENTIFIC_EXECUTION_OPEN=false")
    print("TEST_DATASET_ACCESS=false")
    print("PUBLICATION_PERMITTED=false")
    print("LOCAL_COMPUTE_EXECUTION_OPEN=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
