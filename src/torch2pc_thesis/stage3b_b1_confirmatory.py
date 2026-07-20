"""Confirmatory Stage 3B B1 request, planning, and pair-attempt lifecycle.

This module extends the already validated B1 smoke comparison primitive to the
preregistered 120-pair confirmatory matrix.  It deliberately keeps runtime
authorization separate and writes append-only pair attempts so that recovery
semantics can be audited before evidence sealing.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Final, Literal, cast

import torch

from torch2pc_thesis.stage3b_b1_equivalence import (
    JsonScalar,
    JsonValue,
    atomic_write_json,
    canonical_json_digest,
    sha256_file,
    write_csv_rows,
)
from torch2pc_thesis.stage3b_b1_smoke import (
    AssetRef,
    LaneControl,
    MethodControl,
    PairResult,
    PairSpec,
)
from torch2pc_thesis.stage3b_b1_smoke import run_pair as run_b1_pair

B1_CONFIRMATORY_SCHEMA_VERSION: Final[int] = 1
B1_CONFIRMATORY_REQUEST_SCOPE: Final[str] = "stage3b_b1_confirmatory_request"
B1_CONFIRMATORY_CAMPAIGN_ID: Final[str] = "stage3b-b1-confirmatory-equivalence-v1"
B1_CONFIRMATORY_EXPECTED_PAIR_COUNT: Final[int] = 120
B1_CONFIRMATORY_ENGINEERING_SMOKE_PAIR_COUNT: Final[int] = 12
B1_CONFIRMATORY_EXPECTED_LANES: Final[tuple[str, ...]] = (
    "cpu_float64",
    "rocm_float32",
)
B1_CONFIRMATORY_EXPECTED_METHODS: Final[tuple[str, ...]] = (
    "FixedPred",
    "Strict",
)
B1_CONFIRMATORY_EXPECTED_SEEDS: Final[tuple[int, ...]] = (0, 1, 2)
B1_CONFIRMATORY_EXPECTED_BATCH_INDICES: Final[tuple[int, ...]] = tuple(range(10))
B1_CONFIRMATORY_MAX_ATTEMPTS: Final[int] = 2
B1_CONFIRMATORY_RECONCILE_ACKNOWLEDGEMENT: Final[str] = (
    "RECONCILE_STAGE3B_B1_CONFIRMATORY_ORPHANED_RUNNING_ATTEMPTS"
)
B1_CONFIRMATORY_GATE_IDS: Final[tuple[str, ...]] = (
    "STRUCT-B1",
    "NUM-B1",
    "TRAJ-B1",
    "OBS-B1",
    "PROV-B1",
)
B1_CONFIRMATORY_RETRYABLE_FAILURE_CLASSES: Final[frozenset[str]] = frozenset(
    {"infrastructure", "operator_interruption", "system_interruption"}
)
B1_CONFIRMATORY_NON_RETRYABLE_FAILURE_CLASSES: Final[frozenset[str]] = frozenset(
    {"correctness", "scientific", "provenance", "unknown"}
)

_SHA256_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[0-9a-f]{40}$")

PairState = Literal["pending", "running", "completed", "failed"]


class B1ConfirmatoryError(RuntimeError):
    """Base error for confirmatory request and lifecycle violations."""


class B1ConfirmatoryRetryableError(B1ConfirmatoryError):
    """Infrastructure interruption that may be retried within the attempt cap."""


class B1ConfirmatoryScientificError(B1ConfirmatoryError):
    """Scientific/correctness failure that must not be retried."""


class B1ConfirmatoryOperatorInterruption(B1ConfirmatoryRetryableError):
    """Explicit operator stop outside one active pair attempt."""


@dataclass(frozen=True)
class PairAttemptState:
    pair_id: str
    state: PairState
    attempt_count: int
    failed_attempt_count: int
    running_attempt_count: int
    completed_attempt_count: int
    retry_eligible: bool
    selected_for_execution: bool
    next_attempt_number: int | None

    def to_record(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ConfirmatoryPlan:
    request_id: str
    campaign_id: str
    lane: str | None
    engineering_smoke: bool
    resume: bool
    retry_failed: bool
    execution_performed: bool
    pair_count: int
    selected_pair_ids: tuple[str, ...]
    summary: dict[str, int]
    pairs: tuple[PairAttemptState, ...]

    def to_record(self) -> dict[str, object]:
        return {
            **asdict(self),
            "evidence": False,
            "results_publication_permitted": False,
            "test_dataset_access": False,
            "full_confirmatory_campaign_complete": False,
        }


def load_json_object(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise B1ConfirmatoryError(f"JSON root must be an object: {path}")
    return cast(dict[str, object], value)


def load_and_validate_confirmatory_request(path: Path) -> dict[str, object]:
    payload = load_json_object(path)
    validate_confirmatory_request(payload)
    return payload


def validate_confirmatory_request(payload: Mapping[str, object]) -> None:
    _require_equal(payload, "schema_version", B1_CONFIRMATORY_SCHEMA_VERSION)
    _require_equal(payload, "request_scope", B1_CONFIRMATORY_REQUEST_SCOPE)
    _require_equal(payload, "campaign_id", B1_CONFIRMATORY_CAMPAIGN_ID)
    _require_equal(payload, "scope", "confirmatory")
    _require_equal(payload, "dataset", "FashionMNIST")
    _require_equal(payload, "split", "validation")
    _require_equal(payload, "architecture", "lenet_classic")
    _require_equal(payload, "lanes", list(B1_CONFIRMATORY_EXPECTED_LANES))
    _require_equal(payload, "methods", list(B1_CONFIRMATORY_EXPECTED_METHODS))
    _require_equal(payload, "model_seeds", list(B1_CONFIRMATORY_EXPECTED_SEEDS))
    _require_equal(
        payload,
        "validation_batch_indices",
        list(B1_CONFIRMATORY_EXPECTED_BATCH_INDICES),
    )
    _require_equal(payload, "matched_pair_count", B1_CONFIRMATORY_EXPECTED_PAIR_COUNT)
    _require_equal(payload, "observer_mode", "no_hooks")
    _require_equal(payload, "structural_observer_mode", "counters_only")
    _require_equal(payload, "test_split_access", False)
    _require_equal(payload, "training_mode", True)
    _require_equal(payload, "max_attempts_per_pair", B1_CONFIRMATORY_MAX_ATTEMPTS)

    request_id = _require_path_safe_string(payload, "request_id")
    if not request_id.startswith("stage3b-b1-confirmatory-"):
        raise B1ConfirmatoryError("request_id must start with stage3b-b1-confirmatory-")
    _require_digest(payload, "contract_digest")
    _require_digest(payload, "resolved_config_digest")
    _require_commit(payload, "torch2pc_commit")

    resolved_config = _require_mapping(payload, "resolved_config")
    if canonical_json_digest(resolved_config) != payload["resolved_config_digest"]:
        raise B1ConfirmatoryError("resolved_config_digest does not match resolved_config")

    run_seed_base = payload.get("run_seed_base")
    if not isinstance(run_seed_base, int) or isinstance(run_seed_base, bool):
        raise B1ConfirmatoryError("run_seed_base must be an integer")
    if run_seed_base < 0:
        raise B1ConfirmatoryError("run_seed_base must be non-negative")

    optimizer = _require_mapping(payload, "optimizer")
    _require_equal(optimizer, "name", "SGD")
    _require_equal(optimizer, "learning_rate", 0.001)
    _require_equal(optimizer, "momentum", 0.0)

    method_controls = _require_mapping(payload, "method_controls")
    for method in B1_CONFIRMATORY_EXPECTED_METHODS:
        control = _require_mapping(method_controls, method)
        eta = control.get("eta")
        steps = control.get("inference_steps")
        if not isinstance(eta, int | float) or isinstance(eta, bool) or eta <= 0:
            raise B1ConfirmatoryError(f"{method}.eta must be positive")
        if not isinstance(steps, int) or isinstance(steps, bool) or steps < 1:
            raise B1ConfirmatoryError(f"{method}.inference_steps must be a positive integer")

    lane_controls = _require_mapping(payload, "lane_controls")
    _validate_lane(lane_controls, "cpu_float64", "cpu", "float64")
    _validate_lane(lane_controls, "rocm_float32", "cuda", "float32")

    checkpoints = _require_mapping(payload, "checkpoints")
    if set(checkpoints) != {str(seed) for seed in B1_CONFIRMATORY_EXPECTED_SEEDS}:
        raise B1ConfirmatoryError("checkpoints must contain exactly seeds 0, 1, and 2")
    for seed in B1_CONFIRMATORY_EXPECTED_SEEDS:
        _validate_asset(_require_mapping(checkpoints, str(seed)), f"checkpoint[{seed}]")

    batches = _require_mapping(payload, "validation_batches")
    expected_batch_keys = {str(index) for index in B1_CONFIRMATORY_EXPECTED_BATCH_INDICES}
    if set(batches) != expected_batch_keys:
        raise B1ConfirmatoryError("validation_batches must contain exactly indices 0 through 9")
    observed_content_digests: list[str] = []
    observed_paths: list[str] = []
    for batch_index in B1_CONFIRMATORY_EXPECTED_BATCH_INDICES:
        batch = _require_mapping(batches, str(batch_index))
        _validate_asset(batch, f"validation_batch[{batch_index}]")
        _require_equal(batch, "batch_index", batch_index)
        _require_equal(batch, "split", "validation")
        _require_equal(batch, "batch_size", 256)
        observed_content_digests.append(_require_digest(batch, "content_sha256"))
        path = batch.get("path")
        if not isinstance(path, str):
            raise B1ConfirmatoryError(f"validation_batch[{batch_index}].path must be a string")
        observed_paths.append(path)
    if len(set(observed_paths)) != 10:
        raise B1ConfirmatoryError("ten validation batch indices must reference ten distinct paths")
    if len(set(observed_content_digests)) != 10:
        raise B1ConfirmatoryError("ten validation batches must have ten distinct content digests")

    expected_pair_ids = [spec.pair_id for spec in build_pair_specs_unchecked(payload)]
    if len(expected_pair_ids) != B1_CONFIRMATORY_EXPECTED_PAIR_COUNT:
        raise B1ConfirmatoryError("request did not resolve to 120 matched pairs")
    if len(set(expected_pair_ids)) != B1_CONFIRMATORY_EXPECTED_PAIR_COUNT:
        raise B1ConfirmatoryError("request contains duplicate pair identities")


def build_pair_specs(payload: Mapping[str, object]) -> list[PairSpec]:
    validate_confirmatory_request(payload)
    return build_pair_specs_unchecked(payload)


def build_pair_specs_unchecked(payload: Mapping[str, object]) -> list[PairSpec]:
    checkpoints = _require_mapping(payload, "checkpoints")
    batches = _require_mapping(payload, "validation_batches")
    method_controls = _require_mapping(payload, "method_controls")
    lane_controls = _require_mapping(payload, "lane_controls")
    request_id = str(payload["request_id"])
    run_seed_base = int(cast(int, payload["run_seed_base"]))
    specs: list[PairSpec] = []
    for lane in B1_CONFIRMATORY_EXPECTED_LANES:
        lane_payload = _require_mapping(lane_controls, lane)
        for method in B1_CONFIRMATORY_EXPECTED_METHODS:
            method_payload = _require_mapping(method_controls, method)
            for seed in B1_CONFIRMATORY_EXPECTED_SEEDS:
                checkpoint = _asset_from_mapping(_require_mapping(checkpoints, str(seed)))
                for batch_index in B1_CONFIRMATORY_EXPECTED_BATCH_INDICES:
                    batch = _asset_from_mapping(_require_mapping(batches, str(batch_index)))
                    specs.append(
                        PairSpec(
                            request_id=request_id,
                            attempt_id="unassigned",
                            lane=lane,
                            method=method,
                            model_seed=seed,
                            batch_index=batch_index,
                            run_seed=run_seed_base + seed * 100 + batch_index,
                            checkpoint=checkpoint,
                            batch=batch,
                            method_control=MethodControl(
                                eta=float(cast(int | float, method_payload["eta"])),
                                inference_steps=cast(int, method_payload["inference_steps"]),
                            ),
                            lane_control=LaneControl(
                                device=str(lane_payload["device"]),
                                dtype=str(lane_payload["dtype"]),
                            ),
                            training_mode=True,
                            resolved_config_digest=str(payload["resolved_config_digest"]),
                            source_image_digest="unassigned",
                        )
                    )
    return specs


def resolve_spec_paths(spec: PairSpec, *, project_root: Path) -> PairSpec:
    root = project_root.expanduser().resolve()
    return replace(
        spec,
        checkpoint=AssetRef(
            path=str(_resolve_registered_path(root, spec.checkpoint.path)),
            sha256=spec.checkpoint.sha256,
        ),
        batch=AssetRef(
            path=str(_resolve_registered_path(root, spec.batch.path)),
            sha256=spec.batch.sha256,
        ),
    )


def select_specs(
    specs: Sequence[PairSpec],
    *,
    lane: str | None,
    engineering_smoke: bool,
) -> list[PairSpec]:
    if lane is not None and lane not in B1_CONFIRMATORY_EXPECTED_LANES:
        raise B1ConfirmatoryError(f"unsupported confirmatory lane: {lane}")
    selected = [spec for spec in specs if lane is None or spec.lane == lane]
    if engineering_smoke:
        selected = [spec for spec in selected if spec.batch_index == 0]
    return selected


def plan_confirmatory_lane(
    request: Mapping[str, object],
    *,
    output_root: Path,
    lane: str | None,
    engineering_smoke: bool,
    resume: bool,
    retry_failed: bool,
) -> ConfirmatoryPlan:
    specs = select_specs(
        build_pair_specs(request),
        lane=lane,
        engineering_smoke=engineering_smoke,
    )
    states = tuple(
        _inspect_pair_state(
            output_root=output_root,
            spec=spec,
            resume=resume,
            retry_failed=retry_failed,
        )
        for spec in specs
    )
    if retry_failed and not resume:
        raise B1ConfirmatoryError("retry_failed requires resume")
    if not resume and any(state.attempt_count > 0 for state in states):
        raise B1ConfirmatoryError("existing pair attempts require explicit resume")
    running = [state.pair_id for state in states if state.state == "running"]
    if running:
        raise B1ConfirmatoryError(
            "running attempts require explicit orphan reconciliation: " + ",".join(running)
        )
    non_retryable = [
        state.pair_id for state in states if state.state == "failed" and not state.retry_eligible
    ]
    if non_retryable:
        raise B1ConfirmatoryScientificError(
            "non-retryable pair failures block the campaign: " + ",".join(non_retryable)
        )
    retryable = [
        state.pair_id for state in states if state.state == "failed" and state.retry_eligible
    ]
    if retryable and not (resume and retry_failed):
        raise B1ConfirmatoryError(
            "retryable failures require --resume --retry-failed: " + ",".join(retryable)
        )
    summary_counter = Counter(state.state for state in states)
    selected = tuple(state.pair_id for state in states if state.selected_for_execution)
    return ConfirmatoryPlan(
        request_id=str(request["request_id"]),
        campaign_id=str(request["campaign_id"]),
        lane=lane,
        engineering_smoke=engineering_smoke,
        resume=resume,
        retry_failed=retry_failed,
        execution_performed=False,
        pair_count=len(states),
        selected_pair_ids=selected,
        summary={key: summary_counter[key] for key in sorted(summary_counter)},
        pairs=states,
    )


def reconcile_orphaned_running_attempts(
    request: Mapping[str, object],
    *,
    output_root: Path,
    lane: str,
    authorization_token: str,
    project_source_commit: str,
    source_image_digest: str,
    operator_acknowledgement: str,
) -> list[str]:
    """Close orphaned started attempts after an independently verified process stop."""
    validate_confirmatory_request(request)
    if operator_acknowledgement != B1_CONFIRMATORY_RECONCILE_ACKNOWLEDGEMENT:
        raise B1ConfirmatoryError("orphan reconciliation acknowledgement mismatch")
    root = output_root.expanduser().resolve()
    lock_path = root / "locks" / f"{lane}.lock"
    if lock_path.exists():
        raise B1ConfirmatoryError(f"cannot reconcile while lane lock exists: {lock_path}")
    request_digest = canonical_json_digest(request)
    reconciled: list[str] = []
    for spec in select_specs(build_pair_specs(request), lane=lane, engineering_smoke=False):
        attempts_root = _pair_attempts_root(root, spec.pair_id)
        attempt_dirs = sorted(path for path in attempts_root.glob("attempt-*") if path.is_dir())
        if len(attempt_dirs) > B1_CONFIRMATORY_MAX_ATTEMPTS:
            raise B1ConfirmatoryError(f"pair exceeds max attempts: {spec.pair_id}")
        running_dirs = [
            path
            for path in attempt_dirs
            if (path / "started.json").is_file()
            and not (path / "completed.json").exists()
            and not (path / "failed.json").exists()
        ]
        if len(running_dirs) > 1:
            raise B1ConfirmatoryError(f"multiple orphaned running attempts: {spec.pair_id}")
        for attempt_number, attempt_dir in enumerate(attempt_dirs, start=1):
            if attempt_dir.name != f"attempt-{attempt_number:03d}":
                raise B1ConfirmatoryError(f"non-contiguous attempt sequence: {spec.pair_id}")
            started_path = attempt_dir / "started.json"
            if not started_path.is_file():
                continue
            if (attempt_dir / "completed.json").exists() or (attempt_dir / "failed.json").exists():
                continue
            started = load_json_object(started_path)
            expected = {
                "pair_id": spec.pair_id,
                "attempt_number": attempt_number,
                "request_digest": request_digest,
                "project_source_commit": project_source_commit,
                "source_image_digest": source_image_digest,
                "authorization_token": authorization_token,
                "evidence": False,
                "test_dataset_access": False,
            }
            for key, value in expected.items():
                if started.get(key) != value:
                    raise B1ConfirmatoryError(
                        f"orphan attempt provenance mismatch: {spec.pair_id} {key}"
                    )
            failed = {
                **started,
                "status": "failed",
                "failure_class": "system_interruption",
                "retry_eligible": True,
                "reconciled_orphan": True,
                "operator_acknowledgement": operator_acknowledgement,
            }
            atomic_write_json(attempt_dir / "failed.json", failed)
            reconciled.append(f"{spec.pair_id}/{attempt_dir.name}")
    return reconciled


def run_confirmatory_pair_attempt(
    spec: PairSpec,
    *,
    project_root: Path,
    torch2pc_dir: Path,
    output_root: Path,
    request_digest: str,
    authorization_token: str,
    model_builder: Any,
    project_source_commit: str,
    source_image_digest: str,
) -> dict[str, object]:
    state = _inspect_pair_state(
        output_root=output_root,
        spec=spec,
        resume=True,
        retry_failed=True,
    )
    if state.next_attempt_number is None or not state.selected_for_execution:
        raise B1ConfirmatoryError(f"pair is not executable: {spec.pair_id}")
    attempt_number = state.next_attempt_number
    attempt_id = f"attempt-{attempt_number:03d}"
    attempt_dir = _pair_attempts_root(output_root, spec.pair_id) / attempt_id
    if attempt_dir.exists():
        raise B1ConfirmatoryError(f"append-only attempt already exists: {attempt_dir}")
    attempt_dir.mkdir(parents=True)

    resolved_spec = replace(
        resolve_spec_paths(spec, project_root=project_root),
        attempt_id=attempt_id,
        source_image_digest=source_image_digest,
    )
    provenance = _attempt_provenance(
        resolved_spec,
        request_digest=request_digest,
        authorization_token=authorization_token,
        attempt_number=attempt_number,
        project_source_commit=project_source_commit,
    )
    atomic_write_json(attempt_dir / "started.json", provenance)
    try:
        result = run_b1_pair(
            resolved_spec,
            torch2pc_dir=torch2pc_dir,
            model_builder=model_builder,
        )
        _write_attempt_result(attempt_dir, result)
        if not result.pair_admissible:
            failed = {
                **provenance,
                "status": "failed",
                "failure_class": "correctness",
                "retry_eligible": False,
                "failed_gates": sorted(
                    gate_id for gate_id, gate in result.gates.items() if not bool(gate["passed"])
                ),
            }
            atomic_write_json(attempt_dir / "failed.json", failed)
            raise B1ConfirmatoryScientificError(
                f"confirmatory pair failed correctness gates: {spec.pair_id}"
            )
        completed = {
            **provenance,
            "status": "completed",
            "pair_admissible": True,
            "result_sha256": sha256_file(attempt_dir / "result" / "pair.json"),
        }
        atomic_write_json(attempt_dir / "completed.json", completed)
        return completed
    except B1ConfirmatoryScientificError:
        raise
    except (KeyboardInterrupt, SystemExit):
        interrupted = {
            **provenance,
            "status": "failed",
            "failure_class": "operator_interruption",
            "retry_eligible": True,
        }
        atomic_write_json(attempt_dir / "failed.json", interrupted)
        raise
    except (B1ConfirmatoryRetryableError, OSError, torch.cuda.OutOfMemoryError) as error:
        failed = {
            **provenance,
            "status": "failed",
            "failure_class": "infrastructure",
            "retry_eligible": True,
            "error": str(error),
        }
        atomic_write_json(attempt_dir / "failed.json", failed)
        raise
    except Exception as error:
        failed = {
            **provenance,
            "status": "failed",
            "failure_class": "unknown",
            "retry_eligible": False,
            "error_type": type(error).__name__,
            "error": str(error),
        }
        atomic_write_json(attempt_dir / "failed.json", failed)
        raise


def _inspect_pair_state(
    *,
    output_root: Path,
    spec: PairSpec,
    resume: bool,
    retry_failed: bool,
) -> PairAttemptState:
    attempts_root = _pair_attempts_root(output_root, spec.pair_id)
    attempt_dirs = sorted(path for path in attempts_root.glob("attempt-*") if path.is_dir())
    if len(attempt_dirs) > B1_CONFIRMATORY_MAX_ATTEMPTS:
        raise B1ConfirmatoryError(f"pair exceeds max attempts: {spec.pair_id}")

    completed: list[Path] = []
    failed: list[Path] = []
    running: list[Path] = []
    for attempt_number, attempt_dir in enumerate(attempt_dirs, start=1):
        expected_name = f"attempt-{attempt_number:03d}"
        if attempt_dir.name != expected_name:
            raise B1ConfirmatoryError(f"non-contiguous attempt sequence: {spec.pair_id}")
        started_path = attempt_dir / "started.json"
        if not started_path.is_file():
            raise B1ConfirmatoryError(f"attempt lacks started marker: {attempt_dir}")
        completed_path = attempt_dir / "completed.json"
        failed_path = attempt_dir / "failed.json"
        if completed_path.exists() and failed_path.exists():
            raise B1ConfirmatoryError(f"attempt has multiple terminal markers: {attempt_dir}")
        if completed_path.is_file():
            completed.append(attempt_dir)
            continue
        if failed_path.is_file():
            marker = load_json_object(failed_path)
            failure_class = marker.get("failure_class")
            retry_eligible = marker.get("retry_eligible")
            known_failure = (
                B1_CONFIRMATORY_RETRYABLE_FAILURE_CLASSES
                | B1_CONFIRMATORY_NON_RETRYABLE_FAILURE_CLASSES
            )
            if failure_class not in known_failure:
                raise B1ConfirmatoryError(f"attempt has invalid failure class: {attempt_dir}")
            expected_retry = failure_class in B1_CONFIRMATORY_RETRYABLE_FAILURE_CLASSES
            if retry_eligible is not expected_retry:
                raise B1ConfirmatoryError(f"attempt retry classification mismatch: {attempt_dir}")
            failed.append(attempt_dir)
            continue
        running.append(attempt_dir)

    if len(completed) > 1:
        raise B1ConfirmatoryError(f"multiple completed attempts for pair {spec.pair_id}")
    if completed:
        if completed[0] != attempt_dirs[-1]:
            raise B1ConfirmatoryError(f"completed attempt must be last: {spec.pair_id}")
        if running:
            raise B1ConfirmatoryError(f"running attempt follows completion: {spec.pair_id}")
        return PairAttemptState(
            pair_id=spec.pair_id,
            state="completed",
            attempt_count=len(attempt_dirs),
            failed_attempt_count=len(failed),
            running_attempt_count=0,
            completed_attempt_count=1,
            retry_eligible=False,
            selected_for_execution=False,
            next_attempt_number=None,
        )
    if len(running) > 1 or (running and running[0] != attempt_dirs[-1]):
        raise B1ConfirmatoryError(f"invalid running attempt history: {spec.pair_id}")
    if running:
        return PairAttemptState(
            pair_id=spec.pair_id,
            state="running",
            attempt_count=len(attempt_dirs),
            failed_attempt_count=len(failed),
            running_attempt_count=1,
            completed_attempt_count=0,
            retry_eligible=False,
            selected_for_execution=False,
            next_attempt_number=None,
        )
    if failed:
        last_failure = load_json_object(failed[-1] / "failed.json")
        retry_eligible = bool(last_failure["retry_eligible"])
        selected = (
            resume
            and retry_failed
            and retry_eligible
            and len(attempt_dirs) < B1_CONFIRMATORY_MAX_ATTEMPTS
        )
        return PairAttemptState(
            pair_id=spec.pair_id,
            state="failed",
            attempt_count=len(attempt_dirs),
            failed_attempt_count=len(failed),
            running_attempt_count=0,
            completed_attempt_count=0,
            retry_eligible=retry_eligible,
            selected_for_execution=selected,
            next_attempt_number=len(attempt_dirs) + 1 if selected else None,
        )
    return PairAttemptState(
        pair_id=spec.pair_id,
        state="pending",
        attempt_count=0,
        failed_attempt_count=0,
        running_attempt_count=0,
        completed_attempt_count=0,
        retry_eligible=False,
        selected_for_execution=True,
        next_attempt_number=1,
    )


def _write_attempt_result(attempt_dir: Path, result: PairResult) -> None:
    result_dir = attempt_dir / "result"
    if result_dir.exists():
        raise B1ConfirmatoryError(f"append-only result already exists: {result_dir}")
    result_dir.mkdir()
    atomic_write_json(result_dir / "pair.json", result.summary())
    write_csv_rows(
        result_dir / "trajectory-metrics.csv",
        ({"pair_id": result.pair_id, **metric.to_row()} for metric in result.trajectory_metrics),
    )
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
    write_csv_rows(result_dir / "endpoint-metrics.csv", rows)
    with (result_dir / "structural-events.jsonl").open("w", encoding="utf-8") as stream:
        for event in result.structural_events:
            stream.write(json.dumps(event.to_dict(), sort_keys=True) + "\n")
    required = (
        result_dir / "pair.json",
        result_dir / "trajectory-metrics.csv",
        result_dir / "endpoint-metrics.csv",
        result_dir / "structural-events.jsonl",
    )
    (result_dir / "SHA256SUMS").write_text(
        "".join(f"{sha256_file(path)}  {path.name}\n" for path in required),
        encoding="utf-8",
    )


def _attempt_provenance(
    spec: PairSpec,
    *,
    request_digest: str,
    authorization_token: str,
    attempt_number: int,
    project_source_commit: str,
) -> dict[str, JsonValue]:
    return {
        "schema_version": 1,
        "campaign_id": B1_CONFIRMATORY_CAMPAIGN_ID,
        "pair_id": spec.pair_id,
        "lane": spec.lane,
        "method": spec.method,
        "model_seed": spec.model_seed,
        "validation_batch_index": spec.batch_index,
        "attempt_id": spec.attempt_id,
        "attempt_number": attempt_number,
        "request_id": spec.request_id,
        "request_digest": request_digest,
        "project_source_commit": project_source_commit,
        "authorization_token": authorization_token,
        "source_image_digest": spec.source_image_digest,
        "resolved_config_digest": spec.resolved_config_digest,
        "checkpoint_sha256": spec.checkpoint.sha256,
        "batch_sha256": spec.batch.sha256,
        "evidence": False,
        "test_dataset_access": False,
    }


def _pair_attempts_root(output_root: Path, pair_id: str) -> Path:
    return output_root.expanduser().resolve() / "pairs" / pair_id / "attempts"


def _resolve_registered_path(project_root: Path, registered: str) -> Path:
    candidate = Path(registered)
    resolved = (
        candidate.expanduser().resolve()
        if candidate.is_absolute()
        else (project_root / candidate).resolve()
    )
    try:
        resolved.relative_to(project_root)
    except ValueError as error:
        raise B1ConfirmatoryError(f"registered asset escapes project root: {registered}") from error
    return resolved


def _asset_from_mapping(value: Mapping[str, object]) -> AssetRef:
    return AssetRef(path=str(value["path"]), sha256=str(value["sha256"]))


def _validate_asset(value: Mapping[str, object], label: str) -> None:
    path = value.get("path")
    if not isinstance(path, str) or not path:
        raise B1ConfirmatoryError(f"{label}.path must be non-empty")
    _require_digest(value, "sha256")


def _validate_lane(
    lane_controls: Mapping[str, object],
    lane: str,
    device: str,
    dtype: str,
) -> None:
    control = _require_mapping(lane_controls, lane)
    _require_equal(control, "device", device)
    _require_equal(control, "dtype", dtype)


def _require_mapping(mapping: Mapping[str, object], key: str) -> Mapping[str, object]:
    value = mapping.get(key)
    if not isinstance(value, dict):
        raise B1ConfirmatoryError(f"{key} must be an object")
    return cast(Mapping[str, object], value)


def _require_equal(mapping: Mapping[str, object], key: str, expected: object) -> None:
    observed = mapping.get(key)
    if observed != expected:
        raise B1ConfirmatoryError(f"{key}: expected {expected!r}, observed {observed!r}")


def _require_path_safe_string(mapping: Mapping[str, object], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise B1ConfirmatoryError(f"{key} must be a non-empty string")
    if "/" in value or "\\" in value or value in {".", ".."}:
        raise B1ConfirmatoryError(f"{key} must be path-safe")
    return value


def _require_digest(mapping: Mapping[str, object], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not _SHA256_PATTERN.fullmatch(value):
        raise B1ConfirmatoryError(f"{key} must be a lowercase SHA-256 digest")
    return value


def _require_commit(mapping: Mapping[str, object], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not _COMMIT_PATTERN.fullmatch(value):
        raise B1ConfirmatoryError(f"{key} must be a 40-character Git commit")
    return value
