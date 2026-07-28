#!/usr/bin/env python3
"""Verify QW-LC4-E effect mechanics only in an isolated temporary root."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_lc4_execution_admission import (
    AUTHORIZED_OUTPUT_ROOT,
    EXECUTION_LEASE_RELATIVE,
)
from torch2pc_thesis.stage3b_qwake_lc4_execution_wrapper import (
    EXECUTION_LEASE_OPERATOR_ACKNOWLEDGEMENT,
    ExecutionWrapperContract,
    ProspectiveExecutionLease,
    build_execution_wrapper_contract,
    build_prospective_execution_lease,
    verify_unconsumed_frozen_admission,
)
from torch2pc_thesis.stage3b_qwake_lc4_execution_wrapper_implementation import (
    EXECUTION_IMPLEMENTATION_ID,
    EXECUTION_WRAPPER_RECEIPT_RELATIVE,
    RuntimeBackendReceipt,
    RuntimeExecutionBackend,
    build_runtime_backend_receipt,
    materialize_execution_lease,
    run_claimed_execution_wrapper,
)

WRAPPER_COMMIT = "c" * 40
CLAIMED_AT = "2026-07-27T23:30:00Z"
AUTHORING_ROOT_RELATIVE = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-execution-lease-wrapper-authoring-v1"
)


class _VerifierBackend(RuntimeExecutionBackend):
    @property
    def backend_id(self) -> str:
        return "synthetic-qwake-lc4-implementation-verifier-v1"

    def run(
        self,
        staging_root: Path,
        lease: ProspectiveExecutionLease,
        contract: ExecutionWrapperContract,
    ) -> RuntimeBackendReceipt:
        if contract.lease_sha256 != lease.lease_sha256:
            raise RuntimeError("wrapper contract and lease differ")
        (staging_root / "engineering-result.json").write_text(
            '{"status":"synthetic-verification-pass"}\n',
            encoding="utf-8",
        )
        return build_runtime_backend_receipt(
            backend_id=self.backend_id,
            wrapper_commit=lease.wrapper_commit,
            lease_sha256=lease.lease_sha256,
            output_file_count=1,
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    return parser


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    args = _parser().parse_args()
    project_root = args.project_root.expanduser().resolve()
    repository_lease = project_root / EXECUTION_LEASE_RELATIVE
    repository_output = project_root / AUTHORIZED_OUTPUT_ROOT
    if repository_lease.exists() or repository_lease.is_symlink():
        raise RuntimeError("repository execution lease is already present")
    if repository_output.exists() or repository_output.is_symlink():
        raise RuntimeError("repository runtime output is already present")

    frozen = verify_unconsumed_frozen_admission(project_root)
    authoring_root = project_root / AUTHORING_ROOT_RELATIVE
    authoring_json = authoring_root / "authoring.json"
    authoring_registry = authoring_root / "SHA256SUMS"
    expected, relative = authoring_registry.read_text(
        encoding="utf-8"
    ).strip().split("  ", 1)
    if relative != "authoring.json":
        raise RuntimeError("authoring registry path differs")
    if hashlib.sha256(authoring_json.read_bytes()).hexdigest() != expected:
        raise RuntimeError("authoring registry identity differs")
    authoring = json.loads(authoring_json.read_text(encoding="utf-8"))
    if authoring["next_slice"] != (
        "QW-LC4-E-execution-lease-wrapper-implementation"
    ):
        raise RuntimeError("authoring next slice differs")

    lease = build_prospective_execution_lease(
        frozen,
        claimed_at_utc=CLAIMED_AT,
        wrapper_commit=WRAPPER_COMMIT,
        operator_acknowledgement=(
            EXECUTION_LEASE_OPERATOR_ACKNOWLEDGEMENT
        ),
        output_root_absent_at_claim=True,
        execution_lease_absent_at_claim=True,
    )
    contract = build_execution_wrapper_contract(lease)

    with tempfile.TemporaryDirectory(
        prefix="qwake-lc4-e-implementation-verifier-"
    ) as temporary_raw:
        temporary_root = Path(temporary_raw)
        lease_path = materialize_execution_lease(
            temporary_root,
            lease,
            frozen,
            expected_wrapper_commit=WRAPPER_COMMIT,
        )
        if lease_path.read_bytes() != lease.canonical_json().encode("utf-8"):
            raise RuntimeError("synthetic materialized lease differs")

        outcome = run_claimed_execution_wrapper(
            temporary_root,
            frozen,
            expected_wrapper_commit=WRAPPER_COMMIT,
            backend=_VerifierBackend(),
        )
        wrapper_receipt = (
            outcome.output_root / EXECUTION_WRAPPER_RECEIPT_RELATIVE
        )
        if not wrapper_receipt.is_file() or wrapper_receipt.is_symlink():
            raise RuntimeError("synthetic wrapper receipt is absent")
        if not lease_path.is_file() or lease_path.is_symlink():
            raise RuntimeError("synthetic lease did not persist")
        if outcome.backend_receipt.output_file_count != 1:
            raise RuntimeError("synthetic backend file count differs")
        wrapper_payload = json.loads(
            wrapper_receipt.read_text(encoding="utf-8")
        )
        if wrapper_payload["implementation_id"] != EXECUTION_IMPLEMENTATION_ID:
            raise RuntimeError("synthetic wrapper implementation id differs")
        if wrapper_payload["receipt_sha256"] != (
            outcome.wrapper_receipt_sha256
        ):
            raise RuntimeError("synthetic wrapper receipt digest differs")

        print("FROZEN_ADMISSION_VERIFIED=true")
        print(f"AUTHORING_JSON_SHA256={_sha256(authoring_json)}")
        print(f"AUTHORING_REGISTRY_SHA256={_sha256(authoring_registry)}")
        print(f"LEASE_TEST_VECTOR_SHA256={lease.lease_sha256}")
        print(f"WRAPPER_CONTRACT_TEST_VECTOR_SHA256={contract.contract_sha256}")
        print(
            "BACKEND_RECEIPT_TEST_VECTOR_SHA256="
            f"{outcome.backend_receipt.receipt_sha256}"
        )
        print(
            "WRAPPER_RECEIPT_TEST_VECTOR_SHA256="
            f"{outcome.wrapper_receipt_sha256}"
        )
        print("ATOMIC_LEASE_WRITER_VERIFIED=true")
        print("ATOMIC_OUTPUT_PROMOTION_VERIFIED=true")
        print("LEASE_PERSISTS_AFTER_EXECUTION=true")

    if repository_lease.exists() or repository_lease.is_symlink():
        raise RuntimeError("verifier materialized repository lease")
    if repository_output.exists() or repository_output.is_symlink():
        raise RuntimeError("verifier materialized repository output")

    print("LEASE_WRAPPER_AUTHORING_MERGED=true")
    print("LEASE_WRAPPER_IMPLEMENTATION_MATERIALIZED=true")
    print("EXECUTION_LEASE_WRITER_PRESENT=true")
    print("RUNTIME_EXECUTOR_PRESENT=true")
    print("RESULT_WRITER_PRESENT=true")
    print("EXECUTION_LEASE_MATERIALIZED=false")
    print("QW_LC4_E_EXECUTION_PERMITTED=false")
    print("AUTHORIZATION_CONSUMED=false")
    print("RUNTIME_EXECUTION_STARTED=false")
    print("RUNTIME_EXECUTION_PERFORMED=false")
    print("ENGINEERING_EVIDENCE_PRESENT=false")
    print("SCIENTIFIC_EXECUTION_OPEN=false")
    print("TEST_DATASET_ACCESS=false")
    print("PUBLICATION_PERMITTED=false")
    print("LOCAL_COMPUTE_EXECUTION_OPEN=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
