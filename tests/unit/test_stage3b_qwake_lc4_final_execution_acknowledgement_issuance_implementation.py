from __future__ import annotations

import ast
import shutil
from dataclasses import replace
from pathlib import Path

import pytest

from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_authoring import (
    DURABLE_HOST_OUTCOME_RELATIVE,
    EXECUTION_LEASE_V2_RELATIVE,
    FINAL_EXECUTION_OPERATOR_ACKNOWLEDGEMENT,
    load_final_execution_acknowledgement_authoring,
    load_wiring_merge_validation_receipt,
)
from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_issuance_authoring import (
    ACKNOWLEDGEMENT_RELATIVE,
    AUTHORING_MERGE_RECEIPT_RELATIVE,
    AUTHORING_RECORD_RELATIVE,
    UPSTREAM_AUTHORING_RECORD_RELATIVE,
    UPSTREAM_WIRING_RECEIPT_RELATIVE,
    build_prospective_acknowledgement_issuance,
    load_acknowledgement_authoring_merge_validation_receipt,
    load_final_execution_acknowledgement_issuance_authoring,
)
from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_issuance_implementation import (
    IMPLEMENTATION_ADR_EN_RELATIVE,
    IMPLEMENTATION_ADR_RU_RELATIVE,
    IMPLEMENTATION_MODULE_RELATIVE,
    IMPLEMENTATION_PACKAGE_RELATIVE,
    IMPLEMENTATION_RECORD_RELATIVE,
    IMPLEMENTATION_SOURCE_REGISTRY_RELATIVE,
    IMPLEMENTATION_TEST_RELATIVE,
    IMPLEMENTATION_VERIFIER_RELATIVE,
    LEGACY_EXECUTION_LEASE_RELATIVE,
    AcknowledgementIssuanceImplementationError,
    build_acknowledgement_issuance_authoring_merge_validation_receipt,
    build_frozen_acknowledgement_issuance_implementation_record,
    load_acknowledgement_issuance_authoring_merge_validation_receipt,
    load_acknowledgement_issuance_implementation_record,
    persist_final_execution_acknowledgement,
    verify_final_execution_acknowledgement_issuance_implementation,
    verify_persisted_final_execution_acknowledgement,
)

ROOT = Path(__file__).resolve().parents[2]


def _records():
    implementation_receipt = (
        load_acknowledgement_issuance_authoring_merge_validation_receipt(
            ROOT / IMPLEMENTATION_PACKAGE_RELATIVE / "authoring-merge-validation.json"
        )
    )
    implementation = load_acknowledgement_issuance_implementation_record(
        ROOT / IMPLEMENTATION_RECORD_RELATIVE,
        implementation_receipt,
    )
    authoring_receipt = load_acknowledgement_authoring_merge_validation_receipt(
        ROOT / AUTHORING_MERGE_RECEIPT_RELATIVE
    )
    authoring = load_final_execution_acknowledgement_issuance_authoring(
        ROOT / AUTHORING_RECORD_RELATIVE,
        authoring_receipt,
    )
    upstream_receipt = load_wiring_merge_validation_receipt(
        ROOT / UPSTREAM_WIRING_RECEIPT_RELATIVE
    )
    upstream_authoring = load_final_execution_acknowledgement_authoring(
        ROOT / UPSTREAM_AUTHORING_RECORD_RELATIVE,
        upstream_receipt,
    )
    issuance = build_prospective_acknowledgement_issuance(
        authoring,
        authoring_receipt,
        upstream_authoring,
        upstream_receipt,
        acknowledgement_phrase=FINAL_EXECUTION_OPERATOR_ACKNOWLEDGEMENT,
        operator_identity="operator@example.invalid",
        acknowledged_at_utc="2026-07-30T17:20:00Z",
        issuer_identity="issuer@example.invalid",
        issued_at_utc="2026-07-30T17:21:00Z",
    )
    return (
        implementation_receipt,
        implementation,
        authoring_receipt,
        authoring,
        upstream_receipt,
        upstream_authoring,
        issuance,
    )


