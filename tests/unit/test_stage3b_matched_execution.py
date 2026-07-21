from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from copy import deepcopy
from pathlib import Path
from typing import cast

import pytest
import torch
from torch import Tensor, nn

from torch2pc_thesis import stage3b_matched_execution as matched_execution
from torch2pc_thesis.profiling import ProfilingProtocol
from torch2pc_thesis.stage3b_b0_integration import (
    B0GateConfig,
    torch2pc_method_label,
)
from torch2pc_thesis.stage3b_execution import (
    Stage3BExecutionError,
    generate_manifest,
)
from torch2pc_thesis.stage3b_matched_authorization import (
    MATCHED_DISPATCH_SYMBOLS,
    MATCHED_OPERATOR_ACKNOWLEDGEMENT,
    MatchedRuntimeProbe,
    capture_matched_lane_preflight,
    freeze_matched_project_environment,
    issue_matched_campaign_authorization,
)
from torch2pc_thesis.stage3b_matched_execution import (
    MATCHED_EXECUTION_PROCESS_MODE,
    MATCHED_EXECUTION_STATE_RECONSTRUCTION,
    MatchedCellContext,
    MatchedCellResult,
    MatchedLanePlan,
    MatchedRetryableInfrastructureError,
    MatchedScientificCorrectnessError,
    execute_matched_authorized_lane,
    execute_matched_cell,
    plan_matched_authorized_lane,
    verify_matched_authorized_lane,
)
from torch2pc_thesis.stage3b_matched_profiling import (
    MATCHED_PROFILING_CANDIDATES,
    load_json_object,
    validate_matched_request,
)
from torch2pc_thesis.stage3b_matched_runner import (
    MATCHED_RUNNER_STATE_RESET_POLICY,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MATCHED_MANIFEST_PATH = (
    PROJECT_ROOT / "experiments/frozen/stage3b-matched-profiling-v2/manifest.json"
)
MATCHED_REQUEST_PATH = (
    PROJECT_ROOT / "experiments/frozen/stage3b-matched-profiling-v2/request.json"
)
ROCM_IMAGE = "sha256:" + "7" * 64


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    (root / "README.md").write_text("matched executor\n", encoding="utf-8")
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


def _rocm_probe() -> MatchedRuntimeProbe:
    return MatchedRuntimeProbe(
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


def _opening_inputs(
    tmp_path: Path,
) -> tuple[dict[str, object], dict[str, object], dict[str, object], Path]:
    matched_manifest = load_json_object(MATCHED_MANIFEST_PATH)
    request = deepcopy(load_json_object(MATCHED_REQUEST_PATH))
    base_manifest = generate_manifest()
    assert base_manifest["manifest_digest"] == matched_manifest["source_manifest_digest"]
    base_path = tmp_path / "STAGE3B-EXECUTION-MANIFEST.json"
    base_path.write_text(
        json.dumps(base_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    source_artifacts = cast(dict[str, object], request["source_artifacts"])
    execution_manifest = cast(dict[str, object], source_artifacts["execution_manifest"])
    execution_manifest["sha256"] = _sha256_file(base_path)
    payload = dict(request)
    payload.pop("request_digest")
    request["request_digest"] = _digest(payload)
    validate_matched_request(request)
    return matched_manifest, request, base_manifest, base_path


def _authorized_inputs(
    tmp_path: Path,
) -> tuple[
    dict[str, object],
    dict[str, object],
    dict[str, object],
    dict[str, object],
    Path,
    Path,
    str,
    Path,
    Path,
]:
    matched_manifest, request, base_manifest, base_path = _opening_inputs(tmp_path)
    project_root, source_commit = _project_repo(tmp_path)
    torch2pc_dir = _torch2pc(tmp_path)
    output_root = tmp_path / "matched-output"
    freeze = freeze_matched_project_environment(
        matched_manifest,
        request,
        base_manifest,
        base_manifest_path=base_path,
        project_root=project_root,
        torch2pc_dir=torch2pc_dir,
        output_root=output_root,
        source_commit=source_commit,
        minimum_free_bytes=1,
    )
    preflight = capture_matched_lane_preflight(
        freeze,
        matched_manifest,
        request,
        base_manifest,
        base_manifest_path=base_path,
        project_root=project_root,
        torch2pc_dir=torch2pc_dir,
        source_commit=source_commit,
        image_digest=ROCM_IMAGE,
        probe=_rocm_probe(),
        dispatch_symbols=MATCHED_DISPATCH_SYMBOLS,
    )
    authorization = issue_matched_campaign_authorization(
        freeze,
        preflight,
        operator_acknowledgement=MATCHED_OPERATOR_ACKNOWLEDGEMENT,
    )
    return (
        authorization,
        matched_manifest,
        request,
        base_manifest,
        base_path,
        project_root,
        source_commit,
        torch2pc_dir,
        output_root,
    )


def _plan(
    tmp_path: Path,
    *,
    resume: bool = False,
    retry_failed: bool = False,
    max_attempts: int = 2,
) -> tuple[
    MatchedLanePlan,
    tuple[
        dict[str, object],
        dict[str, object],
        dict[str, object],
        dict[str, object],
        Path,
        Path,
        str,
        Path,
        Path,
    ],
]:
    inputs = _authorized_inputs(tmp_path)
    (
        authorization,
        matched_manifest,
        request,
        base_manifest,
        base_path,
        project_root,
        source_commit,
        torch2pc_dir,
        output_root,
    ) = inputs
    plan = plan_matched_authorized_lane(
        authorization,
        matched_manifest,
        request,
        base_manifest,
        base_manifest_path=base_path,
        project_root=project_root,
        output_root=output_root,
        device="cpu",
        dtype="float64",
        torch2pc_dir=torch2pc_dir,
        source_commit=source_commit,
        image_digest=ROCM_IMAGE,
        resume=resume,
        retry_failed=retry_failed,
        max_attempts=max_attempts,
        probe=_rocm_probe(),
    )
    return plan, inputs


def _fake_result(context: MatchedCellContext) -> MatchedCellResult:
    return MatchedCellResult(
        resolved_config={
            "cell_id": str(context.cell["cell_id"]),
            "block_id": str(context.cell["block_id"]),
            "candidate_id": str(context.cell["candidate_id"]),
            "state_reset_policy": MATCHED_RUNNER_STATE_RESET_POLICY,
            "state_reconstruction": MATCHED_EXECUTION_STATE_RECONSTRUCTION,
        },
        environment={
            "authorization_token": context.authorization_token,
            "matched_manifest_digest": context.matched_manifest_digest,
            "opening_request_digest": context.opening_request_digest,
            "source_manifest_digest": context.source_manifest_digest,
        },
        measurements={
            "status": "matched_cell_complete",
            "evidence": False,
            "test_dataset_access": False,
        },
    )


def test_plan_selects_all_288_cells_in_frozen_order(tmp_path: Path) -> None:
    plan, (_authorization, matched_manifest, *_rest) = _plan(tmp_path)
    record = plan.to_record()

    assert len(plan.cells) == 288
    assert len(plan.selected_cell_ids) == 288
    assert record["matched_cell_count"] == 288
    assert record["summary"] == {"pending": 288}
    assert record["admitted_candidates"] == list(MATCHED_PROFILING_CANDIDATES)
    assert record["state_reset_policy"] == MATCHED_RUNNER_STATE_RESET_POLICY
    assert [cell.cell_id for cell in plan.cells] == [
        str(cell["cell_id"]) for cell in cast(list[dict[str, object]], matched_manifest["cells"])
    ]


def test_first_block_uses_contiguous_balanced_candidate_order(tmp_path: Path) -> None:
    plan, _inputs = _plan(tmp_path)
    first_block = plan.cells[0].block_id
    cells = [cell for cell in plan.cells if cell.block_id == first_block]

    assert len(cells) == 3
    assert [cell.candidate_order for cell in cells] == [0, 1, 2]
    assert {cell.candidate_id for cell in cells} == set(MATCHED_PROFILING_CANDIDATES)


def test_verify_returns_non_evidence_execution_contract(tmp_path: Path) -> None:
    (
        authorization,
        matched_manifest,
        request,
        base_manifest,
        base_path,
        project_root,
        source_commit,
        torch2pc_dir,
        output_root,
    ) = _authorized_inputs(tmp_path)

    result = verify_matched_authorized_lane(
        authorization,
        matched_manifest,
        request,
        base_manifest,
        base_manifest_path=base_path,
        project_root=project_root,
        torch2pc_dir=torch2pc_dir,
        output_root=output_root,
        source_commit=source_commit,
        device="cpu",
        dtype="float64",
        image_digest=ROCM_IMAGE,
        probe=_rocm_probe(),
    )

    assert result["authorization_verified"] is True
    assert result["execution_permitted"] is True
    assert result["measurements_allowed"] is True
    assert result["evidence"] is False
    assert result["results_publication_permitted"] is False
    assert result["test_dataset_access"] is False


def test_single_cell_accepts_runtime_project_relocation(tmp_path: Path) -> None:
    (
        authorization,
        matched_manifest,
        request,
        base_manifest,
        base_path,
        project_root,
        source_commit,
        torch2pc_dir,
        output_root,
    ) = _authorized_inputs(tmp_path)
    relocated_project = tmp_path / "workspace"
    shutil.copytree(project_root, relocated_project)
    relocated_manifest = tmp_path / "container-inputs" / base_path.name
    relocated_manifest.parent.mkdir()
    shutil.copy2(base_path, relocated_manifest)
    first_cell = cast(
        list[dict[str, object]],
        matched_manifest["cells"],
    )[0]

    completed = execute_matched_cell(
        matched_manifest,
        request,
        base_manifest,
        authorization,
        output_root=output_root,
        cell_id=str(first_cell["cell_id"]),
        device="cpu",
        dtype="float64",
        project_root=relocated_project,
        base_manifest_path=relocated_manifest,
        torch2pc_dir=torch2pc_dir,
        source_commit=source_commit,
        image_digest=ROCM_IMAGE,
        executor=_fake_result,
    )

    assert completed["status"] == "matched_cell_complete"
    assert Path(str(completed["attempt_directory"])).is_dir()


def test_single_cell_rejects_relocated_manifest_content_change(
    tmp_path: Path,
) -> None:
    (
        authorization,
        matched_manifest,
        request,
        base_manifest,
        base_path,
        project_root,
        source_commit,
        torch2pc_dir,
        output_root,
    ) = _authorized_inputs(tmp_path)
    relocated_project = tmp_path / "workspace"
    shutil.copytree(project_root, relocated_project)
    relocated_manifest = tmp_path / "container-inputs" / base_path.name
    relocated_manifest.parent.mkdir()
    relocated_manifest.write_text("{}\n", encoding="utf-8")
    first_cell = cast(
        list[dict[str, object]],
        matched_manifest["cells"],
    )[0]

    with pytest.raises(
        Stage3BExecutionError,
        match="base manifest content differs from freeze",
    ):
        execute_matched_cell(
            matched_manifest,
            request,
            base_manifest,
            authorization,
            output_root=output_root,
            cell_id=str(first_cell["cell_id"]),
            device="cpu",
            dtype="float64",
            project_root=relocated_project,
            base_manifest_path=relocated_manifest,
            torch2pc_dir=torch2pc_dir,
            source_commit=source_commit,
            image_digest=ROCM_IMAGE,
            executor=_fake_result,
        )


def test_single_fake_cell_writes_immutable_attempt_layout(tmp_path: Path) -> None:
    (
        authorization,
        matched_manifest,
        request,
        base_manifest,
        base_path,
        project_root,
        source_commit,
        torch2pc_dir,
        output_root,
    ) = _authorized_inputs(tmp_path)
    cell_id = str(cast(list[dict[str, object]], matched_manifest["cells"])[0]["cell_id"])

    completed = execute_matched_cell(
        matched_manifest,
        request,
        base_manifest,
        authorization,
        output_root=output_root,
        cell_id=cell_id,
        device="cpu",
        dtype="float64",
        project_root=project_root,
        base_manifest_path=base_path,
        torch2pc_dir=torch2pc_dir,
        source_commit=source_commit,
        image_digest=ROCM_IMAGE,
        executor=_fake_result,
    )

    attempt = Path(str(completed["attempt_directory"]))
    assert completed["status"] == "matched_cell_complete"
    assert completed["full_cell_complete"] is True
    assert (attempt / "request.json").is_file()
    assert (attempt / "started.json").is_file()
    assert (attempt / "resolved-config.json").is_file()
    assert (attempt / "environment.json").is_file()
    assert (attempt / "measurements.json").is_file()
    assert (attempt / "completed.json").is_file()
    assert not (attempt / "failed.json").exists()


def test_fake_executor_completes_all_288_cells(tmp_path: Path) -> None:
    (
        authorization,
        matched_manifest,
        request,
        base_manifest,
        base_path,
        project_root,
        source_commit,
        torch2pc_dir,
        output_root,
    ) = _authorized_inputs(tmp_path)

    result = execute_matched_authorized_lane(
        authorization,
        matched_manifest,
        request,
        base_manifest,
        base_manifest_path=base_path,
        project_root=project_root,
        output_root=output_root,
        device="cpu",
        dtype="float64",
        torch2pc_dir=torch2pc_dir,
        source_commit=source_commit,
        image_digest=ROCM_IMAGE,
        probe=_rocm_probe(),
        executor=_fake_result,
    )

    assert result["status"] == "matched_lane_complete"
    assert result["executed_cell_count"] == 288
    assert result["completed_cell_count"] == 288
    assert result["remaining_cell_count"] == 0
    assert result["full_lane_complete"] is True
    assert result["full_stage3b_campaign_complete"] is False
    assert result["evidence"] is False
    assert result["test_dataset_access"] is False

    lane_state = json.loads(
        (
            output_root
            / "matched"
            / "lanes"
            / "cpu-float64"
            / "lane-state.json"
        ).read_text(encoding="utf-8")
    )
    journal = [
        json.loads(line)
        for line in (
            output_root / "matched" / "campaign-journal.jsonl"
        ).read_text(encoding="utf-8").splitlines()
    ]
    assert lane_state["status"] == "matched_lane_complete"
    assert lane_state["completed_cell_count"] == 288
    assert lane_state["full_stage3b_campaign_complete"] is False
    assert lane_state["results_publication_permitted"] is False
    assert lane_state["test_dataset_access"] is False
    assert journal[0]["status"] == "matched_lane_running"
    assert journal[-1]["status"] == "matched_lane_complete"


def test_completed_attempts_are_terminal_on_resume(tmp_path: Path) -> None:
    (
        authorization,
        matched_manifest,
        request,
        base_manifest,
        base_path,
        project_root,
        source_commit,
        torch2pc_dir,
        output_root,
    ) = _authorized_inputs(tmp_path)
    first_cell = cast(list[dict[str, object]], matched_manifest["cells"])[0]
    execute_matched_cell(
        matched_manifest,
        request,
        base_manifest,
        authorization,
        output_root=output_root,
        cell_id=str(first_cell["cell_id"]),
        device="cpu",
        dtype="float64",
        project_root=project_root,
        base_manifest_path=base_path,
        torch2pc_dir=torch2pc_dir,
        source_commit=source_commit,
        image_digest=ROCM_IMAGE,
        executor=_fake_result,
    )

    plan = plan_matched_authorized_lane(
        authorization,
        matched_manifest,
        request,
        base_manifest,
        base_manifest_path=base_path,
        project_root=project_root,
        output_root=output_root,
        device="cpu",
        dtype="float64",
        torch2pc_dir=torch2pc_dir,
        source_commit=source_commit,
        image_digest=ROCM_IMAGE,
        resume=True,
        retry_failed=True,
        probe=_rocm_probe(),
    )
    completed = next(cell for cell in plan.cells if cell.cell_id == first_cell["cell_id"])
    assert completed.state == "completed"
    assert completed.selected_for_execution is False
    assert len(plan.selected_cell_ids) == 287


def test_failed_attempt_requires_explicit_retry(tmp_path: Path) -> None:
    (
        authorization,
        matched_manifest,
        request,
        base_manifest,
        base_path,
        project_root,
        source_commit,
        torch2pc_dir,
        output_root,
    ) = _authorized_inputs(tmp_path)
    first_cell = cast(list[dict[str, object]], matched_manifest["cells"])[0]

    def fail(_context: MatchedCellContext) -> MatchedCellResult:
        raise MatchedRetryableInfrastructureError("synthetic matched failure")

    with pytest.raises(
        MatchedRetryableInfrastructureError,
        match="synthetic matched failure",
    ):
        execute_matched_cell(
            matched_manifest,
            request,
            base_manifest,
            authorization,
            output_root=output_root,
            cell_id=str(first_cell["cell_id"]),
            device="cpu",
            dtype="float64",
            project_root=project_root,
            base_manifest_path=base_path,
            torch2pc_dir=torch2pc_dir,
            source_commit=source_commit,
            image_digest=ROCM_IMAGE,
            executor=fail,
        )

    blocked = plan_matched_authorized_lane(
        authorization,
        matched_manifest,
        request,
        base_manifest,
        base_manifest_path=base_path,
        project_root=project_root,
        output_root=output_root,
        device="cpu",
        dtype="float64",
        torch2pc_dir=torch2pc_dir,
        source_commit=source_commit,
        image_digest=ROCM_IMAGE,
        probe=_rocm_probe(),
    )
    failed = next(cell for cell in blocked.cells if cell.cell_id == first_cell["cell_id"])
    assert failed.state == "failed"
    assert failed.selected_for_execution is False

    retried = plan_matched_authorized_lane(
        authorization,
        matched_manifest,
        request,
        base_manifest,
        base_manifest_path=base_path,
        project_root=project_root,
        output_root=output_root,
        device="cpu",
        dtype="float64",
        torch2pc_dir=torch2pc_dir,
        source_commit=source_commit,
        image_digest=ROCM_IMAGE,
        retry_failed=True,
        probe=_rocm_probe(),
    )
    retry_cell = next(cell for cell in retried.cells if cell.cell_id == first_cell["cell_id"])
    assert retry_cell.state == "retryable"
    assert retry_cell.selected_for_execution is True


def test_scientific_failure_is_non_retryable_and_blocks_lane(tmp_path: Path) -> None:
    (
        authorization,
        matched_manifest,
        request,
        base_manifest,
        base_path,
        project_root,
        source_commit,
        torch2pc_dir,
        output_root,
    ) = _authorized_inputs(tmp_path)
    first_cell = cast(list[dict[str, object]], matched_manifest["cells"])[0]

    def fail(_context: MatchedCellContext) -> MatchedCellResult:
        raise MatchedScientificCorrectnessError("synthetic correctness failure")

    with pytest.raises(
        MatchedScientificCorrectnessError,
        match="synthetic correctness failure",
    ):
        execute_matched_cell(
            matched_manifest,
            request,
            base_manifest,
            authorization,
            output_root=output_root,
            cell_id=str(first_cell["cell_id"]),
            device="cpu",
            dtype="float64",
            project_root=project_root,
            base_manifest_path=base_path,
            torch2pc_dir=torch2pc_dir,
            source_commit=source_commit,
            image_digest=ROCM_IMAGE,
            executor=fail,
        )

    plan = plan_matched_authorized_lane(
        authorization,
        matched_manifest,
        request,
        base_manifest,
        base_manifest_path=base_path,
        project_root=project_root,
        output_root=output_root,
        device="cpu",
        dtype="float64",
        torch2pc_dir=torch2pc_dir,
        source_commit=source_commit,
        image_digest=ROCM_IMAGE,
        retry_failed=True,
        probe=_rocm_probe(),
    )
    blocked = next(
        cell for cell in plan.cells if cell.cell_id == first_cell["cell_id"]
    )
    assert blocked.state == "blocked"
    assert blocked.non_retryable_failed_attempt_count == 1
    assert blocked.selected_for_execution is False


def test_interrupted_attempt_requires_explicit_resume(tmp_path: Path) -> None:
    (
        authorization,
        matched_manifest,
        request,
        base_manifest,
        base_path,
        project_root,
        source_commit,
        torch2pc_dir,
        output_root,
    ) = _authorized_inputs(tmp_path)
    first_cell = cast(list[dict[str, object]], matched_manifest["cells"])[0]

    def interrupt(_context: MatchedCellContext) -> MatchedCellResult:
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        execute_matched_cell(
            matched_manifest,
            request,
            base_manifest,
            authorization,
            output_root=output_root,
            cell_id=str(first_cell["cell_id"]),
            device="cpu",
            dtype="float64",
            project_root=project_root,
            base_manifest_path=base_path,
            torch2pc_dir=torch2pc_dir,
            source_commit=source_commit,
            image_digest=ROCM_IMAGE,
            executor=interrupt,
        )

    blocked = plan_matched_authorized_lane(
        authorization,
        matched_manifest,
        request,
        base_manifest,
        base_manifest_path=base_path,
        project_root=project_root,
        output_root=output_root,
        device="cpu",
        dtype="float64",
        torch2pc_dir=torch2pc_dir,
        source_commit=source_commit,
        image_digest=ROCM_IMAGE,
        probe=_rocm_probe(),
    )
    resumed = plan_matched_authorized_lane(
        authorization,
        matched_manifest,
        request,
        base_manifest,
        base_manifest_path=base_path,
        project_root=project_root,
        output_root=output_root,
        device="cpu",
        dtype="float64",
        torch2pc_dir=torch2pc_dir,
        source_commit=source_commit,
        image_digest=ROCM_IMAGE,
        resume=True,
        probe=_rocm_probe(),
    )
    blocked_cell = next(
        cell for cell in blocked.cells if cell.cell_id == first_cell["cell_id"]
    )
    resumed_cell = next(
        cell for cell in resumed.cells if cell.cell_id == first_cell["cell_id"]
    )
    assert blocked_cell.state == "running"
    assert blocked_cell.selected_for_execution is False
    assert resumed_cell.state == "retryable"
    assert resumed_cell.selected_for_execution is True


def test_retry_creates_new_attempt_id(tmp_path: Path) -> None:
    (
        authorization,
        matched_manifest,
        request,
        base_manifest,
        base_path,
        project_root,
        source_commit,
        torch2pc_dir,
        output_root,
    ) = _authorized_inputs(tmp_path)
    first_cell = cast(list[dict[str, object]], matched_manifest["cells"])[0]
    cell_id = str(first_cell["cell_id"])

    def fail(_context: MatchedCellContext) -> MatchedCellResult:
        raise MatchedRetryableInfrastructureError("first matched attempt")

    with pytest.raises(
        MatchedRetryableInfrastructureError,
        match="first matched attempt",
    ):
        execute_matched_cell(
            matched_manifest,
            request,
            base_manifest,
            authorization,
            output_root=output_root,
            cell_id=cell_id,
            device="cpu",
            dtype="float64",
            project_root=project_root,
            base_manifest_path=base_path,
            torch2pc_dir=torch2pc_dir,
            source_commit=source_commit,
            image_digest=ROCM_IMAGE,
            executor=fail,
        )
    completed = execute_matched_cell(
        matched_manifest,
        request,
        base_manifest,
        authorization,
        output_root=output_root,
        cell_id=cell_id,
        device="cpu",
        dtype="float64",
        project_root=project_root,
        base_manifest_path=base_path,
        torch2pc_dir=torch2pc_dir,
        source_commit=source_commit,
        image_digest=ROCM_IMAGE,
        executor=_fake_result,
    )
    attempts = list(
        (
            output_root
            / "matched"
            / "lanes"
            / "cpu-float64"
            / "cells"
            / cell_id
            / "attempts"
        ).iterdir()
    )
    assert len(attempts) == 2
    assert len({attempt.name for attempt in attempts}) == 2
    assert completed["attempt_id"] in {attempt.name for attempt in attempts}


def test_max_attempts_marks_failed_cell_exhausted(tmp_path: Path) -> None:
    (
        authorization,
        matched_manifest,
        request,
        base_manifest,
        base_path,
        project_root,
        source_commit,
        torch2pc_dir,
        output_root,
    ) = _authorized_inputs(tmp_path)
    first_cell = cast(list[dict[str, object]], matched_manifest["cells"])[0]
    cell_id = str(first_cell["cell_id"])

    def fail(_context: MatchedCellContext) -> MatchedCellResult:
        raise MatchedRetryableInfrastructureError("always fails")

    for _ in range(2):
        with pytest.raises(
            MatchedRetryableInfrastructureError,
            match="always fails",
        ):
            execute_matched_cell(
                matched_manifest,
                request,
                base_manifest,
                authorization,
                output_root=output_root,
                cell_id=cell_id,
                device="cpu",
                dtype="float64",
                project_root=project_root,
                base_manifest_path=base_path,
                torch2pc_dir=torch2pc_dir,
                source_commit=source_commit,
                image_digest=ROCM_IMAGE,
                executor=fail,
            )

    plan = plan_matched_authorized_lane(
        authorization,
        matched_manifest,
        request,
        base_manifest,
        base_manifest_path=base_path,
        project_root=project_root,
        output_root=output_root,
        device="cpu",
        dtype="float64",
        torch2pc_dir=torch2pc_dir,
        source_commit=source_commit,
        image_digest=ROCM_IMAGE,
        max_attempts=2,
        retry_failed=True,
        probe=_rocm_probe(),
    )
    exhausted = next(cell for cell in plan.cells if cell.cell_id == cell_id)
    assert exhausted.state == "exhausted"
    assert exhausted.selected_for_execution is False


def test_active_lane_lock_blocks_execution(tmp_path: Path) -> None:
    (
        authorization,
        matched_manifest,
        request,
        base_manifest,
        base_path,
        project_root,
        source_commit,
        torch2pc_dir,
        output_root,
    ) = _authorized_inputs(tmp_path)
    lock = output_root / "matched" / "locks" / "cpu-float64.lock"
    lock.parent.mkdir(parents=True)
    lock.write_text(json.dumps({"pid": os.getpid()}) + "\n", encoding="utf-8")

    with pytest.raises(Stage3BExecutionError, match="lane lock is active"):
        execute_matched_authorized_lane(
            authorization,
            matched_manifest,
            request,
            base_manifest,
            base_manifest_path=base_path,
            project_root=project_root,
            output_root=output_root,
            device="cpu",
            dtype="float64",
            torch2pc_dir=torch2pc_dir,
            source_commit=source_commit,
            image_digest=ROCM_IMAGE,
            probe=_rocm_probe(),
            executor=_fake_result,
        )


def test_invalid_lane_and_attempt_limit_are_rejected(tmp_path: Path) -> None:
    (
        authorization,
        matched_manifest,
        request,
        base_manifest,
        base_path,
        project_root,
        source_commit,
        torch2pc_dir,
        output_root,
    ) = _authorized_inputs(tmp_path)

    with pytest.raises(Stage3BExecutionError, match="limited to"):
        plan_matched_authorized_lane(
            authorization,
            matched_manifest,
            request,
            base_manifest,
            base_manifest_path=base_path,
            project_root=project_root,
            output_root=output_root,
            device="cpu",
            dtype="float32",
            torch2pc_dir=torch2pc_dir,
            source_commit=source_commit,
            image_digest=ROCM_IMAGE,
            probe=_rocm_probe(),
        )
    with pytest.raises(Stage3BExecutionError, match="max_attempts"):
        plan_matched_authorized_lane(
            authorization,
            matched_manifest,
            request,
            base_manifest,
            base_manifest_path=base_path,
            project_root=project_root,
            output_root=output_root,
            device="cpu",
            dtype="float64",
            torch2pc_dir=torch2pc_dir,
            source_commit=source_commit,
            image_digest=ROCM_IMAGE,
            max_attempts=4,
            probe=_rocm_probe(),
        )


def test_emergency_stop_blocks_execution_plan(tmp_path: Path) -> None:
    (
        authorization,
        matched_manifest,
        request,
        base_manifest,
        base_path,
        project_root,
        source_commit,
        torch2pc_dir,
        output_root,
    ) = _authorized_inputs(tmp_path)
    Path(str(authorization["emergency_stop_path"])).touch()

    with pytest.raises(Stage3BExecutionError, match="emergency stop is active"):
        plan_matched_authorized_lane(
            authorization,
            matched_manifest,
            request,
            base_manifest,
            base_manifest_path=base_path,
            project_root=project_root,
            output_root=output_root,
            device="cpu",
            dtype="float64",
            torch2pc_dir=torch2pc_dir,
            source_commit=source_commit,
            image_digest=ROCM_IMAGE,
            probe=_rocm_probe(),
        )


def test_production_contract_declares_fresh_child_per_cell() -> None:
    assert MATCHED_EXECUTION_PROCESS_MODE == "fresh_python_child_per_cell"
    assert MATCHED_EXECUTION_STATE_RECONSTRUCTION == (
        "deterministic_fresh_process_reconstruction_per_candidate"
    )


def _fake_reference_pc_infer(
    model: nn.Module,
    loss_fn: nn.Module,
    inputs: Tensor,
    targets: Tensor,
    method: str,
    *,
    eta: float,
    n: int,
) -> tuple[list[Tensor], Tensor, dict[str, object]]:
    del method
    predictions = model(inputs)
    loss = loss_fn(predictions, targets)
    loss.backward()
    return [inputs + eta * 0.0, predictions], loss, {"steps": n}


def test_cross_candidate_correctness_probe_is_untimed_and_persisted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        matched_execution,
        "load_candidate_pc_infer",
        lambda _candidate_id, _root: _fake_reference_pc_infer,
    )
    cell = {
        "cell_id": "cell-0",
        "block_id": "block-0",
        "block_order": 0,
        "candidate_id": "stage2_baseline",
        "candidate_order": 0,
        "method": "fixedpred",
        "depth": 4,
        "width": 64,
        "batch_size": 2,
        "model_seed": 70,
    }
    context = MatchedCellContext(
        cell=cell,
        authorization_token="a" * 64,
        matched_manifest_digest="b" * 64,
        opening_request_digest="c" * 64,
        source_manifest_digest="d" * 64,
        output_root=tmp_path / "runtime",
        attempt_directory=tmp_path / "attempt",
        device=torch.device("cpu"),
        requested_device="cpu",
        dtype=torch.float64,
        dtype_name="float64",
        torch2pc_dir=tmp_path,
        source_commit="e" * 40,
        image_digest="sha256:" + "f" * 64,
        emergency_stop_path=tmp_path / "stop",
        protocol=ProfilingProtocol(warmup_steps=0, measured_steps=1, repetitions=1),
    )
    config = B0GateConfig(
        method="fixedpred",
        torch2pc_method=torch2pc_method_label("fixedpred"),
        eta=0.1,
        inference_steps=1,
        device=torch.device("cpu"),
        dtype=torch.float64,
    )

    record = matched_execution._run_block_cross_candidate_correctness_gate(
        context,
        architecture="mlp_d4_w64",
        method="fixedpred",
        depth=4,
        width=64,
        batch_size=2,
        model_seed=70,
        block_id="block-0",
        gate_config=config,
    )

    assert record["passed"] is True
    assert record["untimed"] is True
    assert len(cast(list[dict[str, object]], record["pair_comparisons"])) == 2
    persisted = (
        context.output_root
        / "matched/lanes/cpu-float64/blocks/block-0/cross-candidate-correctness.json"
    )
    assert persisted.is_file()


def test_cross_candidate_correctness_probe_rejects_divergence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def divergent_pc_infer(
        model: nn.Module,
        loss_fn: nn.Module,
        inputs: Tensor,
        targets: Tensor,
        method: str,
        *,
        eta: float,
        n: int,
    ) -> tuple[list[Tensor], Tensor, dict[str, object]]:
        beliefs, loss, metadata = _fake_reference_pc_infer(
            model,
            loss_fn,
            inputs,
            targets,
            method,
            eta=eta,
            n=n,
        )
        return [beliefs[0], beliefs[1] + 1.0], loss, metadata

    def loader(candidate_id: str, _root: Path):
        if candidate_id == "composite_vjp":
            return divergent_pc_infer
        return _fake_reference_pc_infer

    monkeypatch.setattr(matched_execution, "load_candidate_pc_infer", loader)
    cell = {
        "cell_id": "cell-0",
        "block_id": "block-0",
        "block_order": 0,
        "candidate_id": "stage2_baseline",
        "candidate_order": 0,
        "method": "fixedpred",
        "depth": 4,
        "width": 64,
        "batch_size": 2,
        "model_seed": 70,
    }
    context = MatchedCellContext(
        cell=cell,
        authorization_token="a" * 64,
        matched_manifest_digest="b" * 64,
        opening_request_digest="c" * 64,
        source_manifest_digest="d" * 64,
        output_root=tmp_path / "runtime",
        attempt_directory=tmp_path / "attempt",
        device=torch.device("cpu"),
        requested_device="cpu",
        dtype=torch.float64,
        dtype_name="float64",
        torch2pc_dir=tmp_path,
        source_commit="e" * 40,
        image_digest="sha256:" + "f" * 64,
        emergency_stop_path=tmp_path / "stop",
        protocol=ProfilingProtocol(
            warmup_steps=0,
            measured_steps=1,
            repetitions=1,
        ),
    )
    config = B0GateConfig(
        method="fixedpred",
        torch2pc_method=torch2pc_method_label("fixedpred"),
        eta=0.1,
        inference_steps=1,
        device=torch.device("cpu"),
        dtype=torch.float64,
    )

    with pytest.raises(
        MatchedScientificCorrectnessError,
        match="cross-candidate correctness gate failed",
    ):
        matched_execution._run_block_cross_candidate_correctness_gate(
            context,
            architecture="mlp_d4_w64",
            method="fixedpred",
            depth=4,
            width=64,
            batch_size=2,
            model_seed=70,
            block_id="block-0",
            gate_config=config,
        )

    record_path = (
        context.output_root
        / "matched/lanes/cpu-float64/blocks/block-0/"
        "cross-candidate-correctness.json"
    )
    record = json.loads(record_path.read_text(encoding="utf-8"))
    assert record["passed"] is False
    assert record["status"] == "cross_candidate_correctness_failed"
    assert record["untimed"] is True
