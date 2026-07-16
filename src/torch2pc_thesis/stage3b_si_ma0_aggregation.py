"""Aggregate and seal the Stage 3B SI-MA0 confirmatory cohort."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import random
import statistics
import subprocess
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

CONTRACT_ID: Final = "stage3b-si-ma0-v2"
EVIDENCE_SCHEMA_ID: Final = "stage3b-si-ma0-confirmatory-evidence-v1"
EXPECTED_EXECUTION_SOURCE_COMMIT: Final = (
    "03016e68ecc7a850da7148d676f47acfb07cc99e"
)
EXPECTED_SEEDS: Final = tuple(range(10))
EXPECTED_BATCH_IDS: Final = (0, 1, 2)
REGIONS: Final = (
    "inference_setup",
    "lower_prediction_and_error",
    "upper_state_vjp",
    "component_aggregation",
    "belief_update",
    "sweep_bookkeeping",
    "inference_finalize",
)
EXPECTED_COUNTS: Final = {
    "si_ma0_event_records.csv": 3000,
    "si_ma0_output_error_records.csv": 600,
    "si_ma0_mode_comparisons.csv": 150,
    "si_ma0_total_timing_records.csv": 7500,
    "si_ma0_region_timing_records.csv": 52500,
    "si_ma0_model_region_summaries.csv": 70,
}
PER_SEED_COUNTS: Final = {
    "si_ma0_event_records.csv": 300,
    "si_ma0_output_error_records.csv": 60,
    "si_ma0_mode_comparisons.csv": 15,
    "si_ma0_total_timing_records.csv": 750,
    "si_ma0_region_timing_records.csv": 5250,
    "si_ma0_model_region_summaries.csv": 7,
}
CONCATENATED_CSV_FILES: Final = (
    "si_ma0_event_records.csv",
    "si_ma0_output_error_records.csv",
    "si_ma0_mode_comparisons.csv",
    "si_ma0_total_timing_records.csv",
    "si_ma0_region_timing_records.csv",
    "si_ma0_vjp_records.csv",
    "si_ma0_saved_tensor_records.csv",
    "si_ma0_graph_lifetime_records.csv",
    "si_ma0_batch_summaries.csv",
    "si_ma0_model_region_summaries.csv",
)
MANDATORY_CELL_FILES: Final = (
    "si_ma0_contract.json",
    "si_ma0_attempts.jsonl",
    "si_ma0_environment.json",
    *CONCATENATED_CSV_FILES,
    "si_ma0_summary.json",
    "si_ma0_decision.json",
    "SHA256SUMS",
)
GENERATED_FILES: Final = (
    "si_ma0_contract.json",
    "si_ma0_attempts.jsonl",
    "si_ma0_environment.json",
    *CONCATENATED_CSV_FILES,
    "si_ma0_seed_summaries.csv",
    "si_ma0_cost_share_seed_values.csv",
    "si_ma0_cost_share_statistics.csv",
    "si_ma0_accounting_residual_statistics.json",
    "si_ma0_source_attempt_manifest.json",
    "si_ma0_obs_oh0_context.json",
    "si_ma0_summary.json",
    "si_ma0_decision.json",
    "si_ma0_report.md",
    "si_ma0_report_EN.md",
    "SHA256SUMS",
)
MAX_ACCOUNTING_RESIDUAL: Final = 0.05
MIN_PASSING_STEP_FRACTION: Final = 0.99
MIN_PASSING_REPETITION_FRACTION: Final = 1.0
BOOTSTRAP_REPEATS: Final = 10_000
BOOTSTRAP_SEED: Final = 20_260_715
OBS_OH0_PATH: Final = Path(
    "results/stage-3/a1-shortcut-observer-controls/sealed/"
    "obs-oh0-v1/rocm/obs_oh0_timing_summary.json"
)
A1_MECHANISM_DECISION_PATH: Final = Path(
    "results/stage-3/a1-mechanism-controls/confirmatory/"
    "mechanism-controls-decision.json"
)


class AggregationError(RuntimeError):
    """Raised when confirmatory evidence is incomplete or inconsistent."""


@dataclass(frozen=True)
class Cell:
    seed: int
    root: Path
    summary: dict[str, Any]
    environment: dict[str, Any]
    decision: dict[str, Any]
    attempts: tuple[dict[str, Any], ...]
    manifest_sha256: str


@dataclass(frozen=True)
class AggregationInputs:
    repo: Path
    working_root: Path
    output_root: Path
    attempt_name: str
    execution_source_commit: str
    ledger: Path
    checkpoint_inventory: Path
    full_archive: Path


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_digest(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256_bytes(payload)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AggregationError(f"unable to read JSON: {path}") from exc


def load_json_object(path: Path) -> dict[str, Any]:
    value = load_json(path)
    if not isinstance(value, dict):
        raise AggregationError(f"expected JSON object: {path}")
    return value


def load_jsonl(path: Path) -> tuple[dict[str, Any], ...]:
    records: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise AggregationError(f"unable to read JSONL: {path}") from exc
    for line_number, raw in enumerate(lines, start=1):
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise AggregationError(
                f"invalid JSONL record at {path}:{line_number}"
            ) from exc
        if not isinstance(value, dict):
            raise AggregationError(
                f"JSONL record is not an object at {path}:{line_number}"
            )
        records.append(value)
    if not records:
        raise AggregationError(f"JSONL file is empty: {path}")
    return tuple(records)


def parse_bool(value: Any, *, field: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes"}:
            return True
        if normalized in {"false", "0", "no"}:
            return False
    raise AggregationError(f"invalid boolean for {field}: {value!r}")


def parse_int(value: Any, *, field: str) -> int:
    if isinstance(value, bool):
        raise AggregationError(f"invalid integer for {field}: {value!r}")
    try:
        return int(str(value))
    except (TypeError, ValueError) as exc:
        raise AggregationError(
            f"invalid integer for {field}: {value!r}"
        ) from exc


def parse_float(value: Any, *, field: str) -> float:
    try:
        parsed = float(str(value))
    except (TypeError, ValueError) as exc:
        raise AggregationError(
            f"invalid float for {field}: {value!r}"
        ) from exc
    return parsed


def git_output(repo: Path, *args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo), *args],
            text=True,
            stderr=subprocess.STDOUT,
        ).strip()
    except subprocess.CalledProcessError as exc:
        raise AggregationError(
            f"git command failed: git {' '.join(args)}\n{exc.output}"
        ) from exc


def require_clean_repository(repo: Path) -> str:
    if not (repo / ".git").exists():
        raise AggregationError(f"not a Git worktree: {repo}")
    status = git_output(repo, "status", "--porcelain")
    if status:
        raise AggregationError(
            "aggregation requires a clean implementation worktree:\n" + status
        )
    return git_output(repo, "rev-parse", "HEAD")


def parse_sha256_manifest(path: Path) -> tuple[tuple[str, Path], ...]:
    entries: list[tuple[str, Path]] = []
    seen: set[Path] = set()
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise AggregationError(f"unable to read manifest: {path}") from exc
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        if "  " not in line:
            raise AggregationError(
                f"invalid SHA256SUMS line {path}:{line_number}"
            )
        digest, relative_raw = line.split("  ", 1)
        if len(digest) != 64 or any(
            character not in "0123456789abcdef" for character in digest
        ):
            raise AggregationError(
                f"invalid SHA256 digest at {path}:{line_number}"
            )
        relative = Path(relative_raw)
        if relative.is_absolute() or ".." in relative.parts:
            raise AggregationError(
                f"unsafe SHA256SUMS path at {path}:{line_number}"
            )
        if relative in seen:
            raise AggregationError(
                f"duplicate SHA256SUMS path at {path}:{line_number}"
            )
        seen.add(relative)
        entries.append((digest, relative))
    if not entries:
        raise AggregationError(f"empty SHA256SUMS: {path}")
    return tuple(entries)


def verify_manifest(root: Path) -> str:
    manifest_path = root / "SHA256SUMS"
    entries = parse_sha256_manifest(manifest_path)
    for expected, relative in entries:
        artifact = root / relative
        if not artifact.is_file():
            raise AggregationError(f"manifest artifact is missing: {artifact}")
        actual = sha256_file(artifact)
        if actual != expected:
            raise AggregationError(
                f"checksum mismatch for {artifact}: {actual} != {expected}"
            )
    return sha256_file(manifest_path)


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise AggregationError(f"CSV has no header: {path}")
            rows = list(reader)
            return list(reader.fieldnames), rows
    except OSError as exc:
        raise AggregationError(f"unable to read CSV: {path}") from exc


def write_csv(
    path: Path,
    rows: Sequence[Mapping[str, Any]],
    *,
    fieldnames: Sequence[str] | None = None,
) -> None:
    if fieldnames is None:
        ordered: list[str] = []
        seen: set[str] = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    ordered.append(key)
        fieldnames = ordered
    if not fieldnames:
        raise AggregationError(f"cannot write headerless CSV: {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: normalize_csv_value(row.get(key))
                    for key in fieldnames
                }
            )


def normalize_csv_value(value: Any) -> Any:
    if isinstance(value, dict | list | tuple):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return value


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def percentile(values: Sequence[float], probability: float) -> float:
    if not values:
        raise AggregationError("percentile requires nonempty values")
    if not 0.0 <= probability <= 1.0:
        raise AggregationError("percentile probability must be in [0, 1]")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = probability * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def descriptive_statistics(values: Sequence[float]) -> dict[str, float | int]:
    if not values:
        raise AggregationError("statistics require nonempty values")
    q1 = percentile(values, 0.25)
    q3 = percentile(values, 0.75)
    return {
        "n": len(values),
        "min": min(values),
        "q1": q1,
        "median": statistics.median(values),
        "mean": statistics.fmean(values),
        "q3": q3,
        "iqr": q3 - q1,
        "p95": percentile(values, 0.95),
        "max": max(values),
    }


def bootstrap_interval(
    values: Sequence[float],
    *,
    statistic: str,
    repeats: int = BOOTSTRAP_REPEATS,
    seed: int = BOOTSTRAP_SEED,
) -> tuple[float, float]:
    if not values:
        raise AggregationError("bootstrap requires nonempty values")
    if repeats <= 0:
        raise AggregationError("bootstrap repeats must be positive")
    if statistic not in {"median", "mean"}:
        raise AggregationError(f"unsupported bootstrap statistic: {statistic}")
    rng = random.Random(seed)
    population = tuple(values)
    size = len(population)
    estimates: list[float] = []
    for _ in range(repeats):
        sample = [population[rng.randrange(size)] for _ in range(size)]
        if statistic == "median":
            estimates.append(float(statistics.median(sample)))
        else:
            estimates.append(float(statistics.fmean(sample)))
    return percentile(estimates, 0.025), percentile(estimates, 0.975)


def validate_summary(
    summary: Mapping[str, Any],
    *,
    seed: int,
    execution_source_commit: str,
) -> None:
    expected = {
        "scope": "confirmatory",
        "lane": "rocm",
        "model_seed": seed,
        "contract_id": CONTRACT_ID,
        "source_git_commit": execution_source_commit,
        "image_revision": execution_source_commit,
        "dataset_loader_used": True,
        "test_split_access": False,
        "confirmatory_cell_decision_made": True,
        "confirmatory_decision_made": False,
        "si_ma0_passed": None,
    }
    mismatches = {
        key: {"observed": summary.get(key), "expected": value}
        for key, value in expected.items()
        if summary.get(key) != value
    }
    if mismatches:
        raise AggregationError(
            f"seed {seed} summary mismatch: "
            + json.dumps(mismatches, sort_keys=True)
        )
    for field in (
        "rec_ma0_cell_passed",
        "obs_ma0_cell_passed",
        "ver_ma0_cell_passed",
        "cost_ma0_cell_passed",
        "cmp_ma0_cell_passed",
        "confirmatory_cell_passed",
    ):
        if not isinstance(summary.get(field), bool):
            raise AggregationError(
                f"seed {seed} summary field must be boolean: {field}"
            )


def discover_cells(inputs: AggregationInputs) -> tuple[Cell, ...]:
    cells: list[Cell] = []
    for seed in EXPECTED_SEEDS:
        root = inputs.working_root / f"seed-{seed}" / inputs.attempt_name
        if not root.is_dir():
            raise AggregationError(f"missing seed-{seed} attempt: {root}")
        missing = [
            name for name in MANDATORY_CELL_FILES if not (root / name).is_file()
        ]
        if missing:
            raise AggregationError(
                f"seed {seed} attempt is incomplete; missing: {missing}"
            )
        manifest_sha = verify_manifest(root)
        summary = load_json_object(root / "si_ma0_summary.json")
        validate_summary(
            summary,
            seed=seed,
            execution_source_commit=inputs.execution_source_commit,
        )
        environment = load_json_object(root / "si_ma0_environment.json")
        decision = load_json_object(root / "si_ma0_decision.json")
        attempts = load_jsonl(root / "si_ma0_attempts.jsonl")
        attempt_id = summary.get("attempt_id")
        if not isinstance(attempt_id, str) or not attempt_id:
            raise AggregationError(f"seed {seed} summary has no attempt_id")
        if not any(record.get("attempt_id") == attempt_id for record in attempts):
            raise AggregationError(
                f"seed {seed} attempts JSONL omits summary attempt_id"
            )
        cells.append(
            Cell(
                seed=seed,
                root=root,
                summary=summary,
                environment=environment,
                decision=decision,
                attempts=attempts,
                manifest_sha256=manifest_sha,
            )
        )
    return tuple(cells)


def verify_contracts(
    repo_contract_path: Path,
    cells: Sequence[Cell],
) -> tuple[dict[str, Any], bytes]:
    repo_contract = load_json_object(repo_contract_path)
    if repo_contract.get("contract_id") != CONTRACT_ID:
        raise AggregationError("repository SI-MA0 contract id mismatch")
    repo_digest = canonical_json_digest(repo_contract)
    first_bytes: bytes | None = None
    for cell in cells:
        path = cell.root / "si_ma0_contract.json"
        payload = path.read_bytes()
        contract = load_json_object(path)
        if canonical_json_digest(contract) != repo_digest:
            raise AggregationError(
                f"seed {cell.seed} contract differs from frozen contract"
            )
        if first_bytes is None:
            first_bytes = payload
        elif payload != first_bytes:
            raise AggregationError(
                f"seed {cell.seed} contract bytes differ across cells"
            )
    if first_bytes is None:
        raise AggregationError("no SI-MA0 contracts discovered")
    return repo_contract, first_bytes


def verify_cell_csv_counts(cells: Sequence[Cell]) -> None:
    for cell in cells:
        for filename, expected_count in PER_SEED_COUNTS.items():
            _, rows = read_csv(cell.root / filename)
            if len(rows) != expected_count:
                raise AggregationError(
                    f"seed {cell.seed} {filename}: "
                    f"{len(rows)} != {expected_count}"
                )
            for row in rows:
                if "model_seed" in row and parse_int(
                    row["model_seed"], field="model_seed"
                ) != cell.seed:
                    raise AggregationError(
                        f"seed {cell.seed} {filename} contains another seed"
                    )


def concatenate_csvs(
    cells: Sequence[Cell],
    output_root: Path,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for filename in CONCATENATED_CSV_FILES:
        fieldnames: list[str] | None = None
        combined: list[dict[str, str]] = []
        for cell in cells:
            current_fields, rows = read_csv(cell.root / filename)
            if fieldnames is None:
                fieldnames = current_fields
            elif current_fields != fieldnames:
                raise AggregationError(
                    f"CSV schema mismatch for {filename} at seed {cell.seed}"
                )
            combined.extend(rows)
        if fieldnames is None:
            raise AggregationError(f"no CSV schema found for {filename}")
        write_csv(output_root / filename, combined, fieldnames=fieldnames)
        counts[filename] = len(combined)
    for filename, expected in EXPECTED_COUNTS.items():
        if counts.get(filename) != expected:
            raise AggregationError(
                f"global count mismatch for {filename}: "
                f"{counts.get(filename)} != {expected}"
            )
    return counts


def concatenate_attempts(cells: Sequence[Cell], output_path: Path) -> int:
    records: list[dict[str, Any]] = []
    seen_attempt_ids: set[str] = set()
    for cell in cells:
        for record in cell.attempts:
            attempt_id = record.get("attempt_id")
            if not isinstance(attempt_id, str) or not attempt_id:
                raise AggregationError(
                    f"seed {cell.seed} attempt record has no attempt_id"
                )
            if attempt_id in seen_attempt_ids:
                raise AggregationError(f"duplicate attempt_id: {attempt_id}")
            seen_attempt_ids.add(attempt_id)
            records.append(record)
    with output_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(
                json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
            )
    return len(records)


def verify_ledger_and_archives(
    ledger_path: Path,
    cells: Sequence[Cell],
    execution_source_commit: str,
) -> dict[int, dict[str, Any]]:
    fieldnames, rows = read_csv_tsv(ledger_path)
    required = {
        "seed",
        "attempt_id",
        "source_git_commit",
        "image_revision",
        "archive",
        "archive_sha256",
    }
    if not required.issubset(fieldnames):
        raise AggregationError(
            f"ledger missing fields: {sorted(required.difference(fieldnames))}"
        )
    by_seed: dict[int, dict[str, Any]] = {}
    summary_by_seed = {cell.seed: cell.summary for cell in cells}
    for row in rows:
        seed = parse_int(row.get("seed"), field="ledger.seed")
        if seed in by_seed:
            raise AggregationError(f"duplicate ledger seed: {seed}")
        if seed not in summary_by_seed:
            raise AggregationError(f"unexpected ledger seed: {seed}")
        summary = summary_by_seed[seed]
        if row.get("attempt_id") != summary.get("attempt_id"):
            raise AggregationError(f"ledger attempt mismatch for seed {seed}")
        if row.get("source_git_commit") != execution_source_commit:
            raise AggregationError(f"ledger source mismatch for seed {seed}")
        if row.get("image_revision") != execution_source_commit:
            raise AggregationError(f"ledger image mismatch for seed {seed}")
        archive = Path(str(row.get("archive", ""))).expanduser().resolve()
        expected_sha = str(row.get("archive_sha256", ""))
        if not archive.is_file():
            raise AggregationError(f"seed {seed} archive is missing: {archive}")
        actual_sha = sha256_file(archive)
        if actual_sha != expected_sha:
            raise AggregationError(
                f"seed {seed} archive hash mismatch: "
                f"{actual_sha} != {expected_sha}"
            )
        by_seed[seed] = {
            "archive": str(archive),
            "archive_sha256": actual_sha,
        }
    if sorted(by_seed) != list(EXPECTED_SEEDS):
        raise AggregationError("ledger does not contain exactly seeds 0..9")
    return by_seed


def read_csv_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            if reader.fieldnames is None:
                raise AggregationError(f"TSV has no header: {path}")
            return list(reader.fieldnames), list(reader)
    except OSError as exc:
        raise AggregationError(f"unable to read TSV: {path}") from exc


def verify_checkpoint_inventory(
    inventory_path: Path,
    *,
    repo: Path,
    execution_source_commit: str,
) -> dict[int, dict[str, Any]]:
    inventory = load_json_object(inventory_path)
    if inventory.get("status") != "ready":
        raise AggregationError("checkpoint inventory status is not ready")
    if inventory.get("execution_scope") != "confirmatory":
        raise AggregationError("checkpoint inventory scope mismatch")
    if inventory.get("source_git_commit") != execution_source_commit:
        raise AggregationError("checkpoint inventory source mismatch")
    records = inventory.get("checkpoints")
    if not isinstance(records, list):
        raise AggregationError("checkpoint inventory records are missing")
    by_seed: dict[int, dict[str, Any]] = {}
    for raw in records:
        if not isinstance(raw, dict):
            raise AggregationError("invalid checkpoint inventory record")
        seed = parse_int(raw.get("model_seed"), field="model_seed")
        if seed in by_seed:
            raise AggregationError(f"duplicate checkpoint seed: {seed}")
        checkpoint_raw = raw.get("checkpoint")
        expected_sha = raw.get("checkpoint_sha256")
        if not isinstance(checkpoint_raw, str) or not checkpoint_raw:
            raise AggregationError(f"invalid checkpoint path for seed {seed}")
        if not isinstance(expected_sha, str) or len(expected_sha) != 64:
            raise AggregationError(f"invalid checkpoint hash for seed {seed}")
        checkpoint = Path(checkpoint_raw)
        if not checkpoint.is_absolute():
            checkpoint = repo / checkpoint
        checkpoint = checkpoint.resolve()
        if not checkpoint.is_file():
            raise AggregationError(
                f"checkpoint missing for seed {seed}: {checkpoint}"
            )
        actual_sha = sha256_file(checkpoint)
        if actual_sha != expected_sha:
            raise AggregationError(
                f"checkpoint hash mismatch for seed {seed}: "
                f"{actual_sha} != {expected_sha}"
            )
        by_seed[seed] = {
            "checkpoint": str(checkpoint),
            "checkpoint_sha256": actual_sha,
        }
    if sorted(by_seed) != list(EXPECTED_SEEDS):
        raise AggregationError(
            "checkpoint inventory does not contain exactly seeds 0..9"
        )
    return by_seed


def verify_full_archive(path: Path) -> str:
    if not path.is_file():
        raise AggregationError(f"full cohort archive is missing: {path}")
    return sha256_file(path)


def verify_prerequisites(repo: Path) -> dict[str, Any]:
    decision_path = repo / A1_MECHANISM_DECISION_PATH
    decision = load_json_object(decision_path)
    fields = decision.get("decision")
    if not isinstance(fields, dict):
        raise AggregationError("A1 mechanism decision fields are missing")
    required = (
        "mechanism_controls_confirmatory_passed",
        "core_controls_passed",
        "si_ma0_open",
    )
    failures = [name for name in required if fields.get(name) is not True]
    if failures:
        raise AggregationError(
            f"SI-MA0 prerequisites are not satisfied: {failures}"
        )
    return {
        "verified": True,
        "decision_path": str(A1_MECHANISM_DECISION_PATH),
        "decision_sha256": sha256_file(decision_path),
        "required_fields": {name: True for name in required},
    }


def compute_seed_summaries(cells: Sequence[Cell]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for cell in cells:
        summary = cell.summary
        timing = summary.get("timing_validation")
        if not isinstance(timing, dict):
            raise AggregationError(
                f"seed {cell.seed} timing_validation is missing"
            )
        rows.append(
            {
                "model_seed": cell.seed,
                "attempt_id": summary["attempt_id"],
                "confirmatory_cell_passed": summary[
                    "confirmatory_cell_passed"
                ],
                "rec_ma0_cell_passed": summary["rec_ma0_cell_passed"],
                "obs_ma0_cell_passed": summary["obs_ma0_cell_passed"],
                "ver_ma0_cell_passed": summary["ver_ma0_cell_passed"],
                "cost_ma0_cell_passed": summary["cost_ma0_cell_passed"],
                "cmp_ma0_cell_passed": summary["cmp_ma0_cell_passed"],
                "passing_measured_step_fraction": timing.get(
                    "passing_measured_step_fraction"
                ),
                "passing_repetition_fraction": timing.get(
                    "passing_repetition_fraction"
                ),
                "source_git_commit": summary["source_git_commit"],
                "image_revision": summary["image_revision"],
                "manifest_sha256": cell.manifest_sha256,
            }
        )
    return rows


def timing_key(row: Mapping[str, str], *, seed: int) -> tuple[int, int, int, int]:
    return (
        seed,
        parse_int(row.get("batch_id"), field="batch_id"),
        parse_int(row.get("timing_repetition"), field="timing_repetition"),
        parse_int(row.get("measured_step"), field="measured_step"),
    )


def analyze_timing(
    cells: Sequence[Cell],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, Any],
    dict[str, Any],
]:
    seed_region_duration: dict[int, dict[str, float]] = {
        seed: {region: 0.0 for region in REGIONS} for seed in EXPECTED_SEEDS
    }
    seed_total_duration: dict[int, float] = {seed: 0.0 for seed in EXPECTED_SEEDS}
    step_records: dict[tuple[int, int, int, int], dict[str, Any]] = {}
    region_sum_by_step: dict[tuple[int, int, int, int], float] = defaultdict(float)
    residual_values: list[float] = []
    finite_failures = 0
    nonnegative_failures = 0

    for cell in cells:
        _, total_rows = read_csv(cell.root / "si_ma0_total_timing_records.csv")
        _, region_rows = read_csv(cell.root / "si_ma0_region_timing_records.csv")
        for row in total_rows:
            key = timing_key(row, seed=cell.seed)
            if key in step_records:
                raise AggregationError(f"duplicate total timing key: {key}")
            total_ms = parse_float(
                row.get("total_device_time_ms"),
                field="total_device_time_ms",
            )
            stored_region_sum = parse_float(
                row.get("exclusive_region_time_sum_ms"),
                field="exclusive_region_time_sum_ms",
            )
            residual = parse_float(
                row.get("accounting_residual"),
                field="accounting_residual",
            )
            finite = parse_bool(row.get("finite"), field="finite")
            nonnegative = parse_bool(
                row.get("nonnegative"), field="nonnegative"
            )
            if not math.isfinite(total_ms) or not math.isfinite(residual):
                finite = False
            if total_ms < 0.0 or stored_region_sum < 0.0:
                nonnegative = False
            finite_failures += int(not finite)
            nonnegative_failures += int(not nonnegative)
            residual_values.append(residual)
            seed_total_duration[cell.seed] += total_ms
            step_records[key] = {
                "total_ms": total_ms,
                "stored_region_sum_ms": stored_region_sum,
                "residual": residual,
                "finite": finite,
                "nonnegative": nonnegative,
            }
        for row in region_rows:
            key = timing_key(row, seed=cell.seed)
            region = str(row.get("region", ""))
            if region not in REGIONS:
                raise AggregationError(f"unexpected timing region: {region!r}")
            duration = parse_float(row.get("duration_ms"), field="duration_ms")
            finite = parse_bool(row.get("finite"), field="region.finite")
            nonnegative = parse_bool(
                row.get("nonnegative"), field="region.nonnegative"
            )
            if not finite or not math.isfinite(duration):
                finite_failures += 1
            if not nonnegative or duration < 0.0:
                nonnegative_failures += 1
            region_sum_by_step[key] += duration
            seed_region_duration[cell.seed][region] += duration

    expected_step_keys = {
        (seed, batch, repetition, step)
        for seed in EXPECTED_SEEDS
        for batch in EXPECTED_BATCH_IDS
        for repetition in range(5)
        for step in range(50)
    }
    if set(step_records) != expected_step_keys:
        missing = sorted(expected_step_keys.difference(step_records))[:20]
        extra = sorted(set(step_records).difference(expected_step_keys))[:20]
        raise AggregationError(
            f"timing step inventory mismatch; missing={missing}, extra={extra}"
        )
    if set(region_sum_by_step) != expected_step_keys:
        raise AggregationError("region timing step inventory is incomplete")

    stored_sum_mismatches = 0
    passing_steps = 0
    for key, record in step_records.items():
        recomputed_sum = region_sum_by_step[key]
        if not math.isclose(
            recomputed_sum,
            float(record["stored_region_sum_ms"]),
            rel_tol=0.0,
            abs_tol=1e-6,
        ):
            stored_sum_mismatches += 1
        recomputed_residual = abs(
            float(record["total_ms"]) - recomputed_sum
        ) / max(float(record["total_ms"]), 1e-12)
        if not math.isclose(
            recomputed_residual,
            float(record["residual"]),
            rel_tol=1e-7,
            abs_tol=1e-6,
        ):
            raise AggregationError(f"accounting residual mismatch at {key}")
        passed = (
            bool(record["finite"])
            and bool(record["nonnegative"])
            and recomputed_residual <= MAX_ACCOUNTING_RESIDUAL
        )
        passing_steps += int(passed)

    repetition_rows: list[dict[str, Any]] = []
    passing_repetitions = 0
    for seed in EXPECTED_SEEDS:
        for batch in EXPECTED_BATCH_IDS:
            for repetition in range(5):
                keys = [
                    (seed, batch, repetition, step) for step in range(50)
                ]
                total_ms = sum(float(step_records[key]["total_ms"]) for key in keys)
                region_ms = sum(region_sum_by_step[key] for key in keys)
                residual = abs(total_ms - region_ms) / max(total_ms, 1e-12)
                finite = all(bool(step_records[key]["finite"]) for key in keys)
                nonnegative = all(
                    bool(step_records[key]["nonnegative"]) for key in keys
                )
                passed = (
                    finite
                    and nonnegative
                    and residual <= MAX_ACCOUNTING_RESIDUAL
                )
                passing_repetitions += int(passed)
                repetition_rows.append(
                    {
                        "model_seed": seed,
                        "batch_id": batch,
                        "timing_repetition": repetition,
                        "total_device_time_ms": total_ms,
                        "exclusive_region_time_sum_ms": region_ms,
                        "accounting_residual": residual,
                        "finite": finite,
                        "nonnegative": nonnegative,
                        "passed": passed,
                    }
                )

    step_fraction = passing_steps / len(step_records)
    repetition_fraction = passing_repetitions / len(repetition_rows)
    cost_gate = (
        finite_failures == 0
        and nonnegative_failures == 0
        and stored_sum_mismatches == 0
        and step_fraction >= MIN_PASSING_STEP_FRACTION
        and repetition_fraction >= MIN_PASSING_REPETITION_FRACTION
    )

    seed_share_rows: list[dict[str, Any]] = []
    values_by_region: dict[str, list[float]] = {
        region: [] for region in (*REGIONS, "unattributed_residual")
    }
    for seed in EXPECTED_SEEDS:
        total_ms = seed_total_duration[seed]
        if not math.isfinite(total_ms) or total_ms <= 0.0:
            raise AggregationError(f"invalid total device time for seed {seed}")
        attributed_share = 0.0
        for region in REGIONS:
            duration = seed_region_duration[seed][region]
            share = duration / total_ms
            attributed_share += share
            values_by_region[region].append(share)
            seed_share_rows.append(
                {
                    "model_seed": seed,
                    "region": region,
                    "region_device_time_ms": duration,
                    "state_inference_total_device_time_ms": total_ms,
                    "cost_share": share,
                    "primary_registered_region": True,
                }
            )
        residual_share = 1.0 - attributed_share
        values_by_region["unattributed_residual"].append(residual_share)
        seed_share_rows.append(
            {
                "model_seed": seed,
                "region": "unattributed_residual",
                "region_device_time_ms": total_ms * residual_share,
                "state_inference_total_device_time_ms": total_ms,
                "cost_share": residual_share,
                "primary_registered_region": False,
            }
        )

    statistics_rows: list[dict[str, Any]] = []
    for region in (*REGIONS, "unattributed_residual"):
        values = values_by_region[region]
        stats = descriptive_statistics(values)
        median_low, median_high = bootstrap_interval(
            values, statistic="median"
        )
        mean_low, mean_high = bootstrap_interval(values, statistic="mean")
        statistics_rows.append(
            {
                "region": region,
                "n_model_seeds": len(values),
                "all_seed_values_json": values,
                "min": stats["min"],
                "q1": stats["q1"],
                "median": stats["median"],
                "mean": stats["mean"],
                "q3": stats["q3"],
                "iqr": stats["iqr"],
                "max": stats["max"],
                "bootstrap_primary_statistic": "median",
                "bootstrap_95_ci_low": median_low,
                "bootstrap_95_ci_high": median_high,
                "bootstrap_mean_95_ci_low": mean_low,
                "bootstrap_mean_95_ci_high": mean_high,
                "bootstrap_repeats": BOOTSTRAP_REPEATS,
                "bootstrap_seed": BOOTSTRAP_SEED,
                "primary_registered_region": region in REGIONS,
            }
        )

    residual_stats = descriptive_statistics(residual_values)
    accounting = {
        "thresholds": {
            "max_relative_residual": MAX_ACCOUNTING_RESIDUAL,
            "minimum_passing_measured_step_fraction": (
                MIN_PASSING_STEP_FRACTION
            ),
            "minimum_passing_repetition_fraction": (
                MIN_PASSING_REPETITION_FRACTION
            ),
        },
        "counts": {
            "measured_steps": len(step_records),
            "repetition_aggregates": len(repetition_rows),
            "passing_measured_steps": passing_steps,
            "passing_repetitions": passing_repetitions,
            "finite_failures": finite_failures,
            "nonnegative_failures": nonnegative_failures,
            "stored_vs_recomputed_region_sum_mismatches": (
                stored_sum_mismatches
            ),
        },
        "passing_measured_step_fraction": step_fraction,
        "passing_repetition_fraction": repetition_fraction,
        "accounting_residual": residual_stats,
        "cost_ma0_passed": cost_gate,
    }
    return seed_share_rows, statistics_rows, accounting, {
        "repetition_rows": repetition_rows,
        "cost_ma0_passed": cost_gate,
    }


def load_obs_oh0_context(repo: Path, residual_median: float) -> dict[str, Any]:
    path = repo / OBS_OH0_PATH
    summary = load_json_object(path)
    arms = summary.get("arm_summaries")
    if not isinstance(arms, dict):
        raise AggregationError("OBS-OH0 arm summaries are missing")
    joint = arms.get("joint_vjp")
    if not isinstance(joint, dict):
        raise AggregationError("OBS-OH0 joint_vjp summary is missing")
    ratios: dict[str, float] = {}
    for field in (
        "primary_runtime_ratio",
        "off_first_median_runtime_ratio",
        "on_first_median_runtime_ratio",
    ):
        value = parse_float(joint.get(field), field=f"OBS-OH0.{field}")
        ratios[field] = value
    overheads = {key: value - 1.0 for key, value in ratios.items()}
    return {
        "source_path": str(OBS_OH0_PATH),
        "source_sha256": sha256_file(path),
        "lane": summary.get("lane"),
        "scope": summary.get("scope"),
        "arm": "joint_vjp",
        "runtime_ratios": ratios,
        "runtime_overheads": overheads,
        "si_ma0_median_accounting_residual": residual_median,
        "absolute_difference_to_primary_overhead": abs(
            residual_median - overheads["primary_runtime_ratio"]
        ),
        "absolute_difference_to_off_first_overhead": abs(
            residual_median - overheads["off_first_median_runtime_ratio"]
        ),
        "absolute_difference_to_on_first_overhead": abs(
            residual_median - overheads["on_first_median_runtime_ratio"]
        ),
        "estimands_are_identical": False,
        "interpretation": (
            "The SI-MA0 accounting residual is descriptively consistent with "
            "the previously sealed ROCm joint-VJP observer-overhead scale, but "
            "the estimands and execution paths differ. This context does not "
            "override the frozen COST-MA0 threshold or decision."
        ),
    }


def compute_global_gates(
    cells: Sequence[Cell],
    *,
    prerequisites_verified: bool,
    cost_ma0_passed: bool,
    counts_verified: bool,
    provenance_verified: bool,
) -> dict[str, bool]:
    return {
        "prerequisites_verified": prerequisites_verified,
        "REC-MA0": all(
            cell.summary.get("rec_ma0_cell_passed") is True for cell in cells
        ),
        "OBS-MA0": all(
            cell.summary.get("obs_ma0_cell_passed") is True for cell in cells
        ),
        "VER-MA0": all(
            cell.summary.get("ver_ma0_cell_passed") is True for cell in cells
        ),
        "COST-MA0": cost_ma0_passed,
        "CMP-MA0": (
            counts_verified
            and provenance_verified
            and all(
                cell.summary.get("cmp_ma0_cell_passed") is True
                for cell in cells
            )
        ),
    }


def render_report_ru(
    *,
    summary: Mapping[str, Any],
    cost_rows: Sequence[Mapping[str, Any]],
    obs_context: Mapping[str, Any],
) -> str:
    stats = {str(row["region"]): row for row in cost_rows}
    residual = summary["accounting_residual_statistics"]["accounting_residual"]
    gates = summary["gates"]
    step_fraction = summary["accounting_residual_statistics"][
        "passing_measured_step_fraction"
    ]
    repetition_fraction = summary["accounting_residual_statistics"][
        "passing_repetition_fraction"
    ]
    primary_overhead = obs_context["runtime_overheads"][
        "primary_runtime_ratio"
    ]
    off_first_overhead = obs_context["runtime_overheads"][
        "off_first_median_runtime_ratio"
    ]
    region_lines = "\n".join(
        f"| `{region}` | {float(stats[region]['median']):.6f} | "
        f"{float(stats[region]['q1']):.6f} | "
        f"{float(stats[region]['q3']):.6f} | "
        f"[{float(stats[region]['bootstrap_95_ci_low']):.6f}, "
        f"{float(stats[region]['bootstrap_95_ci_high']):.6f}] |"
        for region in (*REGIONS, "unattributed_residual")
    )
    gate_lines = "\n".join(
        f"- `{name}`: `{'pass' if passed else 'fail'}`"
        for name, passed in gates.items()
    )
    return (
        "# Stage 3B SI-MA0 — подтверждающий итог\n\n"
        f"**Contract:** `{CONTRACT_ID}`  \n"
        f"**Evidence schema:** `{EVIDENCE_SCHEMA_ID}`  \n"
        f"**Execution source/image:** `{summary['execution_source_commit']}`  \n"
        "**Независимая единица:** model seed, `n=10`\n\n"
        "## Полнота\n\n"
        "Подтверждающий набор содержит все десять model seeds, три фиксированных "
        "validation batches на seed и зарегистрированные количества raw records: "
        "3000 state-update events, 600 output-error records, 150 observer-mode "
        "comparisons, 7500 total timing records, 52500 region timing records и 70 "
        "model-region summaries. Внутренние SHA256 manifests, внешние seed archives, "
        "checkpoint inventory, source commit и image revision проверены.\n\n"
        "## Итоговые gates\n\n"
        f"{gate_lines}\n\n"
        "Итоговое решение: `si_ma0_passed = "
        f"{str(summary['si_ma0_passed']).lower()}`. Evidence является полным, "
        f"поэтому состояние решения — `{summary['decision_state']}`.\n\n"
        "## Атрибуция стоимости\n\n"
        "Доля каждой области сначала вычислена внутри model seed как сумма device "
        "time области, делённая на сумму полного `state_inference` device time. "
        "Bootstrap выполнен только по десяти model seeds (`10000` повторов, seed "
        "`20260715`).\n\n"
        "| Область | Median | Q1 | Q3 | 95% bootstrap CI median |\n"
        "|---|---:|---:|---:|---:|\n"
        f"{region_lines}\n\n"
        "## COST-MA0\n\n"
        "Доля measured steps с accounting residual `<= 0.05`: `"
        f"{float(step_fraction):.6f}`. "
        "Доля прошедших repetition aggregates: `"
        f"{float(repetition_fraction):.6f}`. "
        f"Медианный residual: `{float(residual['median']):.6f}`, средний: "
        f"`{float(residual['mean']):.6f}`. Frozen критерий COST-MA0 не выполнен.\n\n"
        "## Контекст OBS-OH0\n\n"
        "Ранее запечатанный ROCm joint-VJP observer control оценил primary overhead "
        "как `"
        f"{float(primary_overhead):.6f}`, "
        "off-first overhead как `"
        f"{float(off_first_overhead):.6f}`. "
        "Масштаб близок к SI-MA0 residual, но это разные estimands и разные "
        "execution paths. Сопоставление является только описательным и не изменяет "
        "frozen COST-MA0 threshold или итоговый fail.\n\n"
        "## Допустимый вывод\n\n"
        "На зарегистрированных финальных FashionMNIST Strict checkpoints "
        "механизмная реконструкция PC-CATM, численная невозмущающесть наблюдения, "
        "согласованность версий и полнота provenance прошли на всех десяти model "
        "seeds. Строгое пятипроцентное замыкание стоимости по семи областям не "
        "прошло. Поэтому SI-MA0 в целом завершён как `fail` и не открывает "
        "интерпретацию NCZ/ECZ/TNZ или последующие B1/B2 gates. Отрицательный "
        "COST-MA0 сохраняется как результат, а не как основание для retuning или "
        "replacement.\n"
    )


def render_report_en(
    *,
    summary: Mapping[str, Any],
    cost_rows: Sequence[Mapping[str, Any]],
    obs_context: Mapping[str, Any],
) -> str:
    stats = {str(row["region"]): row for row in cost_rows}
    residual = summary["accounting_residual_statistics"]["accounting_residual"]
    gates = summary["gates"]
    step_fraction = summary["accounting_residual_statistics"][
        "passing_measured_step_fraction"
    ]
    repetition_fraction = summary["accounting_residual_statistics"][
        "passing_repetition_fraction"
    ]
    primary_overhead = obs_context["runtime_overheads"][
        "primary_runtime_ratio"
    ]
    off_first_overhead = obs_context["runtime_overheads"][
        "off_first_median_runtime_ratio"
    ]
    region_lines = "\n".join(
        f"| `{region}` | {float(stats[region]['median']):.6f} | "
        f"{float(stats[region]['q1']):.6f} | "
        f"{float(stats[region]['q3']):.6f} | "
        f"[{float(stats[region]['bootstrap_95_ci_low']):.6f}, "
        f"{float(stats[region]['bootstrap_95_ci_high']):.6f}] |"
        for region in (*REGIONS, "unattributed_residual")
    )
    gate_lines = "\n".join(
        f"- `{name}`: `{'pass' if passed else 'fail'}`"
        for name, passed in gates.items()
    )
    return (
        "# Stage 3B SI-MA0 — confirmatory result\n\n"
        f"**Contract:** `{CONTRACT_ID}`  \n"
        f"**Evidence schema:** `{EVIDENCE_SCHEMA_ID}`  \n"
        f"**Execution source/image:** `{summary['execution_source_commit']}`  \n"
        "**Independent unit:** model seed, `n=10`\n\n"
        "## Completeness\n\n"
        "The confirmatory evidence contains all ten model seeds, the three frozen "
        "validation batches per seed, and all registered raw-record counts: 3000 "
        "state-update events, 600 output-error records, 150 observer-mode "
        "comparisons, 7500 total timing records, 52500 region timing records, and "
        "70 model-region summaries. Internal SHA256 manifests, external seed "
        "archives, checkpoint inventory, source commit, and image revision were "
        "verified.\n\n"
        "## Final gates\n\n"
        f"{gate_lines}\n\n"
        "Final decision: `si_ma0_passed = "
        f"{str(summary['si_ma0_passed']).lower()}`. The evidence is complete, so "
        f"the decision state is `{summary['decision_state']}`.\n\n"
        "## Cost attribution\n\n"
        "Each region share was first computed within model seed as summed region "
        "device time divided by summed full `state_inference` device time. "
        "Bootstrap resampling used only the ten model seeds (`10000` repeats, seed "
        "`20260715`).\n\n"
        "| Region | Median | Q1 | Q3 | 95% bootstrap CI median |\n"
        "|---|---:|---:|---:|---:|\n"
        f"{region_lines}\n\n"
        "## COST-MA0\n\n"
        "Fraction of measured steps with accounting residual `<= 0.05`: `"
        f"{float(step_fraction):.6f}`. "
        "Passing repetition-aggregate fraction: `"
        f"{float(repetition_fraction):.6f}`. "
        f"Median residual: `{float(residual['median']):.6f}`; mean residual: "
        f"`{float(residual['mean']):.6f}`. The frozen COST-MA0 criterion failed.\n\n"
        "## OBS-OH0 context\n\n"
        "The previously sealed ROCm joint-VJP observer control estimated primary "
        "overhead at `"
        f"{float(primary_overhead):.6f}` "
        "and off-first overhead at `"
        f"{float(off_first_overhead):.6f}`. "
        "The scale is close to the SI-MA0 residual, but the estimands and execution "
        "paths differ. The comparison is descriptive only and does not override "
        "the frozen COST-MA0 threshold or final failure.\n\n"
        "## Allowed conclusion\n\n"
        "Across the registered final FashionMNIST Strict checkpoints, PC-CATM "
        "mechanism reconstruction, numerical observer non-interference, version "
        "coherence, and provenance completeness passed for all ten model seeds. "
        "The strict five-percent cost closure over the seven registered regions "
        "failed. SI-MA0 therefore ends as `fail` and does not open NCZ/ECZ/TNZ "
        "interpretation or the subsequent B1/B2 gates. The negative COST-MA0 "
        "result is retained rather than used to justify retuning or replacement.\n"
    )


def build_source_manifest(
    *,
    inputs: AggregationInputs,
    cells: Sequence[Cell],
    archives: Mapping[int, Mapping[str, Any]],
    checkpoints: Mapping[int, Mapping[str, Any]],
    aggregation_source_commit: str,
    full_archive_sha256: str,
) -> dict[str, Any]:
    return {
        "schema_id": "stage3b-si-ma0-source-attempt-manifest-v1",
        "contract_id": CONTRACT_ID,
        "execution_source_commit": inputs.execution_source_commit,
        "aggregation_source_commit": aggregation_source_commit,
        "attempt_name": inputs.attempt_name,
        "checkpoint_inventory": {
            "path": str(inputs.checkpoint_inventory),
            "sha256": sha256_file(inputs.checkpoint_inventory),
        },
        "ledger": {
            "path": str(inputs.ledger),
            "sha256": sha256_file(inputs.ledger),
        },
        "full_archive": {
            "path": str(inputs.full_archive),
            "sha256": full_archive_sha256,
        },
        "cells": [
            {
                "model_seed": cell.seed,
                "attempt_id": cell.summary["attempt_id"],
                "output_root": str(cell.root.relative_to(inputs.repo)),
                "cell_sha256_manifest_sha256": cell.manifest_sha256,
                "summary_sha256": sha256_file(
                    cell.root / "si_ma0_summary.json"
                ),
                "decision_sha256": sha256_file(
                    cell.root / "si_ma0_decision.json"
                ),
                "archive": archives[cell.seed],
                "checkpoint": checkpoints[cell.seed],
            }
            for cell in cells
        ],
    }


def write_evidence_manifest(output_root: Path) -> None:
    paths = [
        path
        for path in sorted(output_root.iterdir(), key=lambda item: item.name)
        if path.is_file() and path.name != "SHA256SUMS"
    ]
    with (output_root / "SHA256SUMS").open("w", encoding="utf-8") as handle:
        for path in paths:
            handle.write(f"{sha256_file(path)}  {path.name}\n")


def aggregate(inputs: AggregationInputs) -> dict[str, Any]:
    aggregation_source_commit = require_clean_repository(inputs.repo)
    if inputs.execution_source_commit != EXPECTED_EXECUTION_SOURCE_COMMIT:
        raise AggregationError(
            "unexpected SI-MA0 execution source commit: "
            f"{inputs.execution_source_commit}"
        )
    if inputs.output_root.exists() and any(inputs.output_root.iterdir()):
        raise AggregationError(
            f"confirmatory evidence output must be new and empty: "
            f"{inputs.output_root}"
        )
    inputs.output_root.mkdir(parents=True, exist_ok=True)

    try:
        cells = discover_cells(inputs)
        repo_contract_path = (
            inputs.repo
            / "experiments/planned/STAGE3B-SI-MA0-CONTRACT.json"
        )
        contract, contract_bytes = verify_contracts(repo_contract_path, cells)
        verify_cell_csv_counts(cells)
        prerequisites = verify_prerequisites(inputs.repo)
        archives = verify_ledger_and_archives(
            inputs.ledger,
            cells,
            inputs.execution_source_commit,
        )
        checkpoints = verify_checkpoint_inventory(
            inputs.checkpoint_inventory,
            repo=inputs.repo,
            execution_source_commit=inputs.execution_source_commit,
        )
        full_archive_sha = verify_full_archive(inputs.full_archive)

        (inputs.output_root / "si_ma0_contract.json").write_bytes(
            contract_bytes
        )
        attempt_count = concatenate_attempts(
            cells, inputs.output_root / "si_ma0_attempts.jsonl"
        )
        combined_counts = concatenate_csvs(cells, inputs.output_root)

        seed_summaries = compute_seed_summaries(cells)
        write_csv(
            inputs.output_root / "si_ma0_seed_summaries.csv",
            seed_summaries,
        )
        (
            seed_cost_shares,
            cost_statistics,
            accounting,
            timing_details,
        ) = analyze_timing(cells)
        write_csv(
            inputs.output_root / "si_ma0_cost_share_seed_values.csv",
            seed_cost_shares,
        )
        write_csv(
            inputs.output_root / "si_ma0_cost_share_statistics.csv",
            cost_statistics,
        )
        write_json(
            inputs.output_root / "si_ma0_accounting_residual_statistics.json",
            accounting,
        )

        residual_median = float(accounting["accounting_residual"]["median"])
        obs_context = load_obs_oh0_context(inputs.repo, residual_median)
        write_json(
            inputs.output_root / "si_ma0_obs_oh0_context.json",
            obs_context,
        )

        source_manifest = build_source_manifest(
            inputs=inputs,
            cells=cells,
            archives=archives,
            checkpoints=checkpoints,
            aggregation_source_commit=aggregation_source_commit,
            full_archive_sha256=full_archive_sha,
        )
        write_json(
            inputs.output_root / "si_ma0_source_attempt_manifest.json",
            source_manifest,
        )

        counts_verified = all(
            combined_counts.get(filename) == expected
            for filename, expected in EXPECTED_COUNTS.items()
        )
        provenance_verified = (
            len(cells) == 10
            and all(
                cell.summary.get("source_git_commit")
                == inputs.execution_source_commit
                and cell.summary.get("image_revision")
                == inputs.execution_source_commit
                and cell.summary.get("test_split_access") is False
                for cell in cells
            )
        )
        gates = compute_global_gates(
            cells,
            prerequisites_verified=bool(prerequisites["verified"]),
            cost_ma0_passed=bool(timing_details["cost_ma0_passed"]),
            counts_verified=counts_verified,
            provenance_verified=provenance_verified,
        )
        si_ma0_passed = all(gates.values())
        decision_state = "pass" if si_ma0_passed else "fail"

        environment = {
            "evidence_schema_id": EVIDENCE_SCHEMA_ID,
            "contract_id": CONTRACT_ID,
            "execution_source_git_commit": inputs.execution_source_commit,
            "execution_image_revision": inputs.execution_source_commit,
            "aggregation_source_git_commit": aggregation_source_commit,
            "aggregation_branch": git_output(
                inputs.repo, "branch", "--show-current"
            ),
            "aggregation_runtime": "host_static_analysis",
            "model_seeds": list(EXPECTED_SEEDS),
            "validation_batch_ids": list(EXPECTED_BATCH_IDS),
            "attempt_count": attempt_count,
            "test_split_access": False,
            "prerequisites": prerequisites,
            "source_attempt_manifest_sha256": canonical_json_digest(
                source_manifest
            ),
            "frozen_contract_sha256": sha256_file(repo_contract_path),
        }
        write_json(
            inputs.output_root / "si_ma0_environment.json", environment
        )

        summary = {
            "evidence_schema_id": EVIDENCE_SCHEMA_ID,
            "contract_id": CONTRACT_ID,
            "scope": "confirmatory",
            "lane": "rocm",
            "execution_source_commit": inputs.execution_source_commit,
            "execution_image_revision": inputs.execution_source_commit,
            "aggregation_source_commit": aggregation_source_commit,
            "model_seeds": list(EXPECTED_SEEDS),
            "validation_batch_ids": list(EXPECTED_BATCH_IDS),
            "independent_unit": "model_seed",
            "n_model_seeds": 10,
            "expected_counts": {
                "state_update_events": 3000,
                "output_error_records": 600,
                "diagnostic_records": 3600,
                "mode_comparisons": 150,
                "total_timing_records": 7500,
                "region_timing_records": 52500,
                "model_region_summary_rows": 70,
            },
            "observed_counts": {
                "state_update_events": combined_counts[
                    "si_ma0_event_records.csv"
                ],
                "output_error_records": combined_counts[
                    "si_ma0_output_error_records.csv"
                ],
                "diagnostic_records": (
                    combined_counts["si_ma0_event_records.csv"]
                    + combined_counts["si_ma0_output_error_records.csv"]
                ),
                "mode_comparisons": combined_counts[
                    "si_ma0_mode_comparisons.csv"
                ],
                "total_timing_records": combined_counts[
                    "si_ma0_total_timing_records.csv"
                ],
                "region_timing_records": combined_counts[
                    "si_ma0_region_timing_records.csv"
                ],
                "model_region_summary_rows": combined_counts[
                    "si_ma0_model_region_summaries.csv"
                ],
            },
            "gates": gates,
            "accounting_residual_statistics": accounting,
            "cost_share_statistics_file": (
                "si_ma0_cost_share_statistics.csv"
            ),
            "obs_oh0_context_file": "si_ma0_obs_oh0_context.json",
            "confirmatory_decision_made": True,
            "si_ma0_passed": si_ma0_passed,
            "decision_state": decision_state,
            "next_stage_open": False,
            "interpretation_boundary": contract.get(
                "interpretation_boundary"
            ),
        }
        write_json(inputs.output_root / "si_ma0_summary.json", summary)

        decision = {
            "evidence_schema_id": EVIDENCE_SCHEMA_ID,
            "contract_id": CONTRACT_ID,
            "final_gate_expression": contract.get("final_gate_expression"),
            "gates": gates,
            "evidence_complete": True,
            "confirmatory_decision_made": True,
            "si_ma0_passed": si_ma0_passed,
            "decision_state": decision_state,
            "authorization": {
                "model_level_passive_ncz_ecz_tnz_interpretation": False,
                "stage3b_b1_b2_open": False,
                "reason": "COST-MA0 failed the frozen accounting threshold.",
            },
            "negative_results_retained": True,
            "threshold_retuned": False,
            "records_excluded_after_first_output": False,
        }
        write_json(inputs.output_root / "si_ma0_decision.json", decision)

        (inputs.output_root / "si_ma0_report.md").write_text(
            render_report_ru(
                summary=summary,
                cost_rows=cost_statistics,
                obs_context=obs_context,
            ),
            encoding="utf-8",
        )
        (inputs.output_root / "si_ma0_report_EN.md").write_text(
            render_report_en(
                summary=summary,
                cost_rows=cost_statistics,
                obs_context=obs_context,
            ),
            encoding="utf-8",
        )
        write_evidence_manifest(inputs.output_root)
        verify_manifest(inputs.output_root)

        missing_generated = [
            filename
            for filename in GENERATED_FILES
            if not (inputs.output_root / filename).is_file()
        ]
        if missing_generated:
            raise AggregationError(
                f"generated evidence files missing: {missing_generated}"
            )
        return summary
    except Exception:
        if inputs.output_root.exists():
            for path in sorted(
                inputs.output_root.rglob("*"),
                key=lambda item: len(item.parts),
                reverse=True,
            ):
                if path.is_file() or path.is_symlink():
                    path.unlink()
                elif path.is_dir():
                    path.rmdir()
            inputs.output_root.rmdir()
        raise
