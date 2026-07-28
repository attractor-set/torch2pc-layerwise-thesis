from __future__ import annotations

import ast
import json
from dataclasses import asdict
from pathlib import Path

import pytest

import torch2pc_thesis.stage3b_qwake_lc4_runtime_backend as backend_module
from torch2pc_thesis.stage3b_qwake_lc4_bounded import BoundedArm
from torch2pc_thesis.stage3b_qwake_lc4_execution_admission import (
    AUTHORIZED_OUTPUT_ROOT,
    EXECUTION_LEASE_RELATIVE,
)
from torch2pc_thesis.stage3b_qwake_lc4_execution_wrapper import (
    EXECUTION_LEASE_OPERATOR_ACKNOWLEDGEMENT,
    FROZEN_ADMISSION_SHA256,
    FROZEN_AUTHORIZATION_SHA256,
    FROZEN_TORCH2PC_COMMIT,
    build_execution_wrapper_contract,
    build_prospective_execution_lease,
    sha256_object,
    verify_unconsumed_frozen_admission,
)
from torch2pc_thesis.stage3b_qwake_lc4_runtime_backend import (
    AUTHORING_HEAD_COMMIT,
    AUTHORING_MERGE_COMMIT,
    AUTHORING_REQUEST_SHA256,
    MATERIALIZED_EXECUTION_FREEZE_ID,
    MATERIALIZED_EXECUTION_FREEZE_STATUS,
    ONE_SHOT_ENTRYPOINT_ID,
    RUNTIME_BACKEND_ID,
    RUNTIME_BACKEND_IMPLEMENTATION_ID,
    RUNTIME_BACKEND_IMPLEMENTATION_STATUS,
    ArmExecutionRecord,
    MaterializedExecutionFreeze,
    QWakeLC4RuntimeBackend,
    QWakeLC4RuntimeBackendError,
    ReserveProbeRecord,
    RuntimeCellRecord,
    RuntimeMatrixExecutor,
    RuntimeMatrixResult,
    execute_bounded_runtime_cell,
    inspect_runtime_frontier_normalization,
    run_one_shot_authorized_runtime,
    verify_materialized_execution_freeze,
)
from torch2pc_thesis.stage3b_qwake_lc4_runtime_freeze import (
    RUNTIME_CANDIDATE_INDICES,
    RuntimeArmOrder,
    RuntimeLane,
    load_runtime_authorization,
    runtime_authorization_cells,
)

ROOT = Path(__file__).resolve().parents[2]
IMPLEMENTATION_ROOT = (
    ROOT
    / "experiments/frozen/"
    "stage3b-qwake-lc4-e-runtime-backend-implementation-v1"
)
WRAPPER_COMMIT = "a" * 40


def _sha(character: str) -> str:
    return f"sha256:{character * 64}"


def _freeze() -> MaterializedExecutionFreeze:
    payload: dict[str, object] = {
        "schema_version": 1,
        "freeze_id": MATERIALIZED_EXECUTION_FREEZE_ID,
        "status": MATERIALIZED_EXECUTION_FREEZE_STATUS,
        "source_commit": WRAPPER_COMMIT,
        "wrapper_commit": WRAPPER_COMMIT,
        "torch2pc_commit": FROZEN_TORCH2PC_COMMIT,
        "image_digest": _sha("1"),
        "image_repo_digest": "example.invalid/repo@" + _sha("1"),
        "backend_id": RUNTIME_BACKEND_ID,
        "backend_module_path": (
            "src/torch2pc_thesis/stage3b_qwake_lc4_runtime_backend.py"
        ),
        "backend_module_sha256": _sha("2"),
        "entrypoint_id": ONE_SHOT_ENTRYPOINT_ID,
        "entrypoint_path": (
            "scripts/run_stage3b_qwake_lc4_authorized_runtime.py"
        ),
        "entrypoint_sha256": _sha("3"),
        "authoring_request_id": (
            "stage3b-qwake-lc4-e-execution-freeze-request-v1"
        ),
        "authoring_request_sha256": AUTHORING_REQUEST_SHA256,
        "admission_sha256": FROZEN_ADMISSION_SHA256,
        "authorization_sha256": FROZEN_AUTHORIZATION_SHA256,
        "execution_count": 1,
        "concrete_runtime_backend_present": True,
        "one_shot_entrypoint_present": True,
        "immutable_execution_image_present": True,
        "execution_freeze_materialized": True,
        "runtime_execution_permitted": True,
        "execution_lease_materialized": False,
        "authorization_consumed": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "engineering_evidence_present": False,
        "scientific_execution_open": False,
        "test_dataset_access": False,
        "publication_permitted": False,
        "local_compute_execution_open": False,
    }
    return MaterializedExecutionFreeze(
        **payload,
        freeze_sha256=sha256_object(payload),
    )


