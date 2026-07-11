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


def structural_correction_check(torch2pc_file: str | Path) -> dict[str, Any]:
    """Observe source patterns associated with the published correction.

    This is a structural source-code check. It does not establish semantic
    equivalence by itself; numerical controls are evaluated separately.
    """
    source = Path(torch2pc_file).read_text(encoding="utf-8")
    strict = re.sub(r"\s+", "", _function_source(source, "StrictPCPredErrs"))
    fixed = re.sub(r"\s+", "", _function_source(source, "FixedPredPCPredErrs"))
    exact = re.sub(r"\s+", "", _function_source(source, "ExactPredErrs"))
    loop_pos = strict.find("foriinrange(n):")
    error_pos = strict.find("epsilon[layer]=model[layer-1](v[layer-1])-v[layer]")
    observations = {
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
    return {
        "check_kind": "source_pattern_observation",
        "observations": observations,
        "all_observed": all(observations.values()),
        "scope": "Pinned TorchSeq2PC.py source only; numerical controls remain required.",
    }


def audit_rosenbaum_correction(torch2pc_file: str | Path) -> dict[str, Any]:
    """Backward-compatible representation of the structural source check."""
    result = structural_correction_check(torch2pc_file)
    return {
        "checks": result["observations"],
        "passed": result["all_observed"],
    }


def named_gradients(model: nn.Module) -> dict[str, torch.Tensor]:
    gradients: dict[str, torch.Tensor] = {}
    missing: list[str] = []
    for name, parameter in model.named_parameters():
        if not parameter.requires_grad:
            continue
        if parameter.grad is None:
            missing.append(name)
            continue
        gradients[name] = parameter.grad.detach().clone().flatten().cpu()
    if missing:
        raise RuntimeError(f"Missing gradients for trainable parameters: {missing}")
    if not gradients:
        raise RuntimeError("No trainable parameter gradients were produced")
    return gradients


def cosine(left: torch.Tensor, right: torch.Tensor, epsilon: float = 1e-12) -> float:
    if epsilon <= 0:
        raise ValueError("epsilon must be positive")
    left_norm = float(torch.norm(left))
    right_norm = float(torch.norm(right))
    if left_norm <= epsilon and right_norm <= epsilon:
        return 1.0
    if left_norm <= epsilon or right_norm <= epsilon:
        return 0.0
    return float(torch.dot(left, right) / (left_norm * right_norm))


def relative_l2(
    reference: torch.Tensor,
    candidate: torch.Tensor,
    epsilon: float = 1e-12,
) -> float:
    if epsilon <= 0:
        raise ValueError("epsilon must be positive")
    difference = float(torch.norm(reference - candidate))
    reference_norm = float(torch.norm(reference))
    if reference_norm <= epsilon:
        return 0.0 if difference <= epsilon else float("inf")
    return difference / reference_norm


def gradient_map_table(
    reference: dict[str, torch.Tensor],
    candidate: dict[str, torch.Tensor],
) -> pd.DataFrame:
    if set(reference) != set(candidate):
        missing_reference = sorted(set(candidate) - set(reference))
        missing_candidate = sorted(set(reference) - set(candidate))
        raise RuntimeError(
            "Gradient parameter sets differ: "
            f"missing_in_reference={missing_reference}, "
            f"missing_in_candidate={missing_candidate}"
        )
    if not reference:
        raise RuntimeError("Gradient comparison received no parameters")
    records = []
    for name in sorted(reference):
        left = reference[name]
        right = candidate[name]
        if left.shape != right.shape:
            raise RuntimeError(
                f"Gradient shape mismatch for {name}: {left.shape} != {right.shape}"
            )
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
