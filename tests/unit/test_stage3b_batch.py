from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import cast

import pytest

from torch2pc_thesis.stage3b_batch import (
    B0_BATCH_MAX_CELLS,
    execute_b0_batch_smoke,
    plan_b0_batch_smoke,
)
from torch2pc_thesis.stage3b_execution import Stage3BExecutionError, generate_manifest

SOURCE_COMMIT = "1" * 40


def _write_attempt(
    root: Path,
    *,
    cell_id: str,
    manifest_digest: str,
    device: str = "cpu",
    dtype: str = "float64",
    terminal: str,
    source_commit: str = SOURCE_COMMIT,
) -> None:
    attempt = root / "smoke" / "cells" / cell_id / "attempts" / f"attempt-{terminal}"
    attempt.mkdir(parents=True)
    request = {
        "cell_id": cell_id,
        "manifest_digest": manifest_digest,
        "candidate_id": "stage2_baseline",
        "device": device,
        "dtype": dtype,
        "execution_scope": "single_cell_smoke",
    }
    (attempt / "request.json").write_text(json.dumps(request), encoding="utf-8")
    (attempt / "started.json").write_text(
        json.dumps({**request, "status": "smoke_running"}), encoding="utf-8"
    )
    if terminal == "completed":
        (attempt / "completed.json").write_text(
            json.dumps({**request, "status": "smoke_passed"}), encoding="utf-8"
        )
        (attempt / "environment.json").write_text(
            json.dumps({"project_source_commit": source_commit}), encoding="utf-8"
        )
    elif terminal == "failed":
        (attempt / "failed.json").write_text(
            json.dumps({**request, "status": "smoke_failed"}), encoding="utf-8"
        )


def test_plan_contains_only_96_deterministic_b0_cells(tmp_path: Path) -> None:
    manifest = generate_manifest()
    first = plan_b0_batch_smoke(
        manifest,
        output_root=tmp_path,
        device="cpu",
        dtype="float64",
        source_commit=SOURCE_COMMIT,
        max_cells=4,
    )
    second = plan_b0_batch_smoke(
        manifest,
        output_root=tmp_path,
        device="cpu",
        dtype="float64",
        source_commit=SOURCE_COMMIT,
        max_cells=4,
    )

    assert len(first.cells) == 96
    assert len({cell.cell_id for cell in first.cells}) == 96
    assert all(cell.state == "pending" for cell in first.cells)
    assert first.selected_cell_ids == second.selected_cell_ids
    assert len(first.selected_cell_ids) == 4
    selected_methods = [
        cell.method for cell in first.cells if cell.selected_for_execution
    ]
    assert selected_methods[:2] == ["fixedpred", "strict"]
    assert first.to_record()["full_campaign_execution_enabled"] is False


def test_max_cells_above_hard_limit_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(Stage3BExecutionError, match="max_cells"):
        plan_b0_batch_smoke(
            generate_manifest(),
            output_root=tmp_path,
            device="cpu",
            dtype="float64",
            source_commit=SOURCE_COMMIT,
            max_cells=B0_BATCH_MAX_CELLS + 1,
        )


@pytest.mark.parametrize(
    ("device", "dtype"),
    [("cpu", "float32"), ("rocm", "float64"), ("cuda", "float32")],
)
def test_invalid_lane_is_rejected(tmp_path: Path, device: str, dtype: str) -> None:
    with pytest.raises(Stage3BExecutionError, match="lanes"):
        plan_b0_batch_smoke(
            generate_manifest(),
            output_root=tmp_path,
            device=device,
            dtype=dtype,
            source_commit=SOURCE_COMMIT,
        )


def test_successful_matching_attempt_is_skipped(tmp_path: Path) -> None:
    manifest = generate_manifest()
    manifest_digest = cast(str, manifest["manifest_digest"])
    initial = plan_b0_batch_smoke(
        manifest,
        output_root=tmp_path,
        device="cpu",
        dtype="float64",
        source_commit=SOURCE_COMMIT,
        max_cells=1,
    )
    cell_id = initial.selected_cell_ids[0]
    _write_attempt(
        tmp_path,
        cell_id=cell_id,
        manifest_digest=manifest_digest,
        terminal="completed",
    )

    resumed = plan_b0_batch_smoke(
        manifest,
        output_root=tmp_path,
        device="cpu",
        dtype="float64",
        source_commit=SOURCE_COMMIT,
        max_cells=1,
    )
    state_by_id = {cell.cell_id: cell.state for cell in resumed.cells}
    assert state_by_id[cell_id] == "smoke_passed"
    assert resumed.selected_cell_ids[0] != cell_id


