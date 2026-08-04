"""Atomic lease and no-replace output wrapper for attempt 002.

All effects are explicit.  The implementation owns only the attempt-002 paths
from the new contract and does not call any historical claim or runtime entry
point.
"""

from __future__ import annotations

import ctypes
import errno
import json
import os
import secrets
import shutil
import stat
import sys
import tempfile
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Final, Protocol, cast

from torch2pc_thesis.stage3b_qwake_lc4_attempt_002_contract import (
    ATTEMPT_002_ID,
    ATTEMPT_002_LEASE_ACKNOWLEDGEMENT,
    ATTEMPT_002_LEASE_V1_RELATIVE,
    ATTEMPT_002_OUTPUT_ROOT,
    AUTHORIZED_CELL_COUNT,
    RESERVE_PROBE_COUNT,
    Attempt002AdmissionIdentity,
    canonical_json,
    sha256_object,
)

ATTEMPT_002_LEASE_ID: Final = "stage3b-qwake-lc4-e-attempt-002-lease-v1"
ATTEMPT_002_WRAPPER_CONTRACT_ID: Final = (
    "stage3b-qwake-lc4-e-attempt-002-wrapper-contract-v1"
)
ATTEMPT_002_BACKEND_RECEIPT_ID: Final = (
    "stage3b-qwake-lc4-e-attempt-002-backend-receipt-v1"
)
ATTEMPT_002_WRAPPER_RECEIPT_ID: Final = (
    "stage3b-qwake-lc4-e-attempt-002-wrapper-receipt-v1"
)
ATTEMPT_002_WRAPPER_RECEIPT_RELATIVE: Final = Path(
    "execution-wrapper-receipt.json"
)
_AT_FDCWD: Final = -100
_RENAME_NOREPLACE: Final = 1

__all__ = [
    "ATTEMPT_002_BACKEND_RECEIPT_ID",
    "ATTEMPT_002_LEASE_ID",
    "ATTEMPT_002_WRAPPER_CONTRACT_ID",
    "ATTEMPT_002_WRAPPER_RECEIPT_ID",
    "ATTEMPT_002_WRAPPER_RECEIPT_RELATIVE",
    "Attempt002BackendReceipt",
    "Attempt002ExecutionBackend",
    "Attempt002ExecutionOutcome",
    "Attempt002ExecutionWrapperError",
    "Attempt002LeaseV1",
    "Attempt002WrapperContract",
    "build_attempt_002_backend_receipt",
    "build_attempt_002_lease",
    "build_attempt_002_wrapper_contract",
    "load_attempt_002_lease",
    "materialize_attempt_002_lease",
    "run_claimed_attempt_002",
]


class Attempt002ExecutionWrapperError(RuntimeError):
    """Raised when attempt-002 effects cannot preserve the contract."""


