from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path

import pytest

from torch2pc_thesis.stage3b_execution import (
    STAGE3B_CAMPAIGN_ID,
    Stage3BExecutionError,
)
from torch2pc_thesis.stage3b_matched_profiling import (
    MATCHED_PROFILING_MANIFEST_ID,
    MATCHED_PROFILING_REQUEST_ID,
    MATCHED_PROFILING_SCHEMA_VERSION,
)
from torch2pc_thesis.stage3b_matched_runner import (
    CANDIDATE_ADAPTERS,
    MATCHED_RUNNER_DISPOSITION,
    MATCHED_RUNNER_EXPLICITLY_CLOSED,
    MATCHED_RUNNER_STATE_RESET_POLICY,
    MatchedRunnerError,
    adapter_for_candidate,
    build_matched_runner_plan,
    candidate_ids,
    resolve_candidate_loader,
    run_mocked_block_dispatch,
    validate_runner_plan,
)


def _digest(value: object) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _cells() -> list[dict[str, object]]:
    cells: list[dict[str, object]] = []
    candidate_rotations = (
        (
            "stage2_baseline",
            "isolated_layer_vjp",
            "composite_vjp",
        ),
        (
            "stage2_baseline",
            "composite_vjp",
            "isolated_layer_vjp",
        ),
        (
            "isolated_layer_vjp",
            "stage2_baseline",
            "composite_vjp",
        ),
        (
            "isolated_layer_vjp",
            "composite_vjp",
            "stage2_baseline",
        ),
        (
            "composite_vjp",
            "stage2_baseline",
            "isolated_layer_vjp",
        ),
        (
            "composite_vjp",
            "isolated_layer_vjp",
            "stage2_baseline",
        ),
    )
    for block_order in range(96):
        method = "fixedpred" if block_order < 48 else "strict"
        block_id = f"block-{block_order:03d}"
        method_block_order = block_order if method == "fixedpred" else block_order - 48
        rotation = candidate_rotations[
            method_block_order % len(candidate_rotations)
        ]
        for candidate_order, candidate_id in enumerate(rotation):
            cells.append(
                {
                    "cell_id": f"cell-{block_order:03d}-{candidate_order}",
                    "block_id": block_id,
                    "block_order": block_order,
                    "candidate_order": candidate_order,
                    "candidate_id": candidate_id,
                    "candidate_gate_status": "equivalence_gate_passed",
                    "matched_profiling_eligible": True,
                    "method": method,
                    "depth": 4,
                    "width": 64,
                    "batch_size": 64,
                    "model_seed": 70,
                }
            )
    return cells


def _manifest() -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": MATCHED_PROFILING_SCHEMA_VERSION,
        "manifest_id": MATCHED_PROFILING_MANIFEST_ID,
        "campaign_id": STAGE3B_CAMPAIGN_ID,
        "status": "scientific_admission_open_execution_not_authorized",
        "evidence": False,
        "execution_performed": False,
        "test_dataset_access": False,
        "full_stage3b_campaign_complete": False,
        "selected_cell_count": 288,
        "execution_policy": {
            "scientific_admission": "open",
            "runtime_authorization": "not_issued",
            "measurements_allowed": False,
            "candidate_aware_runner_required": True,
            "rocm_float32_primary_lane_required": True,
            "temporary_output_only_until_runtime_freeze": True,
            "committed_measurements_present": False,
        },
        "future_policy_boundary": {
            "ex_if0_open": False,
            "estimator_present": False,
            "ecz_active": False,
            "qwake_pc_active": False,
            "controller_actions_present": False,
            "offline_policy_selection_present": False,
        },
        "cells": _cells(),
    }
    return {**payload, "manifest_digest": _digest(payload)}


def _request(manifest: Mapping[str, object]) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": MATCHED_PROFILING_SCHEMA_VERSION,
        "request_id": MATCHED_PROFILING_REQUEST_ID,
        "campaign_id": STAGE3B_CAMPAIGN_ID,
        "status": "scientific_admission_open_execution_not_authorized",
        "evidence": False,
        "execution_performed": False,
        "test_dataset_access": False,
        "full_stage3b_campaign_complete": False,
        "scientific_admission": "open",
        "runtime_authorization": "not_issued",
        "measurements_allowed": False,
        "source_artifacts": {
            "matched_manifest": {
                "manifest_digest": manifest["manifest_digest"],
                "selected_cell_count": manifest["selected_cell_count"],
            }
        },
        "admitted_candidates": [
            "stage2_baseline",
            "isolated_layer_vjp",
            "composite_vjp",
        ],
        "explicitly_closed": sorted(MATCHED_RUNNER_EXPLICITLY_CLOSED),
    }
    return {**payload, "request_digest": _digest(payload)}


def _plan(tmp_path: Path):
    manifest = _manifest()
    request = _request(manifest)
    return build_matched_runner_plan(
        manifest,
        request,
        output_root=Path("/tmp") / tmp_path.name,
        verify_dispatch=False,
    )


