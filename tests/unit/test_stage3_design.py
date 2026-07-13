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
    assert design["campaign"]["design_revision"] == 2


def test_stage3_plan_is_validation_only_and_deterministic() -> None:
    design = load_stage3_design()
    first = build_stage3_design_plan(design)
    second = build_stage3_design_plan(design)
    assert first == second
    assert first["status"] == "design_only_not_executable"
    assert first["test_access"] is False
    assert first["profiling_planned_cells"] == 336
    assert first["pilot_planned_cells"] == 48
    assert first["accelerator_screening_planned_cells"] == 27
    assert all(cell["test_access"] is False for cell in first["pilot_cells"])
    assert all(
        cell["test_access"] is False for cell in first["accelerator_screening_cells"]
    )


def test_periodic_refresh_is_planned_only_for_strict() -> None:
    plan = build_stage3_design_plan(load_stage3_design())
    cells = [
        cell for cell in plan["pilot_cells"] if cell["candidate_id"] == "periodic_vjp_refresh"
    ]
    assert len(cells) == 12
    assert {cell["method"] for cell in cells} == {"strict"}
    assert {cell["parameters"]["refresh_interval"] for cell in cells} == {1, 2, 5, 20}


def test_adaptive_stopping_variants_are_explicit_and_method_bounded() -> None:
    plan = build_stage3_design_plan(load_stage3_design())
    cells = [cell for cell in plan["pilot_cells"] if cell["candidate_id"] == "adaptive_stopping"]
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


def test_finite_step_control_is_fixedpred_only_and_endpoint_scoped() -> None:
    design = load_stage3_design()
    candidate = next(
        value for value in design["candidates"] if value["id"] == "fixedpred_finite_step_control"
    )
    assert candidate["track"] == "exact_shortcut"
    assert candidate["methods"] == ["fixedpred"]
    assert candidate["equivalence_scope"] == "endpoint_gradient"
    plan = build_stage3_design_plan(design)
    cells = [
        cell
        for cell in plan["profiling_cells"]
        if cell["candidate_id"] == "fixedpred_finite_step_control"
    ]
    assert len(cells) == 48
    assert {cell["method"] for cell in cells} == {"fixedpred"}


def test_predict_correct_screening_has_explicit_exact_correction_budgets() -> None:
    plan = build_stage3_design_plan(load_stage3_design())
    cells = plan["accelerator_screening_cells"]
    assert len(cells) == 27
    assert {cell["method"] for cell in cells} == {"strict"}
    for candidate_id in {"predict_correct_initialization", "local_secant_preconditioner"}:
        candidate_cells = [cell for cell in cells if cell["candidate_id"] == candidate_id]
        assert len(candidate_cells) == 12
        assert {cell["parameters"]["exact_correction_steps"] for cell in candidate_cells} == {
            1,
            2,
            3,
            5,
        }
        assert all(cell["parameters"]["fallback_to_strict"] is True for cell in candidate_cells)


def test_deferred_accelerators_are_not_in_executable_design_phases() -> None:
    design = load_stage3_design()
    planned = {
        candidate
        for phase in ("profiling", "pilot", "accelerator_screening")
        for candidate in design["phases"][phase]["candidates"]
    }
    assert "hybrid_feedback_exact_refresh" not in planned
    assert "layer_local_anderson" not in planned
    assert "fixed_random_feedback" not in planned


def test_profiling_plan_is_fully_materialized_and_test_free() -> None:
    plan = build_stage3_design_plan(load_stage3_design())
    assert len(plan["profiling_cells"]) == 336
    assert plan["final_maximum_cells"] == 80
    assert all(cell["test_access"] is False for cell in plan["profiling_cells"])


def test_implementation_preserving_candidate_requires_equivalence_gate() -> None:
    design = deepcopy(load_stage3_design())
    candidate = next(value for value in design["candidates"] if value["id"] == "isolated_layer_vjp")
    candidate["equivalence_gate"] = False
    with pytest.raises(Stage3DesignError, match="equivalence_gate"):
        validate_stage3_design(design)


def test_exact_shortcut_requires_endpoint_scope() -> None:
    design = deepcopy(load_stage3_design())
    candidate = next(
        value for value in design["candidates"] if value["id"] == "fixedpred_finite_step_control"
    )
    candidate["equivalence_scope"] = "full_trajectory"
    with pytest.raises(Stage3DesignError, match="endpoint_gradient"):
        validate_stage3_design(design)


def test_predict_correct_gate_requires_exact_correction_guard() -> None:
    design = deepcopy(load_stage3_design())
    design["gates"]["predict_correct"]["require_at_least_one_exact_correction"] = False
    with pytest.raises(Stage3DesignError, match="at least one exact correction"):
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
    assert report["design_revision"] == 2
    assert report["profiling_planned_cells"] == 336
    assert report["pilot_planned_cells"] == 48
    assert report["accelerator_screening_planned_cells"] == 27
    assert report["missing_files"] == []
    assert report["blockers"]
