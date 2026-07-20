"""Seal one complete confirmatory Stage 3B B2 campaign."""

from __future__ import annotations

import csv
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Final, cast

from torch2pc_thesis.stage3b_b1_equivalence import (
    JsonScalar,
    JsonValue,
    atomic_write_json,
    canonical_json_digest,
    sha256_file,
    write_csv_rows,
)
from torch2pc_thesis.stage3b_b2_confirmatory import (
    B2_CONFIRMATORY_CAMPAIGN_ID,
    B2_CONFIRMATORY_EXPECTED_COMPARISON_COUNT,
    B2_CONFIRMATORY_EXPECTED_TRIPLE_COUNT,
    B2_CONFIRMATORY_GATE_IDS,
    B2_CONFIRMATORY_MAX_ATTEMPTS,
    B2_CONFIRMATORY_RETRYABLE_FAILURE_CLASSES,
    B2ConfirmatoryError,
    build_triple_specs,
    load_json_object,
    validate_confirmatory_request,
)
from torch2pc_thesis.stage3b_b2_confirmatory_authorization import (
    validate_authorization,
)
from torch2pc_thesis.stage3b_b2_smoke import PairSpec

B2_CONFIRMATORY_DECISION_ID: Final[str] = "EQ-B2-CONFIRMATORY"
B2_MATCHED_ADMISSION_DECISION_ID: Final[str] = "EQ-B2"
B2_CONFIRMATORY_SEAL_SCHEMA_VERSION: Final[int] = 1


class B2ConfirmatorySealingError(B2ConfirmatoryError):
    """Raised when append-only confirmatory evidence cannot be sealed."""


