"""Atomic QW-LC4-E lease writer and execution-wrapper implementation.

The module implements the effect mechanics required by ADR-066 while keeping
repository execution closed. Importing it has no side effects. A lease is
created only by an explicit function call, and the concrete runtime backend is
injected by the caller. The implementation never imports model code, opens the
scientific campaign, accesses the test dataset, or publishes evidence.
"""

from __future__ import annotations

import ctypes
import errno
import os
import secrets
import shutil
import stat
import sys
import tempfile
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Final, Protocol, cast

from torch2pc_thesis.stage3b_qwake_lc4_execution_admission import (
    AUTHORIZED_OUTPUT_ROOT,
    EXECUTION_LEASE_RELATIVE,
)
from torch2pc_thesis.stage3b_qwake_lc4_execution_wrapper import (
    AUTHORIZED_CELL_COUNT,
    RESERVE_PROBE_COUNT,
    ExecutionWrapperContract,
    FrozenAdmissionIdentity,
    ProspectiveExecutionLease,
    build_execution_wrapper_contract,
    build_prospective_execution_lease,
    canonical_json,
    load_prospective_execution_lease,
    sha256_object,
    validate_execution_wrapper_contract,
    validate_prospective_execution_lease,
    verify_unconsumed_frozen_admission,
)

EXECUTION_IMPLEMENTATION_ID: Final = (
    "stage3b-qwake-lc4-e-execution-lease-wrapper-implementation-v1"
)
EXECUTION_IMPLEMENTATION_STATUS: Final = (
    "atomic_effect_primitives_materialized_execution_not_open"
)
RUNTIME_BACKEND_RECEIPT_ID: Final = (
    "stage3b-qwake-lc4-e-runtime-backend-receipt-v1"
)
RUNTIME_BACKEND_RECEIPT_STATUS: Final = (
    "engineering_runtime_completed_science_closed"
)
EXECUTION_WRAPPER_RECEIPT_ID: Final = (
    "stage3b-qwake-lc4-e-execution-wrapper-receipt-v1"
)
EXECUTION_WRAPPER_RECEIPT_RELATIVE: Final = Path(
    "execution-wrapper-receipt.json"
)
AUTHORING_MERGE_COMMIT: Final = (
    "e0455dc77b49f5b220231509fe6062d275b6ee9b"
)
AUTHORING_HEAD_COMMIT: Final = (
    "0b59a2445d2e3367d717bbdb68d9b9ba45233bb6"
)
AUTHORING_COMMIT: Final = (
    "1c9f2ef2ac7e76e7ed0a5da9d54ac773e6e9df6f"
)

_AT_FDCWD: Final = -100
_RENAME_NOREPLACE: Final = 1

__all__ = [
    "AUTHORING_COMMIT",
    "AUTHORING_HEAD_COMMIT",
    "AUTHORING_MERGE_COMMIT",
    "EXECUTION_IMPLEMENTATION_ID",
    "EXECUTION_IMPLEMENTATION_STATUS",
    "EXECUTION_WRAPPER_RECEIPT_ID",
    "EXECUTION_WRAPPER_RECEIPT_RELATIVE",
    "RUNTIME_BACKEND_RECEIPT_ID",
    "RUNTIME_BACKEND_RECEIPT_STATUS",
    "ExecutionWrapperOutcome",
    "QWakeLC4ExecutionImplementationError",
    "RuntimeBackendReceipt",
    "RuntimeExecutionBackend",
    "build_runtime_backend_receipt",
    "claim_execution_lease",
    "execute_authorized_runtime",
    "load_materialized_execution_lease",
    "materialize_execution_lease",
    "run_claimed_execution_wrapper",
]


class QWakeLC4ExecutionImplementationError(RuntimeError):
    """Raised when an implementation effect cannot preserve the contract."""


