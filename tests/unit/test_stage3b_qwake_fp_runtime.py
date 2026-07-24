from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from dataclasses import fields, replace
from pathlib import Path
from typing import cast

import pytest

from torch2pc_thesis.stage3b_qwake_core import (
    Capability,
    EdgeMeasurement,
    ObservationLevel,
)
from torch2pc_thesis.stage3b_qwake_fp_runtime import (
    RUNTIME_AUTHORIZATION_ID,
    RUNTIME_AUTHORIZATION_STATUS,
    RUNTIME_EFFECT_AUDIT_CAPABILITIES,
    RUNTIME_ENGINEERING_BATCH_ID,
    RUNTIME_OPERATOR_ACKNOWLEDGEMENT,
    ArmOrder,
    MatchedRuntimeBackend,
    QWakeFPRuntimeAuthorization,
    QWakeFPRuntimeEngineeringReport,
    QWakeFPRuntimeError,
    RuntimeArmExecution,
    RuntimeCellSpec,
    RuntimeProbe,
    RuntimeProbeBackend,
    RuntimeValidationPermissionSet,
    ValidationLane,
    build_engineering_report,
    build_lane_report,
    build_runtime_preflight,
    compute_runtime_authorization_sha256,
    compute_runtime_receipt_chain_sha256,
    execute_matched_cell,
    load_authorization,
    load_preflight,
    open_runtime_session,
    seal_engineering_report,
    to_pre_freeze_validation_report,
    validate_runtime_preflight,
    verify_static_validation_receipt,
)
from torch2pc_thesis.stage3b_qwake_fp_runtime_adapter import (
    AnalyticCapture,
    ObservationCapture,
    OracleCapture,
    QWakeFPRuntimeAdapterError,
    QWakeFPRuntimeBackend,
    collect_A0,
    collect_A1,
    collect_A2,
    compute_post_action_oracle,
    record_edge_costs,
    run_registered_analytics,
)
from torch2pc_thesis.stage3b_qwake_fp_spec import (
    ANALYTIC_REGISTRY,
    OBSERVATION_REGISTRY,
    PAIRED_VALIDATION_REGISTRY,
    QWakeFPAnalyticId,
    QWakeFPPairId,
)
from torch2pc_thesis.stage3b_qwake_fp_validation import (
    DisabledCapabilityAudit,
    EffectAudit,
    OracleIsolationRecord,
    PairArmId,
    PairArmRecord,
    RuntimeAdapterId,
)

ROOT = Path(__file__).resolve().parents[2]
SHA_A = "sha256:" + "a" * 64
SHA_B = "sha256:" + "b" * 64
SHA_C = "sha256:" + "c" * 64
SHA_D = "sha256:" + "d" * 64
SHA_E = "sha256:" + "e" * 64
SHA_F = "sha256:" + "f" * 64
SHA_1 = "sha256:" + "1" * 64
SHA_2 = "sha256:" + "2" * 64
SHA_3 = "sha256:" + "3" * 64


