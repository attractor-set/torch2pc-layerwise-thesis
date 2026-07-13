from __future__ import annotations

from copy import deepcopy

import pytest

from torch2pc_thesis.stage3 import (
    Stage3DesignError,
    build_stage3_design_plan,
    load_stage3_design,
    stage3_readiness_report,
    validate_stage3_design,
)


def test_stage3_design_is_valid_and_preserves_provenance_distinction() -> None:
    design = load_stage3_design()
    assert design["baseline"]["stage2_execution_source"] != design["baseline"][
        "stage2_publication_state"
    ]
    assert design["campaign"]["stage1_stage2_immutable"] is True


def test_stage3_plan_is_validation_only_and_deterministic() -> None:
    design = load_stage3_design()
    first = build_stage3_design_plan(design)
    second = build_stage3_design_plan(design)
    assert first == second
    assert first["status"] == "design_only_not_executable"
    assert first["test_access"] is False
    assert first["profiling_planned_cells"] == 288
    assert first["pilot_planned_cells"] == 48
    assert all(cell["test_access"] is False for cell in first["pilot_cells"])


def test_periodic_refresh_is_planned_only_for_strict() -> None:
    plan = build_stage3_design_plan(load_stage3_design())
    cells = [
        cell
        for cell in plan["pilot_cells"]
        if cell["candidate_id"] == "periodic_vjp_refresh"
    ]
    assert len(cells) == 12
    assert {cell["method"] for cell in cells} == {"strict"}
    assert {cell["parameters"]["refresh_interval"] for cell in cells} == {1, 2, 5, 20}


def test_adaptive_stopping_variants_are_explicit_and_method_bounded() -> None:
    plan = build_stage3_design_plan(load_stage3_design())
    cells = [
        cell for cell in plan["pilot_cells"] if cell["candidate_id"] == "adaptive_stopping"
    ]
    assert len(cells) == 18
    assert {cell["variant_id"] for cell in cells} == {
        "tolerance_1e-2",
        "tolerance_5e-3",
        "tolerance_1e-3",
    }
    assert {
        cell["parameters"]["maximum_steps"]
        for cell in cells
        if cell["method"] == "fixedpred"
    } == {10}
    assert {
        cell["parameters"]["maximum_steps"]
        for cell in cells
        if cell["method"] == "strict"
    } == {20}


def test_profiling_plan_is_fully_materialized_and_test_free() -> None:
    plan = build_stage3_design_plan(load_stage3_design())
    assert len(plan["profiling_cells"]) == 288
    assert plan["final_maximum_cells"] == 80
    assert all(cell["test_access"] is False for cell in plan["profiling_cells"])


def test_implementation_preserving_candidate_requires_equivalence_gate() -> None:
    design = deepcopy(load_stage3_design())
    candidate = next(
        value for value in design["candidates"] if value["id"] == "isolated_layer_vjp"
    )
    candidate["equivalence_gate"] = False
    with pytest.raises(Stage3DesignError, match="equivalence_gate"):
        validate_stage3_design(design)


def test_final_template_cannot_enable_test_before_freeze() -> None:
    design = deepcopy(load_stage3_design())
    design["phases"]["final_template"]["test_access"] = True
    with pytest.raises(Stage3DesignError, match="must not enable test access"):
        validate_stage3_design(design)


def test_stage3_readiness_is_implementation_ready_but_execution_blocked() -> None:
    report = stage3_readiness_report()
    assert report["status"] == "ready_for_stage3_implementation"
    assert report["execution_status"] == "blocked_until_candidates_and_freeze"
    assert report["missing_files"] == []
    assert report["blockers"]
