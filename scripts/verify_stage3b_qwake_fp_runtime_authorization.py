#!/usr/bin/env python3
"""Verify a future frozen QW-4B authorization without executing FixedPred."""

from __future__ import annotations

import argparse
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_fp_runtime import (
    load_authorization,
    load_preflight,
    open_runtime_session,
    verify_static_validation_receipt,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--torch2pc-dir", type=Path, default=Path("external/Torch2PC"))
    parser.add_argument("--preflight", type=Path, required=True)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument(
        "--static-validation-receipt",
        type=Path,
        required=True,
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    preflight = load_preflight(args.preflight)
    authorization = load_authorization(args.authorization)
    verify_static_validation_receipt(
        authorization,
        args.static_validation_receipt,
    )
    session = open_runtime_session(
        preflight,
        authorization,
        args.project_root.resolve(),
        args.torch2pc_dir.resolve(),
    )
    print("OK: QW-4B runtime authorization verified")
    print(f"AUTHORIZATION_SHA256={authorization.authorization_sha256}")
    print(f"OUTPUT_ROOT={session.output_root}")
    print("RUNTIME_VALIDATION_PERMITTED=true")
    print("SCIENTIFIC_EXECUTION_OPEN=false")
    print("TEST_DATASET_ACCESS=false")
    print("IMAGE_FREEZE_PERMITTED=false")


if __name__ == "__main__":
    main()
