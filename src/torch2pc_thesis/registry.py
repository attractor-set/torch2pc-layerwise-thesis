from __future__ import annotations

import csv
import fcntl
from collections.abc import Iterator
from dataclasses import asdict, dataclass
from pathlib import Path

FIELDS = [
    "run_id",
    "experiment_id",
    "status",
    "stage",
    "dataset",
    "model",
    "method",
    "eta",
    "inference_steps",
    "model_seed",
    "split_seed",
    "config_sha256",
    "git_commit",
    "torch2pc_commit",
    "run_directory",
    "started_utc",
    "finished_utc",
    "test_evaluated",
    "notes",
]


@dataclass
class RegistryEntry:
    run_id: str
    experiment_id: str
    status: str
    stage: str
    dataset: str
    model: str
    method: str
    eta: str
    inference_steps: str
    model_seed: int
    split_seed: int
    config_sha256: str
    git_commit: str
    torch2pc_commit: str
    run_directory: str
    started_utc: str
    finished_utc: str = ""
    test_evaluated: str = "false"
    notes: str = ""


def initialize_registry(path: str | Path) -> Path:
    registry = Path(path)
    registry.parent.mkdir(parents=True, exist_ok=True)
    if not registry.exists():
        with registry.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS)
            writer.writeheader()
    else:
        with registry.open("r", newline="", encoding="utf-8") as stream:
            reader = csv.reader(stream)
            header = next(reader, [])
        if header != FIELDS:
            raise RuntimeError(
                f"Registry schema mismatch in {registry}. Expected {FIELDS}, found {header}"
            )
    return registry


def append_entry(path: str | Path, entry: RegistryEntry) -> None:
    registry = initialize_registry(path)
    with registry.open("a+", newline="", encoding="utf-8") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writerow(asdict(entry))
        stream.flush()
        fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def rows(path: str | Path) -> Iterator[dict[str, str]]:
    registry = initialize_registry(path)
    with registry.open("r", newline="", encoding="utf-8") as stream:
        yield from csv.DictReader(stream)


def latest_by_run_id(path: str | Path) -> dict[str, dict[str, str]]:
    latest: dict[str, dict[str, str]] = {}
    for row in rows(path):
        latest[row["run_id"]] = row
    return latest


def latest_by_experiment_id(path: str | Path) -> dict[str, dict[str, str]]:
    latest: dict[str, dict[str, str]] = {}
    for row in rows(path):
        latest[row["experiment_id"]] = row
    return latest


def completed_runs(path: str | Path) -> list[dict[str, str]]:
    return [row for row in latest_by_run_id(path).values() if row["status"] == "completed"]


def completed_experiments(path: str | Path) -> list[dict[str, str]]:
    """Return one primary completed attempt per experiment configuration.

    The earliest completed attempt is used. Later successful reruns remain in the
    registry but are not counted as additional independent model replications.
    """
    selected: dict[str, dict[str, str]] = {}
    for row in sorted(
        completed_runs(path),
        key=lambda item: (item["started_utc"], item["run_id"]),
    ):
        selected.setdefault(row["experiment_id"], row)
    return list(selected.values())
