"""Frozen Stage 3B SI-MA1 confirmatory aggregation primitives."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import shutil
import subprocess
import tempfile
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, cast

import numpy as np

from torch2pc_thesis.stage3b_si_ma1 import (
    CONTRACT_ID,
    IMPLEMENTATION_SCHEMA_ID,
    PREREGISTRATION_COMMIT,
)
from torch2pc_thesis.stage3b_si_ma1_confirmatory import (
    CONFIRMATORY_SCHEMA_ID,
    EXPECTED_MODEL_SEEDS,
    CheckpointInventoryEntry,
    canonical_json_digest,
    load_inventory,
    sha256_file,
    validate_attempt_evidence,
)

AGGREGATION_SCHEMA_ID: Final[str] = (
    "stage3b-si-ma1-confirmatory-aggregation-v1"
)
EXECUTION_TAG: Final[str] = (
    "stage3b-si-ma1-confirmatory-execution-v1"
)
EXECUTION_TAG_COMMIT: Final[str] = (
    "bbbfb73c66d91ad28bf4cba32744e2dd039ea397"
)
DEFAULT_INPUT_ROOT: Final[Path] = Path(
    "results/stage-3/si-ma1/working/confirmatory"
)
DEFAULT_OUTPUT_ROOT: Final[Path] = Path(
    "results/stage-3/si-ma1/confirmatory"
)
CONTRACT_PATH: Final[Path] = Path(
    "experiments/planned/STAGE3B-SI-MA1-CONTRACT.json"
)
BOOTSTRAP_REPEATS: Final[int] = 10_000
BOOTSTRAP_SEED: Final[int] = 20_260_716
BOOTSTRAP_LEVEL: Final[float] = 0.95
EXCESS_MARGIN: Final[float] = 0.01
EXPECTED_BLOCK_ROWS: Final[int] = 180
EXPECTED_ORDER_SEED_ROWS: Final[int] = 60
EXPECTED_SOURCE_REVISION: Final[str] = (
    "55e05efabc223b3473fdea02a5b7ea424a79f759"
)

SOURCE_CSV_FILES: Final[tuple[str, ...]] = (
    "si_ma1_arm_timing_records.csv",
    "si_ma1_region_timing_records.csv",
    "si_ma1_numerical_comparisons.csv",
    "si_ma1_topology_comparisons.csv",
    "si_ma1_block_summaries.csv",
    "si_ma1_seed_summaries.csv",
)
FINAL_MANDATORY_FILES: Final[tuple[str, ...]] = (
    "si_ma1_contract.json",
    "si_ma1_attempts.jsonl",
    "si_ma1_environment.json",
    "si_ma1_arm_timing_records.csv",
    "si_ma1_region_timing_records.csv",
    "si_ma1_numerical_comparisons.csv",
    "si_ma1_topology_comparisons.csv",
    "si_ma1_block_summaries.csv",
    "si_ma1_seed_summaries.csv",
    "si_ma1_order_sensitivity.csv",
    "si_ma1_summary.json",
    "si_ma1_decision.json",
    "si_ma1_report.md",
    "si_ma1_report_EN.md",
    "SHA256SUMS",
)


class SIMA1AggregationError(RuntimeError):
    """Raised when frozen confirmatory aggregation invariants fail."""


@dataclass(frozen=True)
class AttemptRecord:
    """One retained confirmatory attempt selected for aggregation."""

    model_seed: int
    attempt_id: str
    root: Path
    checkpoint_sha256: str
    d_seed: float
    source_git_commit: str
    image_revision: str
    experiment_image: str


@dataclass(frozen=True)
class BootstrapResult:
    """Frozen bootstrap result for one seed-level statistic."""

    observed: float
    mean: float
    lower_two_sided_95: float
    upper_two_sided_95: float
    upper_one_sided_95: float
    repeats: int
    seed: int

    def to_record(self) -> dict[str, int | float]:
        return {
            "observed": self.observed,
            "mean": self.mean,
            "lower_two_sided_95": self.lower_two_sided_95,
            "upper_two_sided_95": self.upper_two_sided_95,
            "upper_one_sided_95": self.upper_one_sided_95,
            "repeats": self.repeats,
            "seed": self.seed,
        }


def _finite_float(value: Any, *, label: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise SIMA1AggregationError(f"{label} is not numeric") from error
    if not math.isfinite(result):
        raise SIMA1AggregationError(f"{label} is not finite")
    return result


def _json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SIMA1AggregationError(f"unable to read JSON: {path}") from error
    if not isinstance(value, dict):
        raise SIMA1AggregationError(f"JSON root must be an object: {path}")
    return cast(dict[str, Any], value)


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(
            dict(value),
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _git_output(repo: Path, *args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=repo,
            text=True,
            stderr=subprocess.STDOUT,
        ).strip()
    except subprocess.CalledProcessError as error:
        raise SIMA1AggregationError(
            f"git command failed: git {' '.join(args)}"
        ) from error


def verify_frozen_execution_base(repo: Path, input_root: Path) -> str:
    """Require the frozen execution tag and unchanged raw input tree."""

    head = _git_output(repo, "rev-parse", "HEAD")
    tag_commit = _git_output(repo, "rev-parse", f"{EXECUTION_TAG}^{{commit}}")
    if tag_commit != EXECUTION_TAG_COMMIT:
        raise SIMA1AggregationError("execution tag target differs")
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", tag_commit, head],
        cwd=repo,
        check=False,
    )
    if ancestry.returncode != 0:
        raise SIMA1AggregationError(
            "execution tag is not an ancestor of aggregation HEAD"
        )
    relative_input = input_root
    if input_root.is_absolute():
        try:
            relative_input = input_root.resolve().relative_to(repo.resolve())
        except ValueError as error:
            raise SIMA1AggregationError(
                "input root must be inside the repository"
            ) from error
    diff = subprocess.run(
        ["git", "diff", "--quiet", EXECUTION_TAG, "--", os.fspath(relative_input)],
        cwd=repo,
        check=False,
    )
    if diff.returncode != 0:
        raise SIMA1AggregationError(
            "raw confirmatory execution evidence differs from execution tag"
        )
    untracked = _git_output(
        repo,
        "ls-files",
        "--others",
        "--exclude-standard",
        "--",
        os.fspath(relative_input),
    )
    if untracked:
        raise SIMA1AggregationError(
            "raw confirmatory execution root contains untracked files"
        )
    return head


def bootstrap_median(
    values: Sequence[float],
    *,
    repeats: int = BOOTSTRAP_REPEATS,
    seed: int = BOOTSTRAP_SEED,
) -> BootstrapResult:
    """Compute the registered model-seed percentile bootstrap."""

    array = np.asarray(values, dtype=np.float64)
    if array.shape != (len(EXPECTED_MODEL_SEEDS),):
        raise SIMA1AggregationError(
            "bootstrap requires exactly ten model-seed values"
        )
    if repeats != BOOTSTRAP_REPEATS or seed != BOOTSTRAP_SEED:
        raise SIMA1AggregationError(
            "bootstrap repeats and seed are frozen by preregistration"
        )
    if not np.all(np.isfinite(array)):
        raise SIMA1AggregationError("bootstrap values must be finite")
    generator = np.random.default_rng(seed)
    indices = generator.integers(
        0,
        len(array),
        size=(repeats, len(array)),
    )
    samples = np.median(array[indices], axis=1)
    return BootstrapResult(
        observed=float(np.median(array)),
        mean=float(np.mean(array)),
        lower_two_sided_95=float(
            np.quantile(samples, 0.025, method="linear")
        ),
        upper_two_sided_95=float(
            np.quantile(samples, 0.975, method="linear")
        ),
        upper_one_sided_95=float(
            np.quantile(samples, BOOTSTRAP_LEVEL, method="linear")
        ),
        repeats=repeats,
        seed=seed,
    )


def read_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """Read one LF-compatible CSV with a mandatory header."""

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise SIMA1AggregationError(f"CSV header is missing: {path}")
        rows = [dict(row) for row in reader]
    return list(reader.fieldnames), rows


def concatenate_csvs(paths: Sequence[Path], destination: Path) -> int:
    """Concatenate homogeneous retained CSV files deterministically."""

    fieldnames: list[str] | None = None
    rows: list[dict[str, str]] = []
    for path in paths:
        current_fields, current_rows = read_csv_rows(path)
        if fieldnames is None:
            fieldnames = current_fields
        elif current_fields != fieldnames:
            raise SIMA1AggregationError(
                f"CSV schema mismatch while concatenating {path.name}"
            )
        rows.extend(current_rows)
    if fieldnames is None:
        raise SIMA1AggregationError("no CSV inputs supplied")
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def recompute_seed_values(
    block_rows: Sequence[Mapping[str, str]],
) -> dict[int, float]:
    """Recompute signed D_seed from the 18 retained blocks per seed."""

    grouped: dict[int, list[float]] = defaultdict(list)
    for row in block_rows:
        seed = int(row["model_seed"])
        grouped[seed].append(
            _finite_float(
                row["calibrated_excess_gap"],
                label="calibrated_excess_gap",
            )
        )
    if tuple(sorted(grouped)) != EXPECTED_MODEL_SEEDS:
        raise SIMA1AggregationError("block summaries do not cover seeds 0..9")
    result: dict[int, float] = {}
    for seed in EXPECTED_MODEL_SEEDS:
        values = grouped[seed]
        if len(values) != 18:
            raise SIMA1AggregationError(
                f"seed {seed} must contain exactly 18 matched blocks"
            )
        result[seed] = float(np.median(np.asarray(values, dtype=np.float64)))
    return result


def validate_seed_values(
    recomputed: Mapping[int, float],
    recorded: Mapping[int, float],
) -> None:
    """Require exact scientific agreement up to serialization precision."""

    if tuple(sorted(recorded)) != EXPECTED_MODEL_SEEDS:
        raise SIMA1AggregationError("recorded D_seed values are incomplete")
    for seed in EXPECTED_MODEL_SEEDS:
        if not math.isclose(
            recomputed[seed],
            recorded[seed],
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise SIMA1AggregationError(
                f"seed {seed} D_seed differs from block-level recomputation"
            )


def build_order_sensitivity_rows(
    block_rows: Sequence[Mapping[str, str]],
) -> list[dict[str, str | int | float | bool]]:
    """Build non-authorizing order-stratified and leave-one-order-out rows."""

    expected_orders = ("ABC", "BCA", "CAB", "ACB", "CBA", "BAC")
    by_seed_order: dict[tuple[int, str], list[float]] = defaultdict(list)
    for row in block_rows:
        key = (int(row["model_seed"]), str(row["order"]))
        by_seed_order[key].append(float(row["calibrated_excess_gap"]))
    rows: list[dict[str, str | int | float | bool]] = []
    for order_index, order in enumerate(expected_orders):
        order_values: list[float] = []
        leave_one_out_values: list[float] = []
        for seed in EXPECTED_MODEL_SEEDS:
            values = by_seed_order[(seed, order)]
            if len(values) != 3:
                raise SIMA1AggregationError(
                    f"seed {seed} order {order} must contain three blocks"
                )
            order_values.append(float(np.median(values)))
            retained = [
                value
                for candidate_order in expected_orders
                if candidate_order != order
                for value in by_seed_order[(seed, candidate_order)]
            ]
            if len(retained) != 15:
                raise SIMA1AggregationError(
                    "leave-one-order-out retained block count differs"
                )
            leave_one_out_values.append(float(np.median(retained)))
        order_result = _secondary_bootstrap(
            order_values,
            BOOTSTRAP_SEED + order_index,
        )
        leave_result = _secondary_bootstrap(
            leave_one_out_values,
            BOOTSTRAP_SEED + 100 + order_index,
        )
        rows.extend(
            (
                {
                    "analysis": "order_stratified",
                    "order": order,
                    "model_seed_count": 10,
                    "observed_median": order_result.observed,
                    "mean_seed_value": order_result.mean,
                    "upper_one_sided_95": order_result.upper_one_sided_95,
                    "lower_two_sided_95": order_result.lower_two_sided_95,
                    "upper_two_sided_95": order_result.upper_two_sided_95,
                    "bootstrap_repeats": BOOTSTRAP_REPEATS,
                    "bootstrap_seed": BOOTSTRAP_SEED + order_index,
                    "authorizes_primary_decision": False,
                },
                {
                    "analysis": "leave_one_order_out",
                    "order": order,
                    "model_seed_count": 10,
                    "observed_median": leave_result.observed,
                    "mean_seed_value": leave_result.mean,
                    "upper_one_sided_95": leave_result.upper_one_sided_95,
                    "lower_two_sided_95": leave_result.lower_two_sided_95,
                    "upper_two_sided_95": leave_result.upper_two_sided_95,
                    "bootstrap_repeats": BOOTSTRAP_REPEATS,
                    "bootstrap_seed": BOOTSTRAP_SEED + 100 + order_index,
                    "authorizes_primary_decision": False,
                },
            )
        )
    return rows


def _secondary_bootstrap(values: Sequence[float], seed: int) -> BootstrapResult:
    """Compute a deterministic non-authorizing secondary bootstrap."""

    array = np.asarray(values, dtype=np.float64)
    if array.shape != (10,) or not np.all(np.isfinite(array)):
        raise SIMA1AggregationError(
            "secondary bootstrap requires ten finite seed values"
        )
    generator = np.random.default_rng(seed)
    indices = generator.integers(0, 10, size=(BOOTSTRAP_REPEATS, 10))
    samples = np.median(array[indices], axis=1)
    return BootstrapResult(
        observed=float(np.median(array)),
        mean=float(np.mean(array)),
        lower_two_sided_95=float(np.quantile(samples, 0.025, method="linear")),
        upper_two_sided_95=float(np.quantile(samples, 0.975, method="linear")),
        upper_one_sided_95=float(np.quantile(samples, 0.95, method="linear")),
        repeats=BOOTSTRAP_REPEATS,
        seed=seed,
    )


def write_rows_csv(
    path: Path,
    rows: Sequence[Mapping[str, Any]],
) -> None:
    """Write homogeneous dictionaries with LF endings."""

    if not rows:
        raise SIMA1AggregationError("cannot write an empty CSV")
    fieldnames = list(rows[0])
    if any(list(row) != fieldnames for row in rows):
        raise SIMA1AggregationError("CSV row schemas differ")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def input_tree_digest(root: Path) -> str:
    """Hash every retained execution file path and content."""

    digest = hashlib.sha256()
    files = sorted(path for path in root.rglob("*") if path.is_file())
    if not files:
        raise SIMA1AggregationError("confirmatory input tree is empty")
    for path in files:
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha256_file(path).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def load_attempts(
    *,
    repo: Path,
    input_root: Path,
) -> tuple[tuple[AttemptRecord, ...], tuple[CheckpointInventoryEntry, ...]]:
    """Validate and select exactly one retained attempt per model seed."""

    cohort = _json_object(input_root / "cohort_execution_summary.json")
    if cohort.get("schema_id") != CONFIRMATORY_SCHEMA_ID:
        raise SIMA1AggregationError("cohort execution schema mismatch")
    if cohort.get("contract_id") != CONTRACT_ID:
        raise SIMA1AggregationError("cohort contract mismatch")
    if cohort.get("cohort_complete") is not True:
        raise SIMA1AggregationError("cohort is not complete")
    if cohort.get("confirmatory_decision_made") is not False:
        raise SIMA1AggregationError("execution cohort already made a decision")
    if cohort.get("CAL-COST-MA1") is not None:
        raise SIMA1AggregationError("execution cohort populated CAL-COST-MA1")
    if cohort.get("si_ma1_passed") is not None:
        raise SIMA1AggregationError("execution cohort populated global result")
    if cohort.get("source_git_commit") != EXPECTED_SOURCE_REVISION:
        raise SIMA1AggregationError("execution source revision mismatch")
    if cohort.get("image_revision") != EXPECTED_SOURCE_REVISION:
        raise SIMA1AggregationError("execution image revision mismatch")

    inventory = load_inventory(
        input_root / "checkpoint_inventory.json",
        repo=repo,
        verify_files=True,
    )
    by_seed = {entry.model_seed: entry for entry in inventory}
    raw_attempts = cohort.get("attempts")
    if not isinstance(raw_attempts, list) or len(raw_attempts) != 10:
        raise SIMA1AggregationError("cohort must contain ten attempts")
    attempts: list[AttemptRecord] = []
    for raw in raw_attempts:
        if not isinstance(raw, dict):
            raise SIMA1AggregationError("cohort attempt record must be an object")
        seed = int(raw["model_seed"])
        attempt_id = str(raw["attempt_id"])
        attempt_root = input_root / f"seed-{seed}" / attempt_id
        summary = validate_attempt_evidence(
            attempt_root,
            inventory_entry=by_seed[seed],
        )
        seed_summary = summary.get("seed_summary")
        if not isinstance(seed_summary, dict):
            raise SIMA1AggregationError("attempt seed summary is missing")
        summary_d = _finite_float(seed_summary.get("d_seed"), label="d_seed")
        cohort_d = _finite_float(raw.get("d_seed"), label="cohort d_seed")
        if not math.isclose(summary_d, cohort_d, rel_tol=0.0, abs_tol=1e-12):
            raise SIMA1AggregationError("cohort and attempt D_seed differ")
        attempts.append(
            AttemptRecord(
                model_seed=seed,
                attempt_id=attempt_id,
                root=attempt_root,
                checkpoint_sha256=str(raw["checkpoint_sha256"]),
                d_seed=summary_d,
                source_git_commit=str(summary["source_git_commit"]),
                image_revision=str(summary["image_revision"]),
                experiment_image=str(summary["experiment_image"]),
            )
        )
    ordered = tuple(sorted(attempts, key=lambda item: item.model_seed))
    if tuple(item.model_seed for item in ordered) != EXPECTED_MODEL_SEEDS:
        raise SIMA1AggregationError("attempt seeds differ from 0..9")
    provenance = {
        (item.source_git_commit, item.image_revision, item.experiment_image)
        for item in ordered
    }
    if len(provenance) != 1:
        raise SIMA1AggregationError("attempt provenance differs across seeds")
    return ordered, inventory


def _copy_contract(repo: Path, destination: Path) -> dict[str, Any]:
    contract = _json_object(repo / CONTRACT_PATH)
    if contract.get("contract_id") != CONTRACT_ID:
        raise SIMA1AggregationError("frozen contract id mismatch")
    primary = contract.get("primary_estimand")
    if not isinstance(primary, dict):
        raise SIMA1AggregationError("frozen primary estimand is missing")
    confidence = primary.get("confidence_bound")
    expected = {
        "bootstrap_repeats": BOOTSTRAP_REPEATS,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "level": BOOTSTRAP_LEVEL,
        "resampling_unit": "model_seed",
        "type": "one-sided percentile bootstrap upper bound",
    }
    if confidence != expected or primary.get("excess_margin") != EXCESS_MARGIN:
        raise SIMA1AggregationError("frozen bootstrap contract differs")
    shutil.copy2(repo / CONTRACT_PATH, destination)
    return contract


def _reports(
    *,
    result: BootstrapResult,
    passed: bool,
    seed_values: Mapping[int, float],
) -> tuple[str, str]:
    state_ru = "ПРОЙДЕН" if passed else "НЕ ПРОЙДЕН"
    state_en = "PASS" if passed else "FAIL"
    seeds = "\n".join(
        f"| {seed} | {seed_values[seed]:.12f} |" for seed in EXPECTED_MODEL_SEEDS
    )
    ru = f"""# Stage 3B SI-MA1 — итоговый confirmatory-отчёт

