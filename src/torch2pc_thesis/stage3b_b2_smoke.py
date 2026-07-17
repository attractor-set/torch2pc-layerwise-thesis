from __future__ import annotations

import copy
import csv
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
    B1ObserverMode,
    B1SweepSnapshot,
    load_b1_pc_infer,
)
from torch2pc_thesis.stage3b_b1_reference_trace import (
    reference_pc_infer_with_trace,
)
from torch2pc_thesis.stage3b_b2_composite_vjp import (
    B2CounterCollector,
    B2StructuralEvent,
    load_b2_pc_infer,
    load_patched_reference,
)

PROJECT_BASE_COMMIT = "f74a08818f653a27e8d04044cf59e2c2930b688c"
B1_IMPLEMENTATION_COMMIT = "ec12e9a"
B1_DECISION_COMMIT = "7c8df38084cd936b6c7d97afcc5685a497fdaf62"
B2_IMPLEMENTATION_COMMIT = "8a8a4559cda5f5750b05e14b614b95386329c952"
B2_IMPLEMENTATION_TAG = "stage3b-b2-composite-vjp-implementation-v1"
CANDIDATE_ID = "composite_vjp"
CONTROL_CANDIDATE_ID = "isolated_layer_vjp"
REFERENCE_ID = "stage2_baseline"
EXPECTED_METHODS = ("FixedPred", "Strict")
EXPECTED_LANES = ("cpu_float64", "rocm_float32")
EXPECTED_SEEDS = (0, 1, 2)
EXPECTED_MATCHED_TRIPLES = 12
EXPECTED_PAIRWISE_COMPARISONS = 24
GATE_IDS = ("STRUCT-B2", "NUM-B2", "TRAJ-B2", "OBS-B2", "PROV-B2")

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
    b1_decision: AssetRef
    b2_preregistration_contract: AssetRef
    b2_implementation_contract: AssetRef
    b2_harness_contract: AssetRef
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
    primary_trajectory_metrics: tuple[TensorMetric, ...]
    primary_endpoint_metrics: tuple[TensorMetric, ...]
    primary_scalar_metrics: tuple[ScalarMetric, ...]
    direct_trajectory_metrics: tuple[TensorMetric, ...]
    direct_endpoint_metrics: tuple[TensorMetric, ...]
    direct_scalar_metrics: tuple[ScalarMetric, ...]
    observer_trajectory_metrics: tuple[TensorMetric, ...]
    observer_endpoint_metrics: tuple[TensorMetric, ...]
    observer_scalar_metrics: tuple[ScalarMetric, ...]
    reference_guard_metrics: tuple[TensorMetric, ...]
    structural_events: tuple[B2StructuralEvent, ...]
    provenance: dict[str, JsonValue]

    def summary(self) -> dict[str, JsonValue]:
        return {
            "pair_id": self.pair_id,
            "pair_spec": self.pair_spec,
            "comparison_plan": {
                "primary": f"{REFERENCE_ID}_vs_{CANDIDATE_ID}",
                "required_direct_control": (
                    f"{CONTROL_CANDIDATE_ID}_vs_{CANDIDATE_ID}"
                ),
            },
            "gates": self.gates,
            "pair_admissible": self.pair_admissible,
            "structural_summary": {
                "sweeps_observed": len(self.structural_events),
                "composite_vjp_call_count": sum(
                    event.composite_vjp_call_count for event in self.structural_events
                ),
                "isolated_state_vjp_call_count": 0,
                "block_or_chunk_fallback_call_count": 0,
            },
            "provenance": self.provenance,
        }


