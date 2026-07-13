from __future__ import annotations

import csv
from pathlib import Path

from scripts.snapshot_pilot_registry import snapshot_pilot_registry


def test_snapshot_contains_only_pilot_events(tmp_path: Path) -> None:
    source = tmp_path / "registry.csv"
    destination = tmp_path / "snapshot.csv"
    fieldnames = ["run_id", "stage", "status"]
    with source.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(
            [
                {"run_id": "p1", "stage": "pilot", "status": "running"},
                {"run_id": "p1", "stage": "pilot", "status": "completed"},
                {"run_id": "f1", "stage": "final", "status": "completed"},
            ]
        )
    count = snapshot_pilot_registry(source, destination)
    assert count == 2
    with destination.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert [row["stage"] for row in rows] == ["pilot", "pilot"]
