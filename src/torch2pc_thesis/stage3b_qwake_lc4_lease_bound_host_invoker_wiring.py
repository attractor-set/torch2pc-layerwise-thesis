"""Lease-bound wiring for the QW-LC4-E host runtime invoker.

The module requires an exact persisted execution lease v2 before delegating to
the historical one-shot host runtime invoker.  It captures full stream hashes,
materializes one immutable durable terminal receipt for every post-lease
terminal path, and forbids retry. Importing the module is effect free.
"""

from __future__ import annotations

import hashlib
import json
import stat
import subprocess
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, BinaryIO, Final, Protocol, cast

from torch2pc_thesis.stage3b_qwake_lc4_host_runtime_invoker_implementation import (
    HostChildProcess,
    HostRuntimeInvocationOutcome,
    ProcessSpawner,
    invoke_one_shot_host_runtime,
)
from torch2pc_thesis.stage3b_qwake_lc4_invocation_authorization import (
    INVOCATION_OPERATOR_ACKNOWLEDGEMENT,
)
from torch2pc_thesis.stage3b_qwake_lc4_invocation_wrapper_implementation import (
    LocalImageInspection,
)
from torch2pc_thesis.stage3b_qwake_lc4_persistent_evidence_chain_v2 import (
    DURABLE_HOST_OUTCOME_RELATIVE,
    DurableHostOutcomeReceipt,
    OutputSnapshot,
    PersistentEvidenceChainV2,
    PersistentExecutionLeaseV2,
    build_durable_host_outcome_receipt,
    canonical_json,
    sha256_bytes,
    sha256_object,
)
from torch2pc_thesis.stage3b_qwake_lc4_persistent_evidence_chain_v2_implementation import (
    PersistentWriteResult,
    persist_durable_host_outcome_receipt,
    verify_persisted_persistent_execution_lease_v2,
)

LEASE_BOUND_HOST_INVOKER_WIRING_ID: Final = (
    "stage3b-qwake-lc4-e-lease-bound-host-invoker-wiring-v1"
)
LEASE_BOUND_HOST_INVOKER_WIRING_STATUS: Final = (
    "lease_bound_host_invoker_wired_execution_closed"
)
WIRING_BASE_COMMIT: Final = "0303a1514e2875a057ef1b20293a01b36a9c6b2b"
IMPLEMENTATION_PR_NUMBER: Final = 145
IMPLEMENTATION_HEAD_COMMIT: Final = "45488d8d6d96b6e4419d835479dacd5398aa30f5"
IMPLEMENTATION_PARENT_COMMIT: Final = "3d092440b0314f02072c9773cc91018bf2860744"
IMPLEMENTATION_MERGE_COMMIT: Final = WIRING_BASE_COMMIT
IMPLEMENTATION_MERGED_AT_UTC: Final = "2026-07-30T12:53:35Z"
HISTORICAL_DIRECT_OPERATION_RELATIVE: Final = Path(
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_engineering_invocation_runtime_operation.py"
)
HISTORICAL_DIRECT_OPERATION_SHA256: Final = (
    "sha256:da08c66e78340c067e391a28f326f0d9bb7465d4a56073deac458a764ae6b30d"
)

IMPLEMENTATION_PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-persistent-evidence-chain-v2-implementation-v1"
)
IMPLEMENTATION_PACKAGE_REGISTRY_RELATIVE: Final = (
    IMPLEMENTATION_PACKAGE_RELATIVE / "SHA256SUMS"
)
IMPLEMENTATION_RECORD_RELATIVE: Final = (
    IMPLEMENTATION_PACKAGE_RELATIVE / "implementation.json"
)
IMPLEMENTATION_SOURCE_REGISTRY_RELATIVE: Final = (
    IMPLEMENTATION_PACKAGE_RELATIVE / "source-SHA256SUMS"
)

