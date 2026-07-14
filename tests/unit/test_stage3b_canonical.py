from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import cast

import pytest

from torch2pc_thesis.stage3b_authorization import (
    B0_OPERATOR_ACKNOWLEDGEMENT,
    RuntimeProbe,
    capture_lane_preflight,
    freeze_project_environment,
    issue_campaign_authorization,
)
from torch2pc_thesis.stage3b_canonical import (
    B0_CANONICAL_CELL_SCOPE,
    B0_CANONICAL_PROTOCOL,
    CanonicalCellContext,
    CanonicalCellResult,
    CanonicalLanePlan,
    execute_authorized_lane,
    execute_canonical_cell,
    plan_authorized_lane,
    verify_authorized_lane,
)
from torch2pc_thesis.stage3b_execution import (
    Stage3BExecutionError,
    generate_manifest,
)

CPU_IMAGE = "sha256:" + "1" * 64
ROCM_IMAGE = "sha256:" + "2" * 64


def _run(*args: str, cwd: Path) -> str:
    completed = subprocess.run(
        list(args),
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _project_repo(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "project"
    root.mkdir()
    _run("git", "init", cwd=root)
    _run("git", "config", "user.email", "test@example.com", cwd=root)
    _run("git", "config", "user.name", "Stage3B Test", cwd=root)
    (root / "README.md").write_text("stage3b\n", encoding="utf-8")
    _run("git", "add", "README.md", cwd=root)
    _run("git", "commit", "-m", "test baseline", cwd=root)
    return root, _run("git", "rev-parse", "HEAD", cwd=root)


def _torch2pc(tmp_path: Path) -> Path:
    root = tmp_path / "Torch2PC"
    root.mkdir()
    (root / "TorchSeq2PC.py").write_text(
        "# frozen Torch2PC test source\n",
        encoding="utf-8",
    )
    return root


def _cpu_probe() -> RuntimeProbe:
    return RuntimeProbe(
        python_version="3.12.13",
        pytorch_version="2.7.1+cpu",
        hip_version=None,
        cuda_available=False,
        device_count=0,
        device_name="cpu",
        platform="Linux-test",
        machine="x86_64",
        effective_uid=os.geteuid(),
        effective_gid=os.getegid(),
    )


def _rocm_probe() -> RuntimeProbe:
    return RuntimeProbe(
        python_version="3.12.13",
        pytorch_version="2.7.1+rocm6.3",
        hip_version="6.3.42131",
        cuda_available=True,
        device_count=1,
        device_name="AMD Radeon RX 7700 XT",
        platform="Linux-test",
        machine="x86_64",
        effective_uid=os.geteuid(),
        effective_gid=os.getegid(),
    )


def _authorization(
    tmp_path: Path,
) -> tuple[dict[str, object], dict[str, object], str, Path, Path]:
    manifest = generate_manifest()
    project_root, commit = _project_repo(tmp_path)
    torch2pc_dir = _torch2pc(tmp_path)
    output_root = tmp_path / "authorized-output"
    freeze = freeze_project_environment(
        manifest,
        project_root=project_root,
        torch2pc_dir=torch2pc_dir,
        output_root=output_root,
        source_commit=commit,
        minimum_free_bytes=1,
    )
    cpu = capture_lane_preflight(
        freeze,
        manifest,
        torch2pc_dir=torch2pc_dir,
        source_commit=commit,
        device="cpu",
        dtype="float64",
        image_digest=CPU_IMAGE,
        probe=_cpu_probe(),
    )
    rocm = capture_lane_preflight(
        freeze,
        manifest,
        torch2pc_dir=torch2pc_dir,
        source_commit=commit,
        device="rocm",
        dtype="float32",
        image_digest=ROCM_IMAGE,
        probe=_rocm_probe(),
    )
    authorization = issue_campaign_authorization(
        freeze,
        [cpu, rocm],
        operator_acknowledgement=B0_OPERATOR_ACKNOWLEDGEMENT,
    )
    return authorization, manifest, commit, torch2pc_dir, output_root


def _plan(
    authorization: dict[str, object],
    manifest: dict[str, object],
    commit: str,
    torch2pc_dir: Path,
    output_root: Path,
    *,
    resume: bool = False,
    retry_failed: bool = False,
    max_attempts: int = 2,
) -> CanonicalLanePlan:
    return plan_authorized_lane(
        authorization,
        manifest,
        output_root=output_root,
        device="cpu",
        dtype="float64",
        torch2pc_dir=torch2pc_dir,
        source_commit=commit,
        image_digest=CPU_IMAGE,
        max_attempts=max_attempts,
        resume=resume,
        retry_failed=retry_failed,
        probe=_cpu_probe(),
    )


def _fake_result(context: CanonicalCellContext) -> CanonicalCellResult:
    return CanonicalCellResult(
        resolved_config={
            "cell_id": context.cell["cell_id"],
            "canonical_protocol": dict(B0_CANONICAL_PROTOCOL),
        },
        environment={
            "project_source_commit": context.source_commit,
            "authorization_token": context.authorization_token,
        },
        measurements={
            "status": "canonical_cell_complete",
            "execution_scope": B0_CANONICAL_CELL_SCOPE,
            "evidence": False,
            "full_cell_complete": True,
            "test_dataset_access": False,
        },
    )


def test_fresh_plan_selects_all_96_canonical_b0_cells(tmp_path: Path) -> None:
    authorization, manifest, commit, torch2pc_dir, output_root = _authorization(tmp_path)
    plan = _plan(authorization, manifest, commit, torch2pc_dir, output_root)
    record = plan.to_record()

    assert record["authorization_verified"] is True
    assert record["execution_permitted"] is True
    assert record["execution_performed"] is False
    assert record["b0_cell_count"] == 96
    assert record["summary"] == {"pending": 96}
    assert len(cast(list[object], record["selected_cell_ids"])) == 96
    assert record["canonical_protocol"] == B0_CANONICAL_PROTOCOL
    assert record["evidence"] is False
    assert record["full_lane_complete"] is False
    assert record["full_campaign_complete"] is False
    assert record["results_publication_permitted"] is False
    assert record["test_dataset_access"] is False


def test_plan_order_is_deterministic_and_method_paired(tmp_path: Path) -> None:
    authorization, manifest, commit, torch2pc_dir, output_root = _authorization(tmp_path)
    first = _plan(authorization, manifest, commit, torch2pc_dir, output_root)
    second = _plan(authorization, manifest, commit, torch2pc_dir, output_root)

    assert first.selected_cell_ids == second.selected_cell_ids
    assert [cell.method for cell in first.cells[:4]] == [
        "fixedpred",
        "strict",
        "fixedpred",
        "strict",
    ]
    assert all(cell.selected_for_execution for cell in first.cells)


def test_verify_authorized_lane_returns_non_evidence_contract(tmp_path: Path) -> None:
    authorization, manifest, commit, torch2pc_dir, output_root = _authorization(tmp_path)
    result = verify_authorized_lane(
        authorization,
        manifest,
        torch2pc_dir=torch2pc_dir,
        output_root=output_root,
        source_commit=commit,
        device="cpu",
        dtype="float64",
        image_digest=CPU_IMAGE,
        probe=_cpu_probe(),
    )

    assert result["authorization_verified"] is True
    assert result["execution_permitted"] is True
    assert result["evidence"] is False
    assert result["results_publication_permitted"] is False
    assert result["test_dataset_access"] is False


def test_plan_rejects_image_digest_drift(tmp_path: Path) -> None:
    authorization, manifest, commit, torch2pc_dir, output_root = _authorization(tmp_path)
    with pytest.raises(Stage3BExecutionError, match="lane fingerprint differs"):
        plan_authorized_lane(
            authorization,
            manifest,
            output_root=output_root,
            device="cpu",
            dtype="float64",
            torch2pc_dir=torch2pc_dir,
            source_commit=commit,
            image_digest="sha256:" + "3" * 64,
            probe=_cpu_probe(),
        )


def test_plan_rejects_noncanonical_protocol(tmp_path: Path) -> None:
    authorization, manifest, commit, torch2pc_dir, output_root = _authorization(tmp_path)
    authorization["canonical_protocol"] = {
        "warmup_steps": 1,
        "measured_steps": 1,
        "repetitions": 1,
    }
    with pytest.raises(Stage3BExecutionError, match="protocol differs"):
        _plan(authorization, manifest, commit, torch2pc_dir, output_root)


def test_emergency_stop_blocks_plan(tmp_path: Path) -> None:
    authorization, manifest, commit, torch2pc_dir, output_root = _authorization(tmp_path)
    Path(str(authorization["emergency_stop_path"])).touch()
    with pytest.raises(Stage3BExecutionError, match="emergency stop is active"):
        _plan(authorization, manifest, commit, torch2pc_dir, output_root)


def test_fake_executor_completes_entire_cpu_lane(tmp_path: Path) -> None:
    authorization, manifest, commit, torch2pc_dir, output_root = _authorization(tmp_path)
    result = execute_authorized_lane(
        authorization,
        manifest,
        output_root=output_root,
        device="cpu",
        dtype="float64",
        torch2pc_dir=torch2pc_dir,
        source_commit=commit,
        image_digest=CPU_IMAGE,
        probe=_cpu_probe(),
        executor=_fake_result,
    )

    assert result["status"] == "lane_complete"
    assert result["executed_cell_count"] == 96
    assert result["completed_this_run_count"] == 96
    assert result["failed_this_run_count"] == 0
    assert result["completed_cell_count"] == 96
    assert result["remaining_cell_count"] == 0
    assert result["full_lane_complete"] is True
    assert result["full_campaign_complete"] is False
    assert result["evidence"] is False


def test_completed_attempts_are_terminal_on_resume(tmp_path: Path) -> None:
    authorization, manifest, commit, torch2pc_dir, output_root = _authorization(tmp_path)
    execute_authorized_lane(
        authorization,
        manifest,
        output_root=output_root,
        device="cpu",
        dtype="float64",
        torch2pc_dir=torch2pc_dir,
        source_commit=commit,
        image_digest=CPU_IMAGE,
        probe=_cpu_probe(),
        executor=_fake_result,
    )
    plan = _plan(
        authorization,
        manifest,
        commit,
        torch2pc_dir,
        output_root,
        resume=True,
    )

    assert plan.summary == {"completed": 96}
    assert plan.selected_cell_ids == ()
    assert not any(cell.selected_for_execution for cell in plan.cells)


def test_successful_attempt_layout_is_immutable_and_complete(tmp_path: Path) -> None:
    authorization, manifest, commit, torch2pc_dir, output_root = _authorization(tmp_path)
    cell_id = str(cast(list[dict[str, object]], manifest["cells"])[0]["cell_id"])
    b0_cell_id = _plan(
        authorization,
        manifest,
        commit,
        torch2pc_dir,
        output_root,
    ).selected_cell_ids[0]
    assert cell_id

    completed = execute_canonical_cell(
        manifest,
        authorization,
        output_root=output_root,
        cell_id=b0_cell_id,
        device="cpu",
        dtype="float64",
        torch2pc_dir=torch2pc_dir,
        source_commit=commit,
        image_digest=CPU_IMAGE,
        executor=_fake_result,
    )
    attempt = Path(str(completed["attempt_directory"]))

    assert {path.name for path in attempt.iterdir()} == {
        "request.json",
        "started.json",
        "resolved-config.json",
        "environment.json",
        "measurements.json",
        "completed.json",
    }
    assert completed["status"] == "canonical_cell_complete"
    assert completed["full_cell_complete"] is True
    assert completed["evidence"] is False


def test_interrupted_attempt_requires_explicit_resume(tmp_path: Path) -> None:
    authorization, manifest, commit, torch2pc_dir, output_root = _authorization(tmp_path)
    cell_id = _plan(
        authorization,
        manifest,
        commit,
        torch2pc_dir,
        output_root,
    ).selected_cell_ids[0]

    def interrupt(_context: CanonicalCellContext) -> CanonicalCellResult:
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        execute_canonical_cell(
            manifest,
            authorization,
            output_root=output_root,
            cell_id=cell_id,
            device="cpu",
            dtype="float64",
            torch2pc_dir=torch2pc_dir,
            source_commit=commit,
            image_digest=CPU_IMAGE,
            executor=interrupt,
        )

    blocked = _plan(authorization, manifest, commit, torch2pc_dir, output_root)
    resumed = _plan(
        authorization,
        manifest,
        commit,
        torch2pc_dir,
        output_root,
        resume=True,
    )
    blocked_cell = next(cell for cell in blocked.cells if cell.cell_id == cell_id)
    resumed_cell = next(cell for cell in resumed.cells if cell.cell_id == cell_id)

    assert blocked_cell.state == "running"
    assert blocked_cell.selected_for_execution is False
    assert resumed_cell.state == "retryable"
    assert resumed_cell.selected_for_execution is True


def test_failed_attempt_requires_retry_failed(tmp_path: Path) -> None:
    authorization, manifest, commit, torch2pc_dir, output_root = _authorization(tmp_path)
    cell_id = _plan(
        authorization,
        manifest,
        commit,
        torch2pc_dir,
        output_root,
    ).selected_cell_ids[0]

    def fail(_context: CanonicalCellContext) -> CanonicalCellResult:
        raise RuntimeError("injected failure")

    with pytest.raises(RuntimeError, match="injected failure"):
        execute_canonical_cell(
            manifest,
            authorization,
            output_root=output_root,
            cell_id=cell_id,
            device="cpu",
            dtype="float64",
            torch2pc_dir=torch2pc_dir,
            source_commit=commit,
            image_digest=CPU_IMAGE,
            executor=fail,
        )

    blocked = _plan(authorization, manifest, commit, torch2pc_dir, output_root)
    retried = _plan(
        authorization,
        manifest,
        commit,
        torch2pc_dir,
        output_root,
        retry_failed=True,
    )
    blocked_cell = next(cell for cell in blocked.cells if cell.cell_id == cell_id)
    retry_cell = next(cell for cell in retried.cells if cell.cell_id == cell_id)

    assert blocked_cell.state == "failed"
    assert retry_cell.state == "retryable"
    assert retry_cell.selected_for_execution is True
    assert (output_root / "canonical" / "failure-ledger.jsonl").is_file()


def test_retry_creates_new_attempt_id(tmp_path: Path) -> None:
    authorization, manifest, commit, torch2pc_dir, output_root = _authorization(tmp_path)
    cell_id = _plan(
        authorization,
        manifest,
        commit,
        torch2pc_dir,
        output_root,
    ).selected_cell_ids[0]

    def fail(_context: CanonicalCellContext) -> CanonicalCellResult:
        raise RuntimeError("first attempt")

    with pytest.raises(RuntimeError):
        execute_canonical_cell(
            manifest,
            authorization,
            output_root=output_root,
            cell_id=cell_id,
            device="cpu",
            dtype="float64",
            torch2pc_dir=torch2pc_dir,
            source_commit=commit,
            image_digest=CPU_IMAGE,
            executor=fail,
        )
    completed = execute_canonical_cell(
        manifest,
        authorization,
        output_root=output_root,
        cell_id=cell_id,
        device="cpu",
        dtype="float64",
        torch2pc_dir=torch2pc_dir,
        source_commit=commit,
        image_digest=CPU_IMAGE,
        executor=_fake_result,
    )
    attempts = list(
        (
            output_root
            / "canonical"
            / "lanes"
            / "cpu-float64"
            / "cells"
            / cell_id
            / "attempts"
        ).iterdir()
    )

    assert len(attempts) == 2
    assert len({path.name for path in attempts}) == 2
    assert completed["attempt_id"] in {path.name for path in attempts}


def test_max_attempts_marks_cell_exhausted(tmp_path: Path) -> None:
    authorization, manifest, commit, torch2pc_dir, output_root = _authorization(tmp_path)
    cell_id = _plan(
        authorization,
        manifest,
        commit,
        torch2pc_dir,
        output_root,
    ).selected_cell_ids[0]

    def fail(_context: CanonicalCellContext) -> CanonicalCellResult:
        raise RuntimeError("always fails")

    for _ in range(2):
        with pytest.raises(RuntimeError):
            execute_canonical_cell(
                manifest,
                authorization,
                output_root=output_root,
                cell_id=cell_id,
                device="cpu",
                dtype="float64",
                torch2pc_dir=torch2pc_dir,
                source_commit=commit,
                image_digest=CPU_IMAGE,
                executor=fail,
            )
    plan = _plan(
        authorization,
        manifest,
        commit,
        torch2pc_dir,
        output_root,
        retry_failed=True,
        max_attempts=2,
    )
    cell = next(item for item in plan.cells if item.cell_id == cell_id)

    assert cell.state == "exhausted"
    assert cell.selected_for_execution is False


def test_active_lane_lock_blocks_second_process(tmp_path: Path) -> None:
    authorization, manifest, commit, torch2pc_dir, output_root = _authorization(tmp_path)
    lock = output_root / "canonical" / "locks" / "cpu-float64.lock"
    lock.parent.mkdir(parents=True)
    lock.write_text(json.dumps({"pid": os.getpid()}) + "\n", encoding="utf-8")

    with pytest.raises(Stage3BExecutionError, match="lane lock is active"):
        execute_authorized_lane(
            authorization,
            manifest,
            output_root=output_root,
            device="cpu",
            dtype="float64",
            torch2pc_dir=torch2pc_dir,
            source_commit=commit,
            image_digest=CPU_IMAGE,
            probe=_cpu_probe(),
            executor=_fake_result,
        )


def test_stale_lane_lock_requires_resume_and_is_recovered(tmp_path: Path) -> None:
    authorization, manifest, commit, torch2pc_dir, output_root = _authorization(tmp_path)
    lock = output_root / "canonical" / "locks" / "cpu-float64.lock"
    lock.parent.mkdir(parents=True)
    lock.write_text(json.dumps({"pid": 999_999_999}) + "\n", encoding="utf-8")

    with pytest.raises(Stage3BExecutionError, match="requires explicit --resume"):
        execute_authorized_lane(
            authorization,
            manifest,
            output_root=output_root,
            device="cpu",
            dtype="float64",
            torch2pc_dir=torch2pc_dir,
            source_commit=commit,
            image_digest=CPU_IMAGE,
            probe=_cpu_probe(),
            executor=_fake_result,
        )
    result = execute_authorized_lane(
        authorization,
        manifest,
        output_root=output_root,
        device="cpu",
        dtype="float64",
        torch2pc_dir=torch2pc_dir,
        source_commit=commit,
        image_digest=CPU_IMAGE,
        resume=True,
        probe=_cpu_probe(),
        executor=_fake_result,
    )

    assert result["status"] == "lane_complete"
    assert not lock.exists()


def test_cell_failure_is_isolated_and_lane_remains_incomplete(tmp_path: Path) -> None:
    authorization, manifest, commit, torch2pc_dir, output_root = _authorization(tmp_path)
    first_cell = _plan(
        authorization,
        manifest,
        commit,
        torch2pc_dir,
        output_root,
    ).selected_cell_ids[0]

    def fail_one(context: CanonicalCellContext) -> CanonicalCellResult:
        if context.cell["cell_id"] == first_cell:
            raise RuntimeError("one cell failed")
        return _fake_result(context)

    result = execute_authorized_lane(
        authorization,
        manifest,
        output_root=output_root,
        device="cpu",
        dtype="float64",
        torch2pc_dir=torch2pc_dir,
        source_commit=commit,
        image_digest=CPU_IMAGE,
        probe=_cpu_probe(),
        executor=fail_one,
    )

    assert result["status"] == "lane_incomplete"
    assert result["executed_cell_count"] == 96
    assert result["completed_this_run_count"] == 95
    assert result["failed_this_run_count"] == 1
    assert result["completed_cell_count"] == 95
    assert result["remaining_cell_count"] == 1
    assert result["full_lane_complete"] is False


def test_execution_refuses_unacknowledged_interrupted_attempt(tmp_path: Path) -> None:
    authorization, manifest, commit, torch2pc_dir, output_root = _authorization(tmp_path)
    cell_id = _plan(
        authorization,
        manifest,
        commit,
        torch2pc_dir,
        output_root,
    ).selected_cell_ids[0]

    def interrupt(_context: CanonicalCellContext) -> CanonicalCellResult:
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        execute_canonical_cell(
            manifest,
            authorization,
            output_root=output_root,
            cell_id=cell_id,
            device="cpu",
            dtype="float64",
            torch2pc_dir=torch2pc_dir,
            source_commit=commit,
            image_digest=CPU_IMAGE,
            executor=interrupt,
        )
    with pytest.raises(Stage3BExecutionError, match="use --resume"):
        execute_authorized_lane(
            authorization,
            manifest,
            output_root=output_root,
            device="cpu",
            dtype="float64",
            torch2pc_dir=torch2pc_dir,
            source_commit=commit,
            image_digest=CPU_IMAGE,
            probe=_cpu_probe(),
            executor=_fake_result,
        )


def test_invalid_lane_and_attempt_limits_are_rejected(tmp_path: Path) -> None:
    authorization, manifest, commit, torch2pc_dir, output_root = _authorization(tmp_path)
    with pytest.raises(Stage3BExecutionError, match="limited to"):
        plan_authorized_lane(
            authorization,
            manifest,
            output_root=output_root,
            device="cpu",
            dtype="float32",
            torch2pc_dir=torch2pc_dir,
            source_commit=commit,
            image_digest=CPU_IMAGE,
            probe=_cpu_probe(),
        )
    with pytest.raises(Stage3BExecutionError, match="max_attempts"):
        _plan(
            authorization,
            manifest,
            commit,
            torch2pc_dir,
            output_root,
            max_attempts=4,
        )


def test_lane_journal_and_state_never_mark_full_campaign_complete(tmp_path: Path) -> None:
    authorization, manifest, commit, torch2pc_dir, output_root = _authorization(tmp_path)
    result = execute_authorized_lane(
        authorization,
        manifest,
        output_root=output_root,
        device="cpu",
        dtype="float64",
        torch2pc_dir=torch2pc_dir,
        source_commit=commit,
        image_digest=CPU_IMAGE,
        probe=_cpu_probe(),
        executor=_fake_result,
    )
    lane_state = json.loads(
        (
            output_root
            / "canonical"
            / "lanes"
            / "cpu-float64"
            / "lane-state.json"
        ).read_text(encoding="utf-8")
    )
    journal = [
        json.loads(line)
        for line in (
            output_root / "canonical" / "campaign-journal.jsonl"
        ).read_text(encoding="utf-8").splitlines()
    ]

    assert result["full_campaign_complete"] is False
    assert lane_state["full_lane_complete"] is True
    assert lane_state["full_campaign_complete"] is False
    assert lane_state["results_publication_permitted"] is False
    assert lane_state["test_dataset_access"] is False
    assert journal[0]["status"] == "lane_running"
    assert journal[-1]["status"] == "lane_complete"