def seal_b2_confirmatory_campaign(
    request: Mapping[str, object],
    authorization: Mapping[str, object],
    *,
    output_root: Path,
) -> dict[str, JsonValue]:
    validate_confirmatory_request(request)
    validate_authorization(authorization)
    if authorization.get("execution_mode") != "confirmatory":
        raise B2ConfirmatorySealingError(
            "engineering-smoke authorization cannot seal confirmatory evidence"
        )
    root = output_root.expanduser().resolve()
    if str(root) != authorization["output_root"]:
        raise B2ConfirmatorySealingError("authorization output root mismatch")
    if canonical_json_digest(request) != authorization["request_digest"]:
        raise B2ConfirmatorySealingError("authorization request digest mismatch")
    decision_path = root / "sealed" / "decision.json"
    if decision_path.exists():
        raise B2ConfirmatorySealingError(
            f"append-only decision already exists: {decision_path}"
        )

    specs = build_triple_specs(request)
    if len(specs) != B2_CONFIRMATORY_EXPECTED_TRIPLE_COUNT:
        raise B2ConfirmatorySealingError("request does not contain 120 triples")

    triple_summaries: list[dict[str, object]] = []
    attempt_history: list[dict[str, object]] = []
    trajectory_sources: list[Path] = []
    endpoint_sources: list[Path] = []
    direct_sources: list[Path] = []
    structural_sources: list[tuple[str, Path]] = []

    for spec in specs:
        completed_dir, history = _validate_triple_attempt_history(
            root=root,
            spec=spec,
            request_digest=str(authorization["request_digest"]),
            authorization_token=str(authorization["authorization_token"]),
            project_source_commit=str(authorization["project_source_commit"]),
            source_image_digest=str(authorization["image_digest"]),
        )
        attempt_history.extend(history)
        result_dir = completed_dir / "result"
        _verify_sha256_registry(result_dir)
        triple = load_json_object(result_dir / "triple.json")
        _validate_triple_result(
            triple,
            spec=spec,
            source_image_digest=str(authorization["image_digest"]),
            torch2pc_commit=str(authorization["torch2pc_commit"]),
        )
        triple_summaries.append(triple)
        trajectory_sources.append(result_dir / "trajectory-metrics.csv")
        endpoint_sources.append(result_dir / "endpoint-metrics.csv")
        direct_sources.append(result_dir / "direct-b1-b2-metrics.csv")
        structural_sources.append(
            (spec.pair_id, result_dir / "structural-events.jsonl")
        )

    observed_ids = {str(item["triple_id"]) for item in triple_summaries}
    expected_ids = {spec.pair_id for spec in specs}
    if observed_ids != expected_ids:
        raise B2ConfirmatorySealingError("sealed triple identity set mismatch")

    gate_results: dict[str, JsonValue] = {}
    for gate_id in B2_CONFIRMATORY_GATE_IDS:
        failed = sorted(
            str(item["triple_id"])
            for item in triple_summaries
            if not _triple_gate_passed(item, gate_id)
        )
        gate_results[gate_id] = {
            "passed": not failed,
            "failed_triples": failed,
        }
    failed_triples = sorted(
        str(item["triple_id"])
        for item in triple_summaries
        if item.get("pair_admissible") is not True
    )
    all_passed = not failed_triples and all(
        cast(Mapping[str, object], gate_results[gate_id]).get("passed") is True
        for gate_id in B2_CONFIRMATORY_GATE_IDS
    )
    if not all_passed:
        raise B2ConfirmatorySealingError(
            "confirmatory sealing requires all 120 triples and all gates to pass"
        )

    sealed_root = root / "sealed"
    sealed_root.mkdir(parents=True, exist_ok=False)
    atomic_write_json(sealed_root / "request.json", request)
    atomic_write_json(sealed_root / "authorization.json", authorization)
    atomic_write_json(
        sealed_root / "resolved-config.json",
        cast(Mapping[str, object], request["resolved_config"]),
    )
    _write_jsonl(sealed_root / "attempt-history.jsonl", attempt_history)
    _combine_csv_files(
        trajectory_sources,
        sealed_root / "trajectory-metrics.csv",
    )
    _combine_csv_files(endpoint_sources, sealed_root / "endpoint-metrics.csv")
    _combine_csv_files(direct_sources, sealed_root / "direct-b1-b2-metrics.csv")
    _combine_structural_events(
        structural_sources,
        sealed_root / "structural-events.jsonl",
    )

    decision: dict[str, JsonValue] = {
        "schema_version": B2_CONFIRMATORY_SEAL_SCHEMA_VERSION,
        "decision_id": B2_CONFIRMATORY_DECISION_ID,
        "scope": "confirmatory",
        "confirmatory_equivalence_executed": True,
        "status": "pass",
        "sealed": True,
        "candidate_id": "composite_vjp",
        "control_candidate_id": "isolated_layer_vjp",
        "reference_id": "stage2_baseline",
        "matched_triples_expected": B2_CONFIRMATORY_EXPECTED_TRIPLE_COUNT,
        "matched_triples_observed": len(triple_summaries),
        "pairwise_comparisons_expected": B2_CONFIRMATORY_EXPECTED_COMPARISON_COUNT,
        "pairwise_comparisons_observed": 2 * len(triple_summaries),
        "failed_pair_count": 0,
        "failed_pairs": [],
        "failed_triples": [],
        "dangerous_miss_limit": 0,
        "dangerous_misses": 0,
        "gates": gate_results,
        "request_id": str(request["request_id"]),
        "request_digest": canonical_json_digest(request),
        "authorization_token": str(authorization["authorization_token"]),
        "project_source_commit": str(authorization["project_source_commit"]),
        "torch2pc_commit": str(authorization["torch2pc_commit"]),
        "image_digest": str(authorization["image_digest"]),
        "independent_unit": "model_seed",
        "test_dataset_access": False,
        "results_publication_permitted": False,
        "production_admission_effect": (
            "permits a new versioned matched-profiling scientific-admission "
            "freeze only; does not authorize 288-cell execution"
        ),
    }
    atomic_write_json(decision_path, decision)

    admission_path = sealed_root / "matched-profiling-admission.json"
    admission: dict[str, JsonValue] = {
        "schema_version": B2_CONFIRMATORY_SEAL_SCHEMA_VERSION,
        "decision_id": B2_MATCHED_ADMISSION_DECISION_ID,
        "source_decision_id": B2_CONFIRMATORY_DECISION_ID,
        "source_decision_path": decision_path.name,
        "source_decision_sha256": sha256_file(decision_path),
        "scope": "confirmatory",
        "confirmatory_equivalence_executed": True,
        "status": "pass",
        "sealed": True,
        "candidate_id": "composite_vjp",
        "control_candidate_id": "isolated_layer_vjp",
        "reference_id": "stage2_baseline",
        "matched_triples_expected": B2_CONFIRMATORY_EXPECTED_TRIPLE_COUNT,
        "matched_triples_observed": len(triple_summaries),
        "pairwise_comparisons_expected": B2_CONFIRMATORY_EXPECTED_COMPARISON_COUNT,
        "pairwise_comparisons_observed": 2 * len(triple_summaries),
        "failed_pairs": [],
        "failed_triples": [],
        "gates": gate_results,
        "request_digest": canonical_json_digest(request),
        "authorization_token": str(authorization["authorization_token"]),
        "project_source_commit": str(authorization["project_source_commit"]),
        "torch2pc_commit": str(authorization["torch2pc_commit"]),
        "image_digest": str(authorization["image_digest"]),
        "test_dataset_access": False,
        "results_publication_permitted": False,
        "production_admission_effect": (
            "permits a new versioned matched-profiling scientific-admission "
            "freeze only; does not authorize 288-cell execution"
        ),
    }
    atomic_write_json(admission_path, admission)

    seal_files = (
        sealed_root / "request.json",
        sealed_root / "authorization.json",
        sealed_root / "resolved-config.json",
        sealed_root / "attempt-history.jsonl",
        sealed_root / "trajectory-metrics.csv",
        sealed_root / "endpoint-metrics.csv",
        sealed_root / "direct-b1-b2-metrics.csv",
        sealed_root / "structural-events.jsonl",
        decision_path,
        admission_path,
    )
    (sealed_root / "SHA256SUMS").write_text(
        "".join(f"{sha256_file(path)}  {path.name}\n" for path in seal_files),
        encoding="utf-8",
    )
    decision["matched_profiling_admission_path"] = admission_path.name
    decision["matched_profiling_admission_sha256"] = sha256_file(admission_path)
    decision["seal_digest"] = sha256_file(sealed_root / "SHA256SUMS")
    return decision


