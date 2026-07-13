#!/usr/bin/env python3
"""Run a non-evidence Stage 3B profiler integrity smoke check."""

from __future__ import annotations

import argparse
import json
from copy import deepcopy

import torch
from torch import Tensor, nn

from torch2pc_thesis.profiling import ProfilingProtocol
from torch2pc_thesis.stage3b_profiling import (
    Stage3BProfiler,
    assert_non_perturbing,
    snapshot_named_tensors,
    thresholds_for_device,
    validate_profile_completeness,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--method", choices=("fixedpred", "strict"), default="fixedpred")
    return parser.parse_args()


def _snapshot(model: nn.Module) -> dict[str, Tensor]:
    values: dict[str, Tensor] = {}
    for name, parameter in model.named_parameters():
        values[f"parameter::{name}"] = parameter
        if parameter.grad is not None:
            values[f"gradient::{name}"] = parameter.grad
    return snapshot_named_tensors(values)


def _step(
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    inputs: Tensor,
    targets: Tensor,
    profiler: Stage3BProfiler | None,
) -> None:
    optimizer.zero_grad(set_to_none=True)

    if profiler is None:
        predictions = model(inputs)
        loss = torch.mean((predictions - targets) ** 2)
        state = loss
        state = state + torch.zeros((), dtype=state.dtype)
        state.backward()
        optimizer.step()
        return

    with profiler.region("initial_forward", repetition=0, step=0):
        predictions = model(inputs)
    with profiler.region("state_inference", repetition=0, step=0) as counters:
        loss = torch.mean((predictions - targets) ** 2)
        counters.actual_inference_steps = 1
    with profiler.region("local_state_vjp", repetition=0, step=0):
        state = loss + torch.zeros((), dtype=loss.dtype)
    with profiler.region("parameter_vjp", repetition=0, step=0) as counters:
        state.backward()
        counters.vjp_calls = 1
    with profiler.region("optimizer_step", repetition=0, step=0):
        optimizer.step()


def main() -> None:
    args = parse_args()
    torch.manual_seed(20260713)
    inputs = torch.randn(8, 4, dtype=torch.float64)
    targets = torch.randn(8, 2, dtype=torch.float64)

    reference_model = nn.Linear(4, 2, dtype=torch.float64)
    instrumented_model = deepcopy(reference_model)
    reference_optimizer = torch.optim.SGD(reference_model.parameters(), lr=0.05)
    instrumented_optimizer = torch.optim.SGD(instrumented_model.parameters(), lr=0.05)

    _step(reference_model, reference_optimizer, inputs, targets, None)
    profiler = Stage3BProfiler(device="cpu", method=args.method)
    _step(instrumented_model, instrumented_optimizer, inputs, targets, profiler)

    comparisons = assert_non_perturbing(
        _snapshot(reference_model),
        _snapshot(instrumented_model),
        thresholds=thresholds_for_device("cpu", torch.float64),
    )
    validate_profile_completeness(
        profiler.records,
        ProfilingProtocol(warmup_steps=0, measured_steps=1, repetitions=1),
    )

    payload = {
        "schema_version": 1,
        "workload": "synthetic_cpu_integrity_smoke",
        "evidence": False,
        "method_label": args.method,
        "records": [record.to_record() for record in profiler.records],
        "comparisons": [comparison.to_record() for comparison in comparisons],
        "status": "pass",
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
