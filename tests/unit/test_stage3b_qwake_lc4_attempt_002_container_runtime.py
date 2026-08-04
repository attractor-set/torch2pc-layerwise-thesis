from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from torch2pc_thesis.stage3b_qwake_lc4_attempt_002_contract import (
    ATTEMPT_002_AUTHORIZATION_RELATIVE,
    ATTEMPT_002_AUTHORIZATION_ROOT,
    ATTEMPT_002_BACKEND_RELATIVE,
    ATTEMPT_002_CONTRACT_RELATIVE,
    ATTEMPT_002_DURABLE_OUTCOME_RELATIVE,
    ATTEMPT_002_ENTRYPOINT_RELATIVE,
    ATTEMPT_002_FREEZE_RELATIVE,
    ATTEMPT_002_FREEZE_ROOT,
    ATTEMPT_002_ID,
    ATTEMPT_002_INVOCATION_ACKNOWLEDGEMENT,
    ATTEMPT_002_LEASE_ACKNOWLEDGEMENT,
    ATTEMPT_002_LEASE_V1_RELATIVE,
    ATTEMPT_002_LEASE_V2_RELATIVE,
    ATTEMPT_002_OUTPUT_ROOT,
    ATTEMPT_002_WRAPPER_RELATIVE,
    SCIENTIFIC_RUNTIME_AUTHORIZATION_RELATIVE,
    Attempt002Authorization,
    Attempt002ContractError,
    Attempt002ExecutionFreeze,
    build_attempt_002_admission,
    canonical_json,
    sha256_object,
    verify_attempt_002_execution_freeze,
    verify_unconsumed_attempt_002_authorization,
)
from torch2pc_thesis.stage3b_qwake_lc4_attempt_002_execution_wrapper import (
    Attempt002BackendReceipt,
    Attempt002ExecutionWrapperError,
    Attempt002LeaseV1,
    Attempt002WrapperContract,
    build_attempt_002_backend_receipt,
    build_attempt_002_lease,
    materialize_attempt_002_lease,
    run_claimed_attempt_002,
)
from torch2pc_thesis.stage3b_qwake_lc4_attempt_002_runtime_backend import (
    ATTEMPT_002_BACKEND_ID,
    Attempt002RuntimeBackend,
)
from torch2pc_thesis.stage3b_qwake_lc4_runtime_freeze import (
    load_runtime_authorization,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_COMMIT = "5e26c840b520c9b73fea316e25512788372d6975"
WRAPPER_COMMIT = "6" * 40
TORCH2PC_COMMIT = "b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4"
IMAGE_HEX = "7" * 64
IMAGE_DIGEST = "sha256:" + IMAGE_HEX
IMAGE_REPO_DIGEST = "example.invalid/qwake@sha256:" + IMAGE_HEX
CLAIMED_AT_UTC = "2026-08-04T15:00:00Z"


class FakeBackend:
    backend_id = "attempt-002-fake-backend-v1"

    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls = 0

    def run(
        self,
        staging_root: Path,
        lease: Attempt002LeaseV1,
        contract: Attempt002WrapperContract,
    ) -> Attempt002BackendReceipt:
        self.calls += 1
        if self.fail:
            raise RuntimeError("injected backend failure")
        (staging_root / "engineering-evidence.json").write_text(
            canonical_json(
                {
                    "attempt_id": ATTEMPT_002_ID,
                    "lease_sha256": lease.lease_sha256,
                    "contract_sha256": contract.contract_sha256,
                }
            ),
            encoding="utf-8",
        )
        return build_attempt_002_backend_receipt(
            backend_id=self.backend_id,
            lease=lease,
            contract=contract,
            output_file_count=1,
        )


@dataclass(frozen=True)
class FakeCell:
    response_passed: bool = True
    rng_post_match: bool = True

    def payload(self) -> dict[str, object]:
        return {"response_passed": True, "rng_post_match": True}


@dataclass(frozen=True)
class FakeProbe:
    passed: bool = True

    def payload(self) -> dict[str, object]:
        return {"passed": True}


class FakeMatrixResult:
    cells = (FakeCell(),)
    reserve_probes = (FakeProbe(),)
    aggregates = ({"order_effect_passed": True, "pair_complete": True},)

    def require(self, authorization: object) -> None:
        assert authorization is not None


class FakeMatrixExecutor:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, authorization: object) -> FakeMatrixResult:
        self.calls += 1
        assert authorization is not None
        return FakeMatrixResult()


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _write_canonical(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value), encoding="utf-8")


