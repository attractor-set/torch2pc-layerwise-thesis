from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any

import pandas as pd
import torch
import torch.nn as nn

from torch2pc_thesis.pc_methods import backward_for_method
from torch2pc_thesis.reproducibility import set_global_seed


def _function_source(source_text: str, function_name: str) -> str:
    pattern = re.compile(
        rf"^def\s+{re.escape(function_name)}\s*\(.*?(?=^def\s+|\Z)",
        flags=re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(source_text)
    if match is None:
        raise RuntimeError(f"Function {function_name} not found")
    return match.group(0)


def audit_rosenbaum_correction(torch2pc_file: str | Path) -> dict[str, Any]:
    source = Path(torch2pc_file).read_text(encoding="utf-8")
    strict = re.sub(r"\s+", "", _function_source(source, "StrictPCPredErrs"))
    fixed = re.sub(r"\s+", "", _function_source(source, "FixedPredPCPredErrs"))
    exact = re.sub(r"\s+", "", _function_source(source, "ExactPredErrs"))
    loop_pos = strict.find("foriinrange(n):")
    error_pos = strict.find("epsilon[layer]=model[layer-1](v[layer-1])-v[layer]")
    checks = {
        "strict_recomputes_errors_each_iteration": loop_pos >= 0 and error_pos > loop_pos,
        "strict_error_is_prediction_minus_belief": (
            "epsilon[layer]=model[layer-1](v[layer-1])-v[layer]" in strict
        ),
        "strict_update_is_epsilon_minus_vjp": "dv=epsilon[layer]-epsdfdv" in strict,
        "fixedpred_error_is_activation_minus_belief": (
            "epsilon[layer]=vhat[layer]-v[layer]" in fixed
        ),
        "fixedpred_update_is_epsilon_minus_vjp": "dv=epsilon[layer]-epsdfdv" in fixed,
        "exact_belief_is_activation_minus_epsilon": (
            "v[layer]=vhat[layer]-epsilon[layer]" in exact
        ),
    }
    return {"checks": checks, "passed": all(checks.values())}


def named_gradients(model: nn.Module) -> dict[str, torch.Tensor]:
    return {
        name: (
            torch.zeros_like(parameter)
            if parameter.grad is None
            else parameter.grad.detach().clone()
        ).flatten().cpu()
        for name, parameter in model.named_parameters()
        if parameter.requires_grad
    }


def cosine(left: torch.Tensor, right: torch.Tensor, epsilon: float = 1e-12) -> float:
    return float(torch.dot(left, right) / (torch.norm(left) * torch.norm(right) + epsilon))


def relative_l2(
    reference: torch.Tensor,
    candidate: torch.Tensor,
    epsilon: float = 1e-12,
) -> float:
    return float(torch.norm(reference - candidate) / (torch.norm(reference) + epsilon))


def gradient_map_table(
    reference: dict[str, torch.Tensor],
    candidate: dict[str, torch.Tensor],
) -> pd.DataFrame:
    records = []
    for name in sorted(reference.keys() & candidate.keys()):
        left = reference[name]
        right = candidate[name]
        records.append(
            {
                "parameter": name,
                "cosine": cosine(left, right),
                "relative_l2": relative_l2(left, right),
                "max_abs": float(torch.max(torch.abs(left - right))),
            }
        )
    return pd.DataFrame(records)


def gradients_for_method(
    model: nn.Module,
    inputs: torch.Tensor,
    targets: torch.Tensor,
    *,
    method: str,
    torch2pc_dir: str | Path,
    eta: float | None = None,
    inference_steps: int | None = None,
) -> dict[str, torch.Tensor]:
    model.zero_grad(set_to_none=True)
    backward_for_method(
        model,
        nn.CrossEntropyLoss(),
        inputs,
        targets,
        method=method,
        torch2pc_dir=torch2pc_dir,
        eta=eta,
        inference_steps=inference_steps,
    )
    return named_gradients(model)


def exact_vs_bp(
    model: nn.Module,
    inputs: torch.Tensor,
    targets: torch.Tensor,
    *,
    torch2pc_dir: str | Path,
    seed: int,
) -> pd.DataFrame:
    set_global_seed(seed)
    bp_model = copy.deepcopy(model)
    exact_model = copy.deepcopy(model)
    bp = gradients_for_method(
        bp_model, inputs, targets, method="bp", torch2pc_dir=torch2pc_dir
    )
    exact = gradients_for_method(
        exact_model, inputs, targets, method="exact", torch2pc_dir=torch2pc_dir
    )
    return gradient_map_table(bp, exact)


def fixedpred_vs_exact(
    model: nn.Module,
    inputs: torch.Tensor,
    targets: torch.Tensor,
    *,
    torch2pc_dir: str | Path,
    seed: int,
) -> pd.DataFrame:
    set_global_seed(seed)
    exact_model = copy.deepcopy(model)
    fixed_model = copy.deepcopy(model)
    exact = gradients_for_method(
        exact_model, inputs, targets, method="exact", torch2pc_dir=torch2pc_dir
    )
    fixed = gradients_for_method(
        fixed_model,
        inputs,
        targets,
        method="fixedpred",
        torch2pc_dir=torch2pc_dir,
        eta=1.0,
        inference_steps=len(model),
    )
    return gradient_map_table(exact, fixed)
