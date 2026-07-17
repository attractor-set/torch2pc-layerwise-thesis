from __future__ import annotations

from collections.abc import Callable

import torch
import torch.nn as nn

from torch2pc_thesis.stage3b_b1_isolated_vjp import (
    B1SweepSnapshot,
    PcInferOutput,
    TensorState,
    Torch2PCReference,
)

TrajectorySink = Callable[[B1SweepSnapshot], None]


def reference_pc_infer_with_trace(
    reference: Torch2PCReference,
    model: nn.Sequential,
    loss_fn: nn.Module,
    inputs: torch.Tensor,
    targets: torch.Tensor,
    method: str,
    *,
    eta: float,
    inference_steps: int,
    trajectory_sink: TrajectorySink,
) -> PcInferOutput:
    if method not in {"FixedPred", "Strict"}:
        raise ValueError("Reference trace supports only FixedPred and Strict")
    raw_vhat, loss, dldy = reference.FwdPassPlus(model, loss_fn, inputs, targets)
    vhat = _require_tensor_state(raw_vhat, len(model) + 1)
    if method == "FixedPred":
        beliefs, epsilon = _fixedpred_reference_trace(
            model,
            vhat,
            dldy,
            eta=eta,
            inference_steps=inference_steps,
            trajectory_sink=trajectory_sink,
        )
        reference.SetPCGrads(model, epsilon, inputs, vhat)
    else:
        beliefs, epsilon = _strict_reference_trace(
            model,
            vhat,
            loss_fn,
            targets,
            eta=eta,
            inference_steps=inference_steps,
            trajectory_sink=trajectory_sink,
        )
        reference.SetPCGrads(model, epsilon, inputs, beliefs)
    return vhat, loss, dldy, beliefs, epsilon


def _fixedpred_reference_trace(
    model: nn.Sequential,
    vhat: TensorState,
    dldy: torch.Tensor,
    *,
    eta: float,
    inference_steps: int,
    trajectory_sink: TrajectorySink,
) -> tuple[TensorState, TensorState]:
    fixed = [_required(value).detach() for value in vhat]
    local_inputs: list[torch.Tensor] = []
    local_outputs: list[torch.Tensor] = []
    for layer_index, layer in enumerate(model):
        local_input = fixed[layer_index].detach().requires_grad_(True)
        local_inputs.append(local_input)
        local_output = layer(local_input)
        if not isinstance(local_output, torch.Tensor):
            raise TypeError("Reference trace requires tensor-valued layers")
        local_outputs.append(local_output)

    beliefs: TensorState = [value.detach().clone() for value in fixed]
    epsilon: TensorState = [None] * (len(model) + 1)
    epsilon[-1] = dldy.detach()
    _emit(
        method="FixedPred",
        phase="initial",
        sweep_index=-1,
        beliefs=beliefs,
        epsilon=epsilon,
        corrections=[None] * (len(model) + 1),
        sink=trajectory_sink,
    )

    for sweep_index in range(inference_steps):
        corrections: TensorState = [None] * (len(model) + 1)
        retain_graph = sweep_index < inference_steps - 1
        for layer_index in reversed(range(len(model))):
            belief = _required(beliefs[layer_index])
            upper_error = _required(epsilon[layer_index + 1])
            epsilon[layer_index] = fixed[layer_index] - belief
            propagated = torch.autograd.grad(
                local_outputs[layer_index],
                local_inputs[layer_index],
                grad_outputs=upper_error,
                retain_graph=retain_graph,
            )[0]
            correction = eta * (_required(epsilon[layer_index]) - propagated)
            corrections[layer_index] = correction.detach()
            beliefs[layer_index] = belief + correction
        _detach_iterative_state(beliefs, epsilon)
        _emit(
            method="FixedPred",
            phase="after_sweep",
            sweep_index=sweep_index,
            beliefs=beliefs,
            epsilon=epsilon,
            corrections=corrections,
            sink=trajectory_sink,
        )
    return beliefs, epsilon


