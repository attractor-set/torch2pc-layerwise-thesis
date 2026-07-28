from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from torch2pc_thesis.stage3b_qwake_lc4_execution_admission import (
    AUTHORIZED_OUTPUT_ROOT,
    EXECUTION_LEASE_RELATIVE,
)
from torch2pc_thesis.stage3b_qwake_lc4_execution_freeze import (
    EXECUTION_FREEZE_REQUEST_ID,
    IMPLEMENTATION_HEAD_COMMIT,
    IMPLEMENTATION_MERGE_COMMIT,
    ONE_SHOT_ENTRYPOINT_ID,
    RUNTIME_BACKEND_CONTRACT_ID,
    QWakeLC4ExecutionFreezeError,
    build_execution_freeze_request,
    load_execution_freeze_request,
    validate_execution_freeze_request,
    verify_execution_freeze_prerequisites,
)

ROOT = Path(__file__).resolve().parents[2]
AUTHORING_ROOT = (
    ROOT
    / "experiments/frozen/"
    "stage3b-qwake-lc4-e-execution-freeze-authoring-v1"
)


def test_exact_merged_implementation_prerequisites() -> None:
    source = verify_execution_freeze_prerequisites(ROOT)

    assert source.implementation_merge_commit == IMPLEMENTATION_MERGE_COMMIT
    assert source.implementation_head_commit == IMPLEMENTATION_HEAD_COMMIT
    assert source.output_root == AUTHORIZED_OUTPUT_ROOT
    assert source.execution_lease_relative == (
        EXECUTION_LEASE_RELATIVE.as_posix()
    )
    assert source.authorized_cell_count == 168
    assert source.reserve_probe_count == 28
    assert source.lane_order == (
        "cpu_float64_engineering",
        "rocm_float32_canonical",
    )


def test_execution_freeze_request_round_trip(tmp_path: Path) -> None:
    request = build_execution_freeze_request(ROOT)
    validate_execution_freeze_request(request, ROOT)

    assert request.request_id == EXECUTION_FREEZE_REQUEST_ID
    assert request.runtime_backend_contract_id == (
        RUNTIME_BACKEND_CONTRACT_ID
    )
    assert request.one_shot_entrypoint_id == ONE_SHOT_ENTRYPOINT_ID
    assert request.execution_count == 1
    assert request.claim_and_execute_same_process_required is True
    assert request.no_retry_after_claim_required is True
    assert request.atomic_output_promotion_required is True
    assert request.canonical_backend_receipt_required is True

    request_path = tmp_path / "execution-freeze-request.json"
    request_path.write_text(request.canonical_json(), encoding="utf-8")
    assert load_execution_freeze_request(request_path) == request


def test_missing_backend_and_entrypoint_keep_execution_closed() -> None:
    request = build_execution_freeze_request(ROOT)

    assert request.concrete_runtime_backend_present is False
    assert request.one_shot_entrypoint_present is False
    assert request.immutable_execution_image_present is False
    assert request.execution_freeze_materialized is False
    assert request.execution_lease_materialized is False
    assert request.authorization_consumed is False
    assert request.runtime_execution_permitted is False
    assert request.runtime_execution_started is False
    assert request.runtime_execution_performed is False
    assert request.engineering_evidence_present is False
    assert request.scientific_execution_open is False
    assert request.test_dataset_access is False
    assert request.publication_permitted is False
    assert request.local_compute_execution_open is False


def test_tampered_execution_freeze_request_fails_closed() -> None:
    request = build_execution_freeze_request(ROOT)

    with pytest.raises(QWakeLC4ExecutionFreezeError):
        replace(
            request,
            concrete_runtime_backend_present=True,
        ).require()
    with pytest.raises(QWakeLC4ExecutionFreezeError):
        replace(
            request,
            one_shot_entrypoint_present=True,
        ).require()
    with pytest.raises(QWakeLC4ExecutionFreezeError):
        replace(
            request,
            runtime_execution_permitted=True,
        ).require()
    with pytest.raises(QWakeLC4ExecutionFreezeError):
        replace(
            request,
            request_sha256="sha256:" + "0" * 64,
        ).require()


def test_existing_repository_effects_block_authoring(
    tmp_path: Path,
) -> None:
    lease_root = tmp_path / "lease-case"
    lease_root.mkdir()
    lease_path = lease_root / EXECUTION_LEASE_RELATIVE
    lease_path.parent.mkdir(parents=True)
    lease_path.write_text("{}\n", encoding="utf-8")

    with pytest.raises(
        QWakeLC4ExecutionFreezeError,
        match="execution lease already exists",
    ):
        build_execution_freeze_request(lease_root)

    output_root = tmp_path / "output-case"
    output_path = output_root / AUTHORIZED_OUTPUT_ROOT
    output_path.mkdir(parents=True)

    with pytest.raises(
        QWakeLC4ExecutionFreezeError,
        match="runtime output already exists",
    ):
        build_execution_freeze_request(output_root)