WIRING_PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-lease-bound-host-invoker-wiring-v1"
)
WIRING_RECORD_RELATIVE: Final = WIRING_PACKAGE_RELATIVE / "wiring.json"
IMPLEMENTATION_MERGE_RECEIPT_RELATIVE: Final = (
    WIRING_PACKAGE_RELATIVE / "implementation-merge-validation.json"
)
WIRING_REGISTRY_RELATIVE: Final = WIRING_PACKAGE_RELATIVE / "SHA256SUMS"
WIRING_SOURCE_REGISTRY_RELATIVE: Final = (
    WIRING_PACKAGE_RELATIVE / "source-SHA256SUMS"
)
WIRING_MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_lease_bound_host_invoker_wiring.py"
)
WIRING_VERIFIER_RELATIVE: Final = Path(
    "scripts/verify_stage3b_qwake_lc4_lease_bound_host_invoker_wiring.py"
)
WIRING_TEST_RELATIVE: Final = Path(
    "tests/unit/"
    "test_stage3b_qwake_lc4_lease_bound_host_invoker_wiring.py"
)
WIRING_ADR_RU_RELATIVE: Final = Path(
    "docs/decisions/"
    "ADR-085-stage3b-qwake-lc4-e-lease-bound-host-invoker-wiring.md"
)
WIRING_ADR_EN_RELATIVE: Final = Path(
    "docs/decisions/"
    "ADR-085-stage3b-qwake-lc4-e-lease-bound-host-invoker-wiring_EN.md"
)

_EMPTY_SHA256: Final = sha256_bytes(b"")

__all__ = [
    "LEASE_BOUND_HOST_INVOKER_WIRING_ID",
    "LEASE_BOUND_HOST_INVOKER_WIRING_STATUS",
    "LeaseBoundHostInvokerWiringError",
    "LeaseBoundHostInvokerWiringState",
    "LeaseBoundInvocationResult",
    "build_lease_bound_host_invoker_wiring_state",
    "invoke_lease_bound_host_runtime",
    "snapshot_authorized_output",
    "validate_lease_bound_host_invoker_wiring_state",
]


class LeaseBoundHostInvokerWiringError(RuntimeError):
    """Raised when lease-bound invocation cannot remain fail closed."""


class SignalSender(Protocol):
    def __call__(self, process_group_id: int, signal_number: int) -> None:
        """Forward one signal to the child process group."""


Clock = Callable[[], str]
ImageInspector = Callable[..., LocalImageInspection]


@dataclass(frozen=True)
class LeaseBoundHostInvokerWiringState:
    schema_version: int
    wiring_id: str
    status: str
    wiring_base_commit: str
    implementation_pr_number: int
    implementation_head_commit: str
    implementation_parent_commit: str
    implementation_merge_commit: str
    implementation_merged_at_utc: str
    persisted_lease_v2_required: bool
    exact_persisted_lease_verified_before_invocation: bool
    durable_terminal_receipt_required: bool
    full_stream_hashing_required: bool
    no_retry_enforced: bool
    historical_direct_operation_superseded: bool
    repository_direct_lower_level_call_forbidden: bool
    lease_bound_host_invoker_enforced: bool
    final_execution_acknowledged: bool
    one_shot_engineering_invocation_permitted: bool
    execution_lease_materialized: bool
    durable_host_outcome_present: bool
    authorization_consumed: bool
    runtime_execution_started: bool
    runtime_execution_performed: bool
    image_inspection_performed: bool
    invocation_command_materialized: bool
    docker_run_performed: bool
    local_compute_execution_open: bool
    state_sha256: str

    def require(self) -> None:
        exact: Mapping[str, object] = {
            "schema_version": 1,
            "wiring_id": LEASE_BOUND_HOST_INVOKER_WIRING_ID,
            "status": LEASE_BOUND_HOST_INVOKER_WIRING_STATUS,
            "wiring_base_commit": WIRING_BASE_COMMIT,
            "implementation_pr_number": IMPLEMENTATION_PR_NUMBER,
            "implementation_head_commit": IMPLEMENTATION_HEAD_COMMIT,
            "implementation_parent_commit": IMPLEMENTATION_PARENT_COMMIT,
            "implementation_merge_commit": IMPLEMENTATION_MERGE_COMMIT,
            "implementation_merged_at_utc": IMPLEMENTATION_MERGED_AT_UTC,
            "persisted_lease_v2_required": True,
            "exact_persisted_lease_verified_before_invocation": True,
            "durable_terminal_receipt_required": True,
            "full_stream_hashing_required": True,
            "no_retry_enforced": True,
            "historical_direct_operation_superseded": True,
            "repository_direct_lower_level_call_forbidden": True,
            "lease_bound_host_invoker_enforced": True,
            "final_execution_acknowledged": False,
            "one_shot_engineering_invocation_permitted": False,
            "execution_lease_materialized": False,
            "durable_host_outcome_present": False,
            "authorization_consumed": False,
            "runtime_execution_started": False,
            "runtime_execution_performed": False,
            "image_inspection_performed": False,
            "invocation_command_materialized": False,
            "docker_run_performed": False,
            "local_compute_execution_open": False,
        }
        for field_name, expected in exact.items():
            if getattr(self, field_name) != expected:
                raise LeaseBoundHostInvokerWiringError(
                    f"wiring state differs: {field_name}"
                )
        if self.state_sha256 != sha256_object(self._payload_without_digest()):
            raise LeaseBoundHostInvokerWiringError(
                "wiring state digest differs"
            )

    def _payload_without_digest(self) -> Mapping[str, object]:
        payload = asdict(self)
        payload.pop("state_sha256")
        return cast(Mapping[str, object], payload)