def _arm(arm: BoundedArm, token: str) -> ArmExecutionRecord:
    return ArmExecutionRecord(
        arm=arm.value,
        action_id=(
            "complete_suffix_stage2_baseline_v1"
            if arm is BoundedArm.EXACT_REFERENCE
            else "fixedpred_eta1_wavefront_completion_v1"
        ),
        canonical_response_sha256=_sha(token),
        component_manifest_sha256=_sha(token),
        rng_before_sha256=_sha("4"),
        rng_after_sha256=_sha("5"),
        vjp_count=1,
        fallback_invoked=False,
        cost_fields=(("compute_primary_time_ns", 1),),
    )


def _cell_record(position: int, cell) -> RuntimeCellRecord:
    exact = _arm(BoundedArm.EXACT_REFERENCE, "6")
    analytic = _arm(BoundedArm.ANALYTIC_CANDIDATE, "6")
    order = (
        (BoundedArm.EXACT_REFERENCE, BoundedArm.ANALYTIC_CANDIDATE)
        if cell.arm_order is RuntimeArmOrder.EXACT_THEN_ANALYTIC
        else (BoundedArm.ANALYTIC_CANDIDATE, BoundedArm.EXACT_REFERENCE)
    )
    payload: dict[str, object] = {
        "position": position,
        "lane": cell.lane.value,
        "candidate_index": cell.candidate_index,
        "repeat_index": cell.repeat_index,
        "arm_order": tuple(item.value for item in order),
        "opaque_state_ref": _sha("7"),
        "exact_reference": asdict(exact),
        "analytic_candidate": asdict(analytic),
        "response_defect": 0.0,
        "response_passed": True,
        "structural_equal": True,
        "rng_post_match": True,
    }
    return RuntimeCellRecord(
        position=position,
        lane=cell.lane.value,
        candidate_index=cell.candidate_index,
        repeat_index=cell.repeat_index,
        arm_order=tuple(item.value for item in order),
        opaque_state_ref=_sha("7"),
        exact_reference=exact,
        analytic_candidate=analytic,
        response_defect=0.0,
        response_passed=True,
        structural_equal=True,
        rng_post_match=True,
        cell_sha256=sha256_object(payload),
    )


def _probe(position: int, lane: RuntimeLane, candidate: int, placement: str):
    completed = tuple(range(candidate + 1, 7))
    payload: dict[str, object] = {
        "position": position,
        "lane": lane.value,
        "candidate_index": candidate,
        "placement": placement,
        "opaque_state_ref": _sha("7"),
        "completed_suffix_indices": completed,
        "no_skipped_indices": True,
        "no_duplicate_indices": True,
        "fallback_available": True,
        "fallback_invoked": True,
        "fallback_completed": True,
        "fallback_response_sha256": _sha("8"),
        "direct_reference_response_sha256": _sha("8"),
        "rng_post_sha256": _sha("9"),
        "passed": True,
    }
    return ReserveProbeRecord(
        position=position,
        lane=lane.value,
        candidate_index=candidate,
        placement=placement,
        opaque_state_ref=_sha("7"),
        completed_suffix_indices=completed,
        no_skipped_indices=True,
        no_duplicate_indices=True,
        fallback_available=True,
        fallback_invoked=True,
        fallback_completed=True,
        fallback_response_sha256=_sha("8"),
        direct_reference_response_sha256=_sha("8"),
        rng_post_sha256=_sha("9"),
        passed=True,
        probe_sha256=sha256_object(payload),
    )