def test_failed_and_running_attempts_require_explicit_recovery(tmp_path: Path) -> None:
    manifest = generate_manifest()
    digest = cast(str, manifest["manifest_digest"])
    base = plan_b0_batch_smoke(
        manifest,
        output_root=tmp_path,
        device="cpu",
        dtype="float64",
        source_commit=SOURCE_COMMIT,
        max_cells=2,
    )
    failed_id, running_id = base.selected_cell_ids
    _write_attempt(tmp_path, cell_id=failed_id, manifest_digest=digest, terminal="failed")
    _write_attempt(tmp_path, cell_id=running_id, manifest_digest=digest, terminal="running")

    blocked = plan_b0_batch_smoke(
        manifest,
        output_root=tmp_path,
        device="cpu",
        dtype="float64",
        source_commit=SOURCE_COMMIT,
        max_cells=2,
    )
    blocked_states = {cell.cell_id: cell.state for cell in blocked.cells}
    assert blocked_states[failed_id] == "failed"
    assert blocked_states[running_id] == "running"

    recovered = plan_b0_batch_smoke(
        manifest,
        output_root=tmp_path,
        device="cpu",
        dtype="float64",
        source_commit=SOURCE_COMMIT,
        max_cells=2,
        resume=True,
        retry_failed=True,
    )
    recovered_states = {cell.cell_id: cell.state for cell in recovered.cells}
    assert recovered_states[failed_id] == "retryable"
    assert recovered_states[running_id] == "retryable"


def test_attempt_limit_marks_failed_cell_exhausted(tmp_path: Path) -> None:
    manifest = generate_manifest()
    digest = cast(str, manifest["manifest_digest"])
    plan = plan_b0_batch_smoke(
        manifest,
        output_root=tmp_path,
        device="cpu",
        dtype="float64",
        source_commit=SOURCE_COMMIT,
        max_cells=1,
    )
    cell_id = plan.selected_cell_ids[0]
    _write_attempt(tmp_path, cell_id=cell_id, manifest_digest=digest, terminal="failed")

    exhausted = plan_b0_batch_smoke(
        manifest,
        output_root=tmp_path,
        device="cpu",
        dtype="float64",
        source_commit=SOURCE_COMMIT,
        max_cells=1,
        max_attempts=1,
        retry_failed=True,
    )
    state = next(cell.state for cell in exhausted.cells if cell.cell_id == cell_id)
    assert state == "exhausted"


def test_batch_failure_isolated_and_journal_is_append_only(tmp_path: Path) -> None:
    calls: list[str] = []

    def fake_runner(
        manifest: Mapping[str, object],
        *,
        output_root: Path,
        cell_id: str,
        device: str,
        dtype: str,
        torch2pc_dir: Path,
        source_commit: str,
        image_id: str | None = None,
    ) -> dict[str, object]:
        del manifest, output_root, device, dtype, torch2pc_dir, source_commit, image_id
        calls.append(cell_id)
        if len(calls) == 1:
            raise RuntimeError("synthetic failure")
        return {
            "attempt_id": f"attempt-{cell_id}",
            "attempt_directory": f"/tmp/{cell_id}",
        }

    result = execute_b0_batch_smoke(
        generate_manifest(),
        output_root=tmp_path,
        device="cpu",
        dtype="float64",
        source_commit=SOURCE_COMMIT,
        max_cells=2,
        torch2pc_dir=Path("/tmp/torch2pc"),
        runner=fake_runner,
    )

    assert result["status"] == "batch_smoke_partial_failure"
    assert result["executed_cell_count"] == 2
    assert result["passed_cell_count"] == 1
    assert result["failed_cell_count"] == 1
    assert len(calls) == 2

    journal = tmp_path / "batch" / "campaign-journal.jsonl"
    lines = journal.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["status"] == "batch_smoke_running"
    assert json.loads(lines[1])["status"] == "batch_smoke_partial_failure"


