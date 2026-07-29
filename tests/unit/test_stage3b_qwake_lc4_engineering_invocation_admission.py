# Validate the QW-LC4-E one-shot engineering invocation admission.

from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest

from torch2pc_thesis.stage3b_qwake_lc4_engineering_invocation_admission import (
    INVOCATION_ADMISSION_ID,
    INVOCATION_ADMISSION_STATUS,
    INVOCATION_BASE_COMMIT,
    QWakeLC4EngineeringInvocationAdmissionError,
    load_engineering_invocation_admission,
    verify_engineering_invocation_admission,
)

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-admission-v1"
)
RECORD = PACKAGE / "admission.json"
REGISTRY = PACKAGE / "SHA256SUMS"
MODULE = ROOT / (
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_engineering_invocation_admission.py"
)
VERIFIER = ROOT / (
    "scripts/verify_stage3b_qwake_lc4_engineering_invocation_admission.py"
)
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


def test_admission_package_is_exact_canonical_and_self_hashed() -> None:
    assert sorted(path.name for path in PACKAGE.iterdir()) == [
        "SHA256SUMS",
        "admission.json",
    ]
    expected, relative = REGISTRY.read_text(
        encoding="utf-8", errors="strict"
    ).strip().split("  ", 1)
    assert relative == "admission.json"
    assert _sha256(RECORD) == "sha256:" + expected

    admission = load_engineering_invocation_admission(RECORD)
    assert RECORD.read_text(encoding="utf-8") == admission.canonical_json()
    assert admission.admission_id == INVOCATION_ADMISSION_ID
    assert admission.status == INVOCATION_ADMISSION_STATUS
    assert admission.source.invocation_base_commit == INVOCATION_BASE_COMMIT


def test_admission_verifies_exact_frozen_sources() -> None:
    admission = verify_engineering_invocation_admission(ROOT)

    assert admission.source.repository_freeze_pr_number == 137
    assert admission.source.repository_freeze_head == (
        "cc287334a325f460555bab06725c52ba548985eb"
    )
    assert admission.source.repository_freeze_parent == (
        "da51c8d858c541372525125640db99062041fc20"
    )
    assert admission.source.invocation_authorization_sha256 == (
        "sha256:0a60dacc1bfd5073cf52d76f2ec33ae54f00899aad9877d44607199659fda75a"
    )
    assert admission.source.host_runtime_invoker_implementation_state_sha256 == (
        "sha256:1f5f31d4f220bbf074736f1de0b78a5dafa2849188ac337704d5cc704668fdf4"
    )
    assert admission.source.image_repo_digest.endswith(
        "7da92b8f77f6dc37d42db832c5613ef6149dc488adc5b66465faa33e48ca021d"
    )


def test_admission_keeps_runtime_preexecution_and_effect_gates_closed() -> None:
    admission = verify_engineering_invocation_admission(ROOT)

    assert admission.checks.repository_freeze_complete is True
    assert admission.checks.preexecution_identity_checks_implemented is True
    assert admission.checks.preexecution_identity_verified is False
    assert admission.gates.invocation_admission_record_present is True
    assert admission.gates.one_shot_engineering_invocation_slice_open is True
    assert admission.gates.one_shot_engineering_invocation_permitted is False
    assert admission.gates.branch_runtime_execution_permitted is False
    assert admission.gates.execution_lease_materialized is False
    assert admission.gates.authorization_consumed is False
    assert admission.gates.runtime_execution_started is False
    assert admission.gates.runtime_execution_performed is False
    assert admission.gates.image_inspection_performed is False
    assert admission.gates.docker_run_performed is False
    assert admission.gates.local_compute_execution_open is False
    assert not EXECUTION_LEASE.exists()
    assert not OUTPUT_ROOT.exists()
    assert not tuple(
        OUTPUT_ROOT.parent.glob(f".{OUTPUT_ROOT.name}.staging-*")
    )


def test_admission_rejects_open_effect_or_runtime_verification() -> None:
    admission = verify_engineering_invocation_admission(ROOT)

    with pytest.raises(
        QWakeLC4EngineeringInvocationAdmissionError,
        match="opened a runtime effect",
    ):
        replace(
            admission,
            gates=replace(
                admission.gates,
                one_shot_engineering_invocation_permitted=True,
            ),
        ).require()

    with pytest.raises(
        QWakeLC4EngineeringInvocationAdmissionError,
        match="verified during authoring",
    ):
        replace(
            admission,
            checks=replace(
                admission.checks,
                preexecution_identity_verified=True,
            ),
        ).require()


def test_admission_rejects_changed_source_identity() -> None:
    admission = verify_engineering_invocation_admission(ROOT)

    with pytest.raises(
        QWakeLC4EngineeringInvocationAdmissionError,
        match="source differs",
    ):
        replace(
            admission,
            source=replace(
                admission.source,
                invocation_base_commit="0" * 40,
            ),
        ).require()


def test_verifier_and_module_cannot_invoke_runtime() -> None:
    forbidden_calls = {
        "invoke_one_shot_host_runtime",
        "inspect_local_immutable_image",
        "materialize_one_shot_invocation",
        "claim_execution_lease",
        "execute_authorized_runtime",
        "run_one_shot_authorized_runtime",
        "Popen",
        "run",
    }
    for path in (MODULE, VERIFIER):
        tree = ast.parse(path.read_text(encoding="utf-8", errors="strict"))
        called = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        attributes = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        assert called.isdisjoint(forbidden_calls)
        assert attributes.isdisjoint(forbidden_calls)

    combined = MODULE.read_text(encoding="utf-8") + VERIFIER.read_text(
        encoding="utf-8"
    )
    for marker in (
        "docker image inspect",
        "docker run",
        "subprocess.Popen",
        "invoke_one_shot_host_runtime(",
    ):
        assert marker not in combined


def test_status_and_documentation_record_admission() -> None:
    marker = (
        "ADR-077-stage3b-qwake-lc4-e-one-shot-engineering-"
        "invocation-admission"
    )
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
        assert marker in path.read_text(encoding="utf-8", errors="strict")

    payload = _json(RECORD)
    assert payload["next_slice"] == (
        "QW-LC4-E-one-shot-engineering-invocation-admission-commit"
    )
    assert payload["post_merge_next_slice"] == (
        "QW-LC4-E-one-shot-engineering-invocation-operation"
    )
