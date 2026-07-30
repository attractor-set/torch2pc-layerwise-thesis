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
    UPSTREAM_AUTHORING_RECORD_RELATIVE,
    UPSTREAM_WIRING_RECEIPT_RELATIVE,
    load_acknowledgement_authoring_merge_validation_receipt,
    load_final_execution_acknowledgement_issuance_authoring,
)
from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_issuance_authoring import (
    AUTHORING_MERGE_RECEIPT_RELATIVE as ISSUANCE_AUTHORING_MERGE_RECEIPT_RELATIVE,
)
from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_issuance_authoring import (
    AUTHORING_RECORD_RELATIVE as ISSUANCE_AUTHORING_RECORD_RELATIVE,
)
from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_issuance_implementation import (
    LEGACY_EXECUTION_LEASE_RELATIVE,
)
from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_materialization import (
    IMPLEMENTATION_ADR_EN_RELATIVE,
    IMPLEMENTATION_ADR_RU_RELATIVE,
    IMPLEMENTATION_MODULE_RELATIVE,
    IMPLEMENTATION_PACKAGE_RELATIVE,
    IMPLEMENTATION_RECORD_RELATIVE,
    IMPLEMENTATION_SOURCE_REGISTRY_RELATIVE,
    IMPLEMENTATION_TEST_RELATIVE,
    IMPLEMENTATION_VERIFIER_RELATIVE,
    FinalExecutionAcknowledgementMaterializationImplementationError,
    build_frozen_acknowledgement_materialization_implementation_record,
    build_materialization_authoring_merge_validation_receipt,
    load_acknowledgement_materialization_authoring_merge_validation_receipt,
    load_final_execution_acknowledgement_materialization_implementation_record,
    materialize_final_execution_acknowledgement,
    verify_final_execution_acknowledgement_materialization_implementation,
)
from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_materialization_authoring import (
    AUTHORING_RECORD_RELATIVE as MATERIALIZATION_AUTHORING_RECORD_RELATIVE,
)
from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_materialization_authoring import (
    IMPLEMENTATION_MERGE_RECEIPT_RELATIVE as MATERIALIZATION_AUTHORING_MERGE_RECEIPT_RELATIVE,
)
from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_materialization_authoring import (
    build_prospective_acknowledgement_materialization,
    load_acknowledgement_issuance_implementation_merge_validation_receipt,
    load_final_execution_acknowledgement_materialization_authoring,
)

ROOT = Path(__file__).resolve().parents[2]


