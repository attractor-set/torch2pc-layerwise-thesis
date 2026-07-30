# Validate QW-LC4-E persistent-evidence-chain-v2 authoring.

from __future__ import annotations

import ast
import json
import shutil
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest

from torch2pc_thesis.stage3b_qwake_lc4_persistent_evidence_chain_v2 import (
    ADR_EN_RELATIVE,
    ADR_RU_RELATIVE,
    AUTHORING_BASE_COMMIT,
    DURABLE_HOST_OUTCOME_RELATIVE,
    EXECUTION_LEASE_V2_RELATIVE,
    IDENTITY_REPAIR_MERGE_COMMIT,
    MODULE_RELATIVE,
    PACKAGE_RELATIVE,
    PERSISTENT_EVIDENCE_CHAIN_V2_ID,
    PERSISTENT_LEASE_V2_OPERATOR_ACKNOWLEDGEMENT,
    POST_MERGE_RECEIPT_RELATIVE,
    OutputSnapshot,
    PersistentEvidenceChainV2,
    PersistentEvidenceChainV2Error,
    PersistentExecutionLeaseV2,
    build_durable_host_outcome_receipt,
    build_persistent_execution_lease_v2,
    load_persistent_evidence_chain_v2,
    load_post_merge_validation_receipt,
    sha256_bytes,
    verify_persistent_evidence_chain_v2,
)

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / PACKAGE_RELATIVE
CHAIN_RECORD = PACKAGE / "chain.json"
RECEIPT_RECORD = ROOT / POST_MERGE_RECEIPT_RELATIVE
SOURCE_REGISTRY = PACKAGE / "source-SHA256SUMS"
OUTPUT_ROOT = ROOT / "results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001"
LEASE_V1 = ROOT / (
    "results/stage-3/"
    "qwake-lc4-runtime-validation-v1-attempt-001.execution-lease.json"
)
LEASE_V2 = ROOT / EXECUTION_LEASE_V2_RELATIVE
OUTCOME = ROOT / DURABLE_HOST_OUTCOME_RELATIVE
EXECUTION_COMMIT = "1" * 40
EMPTY_SHA256 = sha256_bytes(b"")


def _registry(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="strict").splitlines():
        digest, relative = line.split("  ", 1)
        result[relative] = "sha256:" + digest
    return result


def _json(path: Path) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads(path.read_text(encoding="utf-8", errors="strict")),
    )


def _lease() -> tuple[PersistentEvidenceChainV2, PersistentExecutionLeaseV2]:
    chain = verify_persistent_evidence_chain_v2(ROOT)
    lease = build_persistent_execution_lease_v2(
        chain,
        claimed_at_utc="2026-07-30T03:00:00Z",
        execution_commit=EXECUTION_COMMIT,
        operator_acknowledgement=(
            PERSISTENT_LEASE_V2_OPERATOR_ACKNOWLEDGEMENT
        ),
        output_root_absent_at_claim=True,
        execution_lease_absent_at_claim=True,
        durable_outcome_absent_at_claim=True,
    )
    return chain, lease


def _absent_snapshot() -> OutputSnapshot:
    return OutputSnapshot(
        present=False,
        tree_sha256=EMPTY_SHA256,
        file_count=0,
        byte_count=0,
        staging_count=0,
    )


def test_package_is_exact_and_self_hashed() -> None:
    assert sorted(path.name for path in PACKAGE.iterdir()) == [
        "SHA256SUMS",
        "chain.json",
        "post-merge-validation.json",
        "source-SHA256SUMS",
    ]
    registry = _registry(PACKAGE / "SHA256SUMS")
    assert registry == {
        "chain.json": sha256_bytes(CHAIN_RECORD.read_bytes()),
        "post-merge-validation.json": sha256_bytes(RECEIPT_RECORD.read_bytes()),
        "source-SHA256SUMS": sha256_bytes(SOURCE_REGISTRY.read_bytes()),
    }


def test_chain_and_receipt_are_canonical() -> None:
    chain = load_persistent_evidence_chain_v2(CHAIN_RECORD)
    receipt = load_post_merge_validation_receipt(RECEIPT_RECORD)
    assert CHAIN_RECORD.read_text(encoding="utf-8") == chain.canonical_json()
    assert RECEIPT_RECORD.read_text(encoding="utf-8") == receipt.canonical_json()
    assert chain.chain_id == PERSISTENT_EVIDENCE_CHAIN_V2_ID
    assert chain.source.authoring_base_commit == AUTHORING_BASE_COMMIT
    assert chain.source.identity_repair_merge_commit == IDENTITY_REPAIR_MERGE_COMMIT
    assert chain.post_merge_validation_receipt_sha256 == sha256_bytes(
        RECEIPT_RECORD.read_bytes()
    )


