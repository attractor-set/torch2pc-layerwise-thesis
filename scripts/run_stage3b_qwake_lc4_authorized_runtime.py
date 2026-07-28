#!/usr/bin/env python3
"""Run the one-shot QW-LC4-E engineering attempt after immutable freeze."""

from __future__ import annotations

import argparse
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_lc4_execution_wrapper import (
    EXECUTION_LEASE_OPERATOR_ACKNOWLEDGEMENT,
)
from torch2pc_thesis.stage3b_qwake_lc4_runtime_backend import (
    run_one_shot_authorized_runtime,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument(
        "--torch2pc-dir",
        type=Path,
        default=Path("external/Torch2PC"),
    )
    parser.add_argument("--claimed-at-utc", required=True)
    parser.add_argument(
        "--operator-acknowledgement",
        required=True,
        help=(
            "Must exactly equal "
            f"{EXECUTION_LEASE_OPERATOR_ACKNOWLEDGEMENT}"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = args.project_root.expanduser().resolve()
    torch2pc_dir = (
        args.torch2pc_dir
        if args.torch2pc_dir.is_absolute()
        else project_root / args.torch2pc_dir
    ).expanduser().resolve()
    outcome = run_one_shot_authorized_runtime(
        project_root,
        torch2pc_dir,
        claimed_at_utc=args.claimed_at_utc,
        operator_acknowledgement=args.operator_acknowledgement,
    )
    print("OK: QW-LC4-E one-shot engineering execution completed")
    print(f"OUTPUT_ROOT={outcome.output_root}")
    print(f"WRAPPER_RECEIPT_SHA256={outcome.wrapper_receipt_sha256}")
    print("ENGINEERING_EVIDENCE_PRESENT=true")
    print("SCIENTIFIC_EXECUTION_OPEN=false")
    print("TEST_DATASET_ACCESS=false")
    print("PUBLICATION_PERMITTED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