def _records():
    implementation_receipt = (
        load_acknowledgement_materialization_authoring_merge_validation_receipt(
            ROOT / IMPLEMENTATION_PACKAGE_RELATIVE / "authoring-merge-validation.json"
        )
    )
    implementation = (
        load_final_execution_acknowledgement_materialization_implementation_record(
            ROOT / IMPLEMENTATION_RECORD_RELATIVE,
            implementation_receipt,
        )
    )
    authoring_receipt = (
        load_acknowledgement_issuance_implementation_merge_validation_receipt(
            ROOT / MATERIALIZATION_AUTHORING_MERGE_RECEIPT_RELATIVE
        )
    )
    authoring = load_final_execution_acknowledgement_materialization_authoring(
        ROOT / MATERIALIZATION_AUTHORING_RECORD_RELATIVE,
        authoring_receipt,
    )
    issuance_receipt = load_acknowledgement_authoring_merge_validation_receipt(
        ROOT / ISSUANCE_AUTHORING_MERGE_RECEIPT_RELATIVE
    )
    issuance_authoring = load_final_execution_acknowledgement_issuance_authoring(
        ROOT / ISSUANCE_AUTHORING_RECORD_RELATIVE,
        issuance_receipt,
    )
    upstream_receipt = load_wiring_merge_validation_receipt(
        ROOT / UPSTREAM_WIRING_RECEIPT_RELATIVE
    )
    upstream_authoring = load_final_execution_acknowledgement_authoring(
        ROOT / UPSTREAM_AUTHORING_RECORD_RELATIVE,
        upstream_receipt,
    )
    materialization = build_prospective_acknowledgement_materialization(
        authoring,
        authoring_receipt,
        issuance_authoring,
        issuance_receipt,
        upstream_authoring,
        upstream_receipt,
        acknowledgement_phrase=FINAL_EXECUTION_OPERATOR_ACKNOWLEDGEMENT,
        operator_identity="operator@example.invalid",
        acknowledged_at_utc="2026-07-30T21:05:00Z",
        issuer_identity="issuer@example.invalid",
        issued_at_utc="2026-07-30T21:06:00Z",
        materializer_identity="issuer@example.invalid",
        materialized_at_utc="2026-07-30T21:07:00Z",
    )
    return (
        implementation_receipt,
        implementation,
        authoring_receipt,
        authoring,
        issuance_receipt,
        issuance_authoring,
        upstream_receipt,
        upstream_authoring,
        materialization,
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
            child = relative.parent / entry if source.name == "SHA256SUMS" else Path(entry)
            if child not in copied_paths:
                pending.append(child)

    (copied / "results/stage-3").mkdir(parents=True, exist_ok=True)
    return copied


def _materialize(copied: Path, materialization_override=None):
    (
        _,
        _,
        authoring_receipt,
        authoring,
        issuance_receipt,
        issuance_authoring,
        upstream_receipt,
        upstream_authoring,
        materialization,
    ) = _records()
    selected = materialization if materialization_override is None else materialization_override
    result = materialize_final_execution_acknowledgement(
        copied,
        authoring,
        authoring_receipt,
        issuance_authoring,
        issuance_receipt,
        upstream_authoring,
        upstream_receipt,
        selected,
    )
    return result, materialization


def test_frozen_records_are_exact() -> None:
    receipt, implementation, *_ = _records()
    assert receipt == build_materialization_authoring_merge_validation_receipt()
    assert implementation == (
        build_frozen_acknowledgement_materialization_implementation_record(receipt)
    )
    assert implementation.gates.acknowledgement_materialization_implemented is True
    assert implementation.gates.final_execution_acknowledgement_issued is False


def test_complete_package_verifies_without_effects() -> None:
    result = verify_final_execution_acknowledgement_materialization_implementation(ROOT)
    assert result.gates.acknowledgement_materialization_implemented is True
    assert result.gates.final_execution_acknowledgement_issued is False
    assert not (ROOT / ACKNOWLEDGEMENT_RELATIVE).exists()
    assert not (ROOT / EXECUTION_LEASE_V2_RELATIVE).exists()
    assert not (ROOT / DURABLE_HOST_OUTCOME_RELATIVE).exists()


def test_explicit_materializer_persists_and_reverifies_exact_bytes(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    result, materialization = _materialize(copied)
    target = copied / ACKNOWLEDGEMENT_RELATIVE
    records = _records()
    expected = materialization.issuance.canonical_json(
        records[5],
        records[4],
        records[7],
        records[6],
    ).encode("utf-8")
    assert target.read_bytes() == expected
    assert result.relative_path == ACKNOWLEDGEMENT_RELATIVE.as_posix()
    assert result.byte_count == len(target.read_bytes())
    assert result.mode == 0o600
    assert result.exact_persisted_bytes_verified is True
    assert result.final_execution_acknowledgement_issued is True
    assert result.one_shot_engineering_invocation_permitted is False


def test_materializer_does_not_create_other_runtime_artifacts(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    _materialize(copied)
    assert not (copied / LEGACY_EXECUTION_LEASE_RELATIVE).exists()
    assert not (copied / EXECUTION_LEASE_V2_RELATIVE).exists()
    assert not (copied / DURABLE_HOST_OUTCOME_RELATIVE).exists()


def test_second_materialization_is_rejected(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    _materialize(copied)
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationImplementationError,
        match="final execution acknowledgement already exists",
    ):
        _materialize(copied)


def test_materializer_identity_drift_is_rejected(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    materialization = _records()[-1]
    drifted = replace(materialization, materializer_identity="other@example.invalid")
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationImplementationError,
        match="materializer identity differs",
    ):
        _materialize(copied, drifted)


def test_materialization_timestamp_drift_is_rejected(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    materialization = _records()[-1]
    drifted = replace(materialization, materialized_at_utc="2026-07-30T21:05:30Z")
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationImplementationError,
        match="materialization timestamp is before issuance",
    ):
        _materialize(copied, drifted)


@pytest.mark.parametrize(
    ("relative", "label"),
    (
        (
            Path("results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001"),
            "authorized output root",
        ),
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
        FinalExecutionAcknowledgementMaterializationImplementationError,
        match=label,
    ):
        _materialize(copied)


def test_symbolic_parent_chain_is_rejected(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    results = copied / "results"
    shutil.rmtree(results)
    real_results = copied / "real-results"
    (real_results / "stage-3").mkdir(parents=True)
    results.symlink_to(real_results, target_is_directory=True)
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationImplementationError,
        match="parent is not a real directory",
    ):
        _materialize(copied)


def test_source_registry_rejects_implementation_drift(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    target = copied / IMPLEMENTATION_MODULE_RELATIVE
    target.write_text(
        target.read_text(encoding="utf-8") + "\n# drift\n",
        encoding="utf-8",
    )
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationImplementationError,
        match="registry target digest differs",
    ):
        verify_final_execution_acknowledgement_materialization_implementation(copied)


def test_repository_has_no_production_materializer_callsite() -> None:
    target_name = "materialize_final_execution_acknowledgement"
    for path in sorted((ROOT / "src").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        calls = set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name):
                calls.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr)
        assert target_name not in calls


def test_implementation_has_one_writer_and_one_reverification_call() -> None:
    tree = ast.parse((ROOT / IMPLEMENTATION_MODULE_RELATIVE).read_text(encoding="utf-8"))
    calls: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            calls.append(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            calls.append(node.func.attr)
    assert calls.count("_persist_acknowledgement_once") == 1
    assert calls.count("_verify_persisted_acknowledgement_once") == 1


def test_implementation_and_verifier_have_no_runtime_calls() -> None:
    forbidden = {
        "invoke_lease_bound_host_runtime",
        "invoke_one_shot_host_runtime",
        "inspect_local_image",
        "materialize_invocation_command",
        "persist_persistent_execution_lease_v2",
        "persist_durable_host_outcome_receipt",
    }
    for relative in (IMPLEMENTATION_MODULE_RELATIVE, IMPLEMENTATION_VERIFIER_RELATIVE):
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
