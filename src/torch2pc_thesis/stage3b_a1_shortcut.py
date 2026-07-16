from __future__ import annotations

import copy
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

import pandas as pd
import torch
import torch.nn as nn

from torch2pc_thesis.stage3b_a1_controls import (
    EquivalenceThresholds,
    ObserverMode,
    TensorComparison,
    compare_tensor_maps,
)

OptimizerFactory = Callable[[Iterable[nn.Parameter]], torch.optim.Optimizer]
JsonScalar = bool | int | float | str | None


@dataclass(frozen=True)
class JointVjpDiagnostics:
    """Structural diagnostics for the opt-in reduced shortcut."""

    top_level_layers: int
    joint_vjp_calls: int
    parameterized_layers: int
    parameter_components: int
    graph_islands: int

    @property
    def one_call_per_layer(self) -> bool:
        return self.joint_vjp_calls == self.top_level_layers

    def to_dict(self) -> dict[str, int | bool]:
        return {
            "top_level_layers": self.top_level_layers,
            "joint_vjp_calls": self.joint_vjp_calls,
            "parameterized_layers": self.parameterized_layers,
            "parameter_components": self.parameter_components,
            "graph_islands": self.graph_islands,
            "one_call_per_layer": self.one_call_per_layer,
        }


@dataclass(frozen=True)
class EqS1Result:
    """BP/reduced-shortcut endpoint equivalence result for EQ-S1."""

    control_id: str
    seed: int
    observer_mode: ObserverMode
    gradient_records: tuple[TensorComparison, ...]
    parameter_records: tuple[TensorComparison, ...]
    optimizer_tensor_records: tuple[TensorComparison, ...]
    optimizer_scalar_state_equal: bool
    shortcut_diagnostics: JointVjpDiagnostics

    @property
    def gradient_passed(self) -> bool:
        return bool(self.gradient_records) and all(
            item.passed for item in self.gradient_records
        )

    @property
    def parameter_step_passed(self) -> bool:
        return bool(self.parameter_records) and all(
            item.passed for item in self.parameter_records
        )

    @property
    def optimizer_state_passed(self) -> bool:
        return all(item.passed for item in self.optimizer_tensor_records) and (
            self.optimizer_scalar_state_equal
        )

    @property
    def passed(self) -> bool:
        return (
            self.gradient_passed
            and self.parameter_step_passed
            and self.optimizer_state_passed
            and self.shortcut_diagnostics.one_call_per_layer
        )

    def records_frame(self) -> pd.DataFrame:
        records: list[dict[str, Any]] = []
        records.extend(
            item.to_record(comparison_kind="endpoint_gradient")
            for item in self.gradient_records
        )
        records.extend(
            item.to_record(comparison_kind="parameter_after_optimizer_step")
            for item in self.parameter_records
        )
        records.extend(
            item.to_record(comparison_kind="optimizer_tensor_state")
            for item in self.optimizer_tensor_records
        )
        return pd.DataFrame.from_records(records)

    def to_summary_dict(self) -> dict[str, Any]:
        return {
            "control_id": self.control_id,
            "seed": self.seed,
            "observer_mode": self.observer_mode.value,
            "gradient_passed": self.gradient_passed,
            "parameter_step_passed": self.parameter_step_passed,
            "optimizer_state_passed": self.optimizer_state_passed,
            "optimizer_scalar_state_equal": self.optimizer_scalar_state_equal,
            "shortcut_diagnostics": self.shortcut_diagnostics.to_dict(),
            "passed": self.passed,
            "gradient_components": len(self.gradient_records),
            "parameter_components": len(self.parameter_records),
            "optimizer_tensor_components": len(self.optimizer_tensor_records),
        }