def test_complete_latest_identity_chain_is_bound() -> None:
    chain = verify_persistent_evidence_chain_v2(ROOT)
    assert chain.source.invocation_authorization_merge_commit
    assert chain.source.execution_authorization_merge_commit
    assert chain.source.preexecution_verification_merge_commit
    assert chain.source.runtime_operation_merge_commit
    assert chain.source.identity_repair_merge_commit
    assert chain.source.image_repo_digest.startswith(
        "torch2pc-layerwise-thesis@sha256:"
    )
    assert chain.source.invocation_count == 1


def test_persistent_lease_v2_is_pure_and_complete() -> None:
    chain, lease = _lease()
    assert lease.persistent_evidence_chain_sha256 == chain.chain_sha256
    assert lease.invocation_authorization_sha256 == (
        chain.source.invocation_authorization_sha256
    )
    assert lease.execution_authorization_sha256 == (
        chain.source.execution_authorization_sha256
    )
    assert lease.preexecution_verification_sha256 == (
        chain.source.preexecution_verification_sha256
    )
    assert lease.runtime_operation_sha256 == chain.source.runtime_operation_sha256
    assert lease.identity_repair_sha256 == chain.source.identity_repair_sha256
    assert lease.invocation_count == 1
    assert lease.authorization_consumed is True
    assert lease.retry_permitted is False
    assert not LEASE_V2.exists()


def test_persistent_lease_rejects_missing_latest_authorization() -> None:
    chain, lease = _lease()
    with pytest.raises(PersistentEvidenceChainV2Error, match="lease v2 differs"):
        replace(
            lease,
            execution_authorization_sha256="sha256:" + "0" * 64,
        ).require(chain)


def test_durable_nonzero_outcome_contains_terminal_evidence() -> None:
    chain, lease = _lease()
    before = _absent_snapshot()
    after = OutputSnapshot(
        present=True,
        tree_sha256="sha256:" + "2" * 64,
        file_count=2,
        byte_count=123,
        staging_count=0,
    )
    receipt = build_durable_host_outcome_receipt(
        chain,
        lease,
        started_at_utc="2026-07-30T03:00:01Z",
        ended_at_utc="2026-07-30T03:00:02Z",
        termination_class="nonzero_return_code",
        return_code=7,
        child_spawn_count=1,
        command_sha256="sha256:" + "3" * 64,
        image_inspection_sha256="sha256:" + "4" * 64,
        stdout_sha256=sha256_bytes(b"stdout\n"),
        stderr_sha256=sha256_bytes(b"failure\n"),
        stdout_total_bytes=len(b"stdout\n"),
        stderr_total_bytes=len(b"failure\n"),
        stdout_captured_bytes=len(b"stdout\n"),
        stderr_captured_bytes=len(b"failure\n"),
        stdout_truncated=False,
        stderr_truncated=False,
        output_before=before,
        output_after=after,
    )
    assert receipt.return_code == 7
    assert receipt.stdout_sha256 == sha256_bytes(b"stdout\n")
    assert receipt.stderr_sha256 == sha256_bytes(b"failure\n")
    assert receipt.output_before == before
    assert receipt.output_after == after
    assert receipt.automatic_retry_performed is False
    assert receipt.retry_permitted is False
    assert not OUTCOME.exists()


def test_durable_outcome_binds_full_stream_and_truncation_state() -> None:
    chain, lease = _lease()
    absent = _absent_snapshot()
    receipt = build_durable_host_outcome_receipt(
        chain,
        lease,
        started_at_utc="2026-07-30T03:00:01Z",
        ended_at_utc="2026-07-30T03:00:02Z",
        termination_class="nonzero_return_code",
        return_code=9,
        child_spawn_count=1,
        command_sha256="sha256:" + "3" * 64,
        image_inspection_sha256="sha256:" + "4" * 64,
        stdout_sha256="sha256:" + "5" * 64,
        stderr_sha256="sha256:" + "6" * 64,
        stdout_total_bytes=100,
        stderr_total_bytes=20,
        stdout_captured_bytes=10,
        stderr_captured_bytes=20,
        stdout_truncated=True,
        stderr_truncated=False,
        output_before=absent,
        output_after=absent,
    )
    assert receipt.stdout_total_bytes == 100
    assert receipt.stdout_captured_bytes == 10
    assert receipt.stdout_truncated is True
    with pytest.raises(
        PersistentEvidenceChainV2Error,
        match="stdout truncation flag differs",
    ):
        replace(receipt, stdout_truncated=False).require(chain, lease)
    with pytest.raises(
        PersistentEvidenceChainV2Error,
        match="stdout captured bytes exceed total bytes",
    ):
        replace(
            receipt,
            stdout_total_bytes=9,
            stdout_captured_bytes=10,
        ).require(chain, lease)


