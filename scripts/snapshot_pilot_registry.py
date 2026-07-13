#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path


def snapshot_pilot_registry(
    source: Path = Path("experiments/registry.csv"),
    destination: Path = Path("results/summaries/pilot_registry_snapshot.csv"),
) -> int:
    if not source.is_file():
        raise RuntimeError(f"Registry is missing: {source}")
    with source.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        fieldnames = reader.fieldnames
        if not fieldnames:
            raise RuntimeError("Registry header is missing")
        rows = [row for row in reader if row.get("stage") == "pilot"]
    if not rows:
        raise RuntimeError("Registry contains no pilot events")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def main() -> None:
    rows = snapshot_pilot_registry()
    print(f"results/summaries/pilot_registry_snapshot.csv ({rows} rows)")


if __name__ == "__main__":
    main()
