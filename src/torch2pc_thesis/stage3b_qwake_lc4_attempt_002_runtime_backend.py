"""Corrected bounded runtime backend for attempt 002.

The module reuses only the immutable scientific matrix executor.  It owns new
attempt-002 output identities and verifies the new corrected freeze before any
matrix execution.
"""

from __future__ import annotations

import hashlib
import os
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Final

from torch2pc_thesis.stage3b_qwake_lc4_attempt_002_contract import (
    ATTEMPT_002_ID,
    ATTEMPT_002_OUTPUT_ROOT,
    SCIENTIFIC_RUNTIME_AUTHORIZATION_RELATIVE,
    Attempt002ExecutionFreeze,
    canonical_json,
    sha256_object,
    verify_attempt_002_execution_freeze,
)
from torch2pc_thesis.stage3b_qwake_lc4_attempt_002_execution_wrapper import (
    Attempt002BackendReceipt,
    Attempt002LeaseV1,
    Attempt002WrapperContract,
    build_attempt_002_backend_receipt,
)
from torch2pc_thesis.stage3b_qwake_lc4_runtime_backend import (
    BoundedTorchMatrixExecutor,
    RuntimeMatrixExecutor,
)
from torch2pc_thesis.stage3b_qwake_lc4_runtime_freeze import (
    load_runtime_authorization,
)

ATTEMPT_002_BACKEND_ID: Final = (
    "stage3b-qwake-lc4-e-attempt-002-bounded-torch-runtime-backend-v1"
)
ATTEMPT_002_REPORT_ID: Final = (
    "stage3b-qwake-lc4-e-attempt-002-runtime-backend-report-v1"
)
_RUNTIME_REPORT_RELATIVE: Final = Path("runtime-backend-report.json")
_MATCHED_CELLS_RELATIVE: Final = Path("matched-cells.jsonl")
_RESERVE_PROBES_RELATIVE: Final = Path("reserve-probes.jsonl")
_AGGREGATES_RELATIVE: Final = Path("paired-cost-aggregates.json")
_IDENTITIES_RELATIVE: Final = Path("runtime-identities.json")
_BACKEND_RECEIPT_RELATIVE: Final = Path("runtime-backend-receipt.json")
_BACKEND_SUMS_RELATIVE: Final = Path("SHA256SUMS")
_EXPECTED_OUTPUT_FILE_COUNT: Final = 7

__all__ = [
    "ATTEMPT_002_BACKEND_ID",
    "ATTEMPT_002_REPORT_ID",
    "Attempt002RuntimeBackend",
    "Attempt002RuntimeBackendError",
]


class Attempt002RuntimeBackendError(RuntimeError):
    """Raised when the attempt-002 backend cannot preserve its freeze."""