def _strict_reference_trace(
    model: nn.Sequential,
    vinit: TensorState,
    loss_fn: nn.Module,
    targets: torch.Tensor,
    *,
    eta: float,
    inference_steps: int,
    trajectory_sink: TrajectorySink,
) -> tuple[TensorState, TensorState]:
    beliefs: TensorState = [
        _required(value).detach().clone() for value in vinit
    ]
    epsilon: TensorState = [None] * (len(model) + 1)
    _emit(
        method="Strict",
        phase="initial",
        sweep_index=-1,
        beliefs=beliefs,
        epsilon=epsilon,
        corrections=[None] * (len(model) + 1),
        sink=trajectory_sink,
    )

    for sweep_index in range(inference_steps):
        corrections: TensorState = [None] * (len(model) + 1)
        penultimate = _required(beliefs[-2])
        current_input: torch.Tensor | None = penultimate.detach().requires_grad_(True)
        current_output = model[-1](current_input)
        if not isinstance(current_output, torch.Tensor):
            raise TypeError("Reference trace requires tensor-valued layers")
        loss = loss_fn(current_output, targets)
        epsilon[-1] = torch.autograd.grad(
            loss,
            current_output,
            retain_graph=True,
        )[0]

        for layer_index in reversed(range(1, len(model))):
            upper_error = _required(epsilon[layer_index + 1])
            if current_input is None:
                raise RuntimeError("Reference trace lost the current graph input")
            propagated = torch.autograd.grad(
                current_output,
                current_input,
                grad_outputs=upper_error,
                retain_graph=False,
            )[0]
            lower_belief = _required(beliefs[layer_index - 1])
            belief = _required(beliefs[layer_index])
            if layer_index == 1:
                with torch.no_grad():
                    lower_output = model[0](lower_belief)
                lower_input = None
            else:
                lower_input = lower_belief.detach().requires_grad_(True)
                lower_output = model[layer_index - 1](lower_input)
            if not isinstance(lower_output, torch.Tensor):
                raise TypeError("Reference trace requires tensor-valued layers")
            epsilon[layer_index] = lower_output - belief
            correction = eta * (_required(epsilon[layer_index]) - propagated)
            corrections[layer_index] = correction.detach()
            beliefs[layer_index] = belief + correction
            current_input = lower_input
            current_output = lower_output

        _detach_iterative_state(beliefs, epsilon)
        _emit(
            method="Strict",
            phase="after_sweep",
            sweep_index=sweep_index,
            beliefs=beliefs,
            epsilon=epsilon,
            corrections=corrections,
            sink=trajectory_sink,
        )
    return beliefs, epsilon


def _emit(
    *,
    method: str,
    phase: str,
    sweep_index: int,
    beliefs: TensorState,
    epsilon: TensorState,
    corrections: TensorState,
    sink: TrajectorySink,
) -> None:
    sink(
        B1SweepSnapshot(
            method=method,
            phase=phase,
            sweep_index=sweep_index,
            beliefs=tuple(_clone_optional(value) for value in beliefs),
            prediction_errors=tuple(_clone_optional(value) for value in epsilon),
            state_corrections=tuple(_clone_optional(value) for value in corrections),
        )
    )


def _require_tensor_state(state: object, expected_length: int) -> TensorState:
    if not isinstance(state, list) or len(state) != expected_length:
        raise RuntimeError("Unexpected Torch2PC state structure")
    result: TensorState = []
    for value in state:
        if not torch.is_tensor(value):
            raise RuntimeError("Torch2PC state contains a non-tensor value")
        result.append(value)
    return result


def _required(value: torch.Tensor | None) -> torch.Tensor:
    if value is None:
        raise RuntimeError("Reference trace encountered a missing tensor")
    return value


def _clone_optional(value: torch.Tensor | None) -> torch.Tensor | None:
    return None if value is None else value.detach().clone()


def _detach_iterative_state(beliefs: TensorState, epsilon: TensorState) -> None:
    for layer_index in range(1, len(beliefs) - 1):
        beliefs[layer_index] = _required(beliefs[layer_index]).detach()
        epsilon[layer_index] = _required(epsilon[layer_index]).detach()
