from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = (
    ROOT
    / "experiments/frozen/"
    "stage3b-qwake-lc4-e-claim-execute-order-correction-v1"
)
PATCH = PACKAGE / "runtime-entrypoint.patch"
CORRECTED_ENTRYPOINT = PACKAGE / "run_stage3b_qwake_lc4_authorized_runtime.py"
ORIGINAL_ENTRYPOINT = ROOT / "scripts/run_stage3b_qwake_lc4_authorized_runtime.py"
CORRECTION_RECORD = PACKAGE / "correction.json"

ORIGINAL_ENTRYPOINT_SHA256 = (
    "504c3e614e199789b25c8b1927d0a35b1b95e1f3a5411e42db794fc93782cc79"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_corrected_entrypoint() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "qwake_lc4_corrected_entrypoint_test",
        CORRECTED_ENTRYPOINT,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def test_correction_preserves_historical_entrypoint() -> None:
    assert _sha256(ORIGINAL_ENTRYPOINT) == ORIGINAL_ENTRYPOINT_SHA256
    record = json.loads(CORRECTION_RECORD.read_text(encoding="utf-8"))
    assert record["source"]["original_entrypoint_sha256"] == (
        "sha256:" + ORIGINAL_ENTRYPOINT_SHA256
    )
    assert record["gates"]["historical_source_modified"] is False
    assert record["gates"]["attempt_001_reuse_permitted"] is False
    assert record["gates"]["runtime_execution_performed"] is False


def test_patch_reconstructs_exact_corrected_entrypoint(tmp_path: Path) -> None:
    target = tmp_path / "scripts/run_stage3b_qwake_lc4_authorized_runtime.py"
    target.parent.mkdir(parents=True)
    target.write_bytes(ORIGINAL_ENTRYPOINT.read_bytes())
    subprocess.run(
        ["git", "apply", "--unidiff-zero", "--check", str(PATCH)],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "apply", "--unidiff-zero", str(PATCH)],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    assert target.read_bytes() == CORRECTED_ENTRYPOINT.read_bytes()


def test_corrected_entrypoint_has_no_legacy_postclaim_call() -> None:
    tree = ast.parse(CORRECTED_ENTRYPOINT.read_text(encoding="utf-8"))
    imported_names = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    assert "execute_authorized_runtime" not in imported_names
    assert "claim_execution_lease" not in imported_names
    assert {
        "build_prospective_execution_lease",
        "materialize_execution_lease",
        "run_claimed_execution_wrapper",
        "verify_unconsumed_frozen_admission",
    } <= imported_names


def test_corrected_entrypoint_reuses_one_admission_through_claim(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_corrected_entrypoint()
    freeze = type("Freeze", (), {"wrapper_commit": "a" * 40})()
    admission = object()
    backend = object()
    lease = object()
    outcome = object()
    calls: list[str] = []

    def verify_freeze(root: Path) -> object:
        assert root == tmp_path.resolve()
        calls.append("verify_freeze")
        return freeze

    def verify_admission(root: Path) -> object:
        assert root == tmp_path.resolve()
        calls.append("verify_admission")
        return admission

    def build_backend(**kwargs: object) -> object:
        assert kwargs == {
            "project_root": tmp_path.resolve(),
            "torch2pc_dir": (tmp_path / "external/Torch2PC").resolve(),
            "execution_freeze": freeze,
        }
        calls.append("build_backend")
        return backend

    def build_lease(received: object, **kwargs: object) -> object:
        assert received is admission
        assert kwargs["wrapper_commit"] == freeze.wrapper_commit
        assert kwargs["output_root_absent_at_claim"] is True
        assert kwargs["execution_lease_absent_at_claim"] is True
        calls.append("build_lease")
        return lease

    def materialize(
        root: Path,
        received_lease: object,
        received_admission: object,
        **kwargs: object,
    ) -> Path:
        assert root == tmp_path.resolve()
        assert received_lease is lease
        assert received_admission is admission
        assert kwargs == {"expected_wrapper_commit": freeze.wrapper_commit}
        calls.append("materialize")
        return tmp_path / "lease.json"

    def run_claimed(
        root: Path,
        received_admission: object,
        **kwargs: object,
    ) -> object:
        assert root == tmp_path.resolve()
        assert received_admission is admission
        assert kwargs == {
            "expected_wrapper_commit": freeze.wrapper_commit,
            "backend": backend,
        }
        calls.append("run_claimed")
        return outcome

    monkeypatch.setattr(module, "verify_materialized_execution_freeze", verify_freeze)
    monkeypatch.setattr(module, "verify_unconsumed_frozen_admission", verify_admission)
    monkeypatch.setattr(module, "QWakeLC4RuntimeBackend", build_backend)
    monkeypatch.setattr(module, "build_prospective_execution_lease", build_lease)
    monkeypatch.setattr(module, "materialize_execution_lease", materialize)
    monkeypatch.setattr(module, "run_claimed_execution_wrapper", run_claimed)
    monkeypatch.setattr(module, "AUTHORIZED_OUTPUT_ROOT", "results/attempt")
    monkeypatch.setattr(
        module,
        "EXECUTION_LEASE_RELATIVE",
        Path("results/attempt.execution-lease.json"),
    )

    result = module.run_corrected_one_shot_authorized_runtime(
        tmp_path,
        tmp_path / "external/Torch2PC",
        claimed_at_utc="2026-08-04T12:00:00Z",
        operator_acknowledgement=(
            module.EXECUTION_LEASE_OPERATOR_ACKNOWLEDGEMENT
        ),
    )

    assert result is outcome
    assert calls == [
        "verify_freeze",
        "verify_admission",
        "build_backend",
        "build_lease",
        "materialize",
        "run_claimed",
    ]


def test_wrong_torch2pc_path_blocks_before_freeze_and_claim(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_corrected_entrypoint()
    calls: list[str] = []

    def forbidden(*_args: object, **_kwargs: object) -> object:
        calls.append("forbidden")
        raise AssertionError("freeze or claim must not run")

    monkeypatch.setattr(module, "verify_materialized_execution_freeze", forbidden)
    monkeypatch.setattr(module, "verify_unconsumed_frozen_admission", forbidden)
    monkeypatch.setattr(module, "build_prospective_execution_lease", forbidden)
    monkeypatch.setattr(module, "materialize_execution_lease", forbidden)

    with pytest.raises(
        module.QWakeLC4RuntimeBackendError,
        match="Torch2PC path differs",
    ):
        module.run_corrected_one_shot_authorized_runtime(
            tmp_path,
            tmp_path / "different/Torch2PC",
            claimed_at_utc="2026-08-04T12:00:00Z",
            operator_acknowledgement=(
                module.EXECUTION_LEASE_OPERATOR_ACKNOWLEDGEMENT
            ),
        )
    assert calls == []


def test_wrong_acknowledgement_blocks_before_admission_and_claim(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_corrected_entrypoint()
    freeze = type("Freeze", (), {"wrapper_commit": "a" * 40})()
    calls: list[str] = []

    monkeypatch.setattr(
        module,
        "verify_materialized_execution_freeze",
        lambda _root: freeze,
    )

    def forbidden(*_args: object, **_kwargs: object) -> object:
        calls.append("forbidden")
        raise AssertionError("post-acknowledgement work must not run")

    monkeypatch.setattr(module, "verify_unconsumed_frozen_admission", forbidden)
    monkeypatch.setattr(module, "QWakeLC4RuntimeBackend", forbidden)
    monkeypatch.setattr(module, "build_prospective_execution_lease", forbidden)
    monkeypatch.setattr(module, "materialize_execution_lease", forbidden)
    monkeypatch.setattr(module, "run_claimed_execution_wrapper", forbidden)

    with pytest.raises(
        module.QWakeLC4RuntimeBackendError,
        match="acknowledgement differs",
    ):
        module.run_corrected_one_shot_authorized_runtime(
            tmp_path,
            tmp_path / "external/Torch2PC",
            claimed_at_utc="2026-08-04T12:00:00Z",
            operator_acknowledgement="WRONG",
        )
    assert calls == []


def test_corrected_entrypoint_integrates_real_claim_and_promotion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from torch2pc_thesis.stage3b_qwake_lc4_execution_admission import (
        AUTHORIZED_OUTPUT_ROOT,
        EXECUTION_ADMISSION_ID,
        EXECUTION_LEASE_RELATIVE,
    )
    from torch2pc_thesis.stage3b_qwake_lc4_execution_wrapper import (
        ADMISSION_CONTROL_PLANE_COMMIT,
        ADMISSION_FREEZE_HEAD_COMMIT,
        ADMISSION_FREEZE_ID,
        ADMISSION_FREEZE_MERGE_COMMIT,
        AUTHORIZED_CELL_COUNT,
        FROZEN_ADMISSION_FILE_SHA256,
        FROZEN_ADMISSION_PACKAGE_REGISTRY_SHA256,
        FROZEN_ADMISSION_RECEIPT_FILE_SHA256,
        FROZEN_ADMISSION_SHA256,
        FROZEN_ADMISSION_SOURCE_REGISTRY_SHA256,
        FROZEN_AUTHORIZATION_SHA256,
        FROZEN_IMAGE_DIGEST,
        FROZEN_TORCH2PC_COMMIT,
        RESERVE_PROBE_COUNT,
        RUNTIME_LANE_ORDER,
        ExecutionWrapperContract,
        FrozenAdmissionIdentity,
        ProspectiveExecutionLease,
        QWakeLC4ExecutionWrapperError,
    )
    from torch2pc_thesis.stage3b_qwake_lc4_execution_wrapper_implementation import (
        RuntimeBackendReceipt,
        RuntimeExecutionBackend,
        build_runtime_backend_receipt,
    )

    module = _load_corrected_entrypoint()
    wrapper_commit = "a" * 40
    freeze = type("Freeze", (), {"wrapper_commit": wrapper_commit})()
    frozen = FrozenAdmissionIdentity(
        freeze_id=ADMISSION_FREEZE_ID,
        freeze_merge_commit=ADMISSION_FREEZE_MERGE_COMMIT,
        freeze_head_commit=ADMISSION_FREEZE_HEAD_COMMIT,
        control_plane_commit=ADMISSION_CONTROL_PLANE_COMMIT,
        admission_id=EXECUTION_ADMISSION_ID,
        admission_sha256=FROZEN_ADMISSION_SHA256,
        admission_file_sha256=FROZEN_ADMISSION_FILE_SHA256,
        receipt_file_sha256=FROZEN_ADMISSION_RECEIPT_FILE_SHA256,
        package_registry_sha256=FROZEN_ADMISSION_PACKAGE_REGISTRY_SHA256,
        source_registry_sha256=FROZEN_ADMISSION_SOURCE_REGISTRY_SHA256,
        torch2pc_commit=FROZEN_TORCH2PC_COMMIT,
        image_digest=FROZEN_IMAGE_DIGEST,
        authorization_sha256=FROZEN_AUTHORIZATION_SHA256,
        output_root=AUTHORIZED_OUTPUT_ROOT,
        execution_lease_relative=EXECUTION_LEASE_RELATIVE.as_posix(),
        authorized_cell_count=AUTHORIZED_CELL_COUNT,
        reserve_probe_count=RESERVE_PROBE_COUNT,
        lane_order=RUNTIME_LANE_ORDER,
        execution_count=1,
        runtime_execution_permitted=True,
        authorization_consumed=False,
        runtime_execution_started=False,
        runtime_execution_performed=False,
        engineering_evidence_present=False,
        scientific_execution_open=False,
        test_dataset_access=False,
        publication_permitted=False,
    )
    frozen.require()

    class Backend(RuntimeExecutionBackend):
        @property
        def backend_id(self) -> str:
            return "claim-execute-order-correction-test-backend"

        def run(
            self,
            staging_root: Path,
            lease: ProspectiveExecutionLease,
            contract: ExecutionWrapperContract,
        ) -> RuntimeBackendReceipt:
            assert contract.lease_sha256 == lease.lease_sha256
            (staging_root / "result.json").write_text(
                '{"status":"ok"}\n',
                encoding="utf-8",
            )
            return build_runtime_backend_receipt(
                backend_id=self.backend_id,
                wrapper_commit=lease.wrapper_commit,
                lease_sha256=lease.lease_sha256,
                output_file_count=1,
            )

    monkeypatch.setattr(
        module,
        "verify_materialized_execution_freeze",
        lambda _root: freeze,
    )
    monkeypatch.setattr(
        module,
        "verify_unconsumed_frozen_admission",
        lambda _root: frozen,
    )
    monkeypatch.setattr(module, "QWakeLC4RuntimeBackend", lambda **_kwargs: Backend())

    outcome = module.run_corrected_one_shot_authorized_runtime(
        tmp_path,
        tmp_path / "external/Torch2PC",
        claimed_at_utc="2026-08-04T12:00:00Z",
        operator_acknowledgement=(
            module.EXECUTION_LEASE_OPERATOR_ACKNOWLEDGEMENT
        ),
    )

    lease_path = tmp_path / EXECUTION_LEASE_RELATIVE
    output_root = tmp_path / AUTHORIZED_OUTPUT_ROOT
    assert lease_path.is_file()
    assert output_root.is_dir()
    assert (output_root / "result.json").is_file()
    assert outcome.lease_path == lease_path
    assert outcome.output_root == output_root

    lease_before = lease_path.read_bytes()
    output_before = (output_root / "result.json").read_bytes()
    with pytest.raises(
        QWakeLC4ExecutionWrapperError,
        match="output root existed at prospective lease claim",
    ):
        module.run_corrected_one_shot_authorized_runtime(
            tmp_path,
            tmp_path / "external/Torch2PC",
            claimed_at_utc="2026-08-04T12:01:00Z",
            operator_acknowledgement=(
                module.EXECUTION_LEASE_OPERATOR_ACKNOWLEDGEMENT
            ),
        )
    assert lease_path.read_bytes() == lease_before
    assert (output_root / "result.json").read_bytes() == output_before
