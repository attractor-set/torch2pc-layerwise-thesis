"""Unit and regression guards for the QW-4A pre-freeze validation harness."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import pytest

from torch2pc_thesis.stage3b_qwake_core import Capability, EdgeMeasurement, ObservationLevel
from torch2pc_thesis.stage3b_qwake_fp_spec import QWakeFPPairId
from torch2pc_thesis.stage3b_qwake_fp_validation import (
    QWAKE_FP_PRE_FREEZE_VALIDATION_REQUEST,
    AdapterBindingStatus,
    DisabledCapabilityAudit,
    EffectAudit,
    OracleIsolationRecord,
    PairArmId,
    PairArmRecord,
    QWakeFPValidationError,
    RuntimeAdapterId,
    ValidationGateId,
    ValidationLane,
    build_pre_freeze_report,
    build_pre_freeze_validation_request,
    compare_matched_pair,
    validate_disabled_capability,
    validate_nested_observation_hashes,
    validate_observer_cost_mapping,
    validate_oracle_isolation,
    validate_request_payload,
)

ROOT = Path(__file__).resolve().parents[2]
FROZEN_DIR = ROOT / "experiments/frozen/stage3b-qwake-fp-pre-freeze-validation-v1"
REQUEST_PATH = FROZEN_DIR / "request.json"
SUMS_PATH = FROZEN_DIR / "SHA256SUMS"

SHA_A = "sha256:" + "a" * 64
SHA_B = "sha256:" + "b" * 64
SHA_C = "sha256:" + "c" * 64
SHA_D = "sha256:" + "d" * 64
SHA_E = "sha256:" + "e" * 64
SHA_F = "sha256:" + "f" * 64
SHA_1 = "sha256:" + "1" * 64
SHA_2 = "sha256:" + "2" * 64
SHA_3 = "sha256:" + "3" * 64


def _equality_hashes(*, mismatch: str | None = None) -> tuple[tuple[str, str], ...]:
    values = {
        "canonical_endpoint_response": SHA_A,
        "named_parameter_gradients": SHA_B,
        "endpoint_beliefs": SHA_C,
        "endpoint_loss": SHA_D,
        "transition_sequence": SHA_E,
        "rng_state_after": SHA_F,
        "snapshot_identity": SHA_1,
    }
    if mismatch is not None:
        values[mismatch] = SHA_2
    return tuple(values.items())


def _observation_hashes(pair_id: QWakeFPPairId) -> tuple[tuple[ObservationLevel, str], ...]:
    return {
        QWakeFPPairId.P0: ((ObservationLevel.A0, SHA_1),),
        QWakeFPPairId.P1: (
            (ObservationLevel.A0, SHA_1),
            (ObservationLevel.A1, SHA_2),
        ),
        QWakeFPPairId.P2: (
            (ObservationLevel.A0, SHA_1),
            (ObservationLevel.A1, SHA_2),
            (ObservationLevel.A2, SHA_3),
        ),
    }[pair_id]


def _arm(
    pair_id: QWakeFPPairId,
    arm_id: PairArmId,
    *,
    mismatch: str | None = None,
    lane: ValidationLane = ValidationLane.CPU_FLOAT64_ENGINEERING,
) -> PairArmRecord:
    instrumented = arm_id is PairArmId.INSTRUMENTED
    effects = EffectAudit()
    measurement = EdgeMeasurement()
    observations: tuple[tuple[ObservationLevel, str], ...] = ()
    if instrumented:
        observations = _observation_hashes(pair_id)
        effects = EffectAudit(
            invocation_count=1,
            tensor_read_count=0 if pair_id is QWakeFPPairId.P0 else 2,
            temporary_allocation_count=0 if pair_id is QWakeFPPairId.P0 else 1,
            synchronization_count=0 if pair_id is QWakeFPPairId.P0 else 1,
            d2h_bytes=0 if pair_id is QWakeFPPairId.P0 else 16,
            trace_bytes=8,
            output_count=len(observations),
        )
        measurement = EdgeMeasurement(
            host_time_ns=11,
            device_time_ns=7,
            synchronization_count=effects.synchronization_count,
            d2h_bytes=effects.d2h_bytes,
            temporary_memory_bytes=32,
            trace_bytes=effects.trace_bytes,
        )
    label = "B0"
    if instrumented:
        label = {
            QWakeFPPairId.P0: "B0+A0",
            QWakeFPPairId.P1: "B0+A0+A1",
            QWakeFPPairId.P2: "B0+A0+A1+A2",
        }[pair_id]
    return PairArmRecord(
        pair_id=pair_id,
        arm_id=arm_id,
        arm_label=label,
        lane=lane,
        model_seed=3,
        batch_id="batch-0",
        initial_state_sha256=SHA_A,
        rng_state_before_sha256=SHA_B,
        equality_hashes=_equality_hashes(mismatch=mismatch),
        observation_payload_sha256s=observations,
        observer_measurement=measurement,
        observer_effects=effects,
    )


def _pair_result(pair_id: QWakeFPPairId):  # type: ignore[no-untyped-def]
    return compare_matched_pair(
        _arm(pair_id, PairArmId.REFERENCE),
        _arm(pair_id, PairArmId.INSTRUMENTED),
    )


def test_validation_module_has_no_torch_or_effect_imports() -> None:
    module = __import__(
        "torch2pc_thesis.stage3b_qwake_fp_validation",
        fromlist=["stage3b_qwake_fp_validation"],
    )
    source = module.__file__
    assert source is not None
    tree = ast.parse(Path(source).read_text(encoding="utf-8"))
    imported_roots = {
        alias.name.split(".", maxsplit=1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_roots.update(
        node.module.split(".", maxsplit=1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    )
    assert "torch" not in imported_roots
    assert "torch2pc" not in imported_roots
    assert imported_roots.isdisjoint({"os", "pathlib", "subprocess", "shutil"})


def test_request_is_finite_deterministic_and_execution_closed() -> None:
    request = QWAKE_FP_PRE_FREEZE_VALIDATION_REQUEST
    assert request.required_lanes == tuple(ValidationLane)
    assert request.pair_ids == tuple(QWakeFPPairId)
    assert request.required_gates == tuple(ValidationGateId)
    assert tuple(item.adapter_id for item in request.adapters) == tuple(RuntimeAdapterId)
    assert request.adapters[0].binding_status is (
        AdapterBindingStatus.EXISTING_LOADER_UNAUTHORIZED
    )
    assert all(
        item.binding_status is AdapterBindingStatus.UNBOUND
        for item in request.adapters[1:]
    )
    assert request.scientific_execution_open is False
    assert request.runtime_authorization_issued is False
    assert request.evidence_generated is False
    assert request.image_freeze_permitted is False
    assert build_pre_freeze_validation_request() == request


def test_frozen_request_matches_python_contract_and_sha256() -> None:
    request = QWAKE_FP_PRE_FREEZE_VALIDATION_REQUEST
    assert REQUEST_PATH.read_text(encoding="utf-8") == request.canonical_json()
    expected = hashlib.sha256(REQUEST_PATH.read_bytes()).hexdigest()
    assert request.sha256() == f"sha256:{expected}"
    assert SUMS_PATH.read_text(encoding="utf-8") == f"{expected}  request.json\n"


def test_request_loader_rejects_missing_or_corrupt_fields() -> None:
    payload = json.loads(REQUEST_PATH.read_text(encoding="utf-8"))
    validate_request_payload(payload)
    missing = dict(payload)
    missing.pop("pair_ids")
    with pytest.raises(QWakeFPValidationError, match="differs"):
        validate_request_payload(missing)
    corrupt = dict(payload)
    corrupt["runtime_authorization_issued"] = True
    with pytest.raises(QWakeFPValidationError, match="differs"):
        validate_request_payload(corrupt)


@pytest.mark.parametrize("pair_id", tuple(QWakeFPPairId))
def test_matched_pair_passes_for_equal_canonical_results(pair_id: QWakeFPPairId) -> None:
    result = _pair_result(pair_id)
    assert result.pair_id is pair_id
    assert result.passed is True
    assert result.equality_mismatches == ()
    assert result.initial_state_equal is True
    assert result.rng_state_before_equal is True
    assert result.observer_cost.observer_ns == 11
    assert result.observer_cost.total_time_ns == 11


def test_matched_pair_reports_exact_mismatch_without_hiding_it() -> None:
    result = compare_matched_pair(
        _arm(QWakeFPPairId.P1, PairArmId.REFERENCE),
        _arm(
            QWakeFPPairId.P1,
            PairArmId.INSTRUMENTED,
            mismatch="named_parameter_gradients",
        ),
    )
    assert result.passed is False
    assert result.equality_mismatches == ("named_parameter_gradients",)


def test_reference_arm_cannot_contain_observer_effects() -> None:
    with pytest.raises(QWakeFPValidationError, match="reference"):
        PairArmRecord(
            pair_id=QWakeFPPairId.P0,
            arm_id=PairArmId.REFERENCE,
            arm_label="B0",
            lane=ValidationLane.CPU_FLOAT64_ENGINEERING,
            model_seed=0,
            batch_id="batch-0",
            initial_state_sha256=SHA_A,
            rng_state_before_sha256=SHA_B,
            equality_hashes=_equality_hashes(),
            observation_payload_sha256s=(),
            observer_measurement=EdgeMeasurement(),
            observer_effects=EffectAudit(invocation_count=1),
        )


def test_a0_arm_cannot_read_tensors_or_synchronize() -> None:
    with pytest.raises(QWakeFPValidationError, match="A0"):
        PairArmRecord(
            pair_id=QWakeFPPairId.P0,
            arm_id=PairArmId.INSTRUMENTED,
            arm_label="B0+A0",
            lane=ValidationLane.CPU_FLOAT64_ENGINEERING,
            model_seed=0,
            batch_id="batch-0",
            initial_state_sha256=SHA_A,
            rng_state_before_sha256=SHA_B,
            equality_hashes=_equality_hashes(),
            observation_payload_sha256s=((ObservationLevel.A0, SHA_1),),
            observer_measurement=EdgeMeasurement(host_time_ns=1),
            observer_effects=EffectAudit(
                invocation_count=1,
                tensor_read_count=1,
                output_count=1,
            ),
        )


def test_nested_observation_hashes_are_preserved_across_p0_p1_p2() -> None:
    assert validate_nested_observation_hashes(
        _arm(QWakeFPPairId.P0, PairArmId.INSTRUMENTED),
        _arm(QWakeFPPairId.P1, PairArmId.INSTRUMENTED),
        _arm(QWakeFPPairId.P2, PairArmId.INSTRUMENTED),
    )


def test_nested_observation_hash_mismatch_fails() -> None:
    p2 = _arm(QWakeFPPairId.P2, PairArmId.INSTRUMENTED)
    changed = PairArmRecord(
        pair_id=p2.pair_id,
        arm_id=p2.arm_id,
        arm_label=p2.arm_label,
        lane=p2.lane,
        model_seed=p2.model_seed,
        batch_id=p2.batch_id,
        initial_state_sha256=p2.initial_state_sha256,
        rng_state_before_sha256=p2.rng_state_before_sha256,
        equality_hashes=p2.equality_hashes,
        observation_payload_sha256s=(
            (ObservationLevel.A0, SHA_3),
            (ObservationLevel.A1, SHA_2),
            (ObservationLevel.A2, SHA_3),
        ),
        observer_measurement=p2.observer_measurement,
        observer_effects=p2.observer_effects,
    )
    assert not validate_nested_observation_hashes(
        _arm(QWakeFPPairId.P0, PairArmId.INSTRUMENTED),
        _arm(QWakeFPPairId.P1, PairArmId.INSTRUMENTED),
        changed,
    )


def test_disabled_capability_requires_zero_effects() -> None:
    clean = DisabledCapabilityAudit(
        capability=Capability.COLLECT_A2,
        enabled=False,
        effects=EffectAudit(),
    )
    validate_disabled_capability(clean)
    dirty = DisabledCapabilityAudit(
        capability=Capability.COLLECT_A2,
        enabled=False,
        effects=EffectAudit(output_count=1),
    )
    with pytest.raises(QWakeFPValidationError, match="disabled capability"):
        validate_disabled_capability(dirty)


def test_oracle_is_strictly_post_action_and_absent_from_features() -> None:
    clean = OracleIsolationRecord(
        pre_action_field_names=("snapshot_id", "global_prediction_error_l2_sq"),
        action_completed_ordinal=10,
        oracle_created_ordinal=11,
        oracle_read_before_action_count=0,
        pre_action_oracle_access_count=0,
    )
    validate_oracle_isolation(clean)
    leaked = OracleIsolationRecord(
        pre_action_field_names=("snapshot_id", "oracle_label"),
        action_completed_ordinal=10,
        oracle_created_ordinal=9,
        oracle_read_before_action_count=1,
        pre_action_oracle_access_count=1,
    )
    with pytest.raises(QWakeFPValidationError, match="oracle isolation"):
        validate_oracle_isolation(leaked)


def test_observer_cost_mapping_does_not_double_count_device_time() -> None:
    measurement = EdgeMeasurement(
        host_time_ns=13,
        device_time_ns=101,
        temporary_memory_bytes=64,
    )
    cost = validate_observer_cost_mapping(measurement)
    assert cost.observer_ns == 13
    assert cost.total_time_ns == 13
    assert cost.memory_bytes == 64


def test_report_requires_all_pairs_negative_audits_and_both_smoke_lanes() -> None:
    pair_results = tuple(_pair_result(pair_id) for pair_id in QWakeFPPairId)
    audits = tuple(
        DisabledCapabilityAudit(capability=capability, enabled=False, effects=EffectAudit())
        for capability in (
            Capability.COLLECT_A0,
            Capability.COLLECT_A1,
            Capability.COLLECT_A2,
            Capability.COMPUTE_POST_ACTION_ORACLE,
        )
    )
    report = build_pre_freeze_report(
        pair_results=pair_results,
        nested_observations_passed=True,
        disabled_capability_audits=audits,
        oracle_isolation_passed=True,
        manifest_integrity_passed=True,
        receipt_chain_passed=True,
        static_and_unit_passed=True,
        cpu_smoke_passed=True,
        rocm_smoke_passed=True,
    )
    assert report.image_freeze_eligible is True
    blocked = build_pre_freeze_report(
        pair_results=pair_results,
        nested_observations_passed=True,
        disabled_capability_audits=audits,
        oracle_isolation_passed=True,
        manifest_integrity_passed=True,
        receipt_chain_passed=True,
        static_and_unit_passed=True,
        cpu_smoke_passed=True,
        rocm_smoke_passed=False,
    )
    assert blocked.image_freeze_eligible is False


def test_qw4a_documents_keep_runtime_and_image_freeze_closed() -> None:
    documents = (
        ROOT / "docs/decisions/ADR-044-stage3b-qwake-fp-pre-freeze-validation.md",
        ROOT / "docs/decisions/ADR-044-stage3b-qwake-fp-pre-freeze-validation_EN.md",
        ROOT / "STATUS.md",
        ROOT / "STATUS_EN.md",
    )
    required = (
        "qwake_fp_pre_freeze_validation_request_frozen=true",
        "qwake_fp_pre_freeze_validation_request_id=stage3b-qwake-fp-pre-freeze-validation-v1",
        "qwake_fp_pre_freeze_validation_harness_implemented=true",
        "qwake_fp_pre_freeze_validation_complete=false",
        "qwake_fp_runtime_authorization_issued=false",
        "qwake_fp_pre_freeze_evidence_generated=false",
        "qwake_fp_live_adapters_bound=false",
        "qwake_fp_scientific_image_freeze_permitted=false",
        "qwake_fp_next_stage=QW-4-runtime-validation",
        "c1_collection_open=false",
        "c2_calibration_open=false",
        "c3_confirmatory_open=false",
        "replication_open=false",
    )
    for path in documents:
        text = path.read_text(encoding="utf-8")
        for token in required:
            assert token in text, (path, token)


def test_current_status_marker_does_not_point_back_to_qw3() -> None:
    for name in ("STATUS.md", "STATUS_EN.md"):
        values = [
            line.split("=", maxsplit=1)[1]
            for line in (ROOT / name).read_text(encoding="utf-8").splitlines()
            if line.startswith("qwake_fp_next_stage=")
        ]
        assert values[-1] == "QW-4-runtime-validation"
