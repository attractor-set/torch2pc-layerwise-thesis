from __future__ import annotations

import ast
import hashlib
import json
import os
from dataclasses import replace
from pathlib import Path

import pytest

import torch2pc_thesis.stage3b_qwake_lc4_execution_wrapper_implementation as implementation
from torch2pc_thesis.stage3b_qwake_lc4_execution_admission import (
    AUTHORIZED_OUTPUT_ROOT,
    EXECUTION_LEASE_RELATIVE,
)
from torch2pc_thesis.stage3b_qwake_lc4_execution_wrapper import (
    EXECUTION_LEASE_OPERATOR_ACKNOWLEDGEMENT,
    ExecutionWrapperContract,
    FrozenAdmissionIdentity,
    ProspectiveExecutionLease,
    QWakeLC4ExecutionWrapperError,
    build_prospective_execution_lease,
    verify_unconsumed_frozen_admission,
)
from torch2pc_thesis.stage3b_qwake_lc4_execution_wrapper_implementation import (
    AUTHORING_COMMIT,
    AUTHORING_HEAD_COMMIT,
    AUTHORING_MERGE_COMMIT,
    EXECUTION_IMPLEMENTATION_ID,
    EXECUTION_WRAPPER_RECEIPT_RELATIVE,
    QWakeLC4ExecutionImplementationError,
    RuntimeBackendReceipt,
    RuntimeExecutionBackend,
    build_runtime_backend_receipt,
    claim_execution_lease,
    load_materialized_execution_lease,
    materialize_execution_lease,
    run_claimed_execution_wrapper,
)

ROOT = Path(__file__).resolve().parents[2]
WRAPPER_COMMIT = "b" * 40
CLAIMED_AT = "2026-07-27T23:30:00Z"
IMPLEMENTATION_ROOT = (
    ROOT
    / "experiments/frozen/"
    "stage3b-qwake-lc4-e-execution-lease-wrapper-implementation-v1"
)


class _RecordingBackend(RuntimeExecutionBackend):
    def __init__(
        self,
        *,
        fail: bool = False,
        empty: bool = False,
        symlink: bool = False,
        invalid_receipt: bool = False,
    ) -> None:
        self.called = False
        self.fail = fail
        self.empty = empty
        self.symlink = symlink
        self.invalid_receipt = invalid_receipt

    @property
    def backend_id(self) -> str:
        return "synthetic-qwake-lc4-backend-v1"

    def run(
        self,
        staging_root: Path,
        lease: ProspectiveExecutionLease,
        contract: ExecutionWrapperContract,
    ) -> RuntimeBackendReceipt:
        self.called = True
        assert contract.lease_sha256 == lease.lease_sha256
        if not self.empty:
            (staging_root / "engineering-result.json").write_text(
                '{"status":"synthetic-pass"}\n',
                encoding="utf-8",
            )
        if self.symlink:
            (staging_root / "result-link").symlink_to(
                staging_root / "engineering-result.json"
            )
        if self.fail:
            raise RuntimeError("synthetic backend failure")
        receipt = build_runtime_backend_receipt(
            backend_id=self.backend_id,
            wrapper_commit=lease.wrapper_commit,
            lease_sha256=lease.lease_sha256,
            output_file_count=1,
        )
        if self.invalid_receipt:
            return replace(receipt, runtime_execution_performed=False)
        return receipt


def _frozen() -> FrozenAdmissionIdentity:
    return verify_unconsumed_frozen_admission(ROOT)


def _lease(frozen: FrozenAdmissionIdentity) -> ProspectiveExecutionLease:
    return build_prospective_execution_lease(
        frozen,
        claimed_at_utc=CLAIMED_AT,
        wrapper_commit=WRAPPER_COMMIT,
        operator_acknowledgement=(
            EXECUTION_LEASE_OPERATOR_ACKNOWLEDGEMENT
        ),
        output_root_absent_at_claim=True,
        execution_lease_absent_at_claim=True,
    )


def _claim(
    project_root: Path,
    frozen: FrozenAdmissionIdentity,
) -> ProspectiveExecutionLease:
    lease = _lease(frozen)
    materialize_execution_lease(
        project_root,
        lease,
        frozen,
        expected_wrapper_commit=WRAPPER_COMMIT,
    )
    return lease


