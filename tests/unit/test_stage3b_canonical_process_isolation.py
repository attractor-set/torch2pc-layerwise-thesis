from __future__ import annotations

import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import cast

import pytest

import torch2pc_thesis.stage3b_canonical as canonical
from torch2pc_thesis.stage3b_authorization import B0_CANDIDATE_ID
from torch2pc_thesis.stage3b_canonical import (
    B0_CANONICAL_PROCESS_MODE,
    B0_CANONICAL_PROTOCOL,
    CanonicalCellProcessError,
    CanonicalLanePlan,
    CanonicalPlannedCell,
    CanonicalSubprocessCellRunner,
    execute_authorized_lane,
)

SOURCE_COMMIT = "a" * 40
IMAGE_DIGEST = "sha256:" + "b" * 64
TOKEN = "token"
MANIFEST_DIGEST = "manifest"


def _json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def _child_attempt(
    command: list[str],
    *,
    attempt_id: str,
    status: str,
    exception_type: str | None = None,
    exception_message: str | None = None,
) -> None:
    def argument(name: str) -> str:
        return command[command.index(name) + 1]

    output_root = Path(argument("--output-root")).resolve()
    cell_id = argument("--cell-id")
    device = argument("--device")
    dtype = argument("--dtype")
    attempt = (
        output_root
        / "canonical"
        / "lanes"
        / f"{device}-{dtype}"
        / "cells"
        / cell_id
        / "attempts"
        / attempt_id
    )
    request: dict[str, object] = {
        "schema_version": 1,
        "campaign_id": "stage3b",
        "authorization_scope": "stage3b_b0_campaign_authorization",
        "execution_scope": "authorized_b0_canonical_cell",
        "attempt_id": attempt_id,
        "cell_id": cell_id,
        "block_id": "b0",
        "candidate_id": B0_CANDIDATE_ID,
        "method": "fixedpred",
        "authorization_token": TOKEN,
        "manifest_digest": MANIFEST_DIGEST,
        "source_commit": argument("--source-commit"),
        "device": device,
        "dtype": dtype,
        "image_digest": argument("--image-digest"),
        "canonical_protocol": dict(B0_CANONICAL_PROTOCOL),
        "evidence": False,
        "full_cell_complete": False,
        "full_lane_complete": False,
        "full_campaign_complete": False,
        "results_publication_permitted": False,
        "test_dataset_access": False,
    }
    _json(attempt / "request.json", request)
    _json(
        attempt / "started.json",
        {**request, "status": "canonical_cell_running"},
    )
    terminal = {
        **request,
        "status": status,
        "attempt_directory": str(attempt),
    }
    if status == "canonical_cell_complete":
        terminal["full_cell_complete"] = True
        _json(attempt / "completed.json", terminal)
    else:
        terminal["exception_type"] = exception_type
        terminal["exception_message"] = exception_message
        _json(attempt / "failed.json", terminal)


class _FakeProcess:
    def __init__(
        self,
        command: list[str],
        *,
        pid: int,
        returncode: int,
        status: str,
        attempt_id: str,
        stderr: str = "",
    ) -> None:
        self.command = command
        self.pid = pid
        self.returncode: int | None = None
        self._final_returncode = returncode
        self._status = status
        self._attempt_id = attempt_id
        self._stderr = stderr

    def communicate(self, timeout: int | None = None) -> tuple[str, str]:
        del timeout
        if self.returncode is None:
            _child_attempt(
                self.command,
                attempt_id=self._attempt_id,
                status=self._status,
                exception_type=(
                    "OutOfMemoryError"
                    if self._status == "canonical_cell_failed"
                    else None
                ),
                exception_message=(
                    "HIP out of memory"
                    if self._status == "canonical_cell_failed"
                    else None
                ),
            )
            self.returncode = self._final_returncode
        return "", self._stderr

    def terminate(self) -> None:
        self.returncode = -15

    def kill(self) -> None:
        self.returncode = -9