def test_candidate_adapters_cover_exact_admitted_set() -> None:
    assert tuple(CANDIDATE_ADAPTERS) == (
        "stage2_baseline",
        "isolated_layer_vjp",
        "composite_vjp",
    )
    assert adapter_for_candidate("isolated_layer_vjp").loader_name == (
        "load_b1_pc_infer"
    )
    assert adapter_for_candidate("composite_vjp").loader_name == "load_b2_pc_infer"


def test_candidate_loader_symbols_are_callable() -> None:
    for candidate_id in CANDIDATE_ADAPTERS:
        assert callable(resolve_candidate_loader(candidate_id))


def test_plan_preserves_288_cell_order_and_remains_blocked(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    record = plan.to_record()
    validate_runner_plan(record)

    assert len(plan.cells) == 288
    assert [cell.plan_index for cell in plan.cells] == list(range(288))
    assert {cell.disposition for cell in plan.cells} == {
        MATCHED_RUNNER_DISPOSITION
    }
    assert record["runtime_authorization"] == "not_issued"
    assert record["measurements_allowed"] is False
    assert record["execution_performed"] is False
    assert record["state_reset_policy"] == MATCHED_RUNNER_STATE_RESET_POLICY
    assert record["summary"] == {MATCHED_RUNNER_DISPOSITION: 288}


def test_plan_maps_method_labels(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    fixedpred = next(cell for cell in plan.cells if cell.method == "fixedpred")
    strict = next(cell for cell in plan.cells if cell.method == "strict")
    assert fixedpred.method_label == "FixedPred"
    assert strict.method_label == "Strict"


def test_plan_rejects_request_manifest_digest_mismatch(tmp_path: Path) -> None:
    manifest = _manifest()
    request = _request(manifest)
    source_artifacts = request["source_artifacts"]
    assert isinstance(source_artifacts, dict)
    matched = source_artifacts["matched_manifest"]
    assert isinstance(matched, dict)
    matched["manifest_digest"] = "0" * 64
    payload = dict(request)
    payload.pop("request_digest")
    request["request_digest"] = _digest(payload)

    with pytest.raises(MatchedRunnerError, match="does not reference"):
        build_matched_runner_plan(
            manifest,
            request,
            output_root=Path("/tmp") / tmp_path.name,
            verify_dispatch=False,
        )


def test_plan_rejects_opened_future_boundary(tmp_path: Path) -> None:
    manifest = _manifest()
    future = manifest["future_policy_boundary"]
    assert isinstance(future, dict)
    future["ecz_active"] = True
    payload = dict(manifest)
    payload.pop("manifest_digest")
    manifest["manifest_digest"] = _digest(payload)
    request = _request(manifest)

    with pytest.raises(MatchedRunnerError, match="changed or opened"):
        build_matched_runner_plan(
            manifest,
            request,
            output_root=Path("/tmp") / tmp_path.name,
            verify_dispatch=False,
        )


def test_plan_rejects_non_temporary_output_root() -> None:
    manifest = _manifest()
    request = _request(manifest)
    with pytest.raises(Stage3BExecutionError, match="under /tmp"):
        build_matched_runner_plan(
            manifest,
            request,
            output_root=Path("/var/tmp/torch2pc-stage3b-profiling"),
            verify_dispatch=False,
        )


def test_mocked_block_restores_state_and_rng_before_each_candidate(
    tmp_path: Path,
) -> None:
    plan = _plan(tmp_path)
    first_block = plan.cells[0].block_id
    state_restores: list[object] = []
    rng_restores: list[object] = []
    executions: list[str] = []

    def executor(cell, adapter):
        executions.append(cell.candidate_id)
        return {"adapter": adapter.execution_role}

    result = run_mocked_block_dispatch(
        plan,
        block_id=first_block,
        state_snapshot="state-0",
        rng_snapshot="rng-0",
        restore_state=state_restores.append,
        restore_rng=rng_restores.append,
        executor=executor,
    )

    block_cells = tuple(cell for cell in plan.cells if cell.block_id == first_block)
    assert state_restores == ["state-0"] * 3
    assert rng_restores == ["rng-0"] * 3
    assert executions == list(candidate_ids(block_cells))
    assert result["execution_performed"] is False
    assert result["measurements_recorded"] is False
    assert result["evidence"] is False
    assert result["state_restore_count"] == 3
    assert result["rng_restore_count"] == 3


def test_mocked_block_rejects_measurement_like_payload(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    with pytest.raises(MatchedRunnerError, match="measurement-like"):
        run_mocked_block_dispatch(
            plan,
            block_id=plan.cells[0].block_id,
            state_snapshot=object(),
            rng_snapshot=object(),
            restore_state=lambda _snapshot: None,
            restore_rng=lambda _snapshot: None,
            executor=lambda _cell, _adapter: {"timing": 1.0},
        )


def test_mocked_block_rejects_unknown_block(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    with pytest.raises(MatchedRunnerError, match="unknown or incomplete"):
        run_mocked_block_dispatch(
            plan,
            block_id="missing-block",
            state_snapshot=object(),
            rng_snapshot=object(),
            restore_state=lambda _snapshot: None,
            restore_rng=lambda _snapshot: None,
            executor=lambda _cell, _adapter: {},
        )
