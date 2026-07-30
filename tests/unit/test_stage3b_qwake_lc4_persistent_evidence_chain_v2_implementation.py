# Validate fail-closed persistence for QW-LC4-E evidence-chain-v2 artifacts.

from __future__ import annotations

import os
import shutil
from dataclasses import replace
from pathlib import Path

import pytest

import torch2pc_thesis.stage3b_qwake_lc4_persistent_evidence_chain_v2_implementation as implementation
from torch2pc_thesis.stage3b_qwake_lc4_persistent_evidence_chain_v2 import (
    DURABLE_HOST_OUTCOME_RELATIVE,
    EXECUTION_LEASE_V2_RELATIVE,
    PACKAGE_RELATIVE,
    PERSISTENT_LEASE_V2_OPERATOR_ACKNOWLEDGEMENT,
    SOURCE_REGISTRY_RELATIVE,
    DurableHostOutcomeReceipt,
    OutputSnapshot,
    PersistentEvidenceChainV2,
    PersistentExecutionLeaseV2,
    build_durable_host_outcome_receipt,
    build_persistent_execution_lease_v2,
    sha256_bytes,
    verify_persistent_evidence_chain_v2,
)
from torch2pc_thesis.stage3b_qwake_lc4_persistent_evidence_chain_v2_implementation import (
    LEGACY_EXECUTION_LEASE_RELATIVE,
    PersistentEvidenceChainV2ImplementationError,
    persist_durable_host_outcome_receipt,
    persist_persistent_execution_lease_v2,
    verify_persisted_durable_host_outcome_receipt,
    verify_persisted_persistent_execution_lease_v2,
)

ROOT = Path(__file__).resolve().parents[2]
EXECUTION_COMMIT = "1" * 40
EMPTY_SHA256 = sha256_bytes(b"")