class _FakeMatrixExecutor(RuntimeMatrixExecutor):
    def execute(self, authorization) -> RuntimeMatrixResult:
        cells = tuple(
            _cell_record(position, cell)
            for position, cell in enumerate(authorization.cells)
        )
        probes = []
        position = 0
        for lane in RuntimeLane:
            for candidate in RUNTIME_CANDIDATE_INDICES:
                probes.append(_probe(position, lane, candidate, "before_repeat_zero"))
                position += 1
                probes.append(
                    _probe(position, lane, candidate, "after_repeat_eleven")
                )
                position += 1
        aggregates_list: list[dict[str, object]] = []
        for aggregate_position, (lane, candidate) in enumerate(
            (lane, candidate)
            for lane in RuntimeLane
            for candidate in RUNTIME_CANDIDATE_INDICES
        ):
            normalization_payload: dict[str, object] = {
                "lane": lane.value,
                "candidate_index": candidate,
                "normalized_indices": (),
                "maximum_absolute_defect": 0.0,
                "absolute_tolerance": 1.0e-12,
                "relative_tolerance": 1.0e-10,
                "raw_frontier_sha256": _sha("b"),
                "canonical_frontier_sha256": _sha("b"),
                "normalization_applied": False,
            }
            normalization_payload["normalization_sha256"] = sha256_object(
                normalization_payload
            )
            aggregate_payload: dict[str, object] = {
                "lane": lane.value,
                "candidate_index": candidate,
                "opaque_state_ref": cells[
                    aggregate_position * 12
                ].opaque_state_ref,
                "aggregate_id": "stage3b-qwake-paired-aggregation-v1",
                "field_summaries": (
                    (
                        "compute_primary_time_ns",
                        {
                            "median_paired_delta": 0.0,
                            "q1_paired_delta": 0.0,
                            "q3_paired_delta": 0.0,
                            "minimum_paired_delta": 0,
                            "maximum_paired_delta": 0,
                        },
                    ),
                ),
                "order_effect_passed": True,
                "pair_complete": True,
                "frontier_normalization": normalization_payload,
            }
            aggregate_payload["aggregate_sha256"] = sha256_object(
                aggregate_payload
            )
            aggregates_list.append(aggregate_payload)
        aggregates = tuple(aggregates_list)
        result = RuntimeMatrixResult(
            cells=cells,
            reserve_probes=tuple(probes),
            aggregates=aggregates,
        )
        result.require(authorization)
        return result


def test_runtime_backend_identity_and_no_import_effects() -> None:
    assert RUNTIME_BACKEND_IMPLEMENTATION_ID == (
        "stage3b-qwake-lc4-e-runtime-backend-implementation-v1"
    )
    assert RUNTIME_BACKEND_IMPLEMENTATION_STATUS == (
        "bounded_backend_and_entrypoint_materialized_execution_not_open"
    )
    assert AUTHORING_MERGE_COMMIT == (
        "49d691d497f4f719e82b271e9b9d441f9e4dfa63"
    )
    assert AUTHORING_HEAD_COMMIT == (
        "1bad6419f3e413353f922d4ac2190bb5c52ac865"
    )
    assert not (ROOT / EXECUTION_LEASE_RELATIVE).exists()
    assert not (ROOT / AUTHORIZED_OUTPUT_ROOT).exists()