def test_durable_prelaunch_rejection_is_representable() -> None:
    chain, lease = _lease()
    absent = _absent_snapshot()
    receipt = build_durable_host_outcome_receipt(
        chain,
        lease,
        started_at_utc="2026-07-30T03:00:01Z",
        ended_at_utc="2026-07-30T03:00:01Z",
        termination_class="prelaunch_rejected",
        return_code=None,
        child_spawn_count=0,
        command_sha256=None,
        image_inspection_sha256=None,
        stdout_sha256=sha256_bytes(b""),
        stderr_sha256=sha256_bytes(b"prelaunch rejected\n"),
        stdout_total_bytes=0,
        stderr_total_bytes=len(b"prelaunch rejected\n"),
        stdout_captured_bytes=0,
        stderr_captured_bytes=len(b"prelaunch rejected\n"),
        stdout_truncated=False,
        stderr_truncated=False,
        output_before=absent,
        output_after=absent,
    )
    assert receipt.return_code is None
    assert receipt.child_spawn_count == 0
    assert receipt.lease_present_before is True
    assert receipt.lease_present_after is True


def test_durable_outcome_rejects_retry_or_bad_return_class() -> None:
    chain, lease = _lease()
    absent = _absent_snapshot()
    receipt = build_durable_host_outcome_receipt(
        chain,
        lease,
        started_at_utc="2026-07-30T03:00:01Z",
        ended_at_utc="2026-07-30T03:00:02Z",
        termination_class="success",
        return_code=0,
        child_spawn_count=1,
        command_sha256="sha256:" + "3" * 64,
        image_inspection_sha256="sha256:" + "4" * 64,
        stdout_sha256=sha256_bytes(b""),
        stderr_sha256=sha256_bytes(b""),
        stdout_total_bytes=0,
        stderr_total_bytes=0,
        stdout_captured_bytes=0,
        stderr_captured_bytes=0,
        stdout_truncated=False,
        stderr_truncated=False,
        output_before=absent,
        output_after=absent,
    )
    with pytest.raises(PersistentEvidenceChainV2Error, match="differs"):
        replace(receipt, automatic_retry_performed=True).require(chain, lease)
    with pytest.raises(PersistentEvidenceChainV2Error, match="nonzero"):
        replace(
            receipt,
            termination_class="success",
            return_code=1,
        ).require(chain, lease)


def test_source_registry_rejects_runtime_source_drift(tmp_path: Path) -> None:
    copied = tmp_path / "repo"
    shutil.copytree(ROOT, copied, symlinks=True)
    target = copied / MODULE_RELATIVE
    target.write_text(
        target.read_text(encoding="utf-8") + "\n# drift\n",
        encoding="utf-8",
    )
    with pytest.raises(
        PersistentEvidenceChainV2Error,
        match="bound source SHA-256 differs",
    ):
        verify_persistent_evidence_chain_v2(copied)


def test_existing_lease_or_outcome_closes_verification(tmp_path: Path) -> None:
    copied = tmp_path / "repo"
    shutil.copytree(ROOT, copied, symlinks=True)
    lease = copied / EXECUTION_LEASE_V2_RELATIVE
    lease.parent.mkdir(parents=True, exist_ok=True)
    lease.write_text("{}\n", encoding="utf-8")
    with pytest.raises(
        PersistentEvidenceChainV2Error,
        match="execution lease v2",
    ):
        verify_persistent_evidence_chain_v2(copied)


def test_authoring_module_contains_no_execution_call() -> None:
    tree = ast.parse((ROOT / MODULE_RELATIVE).read_text(encoding="utf-8"))
    calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "invoke_one_shot_host_runtime" not in calls
    assert "execute_one_shot_engineering_invocation_runtime_operation" not in calls
    assert "claim_execution_lease" not in calls
    assert "materialize_execution_lease" not in calls


def test_authoring_gates_resolve_design_blockers_but_not_wiring() -> None:
    chain = verify_persistent_evidence_chain_v2(ROOT)
    assert chain.gates.post_merge_validation_receipt_present is True
    assert chain.gates.runtime_operation_identity_repair_merged is True
    assert chain.gates.latest_authorization_bound_in_lease_template is True
    assert chain.gates.durable_negative_host_outcome_defined is True
    assert chain.gates.persistent_lease_v2_implementation_present is False
    assert chain.gates.durable_outcome_writer_implemented is False
    assert chain.gates.lease_bound_host_invoker_enforced is False
    assert chain.gates.one_shot_engineering_invocation_permitted is False


def test_bilingual_adr_contains_chain_boundaries() -> None:
    chain = verify_persistent_evidence_chain_v2(ROOT)
    for relative in (ADR_RU_RELATIVE, ADR_EN_RELATIVE):
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert chain.chain_sha256 in text
        assert "LEASE_BOUND_HOST_INVOKER_ENFORCED=false" in text
        assert "ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false" in text


def test_repository_boundary_is_closed() -> None:
    verify_persistent_evidence_chain_v2(ROOT)
    assert not OUTPUT_ROOT.exists()
    assert not LEASE_V1.exists()
    assert not LEASE_V2.exists()
    assert not OUTCOME.exists()
    assert not tuple(OUTPUT_ROOT.parent.glob(f".{OUTPUT_ROOT.name}.staging-*"))
    assert _json(CHAIN_RECORD)["gates"]["runtime_execution_performed"] is False
