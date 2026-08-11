#!/usr/bin/env python3
"""Run one lane-isolated QW-LC4-E attempt-005 engineering invocation."""

from __future__ import annotations

import argparse
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_attempt_005_contract import (
    ATTEMPT_005_LEASE_ACKNOWLEDGEMENT,
    Attempt005ContractError,
    build_attempt_005_admission,
    verify_attempt_005_execution_freeze,
    verify_unconsumed_attempt_005_authorization,
)
from torch2pc_thesis.stage3b_qwake_attempt_005_execution_wrapper import (
    Attempt005ExecutionOutcome,
    build_attempt_005_lease,
    materialize_attempt_005_lease,
    run_claimed_attempt_005,
)
from torch2pc_thesis.stage3b_qwake_attempt_005_runtime_backend import (
    Attempt005RuntimeBackend,
    Attempt005RuntimeBackendError,
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
            f"{ATTEMPT_005_LEASE_ACKNOWLEDGEMENT}"
        ),
    )
    return parser.parse_args()


def run_attempt_005_authorized_runtime(
    project_root: Path,
    torch2pc_dir: Path,
    *,
    claimed_at_utc: str,
    operator_acknowledgement: str,
    matrix_executor: RuntimeMatrixExecutor | None = None,
) -> Attempt005ExecutionOutcome:
    """Carry one attempt-005 admission through build, claim, and execute."""

    root = project_root.expanduser().resolve()
    resolved_torch2pc = torch2pc_dir.expanduser().resolve()
    expected_torch2pc = (root / "external/Torch2PC").resolve()
    if resolved_torch2pc != expected_torch2pc:
        raise Attempt005RuntimeBackendError(
            "attempt-005 Torch2PC path differs from the project checkout"
        )
    if operator_acknowledgement != ATTEMPT_005_LEASE_ACKNOWLEDGEMENT:
        raise Attempt005ContractError(
            "attempt-005 lease acknowledgement differs"
        )

    freeze = verify_attempt_005_execution_freeze(root)
    authorization = verify_unconsumed_attempt_005_authorization(root, freeze)
    admission = build_attempt_005_admission(freeze, authorization)
    backend = Attempt005RuntimeBackend(
        project_root=root,
        torch2pc_dir=resolved_torch2pc,
        execution_freeze=freeze,
        matrix_executor=matrix_executor,
    )
    lease = build_attempt_005_lease(
        admission,
        claimed_at_utc=claimed_at_utc,
        wrapper_commit=freeze.wrapper_commit,
        operator_acknowledgement=operator_acknowledgement,
    )
    materialize_attempt_005_lease(root, lease, admission)
    return run_claimed_attempt_005(
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
    outcome = run_attempt_005_authorized_runtime(
        project_root,
        torch2pc_dir,
        claimed_at_utc=args.claimed_at_utc,
        operator_acknowledgement=args.operator_acknowledgement,
    )
    print("OK: QW-LC4-E attempt-005 engineering execution completed")
    print(f"OUTPUT_ROOT={outcome.output_root}")
    print(f"WRAPPER_RECEIPT_SHA256={outcome.wrapper_receipt_sha256}")
    print("ENGINEERING_EVIDENCE_PRESENT=true")
    print("SCIENTIFIC_EXECUTION_OPEN=false")
    print("TEST_DATASET_ACCESS=false")
    print("PUBLICATION_PERMITTED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