def test_cpu_frontier_roundoff_normalization_is_bounded() -> None:
    records = tuple(
        inspect_runtime_frontier_normalization(
            RuntimeLane.CPU_FLOAT64_ENGINEERING, candidate
        )
        for candidate in RUNTIME_CANDIDATE_INDICES
    )
    assert tuple(record.candidate_index for record in records) == (
        RUNTIME_CANDIDATE_INDICES
    )
    assert all(record.maximum_absolute_defect <= 1.0e-12 for record in records)
    assert all(record.absolute_tolerance == 1.0e-12 for record in records)
    assert all(record.relative_tolerance == 1.0e-10 for record in records)
    assert records[0].normalization_applied is False
    assert records[1].normalization_applied is False
    assert all(record.normalization_applied for record in records[2:])
    assert all(
        record.raw_frontier_sha256 != record.canonical_frontier_sha256
        for record in records[2:]
    )


def test_one_cpu_bounded_cell_matches_required_response() -> None:
    cell = runtime_authorization_cells()[2 * 12]
    assert cell.lane is RuntimeLane.CPU_FLOAT64_ENGINEERING
    record = execute_bounded_runtime_cell(cell)
    assert record.candidate_index == 2
    assert record.response_passed is True
    assert record.structural_equal is True
    assert record.rng_post_match is True
    assert record.response_defect <= 1.0
    assert (
        record.exact_reference.canonical_response_sha256
        != record.analytic_candidate.canonical_response_sha256
    )


def test_backend_writes_complete_regular_output_tree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    freeze = _freeze()
    monkeypatch.setattr(
        backend_module,
        "verify_materialized_execution_freeze",
        lambda _root: freeze,
    )
    monkeypatch.setattr(
        backend_module,
        "_require_git_commit",
        lambda _root, _expected: None,
    )
    frozen = verify_unconsumed_frozen_admission(ROOT)
    lease = build_prospective_execution_lease(
        frozen,
        claimed_at_utc="2026-07-28T04:00:00Z",
        wrapper_commit=WRAPPER_COMMIT,
        operator_acknowledgement=EXECUTION_LEASE_OPERATOR_ACKNOWLEDGEMENT,
        output_root_absent_at_claim=True,
        execution_lease_absent_at_claim=True,
    )
    contract = build_execution_wrapper_contract(lease)
    staging = tmp_path / "staging"
    staging.mkdir()
    backend = QWakeLC4RuntimeBackend(
        project_root=ROOT,
        torch2pc_dir=ROOT / "external/Torch2PC",
        execution_freeze=freeze,
        matrix_executor=_FakeMatrixExecutor(),
    )

    receipt = backend.run(staging, lease, contract)

    assert receipt.output_file_count == 7
    assert receipt.runtime_execution_performed is True
    assert receipt.scientific_execution_open is False
    assert receipt.test_dataset_access is False
    assert receipt.publication_permitted is False
    files = tuple(path.name for path in staging.iterdir())
    assert set(files) == {
        "runtime-backend-report.json",
        "matched-cells.jsonl",
        "reserve-probes.jsonl",
        "paired-cost-aggregates.json",
        "runtime-identities.json",
        "runtime-backend-receipt.json",
        "SHA256SUMS",
    }
    assert all(path.is_file() and not path.is_symlink() for path in staging.iterdir())
    report = json.loads((staging / "runtime-backend-report.json").read_text())
    assert report["authorized_cell_count"] == 168
    assert report["reserve_probe_count"] == 28
    assert report["all_order_effect_gates_passed"] is True
    assert report["all_pairs_complete"] is True
    assert report["scientific_execution_open"] is False
    matched_lines = (staging / "matched-cells.jsonl").read_text(
        encoding="utf-8"
    ).splitlines()
    probe_lines = (staging / "reserve-probes.jsonl").read_text(
        encoding="utf-8"
    ).splitlines()
    assert len(matched_lines) == 168
    assert len(probe_lines) == 28
    assert all(isinstance(json.loads(line), dict) for line in matched_lines)
    assert all(isinstance(json.loads(line), dict) for line in probe_lines)