def _triple_gate_passed(triple: Mapping[str, object], gate_id: str) -> bool:
    gates = triple.get("gates")
    if not isinstance(gates, dict):
        return False
    gate = gates.get(gate_id)
    return isinstance(gate, dict) and gate.get("passed") is True


def _validate_triple_result(
    triple: Mapping[str, object],
    *,
    spec: PairSpec,
    source_image_digest: str,
    torch2pc_commit: str,
) -> None:
    if triple.get("pair_id") != spec.pair_id:
        raise B2ConfirmatorySealingError(
            f"pair result identity mismatch: {spec.pair_id}"
        )
    if triple.get("triple_id") != spec.pair_id:
        raise B2ConfirmatorySealingError(
            f"triple result identity mismatch: {spec.pair_id}"
        )
    if triple.get("pairwise_comparison_count") != 2:
        raise B2ConfirmatorySealingError(
            f"comparison count mismatch: {spec.pair_id}"
        )
    if triple.get("pair_admissible") is not True:
        raise B2ConfirmatorySealingError(
            f"completed triple is not admissible: {spec.pair_id}"
        )
    gates = triple.get("gates")
    if not isinstance(gates, dict):
        raise B2ConfirmatorySealingError(
            f"triple gates are missing: {spec.pair_id}"
        )
    for gate_id in B2_CONFIRMATORY_GATE_IDS:
        gate = gates.get(gate_id)
        if not isinstance(gate, dict) or gate.get("passed") is not True:
            raise B2ConfirmatorySealingError(
                f"triple gate failed or missing: {spec.pair_id} {gate_id}"
            )
    comparison_plan = triple.get("comparison_plan")
    if not isinstance(comparison_plan, dict):
        raise B2ConfirmatorySealingError(
            f"comparison plan is missing: {spec.pair_id}"
        )
    if comparison_plan.get("primary") != "stage2_baseline_vs_composite_vjp":
        raise B2ConfirmatorySealingError(
            f"primary comparison mismatch: {spec.pair_id}"
        )
    if (
        comparison_plan.get("required_direct_control")
        != "isolated_layer_vjp_vs_composite_vjp"
    ):
        raise B2ConfirmatorySealingError(
            f"direct comparison mismatch: {spec.pair_id}"
        )
    pair_spec = triple.get("pair_spec")
    if not isinstance(pair_spec, dict):
        raise B2ConfirmatorySealingError(
            f"triple spec is missing: {spec.pair_id}"
        )
    expected_spec = {
        "lane": spec.lane,
        "method": spec.method,
        "model_seed": spec.model_seed,
        "batch_index": spec.batch_index,
    }
    for key, value in expected_spec.items():
        if pair_spec.get(key) != value:
            raise B2ConfirmatorySealingError(
                f"triple spec mismatch: {spec.pair_id} {key}"
            )
    provenance = triple.get("provenance")
    if not isinstance(provenance, dict):
        raise B2ConfirmatorySealingError(
            f"triple provenance is missing: {spec.pair_id}"
        )
    expected_provenance = {
        "request_id": spec.request_id,
        "resolved_config_digest": spec.resolved_config_digest,
        "source_image_digest": source_image_digest,
        "torch2pc_commit": torch2pc_commit,
        "checkpoint_sha256": spec.checkpoint.sha256,
        "batch_sha256": spec.batch.sha256,
        "b1_confirmatory_decision_sha256": (
            spec.b1_confirmatory_decision.sha256
        ),
        "b1_admission_sha256": spec.b1_admission.sha256,
        "b2_preregistration_contract_sha256": (
            spec.b2_preregistration_contract.sha256
        ),
        "b2_implementation_contract_sha256": (
            spec.b2_implementation_contract.sha256
        ),
        "b2_harness_contract_sha256": spec.b2_harness_contract.sha256,
    }
    for key, value in expected_provenance.items():
        if provenance.get(key) != value:
            raise B2ConfirmatorySealingError(
                f"triple provenance mismatch: {spec.pair_id} {key}"
            )


