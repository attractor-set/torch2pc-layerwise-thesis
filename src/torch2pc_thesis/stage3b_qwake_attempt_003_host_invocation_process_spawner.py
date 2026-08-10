"""Bounded host process spawner for QWake Attempt-003.

The module binds the already-reconciled durable command record to exactly one
future host-side child process. Importing and validating the module are
non-effectful. The only function that may spawn a process is
`spawn_attempt_003_persisted_command`, and tests/verifiers use injected fake
spawners rather than the default subprocess adapter.
"""

from __future__ import annotations

import hashlib
import json
import os
import signal
import subprocess
import threading
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from types import FrameType
from typing import Any, BinaryIO, Final, Protocol, cast

ATTEMPT_ID: Final = "stage3b-qwake-lc4-runtime-validation-v1-attempt-003"
CONTRACT_ID: Final = (
    "stage3b-qwake-attempt-003-host-invocation-process-spawner-contract-v1"
)
CONTRACT_STATUS: Final = (
    "attempt_003_host_invocation_process_spawner_implemented_not_invoked"
)

AUTHORIZED_PARENT_HEAD: Final = "34ec64823bff556706190c2f2c93b3a0653e293d"
AUTHORIZED_PARENT_TREE: Final = "b851597ba271cea6e0b2e5868a654cf5b52b43f2"
AUTHORIZED_BRANCH: Final = (
    "research/stage3b-qwake-attempt-003-host-invocation-process-spawner"
)

COMMAND_MATERIALIZATION_HEAD: Final = "f3b75002a97b3bf31b11e29b527e450a2ffd4dc2"
COMMAND_MATERIALIZATION_MERGE: Final = "34ec64823bff556706190c2f2c93b3a0653e293d"
COMMAND_MATERIALIZATION_CONTRACT_SHA256: Final = (
    "sha256:11e1f76e05c31a4466488dbfe4dd6e3ec238bf7140850fee15a11a8acd984d7b"
)
COMMAND_TEMPLATE_SHA256: Final = (
    "sha256:01fdd895e65ee59970e9a67c500ec4523e0039d468fe8e9553b0e4e2a53a7d89"
)
AUTHORITATIVE_CLAIMED_AT_UTC: Final = "2026-08-10T14:47:42Z"
INVOCATION_SHA256: Final = (
    "sha256:91e762ba21c1d72b9282a3b0419206d5de1c3f88aac82a63dad76e27f0321c24"
)
COMMAND_RECORD_SHA256: Final = (
    "sha256:3ea2d34826fdd5846eee7cdfa84833f6b5e2293cfef76b76a51b64862cb143ca"
)
COMMAND_RECORD_FILE_SHA256: Final = (
    "f519d0821305171aa5c6ed05cad772f9fd85e93601fa1ec551e23058939d1ba6"
)
COMMAND_RECORD_RELATIVE: Final = Path(
    "results/stage-3/"
    "qwake-lc4-runtime-validation-v1-attempt-003.host-invocation-command.json"
)

AUTHORIZATION_SHA256: Final = (
    "sha256:46baed5cebc1efe4abf68c21652775eee5c1123df09465d332c151303d890d63"
)
AUTHORIZATION_CONSUMPTION_OWNER: Final = "container_entrypoint_atomic_execution_lease"
LEASE_CLAIM_OWNER: Final = "container_entrypoint_atomic_execution_lease"

OUTPUT_ROOT: Final = Path(
    "results/stage-3/qwake-lc4-runtime-validation-v1-attempt-003"
)
LEASE_V1: Final = Path(str(OUTPUT_ROOT) + ".execution-lease.json")
LEASE_V2: Final = Path(str(OUTPUT_ROOT) + ".execution-lease-v2.json")
HOST_OUTCOME: Final = Path(str(OUTPUT_ROOT) + ".host-outcome.json")

