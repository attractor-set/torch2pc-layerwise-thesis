from __future__ import annotations

import io
from collections.abc import Mapping, Sequence
from pathlib import Path

import torch2pc_thesis.stage3b_qwake_attempt_003_host_invocation_process_spawner as spawner


class FakeProcess:
    def __init__(self, return_code: int = 0) -> None:
        self.pid = 4242
        self.stdout = io.BytesIO(b"stdout\n")
        self.stderr = io.BytesIO(b"stderr\n")
        self._return_code: int | None = None
        self._terminal_return_code = return_code

    def wait(self, timeout: float | None = None) -> int:
        self._return_code = self._terminal_return_code
        return self._terminal_return_code

    def poll(self) -> int | None:
        return self._return_code


class RecordingSpawner:
    def __init__(self, process: FakeProcess) -> None:
        self.process = process
        self.calls: list[dict[str, object]] = []

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
    ) -> FakeProcess:
        self.calls.append(
            {
                "argv": tuple(argv),
                "cwd": cwd,
                "env": dict(env),
                "stdin": stdin,
                "stdout": stdout,
                "stderr": stderr,
                "shell": shell,
                "start_new_session": start_new_session,
                "close_fds": close_fds,
            }
        )
        return self.process


def sample_command() -> spawner.PersistedHostCommand:
    return spawner.PersistedHostCommand(
        record_sha256=spawner.COMMAND_RECORD_SHA256,
        file_sha256=spawner.COMMAND_RECORD_FILE_SHA256,
        claimed_at_utc=spawner.AUTHORITATIVE_CLAIMED_AT_UTC,
        invocation_sha256=spawner.INVOCATION_SHA256,
        command_template_sha256=spawner.COMMAND_TEMPLATE_SHA256,
        argv=(
            "docker",
            "run",
            "--claimed-at-utc",
            spawner.AUTHORITATIVE_CLAIMED_AT_UTC,
        ),
        environment=(("HOME", "/tmp/home"),),
        mount_sources=("/a", "/b", "/c"),
    )


def test_contract_is_canonical_and_execution_is_still_closed() -> None:
    contract = spawner.build_attempt_003_process_spawner_contract()
    spawner.validate_attempt_003_process_spawner_contract(contract)

    payload = dict(contract)
    observed = payload.pop("contract_sha256")
    assert observed == spawner.sha256_object(payload)

    assert contract["host_process_spawner_present"] is True
    assert contract["host_process_spawner_executable"] is True
    assert contract["docker_run_implemented"] is True
    assert contract["host_process_spawned"] is False
    assert contract["docker_run_invoked"] is False
    assert contract["authorization_consumed"] is False
    assert contract["attempt_started"] is False
    assert contract["execution_lease_materialized"] is False
    assert contract["runtime_execution_permitted"] is False


def test_contract_binds_exact_durable_command() -> None:
    contract = spawner.build_attempt_003_process_spawner_contract()

    assert contract["authoritative_claimed_at_utc"] == "2026-08-10T14:47:42Z"
    assert contract["invocation_sha256"] == (
        "sha256:91e762ba21c1d72b9282a3b0419206d5de1c3f88aac82a63dad76e27f0321c24"
    )
    assert contract["command_record_sha256"] == (
        "sha256:3ea2d34826fdd5846eee7cdfa84833f6b5e2293cfef76b76a51b64862cb143ca"
    )
    assert contract["command_record_file_sha256"] == (
        "f519d0821305171aa5c6ed05cad772f9fd85e93601fa1ec551e23058939d1ba6"
    )


def test_default_process_control_is_fixed() -> None:
    contract = spawner.build_attempt_003_process_spawner_contract()

    assert contract["spawn_count_limit"] == 1
    assert contract["start_new_session_required"] is True
    assert contract["close_fds_required"] is True
    assert contract["shell_interpretation_forbidden"] is True
    assert contract["environment_inheritance_forbidden"] is True
    assert contract["runtime_timeout_seconds"] == 7200
    assert contract["termination_grace_seconds"] == 30
    assert contract["automatic_retry_after_spawn_forbidden"] is True
    assert contract["host_execution_lease_write_forbidden"] is True


def test_bounded_child_uses_exact_one_spawn_without_shell(tmp_path: Path) -> None:
    contract = spawner.build_attempt_003_process_spawner_contract()
    command = sample_command()
    command_path = tmp_path / spawner.COMMAND_RECORD_RELATIVE
    command_path.parent.mkdir(parents=True)
    command_path.write_bytes(b"fixture")
    process = FakeProcess(return_code=0)
    recorder = RecordingSpawner(process)
    sent_signals: list[tuple[int, int]] = []

    outcome = spawner._run_bounded_child(
        tmp_path,
        contract,
        command,
        process_spawner=recorder,
        signal_sender=lambda pgid, signum: sent_signals.append((pgid, signum)),
    )

    assert len(recorder.calls) == 1
    call = recorder.calls[0]
    assert call["argv"] == command.argv
    assert call["cwd"] == tmp_path
    assert call["env"] == dict(spawner.HOST_PROCESS_ENVIRONMENT)
    assert call["shell"] is False
    assert call["start_new_session"] is True
    assert call["close_fds"] is True
    assert sent_signals == []

    assert outcome.classification == "success"
    assert outcome.return_code == 0
    assert outcome.child_spawn_count == 1
    assert outcome.shell_interpretation_used is False
    assert outcome.environment_inherited is False
    assert outcome.host_execution_lease_written is False
    assert outcome.automatic_retry_performed is False
    assert outcome.stdout.text == "stdout\n"
    assert outcome.stderr.text == "stderr\n"


def test_persisted_command_requires_exact_claim() -> None:
    command = sample_command()
    command.require()

    mutated = spawner.PersistedHostCommand(
        **{
            **command.__dict__,
            "claimed_at_utc": "2026-08-10T14:47:43Z",
        }
    )
    try:
        mutated.require()
    except spawner.ProcessSpawnerError as exc:
        assert "claimed_at_utc" in str(exc)
    else:
        raise AssertionError("mutated claim was accepted")


def test_authorization_and_lease_remain_container_owned() -> None:
    contract = spawner.build_attempt_003_process_spawner_contract()

    assert contract["authorization_consumption_owner"] == (
        "container_entrypoint_atomic_execution_lease"
    )
    assert contract["lease_claim_owner"] == (
        "container_entrypoint_atomic_execution_lease"
    )
    assert contract["host_execution_lease_write_forbidden"] is True
