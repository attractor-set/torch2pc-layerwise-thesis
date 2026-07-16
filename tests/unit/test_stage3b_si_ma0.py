from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
import torch
from torch import Tensor, nn

from torch2pc_thesis.stage3b_si_ma0 import (
    CONTRACT_ID,
    OBSERVER_MODES,
    NumericalThresholds,
    SIMA0Error,
    compare_mode_results,
    compare_tensors,
    expected_record_counts,
    instrument_strict_pcinfer,
    load_contract,
    materialize_output_error_records,
    materialize_state_update_records,
    run_observer_mode,
    supports_si_ma0_instrumentation,
    validate_event_order,
)


def FwdPassPlus(
    model: nn.Sequential,
    loss_function: nn.Module,
    inputs: Tensor,
    targets: Tensor,
) -> tuple[list[Tensor], Tensor, Tensor]:
    values = [inputs]
    for module in model:
        values.append(module(values[-1]))
    loss = loss_function(values[-1], targets)
    output_error = torch.autograd.grad(loss, values[-1])[0]
    return values, loss, output_error


def StrictPCPredErrs(
    model: nn.Sequential,
    vinit: list[Tensor],
    loss_function: nn.Module,
    targets: Tensor,
    eta: float,
    n: int,
) -> tuple[list[Tensor | None], list[Tensor | None]]:
    if n < 1:
        raise ValueError("n must be positive")
    depth_plus_one = len(model) + 1
    epsilon: list[Tensor | None] = [None] * depth_plus_one
    values: list[Tensor | None] = [
        activation.detach().clone() for activation in vinit
    ]
    for _sweep in range(n):
        current_input = (
            values[-2].detach().requires_grad_(True)  # type: ignore[union-attr]
        )
        current_output = model[-1](current_input)
        loss = loss_function(current_output, targets)
        epsilon[-1] = torch.autograd.grad(
            loss,
            current_output,
            retain_graph=True,
        )[0]
        for layer in reversed(range(1, depth_plus_one - 1)):
            transported = torch.autograd.grad(
                current_output,
                current_input,
                grad_outputs=epsilon[layer + 1],
                retain_graph=False,
            )[0]
            if layer == 1:
                with torch.no_grad():
                    lower_output = model[0](values[0])
                lower_input = None
            else:
                lower_input = (
                    values[layer - 1]  # type: ignore[assignment]
                    .detach()
                    .requires_grad_(True)
                )
                lower_output = model[layer - 1](lower_input)
            epsilon[layer] = lower_output - values[layer]
            update = epsilon[layer] - transported
            values[layer] = values[layer] + eta * update
            current_input = lower_input  # type: ignore[assignment]
            current_output = lower_output
        for layer in range(1, depth_plus_one - 1):
            values[layer] = values[layer].detach()  # type: ignore[union-attr]
            epsilon[layer] = epsilon[layer].detach()  # type: ignore[union-attr]
    return values, epsilon


def SetPCGrads(
    model: nn.Sequential,
    epsilon: list[Tensor | None],
    inputs: Tensor,
    values: list[Tensor | None] | None = None,
) -> None:
    depth_plus_one = len(model) + 1
    if values is None:
        values = [None] * depth_plus_one
        values[0] = inputs
        for layer in range(1, depth_plus_one):
            values[layer] = model[layer - 1](values[layer - 1])
    for layer in range(depth_plus_one - 1):
        parameters = tuple(model[layer].parameters())
        if not parameters:
            continue
        value = values[layer].detach()
        output = model[layer](value)
        gradients = torch.autograd.grad(
            output,
            parameters,
            grad_outputs=epsilon[layer + 1],
            allow_unused=True,
        )
        for parameter, gradient in zip(parameters, gradients, strict=True):
            parameter.grad = gradient


def PCInfer(
    model: nn.Sequential,
    loss_function: nn.Module,
    inputs: Tensor,
    targets: Tensor,
    error_type: str,
    eta: float = 0.1,
    n: int = 20,
    vinit: list[Tensor] | None = None,
) -> tuple[Any, ...]:
    values, loss, output_error = FwdPassPlus(
        model,
        loss_function,
        inputs,
        targets,
    )
    if error_type != "Strict":
        raise ValueError("test PCInfer supports Strict only")
    if vinit is None:
        vinit = values
    beliefs, epsilon = StrictPCPredErrs(
        model,
        vinit,
        loss_function,
        targets,
        eta,
        n,
    )
    SetPCGrads(model, epsilon, inputs, beliefs)
    return values, loss, output_error, beliefs, epsilon


@pytest.fixture
def thresholds() -> NumericalThresholds:
    return NumericalThresholds(
        zero_atol=1e-12,
        max_relative_l2=1e-9,
        max_abs=1e-10,
        min_cosine=0.999999,
    )


@pytest.fixture
def model_state() -> dict[str, Tensor]:
    torch.manual_seed(7)
    model = nn.Sequential(
        nn.Linear(4, 4),
        nn.Tanh(),
        nn.Linear(4, 2),
    ).to(dtype=torch.float64)
    return copy.deepcopy(model.state_dict())


def build_model(state: dict[str, Tensor]) -> nn.Sequential:
    model = nn.Sequential(
        nn.Linear(4, 4),
        nn.Tanh(),
        nn.Linear(4, 2),
    ).to(dtype=torch.float64)
    model.load_state_dict(state)
    return model


