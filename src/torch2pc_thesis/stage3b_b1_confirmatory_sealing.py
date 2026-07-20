"""Seal one complete confirmatory Stage 3B B1 campaign."""

from __future__ import annotations

import csv
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Final, cast

from torch2pc_thesis.stage3b_b1_confirmatory import (
    B1_CONFIRMATORY_EXPECTED_PAIR_COUNT,
    B1_CONFIRMATORY_GATE_IDS,
    B1_CONFIRMATORY_MAX_ATTEMPTS,
    B1_CONFIRMATORY_RETRYABLE_FAILURE_CLASSES,
    B1ConfirmatoryError,
    build_pair_specs,
    load_json_object,
    validate_confirmatory_request,
)
from torch2pc_thesis.stage3b_b1_confirmatory_authorization import (
    validate_authorization,
)
from torch2pc_thesis.stage3b_b1_equivalence import (
    JsonScalar,
    JsonValue,
    atomic_write_json,
    canonical_json_digest,
    sha256_file,
    write_csv_rows,
)
from torch2pc_thesis.stage3b_b1_smoke import PairSpec

B1_CONFIRMATORY_DECISION_ID: Final[str] = "EQ-B1-CONFIRMATORY"
B1_MATCHED_ADMISSION_DECISION_ID: Final[str] = "EQ-B1"
B1_CONFIRMATORY_SEAL_SCHEMA_VERSION: Final[int] = 1


class B1ConfirmatorySealingError(B1ConfirmatoryError):
    """Raised when append-only confirmatory evidence cannot be sealed."""


