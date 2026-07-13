from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest
import torch
from torch import Tensor, nn

from torch2pc_thesis.profiling import Stage3ProfilingError
from torch2pc_thesis.stage3b_b0_integration import (
    B0GateConfig,
    B0GateReport,
    MethodName,
    flatten_output_tensors,
    run_b0_non_perturbation_gate,
    torch2pc_method_label,
)


def _model() -> nn.Sequential:
    return nn.Sequential(nn.Linear(4, 6), nn.Tanh(), nn.Linear(6, 3)).to(
        dtype=torch.float64
    )


def _optimizer_factory(model: nn.Module) -> torch.optim.Optimizer:
    return torch.optim.SGD(model.parameters(), lr=0.05, momentum=0.1)


def _fake_pc_infer(
    model: nn.Module,
    loss_fn: nn.Module,
    inputs: Tensor,
    targets: Tensor,
    method: str,
    *,
    eta: float,
    n: int,
) -> tuple[list[Tensor], Tensor, dict[str, Any]]:
    del method
    predictions = model(inputs)
    loss = loss_fn(predictions, targets)
    loss.backward()
    beliefs = [inputs + eta * 0.0, predictions]
    return beliefs, loss, {"prediction_error": predictions.detach(), "steps": n}


def _config(method: MethodName = "fixedpred") -> B0GateConfig:
    return B0GateConfig(
        method=method,
        torch2pc_method=torch2pc_method_label(method),
        eta=0.1,
        inference_steps=3,
        device=torch.device("cpu"),
        dtype=torch.float64,
    )


def _batch() -> tuple[Tensor, Tensor]:
    torch.manual_seed(42)
    return (
        torch.randn(8, 4, dtype=torch.float64),
        torch.randint(0, 3, (8,)),
    )


def test_method_label_maps_supported_methods() -> None:
    assert torch2pc_method_label("fixedpred") == "FixedPred"
    assert torch2pc_method_label("STRICT") == "Strict"


def test_method_label_rejects_unknown_method() -> None:
    with pytest.raises(Stage3ProfilingError, match="unsupported B0 method"):
        torch2pc_method_label("exact")


def test_config_rejects_mismatched_torch2pc_label() -> None:
    with pytest.raises(Stage3ProfilingError, match="does not match"):
        B0GateConfig(
            method="fixedpred",
            torch2pc_method="Strict",
            eta=0.1,
            inference_steps=3,
            device=torch.device("cpu"),
            dtype=torch.float64,
        )


def test_flatten_output_tensors_captures_nested_tensor_paths() -> None:
    output = (
        [torch.tensor([1.0]), torch.tensor([2.0])],
        torch.tensor(3.0),
        {"error": torch.tensor([4.0]), "metadata": "ignored"},
    )
    tensors = flatten_output_tensors(output)
    assert set(tensors) == {
        "pc_output[0][0]",
        "pc_output[0][1]",
        "pc_output[1]",
        "pc_output[2].error",
    }


def test_flatten_output_tensors_rejects_tensor_free_output() -> None:
    with pytest.raises(Stage3ProfilingError, match="did not expose any tensors"):
        flatten_output_tensors(("no", {"tensor": None}))


def test_gate_passes_for_real_backward_and_optimizer_step() -> None:
    inputs, targets = _batch()
    report = run_b0_non_perturbation_gate(
        model=_model(),
        optimizer_factory=_optimizer_factory,
        loss_fn=nn.CrossEntropyLoss(),
        inputs=inputs,
        targets=targets,
        pc_infer=_fake_pc_infer,
        config=_config(),
    )
    assert report.passed is True
    assert report.configured_inference_steps == 3
    assert len(report.comparisons) > 0
    assert report.measurement.host_time_us >= 0.0


def test_gate_preserves_input_model_state() -> None:
    inputs, targets = _batch()
    model = _model()
    before = deepcopy(model.state_dict())
    run_b0_non_perturbation_gate(
        model=model,
        optimizer_factory=_optimizer_factory,
        loss_fn=nn.CrossEntropyLoss(),
        inputs=inputs,
        targets=targets,
        pc_infer=_fake_pc_infer,
        config=_config("strict"),
    )
    for name, tensor in model.state_dict().items():
        assert torch.equal(tensor, before[name])


def test_gate_restores_rng_for_stochastic_model() -> None:
    inputs, targets = _batch()
    model = nn.Sequential(
        nn.Linear(4, 6),
        nn.Dropout(p=0.5),
        nn.Linear(6, 3),
    ).to(dtype=torch.float64)
    torch.manual_seed(7)
    report = run_b0_non_perturbation_gate(
        model=model,
        optimizer_factory=_optimizer_factory,
        loss_fn=nn.CrossEntropyLoss(),
        inputs=inputs,
        targets=targets,
        pc_infer=_fake_pc_infer,
        config=_config(),
    )
    assert report.passed is True


def test_gate_detects_instrumented_trajectory_change() -> None:
    inputs, targets = _batch()
    calls = 0

    def drifting_pc_infer(
        model: nn.Module,
        loss_fn: nn.Module,
        batch_inputs: Tensor,
        batch_targets: Tensor,
        method: str,
        *,
        eta: float,
        n: int,
    ) -> tuple[list[Tensor], Tensor]:
        nonlocal calls
        calls += 1
        predictions = model(batch_inputs)
        if calls == 2:
            predictions = predictions + 0.25
        loss = loss_fn(predictions, batch_targets)
        loss.backward()
        del method, eta, n
        return [predictions], loss

    with pytest.raises(Stage3ProfilingError, match="non-perturbation gate failed"):
        run_b0_non_perturbation_gate(
            model=_model(),
            optimizer_factory=_optimizer_factory,
            loss_fn=nn.CrossEntropyLoss(),
            inputs=inputs,
            targets=targets,
            pc_infer=drifting_pc_infer,
            config=_config(),
        )


def test_gate_rejects_invalid_pc_infer_output() -> None:
    inputs, targets = _batch()

    def invalid_pc_infer(*args: Any, **kwargs: Any) -> tuple[str]:
        del args, kwargs
        return ("invalid",)

    with pytest.raises(Stage3ProfilingError, match="unexpected structure"):
        run_b0_non_perturbation_gate(
            model=_model(),
            optimizer_factory=_optimizer_factory,
            loss_fn=nn.CrossEntropyLoss(),
            inputs=inputs,
            targets=targets,
            pc_infer=invalid_pc_infer,
            config=_config(),
        )


def test_report_marks_composite_gate_as_non_evidence() -> None:
    inputs, targets = _batch()
    report: B0GateReport = run_b0_non_perturbation_gate(
        model=_model(),
        optimizer_factory=_optimizer_factory,
        loss_fn=nn.CrossEntropyLoss(),
        inputs=inputs,
        targets=targets,
        pc_infer=_fake_pc_infer,
        config=_config(),
    )
    record = report.to_record()
    assert record["evidence"] is False
    assert record["internal_region_attribution_ready"] is False
    assert record["full_preregistered_gate_complete"] is False
    assert record["actual_inference_step_count_observed"] is False
    assert (
        record["returned_tensor_coverage"]
        == "all_tensors_exposed_by_pcinfer_return"
    )
    assert record["measurement_scope"] == "pcinfer_composite_gate_only"
    assert record["observed_tensor_gate_passed"] is True
    assert record["passed"] is True