@dataclass(frozen=True)
class RuntimeBackendReceipt:
    """Canonical completion receipt returned by an injected runtime backend."""

    schema_version: int
    receipt_id: str
    status: str
    backend_id: str
    wrapper_commit: str
    lease_sha256: str
    authorized_cell_count: int
    reserve_probe_count: int
    output_file_count: int
    runtime_execution_started: bool
    runtime_execution_performed: bool
    engineering_evidence_present: bool
    scientific_execution_open: bool
    test_dataset_access: bool
    publication_permitted: bool
    receipt_sha256: str

    def require(self) -> None:
        if self.schema_version != 1:
            raise QWakeLC4ExecutionImplementationError(
                "unexpected runtime-backend receipt schema"
            )
        if self.receipt_id != RUNTIME_BACKEND_RECEIPT_ID:
            raise QWakeLC4ExecutionImplementationError(
                "unexpected runtime-backend receipt id"
            )
        if self.status != RUNTIME_BACKEND_RECEIPT_STATUS:
            raise QWakeLC4ExecutionImplementationError(
                "unexpected runtime-backend receipt status"
            )
        if not self.backend_id:
            raise QWakeLC4ExecutionImplementationError(
                "runtime backend id is empty"
            )
        _require_commit(self.wrapper_commit, "wrapper_commit")
        _require_sha256(self.lease_sha256, "lease_sha256")
        if self.authorized_cell_count != AUTHORIZED_CELL_COUNT:
            raise QWakeLC4ExecutionImplementationError(
                "runtime-backend authorized cell count differs"
            )
        if self.reserve_probe_count != RESERVE_PROBE_COUNT:
            raise QWakeLC4ExecutionImplementationError(
                "runtime-backend reserve-probe count differs"
            )
        if self.output_file_count < 1:
            raise QWakeLC4ExecutionImplementationError(
                "runtime backend produced no regular output file"
            )
        if not self.runtime_execution_started:
            raise QWakeLC4ExecutionImplementationError(
                "runtime backend did not record execution start"
            )
        if not self.runtime_execution_performed:
            raise QWakeLC4ExecutionImplementationError(
                "runtime backend did not complete execution"
            )
        if not self.engineering_evidence_present:
            raise QWakeLC4ExecutionImplementationError(
                "runtime backend produced no engineering evidence"
            )
        if any(
            (
                self.scientific_execution_open,
                self.test_dataset_access,
                self.publication_permitted,
            )
        ):
            raise QWakeLC4ExecutionImplementationError(
                "runtime-backend receipt opened a scientific capability"
            )
        _require_sha256(self.receipt_sha256, "receipt_sha256")
        if self.receipt_sha256 != sha256_object(
            self._payload_without_digest()
        ):
            raise QWakeLC4ExecutionImplementationError(
                "runtime-backend receipt digest differs"
            )

    def _payload_without_digest(self) -> Mapping[str, object]:
        payload = asdict(self)
        payload.pop("receipt_sha256")
        return cast(Mapping[str, object], payload)

    def canonical_json(self) -> str:
        return canonical_json(self)


class RuntimeExecutionBackend(Protocol):
    """Injected backend surface used by the concrete execution wrapper."""

    @property
    def backend_id(self) -> str:
        """Return a stable backend identifier."""

        ...

    def run(
        self,
        staging_root: Path,
        lease: ProspectiveExecutionLease,
        contract: ExecutionWrapperContract,
    ) -> RuntimeBackendReceipt:
        """Write engineering outputs only below ``staging_root``."""

        ...


@dataclass(frozen=True)
class ExecutionWrapperOutcome:
    """Successful atomic promotion returned after one claimed execution."""

    implementation_id: str
    lease_path: Path
    output_root: Path
    wrapper_receipt_sha256: str
    backend_receipt: RuntimeBackendReceipt

    def require(self) -> None:
        if self.implementation_id != EXECUTION_IMPLEMENTATION_ID:
            raise QWakeLC4ExecutionImplementationError(
                "execution-wrapper outcome implementation id differs"
            )
        if not self.lease_path.is_file() or self.lease_path.is_symlink():
            raise QWakeLC4ExecutionImplementationError(
                "execution-wrapper outcome lease is absent"
            )
        if not self.output_root.is_dir() or self.output_root.is_symlink():
            raise QWakeLC4ExecutionImplementationError(
                "execution-wrapper outcome root is absent"
            )
        _require_sha256(
            self.wrapper_receipt_sha256,
            "wrapper_receipt_sha256",
        )
        self.backend_receipt.require()