def test_subprocess_runner_uses_fresh_child_and_records_process_telemetry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_directory = tmp_path / "run"
    authorization_snapshot = run_directory / "child-inputs" / "authorization.json"
    manifest_snapshot = run_directory / "child-inputs" / "manifest.json"
    _json(authorization_snapshot, {"authorization_token": TOKEN})
    _json(manifest_snapshot, {"manifest_digest": MANIFEST_DIGEST})
    launched: list[list[str]] = []
    pids = iter((4101, 4102))

    def fake_popen(command: list[str], **_kwargs: object) -> _FakeProcess:
        launched.append(command)
        pid = next(pids)
        cell_id = command[command.index("--cell-id") + 1]
        return _FakeProcess(
            command,
            pid=pid,
            returncode=0,
            status="canonical_cell_complete",
            attempt_id=f"attempt-{cell_id}",
        )

    monkeypatch.setattr(canonical.subprocess, "Popen", fake_popen)
    runner = CanonicalSubprocessCellRunner(
        run_directory=run_directory,
        authorization_snapshot=authorization_snapshot,
        manifest_snapshot=manifest_snapshot,
    )
    manifest = {"manifest_digest": MANIFEST_DIGEST}
    authorization = {"authorization_token": TOKEN}

    first = runner(
        manifest,
        authorization,
        output_root=tmp_path / "output",
        cell_id="cell-1",
        device="rocm",
        dtype="float32",
        torch2pc_dir=tmp_path / "Torch2PC",
        source_commit=SOURCE_COMMIT,
        image_digest=IMAGE_DIGEST,
    )
    second = runner(
        manifest,
        authorization,
        output_root=tmp_path / "output",
        cell_id="cell-2",
        device="rocm",
        dtype="float32",
        torch2pc_dir=tmp_path / "Torch2PC",
        source_commit=SOURCE_COMMIT,
        image_digest=IMAGE_DIGEST,
    )

    assert [record["process_isolation"]["child_pid"] for record in (first, second)] == [
        4101,
        4102,
    ]
    expected_prefix = [sys.executable, "-m", runner.child_module]
    assert all(command[:3] == expected_prefix for command in launched)
    process_records = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((run_directory / "processes").glob("*.json"))
    ]
    assert len(process_records) == 2
    assert {record["child_pid"] for record in process_records} == {4101, 4102}
    assert {record["child_exit_code"] for record in process_records} == {0}
    assert {record["process_isolation_mode"] for record in process_records} == {
        B0_CANONICAL_PROCESS_MODE
    }
    assert all(record["terminal_record_sha256"] for record in process_records)


def _planned_cell(
    cell_id: str,
    state: canonical.CanonicalCellState,
) -> CanonicalPlannedCell:
    return CanonicalPlannedCell(
        cell_id=cell_id,
        block_id="b0",
        block_order=0,
        method="fixedpred",
        depth=1,
        width=1,
        batch_size=1,
        model_seed=1,
        state=state,
        attempt_count=int(state != "pending"),
        failed_attempt_count=int(state == "failed"),
        running_attempt_count=0,
        selected_for_execution=state == "pending",
    )


def _plan(
    tmp_path: Path,
    states: tuple[canonical.CanonicalCellState, ...],
) -> CanonicalLanePlan:
    cells = tuple(
        _planned_cell(f"cell-{index}", state)
        for index, state in enumerate(states, start=1)
    )
    return CanonicalLanePlan(
        authorization_token=TOKEN,
        manifest_digest=MANIFEST_DIGEST,
        output_root=str((tmp_path / "output").resolve()),
        source_commit=SOURCE_COMMIT,
        device="rocm",
        dtype="float32",
        image_digest=IMAGE_DIGEST,
        max_attempts=2,
        resume=False,
        retry_failed=False,
        summary=dict(canonical.Counter(cell.state for cell in cells)),
        selected_cell_ids=tuple(
            cell.cell_id for cell in cells if cell.selected_for_execution
        ),
        cells=cells,
    )


