#!/usr/bin/env python3
"""Build the frozen Stage 3B SI-MA0 confirmatory evidence package."""

from __future__ import annotations

import argparse
from pathlib import Path

from torch2pc_thesis.stage3b_si_ma0_aggregation import (
    EXPECTED_EXECUTION_SOURCE_COMMIT,
    AggregationError,
    AggregationInputs,
    aggregate,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
    )
    parser.add_argument(
        "--working-root",
        type=Path,
        default=Path("results/stage-3/si-ma0/working/confirmatory"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("results/stage-3/si-ma0/confirmatory"),
    )
    parser.add_argument(
        "--attempt-name",
        default="primary-03016e68ecc7",
    )
    parser.add_argument(
        "--execution-source-commit",
        default=EXPECTED_EXECUTION_SOURCE_COMMIT,
    )
    parser.add_argument(
        "--ledger",
        type=Path,
        default=Path("/tmp/si-ma0-confirmatory-cell-ledger.tsv"),
    )
    parser.add_argument(
        "--checkpoint-inventory",
        type=Path,
        default=Path(
            "/tmp/si-ma0-confirmatory-checkpoint-inventory.json"
        ),
    )
    parser.add_argument(
        "--full-archive",
        type=Path,
        default=Path(
            "/tmp/si-ma0-confirmatory-all-seeds-"
            f"{EXPECTED_EXECUTION_SOURCE_COMMIT}.tar.gz"
        ),
    )
    return parser.parse_args()


def resolve(path: Path, *, repo: Path) -> Path:
    if path.is_absolute():
        return path.expanduser().resolve()
    return (repo / path).resolve()


def main() -> int:
    args = parse_args()
    repo = args.repo.expanduser().resolve()
    inputs = AggregationInputs(
        repo=repo,
        working_root=resolve(args.working_root, repo=repo),
        output_root=resolve(args.output_root, repo=repo),
        attempt_name=args.attempt_name,
        execution_source_commit=args.execution_source_commit,
        ledger=args.ledger.expanduser().resolve(),
        checkpoint_inventory=args.checkpoint_inventory.expanduser().resolve(),
        full_archive=args.full_archive.expanduser().resolve(),
    )
    try:
        summary = aggregate(inputs)
    except AggregationError as exc:
        print(f"ERROR: {exc}")
        return 2
    print("OK: SI-MA0 confirmatory evidence package generated")
    print(f"output_root={inputs.output_root}")
    print(f"decision_state={summary['decision_state']}")
    print(f"si_ma0_passed={summary['si_ma0_passed']}")
    for gate, passed in summary["gates"].items():
        print(f"{gate}={passed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