## Решение

**CAL-COST-MA1: {state_ru}.**

- Наблюдаемая медиана `D_seed`: `{result.observed:.12f}`.
- Односторонняя 95% bootstrap-граница: `{result.upper_one_sided_95:.12f}`.
- Зарегистрированный порог: `{EXCESS_MARGIN:.12f}`.
- Bootstrap: `{result.repeats}` повторов, seed `{result.seed}`.
- Единица ресэмплирования: независимо обученная модель (`model_seed`).

Правило решения: `CAL-COST-MA1 = upper_bound <= 0.01`.
Signed значения сохранены без усечения.

## Значения по model seed

| model_seed | D_seed |
|---:|---:|
{seeds}

## Научная граница

Результат SI-MA1 калибрует стоимость наблюдателя для существующей реализации
`state_inference`. Он не переписывает отрицательный результат SI-MA0, не включает
стоимость ECZ evaluator и не является измерением end-to-end выгоды B1/B2.
"""
    en = f"""# Stage 3B SI-MA1 — final confirmatory report

## Decision

**CAL-COST-MA1: {state_en}.**

- Observed median `D_seed`: `{result.observed:.12f}`.
- One-sided 95% bootstrap upper bound: `{result.upper_one_sided_95:.12f}`.
- Registered threshold: `{EXCESS_MARGIN:.12f}`.
- Bootstrap: `{result.repeats}` resamples, seed `{result.seed}`.
- Resampling unit: independently trained model (`model_seed`).