@dataclass(frozen=True)
class Attempt002LeaseV1:
    """Canonical one-shot claim for attempt 002."""

    schema_version: int
    lease_id: str
    attempt_id: str
    freeze_sha256: str
    authorization_sha256: str
    scientific_authorization_sha256: str
    claimed_at_utc: str
    wrapper_commit: str
    operator_acknowledgement: str
    output_root: str
    execution_lease_relative: str
    output_root_absent_at_claim: bool
    execution_lease_absent_at_claim: bool
    execution_count: int
    authorization_consumed: bool
    attempt_started: bool
    runtime_execution_started: bool
    runtime_execution_performed: bool
    retry_permitted: bool
    lease_sha256: str

    def require(self, admission: Attempt002AdmissionIdentity) -> None:
        admission.require()
        expected: Mapping[str, object] = {
            "schema_version": 1,
            "lease_id": ATTEMPT_002_LEASE_ID,
            "attempt_id": ATTEMPT_002_ID,
            "freeze_sha256": admission.freeze_sha256,
            "authorization_sha256": admission.authorization_sha256,
            "scientific_authorization_sha256": (
                admission.scientific_authorization_sha256
            ),
            "wrapper_commit": admission.wrapper_commit,
            "operator_acknowledgement": ATTEMPT_002_LEASE_ACKNOWLEDGEMENT,
            "output_root": ATTEMPT_002_OUTPUT_ROOT.as_posix(),
            "execution_lease_relative": (
                ATTEMPT_002_LEASE_V1_RELATIVE.as_posix()
            ),
            "output_root_absent_at_claim": True,
            "execution_lease_absent_at_claim": True,
            "execution_count": 1,
            "authorization_consumed": True,
            "attempt_started": True,
            "runtime_execution_started": False,
            "runtime_execution_performed": False,
            "retry_permitted": False,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise Attempt002ExecutionWrapperError(
                    f"attempt-002 lease {field_name} differs"
                )
        _require_utc(self.claimed_at_utc, "claimed_at_utc")
        _require_commit(self.wrapper_commit, "wrapper_commit")
        _require_sha256(self.lease_sha256, "lease_sha256")
        if self.lease_sha256 != sha256_object(self._payload_without_digest()):
            raise Attempt002ExecutionWrapperError(
                "attempt-002 lease digest differs"
            )

    def _payload_without_digest(self) -> Mapping[str, object]:
        payload = asdict(self)
        payload.pop("lease_sha256")
        return cast(Mapping[str, object], payload)

    def canonical_json(self) -> str:
        return canonical_json(self)


@dataclass(frozen=True)
class Attempt002WrapperContract:
    """Runtime contract derived only from the materialized lease."""

    schema_version: int
    contract_id: str
    attempt_id: str
    freeze_sha256: str
    authorization_sha256: str
    lease_sha256: str
    wrapper_commit: str
    output_root: str
    authorized_cell_count: int
    reserve_probe_count: int
    runtime_execution_permitted: bool
    atomic_output_promotion_required: bool
    retry_permitted: bool
    scientific_execution_open: bool
    test_dataset_access: bool
    publication_permitted: bool
    contract_sha256: str

    def require(self, lease: Attempt002LeaseV1) -> None:
        expected: Mapping[str, object] = {
            "schema_version": 1,
            "contract_id": ATTEMPT_002_WRAPPER_CONTRACT_ID,
            "attempt_id": ATTEMPT_002_ID,
            "freeze_sha256": lease.freeze_sha256,
            "authorization_sha256": lease.authorization_sha256,
            "lease_sha256": lease.lease_sha256,
            "wrapper_commit": lease.wrapper_commit,
            "output_root": ATTEMPT_002_OUTPUT_ROOT.as_posix(),
            "authorized_cell_count": AUTHORIZED_CELL_COUNT,
            "reserve_probe_count": RESERVE_PROBE_COUNT,
            "runtime_execution_permitted": True,
            "atomic_output_promotion_required": True,
            "retry_permitted": False,
            "scientific_execution_open": False,
            "test_dataset_access": False,
            "publication_permitted": False,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise Attempt002ExecutionWrapperError(
                    f"attempt-002 wrapper contract {field_name} differs"
                )
        _require_sha256(self.contract_sha256, "contract_sha256")
        if self.contract_sha256 != sha256_object(
            self._payload_without_digest()
        ):
            raise Attempt002ExecutionWrapperError(
                "attempt-002 wrapper contract digest differs"
            )

    def _payload_without_digest(self) -> Mapping[str, object]:
        payload = asdict(self)
        payload.pop("contract_sha256")
        return cast(Mapping[str, object], payload)


@dataclass(frozen=True)
class Attempt002BackendReceipt:
    """Canonical receipt returned by an injected attempt-002 backend."""

    schema_version: int
    receipt_id: str
    backend_id: str
    attempt_id: str
    freeze_sha256: str
    authorization_sha256: str
    lease_sha256: str
    contract_sha256: str
    wrapper_commit: str
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

    def require(
        self,
        lease: Attempt002LeaseV1,
        contract: Attempt002WrapperContract,
    ) -> None:
        contract.require(lease)
        expected: Mapping[str, object] = {
            "schema_version": 1,
            "receipt_id": ATTEMPT_002_BACKEND_RECEIPT_ID,
            "attempt_id": ATTEMPT_002_ID,
            "freeze_sha256": lease.freeze_sha256,
            "authorization_sha256": lease.authorization_sha256,
            "lease_sha256": lease.lease_sha256,
            "contract_sha256": contract.contract_sha256,
            "wrapper_commit": lease.wrapper_commit,
            "authorized_cell_count": AUTHORIZED_CELL_COUNT,
            "reserve_probe_count": RESERVE_PROBE_COUNT,
            "runtime_execution_started": True,
            "runtime_execution_performed": True,
            "engineering_evidence_present": True,
            "scientific_execution_open": False,
            "test_dataset_access": False,
            "publication_permitted": False,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise Attempt002ExecutionWrapperError(
                    f"attempt-002 backend receipt {field_name} differs"
                )
        if not self.backend_id:
            raise Attempt002ExecutionWrapperError(
                "attempt-002 backend id is empty"
            )
        if self.output_file_count < 1:
            raise Attempt002ExecutionWrapperError(
                "attempt-002 backend produced no regular file"
            )
        _require_sha256(self.receipt_sha256, "receipt_sha256")
        if self.receipt_sha256 != sha256_object(
            self._payload_without_digest()
        ):
            raise Attempt002ExecutionWrapperError(
                "attempt-002 backend receipt digest differs"
            )

    def _payload_without_digest(self) -> Mapping[str, object]:
        payload = asdict(self)
        payload.pop("receipt_sha256")
        return cast(Mapping[str, object], payload)

    def canonical_json(self) -> str:
        return canonical_json(self)


class Attempt002ExecutionBackend(Protocol):
    """Injected backend surface for the new isolated wrapper."""

    @property
    def backend_id(self) -> str:
        """Return a stable backend identity."""

        ...

    def run(
        self,
        staging_root: Path,
        lease: Attempt002LeaseV1,
        contract: Attempt002WrapperContract,
    ) -> Attempt002BackendReceipt:
        """Write complete engineering evidence below ``staging_root``."""

        ...


@dataclass(frozen=True)
class Attempt002ExecutionOutcome:
    """Successful no-replace promotion for attempt 002."""

    lease_path: Path
    output_root: Path
    wrapper_receipt_sha256: str
    backend_receipt: Attempt002BackendReceipt

    def require(self) -> None:
        if not self.lease_path.is_file() or self.lease_path.is_symlink():
            raise Attempt002ExecutionWrapperError(
                "attempt-002 outcome lease is absent"
            )
        if not self.output_root.is_dir() or self.output_root.is_symlink():
            raise Attempt002ExecutionWrapperError(
                "attempt-002 outcome root is absent"
            )
        _require_sha256(
            self.wrapper_receipt_sha256,
            "wrapper_receipt_sha256",
        )


def build_attempt_002_lease(
    admission: Attempt002AdmissionIdentity,
    *,
    claimed_at_utc: str,
    wrapper_commit: str,
    operator_acknowledgement: str,
) -> Attempt002LeaseV1:
    """Build exact lease bytes before the irreversible claim."""

    admission.require()
    payload: dict[str, object] = {
        "schema_version": 1,
        "lease_id": ATTEMPT_002_LEASE_ID,
        "attempt_id": ATTEMPT_002_ID,
        "freeze_sha256": admission.freeze_sha256,
        "authorization_sha256": admission.authorization_sha256,
        "scientific_authorization_sha256": (
            admission.scientific_authorization_sha256
        ),
        "claimed_at_utc": claimed_at_utc,
        "wrapper_commit": wrapper_commit,
        "operator_acknowledgement": operator_acknowledgement,
        "output_root": ATTEMPT_002_OUTPUT_ROOT.as_posix(),
        "execution_lease_relative": ATTEMPT_002_LEASE_V1_RELATIVE.as_posix(),
        "output_root_absent_at_claim": True,
        "execution_lease_absent_at_claim": True,
        "execution_count": 1,
        "authorization_consumed": True,
        "attempt_started": True,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "retry_permitted": False,
    }
    lease = Attempt002LeaseV1(
        **cast(dict[str, Any], payload),
        lease_sha256=sha256_object(payload),
    )
    lease.require(admission)
    return lease


def build_attempt_002_wrapper_contract(
    lease: Attempt002LeaseV1,
    admission: Attempt002AdmissionIdentity,
) -> Attempt002WrapperContract:
    """Derive a runtime contract from the exact claimed lease."""

    lease.require(admission)
    payload: dict[str, object] = {
        "schema_version": 1,
        "contract_id": ATTEMPT_002_WRAPPER_CONTRACT_ID,
        "attempt_id": ATTEMPT_002_ID,
        "freeze_sha256": lease.freeze_sha256,
        "authorization_sha256": lease.authorization_sha256,
        "lease_sha256": lease.lease_sha256,
        "wrapper_commit": lease.wrapper_commit,
        "output_root": ATTEMPT_002_OUTPUT_ROOT.as_posix(),
        "authorized_cell_count": AUTHORIZED_CELL_COUNT,
        "reserve_probe_count": RESERVE_PROBE_COUNT,
        "runtime_execution_permitted": True,
        "atomic_output_promotion_required": True,
        "retry_permitted": False,
        "scientific_execution_open": False,
        "test_dataset_access": False,
        "publication_permitted": False,
    }
    contract = Attempt002WrapperContract(
        **cast(dict[str, Any], payload),
        contract_sha256=sha256_object(payload),
    )
    contract.require(lease)
    return contract


def build_attempt_002_backend_receipt(
    *,
    backend_id: str,
    lease: Attempt002LeaseV1,
    contract: Attempt002WrapperContract,
    output_file_count: int,
) -> Attempt002BackendReceipt:
    """Build a canonical completed engineering-backend receipt."""

    contract.require(lease)
    payload: dict[str, object] = {
        "schema_version": 1,
        "receipt_id": ATTEMPT_002_BACKEND_RECEIPT_ID,
        "backend_id": backend_id,
        "attempt_id": ATTEMPT_002_ID,
        "freeze_sha256": lease.freeze_sha256,
        "authorization_sha256": lease.authorization_sha256,
        "lease_sha256": lease.lease_sha256,
        "contract_sha256": contract.contract_sha256,
        "wrapper_commit": lease.wrapper_commit,
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
    receipt = Attempt002BackendReceipt(
        **cast(dict[str, Any], payload),
        receipt_sha256=sha256_object(payload),
    )
    receipt.require(lease, contract)
    return receipt


def materialize_attempt_002_lease(
    project_root: Path,
    lease: Attempt002LeaseV1,
    admission: Attempt002AdmissionIdentity,
) -> Path:
    """Create lease v1 exactly once with an atomic hard-link claim."""

    root = project_root.expanduser().resolve()
    lease.require(admission)
    output_root = root / ATTEMPT_002_OUTPUT_ROOT
    lease_path = root / ATTEMPT_002_LEASE_V1_RELATIVE
    if _lexists(output_root):
        raise Attempt002ExecutionWrapperError(
            "attempt-002 output root already exists"
        )
    if _lexists(lease_path):
        raise Attempt002ExecutionWrapperError(
            "attempt-002 execution lease already exists"
        )
    _atomic_exclusive_file_claim(
        root,
        lease_path,
        lease.canonical_json().encode("utf-8"),
    )
    if _lexists(output_root):
        raise Attempt002ExecutionWrapperError(
            "attempt-002 output appeared during lease claim"
        )
    observed = load_attempt_002_lease(
        root,
        admission,
        require_output_absent=True,
    )
    if observed != lease:
        raise Attempt002ExecutionWrapperError(
            "materialized attempt-002 lease differs"
        )
    return lease_path


def load_attempt_002_lease(
    project_root: Path,
    admission: Attempt002AdmissionIdentity,
    *,
    require_output_absent: bool,
) -> Attempt002LeaseV1:
    """Load exact already-claimed bytes without permitting retry."""

    root = project_root.expanduser().resolve()
    lease_path = root / ATTEMPT_002_LEASE_V1_RELATIVE
    if not lease_path.is_file() or lease_path.is_symlink():
        raise Attempt002ExecutionWrapperError(
            "attempt-002 execution lease is absent or non-regular"
        )
    try:
        value = json.loads(lease_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise Attempt002ExecutionWrapperError(
            "attempt-002 execution lease JSON is invalid"
        ) from exc
    if not isinstance(value, dict):
        raise Attempt002ExecutionWrapperError(
            "attempt-002 execution lease root differs"
        )
    lease = Attempt002LeaseV1(**cast(dict[str, Any], value))
    lease.require(admission)
    if stat.S_IMODE(lease_path.stat(follow_symlinks=False).st_mode) != 0o600:
        raise Attempt002ExecutionWrapperError(
            "attempt-002 execution lease mode differs"
        )
    if lease_path.read_bytes() != lease.canonical_json().encode("utf-8"):
        raise Attempt002ExecutionWrapperError(
            "attempt-002 execution lease serialization differs"
        )
    output_root = root / ATTEMPT_002_OUTPUT_ROOT
    if require_output_absent and _lexists(output_root):
        raise Attempt002ExecutionWrapperError(
            "attempt-002 output root already exists"
        )
    return lease


def run_claimed_attempt_002(
    project_root: Path,
    admission: Attempt002AdmissionIdentity,
    lease: Attempt002LeaseV1,
    *,
    backend: Attempt002ExecutionBackend,
) -> Attempt002ExecutionOutcome:
    """Run one backend and promote complete output without replacement."""

    root = project_root.expanduser().resolve()
    lease.require(admission)
    observed = load_attempt_002_lease(
        root,
        admission,
        require_output_absent=True,
    )
    if observed != lease:
        raise Attempt002ExecutionWrapperError(
            "attempt-002 provided lease differs from materialized claim"
        )
    contract = build_attempt_002_wrapper_contract(lease, admission)
    if not backend.backend_id:
        raise Attempt002ExecutionWrapperError("attempt-002 backend id is empty")

    output_root = root / ATTEMPT_002_OUTPUT_ROOT
    lease_path = root / ATTEMPT_002_LEASE_V1_RELATIVE
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
        receipt.require(lease, contract)
        if receipt.backend_id != backend.backend_id:
            raise Attempt002ExecutionWrapperError(
                "attempt-002 backend receipt identity differs"
            )
        output_file_count = _validate_staging_tree(staging_root)
        if receipt.output_file_count != output_file_count:
            raise Attempt002ExecutionWrapperError(
                "attempt-002 backend output count differs"
            )
        wrapper_payload: dict[str, object] = {
            "schema_version": 1,
            "receipt_id": ATTEMPT_002_WRAPPER_RECEIPT_ID,
            "attempt_id": ATTEMPT_002_ID,
            "freeze_sha256": admission.freeze_sha256,
            "authorization_sha256": admission.authorization_sha256,
            "lease_sha256": lease.lease_sha256,
            "contract_sha256": contract.contract_sha256,
            "backend_receipt": asdict(receipt),
            "output_root": ATTEMPT_002_OUTPUT_ROOT.as_posix(),
            "atomic_output_promotion": True,
            "authorization_consumed": True,
            "attempt_started": True,
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
            staging_root / ATTEMPT_002_WRAPPER_RECEIPT_RELATIVE,
            canonical_json(wrapper_payload).encode("utf-8"),
        )
        _validate_staging_tree(staging_root)
        _fsync_tree(staging_root)
        if load_attempt_002_lease(
            root,
            admission,
            require_output_absent=True,
        ) != lease:
            raise Attempt002ExecutionWrapperError(
                "attempt-002 lease changed before promotion"
            )
        _rename_noreplace(staging_root, output_root)
        promoted = True
        _fsync_directory(output_parent)
        outcome = Attempt002ExecutionOutcome(
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


def _atomic_exclusive_file_claim(root: Path, target: Path, payload: bytes) -> None:
    if not payload:
        raise Attempt002ExecutionWrapperError("atomic file payload is empty")
    root = root.expanduser().resolve()
    target = target.expanduser()
    _require_below_root(root, target)
    _ensure_directory_chain(root, target.parent)
    if _lexists(target):
        raise Attempt002ExecutionWrapperError(
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
                raise Attempt002ExecutionWrapperError(
                    "atomic file write made no progress"
                )
            view = view[written:]
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = None
        try:
            os.link(temporary, target, follow_symlinks=False)
        except FileExistsError as exc:
            raise Attempt002ExecutionWrapperError(
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
        raise Attempt002ExecutionWrapperError(
            "atomic directory promotion requires Linux"
        )
    if _lexists(target):
        raise Attempt002ExecutionWrapperError(
            "attempt-002 output root already exists"
        )
    library = ctypes.CDLL(None, use_errno=True)
    try:
        renameat2 = cast(Any, library.renameat2)
    except AttributeError as exc:
        raise Attempt002ExecutionWrapperError("renameat2 is unavailable") from exc
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
        raise Attempt002ExecutionWrapperError(
            "attempt-002 output root already exists"
        )
    raise Attempt002ExecutionWrapperError(
        "atomic output promotion failed: " + os.strerror(error_number)
    )


def _validate_staging_tree(staging_root: Path) -> int:
    if not staging_root.is_dir() or staging_root.is_symlink():
        raise Attempt002ExecutionWrapperError(
            "attempt-002 staging root is absent or non-directory"
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
                raise Attempt002ExecutionWrapperError(
                    "attempt-002 staging contains a non-directory entry"
                )
        for file_name in file_names:
            file_path = current / file_name
            if file_path.is_symlink() or not file_path.is_file():
                raise Attempt002ExecutionWrapperError(
                    "attempt-002 staging contains a non-regular file"
                )
            regular_file_count += 1
    if regular_file_count < 1:
        raise Attempt002ExecutionWrapperError(
            "attempt-002 staging contains no regular output file"
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
                raise Attempt002ExecutionWrapperError(
                    "attempt-002 staging contains a symlink"
                )
    for directory in reversed(directories):
        _fsync_directory(directory)


def _ensure_directory_chain(root: Path, directory: Path) -> None:
    root = root.expanduser().resolve()
    directory = directory.expanduser()
    _require_below_root(root, directory)
    current = root
    for part in directory.relative_to(root).parts:
        current = current / part
        if _lexists(current):
            mode = current.lstat().st_mode
            if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
                raise Attempt002ExecutionWrapperError(
                    f"directory chain contains a non-directory: {current}"
                )
        else:
            current.mkdir(mode=0o700)
            _fsync_directory(current.parent)


def _require_below_root(root: Path, path: Path) -> None:
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise Attempt002ExecutionWrapperError(
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
    invalid = any(character not in "0123456789abcdef" for character in value)
    if len(value) != 40 or invalid:
        raise Attempt002ExecutionWrapperError(f"{field_name} is not a commit")


def _require_sha256(value: str, field_name: str) -> None:
    if not value.startswith("sha256:") or len(value) != 71:
        raise Attempt002ExecutionWrapperError(f"{field_name} is not SHA-256")
    digest = value.removeprefix("sha256:")
    if any(character not in "0123456789abcdef" for character in digest):
        raise Attempt002ExecutionWrapperError(f"{field_name} is not SHA-256")


def _require_utc(value: str, field_name: str) -> None:
    if not value.endswith("Z"):
        raise Attempt002ExecutionWrapperError(f"{field_name} is not UTC")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise Attempt002ExecutionWrapperError(f"{field_name} is invalid") from exc
    offset = parsed.utcoffset()
    if offset is None or offset.total_seconds() != 0:
        raise Attempt002ExecutionWrapperError(f"{field_name} is not UTC")