def _copy_minimal_repository(tmp_path: Path) -> Path:
    copied = tmp_path / "repository"
    copied.mkdir()
    pending: list[Path] = [
        path.relative_to(ROOT)
        for path in (ROOT / IMPLEMENTATION_PACKAGE_RELATIVE).iterdir()
    ]
    pending.append(IMPLEMENTATION_SOURCE_REGISTRY_RELATIVE)
    copied_paths: set[Path] = set()

    while pending:
        relative = pending.pop()
        if relative in copied_paths:
            continue
        source = ROOT / relative
        target = copied / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied_paths.add(relative)

        if source.name not in {"SHA256SUMS", "source-SHA256SUMS"}:
            continue
        for line in source.read_text(encoding="utf-8").splitlines():
            _, entry = line.split("  ", 1)
            child = (
                relative.parent / entry
                if source.name == "SHA256SUMS"
                else Path(entry)
            )
            if child not in copied_paths:
                pending.append(child)

    (copied / "results/stage-3").mkdir(parents=True, exist_ok=True)
    return copied


def _persist(copied: Path):
    (
        _,
        _,
        authoring_receipt,
        authoring,
        upstream_receipt,
        upstream_authoring,
        issuance,
    ) = _records()
    result = persist_final_execution_acknowledgement(
        copied,
        authoring,
        authoring_receipt,
        upstream_authoring,
        upstream_receipt,
        issuance,
    )
    return (
        result,
        authoring_receipt,
        authoring,
        upstream_receipt,
        upstream_authoring,
        issuance,
    )


def test_frozen_records_are_exact() -> None:
    receipt, implementation, *_ = _records()
    assert receipt == build_acknowledgement_issuance_authoring_merge_validation_receipt()
    assert implementation == build_frozen_acknowledgement_issuance_implementation_record(
        receipt
    )
    assert implementation.gates.acknowledgement_issuance_implemented is True
    assert implementation.gates.final_execution_acknowledgement_issued is False


def test_complete_package_verifies_without_effects() -> None:
    result = verify_final_execution_acknowledgement_issuance_implementation(ROOT)
    assert result.gates.acknowledgement_issuance_implemented is True
    assert result.gates.final_execution_acknowledgement_issued is False
    assert not (ROOT / ACKNOWLEDGEMENT_RELATIVE).exists()
    assert not (ROOT / EXECUTION_LEASE_V2_RELATIVE).exists()
    assert not (ROOT / DURABLE_HOST_OUTCOME_RELATIVE).exists()