SPAWN_COUNT_LIMIT: Final = 1
RUNTIME_TIMEOUT_SECONDS: Final = 7200
TERMINATION_GRACE_SECONDS: Final = 30
STDOUT_CAPTURE_LIMIT_BYTES: Final = 1_048_576
STDERR_CAPTURE_LIMIT_BYTES: Final = 1_048_576
FORWARDED_SIGNALS: Final = ("SIGINT", "SIGTERM")
_CAPTURE_CHUNK_BYTES: Final = 65_536

HOST_PROCESS_ENVIRONMENT: Final = (
    ("LANG", "C"),
    ("LC_ALL", "C"),
    ("PATH", "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"),
)

POST_MERGE_NEXT_GATE: Final = "attempt003_one_shot_execution"


class ProcessSpawnerError(RuntimeError):
    """Raised when the bounded process-spawner boundary differs."""


@dataclass(frozen=True)
class PersistedHostCommand:
    record_sha256: str
    file_sha256: str
    claimed_at_utc: str
    invocation_sha256: str
    command_template_sha256: str
    argv: tuple[str, ...]
    environment: tuple[tuple[str, str], ...]
    mount_sources: tuple[str, ...]

    def require(self) -> None:
        exact = {
            "record_sha256": COMMAND_RECORD_SHA256,
            "file_sha256": COMMAND_RECORD_FILE_SHA256,
            "claimed_at_utc": AUTHORITATIVE_CLAIMED_AT_UTC,
            "invocation_sha256": INVOCATION_SHA256,
            "command_template_sha256": COMMAND_TEMPLATE_SHA256,
        }
        for name, expected in exact.items():
            if getattr(self, name) != expected:
                raise ProcessSpawnerError(f"persisted command differs: {name}")
        if self.argv[:2] != ("docker", "run"):
            raise ProcessSpawnerError("persisted argv prefix differs")
        matches = [
            index
            for index, value in enumerate(self.argv)
            if value == "--claimed-at-utc"
        ]
        if len(matches) != 1:
            raise ProcessSpawnerError("persisted claimed-at marker count differs")
        index = matches[0]
        if index + 1 >= len(self.argv):
            raise ProcessSpawnerError("persisted claimed-at value is absent")
        if self.argv[index + 1] != AUTHORITATIVE_CLAIMED_AT_UTC:
            raise ProcessSpawnerError("persisted claimed-at value differs")
        if not self.environment:
            raise ProcessSpawnerError("persisted environment is empty")
        if len(self.mount_sources) != 3:
            raise ProcessSpawnerError("persisted mount-source count differs")


@dataclass(frozen=True)
class StreamCapture:
    text: str
    captured_bytes: int
    total_bytes: int
    truncated: bool

    def require(self, limit_bytes: int) -> None:
        if self.captured_bytes < 0 or self.total_bytes < self.captured_bytes:
            raise ProcessSpawnerError("stream capture byte counts differ")
        if self.captured_bytes > limit_bytes:
            raise ProcessSpawnerError("stream capture exceeds bound")
        if self.truncated != (self.total_bytes > self.captured_bytes):
            raise ProcessSpawnerError("stream capture truncation flag differs")


@dataclass(frozen=True)
class HostProcessOutcome:
    contract_sha256: str
    command_record_sha256: str
    invocation_sha256: str
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
    outcome_sha256: str

    def require(self, contract: Mapping[str, object]) -> None:
        if self.contract_sha256 != contract.get("contract_sha256"):
            raise ProcessSpawnerError("outcome contract SHA differs")
        if self.command_record_sha256 != COMMAND_RECORD_SHA256:
            raise ProcessSpawnerError("outcome command-record SHA differs")
        if self.invocation_sha256 != INVOCATION_SHA256:
            raise ProcessSpawnerError("outcome invocation SHA differs")
        if self.child_spawn_count != 1:
            raise ProcessSpawnerError("outcome spawn count differs")
        if self.shell_interpretation_used:
            raise ProcessSpawnerError("outcome used shell interpretation")
        if self.environment_inherited:
            raise ProcessSpawnerError("outcome inherited environment")
        if self.host_execution_lease_written:
            raise ProcessSpawnerError("host wrote execution lease")
        if self.automatic_retry_performed:
            raise ProcessSpawnerError("automatic retry was performed")
        self.stdout.require(STDOUT_CAPTURE_LIMIT_BYTES)
        self.stderr.require(STDERR_CAPTURE_LIMIT_BYTES)
        if self.classification not in {
            "success",
            "nonzero_return_code",
            "child_signal",
            "forwarded_signal",
            "timeout",
        }:
            raise ProcessSpawnerError("outcome classification differs")
        payload = _outcome_payload(self)
        if self.outcome_sha256 != sha256_object(payload):
            raise ProcessSpawnerError("outcome semantic SHA differs")