def _staging_paths(project_root: Path) -> tuple[Path, ...]:
    parent = project_root / Path(AUTHORIZED_OUTPUT_ROOT).parent
    if not parent.is_dir():
        return ()
    return tuple(
        path
        for path in parent.iterdir()
        if path.name.startswith(
            f".{Path(AUTHORIZED_OUTPUT_ROOT).name}.staging-"
        )
    )


def test_implementation_identity_and_source_boundary() -> None:
    assert AUTHORING_MERGE_COMMIT == (
        "e0455dc77b49f5b220231509fe6062d275b6ee9b"
    )
    assert AUTHORING_HEAD_COMMIT == (
        "0b59a2445d2e3367d717bbdb68d9b9ba45233bb6"
    )
    assert AUTHORING_COMMIT == (
        "1c9f2ef2ac7e76e7ed0a5da9d54ac773e6e9df6f"
    )

    module_path = (
        ROOT
        / "src/torch2pc_thesis/"
        "stage3b_qwake_lc4_execution_wrapper_implementation.py"
    )
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_imports = ("torch", "subprocess")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(
                not any(
                    alias.name == name
                    or alias.name.startswith(name + ".")
                    for name in forbidden_imports
                )
                for alias in node.names
            )
        if isinstance(node, ast.ImportFrom):
            imported_from = node.module or ""
            assert all(
                imported_from != name
                and not imported_from.startswith(name + ".")
                for name in forbidden_imports
            )


def test_atomic_lease_claim_writes_exact_canonical_file(
    tmp_path: Path,
) -> None:
    frozen = _frozen()
    lease = _claim(tmp_path, frozen)
    lease_path = tmp_path / EXECUTION_LEASE_RELATIVE

    assert lease_path.is_file()
    assert not lease_path.is_symlink()
    assert lease_path.read_bytes() == lease.canonical_json().encode("utf-8")
    assert lease_path.stat().st_mode & 0o777 == 0o600
    assert not (tmp_path / AUTHORIZED_OUTPUT_ROOT).exists()


def test_second_lease_claim_fails_without_rewriting(tmp_path: Path) -> None:
    frozen = _frozen()
    lease = _claim(tmp_path, frozen)
    lease_path = tmp_path / EXECUTION_LEASE_RELATIVE
    before = lease_path.read_bytes()

    with pytest.raises(
        (
            QWakeLC4ExecutionImplementationError,
            QWakeLC4ExecutionWrapperError,
        ),
        match="execution lease already exists",
    ):
        materialize_execution_lease(
            tmp_path,
            lease,
            frozen,
            expected_wrapper_commit=WRAPPER_COMMIT,
        )

    assert lease_path.read_bytes() == before


def test_existing_output_blocks_claim_without_lease(tmp_path: Path) -> None:
    frozen = _frozen()
    output_root = tmp_path / AUTHORIZED_OUTPUT_ROOT
    output_root.mkdir(parents=True)

    with pytest.raises(
        (
            QWakeLC4ExecutionImplementationError,
            QWakeLC4ExecutionWrapperError,
        ),
        match="output root already exists",
    ):
        materialize_execution_lease(
            tmp_path,
            _lease(frozen),
            frozen,
            expected_wrapper_commit=WRAPPER_COMMIT,
        )

    assert not (tmp_path / EXECUTION_LEASE_RELATIVE).exists()


def test_existing_lease_blocks_claim(tmp_path: Path) -> None:
    frozen = _frozen()
    lease_path = tmp_path / EXECUTION_LEASE_RELATIVE
    lease_path.parent.mkdir(parents=True)
    lease_path.write_text("{}\n", encoding="utf-8")

    with pytest.raises(
        (
            QWakeLC4ExecutionImplementationError,
            QWakeLC4ExecutionWrapperError,
        ),
        match="execution lease",
    ):
        materialize_execution_lease(
            tmp_path,
            _lease(frozen),
            frozen,
            expected_wrapper_commit=WRAPPER_COMMIT,
        )

    assert lease_path.read_text(encoding="utf-8") == "{}\n"


