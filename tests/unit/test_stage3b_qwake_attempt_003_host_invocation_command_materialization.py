from __future__ import annotations

import ast
from pathlib import Path

import pytest

import torch2pc_thesis.stage3b_qwake_attempt_003_host_invocation_command_materialization as command_materialization
from torch2pc_thesis.stage3b_qwake_attempt_003_host_invocation_chain import (
    MaterializedHostInvocation,
)

ROOT = Path(__file__).resolve().parents[2]
MODULE = (
    ROOT
    / "src/torch2pc_thesis/"
    "stage3b_qwake_attempt_003_host_invocation_command_materialization.py"
)
VERIFIER = (
    ROOT
    / "scripts/"
    "verify_stage3b_qwake_attempt_003_host_invocation_command_materialization.py"
)
PACKAGE = (
    ROOT
    / "experiments/frozen/"
    "stage3b-qwake-attempt-003-host-invocation-command-materialization-authoring-v1"
)


def _fresh_invocation() -> MaterializedHostInvocation:
    contract = command_materialization.build_attempt_003_command_materialization_contract()
    preflight = command_materialization.build_preflight_invocation_evidence(contract)
    claimed_at = "2026-08-10T04:10:00Z"
    argv = list(preflight.argv)
    marker = argv.index("--claimed-at-utc")
    argv[marker + 1] = claimed_at
    payload = {
        "schema_version": preflight.schema_version,
        "contract_sha256": preflight.contract_sha256,
        "image_inspection_sha256": preflight.image_inspection_sha256,
        "claimed_at_utc": claimed_at,
        "argv": tuple(argv),
        "environment": preflight.environment,
        "mount_sources": preflight.mount_sources,
        "shell_interpretation_used": False,
        "environment_inherited": False,
        "subprocess_spawned": False,
        "container_created": False,
        "authorization_consumed": False,
        "attempt_started": False,
        "execution_lease_created": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
    }
    return MaterializedHostInvocation(
        **payload,
        invocation_sha256=command_materialization.sha256_object(payload),
    )


def test_contract_binds_preflight_as_evidence_not_execution_claim() -> None:
    contract = command_materialization.build_attempt_003_command_materialization_contract()
    assert contract["contract_id"] == command_materialization.CONTRACT_ID
    assert contract["status"] == command_materialization.CONTRACT_STATUS
    assert contract["authorized_parent_head"] == command_materialization.AUTHORIZED_PARENT_HEAD
    assert contract["preflight_invocation_sha256"] == (
        command_materialization.PREFLIGHT_INVOCATION_SHA256
    )
    assert contract["preflight_claimed_at_authoritative_for_execution"] is False
    assert contract["command_template_sha256"] == (
        command_materialization.COMMAND_TEMPLATE_SHA256
    )
    assert contract["command_materialization_contract_authored"] is True
    assert contract["authoritative_host_command_materialized"] is False
    assert contract["command_persisted"] is False
    assert contract["host_process_spawner_present"] is False
    assert contract["docker_run_implemented"] is False
    assert contract["runtime_execution_permitted"] is False


def test_contract_round_trip_is_canonical(tmp_path: Path) -> None:
    contract = command_materialization.build_attempt_003_command_materialization_contract()
    path = tmp_path / "contract.json"
    path.write_text(command_materialization.canonical_json(contract), encoding="utf-8")
    assert (
        command_materialization.load_attempt_003_command_materialization_contract(path)
        == contract
    )


def test_preflight_evidence_digest_and_template_are_exact() -> None:
    contract = command_materialization.build_attempt_003_command_materialization_contract()
    preflight = command_materialization.build_preflight_invocation_evidence(contract)
    assert preflight.claimed_at_utc == command_materialization.PREFLIGHT_CLAIMED_AT_UTC
    assert preflight.invocation_sha256 == command_materialization.PREFLIGHT_INVOCATION_SHA256
    assert command_materialization.command_template_sha256(preflight) == (
        command_materialization.COMMAND_TEMPLATE_SHA256
    )
    assert preflight.subprocess_spawned is False
    assert preflight.container_created is False
    assert preflight.authorization_consumed is False


def test_fresh_claim_time_preserves_static_command_template() -> None:
    contract = command_materialization.build_attempt_003_command_materialization_contract()
    invocation = _fresh_invocation()
    command_materialization.require_materialized_invocation_matches_contract(
        invocation,
        contract,
    )
    assert command_materialization.command_template_sha256(invocation) == (
        command_materialization.COMMAND_TEMPLATE_SHA256
    )
    assert invocation.claimed_at_utc != command_materialization.PREFLIGHT_CLAIMED_AT_UTC


def test_preflight_claim_time_is_rejected_for_authoritative_materialization() -> None:
    contract = command_materialization.build_attempt_003_command_materialization_contract()
    preflight = command_materialization.build_preflight_invocation_evidence(contract)
    with pytest.raises(
        command_materialization.QWakeAttempt003CommandMaterializationError,
        match="not authoritative",
    ):
        command_materialization.require_materialized_invocation_matches_contract(
            preflight,
            contract,
        )


def test_modified_static_argv_is_rejected() -> None:
    contract = command_materialization.build_attempt_003_command_materialization_contract()
    invocation = _fresh_invocation()
    argv = list(invocation.argv)
    memory_index = argv.index("--memory")
    argv[memory_index + 1] = "47g"
    payload = {
        **{
            key: value
            for key, value in invocation.__dict__.items()
            if key != "invocation_sha256"
        },
        "argv": tuple(argv),
    }
    changed = MaterializedHostInvocation(
        **payload,
        invocation_sha256=command_materialization.sha256_object(payload),
    )
    with pytest.raises(
        command_materialization.QWakeAttempt003CommandMaterializationError,
        match="normalized host command template differs",
    ):
        command_materialization.require_materialized_invocation_matches_contract(
            changed,
            contract,
        )


def test_future_record_is_data_only_and_keeps_runtime_closed() -> None:
    contract = command_materialization.build_attempt_003_command_materialization_contract()
    invocation = _fresh_invocation()
    record = command_materialization.build_attempt_003_host_command_record(
        invocation,
        contract,
    )
    assert record["authoritative_host_command_materialized"] is True
    assert record["command_persisted"] is True
    assert record["host_process_spawned"] is False
    assert record["docker_run_invoked"] is False
    assert record["container_created"] is False
    assert record["authorization_consumed"] is False
    assert record["attempt_started"] is False
    assert record["execution_lease_materialized"] is False
    assert record["runtime_execution_permitted"] is False
    assert record["runtime_execution_performed"] is False


def test_authoring_surfaces_have_no_process_spawner() -> None:
    for path in (MODULE, VERIFIER):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(alias.name != "subprocess" for alias in node.names)
            if isinstance(node, ast.ImportFrom):
                assert node.module != "subprocess"
        assert "Popen(" not in source
        assert "os.system(" not in source
        assert "shell=True" not in source


def test_authoring_package_has_exact_contract() -> None:
    contract_path = PACKAGE / "contract.json"
    assert contract_path.is_file()
    observed = command_materialization.load_attempt_003_command_materialization_contract(
        contract_path
    )
    assert observed == (
        command_materialization.build_attempt_003_command_materialization_contract()
    )