class HostChildProcess(Protocol):
    pid: int
    stdout: BinaryIO | None
    stderr: BinaryIO | None

    def wait(self, timeout: float | None = None) -> int:
        ...

    def poll(self) -> int | None:
        ...


class ProcessSpawner(Protocol):
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
        ...


class SignalSender(Protocol):
    def __call__(self, process_group_id: int, signum: int) -> None:
        ...


def _send_signal_to_process_group(
    process_group_id: int,
    signum: int,
) -> None:
    os.killpg(process_group_id, signum)


def canonical_json(value: object) -> str:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    )


def sha256_object(value: object) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def build_attempt_003_process_spawner_contract() -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": 1,
        "contract_id": CONTRACT_ID,
        "status": CONTRACT_STATUS,
        "attempt_id": ATTEMPT_ID,
        "authorized_parent_head": AUTHORIZED_PARENT_HEAD,
        "authorized_parent_tree": AUTHORIZED_PARENT_TREE,
        "authorized_branch": AUTHORIZED_BRANCH,
        "command_materialization_head_commit": COMMAND_MATERIALIZATION_HEAD,
        "command_materialization_merge_commit": COMMAND_MATERIALIZATION_MERGE,
        "command_materialization_contract_sha256": (
            COMMAND_MATERIALIZATION_CONTRACT_SHA256
        ),
        "command_template_sha256": COMMAND_TEMPLATE_SHA256,
        "authoritative_claimed_at_utc": AUTHORITATIVE_CLAIMED_AT_UTC,
        "invocation_sha256": INVOCATION_SHA256,
        "command_record_sha256": COMMAND_RECORD_SHA256,
        "command_record_file_sha256": COMMAND_RECORD_FILE_SHA256,
        "command_record_relative": COMMAND_RECORD_RELATIVE.as_posix(),
        "authorization_sha256": AUTHORIZATION_SHA256,
        "authorization_consumption_owner": AUTHORIZATION_CONSUMPTION_OWNER,
        "lease_claim_owner": LEASE_CLAIM_OWNER,
        "exact_persisted_command_only": True,
        "exact_argv_only": True,
        "shell_interpretation_forbidden": True,
        "host_process_environment": [list(item) for item in HOST_PROCESS_ENVIRONMENT],
        "environment_inheritance_forbidden": True,
        "working_directory_is_execution_root": True,
        "start_new_session_required": True,
        "close_fds_required": True,
        "spawn_count_limit": SPAWN_COUNT_LIMIT,
        "forwarded_signals": list(FORWARDED_SIGNALS),
        "runtime_timeout_seconds": RUNTIME_TIMEOUT_SECONDS,
        "termination_grace_seconds": TERMINATION_GRACE_SECONDS,
        "stdout_capture_limit_bytes": STDOUT_CAPTURE_LIMIT_BYTES,
        "stderr_capture_limit_bytes": STDERR_CAPTURE_LIMIT_BYTES,
        "automatic_retry_after_spawn_forbidden": True,
        "host_execution_lease_write_forbidden": True,
        "command_record_rewrite_forbidden": True,
        "command_record_delete_forbidden": True,
        "authoritative_host_command_materialized": True,
        "command_persisted": True,
        "process_spawner_contract_present": True,
        "host_process_spawner_present": True,
        "host_process_spawner_executable": True,
        "host_process_spawned": False,
        "docker_run_implemented": True,
        "docker_run_invoked": False,
        "container_created": False,
        "authorization_used": False,
        "authorization_consumed": False,
        "attempt_started": False,
        "execution_lease_materialized": False,
        "runtime_execution_permitted": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "runtime_invoked": False,
        "model_code_invoked": False,
        "dataset_accessed": False,
        "publication_permitted": False,
        "post_merge_next_gate": POST_MERGE_NEXT_GATE,
    }
    contract = dict(payload)
    contract["contract_sha256"] = sha256_object(payload)
    return contract


