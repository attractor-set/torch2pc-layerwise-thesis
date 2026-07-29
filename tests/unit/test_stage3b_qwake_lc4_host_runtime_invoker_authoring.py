from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from torch2pc_thesis.stage3b_qwake_lc4_host_runtime_invoker import (
    AUTHORING_BASE_COMMIT,
    AUTHORIZED_OUTPUT_ROOT,
    CONTAINER_EXECUTION_SEQUENCE,
    EXECUTION_LEASE_RELATIVE,
    HOST_EXECUTION_ARGV_PREFIX,
    HOST_OBSERVATION_ARGV_PREFIX,
    HOST_PRELAUNCH_SEQUENCE,
    HOST_RUNTIME_INVOKER_CONTRACT_ID,
    HOST_RUNTIME_INVOKER_CONTRACT_STATUS,
    TERMINAL_OUTCOME_SEQUENCE,
    WRAPPER_IMPLEMENTATION_HEAD_COMMIT,
    QWakeLC4HostRuntimeInvokerError,
    build_host_runtime_invoker_contract,
    load_host_runtime_invoker_contract,
    validate_host_runtime_invoker_contract,
    verify_host_runtime_invoker_authoring_prerequisites,
)

ROOT = Path(__file__).resolve().parents[2]
MODULE = (
    ROOT
    / "src/torch2pc_thesis/stage3b_qwake_lc4_host_runtime_invoker.py"
)
VERIFIER = (
    ROOT
    / "scripts/verify_stage3b_qwake_lc4_host_runtime_invoker_authoring.py"
)
AUTHORING_ROOT = (
    ROOT
    / "experiments/frozen/"
    "stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-authoring-v1"
)


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def test_exact_merged_implementation_and_authorization_are_verified() -> None:
    implementation_sha256, authorization_sha256 = (
        verify_host_runtime_invoker_authoring_prerequisites(ROOT)
    )
    assert implementation_sha256.startswith("sha256:")
    assert authorization_sha256.startswith("sha256:")
    assert AUTHORING_BASE_COMMIT == (
        "be6486a9e3670343132f2c863a5a0cd5969ee9f6"
    )
    assert WRAPPER_IMPLEMENTATION_HEAD_COMMIT == (
        "f8c1465ef326cb2dbe752c2900ab371a8b669284"
    )


def test_host_runtime_invoker_contract_is_exact_and_effect_free() -> None:
    contract = build_host_runtime_invoker_contract(ROOT)
    validate_host_runtime_invoker_contract(contract, ROOT)

    assert contract.contract_id == HOST_RUNTIME_INVOKER_CONTRACT_ID
    assert contract.status == HOST_RUNTIME_INVOKER_CONTRACT_STATUS
    assert contract.host_observation_argv_prefix == HOST_OBSERVATION_ARGV_PREFIX
    assert contract.host_execution_argv_prefix == HOST_EXECUTION_ARGV_PREFIX
    assert contract.host_prelaunch_sequence == HOST_PRELAUNCH_SEQUENCE
    assert contract.container_execution_sequence == CONTAINER_EXECUTION_SEQUENCE
    assert contract.terminal_outcome_sequence == TERMINAL_OUTCOME_SEQUENCE
    assert contract.lease_claim_owner == (
        "container_entrypoint_same_process_as_runtime"
    )
    assert contract.authorization_consumed_boundary == (
        "atomic_execution_lease_claim"
    )
    assert contract.single_child_spawn_per_invoker_process is True
    assert contract.automatic_retry_after_spawn_forbidden is True
    assert contract.host_execution_lease_write_forbidden is True
    assert contract.claim_and_execute_same_container_process_required is True
    assert contract.post_claim_revalidation_required is True
    assert contract.lease_persists_after_failure is True
    assert contract.child_process_group_required is True
    assert contract.signal_forwarding_required is True
    assert contract.timeout_is_terminal is True
    assert contract.nonzero_return_code_is_terminal is True
    assert contract.bounded_output_capture_required is True
    assert contract.command_persistence_forbidden is True
    assert contract.host_runtime_invoker_contract_present is True
    assert contract.host_runtime_invoker_present is False
    assert contract.host_runtime_invoker_executable is False
    assert contract.host_docker_run_implemented is False
    assert contract.execution_lease_materialized is False
    assert contract.authorization_consumed is False
    assert contract.runtime_execution_started is False
    assert contract.runtime_execution_performed is False


def test_contract_sequence_places_claim_revalidation_before_runtime() -> None:
    contract = build_host_runtime_invoker_contract(ROOT)
    sequence = contract.container_execution_sequence
    claim = sequence.index(
        "container_entrypoint_claims_execution_lease_atomically"
    )
    revalidation = sequence.index(
        "container_entrypoint_revalidates_persistent_lease_and_frozen_admission"
    )
    execution = sequence.index(
        "container_entrypoint_executes_bounded_runtime_backend"
    )
    assert claim < revalidation < execution
    assert contract.host_prelaunch_sequence[-1] == (
        "recheck_lease_output_and_staging_absence"
    )


def test_contract_round_trip_is_canonical(tmp_path: Path) -> None:
    contract = build_host_runtime_invoker_contract(ROOT)
    path = tmp_path / "contract.json"
    path.write_text(contract.canonical_json(), encoding="utf-8")
    assert load_host_runtime_invoker_contract(path) == contract


