from __future__ import annotations

import ast
import hashlib
import json
import shutil
import signal
import subprocess
from dataclasses import replace
from io import BytesIO
from pathlib import Path
from typing import Any

import pytest

from torch2pc_thesis.stage3b_qwake_lc4_host_runtime_invoker import (
    HOST_RUNTIME_INVOKER_CONTRACT_ID,
    build_host_runtime_invoker_contract,
)
from torch2pc_thesis.stage3b_qwake_lc4_host_runtime_invoker_implementation import (
    HOST_PROCESS_ENVIRONMENT,
    HOST_RUNTIME_INVOKER_IMPLEMENTATION_ID,
    HOST_RUNTIME_INVOKER_IMPLEMENTATION_STATUS,
    QWakeLC4HostRuntimeInvokerImplementationError,
    build_host_runtime_invoker_implementation_state,
    invoke_one_shot_host_runtime,
    validate_host_runtime_invoker_implementation_state,
    verify_host_runtime_invoker_implementation_prerequisites,
)
from torch2pc_thesis.stage3b_qwake_lc4_invocation_authorization import (
    INVOCATION_OPERATOR_ACKNOWLEDGEMENT,
)
from torch2pc_thesis.stage3b_qwake_lc4_invocation_wrapper import (
    CONTAINER_IMAGE_ENTRYPOINT,
    build_one_shot_invocation_wrapper_contract,
)
from torch2pc_thesis.stage3b_qwake_lc4_invocation_wrapper_implementation import (
    FIXTURE_CLAIMED_AT_UTC,
    LocalImageInspection,
    load_frozen_image_identity,
    parse_local_image_inspection,
)

ROOT = Path(__file__).resolve().parents[2]
MODULE = (
    ROOT
    / "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_host_runtime_invoker_implementation.py"
)
VERIFIER = (
    ROOT
    / "scripts/"
    "verify_stage3b_qwake_lc4_host_runtime_invoker_implementation.py"
)
IMPLEMENTATION_ROOT = (
    ROOT
    / "experiments/frozen/"
    "stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-implementation-v1"
)


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _resources() -> dict[str, str]:
    return {
        "HOST_UID": "1000",
        "HOST_GID": "1000",
        "VIDEO_GID": "44",
        "RENDER_GID": "109",
        "HIP_VISIBLE_DEVICES": "0",
        "CPUSET_GPU": "0-7",
        "MEM_LIMIT": "48g",
        "SHM_SIZE": "8gb",
        "TMPFS_SIZE": "8g",
        "OMP_NUM_THREADS": "4",
        "MKL_NUM_THREADS": "4",
        "OPENBLAS_NUM_THREADS": "4",
        "NUMEXPR_NUM_THREADS": "4",
    }


def _inspection() -> LocalImageInspection:
    frozen = load_frozen_image_identity(ROOT)
    contract = build_one_shot_invocation_wrapper_contract(ROOT)
    raw: list[dict[str, Any]] = [
        {
            "Id": frozen.image_id,
            "RepoDigests": list(frozen.repo_digests_observed),
            "RepoTags": [frozen.image_tag],
            "Architecture": frozen.architecture,
            "Os": frozen.operating_system,
            "Created": frozen.created,
            "Size": frozen.size_bytes,
            "RootFS": {
                "Type": "layers",
                "Layers": list(frozen.rootfs_layers),
            },
            "Config": {
                "Labels": {
                    "org.opencontainers.image.revision": frozen.oci_revision,
                    "io.torch2pc.base-image": frozen.oci_base_image,
                },
                "Env": [
                    f"SOURCE_GIT_COMMIT={frozen.source_git_commit_env}",
                ],
                "Entrypoint": list(CONTAINER_IMAGE_ENTRYPOINT),
                "WorkingDir": "/workspace",
            },
        }
    ]
    return parse_local_image_inspection(
        json.dumps(raw, sort_keys=True),
        contract,
        frozen,
    )


