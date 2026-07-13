#!/usr/bin/env python3
"""Restore model_seed in aggregated Stage 3 representation tables.

The original raw artifacts remain unchanged. The seed is recovered from the
canonical source_file path component: seed-<integer>.
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Final

SEED_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?:^|/)seed-(?P<seed>\d+)(?:/|$)"
)

TARGET_FILES: Final[tuple[str, ...]] = (
    "all_representation_metrics.csv",
    "all_cross_layer_cka.csv",
)


def parse_seed(source_file: str) -> int:
    match = SEED_PATTERN.search(source_file)

    if match is None:
        raise ValueError(
            "Cannot recover model_seed from source_file: "
            f"{source_file!r}"
        )

    return int(match.group("seed"))


def repair_file(path: Path) -> tuple[int, list[int]]:
    if not path.is_file():
        raise FileNotFoundError(path)

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)

        if reader.fieldnames is None:
            raise ValueError(f"CSV has no header: {path}")

        if "source_file" not in reader.fieldnames:
            raise ValueError(f"CSV has no source_file column: {path}")

        rows = list(reader)
        original_fields = list(reader.fieldnames)

    seeds: set[int] = set()

    for row in rows:
        recovered_seed = parse_seed(row["source_file"])
        seeds.add(recovered_seed)

        existing = row.get("model_seed")

        if isinstance(existing, str) and existing:
            existing_seed = int(existing)

            if existing_seed != recovered_seed:
                raise ValueError(
                    f"Conflicting model_seed in {path}: "
                    f"stored={existing_seed}, recovered={recovered_seed}, "
                    f"source_file={row['source_file']!r}"
                )

        row["model_seed"] = str(recovered_seed)

    fields = [name for name in original_fields if name != "model_seed"]
    source_index = fields.index("source_file")
    fields.insert(source_index + 1, "model_seed")

    temporary = path.with_suffix(path.suffix + ".tmp")

    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    temporary.replace(path)

    return len(rows), sorted(seeds)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        required=True,
        help="Directory containing aggregated Stage 3 CSV files.",
    )
    parser.add_argument(
        "--expected-seeds",
        type=int,
        default=10,
        help="Expected number of distinct model seeds.",
    )
    args = parser.parse_args()

    expected = list(range(args.expected_seeds))

    for filename in TARGET_FILES:
        path = args.root / filename
        row_count, seeds = repair_file(path)

        if seeds != expected:
            raise RuntimeError(
                f"{filename}: expected seeds {expected}, found {seeds}"
            )

        print(
            f"{filename}: rows={row_count}, "
            f"model_seeds={seeds}, status=OK"
        )


if __name__ == "__main__":
    main()
