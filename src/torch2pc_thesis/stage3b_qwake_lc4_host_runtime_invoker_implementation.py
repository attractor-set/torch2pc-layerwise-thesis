"""Bounded implementation of the QW-LC4-E host runtime invoker.

The module implements the future one-shot host process boundary frozen by
ADR-074. Importing it is effect free. The public invocation function performs
fail-closed prelaunch verification, reinspects the exact immutable image,
reconstructs the canonical ``docker run`` argv, and can spawn that argv once.
It never writes the execution lease; the container entrypoint remains the only
lease owner. Repository validation and unit tests inject a fake child process
and never invoke Docker runtime execution.
"""

from __future__ import annotations

import hashlib
import json
import os
import signal
import subprocess
import threading
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from types import FrameType
from typing import Any, BinaryIO, Final, Protocol, cast

from torch2pc_thesis.stage3b_qwake_lc4_host_runtime_invoker import (
    AUTHORIZED_OUTPUT_ROOT,
    EXECUTION_LEASE_RELATIVE,
    HOST_RUNTIME_INVOKER_CONTRACT_ID,
    HostRuntimeInvokerContract,
    build_host_runtime_invoker_contract,
    canonical_json,
    sha256_object,
    validate_host_runtime_invoker_contract,
)
from torch2pc_thesis.stage3b_qwake_lc4_invocation_wrapper_implementation import (
    LocalImageInspection,
    MaterializedOneShotInvocation,
    inspect_local_immutable_image,
    materialize_one_shot_invocation,
    validate_materialized_one_shot_invocation,
)

HOST_RUNTIME_INVOKER_IMPLEMENTATION_ID: Final = (
    "stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-implementation-v1"
)
HOST_RUNTIME_INVOKER_IMPLEMENTATION_STATUS: Final = (
    "bounded_host_runtime_invoker_implemented_execution_not_invoked"
)
IMPLEMENTATION_BASE_COMMIT: Final = (
    "7f1655346bca77834d73a660c9857f1ff23b826c"
)
AUTHORING_HEAD_COMMIT: Final = (
    "5feb27b6d424d9910ea810ee4f5a9bd012e6d033"
)
AUTHORING_MERGE_COMMIT: Final = IMPLEMENTATION_BASE_COMMIT
AUTHORING_MERGED_AT_UTC: Final = "2026-07-29T12:48:46Z"
AUTHORING_PR_NUMBER: Final = 135
AUTHORING_RECORD_SHA256: Final = (
    "sha256:e58843b4cf97c51d9748c76f4c367043ef82ecf2bb3f5bf107c9f6a9528315d6"
)
AUTHORING_REGISTRY_SHA256: Final = (
    "sha256:cbc9bf167ec58f34cd79c13f386ccb572761963cb02f71cb5605fb3ce1c0d038"
)
AUTHORING_MODULE_SHA256: Final = (
    "sha256:0c6cc3769c5dd92690a556b16f50ce6fe29d9f4a007fa1f63e1b889a09974e72"
)
AUTHORING_VERIFIER_SHA256: Final = (
    "sha256:d4eb5a003ae1862b94b0dc4a092fb62a741f3a6296648f1aff9f5dc78c7b623f"
)
AUTHORING_TEST_SHA256: Final = (
    "sha256:15cf97286cdd5f2c2c4cbbaa7cd4eefa9795f7f2910f2cb1e2eecebcab5768bb"
)
HOST_RUNTIME_INVOKER_CONTRACT_SHA256: Final = (
    "sha256:607bf719d8a976569c50d7cfe8604ab341843dad00d3eef8784e1dc6cfd9b88d"
)
HOST_PROCESS_ENVIRONMENT: Final = (
    ("LANG", "C"),
    ("LC_ALL", "C"),
    ("PATH", "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"),
)
_CAPTURE_CHUNK_BYTES: Final = 65_536

AUTHORING_ROOT_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-authoring-v1"
)
AUTHORING_RECORD_RELATIVE: Final = AUTHORING_ROOT_RELATIVE / "authoring.json"
AUTHORING_REGISTRY_RELATIVE: Final = AUTHORING_ROOT_RELATIVE / "SHA256SUMS"
AUTHORING_MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/stage3b_qwake_lc4_host_runtime_invoker.py"
)
AUTHORING_VERIFIER_RELATIVE: Final = Path(
    "scripts/verify_stage3b_qwake_lc4_host_runtime_invoker_authoring.py"
)
AUTHORING_TEST_RELATIVE: Final = Path(
    "tests/unit/test_stage3b_qwake_lc4_host_runtime_invoker_authoring.py"
)