@dataclass(frozen=True)
class LeaseBoundInvocationResult:
    receipt: DurableHostOutcomeReceipt
    write_result: PersistentWriteResult
    host_outcome: HostRuntimeInvocationOutcome | None
    terminal_error: str | None

    def require(
        self,
        chain: PersistentEvidenceChainV2,
        lease: PersistentExecutionLeaseV2,
    ) -> None:
        self.receipt.require(chain, lease)
        self.write_result.require()
        if self.write_result.relative_path != DURABLE_HOST_OUTCOME_RELATIVE.as_posix():
            raise LeaseBoundHostInvokerWiringError(
                "durable outcome write path differs"
            )
        if self.write_result.sha256 != sha256_bytes(
            self.receipt.canonical_json().encode("utf-8")
        ):
            raise LeaseBoundHostInvokerWiringError(
                "durable outcome write digest differs"
            )
        if (self.host_outcome is None) != (self.terminal_error is not None):
            raise LeaseBoundHostInvokerWiringError(
                "terminal result shape differs"
            )


class _HashingReader:
    def __init__(self, stream: BinaryIO) -> None:
        self._stream = stream
        self._sha256 = hashlib.sha256()
        self.total_bytes = 0

    def read(self, size: int = -1) -> bytes:
        chunk = self._stream.read(size)
        if not isinstance(chunk, bytes):
            raise TypeError("child stream did not return bytes")
        self._sha256.update(chunk)
        self.total_bytes += len(chunk)
        return chunk

    def close(self) -> None:
        self._stream.close()

    @property
    def digest(self) -> str:
        return "sha256:" + self._sha256.hexdigest()


class _DigestingProcess:
    def __init__(self, process: HostChildProcess) -> None:
        self._process = process
        self.pid = process.pid
        self.returncode: int | None = process.returncode
        self.stdout_reader = (
            _HashingReader(process.stdout) if process.stdout is not None else None
        )
        self.stderr_reader = (
            _HashingReader(process.stderr) if process.stderr is not None else None
        )
        self.stdout = cast(BinaryIO | None, self.stdout_reader)
        self.stderr = cast(BinaryIO | None, self.stderr_reader)

    def poll(self) -> int | None:
        self.returncode = self._process.poll()
        return self.returncode

    def wait(self, timeout: float | None = None) -> int:
        self.returncode = self._process.wait(timeout=timeout)
        return self.returncode


class _DigestingSpawner:
    def __init__(self, base: ProcessSpawner) -> None:
        self._base = base
        self.attempt_count = 0
        self.process: _DigestingProcess | None = None

    def __call__(
        self,
        argv: Sequence[str],
        *,
        cwd: Path,
        env: Mapping[str, str],
        stdin: int,
        stdout: int,
        stderr: int,
        shell: bool,
        start_new_session: bool,
        close_fds: bool,
    ) -> HostChildProcess:
        self.attempt_count += 1
        if self.attempt_count != 1:
            raise LeaseBoundHostInvokerWiringError(
                "host child retry was attempted"
            )
        process = self._base(
            argv,
            cwd=cwd,
            env=env,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            shell=shell,
            start_new_session=start_new_session,
            close_fds=close_fds,
        )
        wrapped = _DigestingProcess(process)
        self.process = wrapped
        return wrapped