def reduced_shortcut_backward(
    model: nn.Sequential,
    loss_fn: nn.Module,
    inputs: torch.Tensor,
    targets: torch.Tensor,
) -> tuple[torch.Tensor, JointVjpDiagnostics]:
    """Compute exact chain-rule gradients with one joint VJP per top-level layer.

    Every layer is evaluated on a detached leaf input. Reverse propagation then
    performs exactly one ``torch.autograd.grad`` call for that layer, jointly
    returning its input cotangent and all trainable parameter gradients. The
    last call differentiates the scalar loss directly, so no extra output-loss
    VJP is required.
    """

    if not isinstance(model, nn.Sequential):
        raise TypeError("EQ-S1 reduced shortcut requires a top-level nn.Sequential model")
    if len(model) < 1:
        raise ValueError("EQ-S1 reduced shortcut requires at least one layer")

    model.zero_grad(set_to_none=True)

    layer_inputs: list[torch.Tensor] = []
    layer_outputs: list[torch.Tensor] = []
    layer_parameters: list[tuple[nn.Parameter, ...]] = []

    current = inputs.detach()
    for layer in model:
        layer_input = current.detach().requires_grad_(True)
        layer_output = layer(layer_input)
        if not isinstance(layer_output, torch.Tensor):
            raise TypeError("EQ-S1 requires every top-level layer to return one tensor")
        parameters = tuple(
            parameter for parameter in layer.parameters() if parameter.requires_grad
        )
        layer_inputs.append(layer_input)
        layer_outputs.append(layer_output)
        layer_parameters.append(parameters)
        current = layer_output

    loss = loss_fn(layer_outputs[-1], targets)
    if loss.ndim != 0:
        raise ValueError("EQ-S1 requires a scalar reduced loss")

    accumulated: dict[int, torch.Tensor] = {}
    cotangent: torch.Tensor | None = None
    joint_vjp_calls = 0

    for reverse_index in range(len(model) - 1, -1, -1):
        layer_input = layer_inputs[reverse_index]
        layer_output = layer_outputs[reverse_index]
        parameters = layer_parameters[reverse_index]
        differentiation_inputs: tuple[torch.Tensor, ...] = (
            layer_input,
            *parameters,
        )

        if reverse_index == len(model) - 1:
            gradients = torch.autograd.grad(
                outputs=loss,
                inputs=differentiation_inputs,
                create_graph=False,
                retain_graph=False,
                allow_unused=False,
            )
        else:
            if cotangent is None:
                raise RuntimeError("Missing cotangent before a non-terminal layer VJP")
            gradients = torch.autograd.grad(
                outputs=layer_output,
                inputs=differentiation_inputs,
                grad_outputs=cotangent,
                create_graph=False,
                retain_graph=False,
                allow_unused=False,
            )

        joint_vjp_calls += 1
        cotangent = gradients[0].detach()

        for parameter, gradient in zip(parameters, gradients[1:], strict=True):
            key = id(parameter)
            detached = gradient.detach()
            previous = accumulated.get(key)
            accumulated[key] = detached if previous is None else previous + detached

    trainable = [parameter for parameter in model.parameters() if parameter.requires_grad]
    missing = [parameter for parameter in trainable if id(parameter) not in accumulated]
    if missing:
        raise RuntimeError(
            "Reduced shortcut produced no gradient for "
            f"{len(missing)} trainable parameter components"
        )

    for parameter in trainable:
        parameter.grad = accumulated[id(parameter)].clone()

    diagnostics = JointVjpDiagnostics(
        top_level_layers=len(model),
        joint_vjp_calls=joint_vjp_calls,
        parameterized_layers=sum(bool(parameters) for parameters in layer_parameters),
        parameter_components=len(trainable),
        graph_islands=len(layer_outputs),
    )
    if not diagnostics.one_call_per_layer:
        raise RuntimeError("Reduced shortcut violated the one-joint-VJP-per-layer contract")

    return loss.detach(), diagnostics