__all__ = [
    "AUTHORING_HEAD_COMMIT",
    "AUTHORING_MERGE_COMMIT",
    "HOST_PROCESS_ENVIRONMENT",
    "HOST_RUNTIME_INVOKER_IMPLEMENTATION_ID",
    "HOST_RUNTIME_INVOKER_IMPLEMENTATION_STATUS",
    "HostRuntimeInvocationOutcome",
    "HostRuntimeInvokerImplementationState",
    "QWakeLC4HostRuntimeInvokerImplementationError",
    "StreamCapture",
    "build_host_runtime_invoker_implementation_state",
    "invoke_one_shot_host_runtime",
    "validate_host_runtime_invoker_implementation_state",
    "verify_host_runtime_invoker_implementation_prerequisites",
]


class QWakeLC4HostRuntimeInvokerImplementationError(RuntimeError):
    """Raised when the bounded host invoker cannot preserve its contract."""


class HostChildProcess(Protocol):
    """Typed child-process surface used by the bounded runner."""

    pid: int
    stdout: BinaryIO | None
    stderr: BinaryIO | None
    returncode: int | None

    def poll(self) -> int | None:
        """Return the child status without blocking."""

        ...

    def wait(self, timeout: float | None = None) -> int:
        """Wait for the child and return its status."""

        ...


class ProcessSpawner(Protocol):
    """Typed injectable process factory."""

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
        """Spawn one child from an exact argv vector."""

        ...


ImageInspector = Callable[..., LocalImageInspection]
SignalSender = Callable[[int, int], None]