def build_lease_bound_host_invoker_wiring_state(
    project_root: Path,
) -> LeaseBoundHostInvokerWiringState:
    root = _verified_effect_free_root(project_root)
    _verify_wiring_freeze(root)
    payload: dict[str, object] = {
        "schema_version": 1,
        "wiring_id": LEASE_BOUND_HOST_INVOKER_WIRING_ID,
        "status": LEASE_BOUND_HOST_INVOKER_WIRING_STATUS,
        "wiring_base_commit": WIRING_BASE_COMMIT,
        "implementation_pr_number": IMPLEMENTATION_PR_NUMBER,
        "implementation_head_commit": IMPLEMENTATION_HEAD_COMMIT,
        "implementation_parent_commit": IMPLEMENTATION_PARENT_COMMIT,
        "implementation_merge_commit": IMPLEMENTATION_MERGE_COMMIT,
        "implementation_merged_at_utc": IMPLEMENTATION_MERGED_AT_UTC,
        "persisted_lease_v2_required": True,
        "exact_persisted_lease_verified_before_invocation": True,
        "durable_terminal_receipt_required": True,
        "full_stream_hashing_required": True,
        "no_retry_enforced": True,
        "historical_direct_operation_superseded": True,
        "repository_direct_lower_level_call_forbidden": True,
        "lease_bound_host_invoker_enforced": True,
        "final_execution_acknowledged": False,
        "one_shot_engineering_invocation_permitted": False,
        "execution_lease_materialized": False,
        "durable_host_outcome_present": False,
        "authorization_consumed": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "image_inspection_performed": False,
        "invocation_command_materialized": False,
        "docker_run_performed": False,
        "local_compute_execution_open": False,
    }
    state = LeaseBoundHostInvokerWiringState(
        **cast(Any, payload),
        state_sha256=sha256_object(payload),
    )
    state.require()
    return state


def validate_lease_bound_host_invoker_wiring_state(
    state: LeaseBoundHostInvokerWiringState,
    project_root: Path,
) -> None:
    state.require()
    if state != build_lease_bound_host_invoker_wiring_state(project_root):
        raise LeaseBoundHostInvokerWiringError("wiring state differs")


def snapshot_authorized_output(
    project_root: Path,
    chain: PersistentEvidenceChainV2,
) -> OutputSnapshot:
    root = project_root.expanduser().resolve()
    output = root / chain.source.output_root
    staging_count = len(tuple(output.parent.glob(f".{output.name}.staging-*")))
    if not output.exists() and not output.is_symlink():
        snapshot = OutputSnapshot(
            present=False,
            tree_sha256=_EMPTY_SHA256,
            file_count=0,
            byte_count=0,
            staging_count=staging_count,
        )
        snapshot.require()
        return snapshot
    if output.is_symlink() or not output.is_dir():
        raise LeaseBoundHostInvokerWiringError(
            "authorized output root is not a real directory"
        )
    entries: list[dict[str, object]] = []
    total_bytes = 0
    for candidate in sorted(output.rglob("*")):
        relative = candidate.relative_to(output).as_posix()
        if candidate.is_symlink():
            raise LeaseBoundHostInvokerWiringError(
                f"authorized output contains a symbolic path: {relative}"
            )
        if candidate.is_dir():
            continue
        mode = candidate.stat(follow_symlinks=False).st_mode
        if not stat.S_ISREG(mode):
            raise LeaseBoundHostInvokerWiringError(
                f"authorized output contains a non-regular file: {relative}"
            )
        payload = candidate.read_bytes()
        total_bytes += len(payload)
        entries.append(
            {
                "path": relative,
                "byte_count": len(payload),
                "sha256": sha256_bytes(payload),
            }
        )
    snapshot = OutputSnapshot(
        present=True,
        tree_sha256=sha256_bytes(canonical_json(entries).encode("utf-8")),
        file_count=len(entries),
        byte_count=total_bytes,
        staging_count=staging_count,
    )
    snapshot.require()
    return snapshot