def build_runtime_backend_receipt(
    *,
    backend_id: str,
    wrapper_commit: str,
    lease_sha256: str,
    output_file_count: int,
) -> RuntimeBackendReceipt:
    """Build a canonical completed engineering-backend receipt."""

    payload: dict[str, object] = {
        "schema_version": 1,
        "receipt_id": RUNTIME_BACKEND_RECEIPT_ID,
        "status": RUNTIME_BACKEND_RECEIPT_STATUS,
        "backend_id": backend_id,
        "wrapper_commit": wrapper_commit,
        "lease_sha256": lease_sha256,
        "authorized_cell_count": AUTHORIZED_CELL_COUNT,
        "reserve_probe_count": RESERVE_PROBE_COUNT,
        "output_file_count": output_file_count,
        "runtime_execution_started": True,
        "runtime_execution_performed": True,
        "engineering_evidence_present": True,
        "scientific_execution_open": False,
        "test_dataset_access": False,
        "publication_permitted": False,
    }
    receipt = RuntimeBackendReceipt(
        schema_version=1,
        receipt_id=RUNTIME_BACKEND_RECEIPT_ID,
        status=RUNTIME_BACKEND_RECEIPT_STATUS,
        backend_id=backend_id,
        wrapper_commit=wrapper_commit,
        lease_sha256=lease_sha256,
        authorized_cell_count=AUTHORIZED_CELL_COUNT,
        reserve_probe_count=RESERVE_PROBE_COUNT,
        output_file_count=output_file_count,
        runtime_execution_started=True,
        runtime_execution_performed=True,
        engineering_evidence_present=True,
        scientific_execution_open=False,
        test_dataset_access=False,
        publication_permitted=False,
        receipt_sha256=sha256_object(payload),
    )
    receipt.require()
    return receipt


def materialize_execution_lease(
    project_root: Path,
    lease: ProspectiveExecutionLease,
    frozen_admission: FrozenAdmissionIdentity,
    *,
    expected_wrapper_commit: str,
) -> Path:
    """Create the one-attempt lease with an exclusive atomic hard-link claim."""

    root = project_root.expanduser().resolve()
    validate_prospective_execution_lease(
        lease,
        frozen_admission,
        root,
        expected_wrapper_commit=expected_wrapper_commit,
    )
    output_root = root / AUTHORIZED_OUTPUT_ROOT
    lease_path = root / EXECUTION_LEASE_RELATIVE
    if _lexists(output_root):
        raise QWakeLC4ExecutionImplementationError(
            "authorized output root already exists"
        )
    if _lexists(lease_path):
        raise QWakeLC4ExecutionImplementationError(
            "execution lease already exists"
        )

    _atomic_exclusive_file_claim(
        root,
        lease_path,
        lease.canonical_json().encode("utf-8"),
    )

    # The output may appear between the initial absence check and the
    # successful hard-link claim. The claim remains consumed, but execution is
    # blocked before any backend invocation.
    if _lexists(output_root):
        raise QWakeLC4ExecutionImplementationError(
            "authorized output root appeared during lease claim"
        )

    observed = load_materialized_execution_lease(
        root,
        frozen_admission,
        expected_wrapper_commit=expected_wrapper_commit,
        require_output_absent=True,
    )
    if observed != lease:
        raise QWakeLC4ExecutionImplementationError(
            "materialized execution lease differs"
        )
    return lease_path


def claim_execution_lease(
    project_root: Path,
    *,
    claimed_at_utc: str,
    wrapper_commit: str,
    operator_acknowledgement: str,
) -> ProspectiveExecutionLease:
    """Verify the frozen admission and consume its one attempt atomically."""

    root = project_root.expanduser().resolve()
    frozen_admission = verify_unconsumed_frozen_admission(root)
    output_root = root / AUTHORIZED_OUTPUT_ROOT
    lease_path = root / EXECUTION_LEASE_RELATIVE
    lease = build_prospective_execution_lease(
        frozen_admission,
        claimed_at_utc=claimed_at_utc,
        wrapper_commit=wrapper_commit,
        operator_acknowledgement=operator_acknowledgement,
        output_root_absent_at_claim=not _lexists(output_root),
        execution_lease_absent_at_claim=not _lexists(lease_path),
    )
    materialize_execution_lease(
        root,
        lease,
        frozen_admission,
        expected_wrapper_commit=wrapper_commit,
    )
    return lease


