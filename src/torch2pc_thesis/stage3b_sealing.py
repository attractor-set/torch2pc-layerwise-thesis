"""Validate, aggregate, and seal immutable Stage 3B B0 canonical archives."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import shutil
import tempfile
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from statistics import fmean, median
from typing import Final, cast

from torch2pc_thesis.profiling import STAGE3_PROFILE_REGIONS, ProfilingProtocol
from torch2pc_thesis.stage3b_authorization import (
    B0_AUTHORIZATION_SCOPE,
    B0_CANDIDATE_ID,
    B0_EXPECTED_CELL_COUNT,
    validate_campaign_authorization,
    validate_lane_preflight,
    validate_project_freeze,
)
from torch2pc_thesis.stage3b_canonical import (
    B0_CANONICAL_CELL_SCOPE,
    B0_CANONICAL_INFERENCE_STEPS,
    B0_CANONICAL_PROCESS_MODE,
    B0_CANONICAL_PROCESS_SCOPE,
    B0_CANONICAL_SCOPE,
)
from torch2pc_thesis.stage3b_execution import (
    BATCH_SIZES,
    DEPTHS,
    MEASURED_STEPS,
    MODEL_SEEDS,
    REPETITIONS,
    STAGE3B_CAMPAIGN_ID,
    WARMUP_STEPS,
    WIDTHS,
    Stage3BExecutionError,
    validate_manifest,
)
from torch2pc_thesis.stage3b_profiling import (
    GPU_FLOAT32_THRESHOLDS,
    RegionMeasurement,
    validate_profile_completeness,
)

STAGE3B_B0_SEAL_SCHEMA_VERSION: Final[int] = 1
STAGE3B_B0_VALIDATION_SCOPE: Final[str] = (
    "stage3b_b0_rocm_float32_canonical_validation"
)
STAGE3B_B0_SEAL_SCOPE: Final[str] = "stage3b_b0_rocm_float32_canonical_seal"
STAGE3B_B0_EVIDENCE_SCOPE: Final[str] = (
    "stage3b_b0_rocm_float32_canonical_aggregate_evidence"
)
STAGE3B_B0_SEAL_DOMAIN: Final[str] = "torch2pc-stage3b-b0-seal-v1"
STAGE3B_B0_LANE_NAME: Final[str] = "rocm-float32"
_SHA256_HEX_LENGTH: Final[int] = 64

CELL_METRIC_COLUMNS: Final[tuple[str, ...]] = (
    "cell_id",
    "block_id",
    "method",
    "depth",
    "width",
    "batch_size",
    "model_seed",
    "attempt_id",
    "composite_record_count",
    "composite_host_time_mean_us",
    "composite_host_time_median_us",
    "composite_host_time_p95_us",
    "composite_device_time_mean_us",
    "composite_device_time_median_us",
    "composite_device_time_p95_us",
    "composite_peak_allocated_max_bytes",
    "composite_peak_reserved_max_bytes",
    "composite_synchronization_points_total",
    "integrity_record_count",
    "integrity_minimum_cosine",
    "integrity_maximum_relative_l2",
    "integrity_comparison_count_total",
    "integrity_all_passed",
    "configured_inference_steps",
    "observed_inference_steps_min",
    "observed_inference_steps_max",
    "region_record_count",
    "region_non_finite_events_total",
)

REGION_METRIC_COLUMNS: Final[tuple[str, ...]] = (
    "cell_id",
    "method",
    "depth",
    "width",
    "batch_size",
    "model_seed",
    "region",
    "record_count",
    "host_time_mean_us",
    "host_time_median_us",
    "host_time_p95_us",
    "device_time_mean_us",
    "device_time_median_us",
    "device_time_p95_us",
    "peak_allocated_max_bytes",
    "peak_reserved_max_bytes",
    "vjp_calls_total",
    "synchronization_points_total",
    "saved_tensor_bytes_mean",
    "saved_tensor_bytes_max",
    "actual_inference_steps_total",
    "actual_inference_steps_max",
    "non_finite_events_total",
)

PAIRED_METRIC_COLUMNS: Final[tuple[str, ...]] = (
    "depth",
    "width",
    "batch_size",
    "model_seed",
    "fixedpred_cell_id",
    "strict_cell_id",
    "fixedpred_device_time_median_us",
    "strict_device_time_median_us",
    "strict_minus_fixedpred_device_time_median_us",
    "strict_to_fixedpred_device_time_median_ratio",
    "fixedpred_host_time_median_us",
    "strict_host_time_median_us",
    "strict_minus_fixedpred_host_time_median_us",
    "strict_to_fixedpred_host_time_median_ratio",
    "fixedpred_peak_allocated_max_bytes",
    "strict_peak_allocated_max_bytes",
    "strict_minus_fixedpred_peak_allocated_bytes",
    "strict_to_fixedpred_peak_allocated_ratio",
    "fixedpred_peak_reserved_max_bytes",
    "strict_peak_reserved_max_bytes",
    "strict_minus_fixedpred_peak_reserved_bytes",
    "strict_to_fixedpred_peak_reserved_ratio",
)

CONFIGURATION_METRIC_COLUMNS: Final[tuple[str, ...]] = (
    "method",
    "depth",
    "width",
    "batch_size",
    "seed_count",
    "device_time_median_across_seeds_us",
    "device_time_min_across_seeds_us",
    "device_time_max_across_seeds_us",
    "host_time_median_across_seeds_us",
    "host_time_min_across_seeds_us",
    "host_time_max_across_seeds_us",
    "peak_allocated_median_across_seeds_bytes",
    "peak_allocated_max_across_seeds_bytes",
    "peak_reserved_median_across_seeds_bytes",
    "peak_reserved_max_across_seeds_bytes",
    "integrity_minimum_cosine_across_seeds",
    "integrity_maximum_relative_l2_across_seeds",
)


class Stage3BSealingError(Stage3BExecutionError):
    """Raised when an immutable B0 archive cannot be sealed."""


@dataclass(frozen=True)
class B0SealingContract:
    """Frozen validation contract used by the B0 archive sealer."""

    expected_cell_count: int = B0_EXPECTED_CELL_COUNT
    methods: tuple[str, ...] = ("fixedpred", "strict")
    depths: tuple[int, ...] = DEPTHS
    widths: tuple[int, ...] = WIDTHS
    batch_sizes: tuple[int, ...] = BATCH_SIZES
    model_seeds: tuple[int, ...] = MODEL_SEEDS
    warmup_steps: int = WARMUP_STEPS
    measured_steps: int = MEASURED_STEPS
    repetitions: int = REPETITIONS
    required_regions: tuple[str, ...] = tuple(sorted(STAGE3_PROFILE_REGIONS))
    require_unique_child_pids: bool = True

    def __post_init__(self) -> None:
        expected = (
            len(self.methods)
            * len(self.depths)
            * len(self.widths)
            * len(self.batch_sizes)
            * len(self.model_seeds)
        )
        if expected != self.expected_cell_count:
            raise ValueError(
                "B0 sealing contract matrix does not match expected_cell_count: "
                f"matrix={expected}, expected={self.expected_cell_count}"
            )
        if self.warmup_steps < 0 or self.measured_steps < 1 or self.repetitions < 1:
            raise ValueError("B0 sealing protocol counts are invalid")
        if not self.required_regions:
            raise ValueError("B0 sealing requires at least one profiling region")

    @property
    def protocol(self) -> ProfilingProtocol:
        return ProfilingProtocol(
            warmup_steps=self.warmup_steps,
            measured_steps=self.measured_steps,
            repetitions=self.repetitions,
        )

    @property
    def protocol_record(self) -> dict[str, int]:
        return {
            "warmup_steps": self.warmup_steps,
            "measured_steps": self.measured_steps,
            "repetitions": self.repetitions,
        }


DEFAULT_B0_SEALING_CONTRACT: Final[B0SealingContract] = B0SealingContract()


@dataclass(frozen=True)
class ValidatedB0Archive:
    """Validated source records and deterministic derived table rows."""

    validation_record: dict[str, object]
    metric_definitions: dict[str, object]
    cell_rows: tuple[dict[str, object], ...]
    region_rows: tuple[dict[str, object], ...]
    paired_rows: tuple[dict[str, object], ...]
    configuration_rows: tuple[dict[str, object], ...]


@dataclass(frozen=True)
class SealedB0Bundle:
    """Paths and identity of one completed derivative evidence bundle."""

    output_root: Path
    seal_digest: str
    source_archive_inventory_sha256: str
    artifact_count: int

    def to_record(self) -> dict[str, object]:
        return {
            "output_root": str(self.output_root),
            "seal_digest": self.seal_digest,
            "source_archive_inventory_sha256": (
                self.source_archive_inventory_sha256
            ),
            "artifact_count": self.artifact_count,
        }


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _digest_payload(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validated_sha256(value: str, *, label: str, prefixed: bool = False) -> str:
    normalized = value.strip().lower()
    if prefixed:
        if not normalized.startswith("sha256:"):
            raise Stage3BSealingError(f"{label} must use the sha256: prefix")
        raw = normalized.removeprefix("sha256:")
    else:
        raw = normalized
    if len(raw) != _SHA256_HEX_LENGTH or any(
        character not in "0123456789abcdef" for character in raw
    ):
        raise Stage3BSealingError(f"{label} must contain exactly 64 hexadecimal digits")
    return normalized


def _validated_commit(value: str, *, label: str) -> str:
    normalized = value.strip().lower()
    if len(normalized) != 40 or any(
        character not in "0123456789abcdef" for character in normalized
    ):
        raise Stage3BSealingError(
            f"{label} must be an exact 40-character hexadecimal commit"
        )
    return normalized


def _load_json_object(path: Path) -> dict[str, object]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Stage3BSealingError(f"invalid JSON object: {path}") from exc
    if not isinstance(raw, dict):
        raise Stage3BSealingError(f"JSON root must be an object: {path}")
    return cast(dict[str, object], raw)


def _mapping(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise Stage3BSealingError(f"{label} must be an object")
    return cast(Mapping[str, object], value)


def _list(value: object, *, label: str) -> list[object]:
    if not isinstance(value, list):
        raise Stage3BSealingError(f"{label} must be a list")
    return cast(list[object], value)


def _string(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise Stage3BSealingError(f"{label} must be a non-empty string")
    return value


def _integer(value: object, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise Stage3BSealingError(f"{label} must be an integer")
    return value


def _number(value: object, *, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise Stage3BSealingError(f"{label} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise Stage3BSealingError(f"{label} must be finite")
    return result


def _nonnegative_number(value: object, *, label: str) -> float:
    result = _number(value, label=label)
    if result < 0.0:
        raise Stage3BSealingError(f"{label} must be non-negative")
    return result


def _nonnegative_integer(value: object, *, label: str) -> int:
    result = _integer(value, label=label)
    if result < 0:
        raise Stage3BSealingError(f"{label} must be non-negative")
    return result


def _require_boolean(value: object, expected: bool, *, label: str) -> None:
    if value is not expected:
        raise Stage3BSealingError(f"{label} must be {expected}")


def _require_equal(observed: object, expected: object, *, label: str) -> None:
    if observed != expected:
        raise Stage3BSealingError(
            f"{label} differs: expected={expected!r}, observed={observed!r}"
        )


def _nearest_rank_p95(values: Sequence[float]) -> float:
    if not values:
        raise Stage3BSealingError("p95 requires at least one value")
    ordered = sorted(values)
    rank = max(1, math.ceil(0.95 * len(ordered)))
    return ordered[rank - 1]


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator == 0.0:
        if numerator == 0.0:
            return 1.0
        return math.inf
    return numerator / denominator


def _parse_sha256_inventory(path: Path) -> dict[Path, str]:
    entries: dict[Path, str] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise Stage3BSealingError(f"cannot read archive inventory: {path}") from exc
    if not lines:
        raise Stage3BSealingError("archive SHA256SUMS is empty")
    for line_number, line in enumerate(lines, start=1):
        if len(line) < 67 or line[64:66] not in {"  ", " *"}:
            raise Stage3BSealingError(
                f"invalid SHA256SUMS line {line_number}: {line!r}"
            )
        digest = _validated_sha256(
            line[:64], label=f"SHA256SUMS line {line_number} digest"
        )
        raw_name = line[66:]
        if raw_name.startswith("./"):
            raw_name = raw_name[2:]
        relative = Path(raw_name)
        if not raw_name or relative.is_absolute() or ".." in relative.parts:
            raise Stage3BSealingError(
                f"unsafe SHA256SUMS path on line {line_number}: {raw_name!r}"
            )
        if relative == Path("SHA256SUMS"):
            raise Stage3BSealingError("SHA256SUMS must not include itself")
        if relative in entries:
            raise Stage3BSealingError(f"duplicate SHA256SUMS path: {relative}")
        entries[relative] = digest
    return entries


def verify_archive_inventory(
    archive_root: Path,
    *,
    expected_inventory_sha256: str,
) -> dict[Path, str]:
    """Verify the exact immutable file inventory of one persistent archive."""

    root = archive_root.expanduser().resolve()
    if not root.is_dir():
        raise Stage3BSealingError(f"archive root is not a directory: {root}")
    inventory_path = root / "SHA256SUMS"
    if not inventory_path.is_file():
        raise Stage3BSealingError(f"archive inventory is missing: {inventory_path}")
    expected = _validated_sha256(
        expected_inventory_sha256,
        label="expected archive inventory SHA-256",
    )
    observed_inventory = _sha256_file(inventory_path)
    if observed_inventory != expected:
        raise Stage3BSealingError(
            "archive SHA256SUMS digest differs: "
            f"expected={expected}, observed={observed_inventory}"
        )

    entries = _parse_sha256_inventory(inventory_path)
    actual_paths: set[Path] = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            raise Stage3BSealingError(f"archive cannot contain symlinks: {path}")
        if path.is_file() and path != inventory_path:
            actual_paths.add(path.relative_to(root))
    expected_paths = set(entries)
    if actual_paths != expected_paths:
        missing = sorted(str(path) for path in expected_paths - actual_paths)
        extra = sorted(str(path) for path in actual_paths - expected_paths)
        raise Stage3BSealingError(
            f"archive inventory path mismatch: missing={missing}, extra={extra}"
        )

    for relative, digest in sorted(entries.items(), key=lambda item: str(item[0])):
        path = root / relative
        observed = _sha256_file(path)
        if observed != digest:
            raise Stage3BSealingError(
                f"archive file checksum differs: {relative}; "
                f"expected={digest}, observed={observed}"
            )
    return entries


def _archived_path(
    archive_root: Path,
    *,
    source_output_root: Path,
    recorded_path: object,
    label: str,
) -> Path:
    raw = _string(recorded_path, label=label)
    path = Path(raw)
    if not path.is_absolute():
        raise Stage3BSealingError(f"{label} must be an absolute source path")
    try:
        relative = path.relative_to(source_output_root)
    except ValueError as exc:
        raise Stage3BSealingError(
            f"{label} is outside the frozen source output root: {path}"
        ) from exc
    archived = archive_root / relative
    resolved = archived.resolve()
    if not resolved.is_relative_to(archive_root):
        raise Stage3BSealingError(f"{label} escapes the archive root: {path}")
    return resolved


def _single_completed_run(lane_root: Path) -> Path:
    runs_root = lane_root / "runs"
    if not runs_root.is_dir():
        raise Stage3BSealingError(f"canonical runs directory is missing: {runs_root}")
    runs = sorted(
        path
        for path in runs_root.iterdir()
        if path.is_dir() and (path / "completed.json").is_file()
    )
    if len(runs) != 1:
        raise Stage3BSealingError(
            f"B0 sealing requires exactly one completed canonical run, got {len(runs)}"
        )
    return runs[0]


def _validate_protocol_record(
    value: object,
    *,
    contract: B0SealingContract,
    label: str,
) -> None:
    record = _mapping(value, label=label)
    observed = {
        "warmup_steps": _integer(record.get("warmup_steps"), label=f"{label}.warmup_steps"),
        "measured_steps": _integer(
            record.get("measured_steps"), label=f"{label}.measured_steps"
        ),
        "repetitions": _integer(record.get("repetitions"), label=f"{label}.repetitions"),
    }
    _require_equal(observed, contract.protocol_record, label=label)


def _validate_source_non_evidence(
    record: Mapping[str, object],
    *,
    label: str,
    require_full_campaign: bool = True,
    require_publication: bool = True,
    require_test_access: bool = True,
) -> None:
    _require_boolean(record.get("evidence"), False, label=f"{label}.evidence")
    if require_full_campaign:
        _require_boolean(
            record.get("full_campaign_complete"),
            False,
            label=f"{label}.full_campaign_complete",
        )
    if require_publication:
        _require_boolean(
            record.get("results_publication_permitted"),
            False,
            label=f"{label}.results_publication_permitted",
        )
    if require_test_access:
        _require_boolean(
            record.get("test_dataset_access"),
            False,
            label=f"{label}.test_dataset_access",
        )


def _manifest_b0_cells(
    manifest: Mapping[str, object],
    *,
    contract: B0SealingContract,
) -> dict[str, dict[str, object]]:
    raw_cells = _list(manifest.get("cells"), label="manifest.cells")
    cells: dict[str, dict[str, object]] = {}
    observed_matrix: set[tuple[str, int, int, int, int]] = set()
    for raw_cell in raw_cells:
        cell = _mapping(raw_cell, label="manifest cell")
        if cell.get("candidate_id") != B0_CANDIDATE_ID:
            continue
        cell_id = _string(cell.get("cell_id"), label="manifest cell_id")
        if cell_id in cells:
            raise Stage3BSealingError(f"duplicate B0 manifest cell: {cell_id}")
        method = _string(cell.get("method"), label=f"{cell_id}.method")
        depth = _integer(cell.get("depth"), label=f"{cell_id}.depth")
        width = _integer(cell.get("width"), label=f"{cell_id}.width")
        batch_size = _integer(cell.get("batch_size"), label=f"{cell_id}.batch_size")
        model_seed = _integer(cell.get("model_seed"), label=f"{cell_id}.model_seed")
        observed_matrix.add((method, depth, width, batch_size, model_seed))
        cells[cell_id] = dict(cell)

    expected_matrix = {
        (method, depth, width, batch_size, model_seed)
        for method in contract.methods
        for depth in contract.depths
        for width in contract.widths
        for batch_size in contract.batch_sizes
        for model_seed in contract.model_seeds
    }
    if observed_matrix != expected_matrix or len(cells) != contract.expected_cell_count:
        raise Stage3BSealingError(
            "manifest B0 matrix differs from the sealing contract: "
            f"cells={len(cells)}, missing={sorted(expected_matrix - observed_matrix)}, "
            f"extra={sorted(observed_matrix - expected_matrix)}"
        )
    return cells


def _validate_environment(
    environment: Mapping[str, object],
    *,
    source_commit: str,
    image_digest: str,
    manifest_digest: str,
    authorization_token: str,
    torch2pc_source_sha256: str,
    expected_device_name: str,
    expected_hip_version: str,
    expected_pytorch_version: str,
) -> None:
    expected = {
        "project_source_commit": source_commit,
        "container_image_digest": image_digest,
        "manifest_digest": manifest_digest,
        "authorization_token": authorization_token,
        "torch2pc_source_sha256": torch2pc_source_sha256,
        "requested_device": "rocm",
        "resolved_device_type": "cuda",
        "dtype": "float32",
    }
    for key, value in expected.items():
        _require_equal(environment.get(key), value, label=f"environment.{key}")
    _require_equal(
        environment.get("device_name"),
        expected_device_name,
        label="environment.device_name",
    )
    _require_equal(
        environment.get("hip_version"),
        expected_hip_version,
        label="environment.hip_version",
    )
    _require_equal(
        environment.get("pytorch_version"),
        expected_pytorch_version,
        label="environment.pytorch_version",
    )
    for key in (
        "model_state_sha256",
        "synthetic_inputs_sha256",
        "synthetic_targets_sha256",
    ):
        _validated_sha256(_string(environment.get(key), label=f"environment.{key}"), label=key)


def _validate_measurement_index(
    records: Sequence[Mapping[str, object]],
    *,
    contract: B0SealingContract,
    label: str,
) -> None:
    expected = {
        (repetition, step)
        for repetition in range(contract.repetitions)
        for step in range(contract.measured_steps)
    }
    observed: set[tuple[int, int]] = set()
    for index, record in enumerate(records):
        repetition = _nonnegative_integer(
            record.get("repetition"), label=f"{label}[{index}].repetition"
        )
        step = _nonnegative_integer(record.get("step"), label=f"{label}[{index}].step")
        key = (repetition, step)
        if key in observed:
            raise Stage3BSealingError(f"duplicate {label} coordinate: {key}")
        observed.add(key)
    if observed != expected:
        raise Stage3BSealingError(
            f"{label} coordinates are incomplete: "
            f"missing={sorted(expected - observed)}, extra={sorted(observed - expected)}"
        )


def _validate_and_aggregate_measurements(
    measurements: Mapping[str, object],
    *,
    cell: Mapping[str, object],
    contract: B0SealingContract,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    cell_id = _string(cell.get("cell_id"), label="cell.cell_id")
    method = _string(cell.get("method"), label=f"{cell_id}.method")
    expected_inference_steps = B0_CANONICAL_INFERENCE_STEPS[method]
    measured_count = contract.measured_steps * contract.repetitions
    expected_region_count = measured_count * len(contract.required_regions)

    _require_equal(
        measurements.get("status"),
        "canonical_cell_complete",
        label=f"{cell_id}.measurements.status",
    )
    _require_equal(
        measurements.get("execution_scope"),
        B0_CANONICAL_CELL_SCOPE,
        label=f"{cell_id}.measurements.execution_scope",
    )
    _require_boolean(
        measurements.get("full_cell_complete"),
        True,
        label=f"{cell_id}.measurements.full_cell_complete",
    )
    _validate_source_non_evidence(measurements, label=f"{cell_id}.measurements")
    _require_equal(
        measurements.get("warmup_gate_count"),
        contract.warmup_steps * contract.repetitions,
        label=f"{cell_id}.measurements.warmup_gate_count",
    )
    _require_equal(
        measurements.get("measured_gate_count"),
        measured_count,
        label=f"{cell_id}.measurements.measured_gate_count",
    )
    _require_equal(
        measurements.get("expected_region_record_count"),
        expected_region_count,
        label=f"{cell_id}.measurements.expected_region_record_count",
    )
    _require_equal(
        measurements.get("region_record_count"),
        expected_region_count,
        label=f"{cell_id}.measurements.region_record_count",
    )
    validation = _mapping(
        measurements.get("validation"), label=f"{cell_id}.measurements.validation"
    )
    expected_validation = {
        "all_non_perturbation_gates_passed": True,
        "dataset": "synthetic_scaling_family",
        "profile_completeness_validated": True,
        "test_evaluated": False,
        "test_loader_created": False,
    }
    for key, value in expected_validation.items():
        _require_equal(validation.get(key), value, label=f"{cell_id}.validation.{key}")

    composite_raw = _list(
        measurements.get("composite_measurements"),
        label=f"{cell_id}.composite_measurements",
    )
    integrity_raw = _list(
        measurements.get("integrity_measurements"),
        label=f"{cell_id}.integrity_measurements",
    )
    regions_raw = _list(
        measurements.get("region_measurements"),
        label=f"{cell_id}.region_measurements",
    )
    if len(composite_raw) != measured_count:
        raise Stage3BSealingError(
            f"{cell_id} composite record count differs: {len(composite_raw)}"
        )
    if len(integrity_raw) != measured_count:
        raise Stage3BSealingError(
            f"{cell_id} integrity record count differs: {len(integrity_raw)}"
        )
    if len(regions_raw) != expected_region_count:
        raise Stage3BSealingError(
            f"{cell_id} region record count differs: {len(regions_raw)}"
        )

    composite = [
        _mapping(value, label=f"{cell_id}.composite") for value in composite_raw
    ]
    integrity = [
        _mapping(value, label=f"{cell_id}.integrity") for value in integrity_raw
    ]
    region_mappings = [
        _mapping(value, label=f"{cell_id}.region") for value in regions_raw
    ]
    _validate_measurement_index(
        composite, contract=contract, label=f"{cell_id}.composite"
    )
    _validate_measurement_index(
        integrity, contract=contract, label=f"{cell_id}.integrity"
    )

    composite_host: list[float] = []
    composite_device: list[float] = []
    composite_allocated: list[int] = []
    composite_reserved: list[int] = []
    composite_sync_total = 0
    for index, record in enumerate(composite):
        composite_host.append(
            _nonnegative_number(
                record.get("host_time_us"), label=f"{cell_id}.composite[{index}].host"
            )
        )
        composite_device.append(
            _nonnegative_number(
                record.get("device_time_us"), label=f"{cell_id}.composite[{index}].device"
            )
        )
        composite_allocated.append(
            _nonnegative_integer(
                record.get("peak_allocated_bytes"),
                label=f"{cell_id}.composite[{index}].allocated",
            )
        )
        composite_reserved.append(
            _nonnegative_integer(
                record.get("peak_reserved_bytes"),
                label=f"{cell_id}.composite[{index}].reserved",
            )
        )
        composite_sync_total += _nonnegative_integer(
            record.get("synchronization_points"),
            label=f"{cell_id}.composite[{index}].sync",
        )

    minimum_cosines: list[float] = []
    maximum_relative_l2s: list[float] = []
    comparison_total = 0
    observed_inference_steps: list[int] = []
    minimum_cosine_threshold, maximum_l2_threshold = GPU_FLOAT32_THRESHOLDS
    for index, record in enumerate(integrity):
        _require_boolean(
            record.get("all_finite"), True, label=f"{cell_id}.integrity[{index}].finite"
        )
        _require_boolean(
            record.get("internal_region_attribution_ready"),
            True,
            label=f"{cell_id}.integrity[{index}].attribution",
        )
        _require_boolean(
            record.get("passed"), True, label=f"{cell_id}.integrity[{index}].passed"
        )
        configured = _nonnegative_integer(
            record.get("configured_inference_steps"),
            label=f"{cell_id}.integrity[{index}].configured_steps",
        )
        observed = _nonnegative_integer(
            record.get("observed_inference_steps"),
            label=f"{cell_id}.integrity[{index}].observed_steps",
        )
        _require_equal(
            configured,
            expected_inference_steps,
            label=f"{cell_id}.configured_inference_steps",
        )
        _require_equal(
            observed,
            expected_inference_steps,
            label=f"{cell_id}.observed_inference_steps",
        )
        observed_inference_steps.append(observed)
        comparison_total += _nonnegative_integer(
            record.get("comparison_count"),
            label=f"{cell_id}.integrity[{index}].comparison_count",
        )
        cosine = _number(
            record.get("minimum_cosine"),
            label=f"{cell_id}.integrity[{index}].minimum_cosine",
        )
        relative_l2 = _nonnegative_number(
            record.get("maximum_relative_l2"),
            label=f"{cell_id}.integrity[{index}].maximum_relative_l2",
        )
        if cosine < minimum_cosine_threshold or relative_l2 > maximum_l2_threshold:
            raise Stage3BSealingError(
                f"{cell_id} integrity threshold violated at record {index}: "
                f"cosine={cosine}, relative_l2={relative_l2}"
            )
        minimum_cosines.append(cosine)
        maximum_relative_l2s.append(relative_l2)

    region_objects: list[RegionMeasurement] = []
    region_by_name: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for index, record in enumerate(region_mappings):
        candidate_id = _string(
            record.get("candidate_id"), label=f"{cell_id}.region[{index}].candidate_id"
        )
        record_method = _string(
            record.get("method"), label=f"{cell_id}.region[{index}].method"
        )
        _require_equal(candidate_id, B0_CANDIDATE_ID, label="region candidate_id")
        _require_equal(record_method, method, label="region method")
        region = _string(record.get("region"), label=f"{cell_id}.region[{index}].region")
        if region not in contract.required_regions:
            raise Stage3BSealingError(f"{cell_id} contains unexpected region: {region}")
        object_record = RegionMeasurement(
            candidate_id=candidate_id,
            method=record_method,
            repetition=_nonnegative_integer(
                record.get("repetition"), label=f"{cell_id}.region[{index}].repetition"
            ),
            step=_nonnegative_integer(
                record.get("step"), label=f"{cell_id}.region[{index}].step"
            ),
            region=region,
            host_time_us=_nonnegative_number(
                record.get("host_time_us"), label=f"{cell_id}.region[{index}].host"
            ),
            device_time_us=_nonnegative_number(
                record.get("device_time_us"), label=f"{cell_id}.region[{index}].device"
            ),
            peak_allocated_bytes=_nonnegative_integer(
                record.get("peak_allocated_bytes"),
                label=f"{cell_id}.region[{index}].allocated",
            ),
            peak_reserved_bytes=_nonnegative_integer(
                record.get("peak_reserved_bytes"),
                label=f"{cell_id}.region[{index}].reserved",
            ),
            vjp_calls=_nonnegative_integer(
                record.get("vjp_calls"), label=f"{cell_id}.region[{index}].vjp_calls"
            ),
            synchronization_points=_nonnegative_integer(
                record.get("synchronization_points"),
                label=f"{cell_id}.region[{index}].sync",
            ),
            saved_tensor_bytes=_nonnegative_integer(
                record.get("saved_tensor_bytes"),
                label=f"{cell_id}.region[{index}].saved_tensor_bytes",
            ),
            actual_inference_steps=_nonnegative_integer(
                record.get("actual_inference_steps"),
                label=f"{cell_id}.region[{index}].actual_inference_steps",
            ),
            non_finite_events=_nonnegative_integer(
                record.get("non_finite_events"),
                label=f"{cell_id}.region[{index}].non_finite_events",
            ),
        )
        region_objects.append(object_record)
        region_by_name[region].append(record)

    validate_profile_completeness(
        region_objects,
        contract.protocol,
        required_regions=contract.required_regions,
    )
    region_non_finite_total = sum(record.non_finite_events for record in region_objects)
    if region_non_finite_total != 0:
        raise Stage3BSealingError(
            f"{cell_id} contains {region_non_finite_total} non-finite region events"
        )

    base = {
        "cell_id": cell_id,
        "block_id": _string(cell.get("block_id"), label=f"{cell_id}.block_id"),
        "method": method,
        "depth": _integer(cell.get("depth"), label=f"{cell_id}.depth"),
        "width": _integer(cell.get("width"), label=f"{cell_id}.width"),
        "batch_size": _integer(
            cell.get("batch_size"), label=f"{cell_id}.batch_size"
        ),
        "model_seed": _integer(cell.get("model_seed"), label=f"{cell_id}.model_seed"),
    }
    cell_row = {
        **base,
        "composite_record_count": len(composite),
        "composite_host_time_mean_us": fmean(composite_host),
        "composite_host_time_median_us": median(composite_host),
        "composite_host_time_p95_us": _nearest_rank_p95(composite_host),
        "composite_device_time_mean_us": fmean(composite_device),
        "composite_device_time_median_us": median(composite_device),
        "composite_device_time_p95_us": _nearest_rank_p95(composite_device),
        "composite_peak_allocated_max_bytes": max(composite_allocated),
        "composite_peak_reserved_max_bytes": max(composite_reserved),
        "composite_synchronization_points_total": composite_sync_total,
        "integrity_record_count": len(integrity),
        "integrity_minimum_cosine": min(minimum_cosines),
        "integrity_maximum_relative_l2": max(maximum_relative_l2s),
        "integrity_comparison_count_total": comparison_total,
        "integrity_all_passed": True,
        "configured_inference_steps": expected_inference_steps,
        "observed_inference_steps_min": min(observed_inference_steps),
        "observed_inference_steps_max": max(observed_inference_steps),
        "region_record_count": len(region_objects),
        "region_non_finite_events_total": region_non_finite_total,
    }

    region_rows: list[dict[str, object]] = []
    for region in contract.required_regions:
        rows = region_by_name[region]
        host = [_number(row.get("host_time_us"), label="region host time") for row in rows]
        device = [
            _number(row.get("device_time_us"), label="region device time") for row in rows
        ]
        allocated = [
            _integer(row.get("peak_allocated_bytes"), label="region allocated") for row in rows
        ]
        reserved = [
            _integer(row.get("peak_reserved_bytes"), label="region reserved") for row in rows
        ]
        saved = [
            _integer(row.get("saved_tensor_bytes"), label="region saved tensor bytes")
            for row in rows
        ]
        actual_steps = [
            _integer(row.get("actual_inference_steps"), label="region inference steps")
            for row in rows
        ]
        region_rows.append(
            {
                "cell_id": cell_id,
                "method": method,
                "depth": base["depth"],
                "width": base["width"],
                "batch_size": base["batch_size"],
                "model_seed": base["model_seed"],
                "region": region,
                "record_count": len(rows),
                "host_time_mean_us": fmean(host),
                "host_time_median_us": median(host),
                "host_time_p95_us": _nearest_rank_p95(host),
                "device_time_mean_us": fmean(device),
                "device_time_median_us": median(device),
                "device_time_p95_us": _nearest_rank_p95(device),
                "peak_allocated_max_bytes": max(allocated),
                "peak_reserved_max_bytes": max(reserved),
                "vjp_calls_total": sum(
                    _integer(row.get("vjp_calls"), label="region vjp calls")
                    for row in rows
                ),
                "synchronization_points_total": sum(
                    _integer(row.get("synchronization_points"), label="region sync")
                    for row in rows
                ),
                "saved_tensor_bytes_mean": fmean(saved),
                "saved_tensor_bytes_max": max(saved),
                "actual_inference_steps_total": sum(actual_steps),
                "actual_inference_steps_max": max(actual_steps),
                "non_finite_events_total": sum(
                    _integer(row.get("non_finite_events"), label="region non-finite")
                    for row in rows
                ),
            }
        )
    return cell_row, region_rows


def _request_terminal_immutable_fields() -> tuple[str, ...]:
    return (
        "schema_version",
        "campaign_id",
        "authorization_scope",
        "execution_scope",
        "attempt_id",
        "cell_id",
        "block_id",
        "candidate_id",
        "method",
        "authorization_token",
        "manifest_digest",
        "source_commit",
        "device",
        "dtype",
        "image_digest",
        "canonical_protocol",
        "evidence",
        "full_lane_complete",
        "full_campaign_complete",
        "results_publication_permitted",
        "test_dataset_access",
    )


def _aggregate_pairs(
    cell_rows: Sequence[Mapping[str, object]],
    *,
    contract: B0SealingContract,
) -> tuple[dict[str, object], ...]:
    grouped: dict[tuple[int, int, int, int], dict[str, Mapping[str, object]]] = defaultdict(dict)
    for row in cell_rows:
        key = (
            _integer(row.get("depth"), label="cell depth"),
            _integer(row.get("width"), label="cell width"),
            _integer(row.get("batch_size"), label="cell batch_size"),
            _integer(row.get("model_seed"), label="cell model_seed"),
        )
        method = _string(row.get("method"), label="cell method")
        grouped[key][method] = row

    rows: list[dict[str, object]] = []
    for key in sorted(grouped):
        methods = grouped[key]
        if set(methods) != set(contract.methods):
            raise Stage3BSealingError(
                f"paired method coverage differs for configuration {key}: {sorted(methods)}"
            )
        fixedpred = methods["fixedpred"]
        strict = methods["strict"]
        fp_device = _number(
            fixedpred.get("composite_device_time_median_us"), label="fixedpred device"
        )
        strict_device = _number(
            strict.get("composite_device_time_median_us"), label="strict device"
        )
        fp_host = _number(
            fixedpred.get("composite_host_time_median_us"), label="fixedpred host"
        )
        strict_host = _number(
            strict.get("composite_host_time_median_us"), label="strict host"
        )
        fp_allocated = _number(
            fixedpred.get("composite_peak_allocated_max_bytes"), label="fixedpred allocated"
        )
        strict_allocated = _number(
            strict.get("composite_peak_allocated_max_bytes"), label="strict allocated"
        )
        fp_reserved = _number(
            fixedpred.get("composite_peak_reserved_max_bytes"), label="fixedpred reserved"
        )
        strict_reserved = _number(
            strict.get("composite_peak_reserved_max_bytes"), label="strict reserved"
        )
        rows.append(
            {
                "depth": key[0],
                "width": key[1],
                "batch_size": key[2],
                "model_seed": key[3],
                "fixedpred_cell_id": fixedpred["cell_id"],
                "strict_cell_id": strict["cell_id"],
                "fixedpred_device_time_median_us": fp_device,
                "strict_device_time_median_us": strict_device,
                "strict_minus_fixedpred_device_time_median_us": strict_device - fp_device,
                "strict_to_fixedpred_device_time_median_ratio": _safe_ratio(
                    strict_device, fp_device
                ),
                "fixedpred_host_time_median_us": fp_host,
                "strict_host_time_median_us": strict_host,
                "strict_minus_fixedpred_host_time_median_us": strict_host - fp_host,
                "strict_to_fixedpred_host_time_median_ratio": _safe_ratio(
                    strict_host, fp_host
                ),
                "fixedpred_peak_allocated_max_bytes": int(fp_allocated),
                "strict_peak_allocated_max_bytes": int(strict_allocated),
                "strict_minus_fixedpred_peak_allocated_bytes": int(
                    strict_allocated - fp_allocated
                ),
                "strict_to_fixedpred_peak_allocated_ratio": _safe_ratio(
                    strict_allocated, fp_allocated
                ),
                "fixedpred_peak_reserved_max_bytes": int(fp_reserved),
                "strict_peak_reserved_max_bytes": int(strict_reserved),
                "strict_minus_fixedpred_peak_reserved_bytes": int(
                    strict_reserved - fp_reserved
                ),
                "strict_to_fixedpred_peak_reserved_ratio": _safe_ratio(
                    strict_reserved, fp_reserved
                ),
            }
        )
    expected_pairs = contract.expected_cell_count // len(contract.methods)
    if len(rows) != expected_pairs:
        raise Stage3BSealingError(
            f"paired method row count differs: expected={expected_pairs}, observed={len(rows)}"
        )
    return tuple(rows)


def _aggregate_configurations(
    cell_rows: Sequence[Mapping[str, object]],
    *,
    contract: B0SealingContract,
) -> tuple[dict[str, object], ...]:
    grouped: dict[tuple[str, int, int, int], list[Mapping[str, object]]] = defaultdict(list)
    for row in cell_rows:
        key = (
            _string(row.get("method"), label="configuration method"),
            _integer(row.get("depth"), label="configuration depth"),
            _integer(row.get("width"), label="configuration width"),
            _integer(row.get("batch_size"), label="configuration batch_size"),
        )
        grouped[key].append(row)

    rows: list[dict[str, object]] = []
    for key in sorted(grouped):
        group = grouped[key]
        seeds = {_integer(row.get("model_seed"), label="model_seed") for row in group}
        if seeds != set(contract.model_seeds):
            raise Stage3BSealingError(
                f"configuration seed coverage differs for {key}: {sorted(seeds)}"
            )
        device = [
            _number(row.get("composite_device_time_median_us"), label="device median")
            for row in group
        ]
        host = [
            _number(row.get("composite_host_time_median_us"), label="host median")
            for row in group
        ]
        allocated = [
            _number(row.get("composite_peak_allocated_max_bytes"), label="allocated max")
            for row in group
        ]
        reserved = [
            _number(row.get("composite_peak_reserved_max_bytes"), label="reserved max")
            for row in group
        ]
        cosines = [
            _number(row.get("integrity_minimum_cosine"), label="integrity cosine")
            for row in group
        ]
        relative_l2 = [
            _number(row.get("integrity_maximum_relative_l2"), label="integrity relative_l2")
            for row in group
        ]
        rows.append(
            {
                "method": key[0],
                "depth": key[1],
                "width": key[2],
                "batch_size": key[3],
                "seed_count": len(seeds),
                "device_time_median_across_seeds_us": median(device),
                "device_time_min_across_seeds_us": min(device),
                "device_time_max_across_seeds_us": max(device),
                "host_time_median_across_seeds_us": median(host),
                "host_time_min_across_seeds_us": min(host),
                "host_time_max_across_seeds_us": max(host),
                "peak_allocated_median_across_seeds_bytes": median(allocated),
                "peak_allocated_max_across_seeds_bytes": max(allocated),
                "peak_reserved_median_across_seeds_bytes": median(reserved),
                "peak_reserved_max_across_seeds_bytes": max(reserved),
                "integrity_minimum_cosine_across_seeds": min(cosines),
                "integrity_maximum_relative_l2_across_seeds": max(relative_l2),
            }
        )
    expected = (
        len(contract.methods)
        * len(contract.depths)
        * len(contract.widths)
        * len(contract.batch_sizes)
    )
    if len(rows) != expected:
        raise Stage3BSealingError(
            f"configuration aggregate row count differs: expected={expected}, observed={len(rows)}"
        )
    return tuple(rows)


def _metric_definitions(contract: B0SealingContract) -> dict[str, object]:
    return {
        "schema_version": STAGE3B_B0_SEAL_SCHEMA_VERSION,
        "scope": "stage3b_b0_aggregate_metric_definitions",
        "statistical_unit": "model_seed",
        "within_seed_repeated_observations": [
            "repetition",
            "measured_step",
            "profiling_region",
        ],
        "protocol": contract.protocol_record,
        "required_regions": list(contract.required_regions),
        "quantile_definition": {
            "name": "nearest_rank",
            "probability": 0.95,
            "rank": "ceil(0.95 * n), one-indexed",
        },
        "cell_metrics": {
            "time_mean": "arithmetic mean over all measured repetition-step records",
            "time_median": "median over all measured repetition-step records",
            "time_p95": "nearest-rank 95th percentile over measured records",
            "peak_memory": "maximum observed byte count within the cell child process",
            "integrity_minimum_cosine": "minimum B0 gate cosine over measured records",
            "integrity_maximum_relative_l2": "maximum B0 gate relative L2 over measured records",
        },
        "region_metrics": {
            "record_count": "repetitions * measured_steps for one region",
            "counter_totals": "sum over measured repetition-step records",
            "saved_tensor_bytes_mean": "arithmetic mean over measured records",
        },
        "paired_metrics": {
            "pairing_keys": ["depth", "width", "batch_size", "model_seed"],
            "comparison": "strict relative to fixedpred",
        },
        "configuration_metrics": {
            "grouping_keys": ["method", "depth", "width", "batch_size"],
            "unit": "model_seed",
            "expected_seed_count": len(contract.model_seeds),
        },
        "evidence": True,
        "full_b0_campaign_complete": True,
        "full_stage3b_campaign_complete": False,
        "test_dataset_access": False,
    }


def validate_b0_archive(
    archive_root: Path,
    *,
    expected_source_commit: str,
    expected_image_digest: str,
    expected_archive_inventory_sha256: str,
    contract: B0SealingContract = DEFAULT_B0_SEALING_CONTRACT,
) -> ValidatedB0Archive:
    """Validate a complete immutable B0 archive and build compact aggregates."""

    root = archive_root.expanduser().resolve()
    source_commit = _validated_commit(
        expected_source_commit, label="expected execution source commit"
    )
    image_digest = _validated_sha256(
        expected_image_digest,
        label="expected image digest",
        prefixed=True,
    )
    inventory_digest = _validated_sha256(
        expected_archive_inventory_sha256,
        label="expected archive inventory SHA-256",
    )
    inventory = verify_archive_inventory(
        root,
        expected_inventory_sha256=inventory_digest,
    )

    authorization_root = root / "authorization"
    freeze_path = authorization_root / "project-freeze.json"
    preflight_path = authorization_root / "rocm-float32-preflight.json"
    authorization_path = authorization_root / "campaign-authorization.json"
    freeze = _load_json_object(freeze_path)
    preflight = _load_json_object(preflight_path)
    authorization = _load_json_object(authorization_path)
    try:
        validate_project_freeze(freeze)
        validate_lane_preflight(preflight)
        validate_campaign_authorization(authorization)
    except Stage3BExecutionError as exc:
        raise Stage3BSealingError("authorization provenance validation failed") from exc

    _require_equal(
        freeze.get("project_source_commit"), source_commit, label="freeze source commit"
    )
    _require_equal(
        authorization.get("project_source_commit"),
        source_commit,
        label="authorization source commit",
    )
    _require_equal(preflight.get("image_digest"), image_digest, label="preflight image")
    _require_equal(
        authorization.get("authorized_cell_count"),
        contract.expected_cell_count,
        label="authorization cell count",
    )
    _require_equal(
        authorization.get("canonical_execution_count"),
        contract.expected_cell_count,
        label="authorization execution count",
    )
    _validate_protocol_record(
        freeze.get("canonical_protocol"), contract=contract, label="freeze protocol"
    )
    _validate_protocol_record(
        authorization.get("canonical_protocol"),
        contract=contract,
        label="authorization protocol",
    )
    _validate_source_non_evidence(
        freeze, label="freeze", require_publication=False
    )
    _validate_source_non_evidence(authorization, label="authorization")
    _validate_source_non_evidence(
        preflight,
        label="preflight",
        require_publication=False,
        require_test_access=False,
    )

    source_output_root = Path(
        _string(freeze.get("output_root"), label="freeze.output_root")
    )
    if not source_output_root.is_absolute():
        raise Stage3BSealingError("freeze output_root must be absolute")
    lane_root = root / "canonical" / "lanes" / STAGE3B_B0_LANE_NAME
    lane_state_path = lane_root / "lane-state.json"
    lane_state = _load_json_object(lane_state_path)
    run_dir = _single_completed_run(lane_root)
    run_completed_path = run_dir / "completed.json"
    run_results_path = run_dir / "results.json"
    run_completed = _load_json_object(run_completed_path)
    run_results = _load_json_object(run_results_path)
    if run_completed != run_results:
        raise Stage3BSealingError("run completed.json and results.json differ")

    child_inputs = run_dir / "child-inputs"
    manifest_path = child_inputs / "manifest.json"
    authorization_snapshot_path = child_inputs / "authorization.json"
    manifest = _load_json_object(manifest_path)
    authorization_snapshot = _load_json_object(authorization_snapshot_path)
    try:
        validate_manifest(manifest)
    except Stage3BExecutionError as exc:
        raise Stage3BSealingError("archived manifest validation failed") from exc
    if authorization_snapshot != authorization:
        raise Stage3BSealingError("run authorization snapshot differs from archive authorization")

    manifest_digest = _string(manifest.get("manifest_digest"), label="manifest digest")
    authorization_token = _string(
        authorization.get("authorization_token"), label="authorization token"
    )
    torch2pc_source_sha256 = _string(
        freeze.get("torch2pc_source_sha256"), label="Torch2PC source SHA-256"
    )
    _validated_sha256(torch2pc_source_sha256, label="Torch2PC source SHA-256")
    preflight_runtime = _mapping(
        preflight.get("runtime"), label="preflight.runtime"
    )
    expected_device_name = _string(
        preflight_runtime.get("device_name"), label="preflight.runtime.device_name"
    )
    expected_hip_version = _string(
        preflight_runtime.get("hip_version"), label="preflight.runtime.hip_version"
    )
    expected_pytorch_version = _string(
        preflight_runtime.get("pytorch_version"),
        label="preflight.runtime.pytorch_version",
    )
    for label, record in (
        ("freeze", freeze),
        ("authorization", authorization),
        ("lane_state", lane_state),
        ("run_completed", run_completed),
    ):
        _require_equal(
            record.get("campaign_id"), STAGE3B_CAMPAIGN_ID, label=f"{label}.campaign_id"
        )
        _require_equal(
            record.get("manifest_digest"), manifest_digest, label=f"{label}.manifest_digest"
        )
    _require_equal(
        run_completed.get("authorization_scope"),
        B0_AUTHORIZATION_SCOPE,
        label="run authorization scope",
    )
    _require_equal(
        run_completed.get("execution_scope"), B0_CANONICAL_SCOPE, label="run scope"
    )
    _require_equal(
        run_completed.get("status"), "lane_complete", label="run status"
    )
    _require_boolean(
        run_completed.get("execution_performed"), True, label="run execution_performed"
    )
    _require_equal(
        run_completed.get("source_commit"), source_commit, label="run source commit"
    )
    _require_equal(
        run_completed.get("image_digest"), image_digest, label="run image digest"
    )
    _require_equal(run_completed.get("device"), "rocm", label="run device")
    _require_equal(run_completed.get("dtype"), "float32", label="run dtype")
    _validate_protocol_record(
        run_completed.get("canonical_protocol"), contract=contract, label="run protocol"
    )
    _validate_source_non_evidence(run_completed, label="run")
    _require_boolean(
        run_completed.get("full_lane_complete"), True, label="run full_lane_complete"
    )
    _require_equal(
        run_completed.get("process_isolation_mode"),
        B0_CANONICAL_PROCESS_MODE,
        label="run process isolation mode",
    )
    for field, expected_value in {
        "executed_cell_count": contract.expected_cell_count,
        "completed_this_run_count": contract.expected_cell_count,
        "failed_this_run_count": 0,
        "completed_cell_count": contract.expected_cell_count,
        "remaining_cell_count": 0,
    }.items():
        _require_equal(run_completed.get(field), expected_value, label=f"run.{field}")
    _require_equal(run_completed.get("failures"), [], label="run failures")
    _require_boolean(run_completed.get("stopped_early"), False, label="run stopped_early")
    _require_equal(run_completed.get("systemic_stop"), None, label="run systemic_stop")

    _require_equal(lane_state.get("status"), "lane_complete", label="lane status")
    _require_equal(
        lane_state.get("completed_cell_count"),
        contract.expected_cell_count,
        label="lane completed count",
    )
    _require_equal(lane_state.get("failed_cell_count"), 0, label="lane failed count")
    _require_boolean(
        lane_state.get("full_lane_complete"), True, label="lane full_lane_complete"
    )
    _validate_source_non_evidence(lane_state, label="lane_state")
    lane_expected: dict[str, object] = {
        "authorization_token": authorization_token,
        "source_commit": source_commit,
        "image_digest": image_digest,
        "device": "rocm",
        "dtype": "float32",
    }
    for key, lane_expected_value in lane_expected.items():
        _require_equal(
            lane_state.get(key), lane_expected_value, label=f"lane_state.{key}"
        )

    cells = _manifest_b0_cells(manifest, contract=contract)
    selected_ids = [
        _string(value, label="selected_cell_id")
        for value in _list(run_completed.get("selected_cell_ids"), label="selected_cell_ids")
    ]
    if len(selected_ids) != contract.expected_cell_count or len(set(selected_ids)) != len(
        selected_ids
    ):
        raise Stage3BSealingError("run selected_cell_ids are incomplete or duplicated")
    if set(selected_ids) != set(cells):
        raise Stage3BSealingError("run selected cells differ from the manifest B0 matrix")

    result_records = [
        _mapping(value, label="run result")
        for value in _list(run_completed.get("results"), label="run results")
    ]
    if len(result_records) != contract.expected_cell_count:
        raise Stage3BSealingError("run result count differs from the B0 contract")
    result_by_cell: dict[str, Mapping[str, object]] = {}
    for result in result_records:
        cell_id = _string(result.get("cell_id"), label="run result cell_id")
        if cell_id in result_by_cell:
            raise Stage3BSealingError(f"duplicate run result for cell: {cell_id}")
        result_by_cell[cell_id] = result
        _require_equal(
            result.get("status"), "canonical_cell_complete", label=f"{cell_id}.result.status"
        )
        _require_boolean(
            result.get("full_cell_complete"),
            True,
            label=f"{cell_id}.result.full_cell_complete",
        )
        _require_boolean(
            result.get("systemic_resource_failure"),
            False,
            label=f"{cell_id}.result.systemic_resource_failure",
        )
    if set(result_by_cell) != set(cells):
        raise Stage3BSealingError("run results do not cover the complete B0 matrix")

    process_paths = sorted((run_dir / "processes").glob("*.json"))
    if len(process_paths) != contract.expected_cell_count:
        raise Stage3BSealingError(
            f"process record count differs: {len(process_paths)}"
        )
    process_by_cell: dict[str, tuple[Path, Mapping[str, object]]] = {}
    parent_pids: set[int] = set()
    child_pids: list[int] = []
    for process_path in process_paths:
        loaded_process = _load_json_object(process_path)
        cell_id = _string(loaded_process.get("cell_id"), label="process cell_id")
        if cell_id in process_by_cell:
            raise Stage3BSealingError(f"duplicate process record for cell: {cell_id}")
        process_by_cell[cell_id] = (process_path, loaded_process)
        process_expected: dict[str, object] = {
            "execution_scope": B0_CANONICAL_PROCESS_SCOPE,
            "authorization_scope": B0_AUTHORIZATION_SCOPE,
            "authorization_token": authorization_token,
            "manifest_digest": manifest_digest,
            "source_commit": source_commit,
            "device": "rocm",
            "dtype": "float32",
            "image_digest": image_digest,
            "process_isolation_mode": B0_CANONICAL_PROCESS_MODE,
            "child_exit_code": 0,
            "terminal_status": "canonical_cell_complete",
            "terminal_validation_error": None,
            "systemic_resource_failure": False,
        }
        for key, process_expected_value in process_expected.items():
            _require_equal(
                loaded_process.get(key),
                process_expected_value,
                label=f"{cell_id}.process.{key}",
            )
        _validate_source_non_evidence(
            loaded_process, label=f"{cell_id}.process"
        )
        parent_pid = _nonnegative_integer(
            loaded_process.get("parent_pid"), label=f"{cell_id}.parent_pid"
        )
        child_pid = _nonnegative_integer(
            loaded_process.get("child_pid"), label=f"{cell_id}.child_pid"
        )
        if parent_pid == 0 or child_pid == 0 or parent_pid == child_pid:
            raise Stage3BSealingError(f"invalid process isolation PIDs for {cell_id}")
        parent_pids.add(parent_pid)
        child_pids.append(child_pid)
        _string(loaded_process.get("child_stdout_tail"), label=f"{cell_id}.child_stdout_tail")
        child_stderr_tail = loaded_process.get("child_stderr_tail")
        if not isinstance(child_stderr_tail, str):
            raise Stage3BSealingError(f"{cell_id}.child_stderr_tail must be a string")
        _validated_sha256(
            _string(
                loaded_process.get("child_stdout_sha256"),
                label=f"{cell_id}.child_stdout_sha256",
            ),
            label=f"{cell_id}.child_stdout_sha256",
        )
        _validated_sha256(
            _string(
                loaded_process.get("child_stderr_sha256"),
                label=f"{cell_id}.child_stderr_sha256",
            ),
            label=f"{cell_id}.child_stderr_sha256",
        )
    if set(process_by_cell) != set(cells):
        raise Stage3BSealingError("process records do not cover the B0 matrix")
    if len(parent_pids) != 1:
        raise Stage3BSealingError(f"canonical run used multiple parent PIDs: {parent_pids}")
    if contract.require_unique_child_pids and len(set(child_pids)) != len(child_pids):
        raise Stage3BSealingError("canonical child PID records are not unique")

    attempt_dirs = sorted(path for path in lane_root.glob("cells/*/attempts/*") if path.is_dir())
    completed_paths = sorted(lane_root.glob("cells/*/attempts/*/completed.json"))
    failed_paths = sorted(lane_root.glob("cells/*/attempts/*/failed.json"))
    if len(attempt_dirs) != contract.expected_cell_count:
        raise Stage3BSealingError(f"attempt directory count differs: {len(attempt_dirs)}")
    if len(completed_paths) != contract.expected_cell_count or failed_paths:
        raise Stage3BSealingError(
            f"terminal attempt counts differ: completed={len(completed_paths)}, "
            f"failed={len(failed_paths)}"
        )

    attempt_by_cell: dict[str, Path] = {}
    cell_rows: list[dict[str, object]] = []
    region_rows: list[dict[str, object]] = []
    terminal_digests: dict[str, str] = {}
    measurement_digests: dict[str, str] = {}
    immutable_fields = _request_terminal_immutable_fields()
    for cell_id in selected_ids:
        cell = cells[cell_id]
        process_path, process_record = process_by_cell[cell_id]
        request_path = _archived_path(
            root,
            source_output_root=source_output_root,
            recorded_path=process_record.get("request_record"),
            label=f"{cell_id}.request_record",
        )
        terminal_path = _archived_path(
            root,
            source_output_root=source_output_root,
            recorded_path=process_record.get("terminal_record"),
            label=f"{cell_id}.terminal_record",
        )
        attempt_dir = _archived_path(
            root,
            source_output_root=source_output_root,
            recorded_path=process_record.get("attempt_directory"),
            label=f"{cell_id}.attempt_directory",
        )
        if attempt_dir in attempt_by_cell.values():
            raise Stage3BSealingError(f"duplicate attempt directory: {attempt_dir}")
        attempt_by_cell[cell_id] = attempt_dir
        if request_path != attempt_dir / "request.json" or terminal_path != attempt_dir / "completed.json":
            raise Stage3BSealingError(f"attempt record paths are inconsistent for {cell_id}")
        required_files = (
            request_path,
            attempt_dir / "started.json",
            attempt_dir / "resolved-config.json",
            attempt_dir / "environment.json",
            attempt_dir / "measurements.json",
            terminal_path,
        )
        for path in required_files:
            if not path.is_file():
                raise Stage3BSealingError(f"required attempt artifact is missing: {path}")
        if (attempt_dir / "failed.json").exists():
            raise Stage3BSealingError(f"completed attempt also contains failed.json: {attempt_dir}")
        _require_equal(
            process_record.get("request_record_sha256"),
            _sha256_file(request_path),
            label=f"{cell_id}.request_record_sha256",
        )
        _require_equal(
            process_record.get("terminal_record_sha256"),
            _sha256_file(terminal_path),
            label=f"{cell_id}.terminal_record_sha256",
        )
        request = _load_json_object(request_path)
        terminal = _load_json_object(terminal_path)
        started = _load_json_object(attempt_dir / "started.json")
        resolved = _load_json_object(attempt_dir / "resolved-config.json")
        environment = _load_json_object(attempt_dir / "environment.json")
        measurements_path = attempt_dir / "measurements.json"
        measurements = _load_json_object(measurements_path)
        for field in immutable_fields:
            _require_equal(
                terminal.get(field), request.get(field), label=f"{cell_id}.{field}"
            )
        _require_equal(terminal.get("status"), "canonical_cell_complete", label="terminal status")
        _require_boolean(
            terminal.get("full_cell_complete"), True, label="terminal full_cell_complete"
        )
        _require_equal(
            terminal.get("attempt_directory"),
            str(source_output_root / attempt_dir.relative_to(root)),
            label="terminal attempt_directory",
        )
        _require_equal(started.get("status"), "canonical_cell_running", label="started status")
        for field in immutable_fields:
            _require_equal(started.get(field), request.get(field), label=f"started.{field}")
        request_expected: dict[str, object] = {
            "cell_id": cell_id,
            "block_id": cell["block_id"],
            "candidate_id": B0_CANDIDATE_ID,
            "method": cell["method"],
            "authorization_token": authorization_token,
            "manifest_digest": manifest_digest,
            "source_commit": source_commit,
            "device": "rocm",
            "dtype": "float32",
            "image_digest": image_digest,
            "authorization_scope": B0_AUTHORIZATION_SCOPE,
            "execution_scope": B0_CANONICAL_CELL_SCOPE,
        }
        for key, request_expected_value in request_expected.items():
            _require_equal(
                request.get(key),
                request_expected_value,
                label=f"{cell_id}.request.{key}",
            )
        _validate_protocol_record(
            request.get("canonical_protocol"), contract=contract, label=f"{cell_id}.protocol"
        )
        _validate_source_non_evidence(request, label=f"{cell_id}.request")

        expected_resolved: dict[str, object] = {
            "method": cell["method"],
            "depth": cell["depth"],
            "width": cell["width"],
            "batch_size": cell["batch_size"],
            "model_seed": cell["model_seed"],
            "canonical_protocol": contract.protocol_record,
            "required_regions": list(contract.required_regions),
            "inference_steps": B0_CANONICAL_INFERENCE_STEPS[str(cell["method"])],
        }
        for key, resolved_expected_value in expected_resolved.items():
            _require_equal(
                resolved.get(key),
                resolved_expected_value,
                label=f"{cell_id}.resolved.{key}",
            )
        _validate_environment(
            environment,
            source_commit=source_commit,
            image_digest=image_digest,
            manifest_digest=manifest_digest,
            authorization_token=authorization_token,
            torch2pc_source_sha256=torch2pc_source_sha256,
            expected_device_name=expected_device_name,
            expected_hip_version=expected_hip_version,
            expected_pytorch_version=expected_pytorch_version,
        )
        cell_row, cell_region_rows = _validate_and_aggregate_measurements(
            measurements,
            cell=cell,
            contract=contract,
        )
        cell_row["attempt_id"] = _string(
            request.get("attempt_id"), label=f"{cell_id}.attempt_id"
        )
        cell_rows.append(cell_row)
        region_rows.extend(cell_region_rows)
        terminal_digests[cell_id] = _sha256_file(terminal_path)
        measurement_digests[cell_id] = _sha256_file(measurements_path)

        result = result_by_cell[cell_id]
        isolation = _mapping(
            result.get("process_isolation"), label=f"{cell_id}.process_isolation"
        )
        _require_equal(
            _archived_path(
                root,
                source_output_root=source_output_root,
                recorded_path=isolation.get("record_path"),
                label=f"{cell_id}.process record_path",
            ),
            process_path.resolve(),
            label=f"{cell_id}.process record path",
        )
        for key in ("parent_pid", "child_pid", "child_exit_code"):
            _require_equal(isolation.get(key), process_record.get(key), label=f"{cell_id}.{key}")
        _require_equal(
            isolation.get("mode"), B0_CANONICAL_PROCESS_MODE, label=f"{cell_id}.mode"
        )
        _require_equal(
            isolation.get("terminal_record_sha256"),
            process_record.get("terminal_record_sha256"),
            label=f"{cell_id}.result terminal digest",
        )

    if set(attempt_by_cell) != set(cells):
        raise Stage3BSealingError("attempt artifacts do not cover the B0 matrix")

    cell_rows.sort(
        key=lambda row: (
            _integer(row["depth"], label="depth"),
            _integer(row["width"], label="width"),
            _integer(row["batch_size"], label="batch_size"),
            _integer(row["model_seed"], label="model_seed"),
            _string(row["method"], label="method"),
            _string(row["cell_id"], label="cell_id"),
        )
    )
    region_rows.sort(
        key=lambda row: (
            _integer(row["depth"], label="depth"),
            _integer(row["width"], label="width"),
            _integer(row["batch_size"], label="batch_size"),
            _integer(row["model_seed"], label="model_seed"),
            _string(row["method"], label="method"),
            _string(row["region"], label="region"),
        )
    )
    paired_rows = _aggregate_pairs(cell_rows, contract=contract)
    configuration_rows = _aggregate_configurations(cell_rows, contract=contract)

    method_counts = Counter(_string(row["method"], label="method") for row in cell_rows)
    validation_record: dict[str, object] = {
        "schema_version": STAGE3B_B0_SEAL_SCHEMA_VERSION,
        "validation_scope": STAGE3B_B0_VALIDATION_SCOPE,
        "status": "validation_passed",
        "campaign_id": STAGE3B_CAMPAIGN_ID,
        "candidate_id": B0_CANDIDATE_ID,
        "source_archive_inventory_sha256": inventory_digest,
        "source_archive_file_count": len(inventory),
        "source_output_root": str(source_output_root),
        "source_commit": source_commit,
        "image_digest": image_digest,
        "manifest_digest": manifest_digest,
        "authorization_token": authorization_token,
        "run_id": _string(run_completed.get("run_id"), label="run_id"),
        "run_completed_at": _string(
            run_completed.get("completed_at"), label="run completed_at"
        ),
        "canonical_protocol": contract.protocol_record,
        "required_regions": list(contract.required_regions),
        "counts": {
            "cells": len(cell_rows),
            "methods": dict(sorted(method_counts.items())),
            "attempt_directories": len(attempt_dirs),
            "completed_attempts": len(completed_paths),
            "failed_attempts": len(failed_paths),
            "process_records": len(process_paths),
            "parent_processes": len(parent_pids),
            "observed_child_processes": len(child_pids),
            "unique_child_pids": len(set(child_pids)),
            "cell_metric_rows": len(cell_rows),
            "region_metric_rows": len(region_rows),
            "paired_metric_rows": len(paired_rows),
            "configuration_metric_rows": len(configuration_rows),
        },
        "process_isolation": {
            "mode": B0_CANONICAL_PROCESS_MODE,
            "parent_pids": sorted(parent_pids),
            "all_child_exit_codes_zero": True,
            "all_terminal_records_validated": True,
            "systemic_resource_failure_count": 0,
        },
        "integrity": {
            "all_non_perturbation_gates_passed": True,
            "all_profile_completeness_gates_passed": True,
            "non_finite_region_event_count": 0,
            "minimum_cosine_threshold": GPU_FLOAT32_THRESHOLDS[0],
            "maximum_relative_l2_threshold": GPU_FLOAT32_THRESHOLDS[1],
        },
        "source_record_digests": {
            "project_freeze": _sha256_file(freeze_path),
            "lane_preflight": _sha256_file(preflight_path),
            "campaign_authorization": _sha256_file(authorization_path),
            "manifest_snapshot": _sha256_file(manifest_path),
            "authorization_snapshot": _sha256_file(authorization_snapshot_path),
            "lane_state": _sha256_file(lane_state_path),
            "run_completed": _sha256_file(run_completed_path),
            "run_results": _sha256_file(run_results_path),
            "terminal_records_digest": _digest_payload(terminal_digests),
            "measurement_records_digest": _digest_payload(measurement_digests),
        },
        "source_records_evidence": False,
        "evidence": True,
        "full_b0_campaign_complete": True,
        "full_stage3b_campaign_complete": False,
        "results_publication_permitted": True,
        "test_dataset_access": False,
    }
    verify_archive_inventory(root, expected_inventory_sha256=inventory_digest)
    return ValidatedB0Archive(
        validation_record=validation_record,
        metric_definitions=_metric_definitions(contract),
        cell_rows=tuple(cell_rows),
        region_rows=tuple(region_rows),
        paired_rows=paired_rows,
        configuration_rows=configuration_rows,
    )


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_csv(
    path: Path,
    *,
    columns: Sequence[str],
    rows: Iterable[Mapping[str, object]],
) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(columns),
            extrasaction="raise",
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row[column] for column in columns})
            count += 1
    return count


def _artifact_inventory(root: Path, *, excluded: set[str] | None = None) -> list[dict[str, object]]:
    excluded_names = excluded or set()
    records: list[dict[str, object]] = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name not in excluded_names:
            records.append(
                {
                    "path": str(path.relative_to(root)),
                    "sha256": _sha256_file(path),
                    "bytes": path.stat().st_size,
                }
            )
    return records


def _write_sha256sums(root: Path) -> None:
    lines = [
        f"{record['sha256']}  ./{record['path']}"
        for record in _artifact_inventory(root, excluded={"SHA256SUMS"})
    ]
    (root / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")


def seal_b0_archive(
    archive_root: Path,
    output_root: Path,
    *,
    expected_source_commit: str,
    expected_image_digest: str,
    expected_archive_inventory_sha256: str,
    sealing_source_commit: str,
    contract: B0SealingContract = DEFAULT_B0_SEALING_CONTRACT,
) -> SealedB0Bundle:
    """Create a new derivative evidence bundle without modifying the source archive."""

    source = archive_root.expanduser().resolve()
    destination = output_root.expanduser().resolve()
    sealer_commit = _validated_commit(
        sealing_source_commit, label="sealing source commit"
    )
    if destination.exists():
        raise Stage3BSealingError(f"sealing output already exists: {destination}")
    if destination.is_relative_to(source) or source.is_relative_to(destination):
        raise Stage3BSealingError(
            "sealing output and immutable source archive must be separate trees"
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    validated = validate_b0_archive(
        source,
        expected_source_commit=expected_source_commit,
        expected_image_digest=expected_image_digest,
        expected_archive_inventory_sha256=expected_archive_inventory_sha256,
        contract=contract,
    )
    temporary = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent)
    )
    try:
        _write_json(temporary / "validation.json", validated.validation_record)
        _write_json(temporary / "metric-definitions.json", validated.metric_definitions)
        row_counts = {
            "cell_metrics.csv": _write_csv(
                temporary / "cell_metrics.csv",
                columns=CELL_METRIC_COLUMNS,
                rows=validated.cell_rows,
            ),
            "region_metrics.csv": _write_csv(
                temporary / "region_metrics.csv",
                columns=REGION_METRIC_COLUMNS,
                rows=validated.region_rows,
            ),
            "paired_method_metrics.csv": _write_csv(
                temporary / "paired_method_metrics.csv",
                columns=PAIRED_METRIC_COLUMNS,
                rows=validated.paired_rows,
            ),
            "configuration_metrics.csv": _write_csv(
                temporary / "configuration_metrics.csv",
                columns=CONFIGURATION_METRIC_COLUMNS,
                rows=validated.configuration_rows,
            ),
        }
        artifacts_before_seal = _artifact_inventory(temporary)
        validation = validated.validation_record
        seal_without_digest: dict[str, object] = {
            "schema_version": STAGE3B_B0_SEAL_SCHEMA_VERSION,
            "seal_scope": STAGE3B_B0_SEAL_SCOPE,
            "evidence_scope": STAGE3B_B0_EVIDENCE_SCOPE,
            "status": "sealed",
            "campaign_id": STAGE3B_CAMPAIGN_ID,
            "candidate_id": B0_CANDIDATE_ID,
            "source_archive_inventory_sha256": validation[
                "source_archive_inventory_sha256"
            ],
            "source_commit": validation["source_commit"],
            "sealing_source_commit": sealer_commit,
            "image_digest": validation["image_digest"],
            "manifest_digest": validation["manifest_digest"],
            "authorization_token": validation["authorization_token"],
            "run_id": validation["run_id"],
            "run_completed_at": validation["run_completed_at"],
            "canonical_protocol": validation["canonical_protocol"],
            "statistical_unit": "model_seed",
            "row_counts": row_counts,
            "source_record_digests": validation["source_record_digests"],
            "derivative_artifacts": artifacts_before_seal,
            "source_records_evidence": False,
            "evidence": True,
            "full_b0_campaign_complete": True,
            "full_stage3b_campaign_complete": False,
            "results_publication_permitted": True,
            "test_dataset_access": False,
            "limitations": [
                "The seal covers the Stage 3B B0 stage2_baseline candidate only.",
                "The full Stage 3B candidate campaign remains incomplete.",
                "Raw canonical records remain immutable external archive inputs.",
                "No test dataset was accessed by this synthetic scaling campaign.",
            ],
        }
        seal_digest = _digest_payload(
            {"domain": STAGE3B_B0_SEAL_DOMAIN, "record": seal_without_digest}
        )
        seal = {**seal_without_digest, "seal_digest": seal_digest}
        _write_json(temporary / "seal.json", seal)
        _write_sha256sums(temporary)

        for record in _artifact_inventory(temporary, excluded={"SHA256SUMS"}):
            path = temporary / str(record["path"])
            if _sha256_file(path) != record["sha256"]:
                raise Stage3BSealingError(f"derivative artifact verification failed: {path}")
        verify_archive_inventory(
            source,
            expected_inventory_sha256=expected_archive_inventory_sha256,
        )
        os.replace(temporary, destination)
        return SealedB0Bundle(
            output_root=destination,
            seal_digest=seal_digest,
            source_archive_inventory_sha256=str(
                validation["source_archive_inventory_sha256"]
            ),
            artifact_count=len(_artifact_inventory(destination)),
        )
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