@pytest.fixture(scope="module")
def runtime_root(
    tmp_path_factory: pytest.TempPathFactory,
) -> Path:
    """Build a real symlink-free root for fake-spawn tests."""

    root = tmp_path_factory.mktemp(
        "qwake-lc4-host-runtime-invoker"
    )
    for relative in (
        Path("experiments/frozen"),
        Path("scripts"),
        Path("src"),
        Path("tests"),
    ):
        shutil.copytree(
            ROOT / relative,
            root / relative,
        )

    (root / "external/Torch2PC").mkdir(parents=True)
    (root / "results").mkdir(parents=True)

    for relative in (
        Path("experiments/frozen"),
        Path("external/Torch2PC"),
        Path("results"),
    ):
        candidate = root / relative
        assert candidate.is_dir()
        assert not candidate.is_symlink()

    return root


class _FakeProcess:
    def __init__(
        self,
        *,
        stdout: bytes = b"OK\n",
        stderr: bytes = b"",
        wait_results: tuple[object, ...] = (0,),
        pid: int = 4242,
    ) -> None:
        self.pid = pid
        self.stdout = BytesIO(stdout)
        self.stderr = BytesIO(stderr)
        self.returncode: int | None = None
        self._wait_results = list(wait_results)
        self.wait_calls: list[float | None] = []

    def poll(self) -> int | None:
        return self.returncode

    def wait(self, timeout: float | None = None) -> int:
        self.wait_calls.append(timeout)
        if not self._wait_results:
            raise AssertionError("unexpected extra wait")
        result = self._wait_results.pop(0)
        if isinstance(result, BaseException):
            raise result
        self.returncode = int(result)
        return self.returncode


class _FakeSpawner:
    def __init__(self, process: _FakeProcess) -> None:
        self.process = process
        self.calls: list[tuple[tuple[str, ...], dict[str, object]]] = []

    def __call__(
        self,
        argv: object,
        **kwargs: object,
    ) -> _FakeProcess:
        self.calls.append((tuple(str(item) for item in argv), dict(kwargs)))
        return self.process


def test_implementation_state_is_exact_and_effect_free() -> None:
    contract, record_sha256, registry_sha256 = (
        verify_host_runtime_invoker_implementation_prerequisites(ROOT)
    )
    state = build_host_runtime_invoker_implementation_state(ROOT)
    validate_host_runtime_invoker_implementation_state(state, ROOT)

    assert contract.contract_id == HOST_RUNTIME_INVOKER_CONTRACT_ID
    assert state.implementation_id == HOST_RUNTIME_INVOKER_IMPLEMENTATION_ID
    assert state.status == HOST_RUNTIME_INVOKER_IMPLEMENTATION_STATUS
    assert state.contract_sha256 == contract.contract_sha256
    assert state.authoring_record_sha256 == record_sha256
    assert state.authoring_registry_sha256 == registry_sha256
    assert state.prelaunch_image_inspection_count == 2
    assert state.prelaunch_materialization_count == 2
    assert state.subprocess_popen_call_limit == 1
    assert state.host_runtime_invoker_implementation_present is True
    assert state.host_runtime_invoker_present is True
    assert state.host_runtime_invoker_executable is True
    assert state.host_docker_run_implemented is True
    assert state.branch_runtime_execution_permitted is False
    assert state.execution_lease_materialized is False
    assert state.runtime_execution_performed is False


def test_changed_implementation_state_fails_closed() -> None:
    state = build_host_runtime_invoker_implementation_state(ROOT)
    with pytest.raises(
        QWakeLC4HostRuntimeInvokerImplementationError,
        match="branch_runtime_execution_permitted",
    ):
        replace(state, branch_runtime_execution_permitted=True).require()
    with pytest.raises(
        QWakeLC4HostRuntimeInvokerImplementationError,
        match="implementation digest differs",
    ):
        replace(state, state_sha256="sha256:" + "0" * 64).require()