def invoke_lease_bound_host_runtime(
    project_root: Path,
    chain: PersistentEvidenceChainV2,
    lease: PersistentExecutionLeaseV2,
    *,
    host_resources: Mapping[str, str],
    process_spawner: ProcessSpawner | None = None,
    image_inspector: ImageInspector | None = None,
    signal_sender: SignalSender | None = None,
    clock: Clock | None = None,
) -> LeaseBoundInvocationResult:
    """Invoke once only after exact lease-v2 verification and persist outcome."""

    root = project_root.expanduser().resolve()
    _verify_wiring_freeze(root)
    verify_persisted_persistent_execution_lease_v2(root, chain, lease)
    outcome_path = root / DURABLE_HOST_OUTCOME_RELATIVE
    if outcome_path.exists() or outcome_path.is_symlink():
        raise LeaseBoundHostInvokerWiringError(
            "durable host outcome already exists"
        )
    now = clock or _utc_now
    started_at_utc = now()
    before, terminal_error = _snapshot_or_error(root, chain, "before")
    telemetry = _DigestingSpawner(process_spawner or _spawn_process)
    host_outcome: HostRuntimeInvocationOutcome | None = None
    if terminal_error is None:
        try:
            host_outcome = invoke_one_shot_host_runtime(
                root,
                host_resources=host_resources,
                claimed_at_utc=lease.claimed_at_utc,
                operator_acknowledgement=INVOCATION_OPERATOR_ACKNOWLEDGEMENT,
                process_spawner=telemetry,
                image_inspector=image_inspector,
                signal_sender=signal_sender,
            )
        except Exception as exc:
            terminal_error = f"{type(exc).__name__}: {exc}"
    ended_at_utc = now()
    after, after_error = _snapshot_or_error(root, chain, "after")
    if after_error is not None:
        terminal_error = (
            after_error
            if terminal_error is None
            else terminal_error + "; " + after_error
        )
        host_outcome = None
    receipt = _build_receipt(
        chain,
        lease,
        before=before,
        after=after,
        started_at_utc=started_at_utc,
        ended_at_utc=ended_at_utc,
        telemetry=telemetry,
        host_outcome=host_outcome,
        terminal_error=terminal_error,
    )
    write_result = persist_durable_host_outcome_receipt(
        root,
        chain,
        lease,
        receipt,
    )
    result = LeaseBoundInvocationResult(
        receipt=receipt,
        write_result=write_result,
        host_outcome=host_outcome,
        terminal_error=terminal_error,
    )
    result.require(chain, lease)
    return result