def test_writer_persists_exact_canonical_bytes(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    result, receipt, authoring, upstream_receipt, upstream_authoring, issuance = (
        _persist(copied)
    )
    target = copied / ACKNOWLEDGEMENT_RELATIVE
    expected = issuance.canonical_json(
        authoring,
        receipt,
        upstream_authoring,
        upstream_receipt,
    ).encode("utf-8")
    assert target.read_bytes() == expected
    assert result.relative_path == ACKNOWLEDGEMENT_RELATIVE.as_posix()
    assert result.byte_count == len(expected)
    assert result.mode == 0o600


def test_persisted_acknowledgement_verifies_exactly(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    result, receipt, authoring, upstream_receipt, upstream_authoring, issuance = (
        _persist(copied)
    )
    verified = verify_persisted_final_execution_acknowledgement(
        copied,
        authoring,
        receipt,
        upstream_authoring,
        upstream_receipt,
        issuance,
    )
    assert verified == result


def test_existing_acknowledgement_prevents_overwrite(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    _persist(copied)
    with pytest.raises(
        AcknowledgementIssuanceImplementationError,
        match="final execution acknowledgement already exists",
    ):
        _persist(copied)


@pytest.mark.parametrize(
    ("relative", "label"),
    (
        (Path("results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001"), "authorized output root"),
        (LEGACY_EXECUTION_LEASE_RELATIVE, "legacy execution lease"),
        (EXECUTION_LEASE_V2_RELATIVE, "persistent execution lease v2"),
        (DURABLE_HOST_OUTCOME_RELATIVE, "durable host outcome"),
    ),
)
def test_boundary_collision_fails_closed(
    tmp_path: Path,
    relative: Path,
    label: str,
) -> None:
    copied = _copy_minimal_repository(tmp_path)
    target = copied / relative
    if relative.suffix:
        target.write_text("{}\n", encoding="utf-8")
    else:
        target.mkdir()
    with pytest.raises(
        AcknowledgementIssuanceImplementationError,
        match=label,
    ):
        _persist(copied)


def test_symbolic_parent_chain_is_rejected(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    results = copied / "results"
    shutil.rmtree(results)
    real_results = copied / "real-results"
    (real_results / "stage-3").mkdir(parents=True)
    results.symlink_to(real_results, target_is_directory=True)
    with pytest.raises(
        AcknowledgementIssuanceImplementationError,
        match="parent is not a real directory",
    ):
        _persist(copied)


def test_stale_temporary_is_rejected(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    target = copied / ACKNOWLEDGEMENT_RELATIVE
    stale = target.parent / f".{target.name}.tmp-stale"
    stale.write_text("{}\n", encoding="utf-8")
    with pytest.raises(
        AcknowledgementIssuanceImplementationError,
        match="stale acknowledgement temporary exists",
    ):
        _persist(copied)


def test_success_cleans_temporary_files(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    _persist(copied)
    target = copied / ACKNOWLEDGEMENT_RELATIVE
    assert list(target.parent.glob(f".{target.name}.tmp-*")) == []


def test_tampered_persisted_bytes_are_rejected(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    _, receipt, authoring, upstream_receipt, upstream_authoring, issuance = _persist(
        copied
    )
    target = copied / ACKNOWLEDGEMENT_RELATIVE
    target.write_text("{}\n", encoding="utf-8")
    with pytest.raises(
        AcknowledgementIssuanceImplementationError,
        match="bytes differ",
    ):
        verify_persisted_final_execution_acknowledgement(
            copied,
            authoring,
            receipt,
            upstream_authoring,
            upstream_receipt,
            issuance,
        )


def test_wrong_persisted_mode_is_rejected(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    _, receipt, authoring, upstream_receipt, upstream_authoring, issuance = _persist(
        copied
    )
    target = copied / ACKNOWLEDGEMENT_RELATIVE
    target.chmod(0o644)
    with pytest.raises(
        AcknowledgementIssuanceImplementationError,
        match="mode differs",
    ):
        verify_persisted_final_execution_acknowledgement(
            copied,
            authoring,
            receipt,
            upstream_authoring,
            upstream_receipt,
            issuance,
        )


def test_supplied_issuance_identity_drift_is_rejected(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    (
        _,
        _,
        authoring_receipt,
        authoring,
        upstream_receipt,
        upstream_authoring,
        issuance,
    ) = _records()
    drifted = replace(issuance, acknowledgement_relative="wrong.json")
    with pytest.raises(
        AcknowledgementIssuanceImplementationError,
        match="prospective issuance differs",
    ):
        persist_final_execution_acknowledgement(
            copied,
            authoring,
            authoring_receipt,
            upstream_authoring,
            upstream_receipt,
            drifted,
        )


def test_source_registry_rejects_implementation_drift(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    target = copied / IMPLEMENTATION_MODULE_RELATIVE
    target.write_text(
        target.read_text(encoding="utf-8") + "\n# drift\n",
        encoding="utf-8",
    )
    with pytest.raises(
        AcknowledgementIssuanceImplementationError,
        match="registry target digest differs",
    ):
        verify_final_execution_acknowledgement_issuance_implementation(copied)


def test_repository_has_no_production_writer_callsite() -> None:
    target_name = "persist_final_execution_acknowledgement"
    for path in sorted((ROOT / "src").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        calls = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        assert target_name not in calls


def test_implementation_and_verifier_have_no_runtime_calls() -> None:
    forbidden = {
        "invoke_lease_bound_host_runtime",
        "invoke_one_shot_host_runtime",
        "inspect_local_image",
        "materialize_invocation_command",
        "persist_persistent_execution_lease_v2",
        "persist_durable_host_outcome_receipt",
    }
    for relative in (
        IMPLEMENTATION_MODULE_RELATIVE,
        IMPLEMENTATION_VERIFIER_RELATIVE,
    ):
        tree = ast.parse((ROOT / relative).read_text(encoding="utf-8"))
        call_names = set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr)
        assert call_names.isdisjoint(forbidden)
    assert (ROOT / IMPLEMENTATION_ADR_RU_RELATIVE).is_file()
    assert (ROOT / IMPLEMENTATION_ADR_EN_RELATIVE).is_file()
    assert (ROOT / IMPLEMENTATION_TEST_RELATIVE).is_file()