def _write_registry(path: Path, base: Path, relatives: tuple[Path, ...]) -> None:
    lines = []
    for relative in sorted(relatives, key=lambda item: item.as_posix()):
        lines.append(
            f"{hashlib.sha256((base / relative).read_bytes()).hexdigest()}  "
            f"{relative.as_posix()}\n"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")


def _copy_runtime_sources(root: Path) -> None:
    for relative in (
        ATTEMPT_002_CONTRACT_RELATIVE,
        ATTEMPT_002_WRAPPER_RELATIVE,
        ATTEMPT_002_BACKEND_RELATIVE,
        ATTEMPT_002_ENTRYPOINT_RELATIVE,
        SCIENTIFIC_RUNTIME_AUTHORIZATION_RELATIVE,
    ):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((REPOSITORY_ROOT / relative).read_bytes())
    (root / "external/Torch2PC").mkdir(parents=True, exist_ok=True)


def _materialize_future_inputs(
    root: Path,
) -> tuple[Attempt002ExecutionFreeze, Attempt002Authorization]:
    _copy_runtime_sources(root)
    scientific = load_runtime_authorization(
        root / SCIENTIFIC_RUNTIME_AUTHORIZATION_RELATIVE
    )
    freeze_payload: dict[str, object] = {
        "schema_version": 1,
        "freeze_id": "stage3b-qwake-lc4-e-attempt-002-execution-freeze-v1",
        "status": (
            "corrected_image_and_attempt_002_runtime_frozen_"
            "execution_not_started"
        ),
        "attempt_id": ATTEMPT_002_ID,
        "source_commit": SOURCE_COMMIT,
        "wrapper_commit": WRAPPER_COMMIT,
        "torch2pc_commit": TORCH2PC_COMMIT,
        "image_digest": IMAGE_DIGEST,
        "image_repo_digest": IMAGE_REPO_DIGEST,
        "contract_sha256": _sha(root / ATTEMPT_002_CONTRACT_RELATIVE),
        "wrapper_sha256": _sha(root / ATTEMPT_002_WRAPPER_RELATIVE),
        "backend_sha256": _sha(root / ATTEMPT_002_BACKEND_RELATIVE),
        "entrypoint_sha256": _sha(root / ATTEMPT_002_ENTRYPOINT_RELATIVE),
        "scientific_authorization_relative": (
            SCIENTIFIC_RUNTIME_AUTHORIZATION_RELATIVE.as_posix()
        ),
        "scientific_authorization_sha256": scientific.authorization_sha256,
        "scientific_authorization_file_sha256": _sha(
            root / SCIENTIFIC_RUNTIME_AUTHORIZATION_RELATIVE
        ),
        "output_root": ATTEMPT_002_OUTPUT_ROOT.as_posix(),
        "lease_v1_relative": ATTEMPT_002_LEASE_V1_RELATIVE.as_posix(),
        "lease_v2_relative": ATTEMPT_002_LEASE_V2_RELATIVE.as_posix(),
        "durable_outcome_relative": (
            ATTEMPT_002_DURABLE_OUTCOME_RELATIVE.as_posix()
        ),
        "authorized_cell_count": 168,
        "reserve_probe_count": 28,
        "execution_count": 1,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "engineering_evidence_present": False,
        "scientific_execution_open": False,
        "test_dataset_access": False,
        "publication_permitted": False,
    }
    freeze_payload["freeze_sha256"] = sha256_object(freeze_payload)
    _write_canonical(root / ATTEMPT_002_FREEZE_RELATIVE, freeze_payload)
    freeze_sources = (
        ATTEMPT_002_CONTRACT_RELATIVE,
        ATTEMPT_002_WRAPPER_RELATIVE,
        ATTEMPT_002_BACKEND_RELATIVE,
        ATTEMPT_002_ENTRYPOINT_RELATIVE,
        SCIENTIFIC_RUNTIME_AUTHORIZATION_RELATIVE,
    )
    _write_registry(
        root / ATTEMPT_002_FREEZE_ROOT / "source-SHA256SUMS",
        root,
        freeze_sources,
    )
    _write_registry(
        root / ATTEMPT_002_FREEZE_ROOT / "SHA256SUMS",
        root / ATTEMPT_002_FREEZE_ROOT,
        (Path("execution.json"), Path("source-SHA256SUMS")),
    )

    authorization_payload: dict[str, object] = {
        "schema_version": 1,
        "authorization_id": "stage3b-qwake-lc4-e-attempt-002-authorization-v1",
        "status": "effective_unconsumed_attempt_002_runtime_authorization",
        "attempt_id": ATTEMPT_002_ID,
        "freeze_sha256": freeze_payload["freeze_sha256"],
        "operator_identity_kind": "local-posix-account",
        "operator_identity": "test-operator",
        "action_phrase": ATTEMPT_002_INVOCATION_ACKNOWLEDGEMENT,
        "execution_count": 1,
        "authorization_effective": True,
        "authorization_consumed": False,
        "attempt_started": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "retry_permitted": False,
        "scientific_execution_open": False,
        "test_dataset_access": False,
        "publication_permitted": False,
    }
    authorization_payload["authorization_sha256"] = sha256_object(
        authorization_payload
    )
    _write_canonical(
        root / ATTEMPT_002_AUTHORIZATION_RELATIVE,
        authorization_payload,
    )
    _write_registry(
        root / ATTEMPT_002_AUTHORIZATION_ROOT / "source-SHA256SUMS",
        root,
        (ATTEMPT_002_FREEZE_RELATIVE,),
    )
    _write_registry(
        root / ATTEMPT_002_AUTHORIZATION_ROOT / "SHA256SUMS",
        root / ATTEMPT_002_AUTHORIZATION_ROOT,
        (Path("authorization.json"), Path("source-SHA256SUMS")),
    )

    freeze = Attempt002ExecutionFreeze(**freeze_payload)  # type: ignore[arg-type]
    authorization = Attempt002Authorization(  # type: ignore[arg-type]
        **authorization_payload
    )
    freeze.require()
    authorization.require(freeze)
    return freeze, authorization


def _admission_and_lease(
    root: Path,
) -> tuple[object, Attempt002LeaseV1]:
    freeze, authorization = _materialize_future_inputs(root)
    admission = build_attempt_002_admission(freeze, authorization)
    lease = build_attempt_002_lease(
        admission,
        claimed_at_utc=CLAIMED_AT_UTC,
        wrapper_commit=freeze.wrapper_commit,
        operator_acknowledgement=ATTEMPT_002_LEASE_ACKNOWLEDGEMENT,
    )
    return admission, lease


def _load_entrypoint() -> ModuleType:
    path = REPOSITORY_ROOT / ATTEMPT_002_ENTRYPOINT_RELATIVE
    spec = importlib.util.spec_from_file_location("attempt_002_entrypoint", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_attempt_002_paths_are_disjoint_from_terminal_attempt() -> None:
    assert ATTEMPT_002_ID.endswith("attempt-002")
    assert ATTEMPT_002_OUTPUT_ROOT.name.endswith("attempt-002")
    assert ATTEMPT_002_LEASE_V1_RELATIVE.name.endswith(
        "attempt-002.execution-lease.json"
    )
    assert ATTEMPT_002_LEASE_V2_RELATIVE.name.endswith(
        "attempt-002.execution-lease-v2.json"
    )
    assert ATTEMPT_002_DURABLE_OUTCOME_RELATIVE.name.endswith(
        "attempt-002.host-outcome.json"
    )
    runtime_text = "\n".join(
        (REPOSITORY_ROOT / relative).read_text(encoding="utf-8")
        for relative in (
            ATTEMPT_002_CONTRACT_RELATIVE,
            ATTEMPT_002_WRAPPER_RELATIVE,
            ATTEMPT_002_BACKEND_RELATIVE,
            ATTEMPT_002_ENTRYPOINT_RELATIVE,
        )
    )
    assert "attempt-001" not in runtime_text
    assert "7da92b8f77f6dc37d42db832c5613ef6" not in runtime_text
    assert "stage3b-qwake-lc4-e-execution-freeze-v1" not in runtime_text


def test_future_freeze_and_authorization_verify_without_effects(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    freeze, authorization = _materialize_future_inputs(tmp_path)
    monkeypatch.setenv("SOURCE_GIT_COMMIT", SOURCE_COMMIT)
    monkeypatch.setenv("EXPERIMENT_IMAGE_DIGEST", IMAGE_DIGEST)
    monkeypatch.setenv("EXPERIMENT_IMAGE_REPO_DIGEST", IMAGE_REPO_DIGEST)
    assert verify_attempt_002_execution_freeze(tmp_path) == freeze
    assert (
        verify_unconsumed_attempt_002_authorization(tmp_path, freeze)
        == authorization
    )
    assert not (tmp_path / ATTEMPT_002_LEASE_V1_RELATIVE).exists()
    assert not (tmp_path / ATTEMPT_002_OUTPUT_ROOT).exists()


def test_freeze_environment_mismatch_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _materialize_future_inputs(tmp_path)
    monkeypatch.setenv("SOURCE_GIT_COMMIT", "0" * 40)
    monkeypatch.setenv("EXPERIMENT_IMAGE_DIGEST", IMAGE_DIGEST)
    monkeypatch.setenv("EXPERIMENT_IMAGE_REPO_DIGEST", IMAGE_REPO_DIGEST)
    with pytest.raises(Attempt002ContractError, match="SOURCE_GIT_COMMIT"):
        verify_attempt_002_execution_freeze(tmp_path)


def test_atomic_lease_is_mode_0600_and_second_claim_is_rejected(
    tmp_path: Path,
) -> None:
    admission, lease = _admission_and_lease(tmp_path)
    lease_path = materialize_attempt_002_lease(tmp_path, lease, admission)  # type: ignore[arg-type]
    original = lease_path.read_bytes()
    assert stat.S_IMODE(lease_path.stat().st_mode) == 0o600
    assert original == lease.canonical_json().encode("utf-8")
    with pytest.raises(
        Attempt002ExecutionWrapperError,
        match="execution lease already exists",
    ):
        materialize_attempt_002_lease(tmp_path, lease, admission)  # type: ignore[arg-type]
    assert lease_path.read_bytes() == original


def test_successful_wrapper_promotes_once_and_preserves_first_result(
    tmp_path: Path,
) -> None:
    admission, lease = _admission_and_lease(tmp_path)
    materialize_attempt_002_lease(tmp_path, lease, admission)  # type: ignore[arg-type]
    backend = FakeBackend()
    outcome = run_claimed_attempt_002(
        tmp_path,
        admission,  # type: ignore[arg-type]
        lease,
        backend=backend,
    )
    lease_bytes = outcome.lease_path.read_bytes()
    evidence_bytes = (
        outcome.output_root / "engineering-evidence.json"
    ).read_bytes()
    assert backend.calls == 1
    assert outcome.output_root == tmp_path / ATTEMPT_002_OUTPUT_ROOT
    assert (outcome.output_root / "execution-wrapper-receipt.json").is_file()
    with pytest.raises(
        Attempt002ExecutionWrapperError,
        match="output root already exists",
    ):
        run_claimed_attempt_002(
            tmp_path,
            admission,  # type: ignore[arg-type]
            lease,
            backend=backend,
        )
    assert backend.calls == 1
    assert outcome.lease_path.read_bytes() == lease_bytes
    assert (
        outcome.output_root / "engineering-evidence.json"
    ).read_bytes() == evidence_bytes


def test_backend_failure_removes_staging_and_preserves_consumed_lease(
    tmp_path: Path,
) -> None:
    admission, lease = _admission_and_lease(tmp_path)
    lease_path = materialize_attempt_002_lease(
        tmp_path,
        lease,
        admission,  # type: ignore[arg-type]
    )
    original = lease_path.read_bytes()
    backend = FakeBackend(fail=True)
    with pytest.raises(RuntimeError, match="injected backend failure"):
        run_claimed_attempt_002(
            tmp_path,
            admission,  # type: ignore[arg-type]
            lease,
            backend=backend,
        )
    assert lease_path.read_bytes() == original
    assert not (tmp_path / ATTEMPT_002_OUTPUT_ROOT).exists()
    assert not tuple(
        (tmp_path / ATTEMPT_002_OUTPUT_ROOT.parent).glob(
            f".{ATTEMPT_002_OUTPUT_ROOT.name}.staging-*"
        )
    )


def test_symlink_lease_is_rejected(tmp_path: Path) -> None:
    admission, lease = _admission_and_lease(tmp_path)
    lease_path = tmp_path / ATTEMPT_002_LEASE_V1_RELATIVE
    lease_path.parent.mkdir(parents=True, exist_ok=True)
    target = tmp_path / "outside.json"
    target.write_text(lease.canonical_json(), encoding="utf-8")
    lease_path.symlink_to(target)
    with pytest.raises(
        Attempt002ExecutionWrapperError,
        match="absent or non-regular",
    ):
        run_claimed_attempt_002(
            tmp_path,
            admission,  # type: ignore[arg-type]
            lease,
            backend=FakeBackend(),
        )


def test_entrypoint_reuses_one_admission_object(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_entrypoint()
    freeze, authorization = _materialize_future_inputs(tmp_path)
    admission = build_attempt_002_admission(freeze, authorization)
    lease = build_attempt_002_lease(
        admission,
        claimed_at_utc=CLAIMED_AT_UTC,
        wrapper_commit=freeze.wrapper_commit,
        operator_acknowledgement=ATTEMPT_002_LEASE_ACKNOWLEDGEMENT,
    )
    calls: list[tuple[str, object]] = []

    class StubBackend:
        backend_id = "stub"

        def __init__(self, **kwargs: Any) -> None:
            calls.append(("backend", kwargs["execution_freeze"]))

    outcome = object()
    monkeypatch.setattr(
        module,
        "verify_attempt_002_execution_freeze",
        lambda root: calls.append(("freeze", root)) or freeze,
    )
    monkeypatch.setattr(
        module,
        "verify_unconsumed_attempt_002_authorization",
        lambda root, observed: (
            calls.append(("authorization", observed)) or authorization
        ),
    )
    monkeypatch.setattr(
        module,
        "build_attempt_002_admission",
        lambda observed_freeze, observed_authorization: (
            calls.append(("admission", observed_freeze)) or admission
        ),
    )
    monkeypatch.setattr(module, "Attempt002RuntimeBackend", StubBackend)
    monkeypatch.setattr(
        module,
        "build_attempt_002_lease",
        lambda observed, **kwargs: calls.append(("build", observed)) or lease,
    )
    monkeypatch.setattr(
        module,
        "materialize_attempt_002_lease",
        lambda root, observed_lease, observed: calls.append(
            ("materialize", observed)
        ),
    )
    monkeypatch.setattr(
        module,
        "run_claimed_attempt_002",
        lambda root, observed, observed_lease, **kwargs: (
            calls.append(("run", observed)) or outcome
        ),
    )
    observed_outcome = module.run_attempt_002_authorized_runtime(
        tmp_path,
        tmp_path / "external/Torch2PC",
        claimed_at_utc=CLAIMED_AT_UTC,
        operator_acknowledgement=ATTEMPT_002_LEASE_ACKNOWLEDGEMENT,
    )
    assert observed_outcome is outcome
    assert [name for name, _ in calls] == [
        "freeze",
        "authorization",
        "admission",
        "backend",
        "build",
        "materialize",
        "run",
    ]
    assert calls[1][1] is freeze
    assert calls[2][1] is freeze
    assert calls[3][1] is freeze
    assert calls[4][1] is admission
    assert calls[5][1] is admission
    assert calls[6][1] is admission


def test_attempt_002_backend_writes_only_new_identities(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    freeze, authorization = _materialize_future_inputs(tmp_path)
    monkeypatch.setenv("SOURCE_GIT_COMMIT", SOURCE_COMMIT)
    monkeypatch.setenv("EXPERIMENT_IMAGE_DIGEST", IMAGE_DIGEST)
    monkeypatch.setenv("EXPERIMENT_IMAGE_REPO_DIGEST", IMAGE_REPO_DIGEST)
    admission = build_attempt_002_admission(freeze, authorization)
    lease = build_attempt_002_lease(
        admission,
        claimed_at_utc=CLAIMED_AT_UTC,
        wrapper_commit=freeze.wrapper_commit,
        operator_acknowledgement=ATTEMPT_002_LEASE_ACKNOWLEDGEMENT,
    )
    from torch2pc_thesis.stage3b_qwake_lc4_attempt_002_execution_wrapper import (
        build_attempt_002_wrapper_contract,
    )

    contract = build_attempt_002_wrapper_contract(lease, admission)
    staging = tmp_path / "staging"
    staging.mkdir()
    matrix_executor = FakeMatrixExecutor()
    backend = Attempt002RuntimeBackend(
        project_root=tmp_path,
        torch2pc_dir=tmp_path / "external/Torch2PC",
        execution_freeze=freeze,
        matrix_executor=matrix_executor,  # type: ignore[arg-type]
    )
    receipt = backend.run(staging, lease, contract)
    assert receipt.backend_id == ATTEMPT_002_BACKEND_ID
    assert matrix_executor.calls == 1
    identities = json.loads(
        (staging / "runtime-identities.json").read_text(encoding="utf-8")
    )
    assert identities["attempt_id"] == ATTEMPT_002_ID
    assert identities["output_root"] == ATTEMPT_002_OUTPUT_ROOT.as_posix()
    assert identities["image_digest"] == IMAGE_DIGEST
    assert len(tuple(staging.iterdir())) == 7


def test_existing_output_blocks_authorization_before_claim(
    tmp_path: Path,
) -> None:
    freeze, _ = _materialize_future_inputs(tmp_path)
    (tmp_path / ATTEMPT_002_OUTPUT_ROOT).mkdir(parents=True)
    with pytest.raises(Attempt002ContractError, match="effect already exists"):
        verify_unconsumed_attempt_002_authorization(tmp_path, freeze)


def test_importing_new_modules_creates_no_effect_paths(tmp_path: Path) -> None:
    before = tuple(tmp_path.rglob("*"))
    _load_entrypoint()
    after = tuple(tmp_path.rglob("*"))
    assert before == after
    for relative in (
        ATTEMPT_002_OUTPUT_ROOT,
        ATTEMPT_002_LEASE_V1_RELATIVE,
        ATTEMPT_002_LEASE_V2_RELATIVE,
        ATTEMPT_002_DURABLE_OUTCOME_RELATIVE,
    ):
        assert not os.path.lexists(tmp_path / relative)