def test_opened_execution_or_invoker_fails_closed() -> None:
    contract = build_host_runtime_invoker_contract(ROOT)
    with pytest.raises(
        QWakeLC4HostRuntimeInvokerError,
        match="host_runtime_invoker_present",
    ):
        replace(contract, host_runtime_invoker_present=True).require()
    with pytest.raises(
        QWakeLC4HostRuntimeInvokerError,
        match="host_docker_run_implemented",
    ):
        replace(contract, host_docker_run_implemented=True).require()
    with pytest.raises(
        QWakeLC4HostRuntimeInvokerError,
        match="contract digest differs",
    ):
        replace(
            contract,
            contract_sha256="sha256:" + "0" * 64,
        ).require()


def test_repository_effects_block_authoring(tmp_path: Path) -> None:
    lease_root = tmp_path / "lease"
    lease_root.mkdir()
    lease = lease_root / EXECUTION_LEASE_RELATIVE
    lease.parent.mkdir(parents=True)
    lease.write_text("{}\n", encoding="utf-8")
    with pytest.raises(
        QWakeLC4HostRuntimeInvokerError,
        match="execution lease already exists",
    ):
        verify_host_runtime_invoker_authoring_prerequisites(lease_root)

    output_case = tmp_path / "output"
    output = output_case / AUTHORIZED_OUTPUT_ROOT
    output.mkdir(parents=True)
    with pytest.raises(
        QWakeLC4HostRuntimeInvokerError,
        match="runtime output already exists",
    ):
        verify_host_runtime_invoker_authoring_prerequisites(output_case)


def test_authoring_surfaces_cannot_execute_or_import_effectful_modules() -> None:
    sources = (
        MODULE.read_text(encoding="utf-8"),
        VERIFIER.read_text(encoding="utf-8"),
    )
    combined = "\n".join(sources)
    forbidden_markers = (
        "Popen",
        "os.system",
        "shell=True",
        "claim_execution_lease(",
        "materialize_execution_lease(",
        "execute_authorized_runtime(",
        "run_one_shot_authorized_runtime(",
        "inspect_local_immutable_image(",
        "materialize_one_shot_invocation(",
        "write_engineering_evidence",
        "publish_result",
    )
    assert all(marker not in combined for marker in forbidden_markers)

    forbidden_modules = {
        "os",
        "subprocess",
        "torch",
        "torch2pc_thesis.stage3b_qwake_lc4_runtime_backend",
        "torch2pc_thesis.stage3b_qwake_lc4_execution_wrapper_implementation",
        "torch2pc_thesis.stage3b_qwake_lc4_invocation_wrapper_implementation",
    }
    for source in sources:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(
                    alias.name not in forbidden_modules
                    and not alias.name.startswith("torch.")
                    for alias in node.names
                )
            if isinstance(node, ast.ImportFrom):
                imported_from = node.module or ""
                assert imported_from not in forbidden_modules
                assert not imported_from.startswith("torch.")

    assert "HOST_RUNTIME_INVOKER_PRESENT=false" in sources[1]
    assert "HOST_DOCKER_RUN_IMPLEMENTED=false" in sources[1]
    assert "EXECUTION_LEASE_MATERIALIZED=false" in sources[1]
    assert "RUNTIME_EXECUTION_PERFORMED=false" in sources[1]


def test_authoring_package_and_documentation_are_registered() -> None:
    authoring = AUTHORING_ROOT / "authoring.json"
    registry = AUTHORING_ROOT / "SHA256SUMS"
    assert authoring.is_file()
    assert registry.is_file()

    expected, relative = registry.read_text(encoding="utf-8").strip().split(
        "  ", 1
    )
    assert relative == "authoring.json"
    assert hashlib.sha256(authoring.read_bytes()).hexdigest() == expected

    payload = json.loads(authoring.read_text(encoding="utf-8"))
    assert payload["authoring_id"] == (
        "stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-authoring-v1"
    )
    assert payload["status"] == (
        "host_runtime_invoker_contract_materialized_execution_path_absent"
    )
    assert payload["source"]["implementation_merge_commit"] == (
        AUTHORING_BASE_COMMIT
    )
    assert payload["contracts"]["contract_id"] == (
        HOST_RUNTIME_INVOKER_CONTRACT_ID
    )
    assert payload["contracts"]["execution_attempt_limit"] == 1
    assert payload["contracts"]["lease_claim_owner"] == (
        "container_entrypoint_same_process_as_runtime"
    )
    assert payload["gates"]["host_runtime_invoker_contract_present"] is True
    assert payload["gates"]["host_runtime_invoker_present"] is False
    assert payload["gates"]["host_runtime_invoker_executable"] is False
    assert payload["gates"]["host_docker_run_implemented"] is False
    assert payload["gates"]["execution_lease_materialized"] is False
    assert payload["gates"]["runtime_execution_performed"] is False
    assert payload["post_merge_next_slice"] == (
        "QW-LC4-E-one-shot-host-runtime-invoker-implementation"
    )

    assert payload["contracts"]["module_sha256"] == _sha256(MODULE)
    assert payload["contracts"]["verifier_sha256"] == _sha256(VERIFIER)
    assert payload["contracts"]["test_sha256"] == _sha256(Path(__file__))

    marker = "ADR-074-stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-authoring"
    required = (
        ROOT / "STATUS.md",
        ROOT / "STATUS_EN.md",
        ROOT / "docs/qwake-local-compute-extension.md",
        ROOT / "docs/qwake-local-compute-extension_EN.md",
        ROOT / "docs/decisions/index.md",
        ROOT / "docs/decisions/index_EN.md",
        ROOT / "docs/language-map.csv",
        ROOT / "docs/research-log/2026-07.md",
        ROOT / "docs/research-log/2026-07_EN.md",
    )
    for path in required:
        assert marker in path.read_text(encoding="utf-8")