def load_materialized_execution_lease(
    project_root: Path,
    frozen_admission: FrozenAdmissionIdentity,
    *,
    expected_wrapper_commit: str,
    require_output_absent: bool,
) -> ProspectiveExecutionLease:
    """Load and verify an exact already-claimed lease without permitting retry."""

    root = project_root.expanduser().resolve()
    lease_path = root / EXECUTION_LEASE_RELATIVE
    if not lease_path.is_file() or lease_path.is_symlink():
        raise QWakeLC4ExecutionImplementationError(
            "materialized execution lease is absent or non-regular"
        )
    lease = load_prospective_execution_lease(lease_path)
    lease.require()
    frozen_admission.require()
    if lease.wrapper_commit != expected_wrapper_commit:
        raise QWakeLC4ExecutionImplementationError(
            "materialized execution lease wrapper commit differs"
        )
    if lease.admission_sha256 != frozen_admission.admission_sha256:
        raise QWakeLC4ExecutionImplementationError(
            "materialized execution lease admission differs"
        )
    if lease_path.read_bytes() != lease.canonical_json().encode("utf-8"):
        raise QWakeLC4ExecutionImplementationError(
            "materialized execution lease serialization differs"
        )
    output_root = root / AUTHORIZED_OUTPUT_ROOT
    if require_output_absent and _lexists(output_root):
        raise QWakeLC4ExecutionImplementationError(
            "authorized output root already exists"
        )
    return lease


def run_claimed_execution_wrapper(
    project_root: Path,
    frozen_admission: FrozenAdmissionIdentity,
    *,
    expected_wrapper_commit: str,
    backend: RuntimeExecutionBackend,
) -> ExecutionWrapperOutcome:
    """Run one injected backend and atomically promote its complete output."""

    root = project_root.expanduser().resolve()
    lease = load_materialized_execution_lease(
        root,
        frozen_admission,
        expected_wrapper_commit=expected_wrapper_commit,
        require_output_absent=True,
    )
    contract = build_execution_wrapper_contract(lease)
    validate_execution_wrapper_contract(contract, lease)
    if backend.backend_id == "":
        raise QWakeLC4ExecutionImplementationError(
            "runtime backend id is empty"
        )

    output_root = root / AUTHORIZED_OUTPUT_ROOT
    lease_path = root / EXECUTION_LEASE_RELATIVE
    output_parent = output_root.parent
    _ensure_directory_chain(root, output_parent)
    staging_root = Path(
        tempfile.mkdtemp(
            prefix=f".{output_root.name}.staging-",
            dir=output_parent,
        )
    )

    promoted = False
    try:
        receipt = backend.run(staging_root, lease, contract)
        receipt.require()
        if receipt.backend_id != backend.backend_id:
            raise QWakeLC4ExecutionImplementationError(
                "runtime backend receipt id differs from backend"
            )
        if receipt.wrapper_commit != expected_wrapper_commit:
            raise QWakeLC4ExecutionImplementationError(
                "runtime backend receipt wrapper commit differs"
            )
        if receipt.lease_sha256 != lease.lease_sha256:
            raise QWakeLC4ExecutionImplementationError(
                "runtime backend receipt lease differs"
            )

        output_file_count = _validate_staging_tree(staging_root)
        if receipt.output_file_count != output_file_count:
            raise QWakeLC4ExecutionImplementationError(
                "runtime backend output file count differs"
            )

        wrapper_payload: dict[str, object] = {
            "schema_version": 1,
            "receipt_id": EXECUTION_WRAPPER_RECEIPT_ID,
            "implementation_id": EXECUTION_IMPLEMENTATION_ID,
            "authoring_merge_commit": AUTHORING_MERGE_COMMIT,
            "wrapper_commit": expected_wrapper_commit,
            "lease_id": lease.lease_id,
            "lease_sha256": lease.lease_sha256,
            "contract_id": contract.contract_id,
            "contract_sha256": contract.contract_sha256,
            "backend_receipt": asdict(receipt),
            "output_root": AUTHORIZED_OUTPUT_ROOT,
            "atomic_output_promotion": True,
            "authorization_consumed": True,
            "runtime_execution_started": True,
            "runtime_execution_performed": True,
            "engineering_evidence_present": True,
            "scientific_execution_open": False,
            "test_dataset_access": False,
            "publication_permitted": False,
        }
        wrapper_receipt_sha256 = sha256_object(wrapper_payload)
        wrapper_payload["receipt_sha256"] = wrapper_receipt_sha256
        _atomic_exclusive_file_claim(
            staging_root,
            staging_root / EXECUTION_WRAPPER_RECEIPT_RELATIVE,
            canonical_json(wrapper_payload).encode("utf-8"),
        )
        _validate_staging_tree(staging_root)
        _fsync_tree(staging_root)

        # Re-read the persistent claim and close the output race immediately
        # before the no-replace promotion.
        observed_lease = load_materialized_execution_lease(
            root,
            frozen_admission,
            expected_wrapper_commit=expected_wrapper_commit,
            require_output_absent=True,
        )
        if observed_lease != lease:
            raise QWakeLC4ExecutionImplementationError(
                "execution lease changed before output promotion"
            )
        if not lease_path.is_file() or lease_path.is_symlink():
            raise QWakeLC4ExecutionImplementationError(
                "execution lease disappeared before output promotion"
            )

        _rename_noreplace(staging_root, output_root)
        promoted = True
        _fsync_directory(output_parent)
        outcome = ExecutionWrapperOutcome(
            implementation_id=EXECUTION_IMPLEMENTATION_ID,
            lease_path=lease_path,
            output_root=output_root,
            wrapper_receipt_sha256=wrapper_receipt_sha256,
            backend_receipt=receipt,
        )
        outcome.require()
        return outcome
    except Exception:
        if not promoted and _lexists(staging_root):
            shutil.rmtree(staging_root)
        raise