def validate_attempt_003_process_spawner_contract(value: object) -> None:
    if not isinstance(value, dict):
        raise ProcessSpawnerError("process-spawner contract must be an object")
    typed = cast(dict[str, object], value)
    expected = build_attempt_003_process_spawner_contract()
    if set(typed) != set(expected):
        raise ProcessSpawnerError("process-spawner contract keys differ")
    if typed != expected:
        raise ProcessSpawnerError("process-spawner contract values differ")
    payload = dict(typed)
    observed_sha = payload.pop("contract_sha256")
    if observed_sha != sha256_object(payload):
        raise ProcessSpawnerError("process-spawner contract semantic SHA differs")


def load_attempt_003_process_spawner_contract(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProcessSpawnerError("process-spawner contract JSON invalid") from exc
    validate_attempt_003_process_spawner_contract(value)
    return cast(dict[str, object], value)


def load_persisted_attempt_003_host_command(
    execution_root: Path,
    contract: Mapping[str, object],
) -> PersistedHostCommand:
    validate_attempt_003_process_spawner_contract(dict(contract))
    root = execution_root.expanduser().resolve()
    record_path = root / COMMAND_RECORD_RELATIVE
    if not record_path.is_file() or record_path.is_symlink():
        raise ProcessSpawnerError("durable command record is absent or non-regular")
    raw = record_path.read_bytes()
    file_sha = hashlib.sha256(raw).hexdigest()
    if file_sha != COMMAND_RECORD_FILE_SHA256:
        raise ProcessSpawnerError("durable command-record physical SHA differs")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ProcessSpawnerError("durable command record JSON invalid") from exc
    if not isinstance(value, dict):
        raise ProcessSpawnerError("durable command record must be an object")
    record = cast(dict[str, object], value)

    payload = dict(record)
    observed_record_sha = payload.pop("record_sha256", None)
    if not isinstance(observed_record_sha, str):
        raise ProcessSpawnerError("durable command-record semantic SHA is absent")
    if observed_record_sha != COMMAND_RECORD_SHA256:
        raise ProcessSpawnerError("durable command-record semantic SHA differs")
    if sha256_object(payload) != COMMAND_RECORD_SHA256:
        raise ProcessSpawnerError("durable command-record digest reconstruction differs")

    exact: Mapping[str, object] = {
        "claimed_at_utc": AUTHORITATIVE_CLAIMED_AT_UTC,
        "invocation_sha256": INVOCATION_SHA256,
        "command_template_sha256": COMMAND_TEMPLATE_SHA256,
        "authoritative_host_command_materialized": True,
        "command_persisted": True,
        "host_process_spawned": False,
        "docker_run_invoked": False,
        "container_created": False,
        "authorization_used": False,
        "authorization_consumed": False,
        "attempt_started": False,
        "execution_lease_materialized": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "runtime_execution_permitted": False,
        "model_code_invoked": False,
        "dataset_accessed": False,
        "publication_permitted": False,
    }
    for name, expected in exact.items():
        if record.get(name) != expected:
            raise ProcessSpawnerError(f"durable command-record field differs: {name}")

    argv_raw = record.get("argv")
    environment_raw = record.get("environment")
    mount_sources_raw = record.get("mount_sources")
    if not isinstance(argv_raw, list) or not all(
        isinstance(item, str) for item in argv_raw
    ):
        raise ProcessSpawnerError("durable argv differs")
    if not isinstance(environment_raw, list):
        raise ProcessSpawnerError("durable environment differs")
    environment: list[tuple[str, str]] = []
    for item in environment_raw:
        if (
            not isinstance(item, list)
            or len(item) != 2
            or not all(isinstance(value, str) for value in item)
        ):
            raise ProcessSpawnerError("durable environment pair differs")
        environment.append((item[0], item[1]))
    if not isinstance(mount_sources_raw, list) or not all(
        isinstance(item, str) for item in mount_sources_raw
    ):
        raise ProcessSpawnerError("durable mount sources differ")

    command = PersistedHostCommand(
        record_sha256=observed_record_sha,
        file_sha256=file_sha,
        claimed_at_utc=str(record["claimed_at_utc"]),
        invocation_sha256=str(record["invocation_sha256"]),
        command_template_sha256=str(record["command_template_sha256"]),
        argv=tuple(str(item) for item in argv_raw),
        environment=tuple(environment),
        mount_sources=tuple(str(item) for item in mount_sources_raw),
    )
    command.require()

    for source in command.mount_sources:
        candidate = Path(source).resolve()
        if root != candidate and root not in candidate.parents:
            raise ProcessSpawnerError("durable mount source escapes execution root")
        if not candidate.is_dir():
            raise ProcessSpawnerError("durable mount source is absent")
    return command


def spawn_attempt_003_persisted_command(
    execution_root: Path,
    contract: Mapping[str, object],
    *,
    process_spawner: ProcessSpawner | None = None,
    signal_sender: SignalSender | None = None,
) -> HostProcessOutcome:
    """Execute the exact persisted one-shot command.

    This function is never called by repository validation with the default
    process adapter. Actual invocation is a separate operator action after the
    implementation has merged and passed post-merge audit.
    """

    root = execution_root.expanduser().resolve()
    command = load_persisted_attempt_003_host_command(root, contract)
    _require_pre_spawn_effect_boundary(root)

    spawner: ProcessSpawner = (
        process_spawner if process_spawner is not None else _spawn_process
    )
    sender: SignalSender = (
        signal_sender
        if signal_sender is not None
        else _send_signal_to_process_group
    )
    return _run_bounded_child(
        root,
        contract,
        command,
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
        raise ProcessSpawnerError("default process-spawn controls differ")
    process = subprocess.Popen(  # noqa: S603
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
    execution_root: Path,
    contract: Mapping[str, object],
    command: PersistedHostCommand,
    *,
    process_spawner: ProcessSpawner,
    signal_sender: SignalSender,
) -> HostProcessOutcome:
    validate_attempt_003_process_spawner_contract(dict(contract))
    command.require()
    if threading.current_thread() is not threading.main_thread():
        raise ProcessSpawnerError("host process spawner must run in the main thread")
    _require_pre_spawn_effect_boundary(execution_root)

    host_environment = dict(HOST_PROCESS_ENVIRONMENT)
    try:
        process = process_spawner(
            command.argv,
            cwd=execution_root,
            env=host_environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            start_new_session=True,
            close_fds=True,
        )
    except OSError as exc:
        raise ProcessSpawnerError(
            "host child spawn failed before child creation"
        ) from exc

    if process.pid <= 0:
        raise ProcessSpawnerError("spawned child process identifier differs")
    if process.stdout is None or process.stderr is None:
        _terminate_unusable_child(process, signal_sender)
        raise ProcessSpawnerError("spawned child process streams differ")

    stdout_buffer = _CaptureBuffer(STDOUT_CAPTURE_LIMIT_BYTES)
    stderr_buffer = _CaptureBuffer(STDERR_CAPTURE_LIMIT_BYTES)
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
                        timeout=float(RUNTIME_TIMEOUT_SECONDS)
                    )
                except subprocess.TimeoutExpired:
                    timed_out = True
                    return_code = _terminate_timed_out_child(
                        process,
                        signal_sender,
                        float(TERMINATION_GRACE_SECONDS),
                    )
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            terminal_error = exc
            _terminate_unusable_child(process, signal_sender)
    finally:
        stdout_thread.join()
        stderr_thread.join()

    if terminal_error is not None:
        raise ProcessSpawnerError(
            "host child process control failed after spawn"
        ) from terminal_error
    if return_code is None:
        raise ProcessSpawnerError("host child process returned no terminal status")
    if stdout_buffer.error is not None or stderr_buffer.error is not None:
        raise ProcessSpawnerError("bounded child output capture failed")
    if forwarding_errors:
        raise ProcessSpawnerError("child signal forwarding failed")

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

    contract_sha256 = contract.get("contract_sha256")
    if not isinstance(contract_sha256, str):
        raise ProcessSpawnerError("process-spawner contract SHA is absent")

    payload: dict[str, object] = {
        "contract_sha256": contract_sha256,
        "command_record_sha256": command.record_sha256,
        "invocation_sha256": command.invocation_sha256,
        "classification": classification,
        "return_code": return_code,
        "timed_out": timed_out,
        "forwarded_signals": tuple(forwarded),
        "stdout": asdict(stdout_capture),
        "stderr": asdict(stderr_capture),
        "child_spawn_count": 1,
        "shell_interpretation_used": False,
        "environment_inherited": False,
        "host_execution_lease_written": False,
        "automatic_retry_performed": False,
    }
    outcome = HostProcessOutcome(
        contract_sha256=contract_sha256,
        command_record_sha256=command.record_sha256,
        invocation_sha256=command.invocation_sha256,
        classification=classification,
        return_code=return_code,
        timed_out=timed_out,
        forwarded_signals=tuple(forwarded),
        stdout=stdout_capture,
        stderr=stderr_capture,
        child_spawn_count=1,
        shell_interpretation_used=False,
        environment_inherited=False,
        host_execution_lease_written=False,
        automatic_retry_performed=False,
        outcome_sha256=sha256_object(payload),
    )
    outcome.require(contract)
    return outcome


def _outcome_payload(outcome: HostProcessOutcome) -> dict[str, object]:
    return {
        "contract_sha256": outcome.contract_sha256,
        "command_record_sha256": outcome.command_record_sha256,
        "invocation_sha256": outcome.invocation_sha256,
        "classification": outcome.classification,
        "return_code": outcome.return_code,
        "timed_out": outcome.timed_out,
        "forwarded_signals": outcome.forwarded_signals,
        "stdout": asdict(outcome.stdout),
        "stderr": asdict(outcome.stderr),
        "child_spawn_count": outcome.child_spawn_count,
        "shell_interpretation_used": outcome.shell_interpretation_used,
        "environment_inherited": outcome.environment_inherited,
        "host_execution_lease_written": outcome.host_execution_lease_written,
        "automatic_retry_performed": outcome.automatic_retry_performed,
    }


class _CaptureBuffer:
    def __init__(self, limit_bytes: int) -> None:
        if limit_bytes <= 0:
            raise ProcessSpawnerError("capture limit is not positive")
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
        name=f"qwake-attempt003-process-spawner-{name}",
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
        raise ProcessSpawnerError("termination grace period is not positive")
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


def _require_pre_spawn_effect_boundary(root: Path) -> None:
    for relative in (OUTPUT_ROOT, LEASE_V1, LEASE_V2, HOST_OUTCOME):
        if os.path.lexists(root / relative):
            raise ProcessSpawnerError(f"pre-spawn effect already exists: {relative}")
    parent = root / OUTPUT_ROOT.parent
    if parent.is_dir():
        staging = tuple(parent.glob(f".{OUTPUT_ROOT.name}.staging-*"))
        if staging:
            raise ProcessSpawnerError("pre-spawn runtime staging tree exists")

    results = root / "results"
    if not results.is_dir() or results.is_symlink():
        raise ProcessSpawnerError("execution results root differs")
    entries = {
        path.relative_to(results).as_posix()
        for path in results.rglob("*")
    }
    expected = {
        "stage-3",
        COMMAND_RECORD_RELATIVE.relative_to("results").as_posix(),
    }
    if entries != expected:
        raise ProcessSpawnerError("pre-spawn result scope differs")