@dataclass(frozen=True)
class HostRuntimeInvokerImplementationState:
    """Machine-checkable implementation state with repository effects closed."""

    schema_version: int
    implementation_id: str
    status: str
    implementation_base_commit: str
    authoring_head_commit: str
    authoring_merge_commit: str
    authoring_merged_at_utc: str
    authoring_pr_number: int
    authoring_record_sha256: str
    authoring_registry_sha256: str
    authoring_module_sha256: str
    authoring_verifier_sha256: str
    authoring_test_sha256: str
    contract_id: str
    contract_sha256: str
    exact_argv_only: bool
    shell_interpretation_forbidden: bool
    environment_inheritance_forbidden: bool
    working_directory_override_forbidden: bool
    process_group_required: bool
    signal_forwarding_required: bool
    bounded_output_capture_required: bool
    automatic_retry_after_spawn_forbidden: bool
    host_execution_lease_write_forbidden: bool
    prelaunch_image_inspection_count: int
    prelaunch_materialization_count: int
    subprocess_popen_call_limit: int
    host_runtime_invoker_contract_present: bool
    host_runtime_invoker_implementation_present: bool
    host_runtime_invoker_present: bool
    host_runtime_invoker_executable: bool
    host_docker_run_implemented: bool
    branch_runtime_execution_permitted: bool
    execution_lease_materialized: bool
    authorization_consumed: bool
    runtime_execution_started: bool
    runtime_execution_performed: bool
    engineering_evidence_present: bool
    scientific_execution_open: bool
    test_dataset_access: bool
    publication_permitted: bool
    local_compute_execution_open: bool
    state_sha256: str

    def require(self) -> None:
        exact: Mapping[str, object] = {
            "schema_version": 1,
            "implementation_id": HOST_RUNTIME_INVOKER_IMPLEMENTATION_ID,
            "status": HOST_RUNTIME_INVOKER_IMPLEMENTATION_STATUS,
            "implementation_base_commit": IMPLEMENTATION_BASE_COMMIT,
            "authoring_head_commit": AUTHORING_HEAD_COMMIT,
            "authoring_merge_commit": AUTHORING_MERGE_COMMIT,
            "authoring_merged_at_utc": AUTHORING_MERGED_AT_UTC,
            "authoring_pr_number": AUTHORING_PR_NUMBER,
            "authoring_record_sha256": AUTHORING_RECORD_SHA256,
            "authoring_registry_sha256": AUTHORING_REGISTRY_SHA256,
            "authoring_module_sha256": AUTHORING_MODULE_SHA256,
            "authoring_verifier_sha256": AUTHORING_VERIFIER_SHA256,
            "authoring_test_sha256": AUTHORING_TEST_SHA256,
            "contract_id": HOST_RUNTIME_INVOKER_CONTRACT_ID,
            "contract_sha256": HOST_RUNTIME_INVOKER_CONTRACT_SHA256,
            "exact_argv_only": True,
            "shell_interpretation_forbidden": True,
            "environment_inheritance_forbidden": True,
            "working_directory_override_forbidden": True,
            "process_group_required": True,
            "signal_forwarding_required": True,
            "bounded_output_capture_required": True,
            "automatic_retry_after_spawn_forbidden": True,
            "host_execution_lease_write_forbidden": True,
            "prelaunch_image_inspection_count": 2,
            "prelaunch_materialization_count": 2,
            "subprocess_popen_call_limit": 1,
            "host_runtime_invoker_contract_present": True,
            "host_runtime_invoker_implementation_present": True,
            "host_runtime_invoker_present": True,
            "host_runtime_invoker_executable": True,
            "host_docker_run_implemented": True,
            "branch_runtime_execution_permitted": False,
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
        for field_name, expected in exact.items():
            if getattr(self, field_name) != expected:
                raise QWakeLC4HostRuntimeInvokerImplementationError(
                    f"host-runtime-invoker implementation differs: {field_name}"
                )
        for value, field_name in (
            (self.authoring_record_sha256, "authoring_record_sha256"),
            (self.authoring_registry_sha256, "authoring_registry_sha256"),
            (self.authoring_module_sha256, "authoring_module_sha256"),
            (self.authoring_verifier_sha256, "authoring_verifier_sha256"),
            (self.authoring_test_sha256, "authoring_test_sha256"),
            (self.contract_sha256, "contract_sha256"),
            (self.state_sha256, "state_sha256"),
        ):
            _require_sha256(value, field_name)
        if self.state_sha256 != sha256_object(self._payload_without_digest()):
            raise QWakeLC4HostRuntimeInvokerImplementationError(
                "host-runtime-invoker implementation digest differs"
            )

    def _payload_without_digest(self) -> Mapping[str, object]:
        payload = asdict(self)
        payload.pop("state_sha256")
        return cast(Mapping[str, object], payload)

    def canonical_json(self) -> str:
        return canonical_json(asdict(self))


@dataclass(frozen=True)
class StreamCapture:
    """Bounded in-memory representation of one child output stream."""

    text: str
    captured_bytes: int
    total_bytes: int
    truncated: bool

    def require(self, limit_bytes: int) -> None:
        if limit_bytes <= 0:
            raise QWakeLC4HostRuntimeInvokerImplementationError(
                "stream capture limit is not positive"
            )
        if self.captured_bytes < 0 or self.total_bytes < self.captured_bytes:
            raise QWakeLC4HostRuntimeInvokerImplementationError(
                "stream capture byte counts differ"
            )
        if self.captured_bytes > limit_bytes:
            raise QWakeLC4HostRuntimeInvokerImplementationError(
                "stream capture exceeds its bound"
            )
        if self.truncated != (self.total_bytes > self.captured_bytes):
            raise QWakeLC4HostRuntimeInvokerImplementationError(
                "stream truncation flag differs"
            )
        if len(self.text.encode("utf-8", errors="replace")) < self.captured_bytes:
            raise QWakeLC4HostRuntimeInvokerImplementationError(
                "stream capture text differs from byte count"
            )


@dataclass(frozen=True)
class HostRuntimeInvocationOutcome:
    """Terminal in-memory host observation; no command or log is persisted."""

    schema_version: int
    implementation_id: str
    contract_sha256: str
    command_sha256: str
    image_inspection_sha256: str
    classification: str
    return_code: int
    timed_out: bool
    forwarded_signals: tuple[str, ...]
    stdout: StreamCapture
    stderr: StreamCapture
    child_spawn_count: int
    shell_interpretation_used: bool
    environment_inherited: bool
    host_execution_lease_written: bool
    automatic_retry_performed: bool
    command_persisted: bool
    host_log_persisted: bool
    outcome_sha256: str

    def require(self, contract: HostRuntimeInvokerContract) -> None:
        exact: Mapping[str, object] = {
            "schema_version": 1,
            "implementation_id": HOST_RUNTIME_INVOKER_IMPLEMENTATION_ID,
            "contract_sha256": contract.contract_sha256,
            "child_spawn_count": 1,
            "shell_interpretation_used": False,
            "environment_inherited": False,
            "host_execution_lease_written": False,
            "automatic_retry_performed": False,
            "command_persisted": False,
            "host_log_persisted": False,
        }
        for field_name, expected in exact.items():
            if getattr(self, field_name) != expected:
                raise QWakeLC4HostRuntimeInvokerImplementationError(
                    f"host invocation outcome differs: {field_name}"
                )
        if self.classification not in {
            "success",
            "nonzero_return_code",
            "child_signal",
            "timeout",
            "forwarded_signal",
        }:
            raise QWakeLC4HostRuntimeInvokerImplementationError(
                "host invocation classification differs"
            )
        if self.timed_out != (self.classification == "timeout"):
            raise QWakeLC4HostRuntimeInvokerImplementationError(
                "host invocation timeout classification differs"
            )
        _require_sha256(self.command_sha256, "command_sha256")
        _require_sha256(
            self.image_inspection_sha256,
            "image_inspection_sha256",
        )
        _require_sha256(self.outcome_sha256, "outcome_sha256")
        self.stdout.require(contract.stdout_capture_limit_bytes)
        self.stderr.require(contract.stderr_capture_limit_bytes)
        if self.outcome_sha256 != sha256_object(self._payload_without_digest()):
            raise QWakeLC4HostRuntimeInvokerImplementationError(
                "host invocation outcome digest differs"
            )

    def _payload_without_digest(self) -> Mapping[str, object]:
        payload = asdict(self)
        payload.pop("outcome_sha256")
        return cast(Mapping[str, object], payload)


def verify_host_runtime_invoker_implementation_prerequisites(
    project_root: Path,
) -> tuple[HostRuntimeInvokerContract, str, str]:
    """Verify the merged authoring package and the absence of effects."""

    root = project_root.expanduser().resolve()
    _require_effect_boundary_closed(root)
    record_path = root / AUTHORING_RECORD_RELATIVE
    registry_path = root / AUTHORING_REGISTRY_RELATIVE
    _verify_single_file_registry(
        registry_path,
        root / AUTHORING_ROOT_RELATIVE,
        "authoring.json",
    )
    if _sha256_file(record_path) != AUTHORING_RECORD_SHA256:
        raise QWakeLC4HostRuntimeInvokerImplementationError(
            "authoring record SHA-256 differs"
        )
    if _sha256_file(registry_path) != AUTHORING_REGISTRY_SHA256:
        raise QWakeLC4HostRuntimeInvokerImplementationError(
            "authoring registry SHA-256 differs"
        )
    for relative, expected_sha256 in (
        (AUTHORING_MODULE_RELATIVE, AUTHORING_MODULE_SHA256),
        (AUTHORING_VERIFIER_RELATIVE, AUTHORING_VERIFIER_SHA256),
        (AUTHORING_TEST_RELATIVE, AUTHORING_TEST_SHA256),
    ):
        if _sha256_file(root / relative) != expected_sha256:
            raise QWakeLC4HostRuntimeInvokerImplementationError(
                f"authoring source SHA-256 differs: {relative}"
            )
    record = _read_json_object(record_path)
    source = _as_mapping(record.get("source"), "authoring source")
    contracts = _as_mapping(record.get("contracts"), "authoring contracts")
    gates = _as_mapping(record.get("gates"), "authoring gates")
    exact_source: Mapping[str, object] = {
        "implementation_head_commit": (
            "f8c1465ef326cb2dbe752c2900ab371a8b669284"
        ),
        "implementation_merge_commit": (
            "be6486a9e3670343132f2c863a5a0cd5969ee9f6"
        ),
    }
    for field_name, expected_value in exact_source.items():
        if source.get(field_name) != expected_value:
            raise QWakeLC4HostRuntimeInvokerImplementationError(
                f"authoring source differs: {field_name}"
            )
    if contracts.get("contract_sha256") != HOST_RUNTIME_INVOKER_CONTRACT_SHA256:
        raise QWakeLC4HostRuntimeInvokerImplementationError(
            "authoring contract SHA-256 differs"
        )
    expected_gates: Mapping[str, object] = {
        "host_runtime_invoker_contract_present": True,
        "host_runtime_invoker_present": False,
        "host_runtime_invoker_executable": False,
        "host_docker_run_implemented": False,
        "branch_runtime_execution_permitted": False,
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
    for field_name, expected_gate in expected_gates.items():
        if gates.get(field_name) != expected_gate:
            raise QWakeLC4HostRuntimeInvokerImplementationError(
                f"authoring gate differs: {field_name}"
            )
    contract = build_host_runtime_invoker_contract(root)
    validate_host_runtime_invoker_contract(contract, root)
    if contract.contract_sha256 != HOST_RUNTIME_INVOKER_CONTRACT_SHA256:
        raise QWakeLC4HostRuntimeInvokerImplementationError(
            "reconstructed authoring contract SHA-256 differs"
        )
    return contract, _sha256_file(record_path), _sha256_file(registry_path)


def build_host_runtime_invoker_implementation_state(
    project_root: Path,
) -> HostRuntimeInvokerImplementationState:
    """Build the implementation state without inspecting or spawning Docker."""

    contract, record_sha256, registry_sha256 = (
        verify_host_runtime_invoker_implementation_prerequisites(project_root)
    )
    payload: dict[str, object] = {
        "schema_version": 1,
        "implementation_id": HOST_RUNTIME_INVOKER_IMPLEMENTATION_ID,
        "status": HOST_RUNTIME_INVOKER_IMPLEMENTATION_STATUS,
        "implementation_base_commit": IMPLEMENTATION_BASE_COMMIT,
        "authoring_head_commit": AUTHORING_HEAD_COMMIT,
        "authoring_merge_commit": AUTHORING_MERGE_COMMIT,
        "authoring_merged_at_utc": AUTHORING_MERGED_AT_UTC,
        "authoring_pr_number": AUTHORING_PR_NUMBER,
        "authoring_record_sha256": record_sha256,
        "authoring_registry_sha256": registry_sha256,
        "authoring_module_sha256": AUTHORING_MODULE_SHA256,
        "authoring_verifier_sha256": AUTHORING_VERIFIER_SHA256,
        "authoring_test_sha256": AUTHORING_TEST_SHA256,
        "contract_id": contract.contract_id,
        "contract_sha256": contract.contract_sha256,
        "exact_argv_only": True,
        "shell_interpretation_forbidden": True,
        "environment_inheritance_forbidden": True,
        "working_directory_override_forbidden": True,
        "process_group_required": True,
        "signal_forwarding_required": True,
        "bounded_output_capture_required": True,
        "automatic_retry_after_spawn_forbidden": True,
        "host_execution_lease_write_forbidden": True,
        "prelaunch_image_inspection_count": 2,
        "prelaunch_materialization_count": 2,
        "subprocess_popen_call_limit": 1,
        "host_runtime_invoker_contract_present": True,
        "host_runtime_invoker_implementation_present": True,
        "host_runtime_invoker_present": True,
        "host_runtime_invoker_executable": True,
        "host_docker_run_implemented": True,
        "branch_runtime_execution_permitted": False,
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
    state = HostRuntimeInvokerImplementationState(
        **cast(Any, payload),
        state_sha256=sha256_object(payload),
    )
    state.require()
    return state


def validate_host_runtime_invoker_implementation_state(
    state: HostRuntimeInvokerImplementationState,
    project_root: Path,
) -> None:
    """Reconstruct and require the exact implementation state."""

    state.require()
    expected = build_host_runtime_invoker_implementation_state(project_root)
    if state != expected:
        raise QWakeLC4HostRuntimeInvokerImplementationError(
            "host-runtime-invoker implementation state differs"
        )


def invoke_one_shot_host_runtime(
    project_root: Path,
    *,
    host_resources: Mapping[str, str],
    claimed_at_utc: str,
    operator_acknowledgement: str,
    process_spawner: ProcessSpawner | None = None,
    image_inspector: ImageInspector | None = None,
    signal_sender: SignalSender | None = None,
) -> HostRuntimeInvocationOutcome:
    """Perform the exact one-shot host boundary.

    This function is intentionally not called by the implementation verifier or
    repository test suite with its default adapters. A caller must invoke it
    explicitly from a separately authorized execution operation.
    """

    root = project_root.expanduser().resolve()
    state = build_host_runtime_invoker_implementation_state(root)
    state.require()
    contract = build_host_runtime_invoker_contract(root)
    inspector: ImageInspector = (
        image_inspector or inspect_local_immutable_image
    )
    spawner: ProcessSpawner = process_spawner or _spawn_process
    sender: SignalSender = signal_sender or os.killpg

    first_inspection = inspector(
        root,
        timeout_seconds=contract.image_inspection_timeout_seconds,
    )
    first_materialized = materialize_one_shot_invocation(
        root,
        image_inspection=first_inspection,
        host_resources=host_resources,
        claimed_at_utc=claimed_at_utc,
        operator_acknowledgement=operator_acknowledgement,
    )
    validate_materialized_one_shot_invocation(
        first_materialized,
        root,
        image_inspection=first_inspection,
        host_resources=host_resources,
        claimed_at_utc=claimed_at_utc,
        operator_acknowledgement=operator_acknowledgement,
    )

    second_inspection = inspector(
        root,
        timeout_seconds=contract.image_inspection_timeout_seconds,
    )
    if second_inspection != first_inspection:
        raise QWakeLC4HostRuntimeInvokerImplementationError(
            "immutable image changed between prelaunch inspections"
        )
    second_materialized = materialize_one_shot_invocation(
        root,
        image_inspection=second_inspection,
        host_resources=host_resources,
        claimed_at_utc=claimed_at_utc,
        operator_acknowledgement=operator_acknowledgement,
    )
    validate_materialized_one_shot_invocation(
        second_materialized,
        root,
        image_inspection=second_inspection,
        host_resources=host_resources,
        claimed_at_utc=claimed_at_utc,
        operator_acknowledgement=operator_acknowledgement,
    )
    if second_materialized != first_materialized:
        raise QWakeLC4HostRuntimeInvokerImplementationError(
            "canonical invocation changed before child spawn"
        )

    verify_host_runtime_invoker_implementation_prerequisites(root)
    return _run_bounded_child(
        contract,
        second_materialized,
        root,
        process_spawner=spawner,
        signal_sender=sender,
    )


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
        raise QWakeLC4HostRuntimeInvokerImplementationError(
            "default process-spawn controls differ"
        )
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


def _run_bounded_child(
    contract: HostRuntimeInvokerContract,
    materialized: MaterializedOneShotInvocation,
    project_root: Path,
    *,
    process_spawner: ProcessSpawner,
    signal_sender: SignalSender,
) -> HostRuntimeInvocationOutcome:
    if threading.current_thread() is not threading.main_thread():
        raise QWakeLC4HostRuntimeInvokerImplementationError(
            "host invoker must run in the main thread for signal forwarding"
        )
    materialized.require()
    if materialized.argv[:2] != contract.host_execution_argv_prefix:
        raise QWakeLC4HostRuntimeInvokerImplementationError(
            "materialized argv is not the contracted docker run vector"
        )
    _require_effect_boundary_closed(project_root)

    host_environment = dict(HOST_PROCESS_ENVIRONMENT)
    try:
        process = process_spawner(
            materialized.argv,
            cwd=project_root,
            env=host_environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            start_new_session=True,
            close_fds=True,
        )
    except OSError as exc:
        raise QWakeLC4HostRuntimeInvokerImplementationError(
            "host child spawn failed before a child process was created"
        ) from exc

    if process.pid <= 0:
        raise QWakeLC4HostRuntimeInvokerImplementationError(
            "spawned child process identifier differs"
        )
    if process.stdout is None or process.stderr is None:
        _terminate_unusable_child(process, signal_sender)
        raise QWakeLC4HostRuntimeInvokerImplementationError(
            "spawned child process streams differ"
        )

    stdout_buffer = _CaptureBuffer(contract.stdout_capture_limit_bytes)
    stderr_buffer = _CaptureBuffer(contract.stderr_capture_limit_bytes)
    stdout_thread = _capture_thread(process.stdout, stdout_buffer, "stdout")
    stderr_thread = _capture_thread(process.stderr, stderr_buffer, "stderr")
    stdout_thread.start()
    stderr_thread.start()

    forwarded: list[str] = []
    forwarding_errors: list[str] = []
    timed_out = False
    return_code: int | None = None
    terminal_error: Exception | None = None
    try:
        try:
            with _forward_child_signals(
                process.pid,
                signal_sender,
                forwarded,
                forwarding_errors,
            ):
                try:
                    return_code = process.wait(
                        timeout=float(contract.runtime_timeout_seconds)
                    )
                except subprocess.TimeoutExpired:
                    timed_out = True
                    return_code = _terminate_timed_out_child(
                        process,
                        signal_sender,
                        float(contract.termination_grace_seconds),
                    )
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            terminal_error = exc
            _terminate_unusable_child(process, signal_sender)
    finally:
        stdout_thread.join()
        stderr_thread.join()

    if terminal_error is not None:
        raise QWakeLC4HostRuntimeInvokerImplementationError(
            "host child process control failed after spawn"
        ) from terminal_error
    if return_code is None:
        raise QWakeLC4HostRuntimeInvokerImplementationError(
            "host child process returned no terminal status"
        )
    if stdout_buffer.error is not None or stderr_buffer.error is not None:
        raise QWakeLC4HostRuntimeInvokerImplementationError(
            "bounded child output capture failed"
        )
    if forwarding_errors:
        raise QWakeLC4HostRuntimeInvokerImplementationError(
            "child signal forwarding failed"
        )

    stdout_capture = stdout_buffer.freeze()
    stderr_capture = stderr_buffer.freeze()
    if timed_out:
        classification = "timeout"
    elif forwarded:
        classification = "forwarded_signal"
    elif return_code == 0:
        classification = "success"
    elif return_code < 0:
        classification = "child_signal"
    else:
        classification = "nonzero_return_code"

    payload: dict[str, object] = {
        "schema_version": 1,
        "implementation_id": HOST_RUNTIME_INVOKER_IMPLEMENTATION_ID,
        "contract_sha256": contract.contract_sha256,
        "command_sha256": materialized.command_sha256,
        "image_inspection_sha256": materialized.image_inspection_sha256,
        "classification": classification,
        "return_code": return_code,
        "timed_out": timed_out,
        "forwarded_signals": tuple(forwarded),
        "stdout": stdout_capture,
        "stderr": stderr_capture,
        "child_spawn_count": 1,
        "shell_interpretation_used": False,
        "environment_inherited": False,
        "host_execution_lease_written": False,
        "automatic_retry_performed": False,
        "command_persisted": False,
        "host_log_persisted": False,
    }
    digest_payload = dict(payload)
    digest_payload["stdout"] = asdict(stdout_capture)
    digest_payload["stderr"] = asdict(stderr_capture)
    outcome = HostRuntimeInvocationOutcome(
        **cast(Any, payload),
        outcome_sha256=sha256_object(digest_payload),
    )
    outcome.require(contract)
    return outcome


class _CaptureBuffer:
    def __init__(self, limit_bytes: int) -> None:
        if limit_bytes <= 0:
            raise QWakeLC4HostRuntimeInvokerImplementationError(
                "capture limit is not positive"
            )
        self.limit_bytes = limit_bytes
        self.data = bytearray()
        self.total_bytes = 0
        self.error: Exception | None = None

    def consume(self, chunk: bytes) -> None:
        self.total_bytes += len(chunk)
        remaining = self.limit_bytes - len(self.data)
        if remaining > 0:
            self.data.extend(chunk[:remaining])

    def freeze(self) -> StreamCapture:
        captured = bytes(self.data)
        result = StreamCapture(
            text=captured.decode("utf-8", errors="replace"),
            captured_bytes=len(captured),
            total_bytes=self.total_bytes,
            truncated=self.total_bytes > len(captured),
        )
        result.require(self.limit_bytes)
        return result


def _capture_thread(
    stream: BinaryIO,
    buffer: _CaptureBuffer,
    name: str,
) -> threading.Thread:
    def read_stream() -> None:
        try:
            while True:
                chunk = stream.read(_CAPTURE_CHUNK_BYTES)
                if not chunk:
                    break
                buffer.consume(chunk)
        except Exception as exc:  # pragma: no cover - defensive boundary
            buffer.error = exc
        finally:
            stream.close()

    return threading.Thread(
        target=read_stream,
        name=f"qwake-lc4-host-invoker-{name}",
        daemon=False,
    )


@contextmanager
def _forward_child_signals(
    process_group_id: int,
    signal_sender: SignalSender,
    forwarded: list[str],
    errors: list[str],
) -> Iterator[None]:
    old_handlers: dict[signal.Signals, Any] = {}

    def handler(signum: int, _frame: FrameType | None) -> None:
        try:
            signal_sender(process_group_id, signum)
            forwarded.append(signal.Signals(signum).name)
        except (OSError, ValueError) as exc:
            errors.append(type(exc).__name__)

    try:
        for forwarded_signal in (signal.SIGINT, signal.SIGTERM):
            old_handlers[forwarded_signal] = signal.getsignal(forwarded_signal)
            signal.signal(forwarded_signal, handler)
        yield
    finally:
        for restored_signal, old_handler in old_handlers.items():
            signal.signal(restored_signal, old_handler)


def _terminate_timed_out_child(
    process: HostChildProcess,
    signal_sender: SignalSender,
    grace_seconds: float,
) -> int:
    if grace_seconds <= 0:
        raise QWakeLC4HostRuntimeInvokerImplementationError(
            "termination grace period is not positive"
        )
    _send_group_signal_if_running(process, signal_sender, signal.SIGTERM)
    try:
        return process.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        _send_group_signal_if_running(process, signal_sender, signal.SIGKILL)
        return process.wait(timeout=None)


def _terminate_unusable_child(
    process: HostChildProcess,
    signal_sender: SignalSender,
) -> None:
    if process.pid <= 0:
        return
    _send_group_signal_if_running(process, signal_sender, signal.SIGKILL)
    process.wait(timeout=None)


def _send_group_signal_if_running(
    process: HostChildProcess,
    signal_sender: SignalSender,
    signum: int,
) -> None:
    if process.poll() is None:
        try:
            signal_sender(process.pid, signum)
        except ProcessLookupError:
            if process.poll() is None:
                raise


def _require_effect_boundary_closed(root: Path) -> None:
    lease = root / EXECUTION_LEASE_RELATIVE
    output = root / AUTHORIZED_OUTPUT_ROOT
    if lease.exists() or lease.is_symlink():
        raise QWakeLC4HostRuntimeInvokerImplementationError(
            "repository execution lease already exists"
        )
    if output.exists() or output.is_symlink():
        raise QWakeLC4HostRuntimeInvokerImplementationError(
            "repository runtime output already exists"
        )
    staging = tuple(output.parent.glob(f".{output.name}.staging-*"))
    if staging:
        raise QWakeLC4HostRuntimeInvokerImplementationError(
            "repository runtime staging tree already exists"
        )


def _verify_single_file_registry(
    registry_path: Path,
    base: Path,
    required_relative: str,
) -> None:
    if not registry_path.is_file() or registry_path.is_symlink():
        raise QWakeLC4HostRuntimeInvokerImplementationError(
            "authoring registry is absent or non-regular"
        )
    lines = tuple(
        line
        for line in registry_path.read_text(encoding="utf-8").splitlines()
        if line
    )
    if len(lines) != 1 or "  " not in lines[0]:
        raise QWakeLC4HostRuntimeInvokerImplementationError(
            "authoring registry scope differs"
        )
    digest, relative = lines[0].split("  ", 1)
    if relative != required_relative:
        raise QWakeLC4HostRuntimeInvokerImplementationError(
            "authoring registry path differs"
        )
    target = base / relative
    if _sha256_file(target) != "sha256:" + digest:
        raise QWakeLC4HostRuntimeInvokerImplementationError(
            "authoring registry digest differs"
        )


def _read_json_object(path: Path) -> dict[str, object]:
    if not path.is_file() or path.is_symlink():
        raise QWakeLC4HostRuntimeInvokerImplementationError(
            f"JSON source is absent or non-regular: {path}"
        )
    try:
        value: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise QWakeLC4HostRuntimeInvokerImplementationError(
            f"JSON source cannot be decoded: {path}"
        ) from exc
    if not isinstance(value, dict):
        raise QWakeLC4HostRuntimeInvokerImplementationError(
            f"JSON source is not an object: {path}"
        )
    return cast(dict[str, object], value)


def _as_mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise QWakeLC4HostRuntimeInvokerImplementationError(
            f"{field_name} is not an object"
        )
    return cast(Mapping[str, object], value)


def _sha256_file(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise QWakeLC4HostRuntimeInvokerImplementationError(
            f"required regular file is absent: {path}"
        )
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _require_sha256(value: str, field_name: str) -> None:
    if not value.startswith("sha256:") or len(value) != 71:
        raise QWakeLC4HostRuntimeInvokerImplementationError(
            f"{field_name} is not SHA-256"
        )
