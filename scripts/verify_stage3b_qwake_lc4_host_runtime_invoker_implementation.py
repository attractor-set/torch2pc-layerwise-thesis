#!/usr/bin/env python3
"""Verify bounded QW-LC4-E host-invoker implementation without execution."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from torch2pc_thesis.stage3b_qwake_lc4_host_runtime_invoker import (
    AUTHORIZED_OUTPUT_ROOT,
    EXECUTION_LEASE_RELATIVE,
)
from torch2pc_thesis.stage3b_qwake_lc4_host_runtime_invoker_implementation import (
    AUTHORING_HEAD_COMMIT,
    AUTHORING_MERGE_COMMIT,
    HOST_RUNTIME_INVOKER_IMPLEMENTATION_ID,
    HOST_RUNTIME_INVOKER_IMPLEMENTATION_STATUS,
    build_host_runtime_invoker_implementation_state,
    validate_host_runtime_invoker_implementation_state,
)

IMPLEMENTATION_ROOT_RELATIVE = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-implementation-v1"
)
IMPLEMENTATION_RELATIVE = IMPLEMENTATION_ROOT_RELATIVE / "implementation.json"
REGISTRY_RELATIVE = IMPLEMENTATION_ROOT_RELATIVE / "SHA256SUMS"
MODULE_RELATIVE = Path(
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_host_runtime_invoker_implementation.py"
)
VERIFIER_RELATIVE = Path(
    "scripts/verify_stage3b_qwake_lc4_host_runtime_invoker_implementation.py"
)
TEST_RELATIVE = Path(
    "tests/unit/test_stage3b_qwake_lc4_host_runtime_invoker_implementation.py"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path("."))
    return parser.parse_args()


def _sha256_file(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise RuntimeError(f"required regular file is absent: {path}")
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _as_mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise RuntimeError(f"{field_name} is not an object")
    return cast(Mapping[str, object], value)


def _load_implementation_record(root: Path) -> Mapping[str, object]:
    record_path = root / IMPLEMENTATION_RELATIVE
    registry_path = root / REGISTRY_RELATIVE
    if not registry_path.is_file() or registry_path.is_symlink():
        raise RuntimeError("implementation registry is absent or non-regular")
    lines = tuple(
        line
        for line in registry_path.read_text(encoding="utf-8").splitlines()
        if line
    )
    if len(lines) != 1 or "  " not in lines[0]:
        raise RuntimeError("implementation registry scope differs")
    digest, relative = lines[0].split("  ", 1)
    if relative != "implementation.json":
        raise RuntimeError("implementation registry path differs")
    if "sha256:" + digest != _sha256_file(record_path):
        raise RuntimeError("implementation registry digest differs")
    try:
        raw: Any = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("implementation record cannot be decoded") from exc
    return _as_mapping(raw, "implementation record")


def _require_record(root: Path, record: Mapping[str, object]) -> None:
    source = _as_mapping(record.get("source"), "source")
    contracts = _as_mapping(record.get("contracts"), "contracts")
    gates = _as_mapping(record.get("gates"), "gates")
    exact: Mapping[str, object] = {
        "implementation_id": HOST_RUNTIME_INVOKER_IMPLEMENTATION_ID,
        "status": HOST_RUNTIME_INVOKER_IMPLEMENTATION_STATUS,
    }
    for field_name, expected in exact.items():
        if record.get(field_name) != expected:
            raise RuntimeError(f"implementation record differs: {field_name}")
    expected_hashes = {
        "module_sha256": _sha256_file(root / MODULE_RELATIVE),
        "verifier_sha256": _sha256_file(root / VERIFIER_RELATIVE),
        "test_sha256": _sha256_file(root / TEST_RELATIVE),
    }
    for field_name, expected in expected_hashes.items():
        if contracts.get(field_name) != expected:
            raise RuntimeError(f"implementation source digest differs: {field_name}")
    expected_source: Mapping[str, object] = {
        "authoring_head_commit": AUTHORING_HEAD_COMMIT,
        "authoring_merge_commit": AUTHORING_MERGE_COMMIT,
    }
    for field_name, expected in expected_source.items():
        if source.get(field_name) != expected:
            raise RuntimeError(f"implementation source differs: {field_name}")
    expected_contracts: Mapping[str, object] = {
        "prelaunch_image_inspection_count": 2,
        "prelaunch_materialization_count": 2,
        "subprocess_popen_call_limit": 1,
        "exact_argv_only": True,
        "shell_interpretation_forbidden": True,
        "environment_inheritance_forbidden": True,
        "process_group_required": True,
        "signal_forwarding_required": True,
        "bounded_output_capture_required": True,
        "automatic_retry_after_spawn_forbidden": True,
        "host_execution_lease_write_forbidden": True,
    }
    for field_name, expected in expected_contracts.items():
        if contracts.get(field_name) != expected:
            raise RuntimeError(f"implementation contract differs: {field_name}")
    expected_gates: Mapping[str, object] = {
        "host_runtime_invoker_contract_present": True,
        "host_runtime_invoker_implementation_present": True,
        "host_runtime_invoker_present": True,
        "host_runtime_invoker_executable": True,
        "host_docker_run_implemented": True,
        "branch_runtime_execution_permitted": False,
        "execution_lease_materialized": False,
        "authorization_consumed": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "engineering_evidence_present": False,
        "scientific_execution_open": False,
        "test_dataset_access": False,
        "publication_permitted": False,
        "local_compute_execution_open": False,
    }
    for field_name, expected in expected_gates.items():
        if gates.get(field_name) != expected:
            raise RuntimeError(f"implementation gate differs: {field_name}")


def _verify_effectful_surface(root: Path) -> None:
    source = (root / MODULE_RELATIVE).read_text(encoding="utf-8")
    tree = ast.parse(source)
    popen_calls = 0
    run_calls = 0
    main_guards = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if (
                isinstance(node.func.value, ast.Name)
                and node.func.value.id == "subprocess"
                and node.func.attr == "Popen"
            ):
                popen_calls += 1
                keywords = {item.arg: item.value for item in node.keywords}
                shell = keywords.get("shell")
                session = keywords.get("start_new_session")
                if not isinstance(shell, ast.Constant) or shell.value is not False:
                    raise RuntimeError("Popen shell boundary differs")
                if not isinstance(session, ast.Constant) or session.value is not True:
                    raise RuntimeError("Popen process-group boundary differs")
            if (
                isinstance(node.func.value, ast.Name)
                and node.func.value.id == "subprocess"
                and node.func.attr == "run"
            ):
                run_calls += 1
        if isinstance(node, ast.If) and "__main__" in ast.unparse(node.test):
            main_guards += 1
    if popen_calls != 1:
        raise RuntimeError("implementation Popen call count differs")
    if run_calls != 0:
        raise RuntimeError("implementation contains subprocess.run")
    if main_guards != 0:
        raise RuntimeError("implementation exposes an executable main guard")
    forbidden = (
        "shell=True",
        "write_text(",
        "write_bytes(",
        "os.system(",
    )
    if any(marker in source for marker in forbidden):
        raise RuntimeError("implementation contains a forbidden host effect")


def _require_effect_absence(root: Path) -> None:
    lease = root / EXECUTION_LEASE_RELATIVE
    output = root / AUTHORIZED_OUTPUT_ROOT
    if lease.exists() or lease.is_symlink():
        raise RuntimeError("execution lease was materialized")
    if output.exists() or output.is_symlink():
        raise RuntimeError("runtime output was materialized")
    staging = tuple(output.parent.glob(f".{output.name}.staging-*"))
    if staging:
        raise RuntimeError("runtime staging tree was materialized")


def main() -> int:
    args = parse_args()
    root = args.project_root.expanduser().resolve()
    _require_effect_absence(root)
    record = _load_implementation_record(root)
    _require_record(root, record)
    _verify_effectful_surface(root)
    state = build_host_runtime_invoker_implementation_state(root)
    validate_host_runtime_invoker_implementation_state(state, root)
    _require_effect_absence(root)

    print(f"HOST_RUNTIME_INVOKER_IMPLEMENTATION_ID={state.implementation_id}")
    print(f"HOST_RUNTIME_INVOKER_IMPLEMENTATION_STATUS={state.status}")
    print(f"HOST_RUNTIME_INVOKER_IMPLEMENTATION_SHA256={state.state_sha256}")
    print(f"HOST_RUNTIME_INVOKER_CONTRACT_ID={state.contract_id}")
    print(f"HOST_RUNTIME_INVOKER_CONTRACT_SHA256={state.contract_sha256}")
    print(f"AUTHORING_HEAD_COMMIT={AUTHORING_HEAD_COMMIT}")
    print(f"AUTHORING_MERGE_COMMIT={AUTHORING_MERGE_COMMIT}")
    print("PRELAUNCH_IMAGE_INSPECTION_COUNT=2")
    print("PRELAUNCH_MATERIALIZATION_COUNT=2")
    print("SUBPROCESS_POPEN_CALL_LIMIT=1")
    print("HOST_RUNTIME_INVOKER_CONTRACT_PRESENT=true")
    print("HOST_RUNTIME_INVOKER_IMPLEMENTATION_PRESENT=true")
    print("HOST_RUNTIME_INVOKER_PRESENT=true")
    print("HOST_RUNTIME_INVOKER_EXECUTABLE=true")
    print("HOST_DOCKER_RUN_IMPLEMENTED=true")
    print("EXACT_ARGV_ONLY=true")
    print("SHELL_INTERPRETATION_FORBIDDEN=true")
    print("ENVIRONMENT_INHERITANCE_FORBIDDEN=true")
    print("PROCESS_GROUP_REQUIRED=true")
    print("SIGNAL_FORWARDING_REQUIRED=true")
    print("BOUNDED_OUTPUT_CAPTURE_REQUIRED=true")
    print("AUTOMATIC_RETRY_AFTER_SPAWN_FORBIDDEN=true")
    print("HOST_EXECUTION_LEASE_WRITE_FORBIDDEN=true")
    print("BRANCH_RUNTIME_EXECUTION_PERMITTED=false")
    print("EXECUTION_LEASE_MATERIALIZED=false")
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
