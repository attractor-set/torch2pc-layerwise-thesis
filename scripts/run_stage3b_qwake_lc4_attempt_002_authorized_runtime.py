#!/usr/bin/env python3
"""Run one corrected QW-LC4-E attempt-002 engineering invocation."""

from __future__ import annotations

import argparse
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_lc4_attempt_002_contract import (
    ATTEMPT_002_LEASE_ACKNOWLEDGEMENT,
    Attempt002ContractError,
    build_attempt_002_admission,
    verify_attempt_002_execution_freeze,
    verify_unconsumed_attempt_002_authorization,
)
from torch2pc_thesis.stage3b_qwake_lc4_attempt_002_execution_wrapper import (
    Attempt002ExecutionOutcome,
    build_attempt_002_lease,
    materialize_attempt_002_lease,
    run_claimed_attempt_002,
)
from torch2pc_thesis.stage3b_qwake_lc4_attempt_002_runtime_backend import (
    Attempt002RuntimeBackend,
    Attempt002RuntimeBackendError,
)
from torch2pc_thesis.stage3b_qwake_lc4_runtime_backend import (
    RuntimeMatrixExecutor,
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
            f"{ATTEMPT_002_LEASE_ACKNOWLEDGEMENT}"
        ),
    )
    return parser.parse_args()


def run_attempt_002_authorized_runtime(
    project_root: Path,
    torch2pc_dir: Path,
    *,
    claimed_at_utc: str,
    operator_acknowledgement: str,
    matrix_executor: RuntimeMatrixExecutor | None = None,
) -> Attempt002ExecutionOutcome:
    """Carry one attempt-002 admission through build, claim, and execute."""

    root = project_root.expanduser().resolve()
    resolved_torch2pc = torch2pc_dir.expanduser().resolve()
    expected_torch2pc = (root / "external/Torch2PC").resolve()
    if resolved_torch2pc != expected_torch2pc:
        raise Attempt002RuntimeBackendError(
            "attempt-002 Torch2PC path differs from the project checkout"
        )
    if operator_acknowledgement != ATTEMPT_002_LEASE_ACKNOWLEDGEMENT:
        raise Attempt002ContractError(
            "attempt-002 lease acknowledgement differs"
        )

    freeze = verify_attempt_002_execution_freeze(root)
    authorization = verify_unconsumed_attempt_002_authorization(root, freeze)
    admission = build_attempt_002_admission(freeze, authorization)
    backend = Attempt002RuntimeBackend(
        project_root=root,
        torch2pc_dir=resolved_torch2pc,
        execution_freeze=freeze,
        matrix_executor=matrix_executor,
    )
    lease = build_attempt_002_lease(
        admission,
        claimed_at_utc=claimed_at_utc,
        wrapper_commit=freeze.wrapper_commit,
        operator_acknowledgement=operator_acknowledgement,
    )
    materialize_attempt_002_lease(root, lease, admission)
    return run_claimed_attempt_002(
        root,
        admission,
        lease,
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
    outcome = run_attempt_002_authorized_runtime(
        project_root,
        torch2pc_dir,
        claimed_at_utc=args.claimed_at_utc,
        operator_acknowledgement=args.operator_acknowledgement,
    )
    print("OK: QW-LC4-E attempt-002 engineering execution completed")
    print(f"OUTPUT_ROOT={outcome.output_root}")
    print(f"WRAPPER_RECEIPT_SHA256={outcome.wrapper_receipt_sha256}")
    print("ENGINEERING_EVIDENCE_PRESENT=true")
    print("SCIENTIFIC_EXECUTION_OPEN=false")
    print("TEST_DATASET_ACCESS=false")
    print("PUBLICATION_PERMITTED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