def test_output_race_after_claim_leaves_consumed_lease(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frozen = _frozen()
    original = implementation._atomic_exclusive_file_claim

    def racing_claim(root: Path, target: Path, payload: bytes) -> None:
        original(root, target, payload)
        (tmp_path / AUTHORIZED_OUTPUT_ROOT).mkdir(parents=True)

    monkeypatch.setattr(
        implementation,
        "_atomic_exclusive_file_claim",
        racing_claim,
    )

    with pytest.raises(
        QWakeLC4ExecutionImplementationError,
        match="appeared during lease claim",
    ):
        materialize_execution_lease(
            tmp_path,
            _lease(frozen),
            frozen,
            expected_wrapper_commit=WRAPPER_COMMIT,
        )

    assert (tmp_path / EXECUTION_LEASE_RELATIVE).is_file()
    assert (tmp_path / AUTHORIZED_OUTPUT_ROOT).is_dir()


def test_atomic_claim_removes_temporary_file_on_collision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "claim.json"
    original_link = os.link

    def colliding_link(
        source: Path,
        destination: Path,
        *,
        follow_symlinks: bool,
    ) -> None:
        destination.write_text("occupied\n", encoding="utf-8")
        raise FileExistsError(destination)

    monkeypatch.setattr(os, "link", colliding_link)
    with pytest.raises(
        QWakeLC4ExecutionImplementationError,
        match="atomic target already exists",
    ):
        implementation._atomic_exclusive_file_claim(
            tmp_path,
            target,
            b'{"claim":true}\n',
        )
    monkeypatch.setattr(os, "link", original_link)

    assert target.read_text(encoding="utf-8") == "occupied\n"
    assert not tuple(tmp_path.glob(".claim.json.tmp-*"))


def test_materialized_lease_tamper_fails_closed(tmp_path: Path) -> None:
    frozen = _frozen()
    _claim(tmp_path, frozen)
    lease_path = tmp_path / EXECUTION_LEASE_RELATIVE
    payload = json.loads(lease_path.read_text(encoding="utf-8"))
    payload["wrapper_commit"] = "c" * 40
    lease_path.write_text(json.dumps(payload) + "\n", encoding="utf-8")

    with pytest.raises(QWakeLC4ExecutionWrapperError):
        load_materialized_execution_lease(
            tmp_path,
            frozen,
            expected_wrapper_commit=WRAPPER_COMMIT,
            require_output_absent=True,
        )


def test_materialized_lease_symlink_fails_closed(tmp_path: Path) -> None:
    frozen = _frozen()
    target = tmp_path / "outside.json"
    target.write_text("{}\n", encoding="utf-8")
    lease_path = tmp_path / EXECUTION_LEASE_RELATIVE
    lease_path.parent.mkdir(parents=True)
    lease_path.symlink_to(target)

    with pytest.raises(
        QWakeLC4ExecutionImplementationError,
        match="absent or non-regular",
    ):
        load_materialized_execution_lease(
            tmp_path,
            frozen,
            expected_wrapper_commit=WRAPPER_COMMIT,
            require_output_absent=True,
        )


def test_claim_entrypoint_uses_verified_frozen_admission(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frozen = _frozen()
    calls: list[Path] = []

    def verified(root: Path) -> FrozenAdmissionIdentity:
        calls.append(root)
        return frozen

    monkeypatch.setattr(
        implementation,
        "verify_unconsumed_frozen_admission",
        verified,
    )
    lease = claim_execution_lease(
        tmp_path,
        claimed_at_utc=CLAIMED_AT,
        wrapper_commit=WRAPPER_COMMIT,
        operator_acknowledgement=(
            EXECUTION_LEASE_OPERATOR_ACKNOWLEDGEMENT
        ),
    )

    assert calls == [tmp_path.resolve()]
    assert lease.authorization_consumed is True
    assert (tmp_path / EXECUTION_LEASE_RELATIVE).is_file()


def test_successful_wrapper_promotes_complete_tree_atomically(
    tmp_path: Path,
) -> None:
    frozen = _frozen()
    lease = _claim(tmp_path, frozen)
    backend = _RecordingBackend()

    outcome = run_claimed_execution_wrapper(
        tmp_path,
        frozen,
        expected_wrapper_commit=WRAPPER_COMMIT,
        backend=backend,
    )

    output_root = tmp_path / AUTHORIZED_OUTPUT_ROOT
    receipt_path = output_root / EXECUTION_WRAPPER_RECEIPT_RELATIVE
    assert backend.called is True
    assert outcome.implementation_id == EXECUTION_IMPLEMENTATION_ID
    assert outcome.output_root == output_root
    assert (output_root / "engineering-result.json").is_file()
    assert receipt_path.is_file()
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["lease_sha256"] == lease.lease_sha256
    assert receipt["runtime_execution_performed"] is True
    assert receipt["scientific_execution_open"] is False
    assert receipt["test_dataset_access"] is False
    assert receipt["publication_permitted"] is False
    assert (tmp_path / EXECUTION_LEASE_RELATIVE).is_file()
    assert not _staging_paths(tmp_path)


def test_backend_failure_cleans_staging_and_preserves_lease(
    tmp_path: Path,
) -> None:
    frozen = _frozen()
    _claim(tmp_path, frozen)
    backend = _RecordingBackend(fail=True)

    with pytest.raises(RuntimeError, match="synthetic backend failure"):
        run_claimed_execution_wrapper(
            tmp_path,
            frozen,
            expected_wrapper_commit=WRAPPER_COMMIT,
            backend=backend,
        )

    assert (tmp_path / EXECUTION_LEASE_RELATIVE).is_file()
    assert not (tmp_path / AUTHORIZED_OUTPUT_ROOT).exists()
    assert not _staging_paths(tmp_path)


def test_invalid_backend_receipt_cleans_staging(
    tmp_path: Path,
) -> None:
    frozen = _frozen()
    _claim(tmp_path, frozen)
    backend = _RecordingBackend(invalid_receipt=True)

    with pytest.raises(
        QWakeLC4ExecutionImplementationError,
        match="did not complete execution",
    ):
        run_claimed_execution_wrapper(
            tmp_path,
            frozen,
            expected_wrapper_commit=WRAPPER_COMMIT,
            backend=backend,
        )

    assert (tmp_path / EXECUTION_LEASE_RELATIVE).is_file()
    assert not (tmp_path / AUTHORIZED_OUTPUT_ROOT).exists()
    assert not _staging_paths(tmp_path)


def test_symlink_in_staging_tree_fails_closed(tmp_path: Path) -> None:
    frozen = _frozen()
    _claim(tmp_path, frozen)
    backend = _RecordingBackend(symlink=True)

    with pytest.raises(
        QWakeLC4ExecutionImplementationError,
        match="non-regular file",
    ):
        run_claimed_execution_wrapper(
            tmp_path,
            frozen,
            expected_wrapper_commit=WRAPPER_COMMIT,
            backend=backend,
        )

    assert not (tmp_path / AUTHORIZED_OUTPUT_ROOT).exists()
    assert not _staging_paths(tmp_path)


def test_output_race_before_promotion_never_overwrites(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frozen = _frozen()
    _claim(tmp_path, frozen)
    original = implementation._rename_noreplace

    def racing_promotion(source: Path, target: Path) -> None:
        target.mkdir(parents=True)
        (target / "foreign.txt").write_text("foreign\n", encoding="utf-8")
        original(source, target)

    monkeypatch.setattr(
        implementation,
        "_rename_noreplace",
        racing_promotion,
    )

    with pytest.raises(
        QWakeLC4ExecutionImplementationError,
        match="output root already exists",
    ):
        run_claimed_execution_wrapper(
            tmp_path,
            frozen,
            expected_wrapper_commit=WRAPPER_COMMIT,
            backend=_RecordingBackend(),
        )

    output_root = tmp_path / AUTHORIZED_OUTPUT_ROOT
    assert (output_root / "foreign.txt").read_text(encoding="utf-8") == (
        "foreign\n"
    )
    assert (tmp_path / EXECUTION_LEASE_RELATIVE).is_file()
    assert not _staging_paths(tmp_path)


def test_missing_lease_blocks_backend_invocation(tmp_path: Path) -> None:
    backend = _RecordingBackend()

    with pytest.raises(
        QWakeLC4ExecutionImplementationError,
        match="lease is absent",
    ):
        run_claimed_execution_wrapper(
            tmp_path,
            _frozen(),
            expected_wrapper_commit=WRAPPER_COMMIT,
            backend=backend,
        )

    assert backend.called is False


def test_wrapper_commit_mismatch_blocks_backend_invocation(
    tmp_path: Path,
) -> None:
    frozen = _frozen()
    _claim(tmp_path, frozen)
    backend = _RecordingBackend()

    with pytest.raises(
        QWakeLC4ExecutionImplementationError,
        match="wrapper commit differs",
    ):
        run_claimed_execution_wrapper(
            tmp_path,
            frozen,
            expected_wrapper_commit="d" * 40,
            backend=backend,
        )

    assert backend.called is False


def test_empty_backend_output_is_rejected(tmp_path: Path) -> None:
    frozen = _frozen()
    _claim(tmp_path, frozen)

    with pytest.raises(
        QWakeLC4ExecutionImplementationError,
        match="no regular output file",
    ):
        run_claimed_execution_wrapper(
            tmp_path,
            frozen,
            expected_wrapper_commit=WRAPPER_COMMIT,
            backend=_RecordingBackend(empty=True),
        )

    assert not (tmp_path / AUTHORIZED_OUTPUT_ROOT).exists()
    assert (tmp_path / EXECUTION_LEASE_RELATIVE).is_file()


def test_implementation_manifest_and_russian_documentation() -> None:
    implementation_json = IMPLEMENTATION_ROOT / "implementation.json"
    registry = IMPLEMENTATION_ROOT / "SHA256SUMS"
    assert implementation_json.is_file()
    assert registry.is_file()

    expected, relative = registry.read_text(
        encoding="utf-8"
    ).strip().split("  ", 1)
    assert relative == "implementation.json"
    assert hashlib.sha256(implementation_json.read_bytes()).hexdigest() == (
        expected
    )

    payload = json.loads(implementation_json.read_text(encoding="utf-8"))
    assert payload["implementation_id"] == EXECUTION_IMPLEMENTATION_ID
    assert payload["source"]["base_commit"] == AUTHORING_MERGE_COMMIT
    assert payload["gates"]["lease_wrapper_authoring_merged"] is True
    assert payload["gates"]["execution_lease_writer_present"] is True
    assert payload["gates"]["runtime_executor_present"] is True
    assert payload["gates"]["result_writer_present"] is True
    assert payload["gates"]["execution_lease_materialized"] is False
    assert payload["gates"]["qw_lc4_e_execution_permitted"] is False
    assert payload["gates"]["authorization_consumed"] is False
    assert payload["gates"]["runtime_execution_started"] is False
    assert payload["gates"]["runtime_execution_performed"] is False

    marker = (
        "ADR-067-stage3b-qwake-lc4-e-execution-lease-wrapper-implementation"
    )
    for path in (
        ROOT / "STATUS.md",
        ROOT / "STATUS_EN.md",
        ROOT / "docs/qwake-local-compute-extension.md",
        ROOT / "docs/qwake-local-compute-extension_EN.md",
        ROOT / "docs/decisions/index.md",
        ROOT / "docs/decisions/index_EN.md",
        ROOT / "docs/language-map.csv",
        ROOT / "docs/research-log/2026-07.md",
        ROOT / "docs/research-log/2026-07_EN.md",
    ):
        assert marker in path.read_text(encoding="utf-8")

    russian_status = (ROOT / "STATUS.md").read_text(encoding="utf-8")
    assert "Атомарная реализация" in russian_status
    assert "EXECUTION_LEASE_WRITER_PRESENT=true" in russian_status
    assert "RUNTIME_EXECUTOR_PRESENT=true" in russian_status
    assert "RESULT_WRITER_PRESENT=true" in russian_status
    assert "EXECUTION_LEASE_MATERIALIZED=false" in russian_status
    assert "QW_LC4_E_EXECUTION_PERMITTED=false" in russian_status