def _validate_triple_attempt_history(
    *,
    root: Path,
    spec: PairSpec,
    request_digest: str,
    authorization_token: str,
    project_source_commit: str,
    source_image_digest: str,
) -> tuple[Path, list[dict[str, object]]]:
    triple_id = spec.pair_id
    attempts_root = root / "triples" / triple_id / "attempts"
    attempt_dirs = sorted(
        path for path in attempts_root.glob("attempt-*") if path.is_dir()
    )
    if not attempt_dirs:
        raise B2ConfirmatorySealingError(f"triple has no attempts: {triple_id}")
    if len(attempt_dirs) > B2_CONFIRMATORY_MAX_ATTEMPTS:
        raise B2ConfirmatorySealingError(
            f"triple exceeds max attempts: {triple_id} count={len(attempt_dirs)}"
        )
    history: list[dict[str, object]] = []
    completed_dirs: list[Path] = []
    for index, attempt_dir in enumerate(attempt_dirs, start=1):
        if attempt_dir.name != f"attempt-{index:03d}":
            raise B2ConfirmatorySealingError(
                f"attempt sequence is not contiguous: {triple_id}"
            )
        started_path = attempt_dir / "started.json"
        if not started_path.is_file():
            raise B2ConfirmatorySealingError(
                f"attempt lacks started.json: {attempt_dir}"
            )
        started = load_json_object(started_path)
        _validate_attempt_provenance(
            started,
            spec=spec,
            request_digest=request_digest,
            authorization_token=authorization_token,
            project_source_commit=project_source_commit,
            source_image_digest=source_image_digest,
            attempt_number=index,
        )
        completed_path = attempt_dir / "completed.json"
        failed_path = attempt_dir / "failed.json"
        if completed_path.exists() and failed_path.exists():
            raise B2ConfirmatorySealingError(
                f"attempt has multiple terminal markers: {attempt_dir}"
            )
        if completed_path.is_file():
            completed = load_json_object(completed_path)
            _validate_attempt_provenance(
                completed,
                spec=spec,
                request_digest=request_digest,
                authorization_token=authorization_token,
                project_source_commit=project_source_commit,
                source_image_digest=source_image_digest,
                attempt_number=index,
            )
            if completed.get("status") != "completed":
                raise B2ConfirmatorySealingError(
                    f"invalid completed marker: {attempt_dir}"
                )
            triple_path = attempt_dir / "result" / "triple.json"
            if not triple_path.is_file():
                raise B2ConfirmatorySealingError(
                    f"completed attempt lacks triple result: {attempt_dir}"
                )
            if completed.get("result_sha256") != sha256_file(triple_path):
                raise B2ConfirmatorySealingError(
                    f"completed result digest mismatch: {attempt_dir}"
                )
            if completed.get("triple_admissible") is not True:
                raise B2ConfirmatorySealingError(
                    f"completed marker is not admissible: {attempt_dir}"
                )
            if completed.get("pairwise_comparison_count") != 2:
                raise B2ConfirmatorySealingError(
                    f"completed comparison count mismatch: {attempt_dir}"
                )
            completed_dirs.append(attempt_dir)
            history.append(completed)
            continue
        if failed_path.is_file():
            failed = load_json_object(failed_path)
            _validate_attempt_provenance(
                failed,
                spec=spec,
                request_digest=request_digest,
                authorization_token=authorization_token,
                project_source_commit=project_source_commit,
                source_image_digest=source_image_digest,
                attempt_number=index,
            )
            failure_class = failed.get("failure_class")
            if not isinstance(failure_class, str):
                raise B2ConfirmatorySealingError(
                    f"failure class is missing: {attempt_dir}"
                )
            if failure_class not in B2_CONFIRMATORY_RETRYABLE_FAILURE_CLASSES:
                raise B2ConfirmatorySealingError(
                    f"non-retryable failure in triple history: "
                    f"{triple_id} {failure_class}"
                )
            if failed.get("retry_eligible") is not True:
                raise B2ConfirmatorySealingError(
                    f"retryable failure marker is inconsistent: {attempt_dir}"
                )
            history.append(failed)
            continue
        raise B2ConfirmatorySealingError(
            f"running attempt remains at sealing: {attempt_dir}"
        )
    if len(completed_dirs) != 1:
        raise B2ConfirmatorySealingError(
            f"triple must have exactly one completed attempt: {triple_id}"
        )
    if completed_dirs[0] != attempt_dirs[-1]:
        raise B2ConfirmatorySealingError(
            f"completed attempt must be last: {triple_id}"
        )
    return completed_dirs[0], history