def execute_authorized_runtime(
    project_root: Path,
    *,
    expected_wrapper_commit: str,
    backend: RuntimeExecutionBackend,
) -> ExecutionWrapperOutcome:
    """Verify frozen admission and run only after an existing lease claim."""

    root = project_root.expanduser().resolve()
    frozen_admission = verify_unconsumed_frozen_admission(root)
    return run_claimed_execution_wrapper(
        root,
        frozen_admission,
        expected_wrapper_commit=expected_wrapper_commit,
        backend=backend,
    )


def _atomic_exclusive_file_claim(
    root: Path,
    target: Path,
    payload: bytes,
) -> None:
    if not payload:
        raise QWakeLC4ExecutionImplementationError(
            "atomic file payload is empty"
        )
    root = root.expanduser().resolve()
    target = target.expanduser()
    _require_below_root(root, target)
    _ensure_directory_chain(root, target.parent)
    if _lexists(target):
        raise QWakeLC4ExecutionImplementationError(
            f"atomic target already exists: {target}"
        )

    temporary = target.parent / (
        f".{target.name}.tmp-{os.getpid()}-{secrets.token_hex(16)}"
    )
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor: int | None = None
    try:
        descriptor = os.open(temporary, flags, 0o600)
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise QWakeLC4ExecutionImplementationError(
                    "atomic file write made no progress"
                )
            view = view[written:]
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = None
        try:
            os.link(temporary, target, follow_symlinks=False)
        except FileExistsError as exc:
            raise QWakeLC4ExecutionImplementationError(
                f"atomic target already exists: {target}"
            ) from exc
        _fsync_directory(target.parent)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if _lexists(temporary):
            temporary.unlink()
            _fsync_directory(temporary.parent)


