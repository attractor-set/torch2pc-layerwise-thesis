from __future__ import annotations

from scripts.generate_final_execution_plan import build_final_execution_plan


def _base() -> dict:
    return {
        "statistics": {
            "final_seeds": [0, 1, 2],
        }
    }


def _final() -> dict:
    return {
        "selection": {
            "execution_order": "deterministic_hash_counterbalance",
            "execution_order_seed": 20260713,
            "seeds": [0, 1, 2],
            "datasets": ["FashionMNIST", "MNIST"],
            "models": ["lenet_classic"],
            "methods": ["bp", "exact", "fixedpred", "strict"],
        }
    }


def _lock() -> dict:
    return {
        "image_source_git_commit": "a" * 40,
        "torch2pc_commit": "b" * 40,
        "config_sha256": "c" * 64,
    }


def test_final_plan_contains_every_cell_once(monkeypatch) -> None:
    monkeypatch.setattr(
        "scripts.generate_final_execution_plan._method_parameters",
        lambda method: {
            "eta": 0.1 if method in {"fixedpred", "strict"} else None,
            "inference_steps": 10 if method in {"fixedpred", "strict"} else None,
        },
    )
    plan = build_final_execution_plan(
        _base(),
        _final(),
        _lock(),
        environment_lock_sha256="d" * 64,
    )
    assert plan["planned_cells"] == 24
    identities = {
        (
            cell["dataset"],
            cell["model"],
            cell["model_seed"],
            cell["method"],
        )
        for cell in plan["cells"]
    }
    assert len(identities) == 24
    assert plan["environment_lock_sha256"] == "d" * 64


def test_final_plan_is_deterministic_and_counterbalanced(monkeypatch) -> None:
    monkeypatch.setattr(
        "scripts.generate_final_execution_plan._method_parameters",
        lambda method: {"eta": None, "inference_steps": None},
    )
    first = build_final_execution_plan(_base(), _final(), _lock(), environment_lock_sha256="d" * 64)
    second = build_final_execution_plan(
        _base(), _final(), _lock(), environment_lock_sha256="d" * 64
    )
    first_orders = [
        tuple(
            cell["method"]
            for cell in first["cells"]
            if cell["dataset"] == "FashionMNIST" and cell["model_seed"] == seed
        )
        for seed in [0, 1, 2]
    ]
    second_orders = [
        tuple(
            cell["method"]
            for cell in second["cells"]
            if cell["dataset"] == "FashionMNIST" and cell["model_seed"] == seed
        )
        for seed in [0, 1, 2]
    ]
    assert first_orders == second_orders
    assert len(set(first_orders)) > 1


def test_stage_2_plan_preserves_the_same_matrix(monkeypatch) -> None:
    monkeypatch.setattr(
        "scripts.generate_final_execution_plan._method_parameters",
        lambda method: {"eta": None, "inference_steps": None},
    )
    plan = build_final_execution_plan(
        _base(),
        _final(),
        _lock(),
        environment_lock_sha256="d" * 64,
        stage="final_stage_2",
        test_access="once_per_completed_run_after_stage_2_freeze",
    )
    assert plan["stage"] == "final_stage_2"
    assert plan["planned_cells"] == 24
    assert plan["execution_order_seed"] == 20260713