Decision rule: `CAL-COST-MA1 = upper_bound <= 0.01`.
Signed values were retained without truncation.

## Model-seed values

| model_seed | D_seed |
|---:|---:|
{seeds}

## Scientific boundary

SI-MA1 calibrates observer cost for the existing `state_inference`
implementation. It does not rewrite the negative SI-MA0 result, include ECZ
evaluator cost, or establish end-to-end B1/B2 savings.
"""
    return ru, en


def _write_manifest(root: Path) -> None:
    names = [name for name in FINAL_MANDATORY_FILES if name != "SHA256SUMS"]
    missing = [name for name in names if not (root / name).is_file()]
    if missing:
        raise SIMA1AggregationError(f"final mandatory files are missing: {missing}")
    lines = [f"{sha256_file(root / name)}  {name}" for name in sorted(names)]
    (root / "SHA256SUMS").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def aggregate_confirmatory(
    *,
    repo: Path,
    input_root: Path = DEFAULT_INPUT_ROOT,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    """Validate frozen execution evidence and write final SI-MA1 outputs."""

    repo = repo.resolve()
    if input_root.is_absolute() or output_root.is_absolute():
        raise SIMA1AggregationError("input and output roots must be repository-relative")
    head = verify_frozen_execution_base(repo, input_root)
    source = repo / input_root
    destination = repo / output_root
    if destination.exists() and any(destination.iterdir()):
        raise SIMA1AggregationError("final confirmatory destination must be new and empty")
    attempts, _inventory = load_attempts(repo=repo, input_root=source)
    input_digest = input_tree_digest(source)

    parent = destination.parent
    parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".si-ma1-aggregation-", dir=parent))
    try:
        _copy_contract(repo, temporary / "si_ma1_contract.json")
        shutil.copy2(
            source / "attempt_ledger.jsonl",
            temporary / "si_ma1_attempts.jsonl",
        )
        counts: dict[str, int] = {}
        for name in SOURCE_CSV_FILES:
            counts[name] = concatenate_csvs(
                [attempt.root / name for attempt in attempts],
                temporary / name,
            )
        if counts["si_ma1_block_summaries.csv"] != EXPECTED_BLOCK_ROWS:
            raise SIMA1AggregationError("combined block summary count differs")
        _, block_rows = read_csv_rows(temporary / "si_ma1_block_summaries.csv")
        recomputed = recompute_seed_values(block_rows)
        recorded = {attempt.model_seed: attempt.d_seed for attempt in attempts}
        validate_seed_values(recomputed, recorded)

        order_source_rows = 0
        for attempt in attempts:
            _, rows = read_csv_rows(attempt.root / "si_ma1_order_seed_values.csv")
            order_source_rows += len(rows)
        if order_source_rows != EXPECTED_ORDER_SEED_ROWS:
            raise SIMA1AggregationError("order seed-value count differs")
        order_rows = build_order_sensitivity_rows(block_rows)
        write_rows_csv(temporary / "si_ma1_order_sensitivity.csv", order_rows)

        seed_values = [recomputed[seed] for seed in EXPECTED_MODEL_SEEDS]
        result = bootstrap_median(seed_values)
        cal_cost_passed = result.upper_one_sided_95 <= EXCESS_MARGIN
        decision_state = "pass" if cal_cost_passed else "fail"
        source_commit = attempts[0].source_git_commit
        image_revision = attempts[0].image_revision
        experiment_image = attempts[0].experiment_image
        environment = {
            "schema_id": AGGREGATION_SCHEMA_ID,
            "contract_id": CONTRACT_ID,
            "aggregation_git_commit": head,
            "execution_tag": EXECUTION_TAG,
            "execution_tag_commit": EXECUTION_TAG_COMMIT,
            "execution_source_git_commit": source_commit,
            "execution_image_revision": image_revision,
            "experiment_image": experiment_image,
            "input_root": input_root.as_posix(),
            "input_tree_sha256": input_digest,
            "model_seed_count": 10,
            "ecz_evaluator_executed": False,
            "ecz_evaluator_cost_included": False,
            "test_split_accessed": False,
        }
        _write_json(temporary / "si_ma1_environment.json", environment)
        gates = {
            "prerequisites_verified": True,
            "NUM-MA1-cell": True,
            "TOPO-MA1-cell": True,
            "BAL-MA1-cell": True,
            "CMP-MA1-cell": True,
            "CAL-COST-MA1": cal_cost_passed,
        }
        primary = {
            "statistic": "median(D_seed)",
            "resampling_unit": "model_seed",
            "bootstrap_type": "one-sided percentile bootstrap upper bound",
            "bootstrap_quantile_method": "numpy linear",
            "confidence_level": BOOTSTRAP_LEVEL,
            "threshold": EXCESS_MARGIN,
            **result.to_record(),
        }
        seed_records = [
            {"model_seed": seed, "d_seed": recomputed[seed]}
            for seed in EXPECTED_MODEL_SEEDS
        ]
        summary = {
            "schema_id": AGGREGATION_SCHEMA_ID,
            "contract_id": CONTRACT_ID,
            "implementation_schema_id": IMPLEMENTATION_SCHEMA_ID,
            "execution_schema_id": CONFIRMATORY_SCHEMA_ID,
            "si_ma1_prereg_commit": PREREGISTRATION_COMMIT,
            "execution_tag": EXECUTION_TAG,
            "execution_tag_commit": EXECUTION_TAG_COMMIT,
            "source_git_commit": source_commit,
            "image_revision": image_revision,
            "experiment_image": experiment_image,
            "input_tree_sha256": input_digest,
            "model_seed_count": 10,
            "matched_block_count": EXPECTED_BLOCK_ROWS,
            "seed_values": seed_records,
            "primary_estimand": primary,
            "gates": gates,
            "confirmatory_decision_made": True,
            "decision_state": decision_state,
            "si_ma1_passed": cal_cost_passed,
            "ecz_evaluator_executed": False,
            "ecz_evaluator_cost_included": False,
            "si_ma0_result_rewritten": False,
            "b1_b2_gate_condition_satisfied": cal_cost_passed,
            "b1_b2_opened": False,
            "theoretical_pc_tref_patch_required_before_b1_b2": True,
            "secondary_analyses_authorize_decision": False,
            "combined_csv_row_counts": counts,
            "order_seed_value_source_rows": order_source_rows,
            "order_sensitivity_rows": len(order_rows),
        }
        decision = {
            "schema_id": AGGREGATION_SCHEMA_ID,
            "contract_id": CONTRACT_ID,
            "CAL-COST-MA1": cal_cost_passed,
            "decision_rule": "upper_one_sided_95 <= 0.01",
            "upper_one_sided_95": result.upper_one_sided_95,
            "threshold": EXCESS_MARGIN,
            "confirmatory_decision_made": True,
            "decision_state": decision_state,
            "si_ma1_passed": cal_cost_passed,
            "si_ma0_result_rewritten": False,
            "ecz_evaluator_cost_included": False,
            "b1_b2_gate_condition_satisfied": cal_cost_passed,
            "b1_b2_preregistration_permitted": False,
            "b1_b2_implementation_permitted": False,
            "theoretical_pc_tref_patch_required_before_b1_b2": True,
        }
        _write_json(temporary / "si_ma1_summary.json", summary)
        _write_json(temporary / "si_ma1_decision.json", decision)
        report_ru, report_en = _reports(
            result=result,
            passed=cal_cost_passed,
            seed_values=recomputed,
        )
        (temporary / "si_ma1_report.md").write_text(
            report_ru,
            encoding="utf-8",
            newline="\n",
        )
        (temporary / "si_ma1_report_EN.md").write_text(
            report_en,
            encoding="utf-8",
            newline="\n",
        )
        _write_manifest(temporary)
        observed_files = tuple(sorted(path.name for path in temporary.iterdir()))
        if observed_files != tuple(sorted(FINAL_MANDATORY_FILES)):
            raise SIMA1AggregationError("final output file set differs from contract")
        if destination.exists():
            destination.rmdir()
        temporary.rename(destination)
        return summary
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def summary_digest(summary: Mapping[str, Any]) -> str:
    """Expose deterministic summary hashing for unit tests and reports."""

    return canonical_json_digest(dict(summary))
