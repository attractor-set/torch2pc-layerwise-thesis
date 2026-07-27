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
from torch2pc_thesis.stage3b_qwake_lc4_execution_wrapper import (
    ADMISSION_FREEZE_MERGE_COMMIT,
    AUTHORIZED_CELL_COUNT,
    EXECUTION_LEASE_ID,
    EXECUTION_LEASE_OPERATOR_ACKNOWLEDGEMENT,
    EXECUTION_WRAPPER_CONTRACT_ID,
    FROZEN_ADMISSION_SHA256,
    RESERVE_PROBE_COUNT,
    RUNTIME_LANE_ORDER,
    QWakeLC4ExecutionWrapperError,
    build_execution_wrapper_contract,
    build_prospective_execution_lease,
    load_execution_wrapper_contract,
    load_prospective_execution_lease,
    validate_execution_wrapper_contract,
    validate_prospective_execution_lease,
    verify_unconsumed_frozen_admission,
)

ROOT = Path(__file__).resolve().parents[2]
AUTHORING_ROOT = (
    ROOT
    / "experiments/frozen/"
    "stage3b-qwake-lc4-e-execution-lease-wrapper-authoring-v1"
)
WRAPPER_COMMIT = "a" * 40
CLAIMED_AT = "2026-07-27T21:30:00Z"


def _lease(project_root: Path):
    frozen = verify_unconsumed_frozen_admission(project_root)
    return frozen, build_prospective_execution_lease(
        frozen,
        claimed_at_utc=CLAIMED_AT,
        wrapper_commit=WRAPPER_COMMIT,
        operator_acknowledgement=(
            EXECUTION_LEASE_OPERATOR_ACKNOWLEDGEMENT
        ),
        output_root_absent_at_claim=True,
        execution_lease_absent_at_claim=True,
    )


def test_frozen_admission_and_runtime_matrix_are_exact() -> None:
    frozen = verify_unconsumed_frozen_admission(ROOT)

    assert frozen.freeze_merge_commit == ADMISSION_FREEZE_MERGE_COMMIT
    assert frozen.admission_sha256 == FROZEN_ADMISSION_SHA256
    assert frozen.output_root == AUTHORIZED_OUTPUT_ROOT
    assert frozen.execution_lease_relative == (
        EXECUTION_LEASE_RELATIVE.as_posix()
    )
    assert frozen.authorized_cell_count == AUTHORIZED_CELL_COUNT
    assert frozen.reserve_probe_count == RESERVE_PROBE_COUNT
    assert frozen.lane_order == RUNTIME_LANE_ORDER
    assert frozen.execution_count == 1
    assert frozen.runtime_execution_permitted is True
    assert frozen.authorization_consumed is False
    assert frozen.runtime_execution_started is False
    assert frozen.runtime_execution_performed is False


def test_prospective_lease_and_wrapper_round_trip(tmp_path: Path) -> None:
    frozen, lease = _lease(ROOT)
    validate_prospective_execution_lease(
        lease,
        frozen,
        ROOT,
        expected_wrapper_commit=WRAPPER_COMMIT,
    )
    contract = build_execution_wrapper_contract(lease)
    validate_execution_wrapper_contract(contract, lease)

    assert lease.lease_id == EXECUTION_LEASE_ID
    assert lease.authorization_consumed is True
    assert lease.runtime_execution_permitted is True
    assert lease.runtime_execution_started is False
    assert lease.runtime_execution_performed is False
    assert contract.contract_id == EXECUTION_WRAPPER_CONTRACT_ID
    assert contract.authorized_cell_count == AUTHORIZED_CELL_COUNT
    assert contract.reserve_probe_count == RESERVE_PROBE_COUNT
    assert contract.exclusive_atomic_lease_claim_required is True
    assert contract.lease_persists_after_failure is True
    assert contract.retry_after_claim_permitted is False
    assert contract.atomic_output_promotion_required is True

    lease_path = tmp_path / "prospective-lease.json"
    contract_path = tmp_path / "wrapper-contract.json"
    lease_path.write_text(lease.canonical_json(), encoding="utf-8")
    contract_path.write_text(contract.canonical_json(), encoding="utf-8")

    assert load_prospective_execution_lease(lease_path) == lease
    assert load_execution_wrapper_contract(contract_path) == contract


