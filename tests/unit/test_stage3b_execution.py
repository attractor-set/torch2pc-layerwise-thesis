from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

from torch2pc_thesis.stage3b_execution import (
    METHOD_CANDIDATES,
    STAGE3B_MANIFEST_RELATIVE_PATH,
    Stage3BExecutionError,
    atomic_write_json,
    generate_manifest,
    load_manifest,
    plan_dry_run,
    validate_manifest,
    validated_plan_output_path,
    validated_temporary_output_root,
)


def test_manifest_contains_exact_preregistered_matrix() -> None:
    manifest = generate_manifest()
    cells = manifest["cells"]
    assert isinstance(cells, list)
    assert len(cells) == 336
    candidate_counts = Counter(cell["candidate_id"] for cell in cells)
    assert candidate_counts == {
        "stage2_baseline": 96,
        "fixedpred_finite_step_control": 48,
        "isolated_layer_vjp": 96,
        "composite_vjp": 96,
    }
    method_counts = Counter(cell["method"] for cell in cells)
    assert method_counts == {"fixedpred": 192, "strict": 144}


def test_a0_is_fixedpred_only() -> None:
    cells = generate_manifest()["cells"]
    assert isinstance(cells, list)
    methods = {
        cell["method"]
        for cell in cells
        if cell["candidate_id"] == "fixedpred_finite_step_control"
    }
    assert methods == {"fixedpred"}


def test_cell_and_block_identifiers_are_unique() -> None:
    cells = generate_manifest()["cells"]
    assert isinstance(cells, list)
    cell_ids = [cell["cell_id"] for cell in cells]
    block_ids = {cell["block_id"] for cell in cells}
    assert len(set(cell_ids)) == 336
    assert len(block_ids) == 96


def test_manifest_generation_is_deterministic() -> None:
    assert generate_manifest() == generate_manifest()


def test_candidate_order_is_exactly_counterbalanced() -> None:
    cells = generate_manifest()["cells"]
    assert isinstance(cells, list)
    for method, candidates in METHOD_CANDIDATES.items():
        method_cells = [cell for cell in cells if cell["method"] == method]
        counts = Counter(
            (cell["candidate_id"], cell["candidate_order"])
            for cell in method_cells
        )
        expected = 48 // len(candidates)
        for candidate in candidates:
            for position in range(len(candidates)):
                assert counts[(candidate, position)] == expected


def test_manifest_digest_detects_mutation() -> None:
    manifest = generate_manifest()
    manifest["status"] = "mutated"
    with pytest.raises(Stage3BExecutionError, match="manifest_digest"):
        validate_manifest(manifest)


def test_committed_manifest_matches_generator() -> None:
    repository_root = Path(__file__).resolve().parents[2]
    committed = load_manifest(repository_root / STAGE3B_MANIFEST_RELATIVE_PATH)
    assert committed == generate_manifest()


def test_output_root_is_restricted_to_tmp(tmp_path: Path) -> None:
    assert validated_temporary_output_root(tmp_path) == tmp_path.resolve()
    with pytest.raises(Stage3BExecutionError, match="under /tmp"):
        validated_temporary_output_root(Path("/var/tmp/stage3b"))




def test_plan_output_must_stay_under_output_root(tmp_path: Path) -> None:
    inside = tmp_path / "plans" / "dry-run.json"
    assert validated_plan_output_path(inside, output_root=tmp_path) == inside.resolve()
    with pytest.raises(Stage3BExecutionError, match="under output_root"):
        validated_plan_output_path(
            Path("/tmp/other-stage3b/plan.json"), output_root=tmp_path
        )


def test_empty_dry_run_separates_b0_smoke_from_blocked_candidates(
    tmp_path: Path,
) -> None:
    plan = plan_dry_run(generate_manifest(), output_root=tmp_path)
    assert plan.selected_cell_count == 336
    assert plan.summary == {
        "pending_smoke": 96,
        "blocked_candidate_gate": 240,
    }
    assert plan.to_record()["execution_performed"] is False
    assert plan.to_record()["evidence"] is False


def test_completed_b0_cell_is_skipped(tmp_path: Path) -> None:
    manifest = generate_manifest()
    cells = manifest["cells"]
    assert isinstance(cells, list)
    cell = next(cell for cell in cells if cell["candidate_id"] == "stage2_baseline")
    status_path = tmp_path / "cells" / cell["cell_id"] / "status.json"
    atomic_write_json(
        status_path,
        {
            "cell_id": cell["cell_id"],
            "manifest_digest": manifest["manifest_digest"],
            "status": "completed",
        },
    )
    plan = plan_dry_run(
        manifest,
        output_root=tmp_path,
        selected_cell_ids=[cell["cell_id"]],
    )
    assert plan.summary == {"skip_completed": 1}


def test_failed_b0_cell_is_marked_for_retry(tmp_path: Path) -> None:
    manifest = generate_manifest()
    cells = manifest["cells"]
    assert isinstance(cells, list)
    cell = next(cell for cell in cells if cell["candidate_id"] == "stage2_baseline")
    status_path = tmp_path / "cells" / cell["cell_id"] / "status.json"
    atomic_write_json(
        status_path,
        {
            "cell_id": cell["cell_id"],
            "manifest_digest": manifest["manifest_digest"],
            "status": "failed",
        },
    )
    plan = plan_dry_run(
        manifest,
        output_root=tmp_path,
        selected_cell_ids=[cell["cell_id"]],
    )
    assert plan.summary == {"retry_failed": 1}


def test_mismatched_status_is_incomplete(tmp_path: Path) -> None:
    manifest = generate_manifest()
    cells = manifest["cells"]
    assert isinstance(cells, list)
    cell = next(cell for cell in cells if cell["candidate_id"] == "stage2_baseline")
    status_path = tmp_path / "cells" / cell["cell_id"] / "status.json"
    atomic_write_json(
        status_path,
        {
            "cell_id": "other-cell",
            "manifest_digest": manifest["manifest_digest"],
            "status": "completed",
        },
    )
    plan = plan_dry_run(
        manifest,
        output_root=tmp_path,
        selected_cell_ids=[cell["cell_id"]],
    )
    assert plan.summary == {"resume_incomplete": 1}


def test_unknown_selected_cell_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(Stage3BExecutionError, match="unknown selected"):
        plan_dry_run(
            generate_manifest(),
            output_root=tmp_path,
            selected_cell_ids=["unknown-cell"],
        )


def test_atomic_write_json_replaces_destination(tmp_path: Path) -> None:
    destination = tmp_path / "record.json"
    atomic_write_json(destination, {"value": 1})
    atomic_write_json(destination, {"value": 2})
    assert json.loads(destination.read_text(encoding="utf-8")) == {"value": 2}
    assert list(tmp_path.glob("*.tmp")) == []