def test_active_lock_blocks_duplicate_lane(tmp_path: Path) -> None:
    lock = tmp_path / "batch" / "locks" / "cpu-float64.lock"
    lock.parent.mkdir(parents=True)
    lock.write_text(
        json.dumps({"pid": 1, "hostname": __import__("socket").gethostname()}),
        encoding="utf-8",
    )

    def unused_runner(
        manifest: Mapping[str, object],
        *,
        output_root: Path,
        cell_id: str,
        device: str,
        dtype: str,
        torch2pc_dir: Path,
        source_commit: str,
        image_id: str | None = None,
    ) -> dict[str, object]:
        del manifest, output_root, cell_id, device, dtype, torch2pc_dir, source_commit, image_id
        return {}

    with pytest.raises(Stage3BExecutionError, match="already locked"):
        execute_b0_batch_smoke(
            generate_manifest(),
            output_root=tmp_path,
            device="cpu",
            dtype="float64",
            source_commit=SOURCE_COMMIT,
            max_cells=1,
            torch2pc_dir=Path("/tmp/torch2pc"),
            runner=unused_runner,
        )


def test_completed_cpu_attempt_does_not_skip_rocm_lane(tmp_path: Path) -> None:
    manifest = generate_manifest()
    digest = cast(str, manifest["manifest_digest"])
    cpu_plan = plan_b0_batch_smoke(
        manifest,
        output_root=tmp_path,
        device="cpu",
        dtype="float64",
        source_commit=SOURCE_COMMIT,
        max_cells=1,
    )
    cell_id = cpu_plan.selected_cell_ids[0]
    _write_attempt(
        tmp_path,
        cell_id=cell_id,
        manifest_digest=digest,
        device="cpu",
        dtype="float64",
        terminal="completed",
    )

    rocm_plan = plan_b0_batch_smoke(
        manifest,
        output_root=tmp_path,
        device="rocm",
        dtype="float32",
        source_commit=SOURCE_COMMIT,
        max_cells=1,
    )
    state = next(cell.state for cell in rocm_plan.cells if cell.cell_id == cell_id)
    assert state == "pending"


def test_invalid_source_commit_and_output_root_are_rejected(tmp_path: Path) -> None:
    with pytest.raises(Stage3BExecutionError, match="source commit"):
        plan_b0_batch_smoke(
            generate_manifest(),
            output_root=tmp_path,
            device="cpu",
            dtype="float64",
            source_commit="dirty",
        )

    with pytest.raises(Stage3BExecutionError, match="under /tmp"):
        plan_b0_batch_smoke(
            generate_manifest(),
            output_root=Path("/var/tmp/stage3b"),
            device="cpu",
            dtype="float64",
            source_commit=SOURCE_COMMIT,
        )


def test_resume_recovers_stale_lane_lock(tmp_path: Path) -> None:
    lock = tmp_path / "batch" / "locks" / "cpu-float64.lock"
    lock.parent.mkdir(parents=True)
    lock.write_text(
        json.dumps({"pid": 999_999_999, "hostname": __import__("socket").gethostname()}),
        encoding="utf-8",
    )

    def fake_runner(
        manifest: Mapping[str, object],
        *,
        output_root: Path,
        cell_id: str,
        device: str,
        dtype: str,
        torch2pc_dir: Path,
        source_commit: str,
        image_id: str | None = None,
    ) -> dict[str, object]:
        del manifest, output_root, device, dtype, torch2pc_dir, source_commit, image_id
        return {
            "attempt_id": f"attempt-{cell_id}",
            "attempt_directory": f"/tmp/{cell_id}",
        }

    result = execute_b0_batch_smoke(
        generate_manifest(),
        output_root=tmp_path,
        device="cpu",
        dtype="float64",
        source_commit=SOURCE_COMMIT,
        max_cells=1,
        torch2pc_dir=Path("/tmp/torch2pc"),
        resume=True,
        runner=fake_runner,
    )

    assert result["status"] == "batch_smoke_passed"
    assert not lock.exists()