def test_existing_output_or_lease_fails_closed(tmp_path: Path) -> None:
    frozen, lease = _lease(ROOT)
    output_root = tmp_path / AUTHORIZED_OUTPUT_ROOT
    output_root.mkdir(parents=True)

    with pytest.raises(
        QWakeLC4ExecutionWrapperError,
        match="output root already exists",
    ):
        validate_prospective_execution_lease(
            lease,
            frozen,
            tmp_path,
            expected_wrapper_commit=WRAPPER_COMMIT,
        )

    lease_root = tmp_path / "lease-case"
    lease_path = lease_root / EXECUTION_LEASE_RELATIVE
    lease_path.parent.mkdir(parents=True)
    lease_path.write_text("{}\n", encoding="utf-8")

    with pytest.raises(
        QWakeLC4ExecutionWrapperError,
        match="execution lease already exists",
    ):
        validate_prospective_execution_lease(
            lease,
            frozen,
            lease_root,
            expected_wrapper_commit=WRAPPER_COMMIT,
        )


def test_tampered_prospective_records_fail_closed() -> None:
    _, lease = _lease(ROOT)
    contract = build_execution_wrapper_contract(lease)

    with pytest.raises(QWakeLC4ExecutionWrapperError):
        replace(lease, authorization_consumed=False).require()
    with pytest.raises(QWakeLC4ExecutionWrapperError):
        replace(lease, runtime_execution_started=True).require()
    with pytest.raises(QWakeLC4ExecutionWrapperError):
        replace(contract, retry_after_claim_permitted=True).require()
    with pytest.raises(QWakeLC4ExecutionWrapperError):
        replace(contract, runtime_execution_performed=True).require()


def test_authoring_surfaces_expose_no_effectful_executor() -> None:
    module_path = (
        ROOT
        / "src/torch2pc_thesis/"
        "stage3b_qwake_lc4_execution_wrapper.py"
    )
    script_path = (
        ROOT
        / "scripts/"
        "verify_stage3b_qwake_lc4_execution_wrapper_authoring.py"
    )
    sources = (
        module_path.read_text(encoding="utf-8"),
        script_path.read_text(encoding="utf-8"),
    )
    combined = "\n".join(sources)

    forbidden_markers = (
        "def claim_execution_lease(",
        "def execute_runtime(",
        "def run_runtime_execution(",
        "os.open(",
        "subprocess.run(",
        "torch.save(",
        "docker compose run",
        "write_result",
        "publish_result",
        "load_test_dataset",
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

    assert "EXECUTION_LEASE_MATERIALIZED=false" in sources[1]
    assert "RUNTIME_EXECUTOR_PRESENT=false" in sources[1]
    assert "RUNTIME_EXECUTION_STARTED=false" in sources[1]
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
        "stage3b-qwake-lc4-e-execution-lease-wrapper-authoring-v1"
    )
    assert payload["status"] == (
        "lease_wrapper_contracts_materialized_effects_closed"
    )
    assert payload["source"]["base_commit"] == (
        "12b7d24153a681f731a43e8497275016ad4e1656"
    )
    assert payload["gates"]["admission_freeze_merged"] is True
    assert payload["gates"]["execution_lease_schema_implemented"] is True
    assert payload["gates"]["execution_wrapper_contract_implemented"] is True
    assert payload["gates"]["execution_lease_materialized"] is False
    assert payload["gates"]["runtime_executor_present"] is False
    assert payload["gates"]["qw_lc4_e_execution_permitted"] is False
    assert payload["gates"]["authorization_consumed"] is False
    assert payload["gates"]["runtime_execution_started"] is False
    assert payload["gates"]["runtime_execution_performed"] is False

    marker = "ADR-066-stage3b-qwake-lc4-e-execution-lease-wrapper-authoring"
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
        assert "EXECUTION_LEASE_SCHEMA_IMPLEMENTED=true" in text
        assert "EXECUTION_WRAPPER_CONTRACT_IMPLEMENTED=true" in text
        assert "EXECUTION_LEASE_MATERIALIZED=false" in text
        assert "RUNTIME_EXECUTOR_PRESENT=false" in text
        assert "QW_LC4_E_EXECUTION_PERMITTED=false" in text
        assert "AUTHORIZATION_CONSUMED=false" in text
        assert "RUNTIME_EXECUTION_STARTED=false" in text
        assert "RUNTIME_EXECUTION_PERFORMED=false" in text