class Attempt002RuntimeBackend:
    """Wrapper-compatible backend guarded by the corrected freeze."""

    def __init__(
        self,
        *,
        project_root: Path,
        torch2pc_dir: Path,
        execution_freeze: Attempt002ExecutionFreeze,
        matrix_executor: RuntimeMatrixExecutor | None = None,
    ) -> None:
        self.project_root = project_root.expanduser().resolve()
        self.torch2pc_dir = torch2pc_dir.expanduser().resolve()
        expected_torch2pc = (self.project_root / "external/Torch2PC").resolve()
        if self.torch2pc_dir != expected_torch2pc:
            raise Attempt002RuntimeBackendError(
                "attempt-002 Torch2PC path differs from the project checkout"
            )
        self.execution_freeze = execution_freeze
        self.matrix_executor = (
            BoundedTorchMatrixExecutor()
            if matrix_executor is None
            else matrix_executor
        )

    @property
    def backend_id(self) -> str:
        return ATTEMPT_002_BACKEND_ID

    def run(
        self,
        staging_root: Path,
        lease: Attempt002LeaseV1,
        contract: Attempt002WrapperContract,
    ) -> Attempt002BackendReceipt:
        self.execution_freeze.require()
        verified = verify_attempt_002_execution_freeze(self.project_root)
        if verified != self.execution_freeze:
            raise Attempt002RuntimeBackendError(
                "attempt-002 execution-freeze identity changed"
            )
        if lease.freeze_sha256 != self.execution_freeze.freeze_sha256:
            raise Attempt002RuntimeBackendError(
                "attempt-002 lease freeze differs"
            )
        contract.require(lease)
        root = staging_root.expanduser().resolve()
        if not root.is_dir() or root.is_symlink() or tuple(root.iterdir()):
            raise Attempt002RuntimeBackendError(
                "attempt-002 staging root is invalid"
            )

        authorization = load_runtime_authorization(
            self.project_root / SCIENTIFIC_RUNTIME_AUTHORIZATION_RELATIVE
        )
        if (
            authorization.authorization_sha256
            != self.execution_freeze.scientific_authorization_sha256
        ):
            raise Attempt002RuntimeBackendError(
                "attempt-002 scientific authorization differs"
            )
        if (
            authorization.authorization_sha256
            != lease.scientific_authorization_sha256
        ):
            raise Attempt002RuntimeBackendError(
                "attempt-002 lease scientific authorization differs"
            )
        matrix = self.matrix_executor.execute(authorization)
        matrix.require(authorization)

        cells_bytes = _jsonl_bytes(item.payload() for item in matrix.cells)
        probes_bytes = _jsonl_bytes(
            item.payload() for item in matrix.reserve_probes
        )
        aggregates_bytes = canonical_json(
            {
                "schema_version": 1,
                "aggregate_id": (
                    "stage3b-qwake-lc4-e-attempt-002-paired-cost-aggregates-v1"
                ),
                "items": matrix.aggregates,
            }
        ).encode("utf-8")

        all_response_comparisons_passed = all(
            item.response_passed for item in matrix.cells
        )
        all_rng_matches_passed = all(
            item.rng_post_match for item in matrix.cells
        )
        all_reserve_probes_passed = all(
            item.passed for item in matrix.reserve_probes
        )
        all_order_effect_gates_passed = all(
            item.get("order_effect_passed") is True
            for item in matrix.aggregates
        )
        all_pairs_complete = all(
            item.get("pair_complete") is True
            for item in matrix.aggregates
        )
        validation_passed = all(
            (
                all_response_comparisons_passed,
                all_rng_matches_passed,
                all_reserve_probes_passed,
                all_order_effect_gates_passed,
                all_pairs_complete,
            )
        )
        identities_payload: dict[str, object] = {
            "schema_version": 1,
            "attempt_id": ATTEMPT_002_ID,
            "backend_id": self.backend_id,
            "execution_freeze_sha256": self.execution_freeze.freeze_sha256,
            "source_commit": self.execution_freeze.source_commit,
            "wrapper_commit": self.execution_freeze.wrapper_commit,
            "torch2pc_commit": self.execution_freeze.torch2pc_commit,
            "image_digest": self.execution_freeze.image_digest,
            "image_repo_digest": self.execution_freeze.image_repo_digest,
            "scientific_authorization_sha256": (
                authorization.authorization_sha256
            ),
            "authorization_sha256": lease.authorization_sha256,
            "lease_sha256": lease.lease_sha256,
            "wrapper_contract_sha256": contract.contract_sha256,
            "output_root": ATTEMPT_002_OUTPUT_ROOT.as_posix(),
            "engineering_evidence_only": True,
            "scientific_execution_open": False,
            "test_dataset_access": False,
            "publication_permitted": False,
        }
        report_payload: dict[str, object] = {
            "schema_version": 1,
            "report_id": ATTEMPT_002_REPORT_ID,
            "attempt_id": ATTEMPT_002_ID,
            "status": (
                "engineering_matrix_completed_validation_passed"
                if validation_passed
                else "engineering_matrix_completed_validation_failed"
            ),
            "backend_id": self.backend_id,
            "execution_freeze_sha256": self.execution_freeze.freeze_sha256,
            "authorization_sha256": lease.authorization_sha256,
            "lease_sha256": lease.lease_sha256,
            "wrapper_contract_sha256": contract.contract_sha256,
            "authorized_cell_count": len(matrix.cells),
            "reserve_probe_count": len(matrix.reserve_probes),
            "aggregate_count": len(matrix.aggregates),
            "all_response_comparisons_passed": all_response_comparisons_passed,
            "all_rng_matches_passed": all_rng_matches_passed,
            "all_reserve_probes_passed": all_reserve_probes_passed,
            "all_order_effect_gates_passed": all_order_effect_gates_passed,
            "all_pairs_complete": all_pairs_complete,
            "validation_passed": validation_passed,
            "engineering_evidence_present": True,
            "scientific_execution_open": False,
            "test_dataset_access": False,
            "publication_permitted": False,
        }
        report_payload["report_sha256"] = sha256_object(report_payload)

        initial_files = {
            _RUNTIME_REPORT_RELATIVE: canonical_json(report_payload).encode(
                "utf-8"
            ),
            _MATCHED_CELLS_RELATIVE: cells_bytes,
            _RESERVE_PROBES_RELATIVE: probes_bytes,
            _AGGREGATES_RELATIVE: aggregates_bytes,
            _IDENTITIES_RELATIVE: canonical_json(identities_payload).encode(
                "utf-8"
            ),
        }
        for relative, content in initial_files.items():
            _write_exclusive_regular(root / relative, content)

        receipt = build_attempt_002_backend_receipt(
            backend_id=self.backend_id,
            lease=lease,
            contract=contract,
            output_file_count=_EXPECTED_OUTPUT_FILE_COUNT,
        )
        _write_exclusive_regular(
            root / _BACKEND_RECEIPT_RELATIVE,
            receipt.canonical_json().encode("utf-8"),
        )
        sums = []
        for relative in sorted(
            (*initial_files, _BACKEND_RECEIPT_RELATIVE),
            key=lambda item: item.as_posix(),
        ):
            content = (root / relative).read_bytes()
            sums.append(
                f"{hashlib.sha256(content).hexdigest()}  {relative.as_posix()}\n"
            )
        _write_exclusive_regular(
            root / _BACKEND_SUMS_RELATIVE,
            "".join(sums).encode("utf-8"),
        )
        observed_count = sum(1 for path in root.rglob("*") if path.is_file())
        if observed_count != _EXPECTED_OUTPUT_FILE_COUNT:
            raise Attempt002RuntimeBackendError(
                "attempt-002 backend output file count differs"
            )
        return receipt


def _jsonl_bytes(values: Iterable[Mapping[str, object]]) -> bytes:
    return "".join(canonical_json(value) for value in values).encode("utf-8")


def _write_exclusive_regular(path: Path, content: bytes) -> None:
    if not content:
        raise Attempt002RuntimeBackendError(
            f"attempt-002 output content is empty: {path.name}"
        )
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o600)
    try:
        view = memoryview(content)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise Attempt002RuntimeBackendError(
                    "attempt-002 output write made no progress"
                )
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