def _build_receipt(
    chain: PersistentEvidenceChainV2,
    lease: PersistentExecutionLeaseV2,
    *,
    before: OutputSnapshot,
    after: OutputSnapshot,
    started_at_utc: str,
    ended_at_utc: str,
    telemetry: _DigestingSpawner,
    host_outcome: HostRuntimeInvocationOutcome | None,
    terminal_error: str | None,
) -> DurableHostOutcomeReceipt:
    if telemetry.attempt_count > 1:
        raise LeaseBoundHostInvokerWiringError("host child retry was observed")
    process = telemetry.process
    if host_outcome is not None:
        if process is None or telemetry.attempt_count != 1:
            raise LeaseBoundHostInvokerWiringError(
                "successful host outcome lacks one child telemetry record"
            )
        stdout_sha256, stdout_total = _stream_identity(process.stdout_reader)
        stderr_sha256, stderr_total = _stream_identity(process.stderr_reader)
        if stdout_total != host_outcome.stdout.total_bytes:
            raise LeaseBoundHostInvokerWiringError("stdout telemetry differs")
        if stderr_total != host_outcome.stderr.total_bytes:
            raise LeaseBoundHostInvokerWiringError("stderr telemetry differs")
        return build_durable_host_outcome_receipt(
            chain,
            lease,
            started_at_utc=started_at_utc,
            ended_at_utc=ended_at_utc,
            termination_class=host_outcome.classification,
            return_code=host_outcome.return_code,
            child_spawn_count=1,
            command_sha256=host_outcome.command_sha256,
            image_inspection_sha256=host_outcome.image_inspection_sha256,
            stdout_sha256=stdout_sha256,
            stderr_sha256=stderr_sha256,
            stdout_total_bytes=stdout_total,
            stderr_total_bytes=stderr_total,
            stdout_captured_bytes=host_outcome.stdout.captured_bytes,
            stderr_captured_bytes=host_outcome.stderr.captured_bytes,
            stdout_truncated=host_outcome.stdout.truncated,
            stderr_truncated=host_outcome.stderr.truncated,
            output_before=before,
            output_after=after,
        )
    if terminal_error is None:
        raise LeaseBoundHostInvokerWiringError("terminal failure text is absent")
    if telemetry.attempt_count == 0:
        classification = "prelaunch_rejected"
        child_spawn_count = 0
    elif process is None:
        classification = "spawn_failed"
        child_spawn_count = 0
    else:
        classification = _post_spawn_failure_classification(terminal_error)
        child_spawn_count = 1
    stdout_sha256, stdout_total = _stream_identity(
        process.stdout_reader if process is not None else None
    )
    stderr_sha256, stderr_total = _stream_identity(
        process.stderr_reader if process is not None else None
    )
    return build_durable_host_outcome_receipt(
        chain,
        lease,
        started_at_utc=started_at_utc,
        ended_at_utc=ended_at_utc,
        termination_class=classification,
        return_code=(process.returncode if process is not None else None),
        child_spawn_count=child_spawn_count,
        command_sha256=None,
        image_inspection_sha256=None,
        stdout_sha256=stdout_sha256,
        stderr_sha256=stderr_sha256,
        stdout_total_bytes=stdout_total,
        stderr_total_bytes=stderr_total,
        stdout_captured_bytes=stdout_total,
        stderr_captured_bytes=stderr_total,
        stdout_truncated=False,
        stderr_truncated=False,
        output_before=before,
        output_after=after,
    )


def _snapshot_or_error(
    root: Path,
    chain: PersistentEvidenceChainV2,
    phase: str,
) -> tuple[OutputSnapshot, str | None]:
    try:
        return snapshot_authorized_output(root, chain), None
    except (OSError, UnicodeError, ValueError, LeaseBoundHostInvokerWiringError) as exc:
        output = root / chain.source.output_root
        try:
            staging_count = len(
                tuple(output.parent.glob(f".{output.name}.staging-*"))
            )
        except OSError:
            staging_count = 0
        error = f"output snapshot {phase} failed: {type(exc).__name__}: {exc}"
        snapshot = OutputSnapshot(
            present=output.exists() or output.is_symlink(),
            tree_sha256=sha256_bytes(error.encode("utf-8")),
            file_count=0,
            byte_count=0,
            staging_count=staging_count,
        )
        snapshot.require()
        return snapshot, error


def _post_spawn_failure_classification(message: str) -> str:
    if "process control failed" in message:
        return "process_control_failed"
    if "output capture failed" in message:
        return "capture_failed"
    return "unexpected_failure"


def _stream_identity(reader: _HashingReader | None) -> tuple[str, int]:
    if reader is None:
        return _EMPTY_SHA256, 0
    return reader.digest, reader.total_bytes