def seal_b1_confirmatory_campaign(
    request: Mapping[str, object],
    authorization: Mapping[str, object],
    *,
    output_root: Path,
) -> dict[str, JsonValue]:
    validate_confirmatory_request(request)
    validate_authorization(authorization)
    if authorization.get("execution_mode") != "confirmatory":
        raise B1ConfirmatorySealingError(
            "engineering-smoke authorization cannot seal confirmatory evidence"
        )
    root = output_root.expanduser().resolve()
    if str(root) != authorization["output_root"]:
        raise B1ConfirmatorySealingError("authorization output root mismatch")
    if canonical_json_digest(request) != authorization["request_digest"]:
        raise B1ConfirmatorySealingError("authorization request digest mismatch")
    decision_path = root / "sealed" / "decision.json"
    if decision_path.exists():
        raise B1ConfirmatorySealingError(f"append-only decision already exists: {decision_path}")

    specs = build_pair_specs(request)
    if len(specs) != B1_CONFIRMATORY_EXPECTED_PAIR_COUNT:
        raise B1ConfirmatorySealingError("request does not contain 120 pairs")

    pair_summaries: list[dict[str, object]] = []
    attempt_history: list[dict[str, object]] = []
    trajectory_sources: list[Path] = []
    endpoint_sources: list[Path] = []
    structural_sources: list[tuple[str, Path]] = []

    for spec in specs:
        completed_dir, history = _validate_pair_attempt_history(
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
        pair = load_json_object(result_dir / "pair.json")
        if pair.get("pair_id") != spec.pair_id:
            raise B1ConfirmatorySealingError(f"pair result identity mismatch: {spec.pair_id}")
        if pair.get("pair_admissible") is not True:
            raise B1ConfirmatorySealingError(f"completed pair is not admissible: {spec.pair_id}")
        pair_gates = pair.get("gates")
        if not isinstance(pair_gates, dict):
            raise B1ConfirmatorySealingError(f"pair gates are missing: {spec.pair_id}")
        for gate_id in B1_CONFIRMATORY_GATE_IDS:
            gate = pair_gates.get(gate_id)
            if not isinstance(gate, dict) or gate.get("passed") is not True:
                raise B1ConfirmatorySealingError(
                    f"pair gate failed or missing: {spec.pair_id} {gate_id}"
                )
        _validate_pair_result(
            pair,
            spec=spec,
            completed_dir=completed_dir,
            source_image_digest=str(authorization["image_digest"]),
            torch2pc_commit=str(authorization["torch2pc_commit"]),
        )
        pair_summaries.append(pair)
        trajectory_sources.append(result_dir / "trajectory-metrics.csv")
        endpoint_sources.append(result_dir / "endpoint-metrics.csv")
        structural_sources.append((spec.pair_id, result_dir / "structural-events.jsonl"))

    observed_ids = {str(pair["pair_id"]) for pair in pair_summaries}
    expected_ids = {spec.pair_id for spec in specs}
    if observed_ids != expected_ids:
        raise B1ConfirmatorySealingError("sealed pair identity set mismatch")

    failed_pairs = sorted(
        str(pair["pair_id"]) for pair in pair_summaries if pair.get("pair_admissible") is not True
    )
    gate_results: dict[str, JsonValue] = {}
    for gate_id in B1_CONFIRMATORY_GATE_IDS:
        failed = sorted(
            str(pair["pair_id"]) for pair in pair_summaries if not _pair_gate_passed(pair, gate_id)
        )
        gate_results[gate_id] = {"passed": not failed, "failed_pairs": failed}
    all_passed = not failed_pairs and all(
        cast(Mapping[str, object], gate_results[gate_id]).get("passed") is True
        for gate_id in B1_CONFIRMATORY_GATE_IDS
    )
    if not all_passed:
        raise B1ConfirmatorySealingError(
            "confirmatory sealing requires all 120 pairs and all gates to pass"
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
    _combine_structural_events(
        structural_sources,
        sealed_root / "structural-events.jsonl",
    )

    decision: dict[str, JsonValue] = {
        "schema_version": B1_CONFIRMATORY_SEAL_SCHEMA_VERSION,
        "decision_id": B1_CONFIRMATORY_DECISION_ID,
        "scope": "confirmatory",
        "confirmatory_equivalence_executed": True,
        "status": "pass",
        "sealed": True,
        "candidate_id": "isolated_layer_vjp",
        "control_id": "stage2_baseline",
        "registered_pair_count": B1_CONFIRMATORY_EXPECTED_PAIR_COUNT,
        "observed_pair_count": len(pair_summaries),
        "failed_pair_count": 0,
        "failed_pairs": [],
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
            "opens B2 confirmatory preregistration and execution only; "
            "matched profiling remains closed until EQ-B2 confirmatory passes"
        ),
    }
    atomic_write_json(decision_path, decision)
    admission_path = sealed_root / "matched-profiling-admission.json"
    admission: dict[str, JsonValue] = {
        "schema_version": B1_CONFIRMATORY_SEAL_SCHEMA_VERSION,
        "decision_id": B1_MATCHED_ADMISSION_DECISION_ID,
        "source_decision_id": B1_CONFIRMATORY_DECISION_ID,
        "source_decision_path": decision_path.name,
        "source_decision_sha256": sha256_file(decision_path),
        "scope": "confirmatory",
        "confirmatory_equivalence_executed": True,
        "status": "pass",
        "sealed": True,
        "candidate_id": "isolated_layer_vjp",
        "control_id": "stage2_baseline",
        "matched_pairs_expected": B1_CONFIRMATORY_EXPECTED_PAIR_COUNT,
        "matched_pairs_observed": len(pair_summaries),
        "failed_pairs": [],
        "gates": gate_results,
        "request_digest": canonical_json_digest(request),
        "authorization_token": str(authorization["authorization_token"]),
        "project_source_commit": str(authorization["project_source_commit"]),
        "torch2pc_commit": str(authorization["torch2pc_commit"]),
        "image_digest": str(authorization["image_digest"]),
        "test_dataset_access": False,
        "results_publication_permitted": False,
    }
    atomic_write_json(admission_path, admission)
    required = (
        sealed_root / "request.json",
        sealed_root / "authorization.json",
        sealed_root / "resolved-config.json",
        sealed_root / "attempt-history.jsonl",
        sealed_root / "trajectory-metrics.csv",
        sealed_root / "endpoint-metrics.csv",
        sealed_root / "structural-events.jsonl",
        decision_path,
        admission_path,
    )
    (sealed_root / "SHA256SUMS").write_text(
        "".join(f"{sha256_file(path)}  {path.name}\n" for path in required),
        encoding="utf-8",
    )
    return decision


def _pair_gate_passed(pair: Mapping[str, object], gate_id: str) -> bool:
    raw_gates = pair.get("gates")
    if not isinstance(raw_gates, dict):
        return False
    raw_gate = raw_gates.get(gate_id)
    return isinstance(raw_gate, dict) and raw_gate.get("passed") is True


def _validate_pair_result(
    pair: Mapping[str, object],
    *,
    spec: PairSpec,
    completed_dir: Path,
    source_image_digest: str,
    torch2pc_commit: str,
) -> None:
    pair_spec = pair.get("pair_spec")
    if not isinstance(pair_spec, dict):
        raise B1ConfirmatorySealingError(f"pair spec is missing: {spec.pair_id}")
    expected_spec = {
        "request_id": spec.request_id,
        "attempt_id": completed_dir.name,
        "lane": spec.lane,
        "method": spec.method,
        "model_seed": spec.model_seed,
        "batch_index": spec.batch_index,
        "run_seed": spec.run_seed,
        "training_mode": spec.training_mode,
        "resolved_config_digest": spec.resolved_config_digest,
        "source_image_digest": source_image_digest,
    }
    for key, value in expected_spec.items():
        if pair_spec.get(key) != value:
            raise B1ConfirmatorySealingError(f"pair spec mismatch: {spec.pair_id} {key}")
    provenance = pair.get("provenance")
    if not isinstance(provenance, dict):
        raise B1ConfirmatorySealingError(f"pair provenance is missing: {spec.pair_id}")
    expected_provenance = {
        "request_id": spec.request_id,
        "attempt_id": completed_dir.name,
        "resolved_config_digest": spec.resolved_config_digest,
        "source_image_digest": source_image_digest,
        "checkpoint_sha256": spec.checkpoint.sha256,
        "batch_sha256": spec.batch.sha256,
        "torch2pc_commit": torch2pc_commit,
    }
    for key, value in expected_provenance.items():
        if provenance.get(key) != value:
            raise B1ConfirmatorySealingError(f"pair provenance mismatch: {spec.pair_id} {key}")


def _validate_pair_attempt_history(
    *,
    root: Path,
    spec: PairSpec,
    request_digest: str,
    authorization_token: str,
    project_source_commit: str,
    source_image_digest: str,
) -> tuple[Path, list[dict[str, object]]]:
    pair_id = spec.pair_id
    attempts_root = root / "pairs" / pair_id / "attempts"
    attempt_dirs = sorted(path for path in attempts_root.glob("attempt-*") if path.is_dir())
    if not attempt_dirs:
        raise B1ConfirmatorySealingError(f"pair has no attempts: {pair_id}")
    if len(attempt_dirs) > B1_CONFIRMATORY_MAX_ATTEMPTS:
        raise B1ConfirmatorySealingError(
            f"pair exceeds max attempts: {pair_id} count={len(attempt_dirs)}"
        )
    history: list[dict[str, object]] = []
    completed_dirs: list[Path] = []
    for index, attempt_dir in enumerate(attempt_dirs, start=1):
        expected_name = f"attempt-{index:03d}"
        if attempt_dir.name != expected_name:
            raise B1ConfirmatorySealingError(
                f"attempt sequence is not contiguous: {pair_id} {attempt_dir.name}"
            )
        started_path = attempt_dir / "started.json"
        if not started_path.is_file():
            raise B1ConfirmatorySealingError(f"attempt lacks started.json: {attempt_dir}")
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
            raise B1ConfirmatorySealingError(
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
                raise B1ConfirmatorySealingError(f"invalid completed marker: {attempt_dir}")
            pair_path = attempt_dir / "result" / "pair.json"
            if not pair_path.is_file():
                raise B1ConfirmatorySealingError(
                    f"completed attempt lacks pair result: {attempt_dir}"
                )
            if completed.get("result_sha256") != sha256_file(pair_path):
                raise B1ConfirmatorySealingError(f"completed result digest mismatch: {attempt_dir}")
            if completed.get("pair_admissible") is not True:
                raise B1ConfirmatorySealingError(
                    f"completed marker is not admissible: {attempt_dir}"
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
                raise B1ConfirmatorySealingError(f"failure class is missing: {attempt_dir}")
            if failure_class not in B1_CONFIRMATORY_RETRYABLE_FAILURE_CLASSES:
                raise B1ConfirmatorySealingError(
                    f"non-retryable failure in pair history: {pair_id} {failure_class}"
                )
            if failed.get("retry_eligible") is not True:
                raise B1ConfirmatorySealingError(
                    f"retryable failure marker is inconsistent: {attempt_dir}"
                )
            history.append(failed)
            continue
        raise B1ConfirmatorySealingError(f"running attempt remains at sealing: {attempt_dir}")
    if len(completed_dirs) != 1:
        raise B1ConfirmatorySealingError(f"pair must have exactly one completed attempt: {pair_id}")
    if completed_dirs[0] != attempt_dirs[-1]:
        raise B1ConfirmatorySealingError(f"completed attempt must be last: {pair_id}")
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
        "campaign_id": "stage3b-b1-confirmatory-equivalence-v1",
        "pair_id": spec.pair_id,
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
        "evidence": False,
        "test_dataset_access": False,
    }
    for key, registered in expected.items():
        if value.get(key) != registered:
            raise B1ConfirmatorySealingError(f"attempt provenance mismatch: {spec.pair_id} {key}")


def _verify_sha256_registry(result_dir: Path) -> None:
    registry = result_dir / "SHA256SUMS"
    if not registry.is_file():
        raise B1ConfirmatorySealingError(f"result checksum registry missing: {result_dir}")
    lines = registry.read_text(encoding="utf-8").splitlines()
    expected_names = {
        "pair.json",
        "trajectory-metrics.csv",
        "endpoint-metrics.csv",
        "structural-events.jsonl",
    }
    observed_names: set[str] = set()
    for line in lines:
        parts = line.split("  ", maxsplit=1)
        if len(parts) != 2:
            raise B1ConfirmatorySealingError(f"invalid checksum line: {line}")
        digest, name = parts
        observed_names.add(name)
        path = result_dir / name
        if not path.is_file() or sha256_file(path) != digest:
            raise B1ConfirmatorySealingError(f"result checksum mismatch: {path}")
    if observed_names != expected_names:
        raise B1ConfirmatorySealingError(f"result checksum registry is incomplete: {result_dir}")


def _combine_csv_files(sources: Sequence[Path], destination: Path) -> None:
    rows: list[dict[str, JsonScalar]] = []
    fieldnames: list[str] | None = None
    for source in sources:
        with source.open("r", encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames is None:
                raise B1ConfirmatorySealingError(f"CSV has no header: {source}")
            if fieldnames is None:
                fieldnames = list(reader.fieldnames)
            elif list(reader.fieldnames) != fieldnames:
                raise B1ConfirmatorySealingError(f"CSV schema mismatch: {source}")
            rows.extend(cast(dict[str, JsonScalar], row) for row in reader)
    if not rows:
        raise B1ConfirmatorySealingError(f"no rows to aggregate into {destination}")
    write_csv_rows(destination, rows)


def _combine_structural_events(sources: Sequence[tuple[str, Path]], destination: Path) -> None:
    with destination.open("w", encoding="utf-8") as output:
        for pair_id, source in sources:
            for line in source.read_text(encoding="utf-8").splitlines():
                event = json.loads(line)
                if not isinstance(event, dict):
                    raise B1ConfirmatorySealingError(f"structural event is not an object: {source}")
                event["pair_id"] = pair_id
                output.write(json.dumps(event, sort_keys=True) + "\n")


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True) + "\n")
