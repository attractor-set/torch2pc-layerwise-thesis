# Validate the QW-LC4-E runtime-operation identity repair.

from __future__ import annotations

import ast
import hashlib
import json
import shutil
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest

from torch2pc_thesis.stage3b_qwake_lc4_engineering_invocation_runtime_operation_identity_repair import (
    ADR_EN_RELATIVE,
    ADR_RU_RELATIVE,
    IDENTITY_REPAIR_ID,
    PACKAGE_RELATIVE,
    RECORD_RELATIVE,
    REPAIR_ADR_EN_RELATIVE,
    REPAIR_ADR_RU_RELATIVE,
    RUNTIME_OPERATION_MODULE_RELATIVE,
    RUNTIME_OPERATION_SHA256,
    RuntimeOperationIdentityRepairError,
    build_runtime_operation_identity_repair,
    load_runtime_operation_identity_repair,
    verify_runtime_operation_identity_repair,
)

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / PACKAGE_RELATIVE
RECORD = ROOT / RECORD_RELATIVE
SOURCE_REGISTRY = PACKAGE / "source-SHA256SUMS"
RUNTIME_MODULE = ROOT / RUNTIME_OPERATION_MODULE_RELATIVE
EXECUTION_LEASE = ROOT / (
    "results/stage-3/"
    "qwake-lc4-runtime-validation-v1-attempt-001.execution-lease.json"
)
OUTPUT_ROOT = ROOT / (
    "results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001"
)


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads(path.read_text(encoding="utf-8", errors="strict")),
    )


def _registry(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="strict").splitlines():
        digest, relative = line.split("  ", 1)
        result[relative] = "sha256:" + digest
    return result


def test_identity_repair_package_is_exact_and_self_hashed() -> None:
    assert sorted(path.name for path in PACKAGE.iterdir()) == [
        "SHA256SUMS",
        "repair.json",
        "source-SHA256SUMS",
    ]
    package_registry = _registry(PACKAGE / "SHA256SUMS")
    assert package_registry == {
        "repair.json": _sha256(RECORD),
        "source-SHA256SUMS": _sha256(SOURCE_REGISTRY),
    }
    repair = load_runtime_operation_identity_repair(RECORD)
    assert RECORD.read_text(encoding="utf-8") == repair.canonical_json()
    assert repair.repair_id == IDENTITY_REPAIR_ID
    assert repair.source.runtime_operation_sha256 == RUNTIME_OPERATION_SHA256


def test_identity_repair_binds_corrected_sources_and_historical_adrs() -> None:
    repair = verify_runtime_operation_identity_repair(ROOT)
    registry = _registry(SOURCE_REGISTRY)

    assert repair.bound_sources.runtime_operation_module_sha256 == _sha256(
        RUNTIME_MODULE
    )
    assert registry[repair.bound_sources.runtime_operation_module_path] == (
        repair.bound_sources.runtime_operation_module_sha256
    )
    assert repair.source.stale_runtime_operation_module_sha256 != (
        repair.bound_sources.runtime_operation_module_sha256
    )
    for relative in (ADR_RU_RELATIVE, ADR_EN_RELATIVE):
        assert repair.source.stale_runtime_operation_module_sha256 in (
            ROOT / relative
        ).read_text(encoding="utf-8")
    for relative in (REPAIR_ADR_RU_RELATIVE, REPAIR_ADR_EN_RELATIVE):
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert repair.repair_sha256 in text
        assert repair.bound_sources.runtime_operation_module_sha256 in text


def test_runtime_operation_verifier_requires_identity_repair_once() -> None:
    tree = ast.parse(RUNTIME_MODULE.read_text(encoding="utf-8"))
    verifier = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "verify_engineering_invocation_runtime_operation"
    )
    calls = [
        node.func.id
        for node in ast.walk(verifier)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    ]
    assert calls.count("verify_runtime_operation_identity_repair") == 1