def load_and_validate_request(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("B2 smoke request must be a JSON object")
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
    _require_equal(payload, "matched_triples", EXPECTED_MATCHED_TRIPLES)
    _require_equal(
        payload,
        "pairwise_comparisons",
        EXPECTED_PAIRWISE_COMPARISONS,
    )
    _require_equal(payload, "candidate_id", CANDIDATE_ID)
    _require_equal(payload, "control_candidate_id", CONTROL_CANDIDATE_ID)
    _require_equal(payload, "reference_id", REFERENCE_ID)
    _require_equal(payload, "observer_mode", "no_hooks")
    _require_equal(payload, "structural_observer_mode", "counters_only")
    _require_equal(payload, "test_split_access", False)
    _require_equal(payload, "dangerous_miss_limit", 0)
    _require_equal(payload, "torch2pc_commit", PATCHED_TORCH2PC_COMMIT)
    _require_equal(payload, "project_base_commit", PROJECT_BASE_COMMIT)
    _require_equal(payload, "b1_implementation_commit", B1_IMPLEMENTATION_COMMIT)
    _require_equal(payload, "b1_decision_commit", B1_DECISION_COMMIT)
    _require_equal(payload, "b2_implementation_commit", B2_IMPLEMENTATION_COMMIT)
    _require_equal(payload, "b2_implementation_tag", B2_IMPLEMENTATION_TAG)

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
        _validate_asset(
            _require_mapping(checkpoints, str(seed)),
            f"checkpoint[{seed}]",
        )
        _validate_asset(_require_mapping(batches, str(seed)), f"batch[{seed}]")

    for key in (
        "b1_decision",
        "b2_preregistration_contract",
        "b2_implementation_contract",
        "b2_harness_contract",
    ):
        _validate_asset(_require_mapping(payload, key), key)


def build_pair_specs(payload: Mapping[str, Any]) -> list[PairSpec]:
    validate_request(payload)
    checkpoints = _require_mapping(payload, "checkpoints")
    batches = _require_mapping(payload, "batches")
    method_controls = _require_mapping(payload, "method_controls")
    lane_controls = _require_mapping(payload, "lane_controls")
    request_id = cast(str, payload["request_id"])
    attempt_id = cast(str, payload["attempt_id"])
    b1_decision = _asset_from_mapping(_require_mapping(payload, "b1_decision"))
    b2_preregistration_contract = _asset_from_mapping(
        _require_mapping(payload, "b2_preregistration_contract")
    )
    b2_implementation_contract = _asset_from_mapping(
        _require_mapping(payload, "b2_implementation_contract")
    )
    b2_harness_contract = _asset_from_mapping(
        _require_mapping(payload, "b2_harness_contract")
    )

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
                        batch=_asset_from_mapping(_require_mapping(batches, str(seed))),
                        b1_decision=b1_decision,
                        b2_preregistration_contract=b2_preregistration_contract,
                        b2_implementation_contract=b2_implementation_contract,
                        b2_harness_contract=b2_harness_contract,
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

    if len(specs) != EXPECTED_MATCHED_TRIPLES:
        raise RuntimeError("B2 smoke request did not resolve to 12 matched triples")
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

    for asset in (
        spec.checkpoint,
        spec.batch,
        spec.b1_decision,
        spec.b2_preregistration_contract,
        spec.b2_implementation_contract,
        spec.b2_harness_contract,
    ):
        _verify_asset(Path(asset.path), asset.sha256)
    _validate_positive_b1_decision(Path(spec.b1_decision.path))

    model = model_builder("lenet_classic")
    model.load_state_dict(_load_state_dict(Path(spec.checkpoint.path)), strict=True)
    model.to(device=device, dtype=dtype)
    model.train(spec.training_mode)

    inputs, targets = _load_batch(Path(spec.batch.path))
    inputs = inputs.to(device=device, dtype=dtype)
    targets = targets.to(device=device)
    loss_fn = nn.CrossEntropyLoss()

    reference = load_patched_reference(torch2pc_dir)
    control_infer = load_b1_pc_infer(torch2pc_dir)
    candidate_infer = load_b2_pc_infer(torch2pc_dir)
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

    control_model = copy.deepcopy(model)
    control_snapshots: list[B1SweepSnapshot] = []
    restore_rng_snapshot(pair_rng)
    control_before = rng_snapshot_digest(capture_rng_snapshot())
    control_output = control_infer(
        control_model,
        loss_fn,
        inputs,
        targets,
        spec.method,
        eta=spec.method_control.eta,
        inference_steps=spec.method_control.inference_steps,
        observer_mode=B1ObserverMode.NO_HOOKS,
        trajectory_sink=control_snapshots.append,
    )
    control_endpoints = _capture_endpoints_from_output(
        control_model,
        control_output,
        spec.method_control.inference_steps,
        control_before,
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
    structural_snapshots: list[B1SweepSnapshot] = []
    structural_collector = B2CounterCollector()
    restore_rng_snapshot(pair_rng)
    structural_before = rng_snapshot_digest(capture_rng_snapshot())
    structural_output = candidate_infer(
        structural_model,
        loss_fn,
        inputs,
        targets,
        spec.method,
        eta=spec.method_control.eta,
        inference_steps=spec.method_control.inference_steps,
        observer_mode=B1ObserverMode.COUNTERS_ONLY,
        event_sink=structural_collector,
        trajectory_sink=structural_snapshots.append,
    )
    structural_endpoints = _capture_endpoints_from_output(
        structural_model,
        structural_output,
        spec.method_control.inference_steps,
        structural_before,
        rng_snapshot_digest(capture_rng_snapshot()),
    )

    primary_trajectory_metrics = tuple(
        compare_tensor_maps(
            flatten_trajectory(traced_snapshots),
            flatten_trajectory(candidate_snapshots),
            profile,
        )
    )
    primary_endpoint_metrics = tuple(
        compare_tensor_maps(
            _endpoint_tensor_map(traced_endpoints),
            _endpoint_tensor_map(candidate_endpoints),
            profile,
        )
    )
    primary_scalar_metrics = tuple(
        _endpoint_scalar_metrics(traced_endpoints, candidate_endpoints)
    )

    direct_trajectory_metrics = tuple(
        compare_tensor_maps(
            flatten_trajectory(control_snapshots),
            flatten_trajectory(candidate_snapshots),
            profile,
        )
    )
    direct_endpoint_metrics = tuple(
        compare_tensor_maps(
            _endpoint_tensor_map(control_endpoints),
            _endpoint_tensor_map(candidate_endpoints),
            profile,
        )
    )
    direct_scalar_metrics = tuple(
        _endpoint_scalar_metrics(control_endpoints, candidate_endpoints)
    )

    observer_trajectory_metrics = tuple(
        compare_tensor_maps(
            flatten_trajectory(candidate_snapshots),
            flatten_trajectory(structural_snapshots),
            profile,
        )
    )
    observer_endpoint_metrics = tuple(
        compare_tensor_maps(
            _endpoint_tensor_map(candidate_endpoints),
            _endpoint_tensor_map(structural_endpoints),
            profile,
        )
    )
    observer_scalar_metrics = tuple(
        _endpoint_scalar_metrics(candidate_endpoints, structural_endpoints)
    )

    reference_guard_metrics = tuple(
        compare_tensor_maps(
            _endpoint_tensor_map(traced_endpoints),
            _endpoint_tensor_map(canonical_endpoints),
            profile,
        )
    )

    structural_gate = _structural_gate(
        spec,
        structural_collector.events,
        len(model),
    )
    numerical_gate = _combined_metric_gate(
        "NUM-B2",
        primary_endpoint_metrics + direct_endpoint_metrics,
        primary_scalar_metrics + direct_scalar_metrics,
    )
    trajectory_gate = gate_from_tensor_metrics(
        "TRAJ-B2",
        primary_trajectory_metrics + direct_trajectory_metrics,
    )
    observer_gate = _combined_metric_gate(
        "OBS-B2",
        observer_trajectory_metrics + observer_endpoint_metrics,
        observer_scalar_metrics,
    )

    guard_gate = gate_from_tensor_metrics(
        "REFERENCE-TRACE-GUARD",
        reference_guard_metrics,
    )
    provenance_reasons: list[str] = []
    if not guard_gate.passed:
        provenance_reasons.append("canonical_reference_trace_guard_failed")
    if (
        len(
            {
                rng_before,
                traced_before,
                control_before,
                candidate_before,
                structural_before,
            }
        )
        != 1
    ):
        provenance_reasons.append("rng_restoration_mismatch")
    provenance_gate = GateOutcome(
        gate_id="PROV-B2",
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
        primary_trajectory_metrics=primary_trajectory_metrics,
        primary_endpoint_metrics=primary_endpoint_metrics,
        primary_scalar_metrics=primary_scalar_metrics,
        direct_trajectory_metrics=direct_trajectory_metrics,
        direct_endpoint_metrics=direct_endpoint_metrics,
        direct_scalar_metrics=direct_scalar_metrics,
        observer_trajectory_metrics=observer_trajectory_metrics,
        observer_endpoint_metrics=observer_endpoint_metrics,
        observer_scalar_metrics=observer_scalar_metrics,
        reference_guard_metrics=reference_guard_metrics,
        structural_events=tuple(structural_collector.events),
        provenance={
            "project_base_commit": PROJECT_BASE_COMMIT,
            "b1_implementation_commit": B1_IMPLEMENTATION_COMMIT,
            "b1_decision_commit": B1_DECISION_COMMIT,
            "b2_implementation_commit": B2_IMPLEMENTATION_COMMIT,
            "b2_implementation_tag": B2_IMPLEMENTATION_TAG,
            "torch2pc_commit": PATCHED_TORCH2PC_COMMIT,
            "candidate_id": CANDIDATE_ID,
            "control_candidate_id": CONTROL_CANDIDATE_ID,
            "reference_id": REFERENCE_ID,
            "request_id": spec.request_id,
            "attempt_id": spec.attempt_id,
            "resolved_config_digest": spec.resolved_config_digest,
            "source_image_digest": spec.source_image_digest,
            "checkpoint_sha256": spec.checkpoint.sha256,
            "batch_sha256": spec.batch.sha256,
            "b1_decision_sha256": spec.b1_decision.sha256,
            "b2_preregistration_contract_sha256": (
                spec.b2_preregistration_contract.sha256
            ),
            "b2_implementation_contract_sha256": (
                spec.b2_implementation_contract.sha256
            ),
            "b2_harness_contract_sha256": spec.b2_harness_contract.sha256,
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
        _tensor_metric_rows(
            result.pair_id,
            "reference_b2",
            "trajectory",
            result.primary_trajectory_metrics,
        )
        + _tensor_metric_rows(
            result.pair_id,
            "observer",
            "trajectory",
            result.observer_trajectory_metrics,
        ),
    )
    write_csv_rows(
        pair_dir / "endpoint-metrics.csv",
        _mixed_metric_rows(
            result.pair_id,
            "reference_b2",
            "endpoint",
            result.primary_endpoint_metrics,
            result.primary_scalar_metrics,
        )
        + _mixed_metric_rows(
            result.pair_id,
            "observer",
            "endpoint",
            result.observer_endpoint_metrics,
            result.observer_scalar_metrics,
        )
        + _mixed_metric_rows(
            result.pair_id,
            "reference_trace_guard",
            "endpoint",
            result.reference_guard_metrics,
            (),
        ),
    )
    write_csv_rows(
        pair_dir / "direct-b1-b2-metrics.csv",
        _mixed_metric_rows(
            result.pair_id,
            "b1_b2",
            "trajectory",
            result.direct_trajectory_metrics,
            (),
        )
        + _mixed_metric_rows(
            result.pair_id,
            "b1_b2",
            "endpoint",
            result.direct_endpoint_metrics,
            result.direct_scalar_metrics,
        ),
    )
    with (pair_dir / "structural-events.jsonl").open("w", encoding="utf-8") as stream:
        for event in result.structural_events:
            stream.write(json.dumps(event.to_dict(), sort_keys=True) + "\n")

    files = [
        pair_dir / "pair.json",
        pair_dir / "trajectory-metrics.csv",
        pair_dir / "endpoint-metrics.csv",
        pair_dir / "direct-b1-b2-metrics.csv",
        pair_dir / "structural-events.jsonl",
    ]
    (pair_dir / "SHA256SUMS").write_text(
        "".join(f"{sha256_file(path)} {path.name}\n" for path in files),
        encoding="utf-8",
    )
    return pair_dir


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
            f"Incomplete B2 smoke attempt: missing={missing}, unexpected={unexpected}"
        )

    aggregate_destinations = (
        attempt_root / "request.json",
        attempt_root / "resolved-config.json",
        attempt_root / "trajectory-metrics.csv",
        attempt_root / "endpoint-metrics.csv",
        attempt_root / "direct-b1-b2-metrics.csv",
        attempt_root / "structural-events.jsonl",
        attempt_root / "decision.json",
        attempt_root / "SHA256SUMS",
    )
    existing = [path for path in aggregate_destinations if path.exists()]
    if existing:
        raise FileExistsError(
            "Append-only aggregate artifact already exists: "
            + ", ".join(str(path) for path in existing)
        )

    summaries = [
        json.loads(path.read_text(encoding="utf-8")) for path in observed_files
    ]
    failed_pairs = sorted(
        str(summary["pair_id"])
        for summary in summaries
        if not bool(summary["pair_admissible"])
    )

    gates: dict[str, JsonValue] = {}
    for gate_id in GATE_IDS:
        failed = sorted(
            str(summary["pair_id"])
            for summary in summaries
            if not bool(summary["gates"][gate_id]["passed"])
        )
        gates[gate_id] = {"passed": not failed, "failed_pairs": failed}

    eq_pass = not failed_pairs and all(
        bool(cast(Mapping[str, Any], gates[gate_id])["passed"]) for gate_id in GATE_IDS
    )
    decision: dict[str, JsonValue] = {
        "decision_id": "EQ-B2",
        "status": "pass" if eq_pass else "fail",
        "candidate_id": CANDIDATE_ID,
        "control_candidate_id": CONTROL_CANDIDATE_ID,
        "reference_id": REFERENCE_ID,
        "dangerous_miss_limit": 0,
        "dangerous_misses": 0,
        "matched_triples_expected": EXPECTED_MATCHED_TRIPLES,
        "matched_triples_observed": len(summaries),
        "pairwise_comparisons_expected": EXPECTED_PAIRWISE_COMPARISONS,
        "pairwise_comparisons_observed": len(summaries) * 2,
        "failed_pairs": failed_pairs,
        "gates": gates,
        "request_digest": canonical_json_digest(request),
        "sealed": True,
    }

    atomic_write_json(attempt_root / "request.json", request)
    atomic_write_json(
        attempt_root / "resolved-config.json",
        _require_mapping(request, "resolved_config"),
    )
    _combine_csv_files(
        [path.parent / "trajectory-metrics.csv" for path in observed_files],
        attempt_root / "trajectory-metrics.csv",
    )
    _combine_csv_files(
        [path.parent / "endpoint-metrics.csv" for path in observed_files],
        attempt_root / "endpoint-metrics.csv",
    )
    _combine_csv_files(
        [path.parent / "direct-b1-b2-metrics.csv" for path in observed_files],
        attempt_root / "direct-b1-b2-metrics.csv",
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

    required = list(aggregate_destinations[:-1])
    (attempt_root / "SHA256SUMS").write_text(
        "".join(f"{sha256_file(path)} {path.name}\n" for path in required),
        encoding="utf-8",
    )
    return decision


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
        {
            f"endpoint/gradient/{name}": value
            for name, value in endpoints.gradients.items()
        }
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


def _endpoint_scalar_metrics(
    reference: RunEndpoints,
    candidate: RunEndpoints,
) -> list[ScalarMetric]:
    optimizer_metrics: list[ScalarMetric] = scalar_map_metrics(
        "optimizer",
        reference.optimizer.scalar_state,
        candidate.optimizer.scalar_state,
    )
    return optimizer_metrics + [
        ScalarMetric(
            component="inference_steps",
            passed=reference.inference_steps == candidate.inference_steps,
            reference=reference.inference_steps,
            candidate=candidate.inference_steps,
        ),
        ScalarMetric(
            component="rng_before",
            passed=reference.rng_before == candidate.rng_before,
            reference=reference.rng_before,
            candidate=candidate.rng_before,
        ),
        ScalarMetric(
            component="rng_after",
            passed=reference.rng_after == candidate.rng_after,
            reference=reference.rng_after,
            candidate=candidate.rng_after,
        ),
    ]


def _combined_metric_gate(
    gate_id: str,
    tensor_metrics: Sequence[TensorMetric],
    scalar_metrics: Sequence[ScalarMetric],
) -> GateOutcome:
    tensor_gate = gate_from_tensor_metrics(gate_id, tensor_metrics)
    scalar_gate = gate_from_scalar_metrics(gate_id, scalar_metrics)
    return GateOutcome(
        gate_id=gate_id,
        passed=tensor_gate.passed and scalar_gate.passed,
        reasons=tensor_gate.reasons + scalar_gate.reasons,
    )


def _structural_gate(
    spec: PairSpec,
    events: Sequence[B2StructuralEvent],
    model_depth: int,
) -> GateOutcome:
    expected_indices = (
        tuple(range(model_depth))
        if spec.method == "FixedPred"
        else tuple(range(1, model_depth))
    )
    expected_event_count = spec.method_control.inference_steps
    reasons: list[str] = []
    if len(events) != expected_event_count:
        reasons.append(f"event_count:{len(events)}!={expected_event_count}")

    observed_sweeps: list[int] = []
    for event in events:
        observed_sweeps.append(event.sweep_index)
        if event.candidate_id != CANDIDATE_ID:
            reasons.append("candidate_id")
        if event.method != spec.method:
            reasons.append("method")
        if event.layer_indices != expected_indices:
            reasons.append("graph_module_set")
        if event.logical_edge_count != len(expected_indices):
            reasons.append("logical_edge_count")
        if event.composite_vjp_call_count != 1:
            reasons.append("composite_vjp_call_count")
        if event.graph_span != len(expected_indices):
            reasons.append("graph_span")
        if event.graph_lifetime != "single_sweep_composite_vjp_call":
            reasons.append("graph_lifetime")

    if observed_sweeps != list(range(expected_event_count)):
        reasons.append("sweep_index_sequence")

    return GateOutcome(
        gate_id="STRUCT-B2",
        passed=not reasons,
        reasons=tuple(sorted(set(reasons))),
    )


def _tensor_metric_rows(
    pair_id: str,
    comparison: str,
    scope: str,
    metrics: Sequence[TensorMetric],
) -> list[dict[str, JsonScalar]]:
    return [
        {
            "pair_id": pair_id,
            "comparison": comparison,
            "scope": scope,
            "metric_kind": "tensor",
            **metric.to_row(),
            "reference_scalar": None,
            "candidate_scalar": None,
        }
        for metric in metrics
    ]


def _mixed_metric_rows(
    pair_id: str,
    comparison: str,
    scope: str,
    tensor_metrics: Sequence[TensorMetric],
    scalar_metrics: Sequence[ScalarMetric],
) -> list[dict[str, JsonScalar]]:
    rows = _tensor_metric_rows(pair_id, comparison, scope, tensor_metrics)
    for metric in scalar_metrics:
        rows.append(
            {
                "pair_id": pair_id,
                "comparison": comparison,
                "scope": scope,
                "metric_kind": "scalar",
                "component": metric.component,
                "passed": metric.passed,
                "finite": None,
                "presence_match": None,
                "reference_l2": None,
                "candidate_l2": None,
                "difference_l2": None,
                "relative_l2": None,
                "cosine": None,
                "max_abs": None,
                "zero_case": None,
                "reference_scalar": metric.reference,
                "candidate_scalar": metric.candidate,
            }
        )
    return rows


def _combine_csv_files(sources: Sequence[Path], destination: Path) -> None:
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


def _validate_positive_b1_decision(path: Path) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("B1 decision must be a JSON object")
    expected = {
        "decision_id": "EQ-B1",
        "status": "pass",
        "sealed": True,
    }
    for key, value in expected.items():
        if payload.get(key) != value:
            raise ValueError(f"B2 requires positive sealed EQ-B1: {key}")


def _load_state_dict(path: Path) -> Mapping[str, torch.Tensor]:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    if isinstance(payload, dict):
        for key in ("model_state_dict", "state_dict"):
            candidate = payload.get(key)
            if isinstance(candidate, dict):
                return cast(Mapping[str, torch.Tensor], candidate)
        if all(
            isinstance(key, str) and torch.is_tensor(value)
            for key, value in payload.items()
        ):
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
        raise ValueError("B2 smoke batch must come from the validation split")
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
            f"Asset digest mismatch for {path}: "
            f"expected {expected_sha256}, observed {observed}"
        )


def _pair_spec_dict(spec: PairSpec) -> dict[str, JsonValue]:
    return asdict(spec)


def _clone_optional(value: object) -> torch.Tensor | None:
    if value is None:
        return None
    if not torch.is_tensor(value):
        raise RuntimeError("State contains a non-tensor value")
    return cast(torch.Tensor, value).detach().clone()


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
    if len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
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
