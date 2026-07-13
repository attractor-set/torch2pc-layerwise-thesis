#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

from torch2pc_thesis.registry import latest_by_run_id


STAGE = "final_stage_2"
EXPECTED_DATASETS = {"MNIST", "FashionMNIST"}
EXPECTED_METHODS = {"bp", "exact", "fixedpred", "strict"}
EXPECTED_SEEDS = set(range(10))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_completed_cells(rows: list[dict[str, str]]) -> dict[str, Any]:
    completed = [
        row
        for row in rows
        if row.get("stage") == STAGE and row.get("status") == "completed"
    ]
    cells: dict[tuple[str, str, str, int], dict[str, str]] = {}
    duplicates: list[tuple[str, str, str, int]] = []
    for row in completed:
        key = (
            row["dataset"],
            row["model"],
            row["method"],
            int(row["model_seed"]),
        )
        if key in cells:
            duplicates.append(key)
        cells[key] = row

    expected = {
        (dataset, "lenet_classic", method, seed)
        for dataset in EXPECTED_DATASETS
        for method in EXPECTED_METHODS
        for seed in EXPECTED_SEEDS
    }
    observed = set(cells)
    missing = sorted(expected - observed)
    unexpected = sorted(observed - expected)
    if duplicates or missing or unexpected or len(cells) != 80:
        raise RuntimeError(
            "Stage 2 is incomplete or non-unique: "
            f"unique={len(cells)}, duplicates={duplicates}, "
            f"missing={missing}, unexpected={unexpected}"
        )
    if any(row.get("test_evaluated", "").lower() != "true" for row in cells.values()):
        raise RuntimeError("Every completed Stage 2 cell must evaluate the test split")

    candidate_commits = {row["torch2pc_commit"] for row in cells.values()}
    source_commits = {row["git_commit"] for row in cells.values()}
    if len(candidate_commits) != 1 or len(source_commits) != 1:
        raise RuntimeError(
            "Stage 2 successful cells span multiple source or Torch2PC revisions"
        )

    return {
        "stage": STAGE,
        "completed_unique_cells": len(cells),
        "all_test_evaluated": True,
        "by_dataset": dict(sorted(Counter(key[0] for key in cells).items())),
        "by_method": dict(sorted(Counter(key[2] for key in cells).items())),
        "by_seed": {
            str(seed): count
            for seed, count in sorted(Counter(key[3] for key in cells).items())
        },
        "source_git_commit": next(iter(source_commits)),
        "torch2pc_commit": next(iter(candidate_commits)),
    }


def main() -> None:
    source = Path("experiments/registry-stage-2.csv")
    if not source.is_file():
        raise RuntimeError(f"Stage 2 registry is missing: {source}")
    latest = list(latest_by_run_id(source).values())
    summary = validate_completed_cells(latest)

    destination = Path("experiments/registry-stage-2-80-completed.csv")
    shutil.copyfile(source, destination)
    checksum_path = Path(f"{destination}.sha256")
    checksum_path.write_text(
        f"{sha256(destination)}  {destination}\n", encoding="utf-8"
    )

    summary["registry_snapshot"] = str(destination)
    summary["registry_snapshot_sha256"] = sha256(destination)
    summary["terminal_attempts_by_status"] = dict(
        sorted(
            Counter(
                row.get("status", "")
                for row in latest
                if row.get("stage") == STAGE
            ).items()
        )
    )
    output = Path("results/stage-2/summaries/stage-2-completion.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(destination)
    print(checksum_path)
    print(output)


if __name__ == "__main__":
    main()