def minimal_contract() -> dict[str, Any]:
    return {
        "contract_id": CONTRACT_ID,
        "schema_version": 2,
        "status": "frozen_preregistration_amendment",
        "scope": {
            "model_modules": 6,
            "updated_state_layers_per_sweep": 5,
            "output_error_records_per_sweep": 1,
            "inference_steps": 20,
        },
        "expected_counts": {
            "confirmatory_state_update_events": 3000,
            "confirmatory_output_error_records": 600,
            "confirmatory_diagnostic_records": 3600,
        },
        "reconstruction": {
            "record_scope": "state_update_events_only",
            "output_error_is_not_state_update": True,
        },
    }


def test_load_contract_requires_v2(tmp_path: Path) -> None:
    path = tmp_path / "contract.json"
    path.write_text(
        json.dumps(minimal_contract()),
        encoding="utf-8",
    )
    loaded = load_contract(path)
    assert loaded["contract_id"] == CONTRACT_ID

    invalid = minimal_contract()
    invalid["contract_id"] = "stage3b-si-ma0-v1"
    path.write_text(json.dumps(invalid), encoding="utf-8")
    with pytest.raises(SIMA0Error, match="preregistration v2"):
        load_contract(path)


def test_expected_record_counts_separate_output_errors() -> None:
    assert expected_record_counts(
        model_count=10,
        batch_count=3,
        inference_steps=20,
        updated_state_layers=5,
    ) == {
        "state_update_events": 3000,
        "output_error_records": 600,
        "diagnostic_records": 3600,
        "mode_comparisons": 120,
    }


def test_zero_safe_tensor_comparison(
    thresholds: NumericalThresholds,
) -> None:
    zero = torch.zeros(4, dtype=torch.float64)
    result = compare_tensors(zero, zero.clone(), thresholds)
    assert result.passed
    assert result.cosine is None

    nonzero = zero.clone()
    nonzero[0] = 1.0
    mismatch = compare_tensors(zero, nonzero, thresholds)
    assert not mismatch.passed
    assert mismatch.cosine is None


def test_temporary_instrumentation_restores_original(
    thresholds: NumericalThresholds,
) -> None:
    assert supports_si_ma0_instrumentation(PCInfer)
    original = PCInfer.__globals__["StrictPCPredErrs"]
    from torch2pc_thesis.stage3b_si_ma0 import SIMA0Recorder

    recorder = SIMA0Recorder(
        mode="instrumented_disabled",
        device=torch.device("cpu"),
        thresholds=thresholds,
        metadata={},
    )
    with instrument_strict_pcinfer(PCInfer, recorder=recorder):
        assert PCInfer.__globals__["StrictPCPredErrs"] is not original
    assert PCInfer.__globals__["StrictPCPredErrs"] is original


def test_all_observer_modes_match_reference_and_record_cardinality(
    thresholds: NumericalThresholds,
    model_state: dict[str, Tensor],
) -> None:
    inputs = torch.randn(5, 4, dtype=torch.float64)
    targets = torch.tensor([0, 1, 0, 1, 1])
    loss_function = nn.CrossEntropyLoss()
    metadata = {"model_seed": 0, "batch_id": 0}
    results = {}
    initial_rng = torch.get_rng_state().clone()

    for mode in OBSERVER_MODES:
        torch.set_rng_state(initial_rng)
        results[mode] = run_observer_mode(
            pc_infer=PCInfer,
            model=build_model(model_state),
            loss_function=loss_function,
            inputs=inputs,
            targets=targets,
            eta=0.05,
            inference_steps=3,
            mode=mode,
            thresholds=thresholds,
            metadata=metadata,
        )

    reference = results["no_hooks"]
    for mode in OBSERVER_MODES:
        if mode == "no_hooks":
            continue
        comparison = compare_mode_results(
            reference,
            results[mode],
            thresholds,
            metadata=metadata,
        )
        assert comparison["passed"] is True

    recorder = results["full_attribution"].recorder
    assert recorder is not None
    state_records = materialize_state_update_records(recorder, eta=0.05)
    output_records = materialize_output_error_records(recorder)
    assert len(state_records) == 3 * 2
    assert len(output_records) == 3
    assert all(record["passed"] for record in state_records)
    assert all(record["passed"] for record in output_records)
    validate_event_order(
        state_records,
        output_records,
        inference_steps=3,
        updated_state_layers=2,
    )
    assert recorder.vjp_call_count == 3 * 3
    assert recorder.synchronization_count == 0


def test_output_error_precedes_each_sweep_update(
    thresholds: NumericalThresholds,
    model_state: dict[str, Tensor],
) -> None:
    inputs = torch.randn(2, 4, dtype=torch.float64)
    targets = torch.tensor([0, 1])
    result = run_observer_mode(
        pc_infer=PCInfer,
        model=build_model(model_state),
        loss_function=nn.CrossEntropyLoss(),
        inputs=inputs,
        targets=targets,
        eta=0.05,
        inference_steps=2,
        mode="full_attribution",
        thresholds=thresholds,
        metadata={"model_seed": 0, "batch_id": 0},
    )
    recorder = result.recorder
    assert recorder is not None
    states = materialize_state_update_records(recorder, eta=0.05)
    outputs = materialize_output_error_records(recorder)
    for sweep in range(2):
        output_sequence = next(
            int(row["sequence_index"])
            for row in outputs
            if int(row["sweep_index"]) == sweep
        )
        update_sequences = [
            int(row["sequence_index"])
            for row in states
            if int(row["sweep_index"]) == sweep
        ]
        assert output_sequence < min(update_sequences)