def _validate_attempt_provenance(
    value: Mapping[str, object],
    *,
    spec: PairSpec,
    request_digest: str,
    authorization_token: str,
    project_source_commit: str,
    source_image_digest: str,
    attempt_number: int,
) -> None:
    expected = {
        "campaign_id": B2_CONFIRMATORY_CAMPAIGN_ID,
        "triple_id": spec.pair_id,
        "lane": spec.lane,
        "method": spec.method,
        "model_seed": spec.model_seed,
        "validation_batch_index": spec.batch_index,
        "attempt_id": f"attempt-{attempt_number:03d}",
        "attempt_number": attempt_number,
        "request_id": spec.request_id,
        "request_digest": request_digest,
        "project_source_commit": project_source_commit,
        "authorization_token": authorization_token,
        "source_image_digest": source_image_digest,
        "resolved_config_digest": spec.resolved_config_digest,
        "checkpoint_sha256": spec.checkpoint.sha256,
        "batch_sha256": spec.batch.sha256,
        "b1_confirmatory_decision_sha256": (
            spec.b1_confirmatory_decision.sha256
        ),
        "b1_admission_sha256": spec.b1_admission.sha256,
        "b2_candidate_contract_sha256": (
            spec.b2_preregistration_contract.sha256
        ),
        "b2_implementation_contract_sha256": (
            spec.b2_implementation_contract.sha256
        ),
        "b2_harness_contract_sha256": spec.b2_harness_contract.sha256,
        "evidence": False,
        "test_dataset_access": False,
    }
    for key, registered in expected.items():
        if value.get(key) != registered:
            raise B2ConfirmatorySealingError(
                f"attempt provenance mismatch: {spec.pair_id} {key}"
            )