def _spawn_process(
    argv: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    stdin: int,
    stdout: int,
    stderr: int,
    shell: bool,
    start_new_session: bool,
    close_fds: bool,
) -> HostChildProcess:
    if shell or not start_new_session or not close_fds:
        raise LeaseBoundHostInvokerWiringError("process controls differ")
    process = subprocess.Popen(
        tuple(argv),
        cwd=cwd,
        env=dict(env),
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
        shell=False,
        start_new_session=True,
        close_fds=True,
        text=False,
        bufsize=0,
    )
    return cast(HostChildProcess, process)


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _verified_effect_free_root(project_root: Path) -> Path:
    expanded = project_root.expanduser()
    if expanded.is_symlink():
        raise LeaseBoundHostInvokerWiringError("project root is symbolic")
    root = expanded.resolve()
    if not root.is_dir():
        raise LeaseBoundHostInvokerWiringError(
            "project root is absent or non-directory"
        )
    output = root / "results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001"
    lease_v1 = Path(str(output) + ".execution-lease.json")
    lease_v2 = Path(str(output) + ".execution-lease-v2.json")
    outcome = Path(str(output) + ".host-outcome.json")
    for path in (output, lease_v1, lease_v2, outcome):
        if path.exists() or path.is_symlink():
            raise LeaseBoundHostInvokerWiringError(
                f"effect-free wiring boundary is open: {path}"
            )
    if tuple(output.parent.glob(f".{output.name}.staging-*")):
        raise LeaseBoundHostInvokerWiringError(
            "effect-free wiring staging boundary is open"
        )
    return root


