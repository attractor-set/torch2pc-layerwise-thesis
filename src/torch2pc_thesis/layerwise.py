"""Reusable utilities for Stage 3 layer-wise diagnostic probes.

The functions in this module are observational: they collect gradients and
activations without applying an optimizer update. Performance measurements
must be executed separately because hooks and tensor copies add overhead.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
from torch import nn

from torch2pc_thesis.array_types import FloatArray
from torch2pc_thesis.representations import linear_cka, rsa_spearman


@dataclass(frozen=True)
class GradientMetrics:
    """Scalar comparison of a candidate gradient against a reference."""

    cosine: float
    cosine_defined: bool
    relative_l2: float
    norm_ratio: float
    reference_norm: float
    candidate_norm: float
    max_abs_difference: float
    sign_agreement: float
    elements: int

    def to_dict(self) -> dict[str, float | bool | int]:
        return {
            "cosine": self.cosine,
            "cosine_defined": self.cosine_defined,
            "relative_l2": self.relative_l2,
            "norm_ratio": self.norm_ratio,
            "reference_norm": self.reference_norm,
            "candidate_norm": self.candidate_norm,
            "max_abs_difference": self.max_abs_difference,
            "sign_agreement": self.sign_agreement,
            "elements": self.elements,
        }


@dataclass(frozen=True)
class RepresentationMetrics:
    """Similarity metrics for two sample-aligned activation matrices."""

    cka: float
    rsa_spearman: float
    rsa_defined: bool
    samples: int
    reference_features: int
    candidate_features: int

    def to_dict(self) -> dict[str, float | bool | int]:
        return {
            "cka": self.cka,
            "rsa_spearman": self.rsa_spearman,
            "rsa_defined": self.rsa_defined,
            "samples": self.samples,
            "reference_features": self.reference_features,
            "candidate_features": self.candidate_features,
        }


def top_level_parameter_group(parameter_name: str) -> str:
    """Return the first module path component for a named parameter."""

    return parameter_name.split(".", maxsplit=1)[0]


def collect_gradient_vectors(
    model: nn.Module,
    *,
    scope: str,
    include_missing_as_zero: bool = True,
) -> dict[str, torch.Tensor]:
    """Collect flattened gradients by parameter or top-level module.

    Returned tensors are detached CPU float64 vectors so subsequent method
    calls cannot mutate the observations and numerical comparisons are stable.
    """

    if scope not in {"parameter", "top_level"}:
        raise ValueError("scope must be 'parameter' or 'top_level'")

    grouped: dict[str, list[torch.Tensor]] = {}
    for name, parameter in model.named_parameters():
        gradient = parameter.grad
        if gradient is None:
            if not include_missing_as_zero:
                continue
            gradient = torch.zeros_like(parameter)
        if not torch.isfinite(gradient).all():
            raise ValueError(f"non-finite gradient detected for parameter {name!r}")

        key = name if scope == "parameter" else top_level_parameter_group(name)
        grouped.setdefault(key, []).append(
            gradient.detach().reshape(-1).to(device="cpu", dtype=torch.float64)
        )

    return {key: torch.cat(parts) for key, parts in grouped.items()}


def compare_gradient_vectors(
    reference: torch.Tensor,
    candidate: torch.Tensor,
    *,
    epsilon: float = 1e-12,
) -> GradientMetrics:
    """Compare two flattened gradient vectors."""

    reference = reference.detach().reshape(-1).to(device="cpu", dtype=torch.float64)
    candidate = candidate.detach().reshape(-1).to(device="cpu", dtype=torch.float64)
    if reference.shape != candidate.shape:
        raise ValueError(
            "gradient vectors must have the same shape: "
            f"{tuple(reference.shape)} != {tuple(candidate.shape)}"
        )
    if reference.numel() == 0:
        raise ValueError("gradient vectors must be non-empty")
    if not torch.isfinite(reference).all() or not torch.isfinite(candidate).all():
        raise ValueError("gradient vectors must contain only finite values")

    reference_norm = float(torch.linalg.vector_norm(reference).item())
    candidate_norm = float(torch.linalg.vector_norm(candidate).item())
    difference = candidate - reference
    difference_norm = float(torch.linalg.vector_norm(difference).item())

    cosine_defined = reference_norm > epsilon and candidate_norm > epsilon
    if cosine_defined:
        cosine_tensor = torch.dot(reference, candidate) / (reference_norm * candidate_norm)
        cosine = float(torch.clamp(cosine_tensor, min=-1.0, max=1.0).item())
    else:
        cosine = float("nan")

    reference_sign = torch.sign(reference)
    candidate_sign = torch.sign(candidate)
    sign_agreement = float((reference_sign == candidate_sign).to(torch.float64).mean().item())

    return GradientMetrics(
        cosine=cosine,
        cosine_defined=cosine_defined,
        relative_l2=difference_norm / max(reference_norm, epsilon),
        norm_ratio=candidate_norm / max(reference_norm, epsilon),
        reference_norm=reference_norm,
        candidate_norm=candidate_norm,
        max_abs_difference=float(torch.max(torch.abs(difference)).item()),
        sign_agreement=sign_agreement,
        elements=reference.numel(),
    )


def compare_gradient_maps(
    reference: Mapping[str, torch.Tensor],
    candidate: Mapping[str, torch.Tensor],
    *,
    epsilon: float = 1e-12,
) -> dict[str, GradientMetrics]:
    """Compare aligned dictionaries of gradient vectors."""

    reference_keys = set(reference)
    candidate_keys = set(candidate)
    if reference_keys != candidate_keys:
        missing = sorted(reference_keys - candidate_keys)
        extra = sorted(candidate_keys - reference_keys)
        raise ValueError(f"gradient map keys differ; missing={missing}, extra={extra}")

    return {
        key: compare_gradient_vectors(reference[key], candidate[key], epsilon=epsilon)
        for key in reference
    }


def flatten_activation(output: torch.Tensor) -> torch.Tensor:
    """Convert a layer output into a two-dimensional [samples, features] tensor."""

    if output.ndim == 0:
        raise ValueError("activation output must contain a batch dimension")
    if output.ndim == 1:
        return output.reshape(output.shape[0], 1)
    return output.reshape(output.shape[0], -1)


def _extract_tensor(output: Any, *, layer_name: str) -> torch.Tensor:
    if isinstance(output, torch.Tensor):
        return output
    if (
        isinstance(output, tuple | list)
        and len(output) == 1
        and isinstance(output[0], torch.Tensor)
    ):
        return output[0]
    raise TypeError(
        f"layer {layer_name!r} produced an unsupported output type: {type(output).__name__}"
    )


@contextmanager
def _activation_hooks(
    model: nn.Module,
    layer_names: Sequence[str],
    storage: dict[str, list[torch.Tensor]],
) -> Iterator[None]:
    modules = dict(model.named_modules())
    missing = [name for name in layer_names if name not in modules]
    if missing:
        raise ValueError(f"unknown layer names: {missing}")

    handles: list[torch.utils.hooks.RemovableHandle] = []
    for layer_name in layer_names:
        module = modules[layer_name]

        def hook(
            _module: nn.Module,
            _inputs: tuple[Any, ...],
            output: Any,
            *,
            captured_name: str = layer_name,
        ) -> None:
            tensor = _extract_tensor(output, layer_name=captured_name)
            if not torch.isfinite(tensor).all():
                raise ValueError(f"non-finite activation detected at layer {captured_name!r}")
            storage[captured_name].append(
                flatten_activation(tensor.detach()).to(device="cpu", dtype=torch.float64)
            )

        handles.append(module.register_forward_hook(hook))

    try:
        yield
    finally:
        for handle in handles:
            handle.remove()


def capture_activations(
    model: nn.Module,
    inputs: Sequence[torch.Tensor],
    *,
    layer_names: Sequence[str],
    device: torch.device,
    dtype: torch.dtype,
    max_samples: int | None = None,
) -> dict[str, FloatArray]:
    """Capture deterministic, sample-aligned activations from selected modules."""

    if not layer_names:
        raise ValueError("at least one layer name is required")
    if max_samples is not None and max_samples <= 0:
        raise ValueError("max_samples must be positive")

    storage: dict[str, list[torch.Tensor]] = {name: [] for name in layer_names}
    was_training = model.training
    model.eval()

    seen = 0
    with torch.no_grad(), _activation_hooks(model, layer_names, storage):
        for batch in inputs:
            if max_samples is not None and seen >= max_samples:
                break
            remaining = None if max_samples is None else max_samples - seen
            selected = batch if remaining is None else batch[:remaining]
            if selected.shape[0] == 0:
                continue
            model(selected.to(device=device, dtype=dtype, non_blocking=False))
            seen += int(selected.shape[0])

    model.train(was_training)
    if seen == 0:
        raise ValueError("no samples were captured")

    activations: dict[str, FloatArray] = {}
    for layer_name, chunks in storage.items():
        if not chunks:
            raise RuntimeError(f"layer {layer_name!r} did not produce any activation")
        matrix = torch.cat(chunks, dim=0)[:seen]
        activations[layer_name] = matrix.numpy()
    return activations


def compare_representations(
    reference: FloatArray,
    candidate: FloatArray,
) -> RepresentationMetrics:
    """Compute CKA and RSA for two sample-aligned activation matrices."""

    reference_values: FloatArray = np.asarray(reference, dtype=np.float64)
    candidate_values: FloatArray = np.asarray(candidate, dtype=np.float64)
    if reference_values.ndim != 2 or candidate_values.ndim != 2:
        raise ValueError("representations must be two-dimensional")
    if reference_values.shape[0] != candidate_values.shape[0]:
        raise ValueError("representations must contain the same number of samples")
    if reference_values.shape[0] < 2:
        raise ValueError("at least two samples are required")
    if not np.isfinite(reference_values).all() or not np.isfinite(candidate_values).all():
        raise ValueError("representations must contain only finite values")

    cka = float(linear_cka(reference_values, candidate_values))
    try:
        rsa = float(rsa_spearman(reference_values, candidate_values))
        rsa_defined = bool(np.isfinite(rsa))
    except (ValueError, FloatingPointError):
        rsa = float("nan")
        rsa_defined = False

    return RepresentationMetrics(
        cka=cka,
        rsa_spearman=rsa,
        rsa_defined=rsa_defined,
        samples=int(reference_values.shape[0]),
        reference_features=int(reference_values.shape[1]),
        candidate_features=int(candidate_values.shape[1]),
    )


def corresponding_representation_metrics(
    reference: Mapping[str, FloatArray],
    candidate: Mapping[str, FloatArray],
) -> dict[str, RepresentationMetrics]:
    """Compare representations from identically named layers."""

    reference_keys = set(reference)
    candidate_keys = set(candidate)
    if reference_keys != candidate_keys:
        missing = sorted(reference_keys - candidate_keys)
        extra = sorted(candidate_keys - reference_keys)
        raise ValueError(f"activation map keys differ; missing={missing}, extra={extra}")
    return {
        layer_name: compare_representations(reference[layer_name], candidate[layer_name])
        for layer_name in reference
    }


def cross_layer_cka(
    reference: Mapping[str, FloatArray],
    candidate: Mapping[str, FloatArray],
) -> dict[tuple[str, str], float]:
    """Compute the full reference-layer × candidate-layer CKA matrix."""

    output: dict[tuple[str, str], float] = {}
    for reference_name, reference_values in reference.items():
        for candidate_name, candidate_values in candidate.items():
            if reference_values.shape[0] != candidate_values.shape[0]:
                raise ValueError("all cross-layer comparisons must use the same samples")
            output[(reference_name, candidate_name)] = float(
                linear_cka(reference_values, candidate_values)
            )
    return output