def test_success_path_reinspects_and_spawns_exactly_once(runtime_root: Path) -> None:
    inspection = _inspection()
    inspect_calls: list[tuple[Path, float]] = []

    def inspect(root: Path, *, timeout_seconds: float) -> LocalImageInspection:
        inspect_calls.append((root, timeout_seconds))
        return inspection

    process = _FakeProcess(stdout=b"completed\n", stderr=b"warning\n")
    spawner = _FakeSpawner(process)
    signals: list[tuple[int, int]] = []

    outcome = invoke_one_shot_host_runtime(
        runtime_root,
        host_resources=_resources(),
        claimed_at_utc=FIXTURE_CLAIMED_AT_UTC,
        operator_acknowledgement=INVOCATION_OPERATOR_ACKNOWLEDGEMENT,
        process_spawner=spawner,
        image_inspector=inspect,
        signal_sender=lambda pid, signum: signals.append((pid, signum)),
    )

    assert len(inspect_calls) == 2
    assert {
        observed_root
        for observed_root, _ in inspect_calls
    } == {runtime_root}
    assert len(spawner.calls) == 1
    argv, kwargs = spawner.calls[0]
    assert argv[:2] == ("docker", "run")
    assert kwargs["cwd"] == runtime_root
    assert kwargs["env"] == dict(HOST_PROCESS_ENVIRONMENT)
    assert kwargs["shell"] is False
    assert kwargs["start_new_session"] is True
    assert kwargs["close_fds"] is True
    assert outcome.classification == "success"
    assert outcome.return_code == 0
    assert outcome.child_spawn_count == 1
    assert outcome.stdout.text == "completed\n"
    assert outcome.stderr.text == "warning\n"
    assert outcome.command_persisted is False
    assert outcome.host_log_persisted is False
    assert signals == []


def test_spawn_error_is_single_and_terminal(runtime_root: Path) -> None:
    inspection = _inspection()
    attempts = 0

    def inspect(_root: Path, *, timeout_seconds: float) -> LocalImageInspection:
        assert timeout_seconds > 0
        return inspection

    def fail_spawn(_argv: object, **_kwargs: object) -> _FakeProcess:
        nonlocal attempts
        attempts += 1
        raise OSError("synthetic spawn failure")

    with pytest.raises(
        QWakeLC4HostRuntimeInvokerImplementationError,
        match="spawn failed",
    ):
        invoke_one_shot_host_runtime(
            runtime_root,
            host_resources=_resources(),
            claimed_at_utc=FIXTURE_CLAIMED_AT_UTC,
            operator_acknowledgement=INVOCATION_OPERATOR_ACKNOWLEDGEMENT,
            process_spawner=fail_spawn,
            image_inspector=inspect,
            signal_sender=lambda _pid, _signum: None,
        )
    assert attempts == 1



def test_invalid_child_identifier_never_targets_host_process_group(runtime_root: Path) -> None:
    inspection = _inspection()

    def inspect(_root: Path, *, timeout_seconds: float) -> LocalImageInspection:
        assert timeout_seconds > 0
        return inspection

    signals: list[tuple[int, int]] = []
    process = _FakeProcess(pid=0)
    with pytest.raises(
        QWakeLC4HostRuntimeInvokerImplementationError,
        match="identifier differs",
    ):
        invoke_one_shot_host_runtime(
            runtime_root,
            host_resources=_resources(),
            claimed_at_utc=FIXTURE_CLAIMED_AT_UTC,
            operator_acknowledgement=INVOCATION_OPERATOR_ACKNOWLEDGEMENT,
            process_spawner=_FakeSpawner(process),
            image_inspector=inspect,
            signal_sender=lambda pid, signum: signals.append((pid, signum)),
        )
    assert signals == []


