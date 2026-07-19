"""Validation and sealing for the 288-cell Stage 3B matched campaign."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final, cast

from torch2pc_thesis.stage3b_matched_profiling import (
    MATCHED_PROFILING_CANDIDATES,
    validate_matched_manifest,
)

MATCHED_SEAL_SCHEMA_VERSION: Final[int] = 1
MATCHED_SEAL_SCOPE: Final[str] = "stage3b_b1_b2_matched_sealed_evidence_v1"
MATCHED_REQUIRED_VALIDATION: Final[dict[str, object]] = {
    "dataset": "synthetic_scaling_family",
    "test_loader_created": False,
    "test_evaluated": False,
    "profile_completeness_validated": True,
    "measurement_lane_completeness_validated": True,
    "primary_timing_observer_mode": "no_hooks",
    "structural_counters_observer_mode": "counters_only",
    "observer_cost_reported_separately": True,
    "observer_cost_subtracted_from_primary_timing": False,
    "structural_locality_events_validated": True,
    "all_non_perturbation_gates_passed": True,
    "fresh_process_per_candidate": True,
    "block_state_reconstructed_from_shared_seeds": True,
}
MATCHED_SEALED_FILES: Final[tuple[str, ...]] = (
    "profiling_cells.csv",
    "profiling_repetitions.csv",
    "locality_events.jsonl",
    "profiling_summary.csv",
    "analysis_metadata.json",
    "environment-lock.json",
    "runtime-inventory.json",
    "seal.json",
)


class Stage3BMatchedSealingError(RuntimeError):
    """Raised when matched runtime artifacts violate the frozen contract."""


@dataclass(frozen=True)
class ValidatedMatchedCell:
    cell: Mapping[str, object]
    attempt_directory: Path
    resolved_config: Mapping[str, object]
    environment: Mapping[str, object]
    measurements: Mapping[str, object]
    locality_events: tuple[Mapping[str, object], ...]


@dataclass(frozen=True)
class ValidatedMatchedRuntime:
    root: Path
    source_commit: str
    image_digest: str
    authorization_token: str
    manifest_digest: str
    protocol: Mapping[str, object]
    cells: tuple[ValidatedMatchedCell, ...]
    runtime_inventory: tuple[Mapping[str, object], ...]
    runtime_inventory_sha256: str


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Stage3BMatchedSealingError(f"cannot read JSON object: {path}") from exc
    if not isinstance(value, dict):
        raise Stage3BMatchedSealingError(f"expected JSON object: {path}")
    return cast(dict[str, object], value)


def _mapping(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise Stage3BMatchedSealingError(f"{label} must be a mapping")
    return cast(Mapping[str, object], value)


def _list_of_mappings(value: object, *, label: str) -> list[Mapping[str, object]]:
    if not isinstance(value, list) or not all(isinstance(item, Mapping) for item in value):
        raise Stage3BMatchedSealingError(f"{label} must be a list of mappings")
    return cast(list[Mapping[str, object]], value)


def _require_equal(observed: object, expected: object, *, label: str) -> None:
    if observed != expected:
        raise Stage3BMatchedSealingError(
            f"{label} differs: expected={expected!r}, observed={observed!r}"
        )


def _finite(value: object, *, label: str) -> float:
    try:
        result = float(cast(Any, value))
    except (TypeError, ValueError) as exc:
        raise Stage3BMatchedSealingError(f"{label} must be numeric") from exc
    if not math.isfinite(result):
        raise Stage3BMatchedSealingError(f"{label} must be finite")
    return result


def _read_jsonl(path: Path) -> tuple[Mapping[str, object], ...]:
    events: list[Mapping[str, object]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise Stage3BMatchedSealingError(f"cannot read JSONL: {path}") from exc
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise Stage3BMatchedSealingError(
                f"invalid JSONL at {path}:{line_number}"
            ) from exc
        if not isinstance(value, dict):
            raise Stage3BMatchedSealingError(
                f"JSONL event is not an object at {path}:{line_number}"
            )
        events.append(cast(Mapping[str, object], value))
    if not events:
        raise Stage3BMatchedSealingError(f"locality event stream is empty: {path}")
    return tuple(events)


def _inventory(paths: Iterable[Path], *, root: Path) -> tuple[dict[str, object], ...]:
    records = [
        {
            "path": path.relative_to(root).as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in sorted(set(paths))
    ]
    return tuple(records)


def validate_matched_runtime(
    runtime_root: Path,
    matched_manifest: Mapping[str, object],
    *,
    expected_source_commit: str,
    expected_image_digest: str,
    expected_authorization_token: str,
) -> ValidatedMatchedRuntime:
    """Validate exact terminal, measurement-lane, and locality completeness."""

    validate_matched_manifest(matched_manifest)
    root = runtime_root.expanduser().resolve()
    if not root.is_dir():
        raise Stage3BMatchedSealingError(f"runtime root is not a directory: {root}")
    lane_root = root / "matched/lanes/rocm-float32"
    if not lane_root.is_dir():
        raise Stage3BMatchedSealingError(f"missing ROCm/float32 lane: {lane_root}")
    protocol = _mapping(matched_manifest.get("protocol"), label="manifest.protocol")
    repetitions = int(cast(int, protocol["repetitions"]))
    measured_steps = int(cast(int, protocol["measured_steps"]))
    warmup_steps = int(cast(int, protocol["warmup_steps"]))
    expected_step_count = repetitions * measured_steps
    expected_region_count = expected_step_count * 5
    raw_cells = _list_of_mappings(matched_manifest.get("cells"), label="manifest.cells")
    validated: list[ValidatedMatchedCell] = []
    inventory_paths: list[Path] = []
    candidate_counts: Counter[str] = Counter()
    block_counts: Counter[str] = Counter()

    for cell in raw_cells:
        cell_id = str(cell["cell_id"])
        attempts_root = lane_root / "cells" / cell_id / "attempts"
        if not attempts_root.is_dir():
            raise Stage3BMatchedSealingError(f"missing attempts for {cell_id}")
        attempt_dirs = sorted(path for path in attempts_root.iterdir() if path.is_dir())
        completed_dirs = [path for path in attempt_dirs if (path / "completed.json").is_file()]
        failed_dirs = [path for path in attempt_dirs if (path / "failed.json").is_file()]
        running_dirs = [
            path
            for path in attempt_dirs
            if (path / "started.json").is_file()
            and not (path / "completed.json").is_file()
            and not (path / "failed.json").is_file()
        ]
        if len(completed_dirs) != 1 or failed_dirs or running_dirs:
            raise Stage3BMatchedSealingError(
                f"{cell_id} terminal state is not uniquely successful: "
                f"completed={len(completed_dirs)}, failed={len(failed_dirs)}, "
                f"running={len(running_dirs)}"
            )
        attempt = completed_dirs[0]
        required = {
            "request.json",
            "started.json",
            "resolved-config.json",
            "environment.json",
            "measurements.json",
            "locality-events.jsonl",
            "completed.json",
        }
        present = {path.name for path in attempt.iterdir() if path.is_file()}
        missing = sorted(required - present)
        if missing:
            raise Stage3BMatchedSealingError(f"{cell_id} is missing files: {missing}")
        inventory_paths.extend(attempt / name for name in sorted(required))
        request = _load_json(attempt / "request.json")
        completed = _load_json(attempt / "completed.json")
        config = _load_json(attempt / "resolved-config.json")
        environment = _load_json(attempt / "environment.json")
        measurements = _load_json(attempt / "measurements.json")
        events_path = attempt / "locality-events.jsonl"
        events = _read_jsonl(events_path)
        candidate_id = str(cell["candidate_id"])
        method = str(cell["method"])
        block_id = str(cell["block_id"])
        for record_name, record in {"request": request, "completed": completed}.items():
            _require_equal(record.get("cell_id"), cell_id, label=f"{cell_id}.{record_name}.cell_id")
            _require_equal(
                record.get("candidate_id"), candidate_id, label=f"{cell_id}.{record_name}.candidate"
            )
            _require_equal(record.get("method"), method, label=f"{cell_id}.{record_name}.method")
            _require_equal(
                record.get("authorization_token"),
                expected_authorization_token,
                label=f"{cell_id}.{record_name}.authorization_token",
            )
            _require_equal(
                record.get("source_commit"),
                expected_source_commit,
                label=f"{cell_id}.{record_name}.source_commit",
            )
            _require_equal(
                record.get("image_digest"),
                expected_image_digest,
                label=f"{cell_id}.{record_name}.image_digest",
            )
        _require_equal(completed.get("status"), "matched_cell_complete", label=f"{cell_id}.status")
        _require_equal(config.get("candidate_id"), candidate_id, label=f"{cell_id}.config.candidate")
        _require_equal(config.get("block_id"), block_id, label=f"{cell_id}.config.block")
        _require_equal(environment.get("project_source_commit"), expected_source_commit, label=f"{cell_id}.environment.commit")
        _require_equal(environment.get("container_image_digest"), expected_image_digest, label=f"{cell_id}.environment.image")
        _require_equal(environment.get("authorization_token"), expected_authorization_token, label=f"{cell_id}.environment.token")
        _require_equal(measurements.get("status"), "matched_cell_complete", label=f"{cell_id}.measurements.status")
        _require_equal(measurements.get("evidence"), False, label=f"{cell_id}.measurements.evidence")
        _require_equal(measurements.get("test_dataset_access"), False, label=f"{cell_id}.measurements.test")
        _require_equal(measurements.get("warmup_gate_count"), repetitions * warmup_steps, label=f"{cell_id}.warmup_count")
        _require_equal(measurements.get("measured_gate_count"), expected_step_count, label=f"{cell_id}.measured_count")
        _require_equal(measurements.get("region_record_count"), expected_region_count, label=f"{cell_id}.region_count")
        primary = _list_of_mappings(measurements.get("primary_timing_measurements"), label=f"{cell_id}.primary")
        structural_timing = _list_of_mappings(measurements.get("structural_timing_measurements"), label=f"{cell_id}.structural_timing")
        observer = _list_of_mappings(measurements.get("observer_cost_measurements"), label=f"{cell_id}.observer")
        structural = _list_of_mappings(measurements.get("structural_measurements"), label=f"{cell_id}.structural")
        integrity = _list_of_mappings(measurements.get("integrity_measurements"), label=f"{cell_id}.integrity")
        for label, rows in {
            "primary": primary,
            "structural_timing": structural_timing,
            "observer": observer,
            "structural": structural,
            "integrity": integrity,
        }.items():
            _require_equal(len(rows), expected_step_count, label=f"{cell_id}.{label}.count")
        if not all(bool(row.get("passed")) for row in integrity):
            raise Stage3BMatchedSealingError(f"{cell_id} contains a failed integrity row")
        for row in primary:
            _require_equal(row.get("measurement_lane"), "primary_timing", label=f"{cell_id}.primary.lane")
            _require_equal(row.get("observer_mode"), "no_hooks", label=f"{cell_id}.primary.observer")
            _finite(row.get("host_time_us"), label=f"{cell_id}.primary.host")
            _finite(row.get("device_time_us"), label=f"{cell_id}.primary.device")
        for row in structural_timing:
            _require_equal(row.get("measurement_lane"), "structural_counters", label=f"{cell_id}.structural_timing.lane")
            _require_equal(row.get("observer_mode"), "counters_only", label=f"{cell_id}.structural_timing.observer")
        expected_events = sum(int(cast(int, row["event_count"])) for row in structural)
        _require_equal(measurements.get("locality_event_count"), expected_events, label=f"{cell_id}.locality_count")
        _require_equal(len(events), expected_events, label=f"{cell_id}.locality_lines")
        _require_equal(measurements.get("locality_events_sha256"), sha256_file(events_path), label=f"{cell_id}.locality_sha256")
        for event in events:
            _require_equal(event.get("cell_id"), cell_id, label=f"{cell_id}.event.cell")
            _require_equal(event.get("candidate_id"), candidate_id, label=f"{cell_id}.event.candidate")
            _require_equal(event.get("method"), method, label=f"{cell_id}.event.method")
            radius = event.get("dependency_radius")
            if radius is not None and int(cast(int, radius)) > 1:
                raise Stage3BMatchedSealingError(
                    f"{cell_id} has a mathematically local event with dependency_radius>1"
                )
        validation = _mapping(measurements.get("validation"), label=f"{cell_id}.validation")
        for key, expected in MATCHED_REQUIRED_VALIDATION.items():
            _require_equal(validation.get(key), expected, label=f"{cell_id}.validation.{key}")
        candidate_counts[candidate_id] += 1
        block_counts[block_id] += 1
        validated.append(
            ValidatedMatchedCell(
                cell=cell,
                attempt_directory=attempt,
                resolved_config=config,
                environment=environment,
                measurements=measurements,
                locality_events=events,
            )
        )

    expected_candidates = set(MATCHED_PROFILING_CANDIDATES)
    if set(candidate_counts) != expected_candidates:
        raise Stage3BMatchedSealingError(
            f"candidate coverage differs: {dict(candidate_counts)}"
        )
    expected_per_candidate = len(raw_cells) // len(expected_candidates)
    if set(candidate_counts.values()) != {expected_per_candidate}:
        raise Stage3BMatchedSealingError(
            f"candidate counts are unbalanced: {dict(candidate_counts)}"
        )
    if set(block_counts.values()) != {len(expected_candidates)}:
        raise Stage3BMatchedSealingError("matched blocks do not contain all candidates")
    inventory = _inventory(inventory_paths, root=root)
    inventory_sha = _sha256_bytes((_canonical_json(inventory) + "\n").encode("utf-8"))
    return ValidatedMatchedRuntime(
        root=root,
        source_commit=expected_source_commit,
        image_digest=expected_image_digest,
        authorization_token=expected_authorization_token,
        manifest_digest=str(matched_manifest["manifest_digest"]),
        protocol=protocol,
        cells=tuple(validated),
        runtime_inventory=inventory,
        runtime_inventory_sha256=inventory_sha,
    )


def _median(values: Sequence[float]) -> float:
    if not values:
        raise Stage3BMatchedSealingError("cannot calculate median of empty values")
    return float(statistics.median(values))


def _write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    if not rows:
        raise Stage3BMatchedSealingError(f"cannot write empty table: {path.name}")
    columns: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                columns.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _identity(cell: ValidatedMatchedCell) -> dict[str, object]:
    config = cell.resolved_config
    return {
        "cell_id": str(cell.cell["cell_id"]),
        "block_id": str(cell.cell["block_id"]),
        "candidate_id": str(cell.cell["candidate_id"]),
        "method": str(cell.cell["method"]),
        "depth": int(cast(int, config["depth"])),
        "width": int(cast(int, config["width"])),
        "batch_size": int(cast(int, config["batch_size"])),
        "model_seed": int(cast(int, config["model_seed"])),
    }


def _repetition_rows(validated: ValidatedMatchedRuntime) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for cell in validated.cells:
        identity = _identity(cell)
        measurements = cell.measurements
        primary = _list_of_mappings(measurements["primary_timing_measurements"], label="primary")
        observer = _list_of_mappings(measurements["observer_cost_measurements"], label="observer")
        structural = _list_of_mappings(measurements["structural_measurements"], label="structural")
        regions = _list_of_mappings(measurements["region_measurements"], label="regions")
        repetitions = sorted({int(cast(int, row["repetition"])) for row in primary})
        for repetition in repetitions:
            p_rows = [row for row in primary if int(cast(int, row["repetition"])) == repetition]
            o_rows = [row for row in observer if int(cast(int, row["repetition"])) == repetition]
            s_rows = [row for row in structural if int(cast(int, row["repetition"])) == repetition]
            r_rows = [row for row in regions if int(cast(int, row["repetition"])) == repetition]
            saved_by_step: defaultdict[int, int] = defaultdict(int)
            for row in r_rows:
                saved_by_step[int(cast(int, row["step"]))] += int(cast(int, row["saved_tensor_bytes"]))
            output.append(
                {
                    **identity,
                    "repetition": repetition,
                    "primary_host_time_median_us": _median([_finite(row["host_time_us"], label="host") for row in p_rows]),
                    "primary_device_time_median_us": _median([_finite(row["device_time_us"], label="device") for row in p_rows]),
                    "primary_peak_allocated_max_bytes": max(int(cast(int, row["peak_allocated_bytes"])) for row in p_rows),
                    "primary_peak_reserved_max_bytes": max(int(cast(int, row["peak_reserved_bytes"])) for row in p_rows),
                    "observer_cost_median_ms": _median([_finite(row["observer_cost_ms"], label="observer") for row in o_rows]),
                    "saved_tensor_bytes_median": _median([float(value) for value in saved_by_step.values()]),
                    "state_vjp_calls_median": _median([float(cast(int, row["state_vjp_calls"])) for row in s_rows]),
                    "graph_span_max": max(int(cast(int, row["graph_span"])) for row in s_rows),
                    "dependency_radius_max": max(int(cast(int, row["dependency_radius"])) for row in s_rows if row["dependency_radius"] is not None),
                    "graph_lifetimes": "|".join(sorted({value for row in s_rows for value in cast(list[str], row["graph_lifetimes"])})),
                    "feedback_operator": str(s_rows[0]["feedback_operator"]),
                    "fallback_validation_cost_ms": "",
                    "fallback_validation_status": str(s_rows[0]["fallback_validation_status"]),
                }
            )
    return output


def _cell_rows(repetitions: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    grouped: defaultdict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in repetitions:
        grouped[str(row["cell_id"])].append(row)
    output: list[dict[str, object]] = []
    for _cell_id, rows in sorted(grouped.items()):
        first = rows[0]
        output.append(
            {
                key: first[key]
                for key in ("cell_id", "block_id", "candidate_id", "method", "depth", "width", "batch_size", "model_seed")
            }
            | {
                "primary_host_time_us": _median([float(cast(Any, row["primary_host_time_median_us"])) for row in rows]),
                "primary_device_time_us": _median([float(cast(Any, row["primary_device_time_median_us"])) for row in rows]),
                "primary_peak_allocated_bytes": max(int(cast(Any, row["primary_peak_allocated_max_bytes"])) for row in rows),
                "primary_peak_reserved_bytes": max(int(cast(Any, row["primary_peak_reserved_max_bytes"])) for row in rows),
                "observer_cost_ms": _median([float(cast(Any, row["observer_cost_median_ms"])) for row in rows]),
                "saved_tensor_bytes": _median([float(cast(Any, row["saved_tensor_bytes_median"])) for row in rows]),
                "state_vjp_calls": _median([float(cast(Any, row["state_vjp_calls_median"])) for row in rows]),
                "graph_span": max(int(cast(Any, row["graph_span_max"])) for row in rows),
                "dependency_radius": max(int(cast(Any, row["dependency_radius_max"])) for row in rows),
                "graph_lifetimes": str(first["graph_lifetimes"]),
                "feedback_operator": str(first["feedback_operator"]),
                "fallback_validation_cost_ms": "",
                "fallback_validation_status": str(first["fallback_validation_status"]),
            }
        )
    return output


def _summary_rows(cells: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    grouped: defaultdict[tuple[object, ...], list[Mapping[str, object]]] = defaultdict(list)
    keys = ("candidate_id", "method", "depth", "width", "batch_size")
    for row in cells:
        grouped[tuple(row[key] for key in keys)].append(row)
    output: list[dict[str, object]] = []
    for group, rows in sorted(grouped.items(), key=lambda item: tuple(map(str, item[0]))):
        output.append(
            dict(zip(keys, group, strict=True))
            | {
                "model_seed_count": len(rows),
                "primary_host_time_median_us": _median([float(cast(Any, row["primary_host_time_us"])) for row in rows]),
                "primary_device_time_median_us": _median([float(cast(Any, row["primary_device_time_us"])) for row in rows]),
                "primary_peak_allocated_median_bytes": _median([float(cast(Any, row["primary_peak_allocated_bytes"])) for row in rows]),
                "primary_peak_reserved_median_bytes": _median([float(cast(Any, row["primary_peak_reserved_bytes"])) for row in rows]),
                "observer_cost_median_ms": _median([float(cast(Any, row["observer_cost_ms"])) for row in rows]),
                "saved_tensor_bytes_median": _median([float(cast(Any, row["saved_tensor_bytes"])) for row in rows]),
                "state_vjp_calls_median": _median([float(cast(Any, row["state_vjp_calls"])) for row in rows]),
                "graph_span_max": max(int(cast(Any, row["graph_span"])) for row in rows),
                "dependency_radius_max": max(int(cast(Any, row["dependency_radius"])) for row in rows),
            }
        )
    return output


def seal_matched_runtime(
    runtime_root: Path,
    output_root: Path,
    matched_manifest: Mapping[str, object],
    *,
    expected_source_commit: str,
    expected_image_digest: str,
    expected_authorization_token: str,
    sealing_source_commit: str,
    sealed_at_utc: str | None = None,
) -> dict[str, object]:
    """Validate runtime artifacts and write a compact immutable evidence bundle."""

    validated = validate_matched_runtime(
        runtime_root,
        matched_manifest,
        expected_source_commit=expected_source_commit,
        expected_image_digest=expected_image_digest,
        expected_authorization_token=expected_authorization_token,
    )
    destination = output_root.expanduser().resolve()
    if destination.exists() and any(destination.iterdir()):
        raise Stage3BMatchedSealingError(f"output root is not empty: {destination}")
    destination.mkdir(parents=True, exist_ok=True)
    repetition_rows = _repetition_rows(validated)
    cell_rows = _cell_rows(repetition_rows)
    summary_rows = _summary_rows(cell_rows)
    _write_csv(destination / "profiling_repetitions.csv", repetition_rows)
    _write_csv(destination / "profiling_cells.csv", cell_rows)
    _write_csv(destination / "profiling_summary.csv", summary_rows)
    with (destination / "locality_events.jsonl").open("w", encoding="utf-8") as handle:
        for cell in validated.cells:
            for event in cell.locality_events:
                handle.write(_canonical_json(event) + "\n")
    (destination / "runtime-inventory.json").write_text(
        json.dumps(list(validated.runtime_inventory), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    environment_lock = {
        "schema_version": MATCHED_SEAL_SCHEMA_VERSION,
        "source_commit": validated.source_commit,
        "sealing_source_commit": sealing_source_commit,
        "image_digest": validated.image_digest,
        "authorization_token": validated.authorization_token,
        "manifest_digest": validated.manifest_digest,
        "runtime_inventory_sha256": validated.runtime_inventory_sha256,
        "cell_environment_sha256": {
            str(cell.cell["cell_id"]): _sha256_bytes(
                (_canonical_json(cell.environment) + "\n").encode("utf-8")
            )
            for cell in validated.cells
        },
    }
    (destination / "environment-lock.json").write_text(
        json.dumps(environment_lock, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    metadata = {
        "schema_version": MATCHED_SEAL_SCHEMA_VERSION,
        "scope": MATCHED_SEAL_SCOPE,
        "protocol": dict(validated.protocol),
        "independent_unit": "model_seed",
        "aggregation_order": ["measured_steps_to_repetition", "repetitions_to_cell", "cells_to_model_seed"],
        "measurement_lanes": {
            "primary_timing": {"observer_mode": "no_hooks"},
            "structural_counters": {"observer_mode": "counters_only"},
        },
        "observer_cost_rule": {
            "reported_separately": True,
            "not_subtracted_from_primary_timing": True,
        },
        "fallback_validation": {
            "status": "not_applicable_before_ex_if0",
            "cost_ms": None,
        },
        "test_dataset_access": False,
        "results_publication_permitted": False,
    }
    (destination / "analysis_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    sealed_at = sealed_at_utc or datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")
    seal = {
        "schema_version": MATCHED_SEAL_SCHEMA_VERSION,
        "scope": MATCHED_SEAL_SCOPE,
        "status": "sealed",
        "sealed_at": sealed_at,
        "source_commit": validated.source_commit,
        "sealing_source_commit": sealing_source_commit,
        "image_digest": validated.image_digest,
        "authorization_token": validated.authorization_token,
        "manifest_digest": validated.manifest_digest,
        "runtime_inventory_sha256": validated.runtime_inventory_sha256,
        "matched_cell_count": len(validated.cells),
        "candidate_counts": dict(Counter(str(cell.cell["candidate_id"]) for cell in validated.cells)),
        "evidence": True,
        "full_lane_complete": True,
        "full_stage3b_campaign_complete": False,
        "results_publication_permitted": False,
        "test_dataset_access": False,
    }
    (destination / "seal.json").write_text(
        json.dumps(seal, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    checksums = [
        f"{sha256_file(destination / name)}  {name}"
        for name in MATCHED_SEALED_FILES
    ]
    (destination / "SHA256SUMS").write_text("\n".join(checksums) + "\n", encoding="utf-8")
    validate_sealed_matched_evidence(destination)
    return seal


def validate_sealed_matched_evidence(root: Path) -> dict[str, object]:
    resolved = root.expanduser().resolve()
    sums = resolved / "SHA256SUMS"
    if not sums.is_file():
        raise Stage3BMatchedSealingError("sealed evidence is missing SHA256SUMS")
    observed_names: set[str] = set()
    for line in sums.read_text(encoding="utf-8").splitlines():
        digest, name = line.split(maxsplit=1)
        name = name.removeprefix("*")
        observed_names.add(name)
        path = resolved / name
        if not path.is_file() or sha256_file(path) != digest:
            raise Stage3BMatchedSealingError(f"sealed checksum failed: {name}")
    if observed_names != set(MATCHED_SEALED_FILES):
        raise Stage3BMatchedSealingError(
            f"sealed inventory differs: {sorted(observed_names)}"
        )
    seal = _load_json(resolved / "seal.json")
    _require_equal(seal.get("status"), "sealed", label="seal.status")
    _require_equal(seal.get("evidence"), True, label="seal.evidence")
    _require_equal(seal.get("results_publication_permitted"), False, label="seal.publication")
    _require_equal(seal.get("test_dataset_access"), False, label="seal.test")
    return seal