def test_lane_stops_after_first_systemic_oom_without_launching_later_cells(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plans = iter(
        (
            _plan(tmp_path, ("pending", "pending", "pending")),
            _plan(tmp_path, ("failed", "pending", "pending")),
        )
    )
    monkeypatch.setattr(
        canonical,
        "plan_authorized_lane",
        lambda *_args, **_kwargs: next(plans),
    )
    launched: list[str] = []

    def oom_runner(
        _manifest: Mapping[str, object],
        _authorization: Mapping[str, object],
        *,
        cell_id: str,
        **_kwargs: object,
    ) -> dict[str, object]:
        launched.append(cell_id)
        marker = tmp_path / "attempt-markers" / cell_id
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.touch()
        return {
            "status": "canonical_cell_failed",
            "cell_id": cell_id,
            "attempt_id": "attempt-1",
            "attempt_directory": str(marker),
            "exception_type": "OutOfMemoryError",
            "exception_message": "HIP out of memory",
            "systemic_resource_failure": True,
            "process_isolation": {
                "mode": B0_CANONICAL_PROCESS_MODE,
                "child_pid": 4201,
                "child_exit_code": 1,
            },
        }

    result = execute_authorized_lane(
        {"emergency_stop_path": str(tmp_path / "EMERGENCY-STOP")},
        {"manifest_digest": MANIFEST_DIGEST},
        output_root=tmp_path / "output",
        device="rocm",
        dtype="float32",
        torch2pc_dir=tmp_path / "Torch2PC",
        source_commit=SOURCE_COMMIT,
        image_digest=IMAGE_DIGEST,
        cell_runner=cast(canonical.CanonicalCellRunner, oom_runner),
    )

    assert launched == ["cell-1"]
    assert {path.name for path in (tmp_path / "attempt-markers").iterdir()} == {
        "cell-1"
    }
    assert result["status"] == "lane_incomplete"
    assert result["executed_cell_count"] == 1
    assert result["failed_this_run_count"] == 1
    assert result["stopped_early"] is True
    assert result["systemic_stop"]["reason"] == "systemic_gpu_out_of_memory"


def test_parent_rejects_tampered_terminal_record(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_directory = tmp_path / "run"
    authorization_snapshot = run_directory / "authorization.json"
    manifest_snapshot = run_directory / "manifest.json"
    _json(authorization_snapshot, {"authorization_token": TOKEN})
    _json(manifest_snapshot, {"manifest_digest": MANIFEST_DIGEST})

    def fake_popen(command: list[str], **_kwargs: object) -> _FakeProcess:
        process = _FakeProcess(
            command,
            pid=4301,
            returncode=0,
            status="canonical_cell_complete",
            attempt_id="attempt-tampered",
        )
        original_communicate = process.communicate

        def communicate(timeout: int | None = None) -> tuple[str, str]:
            output = original_communicate(timeout)
            cell_id = command[command.index("--cell-id") + 1]
            terminal = next(
                (
                    tmp_path
                    / "output"
                    / "canonical"
                    / "lanes"
                    / "rocm-float32"
                    / "cells"
                    / cell_id
                    / "attempts"
                ).glob("*/completed.json")
            )
            payload = json.loads(terminal.read_text(encoding="utf-8"))
            payload["source_commit"] = "0" * 40
            _json(terminal, payload)
            return output

        process.communicate = communicate  # type: ignore[method-assign]
        return process

    monkeypatch.setattr(canonical.subprocess, "Popen", fake_popen)
    runner = CanonicalSubprocessCellRunner(
        run_directory=run_directory,
        authorization_snapshot=authorization_snapshot,
        manifest_snapshot=manifest_snapshot,
    )
    with pytest.raises(
        CanonicalCellProcessError,
        match="terminal record does not match",
    ):
        runner(
            {"manifest_digest": MANIFEST_DIGEST},
            {"authorization_token": TOKEN},
            output_root=tmp_path / "output",
            cell_id="cell-tampered",
            device="rocm",
            dtype="float32",
            torch2pc_dir=tmp_path / "Torch2PC",
            source_commit=SOURCE_COMMIT,
            image_digest=IMAGE_DIGEST,
        )
    process_record = next((run_directory / "processes").glob("*.json"))
    telemetry = json.loads(process_record.read_text(encoding="utf-8"))
    assert telemetry["child_pid"] == 4301
    assert telemetry["child_exit_code"] == 0
    assert telemetry["terminal_validation_error"]


def test_interrupted_child_attempt_remains_resume_retryable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_directory = tmp_path / "run"
    authorization_snapshot = run_directory / "authorization.json"
    manifest_snapshot = run_directory / "manifest.json"
    _json(authorization_snapshot, {"authorization_token": TOKEN})
    _json(manifest_snapshot, {"manifest_digest": MANIFEST_DIGEST})

    class InterruptedProcess:
        pid = 4401
        returncode: int | None = None

        def __init__(self, command: list[str]) -> None:
            self.command = command

        def communicate(self, timeout: int | None = None) -> tuple[str, str]:
            del timeout
            output_root = Path(
                self.command[self.command.index("--output-root") + 1]
            ).resolve()
            cell_id = self.command[self.command.index("--cell-id") + 1]
            attempt = (
                output_root
                / "canonical"
                / "lanes"
                / "rocm-float32"
                / "cells"
                / cell_id
                / "attempts"
                / "attempt-interrupted"
            )
            request = {
                "execution_scope": "authorized_b0_canonical_cell",
                "cell_id": cell_id,
                "candidate_id": B0_CANDIDATE_ID,
                "authorization_token": TOKEN,
                "manifest_digest": MANIFEST_DIGEST,
                "source_commit": SOURCE_COMMIT,
                "device": "rocm",
                "dtype": "float32",
                "image_digest": IMAGE_DIGEST,
                "canonical_protocol": dict(B0_CANONICAL_PROTOCOL),
                "attempt_id": "attempt-interrupted",
            }
            _json(attempt / "request.json", request)
            _json(
                attempt / "started.json",
                {**request, "status": "canonical_cell_running"},
            )
            self.returncode = 130
            return "", "KeyboardInterrupt"

        def terminate(self) -> None:
            self.returncode = -15

        def kill(self) -> None:
            self.returncode = -9

    monkeypatch.setattr(
        canonical.subprocess,
        "Popen",
        lambda command, **_kwargs: InterruptedProcess(command),
    )
    runner = CanonicalSubprocessCellRunner(
        run_directory=run_directory,
        authorization_snapshot=authorization_snapshot,
        manifest_snapshot=manifest_snapshot,
    )
    with pytest.raises(CanonicalCellProcessError, match="terminal record"):
        runner(
            {"manifest_digest": MANIFEST_DIGEST},
            {"authorization_token": TOKEN},
            output_root=tmp_path / "output",
            cell_id="cell-interrupted",
            device="rocm",
            dtype="float32",
            torch2pc_dir=tmp_path / "Torch2PC",
            source_commit=SOURCE_COMMIT,
            image_digest=IMAGE_DIGEST,
        )

    summary = canonical._inspect_attempts(
        lane_root=(tmp_path / "output" / "canonical" / "lanes" / "rocm-float32"),
        cell_id="cell-interrupted",
        authorization_token=TOKEN,
        manifest_digest=MANIFEST_DIGEST,
        source_commit=SOURCE_COMMIT,
        device="rocm",
        dtype="float32",
        image_digest=IMAGE_DIGEST,
    )
    assert summary.running_count == 1
    assert canonical._state_from_attempts(
        summary,
        resume=True,
        retry_failed=False,
        max_attempts=2,
    ) == "retryable"



def test_parent_interruption_records_child_exit_before_propagating(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_directory = tmp_path / "run"
    authorization_snapshot = run_directory / "authorization.json"
    manifest_snapshot = run_directory / "manifest.json"
    _json(authorization_snapshot, {"authorization_token": TOKEN})
    _json(manifest_snapshot, {"manifest_digest": MANIFEST_DIGEST})

    class ParentInterruptedProcess:
        pid = 4501
        returncode: int | None = None

        def __init__(self, command: list[str]) -> None:
            self.command = command
            self.communicate_count = 0

        def communicate(self, timeout: int | None = None) -> tuple[str, str]:
            del timeout
            self.communicate_count += 1
            if self.communicate_count == 1:
                output_root = Path(
                    self.command[self.command.index("--output-root") + 1]
                ).resolve()
                cell_id = self.command[self.command.index("--cell-id") + 1]
                attempt = (
                    output_root
                    / "canonical"
                    / "lanes"
                    / "rocm-float32"
                    / "cells"
                    / cell_id
                    / "attempts"
                    / "attempt-parent-interrupted"
                )
                request = {
                    "execution_scope": "authorized_b0_canonical_cell",
                    "cell_id": cell_id,
                    "candidate_id": B0_CANDIDATE_ID,
                    "authorization_token": TOKEN,
                    "manifest_digest": MANIFEST_DIGEST,
                    "source_commit": SOURCE_COMMIT,
                    "device": "rocm",
                    "dtype": "float32",
                    "image_digest": IMAGE_DIGEST,
                    "canonical_protocol": dict(B0_CANONICAL_PROTOCOL),
                    "attempt_id": "attempt-parent-interrupted",
                }
                _json(attempt / "request.json", request)
                _json(
                    attempt / "started.json",
                    {**request, "status": "canonical_cell_running"},
                )
                raise KeyboardInterrupt
            return "", "terminated by parent"

        def terminate(self) -> None:
            self.returncode = -15

        def kill(self) -> None:
            self.returncode = -9

    monkeypatch.setattr(
        canonical.subprocess,
        "Popen",
        lambda command, **_kwargs: ParentInterruptedProcess(command),
    )
    runner = CanonicalSubprocessCellRunner(
        run_directory=run_directory,
        authorization_snapshot=authorization_snapshot,
        manifest_snapshot=manifest_snapshot,
    )
    with pytest.raises(KeyboardInterrupt):
        runner(
            {"manifest_digest": MANIFEST_DIGEST},
            {"authorization_token": TOKEN},
            output_root=tmp_path / "output",
            cell_id="cell-parent-interrupted",
            device="rocm",
            dtype="float32",
            torch2pc_dir=tmp_path / "Torch2PC",
            source_commit=SOURCE_COMMIT,
            image_digest=IMAGE_DIGEST,
        )

    process_record = next((run_directory / "processes").glob("*.json"))
    telemetry = json.loads(process_record.read_text(encoding="utf-8"))
    assert telemetry["child_pid"] == 4501
    assert telemetry["child_exit_code"] == -15
    assert telemetry["terminal_validation_error"]


def test_internal_child_rejects_cpu_canonical_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import torch2pc_thesis.stage3b_canonical_child as child

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "stage3b_canonical_child",
            "--authorization",
            "authorization.json",
            "--manifest",
            "manifest.json",
            "--output-root",
            "/tmp/stage3b",
            "--cell-id",
            "cell-1",
            "--device",
            "cpu",
            "--dtype",
            "float64",
            "--torch2pc-dir",
            "external/Torch2PC",
            "--source-commit",
            SOURCE_COMMIT,
            "--image-digest",
            IMAGE_DIGEST,
        ],
    )
    with pytest.raises(SystemExit):
        child.parse_args()
