from __future__ import annotations

import copy
import json
import random
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, cast

import numpy as np
import torch
import torch.nn as nn

from torch2pc_thesis.stage3b_b1_equivalence import (
    THRESHOLD_PROFILES,
    GateOutcome,
    JsonScalar,
    JsonValue,
    RunEndpoints,
    ScalarMetric,
    TensorMetric,
    apply_registered_sgd_step,
    atomic_write_json,
    canonical_json_digest,
    capture_rng_snapshot,
    collect_named_gradients,
    collect_named_parameters,
    compare_tensor_maps,
    flatten_state,
    flatten_trajectory,
    gate_from_scalar_metrics,
    gate_from_tensor_metrics,
    restore_rng_snapshot,
    rng_snapshot_digest,
    scalar_map_metrics,
    sha256_file,
    write_csv_rows,
)
from torch2pc_thesis.stage3b_b1_isolated_vjp import (
    PATCHED_TORCH2PC_COMMIT,
    B1CounterCollector,
    B1ObserverMode,
    B1StructuralEvent,
    B1SweepSnapshot,
    load_b1_pc_infer,
    load_patched_reference,
)
from torch2pc_thesis.stage3b_b1_reference_trace import (
    reference_pc_infer_with_trace,
)

PROJECT_BASE_COMMIT = "542d1dd10cfbc96746c2925c025e3f5311e753db"
B1_IMPLEMENTATION_COMMIT = "ec12e9a"
EXPECTED_METHODS = ("FixedPred", "Strict")
EXPECTED_LANES = ("cpu_float64", "rocm_float32")
EXPECTED_SEEDS = (0, 1, 2)

ModelBuilder = Callable[[str], nn.Sequential]


@dataclass(frozen=True)
class AssetRef:
    path: str
    sha256: str


@dataclass(frozen=True)
class MethodControl:
    eta: float
    inference_steps: int


@dataclass(frozen=True)
class LaneControl:
    device: str
    dtype: str


@dataclass(frozen=True)
class PairSpec:
    request_id: str
    attempt_id: str
    lane: str
    method: str
    model_seed: int
    batch_index: int
    run_seed: int
    checkpoint: AssetRef
    batch: AssetRef
    method_control: MethodControl
    lane_control: LaneControl
    training_mode: bool
    resolved_config_digest: str
    source_image_digest: str

    @property
    def pair_id(self) -> str:
        return (
            f"{self.lane}__{self.method.lower()}__"
            f"seed-{self.model_seed}__batch-{self.batch_index}"
        )


@dataclass(frozen=True)
class PairResult:
    pair_id: str
    pair_spec: dict[str, JsonValue]
    gates: dict[str, dict[str, JsonValue]]
    pair_admissible: bool
    trajectory_metrics: tuple[TensorMetric, ...]
    endpoint_metrics: tuple[TensorMetric, ...]
    scalar_metrics: tuple[ScalarMetric, ...]
    structural_events: tuple[B1StructuralEvent, ...]
    provenance: dict[str, JsonValue]

    def summary(self) -> dict[str, JsonValue]:
        return {
            "pair_id": self.pair_id,
            "pair_spec": self.pair_spec,
            "gates": self.gates,
            "pair_admissible": self.pair_admissible,
            "provenance": self.provenance,
        }


