#!/usr/bin/env python3
"""Verify a frozen QW-LC4-E admission without starting execution."""

from __future__ import annotations

import argparse
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_lc4_execution_admission import (
    load_execution_admission,
    validate_execution_admission,
    verify_frozen_runtime_package,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--admission", type=Path, required=True)
    parser.add_argument(
        "--control-plane-commit",
        required=True,
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    frozen = verify_frozen_runtime_package(args.project_root)
    admission = load_execution_admission(args.admission)
    validate_execution_admission(
        admission,
        frozen,
        args.project_root,
        expected_control_plane_commit=args.control_plane_commit,
    )
    print("ADMISSION_VERIFIED=true")
    print("RUNTIME_EXECUTION_PERMITTED=true")
    print("RUNTIME_EXECUTION_STARTED=false")
    print("RUNTIME_EXECUTION_PERFORMED=false")
    print("ENGINEERING_EVIDENCE_PRESENT=false")
    print("SCIENTIFIC_EXECUTION_OPEN=false")
    print("TEST_DATASET_ACCESS=false")
    print("PUBLICATION_PERMITTED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
