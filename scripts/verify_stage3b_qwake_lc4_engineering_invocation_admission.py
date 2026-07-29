#!/usr/bin/env python3
"""Verify QW-LC4-E one-shot engineering invocation admission."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Final

from torch2pc_thesis.stage3b_qwake_lc4_engineering_invocation_admission import (
    INVOCATION_ADMISSION_ID,
    verify_engineering_invocation_admission,
)

_DESCRIPTION: Final = (
    "Verify the exact one-shot engineering invocation admission without "
    "inspecting an image or invoking runtime."
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=_DESCRIPTION)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    admission = verify_engineering_invocation_admission(args.project_root)

    print(f"INVOCATION_ADMISSION_ID={INVOCATION_ADMISSION_ID}")
    print(f"INVOCATION_ADMISSION_SHA256={admission.admission_sha256}")
    print(
        "INVOCATION_BASE_COMMIT="
        f"{admission.source.invocation_base_commit}"
    )
    print("REPOSITORY_FREEZE_COMPLETE=true")
    print("INVOCATION_ADMISSION_RECORD_PRESENT=true")
    print("PREEXECUTION_IDENTITY_CHECKS_IMPLEMENTED=true")
    print("PREEXECUTION_IDENTITY_VERIFIED=false")
    print("ONE_SHOT_ENGINEERING_INVOCATION_SLICE_OPEN=true")
    print("ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false")
    print("ONE_SHOT_ENGINEERING_INVOCATION_PERFORMED=false")
    print("BRANCH_RUNTIME_EXECUTION_PERMITTED=false")
    print("EXECUTION_LEASE_MATERIALIZED=false")
    print("AUTHORIZATION_CONSUMED=false")
    print("RUNTIME_EXECUTION_STARTED=false")
    print("RUNTIME_EXECUTION_PERFORMED=false")
    print("ENGINEERING_EVIDENCE_PRESENT=false")
    print("SCIENTIFIC_EXECUTION_OPEN=false")
    print("TEST_DATASET_ACCESS=false")
    print("PUBLICATION_PERMITTED=false")
    print("IMAGE_INSPECTION_PERFORMED=false")
    print("DOCKER_RUN_PERFORMED=false")
    print("LOCAL_COMPUTE_EXECUTION_OPEN=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