def test_authoring_surfaces_expose_no_runtime_effects() -> None:
    module_path = (
        ROOT
        / "src/torch2pc_thesis/"
        "stage3b_qwake_lc4_execution_freeze.py"
    )
    script_path = (
        ROOT
        / "scripts/"
        "verify_stage3b_qwake_lc4_execution_freeze_authoring.py"
    )
    sources = (
        module_path.read_text(encoding="utf-8"),
        script_path.read_text(encoding="utf-8"),
    )
    combined = "\n".join(sources)

    forbidden_markers = (
        "def claim_execution_lease(",
        "def execute_authorized_runtime(",
        "def run_claimed_execution_wrapper(",
        "class RuntimeExecutionBackend",
        "os.open(",
        "subprocess.run(",
        "torch.save(",
        "docker compose run",
        "load_test_dataset",
        "write_engineering_evidence",
        "publish_result",
    )
    assert all(marker not in combined for marker in forbidden_markers)

    for source in sources:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = tuple(alias.name for alias in node.names)
                assert all(
                    name != "torch" and not name.startswith("torch.")
                    for name in imported
                )
            if isinstance(node, ast.ImportFrom):
                imported_from = node.module or ""
                assert (
                    imported_from != "torch"
                    and not imported_from.startswith("torch.")
                )

    assert "CONCRETE_RUNTIME_BACKEND_PRESENT=false" in sources[1]
    assert "ONE_SHOT_ENTRYPOINT_PRESENT=false" in sources[1]
    assert "EXECUTION_LEASE_MATERIALIZED=false" in sources[1]
    assert "RUNTIME_EXECUTION_PERFORMED=false" in sources[1]


def test_authoring_manifest_and_repository_documentation() -> None:
    registry = AUTHORING_ROOT / "SHA256SUMS"
    authoring = AUTHORING_ROOT / "authoring.json"

    assert registry.is_file()
    assert authoring.is_file()
    expected, relative = registry.read_text(
        encoding="utf-8"
    ).strip().split("  ", 1)
    assert relative == "authoring.json"
    assert hashlib.sha256(authoring.read_bytes()).hexdigest() == expected

    payload = json.loads(authoring.read_text(encoding="utf-8"))
    assert payload["authoring_id"] == (
        "stage3b-qwake-lc4-e-execution-freeze-authoring-v1"
    )
    assert payload["status"] == (
        "execution_freeze_contract_materialized_backend_and_lease_absent"
    )
    assert payload["source"]["base_commit"] == IMPLEMENTATION_MERGE_COMMIT
    assert payload["source"]["implementation_head_commit"] == (
        IMPLEMENTATION_HEAD_COMMIT
    )
    assert payload["gates"]["lease_wrapper_implementation_merged"] is True
    assert payload["gates"]["execution_freeze_branch_open"] is True
    assert (
        payload["gates"]["execution_freeze_contract_materialized"] is True
    )
    assert payload["gates"]["concrete_runtime_backend_present"] is False
    assert payload["gates"]["one_shot_entrypoint_present"] is False
    assert payload["gates"]["execution_freeze_materialized"] is False
    assert payload["gates"]["execution_lease_materialized"] is False
    assert payload["gates"]["qw_lc4_e_execution_permitted"] is False
    assert payload["gates"]["runtime_execution_started"] is False
    assert payload["gates"]["runtime_execution_performed"] is False
    assert payload["post_merge_next_slice"] == (
        "QW-LC4-E-runtime-backend-implementation"
    )

    marker = "ADR-068-stage3b-qwake-lc4-e-execution-freeze-authoring"
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

    for path in (ROOT / "STATUS.md", ROOT / "STATUS_EN.md"):
        text = path.read_text(encoding="utf-8")
        assert "EXECUTION_FREEZE_CONTRACT_MATERIALIZED=true" in text
        assert "CONCRETE_RUNTIME_BACKEND_PRESENT=false" in text
        assert "ONE_SHOT_ENTRYPOINT_PRESENT=false" in text
        assert "EXECUTION_FREEZE_MATERIALIZED=false" in text
        assert "EXECUTION_LEASE_MATERIALIZED=false" in text
        assert "QW_LC4_E_EXECUTION_PERMITTED=false" in text