def test_runtime_matrix_preserves_failed_order_effect_gate() -> None:
    authorization = load_runtime_authorization(
        ROOT
        / "experiments/frozen/stage3b-qwake-lc4-f-runtime-freeze-v1/"
        "authorization.json"
    )
    result = _FakeMatrixExecutor().execute(authorization)
    broken = [dict(item) for item in result.aggregates]
    payload = dict(broken[0])
    payload["order_effect_passed"] = False
    payload.pop("aggregate_sha256")
    payload["aggregate_sha256"] = sha256_object(payload)
    broken[0] = payload
    invalid = RuntimeMatrixResult(
        cells=result.cells,
        reserve_probes=result.reserve_probes,
        aggregates=tuple(broken),
    )
    invalid.require(authorization)
    assert invalid.aggregates[0]["order_effect_passed"] is False


def test_missing_materialized_freeze_blocks_before_lease_claim(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(
        QWakeLC4RuntimeBackendError,
        match="package is absent",
    ):
        verify_materialized_execution_freeze(tmp_path)

    calls: list[str] = []

    def forbidden_claim(*_args, **_kwargs):
        calls.append("claim")
        raise AssertionError("claim must not run")

    monkeypatch.setattr(backend_module, "claim_execution_lease", forbidden_claim)
    with pytest.raises(
        QWakeLC4RuntimeBackendError,
        match="package is absent",
    ):
        run_one_shot_authorized_runtime(
            tmp_path,
            tmp_path / "external/Torch2PC",
            claimed_at_utc="2026-07-28T04:00:00Z",
            operator_acknowledgement=EXECUTION_LEASE_OPERATOR_ACKNOWLEDGEMENT,
        )
    assert calls == []
    assert not (tmp_path / EXECUTION_LEASE_RELATIVE).exists()


def test_entrypoint_has_only_explicit_main_effect_boundary() -> None:
    path = ROOT / "scripts/run_stage3b_qwake_lc4_authorized_runtime.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    calls = [
        node
        for node in tree.body
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
    ]
    assert calls == []
    guards = [
        node
        for node in tree.body
        if isinstance(node, ast.If)
    ]
    assert len(guards) == 1


def test_implementation_manifest_and_closed_gates() -> None:
    manifest = json.loads(
        (IMPLEMENTATION_ROOT / "implementation.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["implementation_id"] == RUNTIME_BACKEND_IMPLEMENTATION_ID
    assert manifest["status"] == RUNTIME_BACKEND_IMPLEMENTATION_STATUS
    assert manifest["source"]["base_commit"] == AUTHORING_MERGE_COMMIT
    assert manifest["gates"]["concrete_runtime_backend_present"] is True
    assert manifest["gates"]["one_shot_entrypoint_present"] is True
    assert manifest["gates"]["runtime_execution_freeze_guard_present"] is True
    for gate in (
        "immutable_execution_image_present",
        "execution_freeze_materialized",
        "execution_lease_materialized",
        "qw_lc4_e_execution_permitted",
        "authorization_consumed",
        "runtime_execution_started",
        "runtime_execution_performed",
        "engineering_evidence_present",
        "scientific_execution_open",
        "test_dataset_access",
        "publication_permitted",
        "local_compute_execution_open",
    ):
        assert manifest["gates"][gate] is False
    assert manifest["next_slice"] == (
        "QW-LC4-E-runtime-backend-implementation-commit"
    )
    assert manifest["post_merge_next_slice"] == (
        "QW-LC4-E-execution-freeze-materialization"
    )


def test_frozen_authorization_remains_exact() -> None:
    authorization = load_runtime_authorization(
        ROOT
        / "experiments/frozen/stage3b-qwake-lc4-f-runtime-freeze-v1/"
        "authorization.json"
    )
    assert len(authorization.cells) == 168
    assert authorization.authorization_sha256 == FROZEN_AUTHORIZATION_SHA256