def test_timeout_sends_term_without_retry(runtime_root: Path) -> None:
    inspection = _inspection()

    def inspect(_root: Path, *, timeout_seconds: float) -> LocalImageInspection:
        assert timeout_seconds > 0
        return inspection

    process = _FakeProcess(
        wait_results=(
            subprocess.TimeoutExpired(cmd=("docker", "run"), timeout=7200),
            143,
        )
    )
    spawner = _FakeSpawner(process)
    signals: list[tuple[int, int]] = []

    outcome = invoke_one_shot_host_runtime(
        runtime_root,
        host_resources=_resources(),
        claimed_at_utc=FIXTURE_CLAIMED_AT_UTC,
        operator_acknowledgement=INVOCATION_OPERATOR_ACKNOWLEDGEMENT,
        process_spawner=spawner,
        image_inspector=inspect,
        signal_sender=lambda pid, signum: signals.append((pid, signum)),
    )

    assert outcome.classification == "timeout"
    assert outcome.timed_out is True
    assert outcome.return_code == 143
    assert len(spawner.calls) == 1
    assert signals == [(4242, signal.SIGTERM)]
    assert process.wait_calls == [7200.0, 30.0]


def test_output_capture_is_bounded(
    runtime_root: Path,
) -> None:
    inspection = _inspection()
    contract = build_host_runtime_invoker_contract(runtime_root)
    payload = b"x" * (contract.stdout_capture_limit_bytes + 100)

    def inspect(_root: Path, *, timeout_seconds: float) -> LocalImageInspection:
        assert timeout_seconds > 0
        return inspection

    process = _FakeProcess(stdout=payload)
    outcome = invoke_one_shot_host_runtime(
        runtime_root,
        host_resources=_resources(),
        claimed_at_utc=FIXTURE_CLAIMED_AT_UTC,
        operator_acknowledgement=INVOCATION_OPERATOR_ACKNOWLEDGEMENT,
        process_spawner=_FakeSpawner(process),
        image_inspector=inspect,
        signal_sender=lambda _pid, _signum: None,
    )

    assert outcome.stdout.captured_bytes == contract.stdout_capture_limit_bytes
    assert outcome.stdout.total_bytes == len(payload)
    assert outcome.stdout.truncated is True


def test_implementation_source_has_one_popen_and_no_runtime_call_on_import() -> None:
    source = MODULE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    popen_calls = 0
    run_calls = 0
    main_guards = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if (
                isinstance(node.func.value, ast.Name)
                and node.func.value.id == "subprocess"
                and node.func.attr == "Popen"
            ):
                popen_calls += 1
            if (
                isinstance(node.func.value, ast.Name)
                and node.func.value.id == "subprocess"
                and node.func.attr == "run"
            ):
                run_calls += 1
        if isinstance(node, ast.If) and "__main__" in ast.unparse(node.test):
            main_guards += 1
    assert popen_calls == 1
    assert run_calls == 0
    assert main_guards == 0
    assert "shell=True" not in source
    assert "write_text(" not in source
    assert "write_bytes(" not in source


def test_frozen_implementation_record_binds_exact_sources() -> None:
    record = IMPLEMENTATION_ROOT / "implementation.json"
    registry = IMPLEMENTATION_ROOT / "SHA256SUMS"
    assert record.is_file()
    assert registry.is_file()
    line = registry.read_text(encoding="utf-8").strip()
    digest, relative = line.split("  ", 1)
    assert relative == "implementation.json"
    assert "sha256:" + digest == _sha256(record)
    payload = json.loads(record.read_text(encoding="utf-8"))
    assert payload["contracts"]["module_sha256"] == _sha256(MODULE)
    assert payload["contracts"]["verifier_sha256"] == _sha256(VERIFIER)
    assert payload["contracts"]["test_sha256"] == _sha256(Path(__file__))
    assert payload["gates"]["host_runtime_invoker_present"] is True
    assert payload["gates"]["host_docker_run_implemented"] is True
    assert payload["gates"]["branch_runtime_execution_permitted"] is False
    assert payload["gates"]["execution_lease_materialized"] is False