def test_identity_repair_record_is_reconstructible() -> None:
    frozen = load_runtime_operation_identity_repair(RECORD)
    built = build_runtime_operation_identity_repair(
        recorded_at_utc=frozen.recorded_at_utc,
        bound_sources=frozen.bound_sources,
    )
    assert built == frozen


def test_identity_repair_rejects_stale_corrected_identity() -> None:
    repair = verify_runtime_operation_identity_repair(ROOT)
    with pytest.raises(
        RuntimeOperationIdentityRepairError,
        match="still has stale identity",
    ):
        replace(
            repair,
            bound_sources=replace(
                repair.bound_sources,
                runtime_operation_module_sha256=(
                    repair.source.stale_runtime_operation_module_sha256
                ),
            ),
        ).require()


def test_identity_repair_rejects_open_execution_gate() -> None:
    repair = verify_runtime_operation_identity_repair(ROOT)
    with pytest.raises(
        RuntimeOperationIdentityRepairError,
        match="gates differ",
    ):
        replace(
            repair,
            gates=replace(
                repair.gates,
                one_shot_engineering_invocation_permitted=True,
            ),
        ).require()


def test_identity_repair_rejects_source_registry_drift(tmp_path: Path) -> None:
    copied = tmp_path / "repo"
    shutil.copytree(ROOT, copied, symlinks=True)
    target = copied / RUNTIME_OPERATION_MODULE_RELATIVE
    target.write_text(
        target.read_text(encoding="utf-8") + "\n# synthetic drift\n",
        encoding="utf-8",
    )
    with pytest.raises(
        RuntimeOperationIdentityRepairError,
        match="repaired source SHA-256 differs",
    ):
        verify_runtime_operation_identity_repair(copied)


def test_identity_repair_rejects_package_registry_drift(tmp_path: Path) -> None:
    copied = tmp_path / "repo"
    shutil.copytree(ROOT, copied, symlinks=True)
    registry = copied / PACKAGE_RELATIVE / "SHA256SUMS"
    registry.write_text("0" * 64 + "  repair.json\n", encoding="utf-8")
    with pytest.raises(RuntimeOperationIdentityRepairError):
        verify_runtime_operation_identity_repair(copied)


def test_identity_repair_rejects_existing_effects(tmp_path: Path) -> None:
    copied = tmp_path / "repo"
    shutil.copytree(ROOT, copied, symlinks=True)
    lease = copied / EXECUTION_LEASE.relative_to(ROOT)
    lease.parent.mkdir(parents=True, exist_ok=True)
    lease.write_text("{}\n", encoding="utf-8")
    with pytest.raises(
        RuntimeOperationIdentityRepairError,
        match="execution lease",
    ):
        verify_runtime_operation_identity_repair(copied)


def test_identity_repair_preserves_closed_repository_boundary() -> None:
    verify_runtime_operation_identity_repair(ROOT)
    assert not EXECUTION_LEASE.exists()
    assert not OUTPUT_ROOT.exists()
    assert not tuple(OUTPUT_ROOT.parent.glob(f".{OUTPUT_ROOT.name}.staging-*"))


def test_identity_repair_documents_remaining_blockers() -> None:
    repair = verify_runtime_operation_identity_repair(ROOT)
    assert repair.gates.corrected_full_validation_receipt_present is False
    assert repair.gates.runtime_operation_identity_repair_merged is False
    assert repair.gates.latest_authorization_bound_in_persistent_lease is False
    assert repair.gates.durable_negative_host_outcome_defined is False
    assert repair.gates.final_execution_acknowledged is False
    assert repair.gates.one_shot_engineering_invocation_permitted is False


def test_identity_repair_source_registry_has_no_unbound_duplicates() -> None:
    registry = _registry(SOURCE_REGISTRY)
    assert len(registry) == len(set(registry))
    assert all(value.startswith("sha256:") for value in registry.values())
    assert _json(RECORD)["repair_sha256"].startswith("sha256:")