def _run(*args: str, cwd: Path) -> str:
    completed = subprocess.run(
        args,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _init_repo(path: Path, files: dict[str, str]) -> str:
    path.mkdir(parents=True)
    for relative, text in files.items():
        target = path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    _run("git", "init", "-b", "main", cwd=path)
    _run("git", "config", "user.email", "runtime@example.com", cwd=path)
    _run("git", "config", "user.name", "Runtime Test", cwd=path)
    _run("git", "add", "-A", cwd=path)
    _run("git", "commit", "-m", "fixture", cwd=path)
    return _run("git", "rev-parse", "HEAD", cwd=path)


@pytest.fixture()
def runtime_repositories(tmp_path: Path) -> tuple[Path, str, Path, str]:
    request_relative = Path(
        "experiments/frozen/"
        "stage3b-qwake-fp-pre-freeze-validation-v1/request.json"
    )
    sums_relative = request_relative.parent / "SHA256SUMS"
    project = tmp_path / "project"
    source_commit = _init_repo(
        project,
        {
            str(request_relative): (ROOT / request_relative).read_text(encoding="utf-8"),
            str(sums_relative): (ROOT / sums_relative).read_text(encoding="utf-8"),
            "tracked.txt": "source\n",
        },
    )
    torch2pc = tmp_path / "Torch2PC"
    torch2pc_commit = _init_repo(torch2pc, {"TorchSeq2PC.py": "PCInfer = object()\n"})
    return project, source_commit, torch2pc, torch2pc_commit


class _ProbeBackend(RuntimeProbeBackend):
    def probe(self, lane: ValidationLane) -> RuntimeProbe:
        if lane is ValidationLane.CPU_FLOAT64_ENGINEERING:
            return RuntimeProbe(
                lane=lane,
                python_version="3.12.0",
                python_implementation="CPython",
                python_executable="/usr/bin/python3",
                platform="Linux-test",
                machine="x86_64",
                torch_version="2.0.0",
                hip_version="",
                accelerator_available=False,
                accelerator_count=0,
                accelerator_name="",
                dtype="float64",
            )
        return RuntimeProbe(
            lane=lane,
            python_version="3.12.0",
            python_implementation="CPython",
            python_executable="/usr/bin/python3",
            platform="Linux-test",
            machine="x86_64",
            torch_version="2.0.0+rocm",
            hip_version="6.0",
            accelerator_available=True,
            accelerator_count=1,
            accelerator_name="Synthetic ROCm GPU",
            dtype="float32",
        )


def _build_preflight(
    runtime_repositories: tuple[Path, str, Path, str],
):  # type: ignore[no-untyped-def]
    project, source_commit, torch2pc, torch2pc_commit = runtime_repositories
    return build_runtime_preflight(
        project,
        torch2pc,
        source_commit=source_commit,
        torch2pc_commit=torch2pc_commit,
        image_digest=SHA_A,
        captured_at_utc="2026-07-24T18:00:00Z",
        probe_backend=_ProbeBackend(),
    )


def _cells() -> tuple[RuntimeCellSpec, ...]:
    cells: list[RuntimeCellSpec] = []
    for lane in ValidationLane:
        for index, pair_id in enumerate(QWakeFPPairId):
            cells.append(
                RuntimeCellSpec(
                    lane=lane,
                    pair_id=pair_id,
                    model_seed=0,
                    batch_id=RUNTIME_ENGINEERING_BATCH_ID,
                    arm_order=(
                        ArmOrder.REFERENCE_THEN_INSTRUMENTED
                        if index % 2 == 0
                        else ArmOrder.INSTRUMENTED_THEN_REFERENCE
                    ),
                )
            )
    return tuple(cells)


def _authorization(preflight) -> QWakeFPRuntimeAuthorization:  # type: ignore[no-untyped-def]
    payload = {
        "schema_version": 1,
        "authorization_id": RUNTIME_AUTHORIZATION_ID,
        "status": RUNTIME_AUTHORIZATION_STATUS,
        "issued_at_utc": "2026-07-24T19:00:00Z",
        "operator_acknowledgement": RUNTIME_OPERATOR_ACKNOWLEDGEMENT,
        "preflight_sha256": preflight.preflight_sha256,
        "source_identity": preflight.source_identity,
        "static_validation_receipt_sha256": SHA_B,
        "receipt_chain_sha256": compute_runtime_receipt_chain_sha256(
            preflight_sha256=preflight.preflight_sha256,
            static_validation_receipt_sha256=SHA_B,
        ),
        "permissions": RuntimeValidationPermissionSet.complete(),
        "cells": _cells(),
        "output_root": "results/stage-3/qwake-fp-runtime-validation-attempt-001",
        "output_root_absent_at_issue": True,
        "execution_count": 1,
        "scientific_execution_open": False,
        "test_dataset_access": False,
        "publication_permitted": False,
        "image_freeze_permitted": False,
    }
    return QWakeFPRuntimeAuthorization(
        **payload,
        authorization_sha256=compute_runtime_authorization_sha256(payload),
    )


def _hash_bytes(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


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


def _observations(pair_id: QWakeFPPairId) -> tuple[tuple[ObservationLevel, str], ...]:
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


class _MatchedBackend(MatchedRuntimeBackend):
    def __init__(self, *, mismatch: str | None = None) -> None:
        self.mismatch = mismatch
        self.state_restores = 0
        self.rng_restores = 0
        self.arm_order: list[PairArmId] = []
        self.permissions_by_arm: dict[PairArmId, frozenset[Capability]] = {}

    def capture_initial_state(self) -> bytes:
        return b"initial-state"

    def restore_initial_state(self, state: bytes) -> None:
        assert state == b"initial-state"
        self.state_restores += 1

    def capture_rng_state(self) -> bytes:
        return b"rng-state"

    def restore_rng_state(self, state: bytes) -> None:
        assert state == b"rng-state"
        self.rng_restores += 1

    def run_arm(
        self,
        cell: RuntimeCellSpec,
        arm_id: PairArmId,
        permissions: RuntimeValidationPermissionSet,
    ) -> RuntimeArmExecution:
        permissions.require(Capability.EXECUTE_FIXEDPRED)
        self.permissions_by_arm[arm_id] = permissions.capabilities
        self.arm_order.append(arm_id)
        instrumented = arm_id is PairArmId.INSTRUMENTED
        observations = _observations(cell.pair_id) if instrumented else ()
        effects = EffectAudit()
        measurement = EdgeMeasurement()
        if instrumented:
            effects = EffectAudit(
                invocation_count=1,
                tensor_read_count=0 if cell.pair_id is QWakeFPPairId.P0 else 2,
                temporary_allocation_count=(
                    0 if cell.pair_id is QWakeFPPairId.P0 else 1
                ),
                synchronization_count=(
                    0 if cell.pair_id is QWakeFPPairId.P0 else 1
                ),
                d2h_bytes=0 if cell.pair_id is QWakeFPPairId.P0 else 16,
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
        pair = next(
            item for item in PAIRED_VALIDATION_REGISTRY if item.pair_id is cell.pair_id
        )
        record = PairArmRecord(
            pair_id=cell.pair_id,
            arm_id=arm_id,
            arm_label=pair.reference if not instrumented else pair.instrumented,
            lane=cell.lane,
            model_seed=cell.model_seed,
            batch_id=cell.batch_id,
            initial_state_sha256=_hash_bytes(b"initial-state"),
            rng_state_before_sha256=_hash_bytes(b"rng-state"),
            equality_hashes=_equality_hashes(
                mismatch=self.mismatch if instrumented else None
            ),
            observation_payload_sha256s=observations,
            observer_measurement=measurement,
            observer_effects=effects,
        )
        oracle = OracleIsolationRecord(
            pre_action_field_names=("snapshot_id", "compute_step"),
            action_completed_ordinal=10,
            oracle_created_ordinal=11,
            oracle_read_before_action_count=0,
            pre_action_oracle_access_count=0,
        )
        disabled = tuple(
            DisabledCapabilityAudit(
                capability=capability,
                enabled=False,
                effects=EffectAudit(),
            )
            for capability in RUNTIME_EFFECT_AUDIT_CAPABILITIES
            if capability not in permissions.capabilities
        )
        return RuntimeArmExecution(
            record=record,
            oracle_isolation=oracle,
            disabled_capability_audits=disabled,
        )


class _AdapterBackend(QWakeFPRuntimeBackend):
    def collect_observation(self, level: ObservationLevel) -> ObservationCapture:
        spec = next(item for item in OBSERVATION_REGISTRY if item.level is level)
        effects = EffectAudit(
            invocation_count=1,
            tensor_read_count=0 if level is ObservationLevel.A0 else 1,
            temporary_allocation_count=0 if level is ObservationLevel.A0 else 1,
            synchronization_count=0 if level is ObservationLevel.A0 else 1,
            output_count=len(spec.cumulative_fields),
        )
        return ObservationCapture(
            level=level,
            fields=tuple((name, index) for index, name in enumerate(spec.cumulative_fields)),
            measurement=EdgeMeasurement(host_time_ns=1),
            effects=effects,
        )

    def run_analytic(self, analytic_id: QWakeFPAnalyticId) -> AnalyticCapture:
        spec = next(item for item in ANALYTIC_REGISTRY if item.analytic_id is analytic_id)
        return AnalyticCapture(
            analytic_id=analytic_id,
            fields=tuple((name, index) for index, name in enumerate(spec.output_fields)),
            measurement=EdgeMeasurement(host_time_ns=1),
            effects=EffectAudit(
                invocation_count=1,
                output_count=len(spec.output_fields),
            ),
        )

    def compute_post_action_oracle(self) -> OracleCapture:
        return OracleCapture(
            fields=(("defect", 0.0),),
            isolation=OracleIsolationRecord(
                pre_action_field_names=("snapshot_id",),
                action_completed_ordinal=3,
                oracle_created_ordinal=4,
                oracle_read_before_action_count=0,
                pre_action_oracle_access_count=0,
            ),
            measurement=EdgeMeasurement(host_time_ns=1),
            effects=EffectAudit(invocation_count=1, output_count=1),
        )

    def record_edge_costs(self) -> EdgeMeasurement:
        return EdgeMeasurement(host_time_ns=2, device_time_ns=1)


def test_runtime_modules_do_not_import_torch_at_module_scope() -> None:
    for relative in (
        "src/torch2pc_thesis/stage3b_qwake_fp_runtime.py",
        "src/torch2pc_thesis/stage3b_qwake_fp_runtime_adapter.py",
    ):
        tree = ast.parse((ROOT / relative).read_text(encoding="utf-8"))
        imported = {
            alias.name.split(".", maxsplit=1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imported.update(
            node.module.split(".", maxsplit=1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        )
        assert "torch" not in imported
        assert "torch2pc" not in imported


def test_frozen_adapter_registry_symbols_are_now_callable() -> None:
    for contract in (
        cast(tuple, __import__(
            "torch2pc_thesis.stage3b_qwake_fp_validation",
            fromlist=["QWAKE_FP_PRE_FREEZE_VALIDATION_REQUEST"],
        ).QWAKE_FP_PRE_FREEZE_VALIDATION_REQUEST.adapters)
    ):
        module = __import__(contract.module_name, fromlist=[contract.symbol_name])
        assert callable(getattr(module, contract.symbol_name))


def test_runtime_permissions_deny_all_and_reject_campaign_capabilities() -> None:
    denied = RuntimeValidationPermissionSet.deny_all()
    with pytest.raises(QWakeFPRuntimeError, match="not authorized"):
        denied.require(Capability.EXECUTE_FIXEDPRED)
    with pytest.raises(QWakeFPRuntimeError, match="forbidden"):
        RuntimeValidationPermissionSet(
            capabilities=frozenset({Capability.ACCESS_CONFIRMATORY_DATA})
        )


def test_effect_local_adapter_functions_require_permissions() -> None:
    backend = _AdapterBackend()
    denied = RuntimeValidationPermissionSet.deny_all()
    with pytest.raises(QWakeFPRuntimeError, match="COLLECT_A0"):
        collect_A0(denied, backend)
    allowed = RuntimeValidationPermissionSet.complete()
    assert collect_A0(allowed, backend).level is ObservationLevel.A0
    assert collect_A1(allowed, backend).level is ObservationLevel.A1
    assert collect_A2(allowed, backend).level is ObservationLevel.A2
    assert len(run_registered_analytics(allowed, backend, tuple(QWakeFPAnalyticId))) == 3
    assert compute_post_action_oracle(allowed, backend).isolation.passed
    assert record_edge_costs(allowed, backend).host_time_ns == 2


def test_a0_capture_rejects_tensor_effects() -> None:
    spec = OBSERVATION_REGISTRY[0]
    with pytest.raises(QWakeFPRuntimeAdapterError, match="tensor-free"):
        ObservationCapture(
            level=ObservationLevel.A0,
            fields=tuple((name, 0) for name in spec.cumulative_fields),
            measurement=EdgeMeasurement(),
            effects=EffectAudit(
                invocation_count=1,
                tensor_read_count=1,
                output_count=len(spec.cumulative_fields),
            ),
        )


def test_rocm_probe_requires_available_hip_accelerator() -> None:
    with pytest.raises(QWakeFPRuntimeError, match="available accelerator"):
        RuntimeProbe(
            lane=ValidationLane.ROCM_FLOAT32_CANONICAL,
            python_version="3.12",
            python_implementation="CPython",
            python_executable="/usr/bin/python3",
            platform="Linux",
            machine="x86_64",
            torch_version="2.0",
            hip_version="",
            accelerator_available=False,
            accelerator_count=0,
            accelerator_name="",
            dtype="float32",
        )


def test_preflight_is_deny_all_and_binds_source_request_and_adapters(
    runtime_repositories: tuple[Path, str, Path, str],
) -> None:
    project, _source_commit, torch2pc, _torch2pc_commit = runtime_repositories
    preflight = _build_preflight(runtime_repositories)
    assert preflight.permissions == RuntimeValidationPermissionSet.deny_all()
    assert tuple(probe.lane for probe in preflight.runtime_probes) == tuple(
        ValidationLane
    )
    assert preflight.bound_adapter_ids == tuple(RuntimeAdapterId)
    assert preflight.execution_authorization_present is False
    assert preflight.runtime_validation_permitted is False
    assert preflight.scientific_execution_open is False
    validate_runtime_preflight(
        preflight,
        project,
        torch2pc,
        probe_backend=_ProbeBackend(),
    )


def test_preflight_rejects_dirty_project(
    runtime_repositories: tuple[Path, str, Path, str],
) -> None:
    project, source_commit, torch2pc, torch2pc_commit = runtime_repositories
    (project / "dirty.txt").write_text("dirty\n", encoding="utf-8")
    with pytest.raises(QWakeFPRuntimeError, match="worktree must be clean"):
        build_runtime_preflight(
            project,
            torch2pc,
            source_commit=source_commit,
            torch2pc_commit=torch2pc_commit,
            image_digest=SHA_A,
            captured_at_utc="2026-07-24T18:00:00Z",
            probe_backend=_ProbeBackend(),
        )


def test_authorization_requires_exact_two_lane_pair_registry(
    runtime_repositories: tuple[Path, str, Path, str],
) -> None:
    preflight = _build_preflight(runtime_repositories)
    authorization = _authorization(preflight)
    assert {cell.lane for cell in authorization.cells} == set(ValidationLane)
    assert {
        cell.pair_id
        for cell in authorization.cells
        if cell.lane is ValidationLane.ROCM_FLOAT32_CANONICAL
    } == set(QWakeFPPairId)
    with pytest.raises(QWakeFPRuntimeError, match="science, publication"):
        payload = {
            "schema_version": authorization.schema_version,
            "authorization_id": authorization.authorization_id,
            "status": authorization.status,
            "issued_at_utc": authorization.issued_at_utc,
            "operator_acknowledgement": authorization.operator_acknowledgement,
            "preflight_sha256": authorization.preflight_sha256,
            "source_identity": authorization.source_identity,
            "static_validation_receipt_sha256": (
                authorization.static_validation_receipt_sha256
            ),
            "receipt_chain_sha256": authorization.receipt_chain_sha256,
            "permissions": authorization.permissions,
            "cells": authorization.cells,
            "output_root": authorization.output_root,
            "output_root_absent_at_issue": authorization.output_root_absent_at_issue,
            "execution_count": authorization.execution_count,
            "scientific_execution_open": authorization.scientific_execution_open,
            "test_dataset_access": True,
            "publication_permitted": authorization.publication_permitted,
            "image_freeze_permitted": authorization.image_freeze_permitted,
        }
        QWakeFPRuntimeAuthorization(
            **payload,
            authorization_sha256=compute_runtime_authorization_sha256(payload),
        )


def test_open_session_rejects_existing_output_root(
    runtime_repositories: tuple[Path, str, Path, str],
) -> None:
    project, _source_commit, torch2pc, _torch2pc_commit = runtime_repositories
    preflight = _build_preflight(runtime_repositories)
    authorization = _authorization(preflight)
    output = project / authorization.output_root
    output.mkdir(parents=True)
    with pytest.raises(QWakeFPRuntimeError, match="already exists"):
        open_runtime_session(
            preflight,
            authorization,
            project,
            torch2pc,
            probe_backend=_ProbeBackend(),
        )


def test_matched_runner_restores_state_and_rng_before_both_arms(
    runtime_repositories: tuple[Path, str, Path, str],
) -> None:
    project, _source_commit, torch2pc, _torch2pc_commit = runtime_repositories
    preflight = _build_preflight(runtime_repositories)
    authorization = _authorization(preflight)
    session = open_runtime_session(
        preflight,
        authorization,
        project,
        torch2pc,
        probe_backend=_ProbeBackend(),
    )
    cell = authorization.cells[1]
    backend = _MatchedBackend()
    result = execute_matched_cell(session, backend, cell)
    assert result.passed
    assert backend.state_restores == 2
    assert backend.rng_restores == 2
    assert tuple(backend.arm_order) == cell.arm_order.arms
    reference_permissions = backend.permissions_by_arm[PairArmId.REFERENCE]
    instrumented_permissions = backend.permissions_by_arm[PairArmId.INSTRUMENTED]
    assert Capability.COLLECT_A0 not in reference_permissions
    assert Capability.COLLECT_A0 in instrumented_permissions
    assert Capability.COLLECT_A2 not in instrumented_permissions


def test_matched_runner_preserves_exact_mismatch(
    runtime_repositories: tuple[Path, str, Path, str],
) -> None:
    project, _source_commit, torch2pc, _torch2pc_commit = runtime_repositories
    preflight = _build_preflight(runtime_repositories)
    authorization = _authorization(preflight)
    session = open_runtime_session(
        preflight,
        authorization,
        project,
        torch2pc,
        probe_backend=_ProbeBackend(),
    )
    backend = _MatchedBackend(mismatch="named_parameter_gradients")
    result = execute_matched_cell(session, backend, authorization.cells[0])
    assert not result.passed
    assert result.pair_validation.equality_mismatches == (
        "named_parameter_gradients",
    )


def _run_lane(
    session,
    lane: ValidationLane,
) -> tuple:  # type: ignore[no-untyped-def]
    results = []
    for cell in session.authorization.cells:
        if cell.lane is lane:
            results.append(execute_matched_cell(session, _MatchedBackend(), cell))
    return tuple(results)


def test_two_lane_report_and_seal_are_deterministic(
    runtime_repositories: tuple[Path, str, Path, str],
) -> None:
    project, _source_commit, torch2pc, _torch2pc_commit = runtime_repositories
    preflight = _build_preflight(runtime_repositories)
    authorization = _authorization(preflight)
    session = open_runtime_session(
        preflight,
        authorization,
        project,
        torch2pc,
        probe_backend=_ProbeBackend(),
    )
    lanes = tuple(
        build_lane_report(lane, _run_lane(session, lane))
        for lane in ValidationLane
    )
    report = build_engineering_report(
        session,
        lanes,
        manifest_integrity_passed=True,
        receipt_chain_passed=True,
        static_and_unit_passed=True,
    )
    assert isinstance(report, QWakeFPRuntimeEngineeringReport)
    assert report.image_freeze_eligible
    sealed = seal_engineering_report(report)
    assert sealed.sha256 == report.sha256()
    assert seal_engineering_report(report) == sealed
    projected = to_pre_freeze_validation_report(report)
    assert projected.image_freeze_eligible
    assert projected.scientific_evidence is False


def test_runtime_json_round_trip_is_strict(
    runtime_repositories: tuple[Path, str, Path, str],
    tmp_path: Path,
) -> None:
    preflight = _build_preflight(runtime_repositories)
    authorization = _authorization(preflight)
    preflight_path = tmp_path / "preflight.json"
    authorization_path = tmp_path / "authorization.json"
    preflight_path.write_text(preflight.canonical_json(), encoding="utf-8")
    authorization_path.write_text(
        json.dumps(
            cast(dict[str, object], authorization.payload_without_digest())
            | {"authorization_sha256": authorization.authorization_sha256},
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    assert load_preflight(preflight_path) == preflight
    assert load_authorization(authorization_path) == authorization


def test_authorization_rejects_output_root_traversal(
    runtime_repositories: tuple[Path, str, Path, str],
) -> None:
    preflight = _build_preflight(runtime_repositories)
    authorization = _authorization(preflight)
    payload = {
        field.name: getattr(authorization, field.name)
        for field in fields(authorization)
        if field.name != "authorization_sha256"
    }
    payload["output_root"] = "../outside"
    with pytest.raises(QWakeFPRuntimeError, match="confined"):
        QWakeFPRuntimeAuthorization(
            **payload,
            authorization_sha256=compute_runtime_authorization_sha256(payload),
        )


def test_lane_report_rejects_incomplete_pair_registry(
    runtime_repositories: tuple[Path, str, Path, str],
) -> None:
    project, _source_commit, torch2pc, _torch2pc_commit = runtime_repositories
    preflight = _build_preflight(runtime_repositories)
    authorization = _authorization(preflight)
    session = open_runtime_session(
        preflight,
        authorization,
        project,
        torch2pc,
        probe_backend=_ProbeBackend(),
    )
    cells = _run_lane(session, ValidationLane.CPU_FLOAT64_ENGINEERING)
    with pytest.raises(QWakeFPRuntimeError, match="exactly P0, P1, P2"):
        build_lane_report(ValidationLane.CPU_FLOAT64_ENGINEERING, cells[:2])


def test_runtime_json_loader_rejects_unknown_and_duplicate_keys(
    runtime_repositories: tuple[Path, str, Path, str],
    tmp_path: Path,
) -> None:
    preflight = _build_preflight(runtime_repositories)
    payload = json.loads(preflight.canonical_json())
    payload["unexpected"] = True
    unknown_path = tmp_path / "unknown.json"
    unknown_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(QWakeFPRuntimeError, match="keys differ"):
        load_preflight(unknown_path)

    duplicate_path = tmp_path / "duplicate.json"
    duplicate_path.write_text(
        '{"schema_version":1,"schema_version":1}',
        encoding="utf-8",
    )
    with pytest.raises(QWakeFPRuntimeError, match="cannot read JSON"):
        load_preflight(duplicate_path)


def test_runtime_payload_rejects_non_finite_values() -> None:
    capture = _AdapterBackend().collect_observation(ObservationLevel.A0)
    first_name, _first_value = capture.fields[0]
    bad = replace(
        capture,
        fields=((first_name, float("nan")), *capture.fields[1:]),
    )
    with pytest.raises(QWakeFPRuntimeAdapterError, match="non-finite"):
        bad.payload_sha256()


def test_runtime_implementation_status_remains_execution_closed() -> None:
    for name in ("STATUS.md", "STATUS_EN.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "qwake_fp_runtime_validation_implementation_complete=true" in text
        assert "qwake_fp_runtime_authorization_issued=false" in text
        assert "qwake_fp_runtime_validation_performed=false" in text
        assert "qwake_fp_canonical_torch_backend_implemented=true" in text
        assert "qwake_fp_all_snapshot_observer_implemented=true" in text
        assert "qwake_fp_authorized_execution_cli_implemented=true" in text
        assert "qwake_fp_static_validation_receipt_chain_implemented=true" in text
        assert "qwake_fp_pre_freeze_evidence_generated=false" in text
        assert "qwake_fp_scientific_image_freeze_permitted=false" in text
        assert "qwake_fp_next_stage=QW-4-runtime-validation" in text
        assert "qwake_fp_next_slice=QW-4-runtime-freeze" in text


def test_scripts_do_not_issue_authorization_or_execute_model() -> None:
    preflight_script = (
        ROOT / "scripts/preflight_stage3b_qwake_fp_runtime.py"
    ).read_text(encoding="utf-8")
    verify_script = (
        ROOT / "scripts/verify_stage3b_qwake_fp_runtime_authorization.py"
    ).read_text(encoding="utf-8")
    assert "issue" not in preflight_script.lower()
    assert "run_arm" not in preflight_script
    assert "run_arm" not in verify_script
    assert "scientific_execution_open=false" in verify_script.lower()


def test_static_validation_receipt_is_bound_to_authorization(
    runtime_repositories: tuple[Path, str, Path, str],
    tmp_path: Path,
) -> None:
    preflight = _build_preflight(runtime_repositories)
    receipt = tmp_path / "static-validation-receipt.json"
    receipt.write_bytes(b"static validation passed\n")
    receipt_sha256 = "sha256:" + hashlib.sha256(receipt.read_bytes()).hexdigest()
    payload = {
        "schema_version": 1,
        "authorization_id": RUNTIME_AUTHORIZATION_ID,
        "status": RUNTIME_AUTHORIZATION_STATUS,
        "issued_at_utc": "2026-07-24T19:00:00Z",
        "operator_acknowledgement": RUNTIME_OPERATOR_ACKNOWLEDGEMENT,
        "preflight_sha256": preflight.preflight_sha256,
        "source_identity": preflight.source_identity,
        "static_validation_receipt_sha256": receipt_sha256,
        "receipt_chain_sha256": compute_runtime_receipt_chain_sha256(
            preflight_sha256=preflight.preflight_sha256,
            static_validation_receipt_sha256=receipt_sha256,
        ),
        "permissions": RuntimeValidationPermissionSet.complete(),
        "cells": _cells(),
        "output_root": "results/stage-3/qwake-runtime-test",
        "output_root_absent_at_issue": True,
        "execution_count": 1,
        "scientific_execution_open": False,
        "test_dataset_access": False,
        "publication_permitted": False,
        "image_freeze_permitted": False,
    }
    authorization = QWakeFPRuntimeAuthorization(
        **payload,
        authorization_sha256=compute_runtime_authorization_sha256(payload),
    )
    assert verify_static_validation_receipt(authorization, receipt) == receipt_sha256
    receipt.write_bytes(b"changed\n")
    with pytest.raises(QWakeFPRuntimeError, match="receipt digest differs"):
        verify_static_validation_receipt(authorization, receipt)


def test_execution_script_hardcodes_canonical_backend_and_receipt_gate() -> None:
    script = (
        ROOT / "scripts/run_stage3b_qwake_fp_runtime_validation.py"
    ).read_text(encoding="utf-8")
    assert "TorchFixedPredEngineeringBackend" in script
    assert "verify_static_validation_receipt" in script
    assert "--static-validation-receipt" in script
    assert "SCIENTIFIC_EVIDENCE=false" in script
    assert "PUBLICATION_PERMITTED=false" in script