def _copy_file(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def _sandbox(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    package = ROOT / PACKAGE_RELATIVE
    for source in package.iterdir():
        _copy_file(source, root / PACKAGE_RELATIVE / source.name)
    registries = [
        ROOT / SOURCE_REGISTRY_RELATIVE,
        ROOT / implementation.IMPLEMENTATION_SOURCE_REGISTRY_RELATIVE,
    ]
    for source_registry in registries:
        for line in source_registry.read_text(
            encoding="utf-8",
            errors="strict",
        ).splitlines():
            _digest, relative = line.split("  ", 1)
            _copy_file(ROOT / relative, root / relative)
    implementation_package = ROOT / implementation.IMPLEMENTATION_PACKAGE_RELATIVE
    for source in implementation_package.iterdir():
        _copy_file(
            source,
            root / implementation.IMPLEMENTATION_PACKAGE_RELATIVE / source.name,
        )
    (root / "results/stage-3").mkdir(parents=True)
    return root


def _lease(
    root: Path,
) -> tuple[PersistentEvidenceChainV2, PersistentExecutionLeaseV2]:
    chain = verify_persistent_evidence_chain_v2(root)
    lease = build_persistent_execution_lease_v2(
        chain,
        claimed_at_utc="2026-07-30T04:00:00Z",
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


def _receipt(
    chain: PersistentEvidenceChainV2,
    lease: PersistentExecutionLeaseV2,
) -> DurableHostOutcomeReceipt:
    absent = _absent_snapshot()
    return build_durable_host_outcome_receipt(
        chain,
        lease,
        started_at_utc="2026-07-30T04:00:01Z",
        ended_at_utc="2026-07-30T04:00:02Z",
        termination_class="prelaunch_rejected",
        return_code=None,
        child_spawn_count=0,
        command_sha256=None,
        image_inspection_sha256=None,
        stdout_sha256=EMPTY_SHA256,
        stderr_sha256=sha256_bytes(b"rejected\n"),
        stdout_total_bytes=0,
        stderr_total_bytes=len(b"rejected\n"),
        stdout_captured_bytes=0,
        stderr_captured_bytes=len(b"rejected\n"),
        stdout_truncated=False,
        stderr_truncated=False,
        output_before=absent,
        output_after=absent,
    )


def test_persistent_lease_is_written_once_with_exact_identity(
    tmp_path: Path,
) -> None:
    root = _sandbox(tmp_path)
    chain, lease = _lease(root)
    result = persist_persistent_execution_lease_v2(root, chain, lease)
    target = root / EXECUTION_LEASE_V2_RELATIVE
    assert target.read_text(encoding="utf-8") == lease.canonical_json()
    assert result.relative_path == EXECUTION_LEASE_V2_RELATIVE.as_posix()
    assert result.byte_count == len(lease.canonical_json().encode("utf-8"))
    assert result.mode == 0o600
    assert verify_persisted_persistent_execution_lease_v2(
        root,
        chain,
        lease,
    ) == result


def test_persistent_lease_rejects_collision(tmp_path: Path) -> None:
    root = _sandbox(tmp_path)
    chain, lease = _lease(root)
    persist_persistent_execution_lease_v2(root, chain, lease)
    with pytest.raises(
        PersistentEvidenceChainV2ImplementationError,
        match="already exists",
    ):
        persist_persistent_execution_lease_v2(root, chain, lease)


@pytest.mark.parametrize(
    "relative",
    [
        Path("results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001"),
        LEGACY_EXECUTION_LEASE_RELATIVE,
        DURABLE_HOST_OUTCOME_RELATIVE,
    ],
)
def test_persistent_lease_rejects_preexisting_boundary_artifact(
    tmp_path: Path,
    relative: Path,
) -> None:
    root = _sandbox(tmp_path)
    chain, lease = _lease(root)
    target = root / relative
    if relative.suffix:
        target.write_text("occupied\n", encoding="utf-8")
    else:
        target.mkdir()
    with pytest.raises(
        PersistentEvidenceChainV2ImplementationError,
        match="already exists",
    ):
        persist_persistent_execution_lease_v2(root, chain, lease)


def test_persistent_lease_rejects_false_absence_claim(tmp_path: Path) -> None:
    root = _sandbox(tmp_path)
    chain, lease = _lease(root)
    invalid = replace(lease, output_root_absent_at_claim=False)
    with pytest.raises(
        PersistentEvidenceChainV2ImplementationError,
        match="output root existed",
    ):
        persist_persistent_execution_lease_v2(root, chain, invalid)


def test_outcome_requires_exact_persisted_lease(tmp_path: Path) -> None:
    root = _sandbox(tmp_path)
    chain, lease = _lease(root)
    receipt = _receipt(chain, lease)
    with pytest.raises(
        PersistentEvidenceChainV2ImplementationError,
        match="artifact is absent",
    ):
        persist_durable_host_outcome_receipt(root, chain, lease, receipt)


def test_outcome_rejects_tampered_persisted_lease(tmp_path: Path) -> None:
    root = _sandbox(tmp_path)
    chain, lease = _lease(root)
    persist_persistent_execution_lease_v2(root, chain, lease)
    target = root / EXECUTION_LEASE_V2_RELATIVE
    target.chmod(0o600)
    target.write_text("{}\n", encoding="utf-8")
    receipt = _receipt(chain, lease)
    with pytest.raises(
        PersistentEvidenceChainV2ImplementationError,
        match="bytes differ",
    ):
        persist_durable_host_outcome_receipt(root, chain, lease, receipt)


def test_durable_outcome_is_written_once_after_exact_lease(
    tmp_path: Path,
) -> None:
    root = _sandbox(tmp_path)
    chain, lease = _lease(root)
    receipt = _receipt(chain, lease)
    persist_persistent_execution_lease_v2(root, chain, lease)
    result = persist_durable_host_outcome_receipt(
        root,
        chain,
        lease,
        receipt,
    )
    target = root / DURABLE_HOST_OUTCOME_RELATIVE
    assert target.read_text(encoding="utf-8") == receipt.canonical_json()
    assert result.mode == 0o600
    assert verify_persisted_durable_host_outcome_receipt(
        root,
        chain,
        lease,
        receipt,
    ) == result
    with pytest.raises(
        PersistentEvidenceChainV2ImplementationError,
        match="already exists",
    ):
        persist_durable_host_outcome_receipt(root, chain, lease, receipt)


def test_symlinked_target_parent_is_rejected(tmp_path: Path) -> None:
    root = _sandbox(tmp_path)
    chain, lease = _lease(root)
    shutil.rmtree(root / "results")
    outside = tmp_path / "outside"
    (outside / "stage-3").mkdir(parents=True)
    (root / "results").symlink_to(outside, target_is_directory=True)
    with pytest.raises(
        PersistentEvidenceChainV2ImplementationError,
        match="not a real directory",
    ):
        persist_persistent_execution_lease_v2(root, chain, lease)


def test_failed_link_leaves_no_target_or_temporary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _sandbox(tmp_path)
    chain, lease = _lease(root)

    def fail_link(*_args: object, **_kwargs: object) -> None:
        raise OSError("injected link failure")

    monkeypatch.setattr(implementation.os, "link", fail_link)
    with pytest.raises(
        PersistentEvidenceChainV2ImplementationError,
        match="atomic write failed",
    ):
        persist_persistent_execution_lease_v2(root, chain, lease)
    target = root / EXECUTION_LEASE_V2_RELATIVE
    assert not target.exists()
    assert list(target.parent.glob(f".{target.name}.tmp-*")) == []


def test_supplied_chain_must_match_frozen_project_chain(tmp_path: Path) -> None:
    root = _sandbox(tmp_path)
    chain, lease = _lease(root)
    invalid_chain = replace(chain, recorded_at_utc="2026-07-30T04:10:00Z")
    with pytest.raises(PersistentEvidenceChainV2ImplementationError):
        persist_persistent_execution_lease_v2(root, invalid_chain, lease)



def test_tampered_implementation_source_is_rejected(tmp_path: Path) -> None:
    root = _sandbox(tmp_path)
    chain, lease = _lease(root)
    module = root / implementation.IMPLEMENTATION_MODULE_RELATIVE
    module.write_text(
        module.read_text(encoding="utf-8") + "# tampered\n",
        encoding="utf-8",
    )
    with pytest.raises(
        PersistentEvidenceChainV2ImplementationError,
        match="digest differs",
    ):
        persist_persistent_execution_lease_v2(root, chain, lease)

def test_persisted_mode_tampering_is_rejected(tmp_path: Path) -> None:
    root = _sandbox(tmp_path)
    chain, lease = _lease(root)
    persist_persistent_execution_lease_v2(root, chain, lease)
    target = root / EXECUTION_LEASE_V2_RELATIVE
    os.chmod(target, 0o644)
    with pytest.raises(
        PersistentEvidenceChainV2ImplementationError,
        match="mode differs",
    ):
        verify_persisted_persistent_execution_lease_v2(root, chain, lease)