def load_and_validate_request(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Smoke request must be a JSON object")
    validate_request(payload)
    return payload


def validate_request(payload: Mapping[str, Any]) -> None:
    _require_equal(payload, "schema_version", 1)
    _require_equal(payload, "scope", "smoke")
    _require_equal(payload, "dataset", "FashionMNIST")
    _require_equal(payload, "split", "validation")
    _require_equal(payload, "architecture", "lenet_classic")
    _require_equal(payload, "methods", list(EXPECTED_METHODS))
    _require_equal(payload, "model_seeds", list(EXPECTED_SEEDS))
    _require_equal(payload, "batches_per_seed", 1)
    _require_equal(payload, "lanes", list(EXPECTED_LANES))
    _require_equal(payload, "observer_mode", "no_hooks")
    _require_equal(payload, "structural_observer_mode", "counters_only")
    _require_equal(payload, "test_split_access", False)
    _require_equal(payload, "dangerous_miss_limit", 0)
    _require_equal(payload, "torch2pc_commit", PATCHED_TORCH2PC_COMMIT)
    _require_equal(payload, "project_base_commit", PROJECT_BASE_COMMIT)
    _require_equal(payload, "b1_implementation_commit", B1_IMPLEMENTATION_COMMIT)

    request_id = _require_non_empty_string(payload, "request_id")
    attempt_id = _require_non_empty_string(payload, "attempt_id")
    if "/" in request_id or "/" in attempt_id:
        raise ValueError("request_id and attempt_id must be path-safe")
    resolved_config_digest = _require_sha256(payload, "resolved_config_digest")
    _require_sha256(payload, "source_image_digest")
    resolved_config = _require_mapping(payload, "resolved_config")
    if canonical_json_digest(resolved_config) != resolved_config_digest:
        raise ValueError("resolved_config_digest does not match resolved_config")
    run_seed_base = payload.get("run_seed_base")
    if not isinstance(run_seed_base, int) or run_seed_base < 0:
        raise ValueError("run_seed_base must be a non-negative integer")
    if not isinstance(payload.get("training_mode"), bool):
        raise ValueError("training_mode must be boolean")

    optimizer = _require_mapping(payload, "optimizer")
    _require_equal(optimizer, "name", "SGD")
    _require_equal(optimizer, "learning_rate", 0.001)
    _require_equal(optimizer, "momentum", 0.0)

    lane_controls = _require_mapping(payload, "lane_controls")
    _validate_lane_control(lane_controls, "cpu_float64", "cpu", "float64")
    _validate_lane_control(lane_controls, "rocm_float32", "cuda", "float32")

    method_controls = _require_mapping(payload, "method_controls")
    for method in EXPECTED_METHODS:
        control = _require_mapping(method_controls, method)
        eta = control.get("eta")
        steps = control.get("inference_steps")
        if not isinstance(eta, float | int) or float(eta) <= 0:
            raise ValueError(f"{method}.eta must be positive")
        if not isinstance(steps, int) or steps < 1:
            raise ValueError(f"{method}.inference_steps must be positive")

    checkpoints = _require_mapping(payload, "checkpoints")
    batches = _require_mapping(payload, "batches")
    for seed in EXPECTED_SEEDS:
        _validate_asset(_require_mapping(checkpoints, str(seed)), f"checkpoint[{seed}]")
        _validate_asset(_require_mapping(batches, str(seed)), f"batch[{seed}]")


def build_pair_specs(payload: Mapping[str, Any]) -> list[PairSpec]:
    validate_request(payload)
    checkpoints = _require_mapping(payload, "checkpoints")
    batches = _require_mapping(payload, "batches")
    method_controls = _require_mapping(payload, "method_controls")
    lane_controls = _require_mapping(payload, "lane_controls")
    request_id = cast(str, payload["request_id"])
    attempt_id = cast(str, payload["attempt_id"])
    specs: list[PairSpec] = []
    for lane in EXPECTED_LANES:
        lane_payload = _require_mapping(lane_controls, lane)
        for method in EXPECTED_METHODS:
            method_payload = _require_mapping(method_controls, method)
            for seed in EXPECTED_SEEDS:
                specs.append(
                    PairSpec(
                        request_id=request_id,
                        attempt_id=attempt_id,
                        lane=lane,
                        method=method,
                        model_seed=seed,
                        batch_index=0,
                        run_seed=int(payload["run_seed_base"]) + seed,
                        checkpoint=_asset_from_mapping(
                            _require_mapping(checkpoints, str(seed))
                        ),
                        batch=_asset_from_mapping(
                            _require_mapping(batches, str(seed))
                        ),
                        method_control=MethodControl(
                            eta=float(method_payload["eta"]),
                            inference_steps=int(method_payload["inference_steps"]),
                        ),
                        lane_control=LaneControl(
                            device=str(lane_payload["device"]),
                            dtype=str(lane_payload["dtype"]),
                        ),
                        training_mode=bool(payload["training_mode"]),
                        resolved_config_digest=str(payload["resolved_config_digest"]),
                        source_image_digest=str(payload["source_image_digest"]),
                    )
                )
    if len(specs) != 12:
        raise RuntimeError("B1 smoke request did not resolve to 12 matched pairs")
    return specs


def run_pair(
    spec: PairSpec,
    *,
    torch2pc_dir: Path,
    model_builder: ModelBuilder,
) -> PairResult:
    profile = THRESHOLD_PROFILES[spec.lane]
    device = _resolve_device(spec.lane_control)
    dtype = _resolve_dtype(spec.lane_control.dtype)
    checkpoint_path = Path(spec.checkpoint.path)
    batch_path = Path(spec.batch.path)
    _verify_asset(checkpoint_path, spec.checkpoint.sha256)
    _verify_asset(batch_path, spec.batch.sha256)

    model = model_builder("lenet_classic")
    state_dict = _load_state_dict(checkpoint_path)
    model.load_state_dict(state_dict, strict=True)
    model.to(device=device, dtype=dtype)
    model.train(spec.training_mode)
    inputs, targets = _load_batch(batch_path)
    inputs = inputs.to(device=device, dtype=dtype)
    targets = targets.to(device=device)
    loss_fn = nn.CrossEntropyLoss()

    reference = load_patched_reference(torch2pc_dir)
    candidate_infer = load_b1_pc_infer(torch2pc_dir)
    canonical_infer = getattr(cast(Any, reference), "PCInfer", None)
    if not callable(canonical_infer):
        raise RuntimeError("Patched reference lacks canonical PCInfer")

    _seed_everything(spec.run_seed)
    pair_rng = capture_rng_snapshot()
    rng_before = rng_snapshot_digest(pair_rng)

    traced_model = copy.deepcopy(model)
    traced_snapshots: list[B1SweepSnapshot] = []
    restore_rng_snapshot(pair_rng)
    traced_before = rng_snapshot_digest(capture_rng_snapshot())
    traced_output = reference_pc_infer_with_trace(
        reference,
        traced_model,
        loss_fn,
        inputs,
        targets,
        spec.method,
        eta=spec.method_control.eta,
        inference_steps=spec.method_control.inference_steps,
        trajectory_sink=traced_snapshots.append,
    )
    traced_endpoints = _capture_endpoints_from_output(
        traced_model,
        traced_output,
        spec.method_control.inference_steps,
        traced_before,
        rng_snapshot_digest(capture_rng_snapshot()),
    )

    canonical_model = copy.deepcopy(model)
    restore_rng_snapshot(pair_rng)
    canonical_before = rng_snapshot_digest(capture_rng_snapshot())
    canonical_output = canonical_infer(
        canonical_model,
        loss_fn,
        inputs,
        targets,
        spec.method,
        eta=spec.method_control.eta,
        n=spec.method_control.inference_steps,
    )
    canonical_endpoints = _capture_endpoints_from_output(
        canonical_model,
        canonical_output,
        spec.method_control.inference_steps,
        canonical_before,
        rng_snapshot_digest(capture_rng_snapshot()),
    )

    candidate_model = copy.deepcopy(model)
    candidate_snapshots: list[B1SweepSnapshot] = []
    restore_rng_snapshot(pair_rng)
    candidate_before = rng_snapshot_digest(capture_rng_snapshot())
    candidate_output = candidate_infer(
        candidate_model,
        loss_fn,
        inputs,
        targets,
        spec.method,
        eta=spec.method_control.eta,
        inference_steps=spec.method_control.inference_steps,
        observer_mode=B1ObserverMode.NO_HOOKS,
        trajectory_sink=candidate_snapshots.append,
    )
    candidate_endpoints = _capture_endpoints_from_output(
        candidate_model,
        candidate_output,
        spec.method_control.inference_steps,
        candidate_before,
        rng_snapshot_digest(capture_rng_snapshot()),
    )

    structural_model = copy.deepcopy(model)
    structural_collector = B1CounterCollector()
    restore_rng_snapshot(pair_rng)
    candidate_infer(
        structural_model,
        loss_fn,
        inputs,
        targets,
        spec.method,
        eta=spec.method_control.eta,
        inference_steps=spec.method_control.inference_steps,
        observer_mode=B1ObserverMode.COUNTERS_ONLY,
        event_sink=structural_collector,
    )

    trajectory_metrics = tuple(
        compare_tensor_maps(
            flatten_trajectory(traced_snapshots),
            flatten_trajectory(candidate_snapshots),
            profile,
        )
    )
    endpoint_metrics = tuple(
        compare_tensor_maps(
            _endpoint_tensor_map(traced_endpoints),
            _endpoint_tensor_map(candidate_endpoints),
            profile,
        )
    )
    guard_metrics = tuple(
        compare_tensor_maps(
            _endpoint_tensor_map(traced_endpoints),
            _endpoint_tensor_map(canonical_endpoints),
            profile,
        )
    )

    scalar_metrics = tuple(
        scalar_map_metrics(
            "optimizer",
            traced_endpoints.optimizer.scalar_state,
            candidate_endpoints.optimizer.scalar_state,
        )
        + [
            ScalarMetric(
                component="inference_steps",
                passed=(
                    traced_endpoints.inference_steps
                    == candidate_endpoints.inference_steps
                    == spec.method_control.inference_steps
                ),
                reference=traced_endpoints.inference_steps,
                candidate=candidate_endpoints.inference_steps,
            ),
            ScalarMetric(
                component="rng_before",
                passed=(traced_endpoints.rng_before == candidate_endpoints.rng_before),
                reference=traced_endpoints.rng_before,
                candidate=candidate_endpoints.rng_before,
            ),
            ScalarMetric(
                component="rng_after",
                passed=(traced_endpoints.rng_after == candidate_endpoints.rng_after),
                reference=traced_endpoints.rng_after,
                candidate=candidate_endpoints.rng_after,
            ),
        ]
    )

    structural_gate = _structural_gate(
        spec,
        structural_collector.events,
        len(model),
    )
    tensor_numerical_gate = gate_from_tensor_metrics("NUM-B1", endpoint_metrics)
    scalar_numerical_gate = gate_from_scalar_metrics("NUM-B1", scalar_metrics)
    numerical_gate = GateOutcome(
        gate_id="NUM-B1",
        passed=tensor_numerical_gate.passed and scalar_numerical_gate.passed,
        reasons=tensor_numerical_gate.reasons + scalar_numerical_gate.reasons,
    )
    trajectory_gate = gate_from_tensor_metrics("TRAJ-B1", trajectory_metrics)
    observer_gate = GateOutcome(
        gate_id="OBS-B1",
        passed=True,
        reasons=(),
    )
    guard_gate = gate_from_tensor_metrics("REFERENCE-TRACE-GUARD", guard_metrics)
    provenance_reasons: list[str] = []
    if not guard_gate.passed:
        provenance_reasons.append("canonical_reference_trace_guard_failed")
    if rng_before != traced_before or rng_before != candidate_before:
        provenance_reasons.append("rng_restoration_mismatch")
    provenance_gate = GateOutcome(
        gate_id="PROV-B1",
        passed=not provenance_reasons,
        reasons=tuple(provenance_reasons),
    )
    gates = (
        structural_gate,
        numerical_gate,
        trajectory_gate,
        observer_gate,
        provenance_gate,
    )
    pair_admissible = all(gate.passed for gate in gates)
    return PairResult(
        pair_id=spec.pair_id,
        pair_spec=_pair_spec_dict(spec),
        gates={gate.gate_id: gate.to_dict() for gate in gates},
        pair_admissible=pair_admissible,
        trajectory_metrics=trajectory_metrics,
        endpoint_metrics=endpoint_metrics + guard_metrics,
        scalar_metrics=scalar_metrics,
        structural_events=tuple(structural_collector.events),
        provenance={
            "project_base_commit": PROJECT_BASE_COMMIT,
            "b1_implementation_commit": B1_IMPLEMENTATION_COMMIT,
            "torch2pc_commit": PATCHED_TORCH2PC_COMMIT,
            "request_id": spec.request_id,
            "attempt_id": spec.attempt_id,
            "resolved_config_digest": spec.resolved_config_digest,
            "source_image_digest": spec.source_image_digest,
            "checkpoint_sha256": spec.checkpoint.sha256,
            "batch_sha256": spec.batch.sha256,
            "rng_pair_digest": rng_before,
        },
    )


def write_pair_result(root: Path, result: PairResult) -> Path:
    pair_dir = root / "pairs" / result.pair_id
    if pair_dir.exists():
        raise FileExistsError(f"Append-only pair directory already exists: {pair_dir}")
    pair_dir.mkdir(parents=True)
    atomic_write_json(pair_dir / "pair.json", result.summary())
    write_csv_rows(
        pair_dir / "trajectory-metrics.csv",
        (
            {"pair_id": result.pair_id, **metric.to_row()}
            for metric in result.trajectory_metrics
        ),
    )
    write_csv_rows(
        pair_dir / "endpoint-metrics.csv",
        _endpoint_metric_rows(result),
    )
    with (pair_dir / "structural-events.jsonl").open("w", encoding="utf-8") as stream:
        for event in result.structural_events:
            stream.write(json.dumps(event.to_dict(), sort_keys=True) + "\n")
    files = [
        pair_dir / "pair.json",
        pair_dir / "trajectory-metrics.csv",
        pair_dir / "endpoint-metrics.csv",
        pair_dir / "structural-events.jsonl",
    ]
    (pair_dir / "SHA256SUMS").write_text(
        "".join(f"{sha256_file(path)}  {path.name}\n" for path in files),
        encoding="utf-8",
    )
    return pair_dir


def _endpoint_metric_rows(result: PairResult) -> list[dict[str, JsonScalar]]:
    rows: list[dict[str, JsonScalar]] = []
    for tensor_metric in result.endpoint_metrics:
        rows.append(
            {
                "pair_id": result.pair_id,
                "metric_kind": "tensor",
                **tensor_metric.to_row(),
                "reference_scalar": None,
                "candidate_scalar": None,
            }
        )
    for scalar_metric in result.scalar_metrics:
        rows.append(
            {
                "pair_id": result.pair_id,
                "metric_kind": "scalar",
                "component": scalar_metric.component,
                "passed": scalar_metric.passed,
                "finite": None,
                "presence_match": None,
                "reference_l2": None,
                "candidate_l2": None,
                "difference_l2": None,
                "relative_l2": None,
                "cosine": None,
                "max_abs": None,
                "zero_case": None,
                "reference_scalar": scalar_metric.reference,
                "candidate_scalar": scalar_metric.candidate,
            }
        )
    return rows


def aggregate_attempt(
    request: Mapping[str, Any],
    attempt_root: Path,
) -> dict[str, JsonValue]:
    specs = build_pair_specs(request)
    expected_ids = {spec.pair_id for spec in specs}
    pair_root = attempt_root / "pairs"
    observed_files = sorted(pair_root.glob("*/pair.json"))
    observed_ids = {path.parent.name for path in observed_files}
    if observed_ids != expected_ids:
        missing = sorted(expected_ids - observed_ids)
        unexpected = sorted(observed_ids - expected_ids)
        raise RuntimeError(
            f"Incomplete smoke attempt: missing={missing}, unexpected={unexpected}"
        )

    summaries = [json.loads(path.read_text(encoding="utf-8")) for path in observed_files]
    failed_pairs = sorted(
        str(summary["pair_id"])
        for summary in summaries
        if not bool(summary["pair_admissible"])
    )
    all_gate_ids = ("STRUCT-B1", "NUM-B1", "TRAJ-B1", "OBS-B1", "PROV-B1")
    gates: dict[str, JsonValue] = {}
    for gate_id in all_gate_ids:
        failed = sorted(
            str(summary["pair_id"])
            for summary in summaries
            if not bool(summary["gates"][gate_id]["passed"])
        )
        gates[gate_id] = {"passed": not failed, "failed_pairs": failed}
    eq_pass = not failed_pairs and all(
        bool(gates[gate_id]["passed"])
        for gate_id in all_gate_ids
    )
    decision: dict[str, JsonValue] = {
        "decision_id": "EQ-B1",
        "status": "pass" if eq_pass else "fail",
        "dangerous_miss_limit": 0,
        "dangerous_misses": 0,
        "matched_pairs_expected": 12,
        "matched_pairs_observed": len(summaries),
        "failed_pairs": failed_pairs,
        "gates": gates,
        "request_digest": canonical_json_digest(request),
        "sealed": True,
    }
    if (attempt_root / "decision.json").exists():
        raise FileExistsError("Append-only decision.json already exists")

    atomic_write_json(attempt_root / "request.json", request)
    resolved_config = _require_mapping(request, "resolved_config")
    atomic_write_json(attempt_root / "resolved-config.json", resolved_config)
    _combine_csv_files(
        [path.parent / "trajectory-metrics.csv" for path in observed_files],
        attempt_root / "trajectory-metrics.csv",
    )
    _combine_csv_files(
        [path.parent / "endpoint-metrics.csv" for path in observed_files],
        attempt_root / "endpoint-metrics.csv",
    )
    with (attempt_root / "structural-events.jsonl").open(
        "w", encoding="utf-8"
    ) as output_stream:
        for pair_file in observed_files:
            pair_id = pair_file.parent.name
            events_path = pair_file.parent / "structural-events.jsonl"
            for line in events_path.read_text(encoding="utf-8").splitlines():
                event = json.loads(line)
                event["pair_id"] = pair_id
                output_stream.write(json.dumps(event, sort_keys=True) + "\n")
    atomic_write_json(attempt_root / "decision.json", decision)
    required = [
        attempt_root / "request.json",
        attempt_root / "resolved-config.json",
        attempt_root / "trajectory-metrics.csv",
        attempt_root / "endpoint-metrics.csv",
        attempt_root / "structural-events.jsonl",
        attempt_root / "decision.json",
    ]
    (attempt_root / "SHA256SUMS").write_text(
        "".join(
            f"{sha256_file(path)}  {path.name}\n"
            for path in required
        ),
        encoding="utf-8",
    )
    return decision


def _combine_csv_files(sources: Sequence[Path], destination: Path) -> None:
    import csv

    rows: list[dict[str, JsonScalar]] = []
    fieldnames: list[str] | None = None
    for source in sources:
        with source.open("r", encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames is None:
                raise RuntimeError(f"CSV has no header: {source}")
            if fieldnames is None:
                fieldnames = list(reader.fieldnames)
            elif list(reader.fieldnames) != fieldnames:
                raise RuntimeError(f"CSV schema mismatch: {source}")
            rows.extend(cast(dict[str, JsonScalar], row) for row in reader)
    if fieldnames is None or not rows:
        raise RuntimeError(f"No rows to aggregate into {destination}")
    write_csv_rows(destination, rows)


def _capture_endpoints_from_output(
    model: nn.Module,
    output: object,
    inference_steps: int,
    rng_before: str,
    rng_after: str,
) -> RunEndpoints:
    if not isinstance(output, tuple) or len(output) != 5:
        raise RuntimeError("Unexpected PCInfer output structure")
    _, loss, dldy, beliefs, epsilon = output
    if not torch.is_tensor(loss) or not torch.is_tensor(dldy):
        raise RuntimeError("Unexpected PCInfer scalar/cotangent output")
    if not isinstance(beliefs, list) or not isinstance(epsilon, list):
        raise RuntimeError("Unexpected PCInfer state output")
    gradients = collect_named_gradients(model)
    optimizer = apply_registered_sgd_step(model)
    return RunEndpoints(
        loss=loss.detach().clone(),
        output_cotangent=dldy.detach().clone(),
        final_beliefs=tuple(_clone_optional(value) for value in beliefs),
        final_prediction_errors=tuple(_clone_optional(value) for value in epsilon),
        gradients=gradients,
        parameters_after_step=collect_named_parameters(model),
        optimizer=optimizer,
        inference_steps=inference_steps,
        rng_before=rng_before,
        rng_after=rng_after,
    )


def _endpoint_tensor_map(endpoints: RunEndpoints) -> dict[str, torch.Tensor | None]:
    result: dict[str, torch.Tensor | None] = {
        "endpoint/final_loss": endpoints.loss,
        "endpoint/output_cotangent": endpoints.output_cotangent,
    }
    result.update(flatten_state("endpoint/final_beliefs", endpoints.final_beliefs))
    result.update(
        flatten_state(
            "endpoint/final_prediction_errors",
            endpoints.final_prediction_errors,
        )
    )
    result.update(
        {f"endpoint/gradient/{name}": value for name, value in endpoints.gradients.items()}
    )
    result.update(
        {
            f"endpoint/parameter_after_sgd/{name}": value
            for name, value in endpoints.parameters_after_step.items()
        }
    )
    result.update(
        {
            f"endpoint/optimizer/{name}": value
            for name, value in endpoints.optimizer.tensor_state.items()
        }
    )
    return result


def _structural_gate(
    spec: PairSpec,
    events: Sequence[B1StructuralEvent],
    model_depth: int,
) -> GateOutcome:
    edge_count = model_depth if spec.method == "FixedPred" else model_depth - 1
    expected = edge_count * spec.method_control.inference_steps
    reasons: list[str] = []
    if len(events) != expected:
        reasons.append(f"event_count:{len(events)}!={expected}")
    for event in events:
        if event.logical_edge_count != 1:
            reasons.append("logical_edge_count")
        if event.state_vjp_call_count != 1:
            reasons.append("state_vjp_call_count")
        if event.graph_island_count != 1:
            reasons.append("graph_island_count")
        if event.graph_span != 1:
            reasons.append("graph_span")
        if event.graph_lifetime != "single_vjp_call":
            reasons.append("graph_lifetime")
    return GateOutcome(
        gate_id="STRUCT-B1",
        passed=not reasons,
        reasons=tuple(sorted(set(reasons))),
    )


def _load_state_dict(path: Path) -> Mapping[str, torch.Tensor]:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    if isinstance(payload, dict):
        for key in ("model_state_dict", "state_dict"):
            candidate = payload.get(key)
            if isinstance(candidate, dict):
                return cast(Mapping[str, torch.Tensor], candidate)
        if all(isinstance(key, str) and torch.is_tensor(value) for key, value in payload.items()):
            return cast(Mapping[str, torch.Tensor], payload)
    raise ValueError(f"Unsupported checkpoint structure: {path}")


def _load_batch(path: Path) -> tuple[torch.Tensor, torch.Tensor]:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    if not isinstance(payload, dict):
        raise ValueError("Batch artifact must be a dictionary")
    inputs = payload.get("inputs")
    targets = payload.get("targets")
    split = payload.get("split")
    if split != "validation":
        raise ValueError("B1 smoke batch must come from the validation split")
    if not torch.is_tensor(inputs) or not torch.is_tensor(targets):
        raise ValueError("Batch artifact lacks tensor inputs/targets")
    return inputs, targets


def _resolve_device(control: LaneControl) -> torch.device:
    if control.device == "cpu":
        return torch.device("cpu")
    if control.device == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("ROCm lane requires torch.cuda.is_available()")
        return torch.device("cuda")
    raise ValueError(f"Unsupported lane device: {control.device}")


def _resolve_dtype(name: str) -> torch.dtype:
    if name == "float64":
        return torch.float64
    if name == "float32":
        return torch.float32
    raise ValueError(f"Unsupported lane dtype: {name}")


def _seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def _verify_asset(path: Path, expected_sha256: str) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)
    observed = sha256_file(path)
    if observed != expected_sha256:
        raise RuntimeError(
            f"Asset digest mismatch for {path}: expected {expected_sha256}, observed {observed}"
        )


def _pair_spec_dict(spec: PairSpec) -> dict[str, JsonValue]:
    return asdict(spec)


def _clone_optional(value: object) -> torch.Tensor | None:
    if value is None:
        return None
    if not torch.is_tensor(value):
        raise RuntimeError("State contains a non-tensor value")
    tensor = cast(torch.Tensor, value)
    return tensor.detach().clone()


def _require_equal(mapping: Mapping[str, Any], key: str, expected: Any) -> None:
    observed = mapping.get(key)
    if observed != expected:
        raise ValueError(f"{key}: expected {expected!r}, observed {observed!r}")


def _require_mapping(mapping: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = mapping.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be an object")
    return value


def _require_non_empty_string(mapping: Mapping[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _require_sha256(mapping: Mapping[str, Any], key: str) -> str:
    value = _require_non_empty_string(mapping, key)
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{key} must be a lowercase SHA-256 digest")
    return value


def _validate_asset(asset: Mapping[str, Any], label: str) -> None:
    path = asset.get("path")
    sha256 = asset.get("sha256")
    if not isinstance(path, str) or not path:
        raise ValueError(f"{label}.path must be non-empty")
    if (
        not isinstance(sha256, str)
        or len(sha256) != 64
        or any(character not in "0123456789abcdef" for character in sha256)
    ):
        raise ValueError(f"{label}.sha256 must be a lowercase SHA-256 digest")


def _validate_lane_control(
    controls: Mapping[str, Any],
    lane: str,
    device: str,
    dtype: str,
) -> None:
    control = _require_mapping(controls, lane)
    _require_equal(control, "device", device)
    _require_equal(control, "dtype", dtype)


def _asset_from_mapping(asset: Mapping[str, Any]) -> AssetRef:
    return AssetRef(path=str(asset["path"]), sha256=str(asset["sha256"]))