def _rename_noreplace(source: Path, target: Path) -> None:
    if os.name != "posix" or not sys.platform.startswith("linux"):
        raise QWakeLC4ExecutionImplementationError(
            "atomic no-replace directory promotion requires Linux"
        )
    if _lexists(target):
        raise QWakeLC4ExecutionImplementationError(
            "authorized output root already exists"
        )
    library = ctypes.CDLL(None, use_errno=True)
    try:
        renameat2 = cast(Any, library.renameat2)
    except AttributeError as exc:
        raise QWakeLC4ExecutionImplementationError(
            "renameat2 is unavailable"
        ) from exc
    renameat2.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    renameat2.restype = ctypes.c_int
    result = renameat2(
        _AT_FDCWD,
        os.fsencode(source),
        _AT_FDCWD,
        os.fsencode(target),
        _RENAME_NOREPLACE,
    )
    if result == 0:
        return
    error_number = ctypes.get_errno()
    if error_number == errno.EEXIST:
        raise QWakeLC4ExecutionImplementationError(
            "authorized output root already exists"
        )
    raise QWakeLC4ExecutionImplementationError(
        "atomic output promotion failed: " + os.strerror(error_number)
    )


def _validate_staging_tree(staging_root: Path) -> int:
    if not staging_root.is_dir() or staging_root.is_symlink():
        raise QWakeLC4ExecutionImplementationError(
            "runtime staging root is absent or non-regular"
        )
    regular_file_count = 0
    for current_root, directory_names, file_names in os.walk(
        staging_root,
        followlinks=False,
    ):
        current = Path(current_root)
        for directory_name in directory_names:
            directory = current / directory_name
            if directory.is_symlink() or not directory.is_dir():
                raise QWakeLC4ExecutionImplementationError(
                    "runtime staging tree contains a non-directory entry"
                )
        for file_name in file_names:
            file_path = current / file_name
            if file_path.is_symlink() or not file_path.is_file():
                raise QWakeLC4ExecutionImplementationError(
                    "runtime staging tree contains a non-regular file"
                )
            regular_file_count += 1
    if regular_file_count < 1:
        raise QWakeLC4ExecutionImplementationError(
            "runtime staging tree contains no regular output file"
        )
    return regular_file_count


def _fsync_tree(root: Path) -> None:
    directories: list[Path] = []
    for current_root, directory_names, file_names in os.walk(
        root,
        topdown=True,
        followlinks=False,
    ):
        current = Path(current_root)
        directories.append(current)
        for file_name in file_names:
            file_path = current / file_name
            descriptor = os.open(file_path, os.O_RDONLY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        for directory_name in directory_names:
            directory = current / directory_name
            if directory.is_symlink():
                raise QWakeLC4ExecutionImplementationError(
                    "runtime staging tree contains a symlink"
                )
    for directory in reversed(directories):
        _fsync_directory(directory)


def _ensure_directory_chain(root: Path, directory: Path) -> None:
    root = root.expanduser().resolve()
    directory = directory.expanduser()
    _require_below_root(root, directory)
    relative = directory.relative_to(root)
    current = root
    for part in relative.parts:
        current = current / part
        if _lexists(current):
            mode = current.lstat().st_mode
            if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
                raise QWakeLC4ExecutionImplementationError(
                    f"directory chain contains a non-directory: {current}"
                )
        else:
            current.mkdir(mode=0o700)
            _fsync_directory(current.parent)


def _require_below_root(root: Path, path: Path) -> None:
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise QWakeLC4ExecutionImplementationError(
            f"effect path escapes project root: {path}"
        ) from exc


def _fsync_directory(directory: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(directory, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _lexists(path: Path) -> bool:
    return os.path.lexists(path)


def _require_commit(value: str, field_name: str) -> None:
    if len(value) != 40 or any(character not in "0123456789abcdef" for character in value):
        raise QWakeLC4ExecutionImplementationError(
            f"{field_name} is not a commit"
        )


def _require_sha256(value: str, field_name: str) -> None:
    if not value.startswith("sha256:") or len(value) != 71:
        raise QWakeLC4ExecutionImplementationError(
            f"{field_name} is not a SHA-256 identity"
        )
    digest = value.removeprefix("sha256:")
    if any(character not in "0123456789abcdef" for character in digest):
        raise QWakeLC4ExecutionImplementationError(
            f"{field_name} is not a SHA-256 identity"
        )