def evaluate_eq_s1(
    model: nn.Sequential,
    inputs: torch.Tensor,
    targets: torch.Tensor,
    *,
    torch2pc_dir: str,
    seed: int,
    thresholds: EquivalenceThresholds,
    optimizer_factory: OptimizerFactory,
) -> EqS1Result:
    """Evaluate BP against the opt-in one-joint-VJP-per-layer shortcut."""

    from torch2pc_thesis.pc_methods import backward_for_method
    from torch2pc_thesis.reproducibility import set_global_seed

    set_global_seed(seed, warn_only=False)
    bp_model = copy.deepcopy(model)
    shortcut_model = copy.deepcopy(model)

    cpu_rng = torch.random.get_rng_state()
    cuda_rng = torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None

    bp_model.zero_grad(set_to_none=True)
    backward_for_method(
        bp_model,
        nn.CrossEntropyLoss(),
        inputs,
        targets,
        method="bp",
        torch2pc_dir=torch2pc_dir,
        eta=None,
        inference_steps=None,
    )

    torch.random.set_rng_state(cpu_rng)
    if cuda_rng is not None:
        torch.cuda.set_rng_state_all(cuda_rng)

    _, diagnostics = reduced_shortcut_backward(
        shortcut_model,
        nn.CrossEntropyLoss(),
        inputs,
        targets,
    )

    gradient_records = compare_tensor_maps(
        _named_gradients(bp_model),
        _named_gradients(shortcut_model),
        thresholds,
        prefix="gradient:",
    )

    bp_optimizer = optimizer_factory(bp_model.parameters())
    shortcut_optimizer = optimizer_factory(shortcut_model.parameters())
    bp_optimizer.step()
    shortcut_optimizer.step()

    parameter_records = compare_tensor_maps(
        _named_parameters(bp_model),
        _named_parameters(shortcut_model),
        thresholds,
        prefix="parameter:",
    )

    bp_tensors, bp_scalars = _flatten_optimizer_state(bp_optimizer, bp_model)
    shortcut_tensors, shortcut_scalars = _flatten_optimizer_state(
        shortcut_optimizer,
        shortcut_model,
    )
    optimizer_tensor_records = compare_tensor_maps(
        bp_tensors,
        shortcut_tensors,
        thresholds,
        prefix="optimizer:",
    )

    return EqS1Result(
        control_id="EQ-S1",
        seed=seed,
        observer_mode=ObserverMode.NO_HOOKS,
        gradient_records=gradient_records,
        parameter_records=parameter_records,
        optimizer_tensor_records=optimizer_tensor_records,
        optimizer_scalar_state_equal=bp_scalars == shortcut_scalars,
        shortcut_diagnostics=diagnostics,
    )


def _named_gradients(model: nn.Module) -> dict[str, torch.Tensor]:
    gradients: dict[str, torch.Tensor] = {}
    missing: list[str] = []
    for name, parameter in model.named_parameters():
        if not parameter.requires_grad:
            continue
        if parameter.grad is None:
            missing.append(name)
        else:
            gradients[name] = parameter.grad.detach().clone()
    if missing:
        raise RuntimeError(f"Missing gradients for trainable parameters: {missing}")
    if not gradients:
        raise RuntimeError("No trainable parameter gradients were produced")
    return gradients


def _named_parameters(model: nn.Module) -> dict[str, torch.Tensor]:
    return {
        name: parameter.detach().clone()
        for name, parameter in model.named_parameters()
        if parameter.requires_grad
    }


def _flatten_optimizer_state(
    optimizer: torch.optim.Optimizer,
    model: nn.Module,
) -> tuple[dict[str, torch.Tensor], dict[str, JsonScalar]]:
    names = {id(parameter): name for name, parameter in model.named_parameters()}
    tensors: dict[str, torch.Tensor] = {}
    scalars: dict[str, JsonScalar] = {}

    for group_index, group in enumerate(optimizer.param_groups):
        for key, value in sorted(group.items()):
            if key == "params":
                continue
            path = f"group:{group_index}:{key}"
            if isinstance(value, torch.Tensor):
                tensors[path] = value.detach().clone()
            elif isinstance(value, bool | int | float | str) or value is None:
                scalars[path] = value
            else:
                scalars[path] = repr(value)

    for parameter, state in optimizer.state.items():
        parameter_name = names.get(id(parameter))
        if parameter_name is None:
            raise RuntimeError("Optimizer state references an unknown parameter")
        for key, value in sorted(state.items()):
            path = f"state:{parameter_name}:{key}"
            if isinstance(value, torch.Tensor):
                tensors[path] = value.detach().clone()
            elif isinstance(value, bool | int | float | str) or value is None:
                scalars[path] = value
            else:
                scalars[path] = repr(value)

    return tensors, scalars
