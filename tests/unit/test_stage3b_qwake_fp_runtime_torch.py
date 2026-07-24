from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import torch
from torch import Tensor, nn

from torch2pc_thesis.stage3b_qwake_core import Capability, ObservationLevel
from torch2pc_thesis.stage3b_qwake_fp_runtime import (
    RUNTIME_ENGINEERING_BATCH_ID,
    ArmOrder,
    RuntimeArmExecution,
    RuntimeCellSpec,
    RuntimeValidationPermissionSet,
)
from torch2pc_thesis.stage3b_qwake_fp_runtime_torch import (
    TorchFixedPredEngineeringBackend,
    _instrumented_fixedpred,
)
from torch2pc_thesis.stage3b_qwake_fp_spec import QWakeFPPairId
from torch2pc_thesis.stage3b_qwake_fp_validation import (
    PairArmId,
    PairArmRecord,
    ValidationLane,
    compare_matched_pair,
    validate_nested_observation_hashes,
)


def FwdPassPlus(
    model: nn.Sequential,
    loss_fn: nn.Module,
    inputs: Tensor,
    targets: Tensor,
) -> tuple[list[Tensor], Tensor, Tensor]:
    activations = [inputs]
    for layer in model:
        activations.append(layer(activations[-1]))
    loss = loss_fn(activations[-1], targets)
    dldy = torch.autograd.grad(loss, activations[-1])[0]
    return activations, loss, dldy


def FixedPredPCPredErrs(
    model: nn.Sequential,
    vhat: Sequence[Tensor],
    dldy: Tensor,
    eta: float = 1.0,
    n: int | None = None,
) -> tuple[list[Tensor], list[Tensor | None]]:
    depth_plus_one = len(model) + 1
    step_count = len(model) if n is None else int(n)
    fixed = [activation.detach() for activation in vhat]
    linear_inputs: list[Tensor] = []
    linear_outputs: list[Tensor] = []
    for layer in range(depth_plus_one - 1):
        linear_input = fixed[layer].detach().requires_grad_(True)
        linear_inputs.append(linear_input)
        linear_outputs.append(model[layer](linear_input))
    epsilon: list[Tensor | None] = [None] * depth_plus_one
    epsilon[-1] = dldy.detach()
    beliefs = [activation.clone() for activation in fixed]
    for iteration in range(step_count):
        retain_graph = iteration < step_count - 1
        for layer in reversed(range(depth_plus_one - 1)):
            epsilon[layer] = fixed[layer] - beliefs[layer]
            upper = epsilon[layer + 1]
            assert upper is not None
            epsdfdv = torch.autograd.grad(
                linear_outputs[layer],
                linear_inputs[layer],
                grad_outputs=upper,
                retain_graph=retain_graph,
            )[0]
            current = epsilon[layer]
            assert current is not None
            beliefs[layer] = beliefs[layer] + eta * (current - epsdfdv)
        for layer in range(1, depth_plus_one - 1):
            beliefs[layer] = beliefs[layer].detach()
            assert epsilon[layer] is not None
            epsilon[layer] = epsilon[layer].detach()
    return beliefs, epsilon


def SetPCGrads(
    model: nn.Sequential,
    epsilon: Sequence[Tensor | None],
    inputs: Tensor,
    v: Sequence[Tensor] | None = None,
) -> None:
    activations = list(v) if v is not None else [inputs]
    if v is None:
        for layer in model:
            activations.append(layer(activations[-1]))
    for layer, module in enumerate(model):
        parameters = tuple(module.parameters())
        if not parameters:
            continue
        output = module(activations[layer].detach())
        upper = epsilon[layer + 1]
        assert upper is not None
        gradients = torch.autograd.grad(
            output,
            parameters,
            grad_outputs=upper,
            allow_unused=True,
        )
        for parameter, gradient in zip(parameters, gradients, strict=True):
            parameter.grad = gradient


def PCInfer(
    model: nn.Sequential,
    loss_fn: nn.Module,
    inputs: Tensor,
    targets: Tensor,
    method: str,
    eta: float = 0.1,
    n: int = 20,
    vinit: object | None = None,
) -> tuple[Any, ...]:
    del vinit
    if method != "FixedPred":
        raise ValueError("test PCInfer supports FixedPred only")
    vhat, loss, dldy = FwdPassPlus(model, loss_fn, inputs, targets)
    beliefs, epsilon = FixedPredPCPredErrs(model, vhat, dldy, eta, n)
    SetPCGrads(model, epsilon, inputs, vhat)
    return vhat, loss, dldy, beliefs, epsilon


def _model() -> nn.Sequential:
    torch.manual_seed(91)
    return nn.Sequential(
        nn.Linear(4, 6),
        nn.Tanh(),
        nn.Linear(6, 3),
    ).to(dtype=torch.float64)


def _batch() -> tuple[Tensor, Tensor]:
    generator = torch.Generator().manual_seed(92)
    return (
        torch.randn(2, 4, generator=generator, dtype=torch.float64),
        torch.tensor([0, 2]),
    )