def _verify_sha256_registry(result_dir: Path) -> None:
    registry = result_dir / "SHA256SUMS"
    if not registry.is_file():
        raise B2ConfirmatorySealingError(
            f"result checksum registry missing: {result_dir}"
        )
    lines = registry.read_text(encoding="utf-8").splitlines()
    expected_names = {
        "triple.json",
        "trajectory-metrics.csv",
        "endpoint-metrics.csv",
        "direct-b1-b2-metrics.csv",
        "structural-events.jsonl",
    }
    observed_names: set[str] = set()
    for line in lines:
        parts = line.split("  ", maxsplit=1)
        if len(parts) != 2:
            raise B2ConfirmatorySealingError(f"invalid checksum line: {line}")
        digest, name = parts
        observed_names.add(name)
        path = result_dir / name
        if not path.is_file() or sha256_file(path) != digest:
            raise B2ConfirmatorySealingError(
                f"result checksum mismatch: {path}"
            )
    if observed_names != expected_names:
        raise B2ConfirmatorySealingError(
            f"result checksum registry is incomplete: {result_dir}"
        )


def _combine_csv_files(sources: Sequence[Path], destination: Path) -> None:
    rows: list[dict[str, JsonScalar]] = []
    fieldnames: list[str] | None = None
    for source in sources:
        with source.open("r", encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames is None:
                raise B2ConfirmatorySealingError(f"CSV has no header: {source}")
            if fieldnames is None:
                fieldnames = list(reader.fieldnames)
            elif list(reader.fieldnames) != fieldnames:
                raise B2ConfirmatorySealingError(
                    f"CSV schema mismatch: {source}"
                )
            rows.extend(cast(dict[str, JsonScalar], row) for row in reader)
    if not rows:
        raise B2ConfirmatorySealingError(
            f"no rows to aggregate into {destination}"
        )
    write_csv_rows(destination, rows)


def _combine_structural_events(
    sources: Sequence[tuple[str, Path]],
    destination: Path,
) -> None:
    with destination.open("w", encoding="utf-8") as output:
        for triple_id, source in sources:
            for line in source.read_text(encoding="utf-8").splitlines():
                event = json.loads(line)
                if not isinstance(event, dict):
                    raise B2ConfirmatorySealingError(
                        f"structural event is not an object: {source}"
                    )
                event["triple_id"] = triple_id
                output.write(json.dumps(event, sort_keys=True) + "\n")


def _write_jsonl(
    path: Path,
    rows: Sequence[Mapping[str, object]],
) -> None:
    with path.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True) + "\n")
