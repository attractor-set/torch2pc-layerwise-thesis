from __future__ import annotations

import copy
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
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
from torch2pc_thesis.stage3b_a1_shortcut import (
    JointVjpDiagnostics,
    reduced_shortcut_backward,
)

OptimizerFactory = Callable[[Iterable[nn.Parameter]], torch.optim.Optimizer]
JsonScalar = bool | int | float | str | None


@dataclass(frozen=True)
class EqS2Result:
    """FixedPred/reduced-shortcut endpoint equivalence result for EQ-S2."""

    control_id: str
    seed: int
    inference_steps: int
    eta: float
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
    def structural_contract_passed(self) -> bool:
        diagnostics = self.shortcut_diagnostics
        return (
            diagnostics.one_call_per_layer
            and diagnostics.graph_islands == diagnostics.top_level_layers
        )

    @property
    def passed(self) -> bool:
        return (
            self.gradient_passed
            and self.parameter_step_passed
            and self.optimizer_state_passed
            and self.structural_contract_passed
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
            "inference_steps": self.inference_steps,
            "eta": self.eta,
            "observer_mode": self.observer_mode.value,
            "gradient_passed": self.gradient_passed,
            "parameter_step_passed": self.parameter_step_passed,
            "optimizer_state_passed": self.optimizer_state_passed,
            "optimizer_scalar_state_equal": self.optimizer_scalar_state_equal,
            "structural_contract_passed": self.structural_contract_passed,
            "shortcut_diagnostics": self.shortcut_diagnostics.to_dict(),
            "passed": self.passed,
            "gradient_components": len(self.gradient_records),
            "parameter_components": len(self.parameter_records),
            "optimizer_tensor_components": len(self.optimizer_tensor_records),
        }


def evaluate_eq_s2(
    model: nn.Sequential,
    inputs: torch.Tensor,
    targets: torch.Tensor,
    *,
    torch2pc_dir: str | Path,
    seed: int,
    thresholds: EquivalenceThresholds,
    optimizer_factory: OptimizerFactory,
) -> EqS2Result:
    """Evaluate iterative FixedPred against the joint-VJP reduced shortcut."""

    from torch2pc_thesis.pc_methods import backward_for_method
    from torch2pc_thesis.reproducibility import set_global_seed

    if not isinstance(model, nn.Sequential):
        raise TypeError("EQ-S2 requires a top-level nn.Sequential model")
    inference_steps = len(model)
    if inference_steps < 1:
        raise ValueError("EQ-S2 requires at least one top-level layer")

    set_global_seed(seed, warn_only=False)
    fixedpred_model = copy.deepcopy(model)
    shortcut_model = copy.deepcopy(model)

    cpu_rng = torch.random.get_rng_state()
    cuda_rng = torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None

    fixedpred_model.zero_grad(set_to_none=True)
    backward_for_method(
        fixedpred_model,
        nn.CrossEntropyLoss(),
        inputs,
        targets,
        method="fixedpred",
        torch2pc_dir=torch2pc_dir,
        eta=1.0,
        inference_steps=inference_steps,
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
        _named_gradients(fixedpred_model),
        _named_gradients(shortcut_model),
        thresholds,
        prefix="gradient:",
    )

    fixedpred_optimizer = optimizer_factory(fixedpred_model.parameters())
    shortcut_optimizer = optimizer_factory(shortcut_model.parameters())
    fixedpred_optimizer.step()
    shortcut_optimizer.step()

    parameter_records = compare_tensor_maps(
        _named_parameters(fixedpred_model),
        _named_parameters(shortcut_model),
        thresholds,
        prefix="parameter:",
    )

    fixedpred_tensors, fixedpred_scalars = _flatten_optimizer_state(
        fixedpred_optimizer,
        fixedpred_model,
    )
    shortcut_tensors, shortcut_scalars = _flatten_optimizer_state(
        shortcut_optimizer,
        shortcut_model,
    )
    optimizer_tensor_records = compare_tensor_maps(
        fixedpred_tensors,
        shortcut_tensors,
        thresholds,
        prefix="optimizer:",
    )

    return EqS2Result(
        control_id="EQ-S2",
        seed=seed,
        inference_steps=inference_steps,
        eta=1.0,
        observer_mode=ObserverMode.NO_HOOKS,
        gradient_records=gradient_records,
        parameter_records=parameter_records,
        optimizer_tensor_records=optimizer_tensor_records,
        optimizer_scalar_state_equal=fixedpred_scalars == shortcut_scalars,
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
    parameters = {
        name: parameter.detach().clone()
        for name, parameter in model.named_parameters()
        if parameter.requires_grad
    }
    if not parameters:
        raise RuntimeError("No trainable parameters were found")
    return parameters


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