def _verify_wiring_freeze(root: Path) -> None:
    package = root / WIRING_PACKAGE_RELATIVE
    expected_files = {
        "SHA256SUMS",
        "implementation-merge-validation.json",
        "source-SHA256SUMS",
        "wiring.json",
    }
    if not package.is_dir() or package.is_symlink():
        raise LeaseBoundHostInvokerWiringError(
            "wiring package is absent or invalid"
        )
    if {path.name for path in package.iterdir()} != expected_files:
        raise LeaseBoundHostInvokerWiringError("wiring package file set differs")
    wiring_package_paths = _verify_registry(
        root / WIRING_REGISTRY_RELATIVE, package
    )
    if wiring_package_paths != {
        "implementation-merge-validation.json",
        "source-SHA256SUMS",
        "wiring.json",
    }:
        raise LeaseBoundHostInvokerWiringError(
            "wiring package registry scope differs"
        )
    _verify_registry(root / WIRING_SOURCE_REGISTRY_RELATIVE, root)
    implementation_package = root / IMPLEMENTATION_PACKAGE_RELATIVE
    if not implementation_package.is_dir() or implementation_package.is_symlink():
        raise LeaseBoundHostInvokerWiringError(
            "persistence implementation package is absent or invalid"
        )
    implementation_package_paths = _verify_registry(
        root / IMPLEMENTATION_PACKAGE_REGISTRY_RELATIVE,
        implementation_package,
    )
    if implementation_package_paths != {
        "authoring-merge-validation.json",
        "implementation.json",
        "source-SHA256SUMS",
    }:
        raise LeaseBoundHostInvokerWiringError(
            "persistence implementation package registry scope differs"
        )
    _verify_registry(root / IMPLEMENTATION_SOURCE_REGISTRY_RELATIVE, root)
    implementation_record = _load_json(root / IMPLEMENTATION_RECORD_RELATIVE)
    if implementation_record.get("implementation_sha256") != (
        "sha256:3671f7b12b570e7caace38dec0e023691bc1051b3cbf8e72ddfda59058369362"
    ):
        raise LeaseBoundHostInvokerWiringError(
            "persistence implementation identity differs"
        )
    merge_receipt = _load_json(root / IMPLEMENTATION_MERGE_RECEIPT_RELATIVE)
    exact_merge: Mapping[str, object] = {
        "schema_version": 1,
        "receipt_id": (
            "stage3b-qwake-lc4-e-persistent-evidence-chain-v2-"
            "implementation-post-merge-validation-v1"
        ),
        "pr_number": IMPLEMENTATION_PR_NUMBER,
        "head_commit": IMPLEMENTATION_HEAD_COMMIT,
        "base_commit": IMPLEMENTATION_PARENT_COMMIT,
        "merge_commit": IMPLEMENTATION_MERGE_COMMIT,
        "merged_at_utc": IMPLEMENTATION_MERGED_AT_UTC,
        "commit_count": 1,
        "file_count": 18,
        "focused_tests_passed": 29,
        "targeted_tests_passed": 230,
        "full_tests_passed": 1277,
        "full_test_warnings": 14,
        "required_ci_checks_passed": True,
        "ruff_passed": True,
        "mypy_passed": True,
        "ru_mkdocs_passed": True,
        "en_mkdocs_passed": True,
        "runtime_boundary_closed": True,
    }
    for field_name, expected in exact_merge.items():
        if merge_receipt.get(field_name) != expected:
            raise LeaseBoundHostInvokerWiringError(
                f"implementation merge receipt differs: {field_name}"
            )
    merge_digest = merge_receipt.get("receipt_sha256")
    reduced_merge = dict(merge_receipt)
    reduced_merge.pop("receipt_sha256", None)
    if merge_digest != sha256_object(reduced_merge):
        raise LeaseBoundHostInvokerWiringError(
            "implementation merge receipt digest differs"
        )
    record = _load_json(root / WIRING_RECORD_RELATIVE)
    exact: Mapping[str, object] = {
        "schema_version": 1,
        "wiring_id": LEASE_BOUND_HOST_INVOKER_WIRING_ID,
        "status": LEASE_BOUND_HOST_INVOKER_WIRING_STATUS,
        "wiring_base_commit": WIRING_BASE_COMMIT,
        "implementation_pr_number": IMPLEMENTATION_PR_NUMBER,
        "implementation_head_commit": IMPLEMENTATION_HEAD_COMMIT,
        "implementation_parent_commit": IMPLEMENTATION_PARENT_COMMIT,
        "implementation_merge_commit": IMPLEMENTATION_MERGE_COMMIT,
        "implementation_merged_at_utc": IMPLEMENTATION_MERGED_AT_UTC,
        "persisted_lease_v2_required": True,
        "durable_terminal_receipt_required": True,
        "full_stream_hashing_required": True,
        "no_retry_enforced": True,
        "historical_direct_operation_superseded": True,
        "repository_direct_lower_level_call_forbidden": True,
        "lease_bound_host_invoker_enforced": True,
        "final_execution_acknowledged": False,
        "one_shot_engineering_invocation_permitted": False,
        "execution_lease_materialized": False,
        "durable_host_outcome_present": False,
        "authorization_consumed": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "image_inspection_performed": False,
        "invocation_command_materialized": False,
        "docker_run_performed": False,
        "local_compute_execution_open": False,
    }
    for field_name, expected in exact.items():
        if record.get(field_name) != expected:
            raise LeaseBoundHostInvokerWiringError(
                f"wiring record differs: {field_name}"
            )
    observed = record.get("wiring_sha256")
    reduced = dict(record)
    reduced.pop("wiring_sha256", None)
    if observed != sha256_object(reduced):
        raise LeaseBoundHostInvokerWiringError(
            "wiring semantic digest differs"
        )
    if sha256_bytes((root / HISTORICAL_DIRECT_OPERATION_RELATIVE).read_bytes()) != (
        HISTORICAL_DIRECT_OPERATION_SHA256
    ):
        raise LeaseBoundHostInvokerWiringError(
            "historical direct operation identity differs"
        )


def _verify_registry(registry: Path, base: Path) -> set[str]:
    if not registry.is_file() or registry.is_symlink():
        raise LeaseBoundHostInvokerWiringError("registry is absent or invalid")
    observed: set[str] = set()
    for line in registry.read_text(encoding="utf-8", errors="strict").splitlines():
        digest, relative = line.split("  ", 1)
        if relative in observed:
            raise LeaseBoundHostInvokerWiringError(
                f"duplicate registry path: {relative}"
            )
        observed.add(relative)
        path = base / relative
        if not path.is_file() or path.is_symlink():
            raise LeaseBoundHostInvokerWiringError(
                f"registered source is absent: {relative}"
            )
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise LeaseBoundHostInvokerWiringError(
                f"registered source digest differs: {relative}"
            )
    return observed


def _load_json(path: Path) -> dict[str, object]:
    if not path.is_file() or path.is_symlink():
        raise LeaseBoundHostInvokerWiringError("required JSON is absent")
    payload = json.loads(path.read_text(encoding="utf-8", errors="strict"))
    if not isinstance(payload, dict):
        raise LeaseBoundHostInvokerWiringError("required JSON root differs")
    return cast(dict[str, object], payload)
