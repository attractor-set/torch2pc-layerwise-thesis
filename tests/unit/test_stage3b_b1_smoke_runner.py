from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import torch
import torch.nn as nn

import torch2pc_thesis.stage3b_b1_smoke as smoke
from torch2pc_thesis.stage3b_b1_equivalence import sha256_file
from torch2pc_thesis.stage3b_b1_isolated_vjp import pc_infer_b1
from torch2pc_thesis.stage3b_b1_reference_trace import reference_pc_infer_with_trace


def _model() -> nn.Sequential:
    return nn.Sequential(
        nn.Linear(4, 6),
        nn.Tanh(),
        nn.Linear(6, 5),
        nn.Tanh(),
        nn.Linear(5, 3),
    ).double()


def _forward(
    model: nn.Sequential,
    loss_fn: nn.Module,
    inputs: torch.Tensor,
    targets: torch.Tensor,
) -> tuple[list[torch.Tensor], torch.Tensor, torch.Tensor]:
    values = [inputs]
    for layer in model:
        values.append(layer(values[-1]))
    loss = loss_fn(values[-1], targets)
    dldy = torch.autograd.grad(loss, values[-1])[0]
    return values, loss, dldy


def _set_pc_grads(
    model: nn.Sequential,
    epsilon: list[torch.Tensor | None],
    inputs: torch.Tensor,
    beliefs: list[torch.Tensor | None] | None = None,
) -> None:
    values = beliefs
    if values is None:
        values = [inputs]
        for layer in model:
            previous = values[-1]
            assert previous is not None
            values.append(layer(previous))
    for layer_index, layer in enumerate(model):
        parameters = tuple(layer.parameters())
        if not parameters:
            continue
        layer_input = values[layer_index]
        upper_error = epsilon[layer_index + 1]
        assert layer_input is not None
        assert upper_error is not None
        output = layer(layer_input.detach())
        gradients = torch.autograd.grad(
            output,
            parameters,
            grad_outputs=upper_error,
            allow_unused=True,
        )
        for parameter, gradient in zip(parameters, gradients, strict=True):
            parameter.grad = gradient


def _reference() -> Any:
    reference = SimpleNamespace(FwdPassPlus=_forward, SetPCGrads=_set_pc_grads)

    def pc_infer(
        model: nn.Sequential,
        loss_fn: nn.Module,
        inputs: torch.Tensor,
        targets: torch.Tensor,
        method: str,
        *,
        eta: float,
        n: int,
    ) -> object:
        return reference_pc_infer_with_trace(
            reference,
            model,
            loss_fn,
            inputs,
            targets,
            method,
            eta=eta,
            inference_steps=n,
            trajectory_sink=lambda snapshot: None,
        )

    reference.PCInfer = pc_infer
    return reference


@pytest.mark.parametrize(("method", "eta"), [("FixedPred", 0.1), ("Strict", 0.05)])
def test_matched_pair_runner_passes_with_identical_reference_and_candidate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    method: str,
    eta: float,
) -> None:
    reference = _reference()
    monkeypatch.setattr(smoke, "load_patched_reference", lambda path: reference)
    monkeypatch.setattr(
        smoke,
        "load_b1_pc_infer",
        lambda path: (
            lambda model, loss_fn, inputs, targets, method, **kwargs: pc_infer_b1(
                reference,
                model,
                loss_fn,
                inputs,
                targets,
                method,
                **kwargs,
            )
        ),
    )
    checkpoint = tmp_path / "checkpoint.pt"
    batch = tmp_path / "batch.pt"
    torch.manual_seed(22)
    torch.save(_model().state_dict(), checkpoint)
    torch.save(
        {
            "split": "validation",
            "inputs": torch.randn(8, 4, dtype=torch.float64),
            "targets": torch.randint(0, 3, (8,)),
        },
        batch,
    )
    spec = smoke.PairSpec(
        request_id="unit",
        attempt_id="unit-attempt",
        lane="cpu_float64",
        method=method,
        model_seed=0,
        batch_index=0,
        run_seed=99,
        checkpoint=smoke.AssetRef(str(checkpoint), sha256_file(checkpoint)),
        batch=smoke.AssetRef(str(batch), sha256_file(batch)),
        method_control=smoke.MethodControl(eta=eta, inference_steps=3),
        lane_control=smoke.LaneControl(device="cpu", dtype="float64"),
        training_mode=True,
        resolved_config_digest="a" * 64,
        source_image_digest="b" * 64,
    )
    result = smoke.run_pair(spec, torch2pc_dir=tmp_path, model_builder=lambda name: _model())
    assert result.pair_admissible
    assert all(bool(gate["passed"]) for gate in result.gates.values())
    pair_dir = smoke.write_pair_result(tmp_path / "attempt", result)
    assert (pair_dir / "endpoint-metrics.csv").is_file()
    assert (pair_dir / "trajectory-metrics.csv").is_file()
    assert (pair_dir / "SHA256SUMS").is_file()