def _cell(pair_id: QWakeFPPairId) -> RuntimeCellSpec:
    return RuntimeCellSpec(
        lane=ValidationLane.CPU_FLOAT64_ENGINEERING,
        pair_id=pair_id,
        model_seed=0,
        batch_id=RUNTIME_ENGINEERING_BATCH_ID,
        arm_order=ArmOrder.REFERENCE_THEN_INSTRUMENTED,
    )


def _permissions(
    pair_id: QWakeFPPairId,
    arm_id: PairArmId,
) -> RuntimeValidationPermissionSet:
    values = {
        Capability.EXECUTE_FIXEDPRED,
        Capability.COMPUTE_CANONICAL_SUFFIX,
        Capability.COMPUTE_POST_ACTION_ORACLE,
    }
    if arm_id is PairArmId.INSTRUMENTED:
        values.update(
            {
                Capability.COLLECT_A0,
                Capability.RUN_COST_DOMINANCE_CHECK,
            }
        )
        if pair_id in {QWakeFPPairId.P1, QWakeFPPairId.P2}:
            values.add(Capability.COLLECT_A1)
        if pair_id is QWakeFPPairId.P2:
            values.add(Capability.COLLECT_A2)
    return RuntimeValidationPermissionSet(capabilities=frozenset(values))


def _run_pair(
    pair_id: QWakeFPPairId,
) -> tuple[RuntimeArmExecution, RuntimeArmExecution]:
    cell = _cell(pair_id)
    backend = TorchFixedPredEngineeringBackend(
        cell=cell,
        torch2pc_dir=Path("unused"),
        _model=_model(),
        _pc_infer=PCInfer,
        _batch=_batch(),
    )
    state = backend.capture_initial_state()
    rng = backend.capture_rng_state()
    backend.restore_initial_state(state)
    backend.restore_rng_state(rng)
    reference = backend.run_arm(
        cell,
        PairArmId.REFERENCE,
        _permissions(pair_id, PairArmId.REFERENCE),
    )
    backend.restore_initial_state(state)
    backend.restore_rng_state(rng)
    instrumented = backend.run_arm(
        cell,
        PairArmId.INSTRUMENTED,
        _permissions(pair_id, PairArmId.INSTRUMENTED),
    )
    return reference, instrumented


def test_instrumented_fixedpred_preserves_endpoint_and_emits_every_snapshot() -> None:
    model = _model()
    inputs, targets = _batch()
    vhat, _loss, dldy = FwdPassPlus(
        model,
        nn.CrossEntropyLoss(),
        inputs,
        targets,
    )
    reference_v, reference_e = FixedPredPCPredErrs(
        model,
        vhat,
        dldy,
        eta=1.0,
        n=len(model),
    )
    snapshots: list[int] = []
    candidate_v, candidate_e = _instrumented_fixedpred(
        model,
        vhat,
        dldy,
        eta=1.0,
        n=len(model),
        snapshot_callback=lambda step, _v, _e, _f: snapshots.append(step),
    )
    assert snapshots == list(range(len(model) + 1))
    for reference, candidate in zip(reference_v, candidate_v, strict=True):
        assert torch.equal(reference, candidate)
    for reference, candidate in zip(reference_e, candidate_e, strict=True):
        if reference is None:
            assert candidate is None
        else:
            assert candidate is not None
            assert torch.equal(reference, candidate)


def test_concrete_backend_passes_all_three_cpu_matched_pairs() -> None:
    records: dict[QWakeFPPairId, PairArmRecord] = {}
    for pair_id in QWakeFPPairId:
        reference, instrumented = _run_pair(pair_id)
        result = compare_matched_pair(reference.record, instrumented.record)
        assert result.passed
        assert reference.oracle_isolation.passed
        assert instrumented.oracle_isolation.passed
        assert all(item.passed for item in reference.disabled_capability_audits)
        assert all(item.passed for item in instrumented.disabled_capability_audits)
        records[pair_id] = instrumented.record
    assert validate_nested_observation_hashes(
        records[QWakeFPPairId.P0],
        records[QWakeFPPairId.P1],
        records[QWakeFPPairId.P2],
    )


def test_a0_remains_tensor_free_and_a1_a2_are_incremental() -> None:
    _reference0, p0 = _run_pair(QWakeFPPairId.P0)
    _reference1, p1 = _run_pair(QWakeFPPairId.P1)
    _reference2, p2 = _run_pair(QWakeFPPairId.P2)
    assert p0.record.observer_effects.tensor_read_count == 0
    assert p0.record.observer_effects.temporary_allocation_count == 0
    assert p0.record.observer_effects.synchronization_count == 0
    assert p0.record.observer_effects.d2h_bytes == 0
    assert tuple(dict(p1.record.observation_payload_sha256s)) == (
        ObservationLevel.A0,
        ObservationLevel.A1,
    )
    assert tuple(dict(p2.record.observation_payload_sha256s)) == tuple(
        ObservationLevel
    )
