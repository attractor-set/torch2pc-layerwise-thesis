#!/usr/bin/env python3
"""Run one corrected QW-LC4-E engineering attempt after immutable freeze."""

from __future__ import annotations

import argparse
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_lc4_execution_admission import (
    AUTHORIZED_OUTPUT_ROOT,
    EXECUTION_LEASE_RELATIVE,
)
from torch2pc_thesis.stage3b_qwake_lc4_execution_wrapper import (
    EXECUTION_LEASE_OPERATOR_ACKNOWLEDGEMENT,
    build_prospective_execution_lease,
    verify_unconsumed_frozen_admission,
)
from torch2pc_thesis.stage3b_qwake_lc4_execution_wrapper_implementation import (
    ExecutionWrapperOutcome,
    materialize_execution_lease,
    run_claimed_execution_wrapper,
)
from torch2pc_thesis.stage3b_qwake_lc4_runtime_backend import (
    QWakeLC4RuntimeBackend,
    QWakeLC4RuntimeBackendError,
    verify_materialized_execution_freeze,
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


def run_corrected_one_shot_authorized_runtime(
    project_root: Path,
    torch2pc_dir: Path,
    *,
    claimed_at_utc: str,
    operator_acknowledgement: str,
) -> ExecutionWrapperOutcome:
    """Capture one admission, claim it, and execute with that same identity."""

    root = project_root.expanduser().resolve()
    resolved_torch2pc = torch2pc_dir.expanduser().resolve()
    expected_torch2pc = (root / "external/Torch2PC").resolve()
    if resolved_torch2pc != expected_torch2pc:
        raise QWakeLC4RuntimeBackendError(
            "one-shot Torch2PC path differs from the project checkout"
        )

    freeze = verify_materialized_execution_freeze(root)
    if operator_acknowledgement != EXECUTION_LEASE_OPERATOR_ACKNOWLEDGEMENT:
        raise QWakeLC4RuntimeBackendError(
            "one-shot operator acknowledgement differs"
        )

    frozen_admission = verify_unconsumed_frozen_admission(root)
    backend = QWakeLC4RuntimeBackend(
        project_root=root,
        torch2pc_dir=resolved_torch2pc,
        execution_freeze=freeze,
    )

    output_root = root / AUTHORIZED_OUTPUT_ROOT
    lease_path = root / EXECUTION_LEASE_RELATIVE
    lease = build_prospective_execution_lease(
        frozen_admission,
        claimed_at_utc=claimed_at_utc,
        wrapper_commit=freeze.wrapper_commit,
        operator_acknowledgement=operator_acknowledgement,
        output_root_absent_at_claim=(
            not output_root.exists() and not output_root.is_symlink()
        ),
        execution_lease_absent_at_claim=(
            not lease_path.exists() and not lease_path.is_symlink()
        ),
    )
    materialize_execution_lease(
        root,
        lease,
        frozen_admission,
        expected_wrapper_commit=freeze.wrapper_commit,
    )
    return run_claimed_execution_wrapper(
        root,
        frozen_admission,
        expected_wrapper_commit=freeze.wrapper_commit,
        backend=backend,
    )


def main() -> int:
    args = parse_args()
    project_root = args.project_root.expanduser().resolve()
    torch2pc_dir = (
        args.torch2pc_dir
        if args.torch2pc_dir.is_absolute()
        else project_root / args.torch2pc_dir
    ).expanduser().resolve()
    outcome = run_corrected_one_shot_authorized_runtime(
        project_root,
        torch2pc_dir,
        claimed_at_utc=args.claimed_at_utc,
        operator_acknowledgement=args.operator_acknowledgement,
    )
    print("OK: corrected QW-LC4-E one-shot engineering execution completed")
    print(f"OUTPUT_ROOT={outcome.output_root}")
    print(f"WRAPPER_RECEIPT_SHA256={outcome.wrapper_receipt_sha256}")
    print("ENGINEERING_EVIDENCE_PRESENT=true")
    print("SCIENTIFIC_EXECUTION_OPEN=false")
    print("TEST_DATASET_ACCESS=false")
    print("PUBLICATION_PERMITTED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
