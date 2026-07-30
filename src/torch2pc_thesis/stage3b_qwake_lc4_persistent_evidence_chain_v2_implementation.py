"""Fail-closed persistence for QW-LC4-E evidence-chain-v2 artifacts.

The module implements exclusive durable writes for the already-authored
persistent execution lease v2 and terminal host-outcome receipt.  It does not
inspect container images, materialize commands, spawn subprocesses, invoke
Docker, execute local compute, or wire the host runtime invoker.
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from torch2pc_thesis.stage3b_qwake_lc4_persistent_evidence_chain_v2 import (
    CHAIN_RECORD_RELATIVE,
    DURABLE_HOST_OUTCOME_RELATIVE,
    EXECUTION_LEASE_V2_RELATIVE,
    POST_MERGE_RECEIPT_RELATIVE,
    REGISTRY_RELATIVE,
    SOURCE_REGISTRY_RELATIVE,
    DurableHostOutcomeReceipt,
    PersistentEvidenceChainV2,
    PersistentEvidenceChainV2Error,
    PersistentExecutionLeaseV2,
    load_persistent_evidence_chain_v2,
    load_post_merge_validation_receipt,
    sha256_bytes,
    verify_persistent_evidence_chain_v2,
)

PERSISTENT_EVIDENCE_CHAIN_V2_IMPLEMENTATION_ID: Final = (
    "stage3b-qwake-lc4-e-persistent-evidence-chain-v2-implementation-v1"
)
PERSISTENT_EVIDENCE_CHAIN_V2_IMPLEMENTATION_STATUS: Final = (
    "persistent_writers_implemented_runtime_wiring_closed"
)
IMPLEMENTATION_BASE_COMMIT: Final = (
    "3d092440b0314f02072c9773cc91018bf2860744"
)
AUTHORING_PR_NUMBER: Final = 144
AUTHORING_HEAD_COMMIT: Final = (
    "a813d11e3b5ea2d07ef4cd1cb96687aee21c9338"
)
AUTHORING_PARENT_COMMIT: Final = (
    "5e61ed650c9beda2cde1f58650345f01694836f6"
)
AUTHORING_MERGE_COMMIT: Final = IMPLEMENTATION_BASE_COMMIT
AUTHORING_MERGED_AT_UTC: Final = "2026-07-30T03:37:38Z"
LEGACY_EXECUTION_LEASE_RELATIVE: Final = Path(
    "results/stage-3/"
    "qwake-lc4-runtime-validation-v1-attempt-001.execution-lease.json"
)

IMPLEMENTATION_PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-persistent-evidence-chain-v2-implementation-v1"
)
IMPLEMENTATION_RECORD_RELATIVE: Final = (
    IMPLEMENTATION_PACKAGE_RELATIVE / "implementation.json"
)
AUTHORING_MERGE_RECEIPT_RELATIVE: Final = (
    IMPLEMENTATION_PACKAGE_RELATIVE / "authoring-merge-validation.json"
)
IMPLEMENTATION_REGISTRY_RELATIVE: Final = (
    IMPLEMENTATION_PACKAGE_RELATIVE / "SHA256SUMS"
)
IMPLEMENTATION_SOURCE_REGISTRY_RELATIVE: Final = (
    IMPLEMENTATION_PACKAGE_RELATIVE / "source-SHA256SUMS"
)
IMPLEMENTATION_MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_persistent_evidence_chain_v2_implementation.py"
)
IMPLEMENTATION_VERIFIER_RELATIVE: Final = Path(
    "scripts/verify_stage3b_qwake_lc4_persistent_evidence_chain_v2_implementation.py"
)
IMPLEMENTATION_TEST_RELATIVE: Final = Path(
    "tests/unit/"
    "test_stage3b_qwake_lc4_persistent_evidence_chain_v2_implementation.py"
)
IMPLEMENTATION_ADR_RU_RELATIVE: Final = Path(
    "docs/decisions/"
    "ADR-084-stage3b-qwake-lc4-e-persistent-evidence-chain-v2-implementation.md"
)
IMPLEMENTATION_ADR_EN_RELATIVE: Final = Path(
    "docs/decisions/"
    "ADR-084-stage3b-qwake-lc4-e-persistent-evidence-chain-v2-implementation_EN.md"
)

__all__ = [
    "PERSISTENT_EVIDENCE_CHAIN_V2_IMPLEMENTATION_ID",
    "PersistentEvidenceChainV2ImplementationError",
    "PersistentWriteResult",
    "persist_durable_host_outcome_receipt",
    "persist_persistent_execution_lease_v2",
    "verify_persisted_durable_host_outcome_receipt",
    "verify_persisted_persistent_execution_lease_v2",
]


class PersistentEvidenceChainV2ImplementationError(RuntimeError):
    """Raised when a persistent write or verification fails closed."""


@dataclass(frozen=True)
class PersistentWriteResult:
    """Identity of one successfully persisted immutable JSON artifact."""

    relative_path: str
    byte_count: int
    sha256: str
    mode: int

    def require(self) -> None:
        if not self.relative_path or Path(self.relative_path).is_absolute():
            raise PersistentEvidenceChainV2ImplementationError(
                "persistent write result path is invalid"
            )
        if self.byte_count <= 0:
            raise PersistentEvidenceChainV2ImplementationError(
                "persistent write result is empty"
            )
        if not self.sha256.startswith("sha256:") or len(self.sha256) != 71:
            raise PersistentEvidenceChainV2ImplementationError(
                "persistent write result digest is invalid"
            )
        if self.mode != 0o600:
            raise PersistentEvidenceChainV2ImplementationError(
                "persistent write result mode differs"
            )


def persist_persistent_execution_lease_v2(
    project_root: Path,
    chain: PersistentEvidenceChainV2,
    lease: PersistentExecutionLeaseV2,
) -> PersistentWriteResult:
    """Persist one immutable lease v2 after exact absence checks.

    The function only writes the lease file.  It does not inspect the image,
    materialize a command, start execution, or call the host invoker.
    """

    root = _verified_root(project_root, chain, require_closed_boundary=True)
    _require_lease(chain, lease)
    output_root = _target(root, Path(chain.source.output_root))
    legacy_lease = _target(root, LEGACY_EXECUTION_LEASE_RELATIVE)
    lease_target = _target(root, EXECUTION_LEASE_V2_RELATIVE)
    outcome_target = _target(root, DURABLE_HOST_OUTCOME_RELATIVE)

    _require_absent(output_root, "authorized output root")
    _require_absent(legacy_lease, "legacy execution lease")
    _require_absent(lease_target, "persistent execution lease v2")
    _require_absent(outcome_target, "durable host outcome")
    if not (
        lease.output_root_absent_at_claim
        and lease.execution_lease_absent_at_claim
        and lease.durable_outcome_absent_at_claim
    ):
        raise PersistentEvidenceChainV2ImplementationError(
            "lease absence claims differ from required preconditions"
        )

    return _atomic_write_once(
        root,
        lease_target,
        lease.canonical_json().encode("utf-8"),
    )


def verify_persisted_persistent_execution_lease_v2(
    project_root: Path,
    chain: PersistentEvidenceChainV2,
    lease: PersistentExecutionLeaseV2,
) -> PersistentWriteResult:
    """Verify exact persisted lease bytes and filesystem identity."""

    root = _verified_root(project_root, chain, require_closed_boundary=False)
    _require_lease(chain, lease)
    return _verify_exact_file(
        root,
        _target(root, EXECUTION_LEASE_V2_RELATIVE),
        lease.canonical_json().encode("utf-8"),
    )


def persist_durable_host_outcome_receipt(
    project_root: Path,
    chain: PersistentEvidenceChainV2,
    lease: PersistentExecutionLeaseV2,
    receipt: DurableHostOutcomeReceipt,
) -> PersistentWriteResult:
    """Persist one immutable terminal receipt after exact lease verification."""

    root = _verified_root(project_root, chain, require_closed_boundary=False)
    _require_lease(chain, lease)
    _require_receipt(chain, lease, receipt)
    lease_target = _target(root, EXECUTION_LEASE_V2_RELATIVE)
    outcome_target = _target(root, DURABLE_HOST_OUTCOME_RELATIVE)

    _verify_exact_file(
        root,
        lease_target,
        lease.canonical_json().encode("utf-8"),
    )
    _require_absent(outcome_target, "durable host outcome")
    return _atomic_write_once(
        root,
        outcome_target,
        receipt.canonical_json().encode("utf-8"),
    )


def verify_persisted_durable_host_outcome_receipt(
    project_root: Path,
    chain: PersistentEvidenceChainV2,
    lease: PersistentExecutionLeaseV2,
    receipt: DurableHostOutcomeReceipt,
) -> PersistentWriteResult:
    """Verify exact persisted terminal receipt bytes and filesystem identity."""

    root = _verified_root(project_root, chain, require_closed_boundary=False)
    _require_lease(chain, lease)
    _require_receipt(chain, lease, receipt)
    _verify_exact_file(
        root,
        _target(root, EXECUTION_LEASE_V2_RELATIVE),
        lease.canonical_json().encode("utf-8"),
    )
    return _verify_exact_file(
        root,
        _target(root, DURABLE_HOST_OUTCOME_RELATIVE),
        receipt.canonical_json().encode("utf-8"),
    )



def _require_lease(
    chain: PersistentEvidenceChainV2,
    lease: PersistentExecutionLeaseV2,
) -> None:
    try:
        lease.require(chain)
    except PersistentEvidenceChainV2Error as exc:
        raise PersistentEvidenceChainV2ImplementationError(str(exc)) from exc


def _require_receipt(
    chain: PersistentEvidenceChainV2,
    lease: PersistentExecutionLeaseV2,
    receipt: DurableHostOutcomeReceipt,
) -> None:
    try:
        receipt.require(chain, lease)
    except PersistentEvidenceChainV2Error as exc:
        raise PersistentEvidenceChainV2ImplementationError(str(exc)) from exc

def _verified_root(
    project_root: Path,
    supplied_chain: PersistentEvidenceChainV2,
    *,
    require_closed_boundary: bool,
) -> Path:
    expanded = project_root.expanduser()
    if expanded.is_symlink():
        raise PersistentEvidenceChainV2ImplementationError(
            "project root is symbolic"
        )
    root = expanded.resolve()
    if not root.is_dir():
        raise PersistentEvidenceChainV2ImplementationError(
            "project root is absent or non-directory"
        )
    try:
        _verify_implementation_freeze(root)
        if require_closed_boundary:
            frozen_chain = verify_persistent_evidence_chain_v2(root)
        else:
            frozen_chain = _verify_static_chain(root)
        supplied_chain.require()
    except PersistentEvidenceChainV2ImplementationError:
        raise
    except (
        PersistentEvidenceChainV2Error,
        OSError,
        UnicodeError,
        ValueError,
    ) as exc:
        raise PersistentEvidenceChainV2ImplementationError(str(exc)) from exc
    if supplied_chain.canonical_json() != frozen_chain.canonical_json():
        raise PersistentEvidenceChainV2ImplementationError(
            "supplied evidence chain differs from frozen project chain"
        )
    return root



def _verify_implementation_freeze(root: Path) -> None:
    package = root / IMPLEMENTATION_PACKAGE_RELATIVE
    if not package.is_dir() or package.is_symlink():
        raise PersistentEvidenceChainV2ImplementationError(
            "implementation package is absent or invalid"
        )
    expected_files = {
        "SHA256SUMS",
        "authoring-merge-validation.json",
        "implementation.json",
        "source-SHA256SUMS",
    }
    if {path.name for path in package.iterdir()} != expected_files:
        raise PersistentEvidenceChainV2ImplementationError(
            "implementation package file set differs"
        )
    _verify_registry(root / IMPLEMENTATION_REGISTRY_RELATIVE, package)
    _verify_registry(root / IMPLEMENTATION_SOURCE_REGISTRY_RELATIVE, root)
    record_path = root / IMPLEMENTATION_RECORD_RELATIVE
    try:
        record = json.loads(
            record_path.read_text(encoding="utf-8", errors="strict")
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PersistentEvidenceChainV2ImplementationError(
            "implementation record is invalid"
        ) from exc
    if not isinstance(record, dict):
        raise PersistentEvidenceChainV2ImplementationError(
            "implementation record root differs"
        )
    exact: dict[str, object] = {
        "schema_version": 1,
        "implementation_id": PERSISTENT_EVIDENCE_CHAIN_V2_IMPLEMENTATION_ID,
        "status": PERSISTENT_EVIDENCE_CHAIN_V2_IMPLEMENTATION_STATUS,
        "implementation_base_commit": IMPLEMENTATION_BASE_COMMIT,
        "authoring_pr_number": AUTHORING_PR_NUMBER,
        "authoring_head_commit": AUTHORING_HEAD_COMMIT,
        "authoring_parent_commit": AUTHORING_PARENT_COMMIT,
        "authoring_merge_commit": AUTHORING_MERGE_COMMIT,
        "authoring_merged_at_utc": AUTHORING_MERGED_AT_UTC,
        "persistent_lease_v2_implementation_present": True,
        "durable_outcome_writer_implemented": True,
        "lease_bound_host_invoker_enforced": False,
        "one_shot_engineering_invocation_permitted": False,
        "runtime_execution_performed": False,
        "docker_run_performed": False,
        "local_compute_execution_open": False,
    }
    for field_name, expected in exact.items():
        if record.get(field_name) != expected:
            raise PersistentEvidenceChainV2ImplementationError(
                f"implementation record differs: {field_name}"
            )
    observed_digest = record.get("implementation_sha256")
    reduced = dict(record)
    reduced.pop("implementation_sha256", None)
    expected_digest = "sha256:" + hashlib.sha256(
        json.dumps(
            reduced,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    if observed_digest != expected_digest:
        raise PersistentEvidenceChainV2ImplementationError(
            "implementation semantic digest differs"
        )

def _verify_static_chain(root: Path) -> PersistentEvidenceChainV2:
    chain_path = root / CHAIN_RECORD_RELATIVE
    receipt_path = root / POST_MERGE_RECEIPT_RELATIVE
    registry_path = root / REGISTRY_RELATIVE
    source_registry_path = root / SOURCE_REGISTRY_RELATIVE
    chain = load_persistent_evidence_chain_v2(chain_path)
    load_post_merge_validation_receipt(receipt_path)
    if chain.post_merge_validation_receipt_sha256 != sha256_bytes(
        receipt_path.read_bytes()
    ):
        raise PersistentEvidenceChainV2ImplementationError(
            "post-merge receipt identity differs"
        )
    _verify_registry(registry_path, registry_path.parent)
    _verify_registry(source_registry_path, root)
    return chain


def _verify_registry(registry: Path, base: Path) -> None:
    if not registry.is_file() or registry.is_symlink():
        raise PersistentEvidenceChainV2ImplementationError(
            f"frozen registry is absent or invalid: {registry}"
        )
    for line in registry.read_text(
        encoding="utf-8",
        errors="strict",
    ).splitlines():
        digest, relative = line.split("  ", 1)
        target = base / relative
        if not target.is_file() or target.is_symlink():
            raise PersistentEvidenceChainV2ImplementationError(
                f"frozen registry target is absent or invalid: {target}"
            )
        if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            raise PersistentEvidenceChainV2ImplementationError(
                f"frozen registry target digest differs: {target}"
            )


def _target(root: Path, relative: Path) -> Path:
    if relative.is_absolute() or ".." in relative.parts:
        raise PersistentEvidenceChainV2ImplementationError(
            "persistent target path is not repository-relative"
        )
    target = root.joinpath(relative)
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise PersistentEvidenceChainV2ImplementationError(
            "persistent target escapes project root"
        ) from exc
    _require_existing_directory_chain(root, target.parent)
    return target


def _require_existing_directory_chain(root: Path, directory: Path) -> None:
    try:
        relative = directory.relative_to(root)
    except ValueError as exc:
        raise PersistentEvidenceChainV2ImplementationError(
            "persistent target parent escapes project root"
        ) from exc
    current = root
    for part in relative.parts:
        current = current / part
        try:
            metadata = current.lstat()
        except FileNotFoundError as exc:
            raise PersistentEvidenceChainV2ImplementationError(
                f"persistent target parent is absent: {current}"
            ) from exc
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise PersistentEvidenceChainV2ImplementationError(
                f"persistent target parent is not a real directory: {current}"
            )


def _require_absent(path: Path, label: str) -> None:
    if _lexists(path):
        raise PersistentEvidenceChainV2ImplementationError(
            f"{label} already exists: {path}"
        )


def _atomic_write_once(
    root: Path,
    target: Path,
    payload: bytes,
) -> PersistentWriteResult:
    if not payload or not payload.endswith(b"\n"):
        raise PersistentEvidenceChainV2ImplementationError(
            "persistent JSON payload is empty or non-canonical"
        )
    _require_json_object(payload)
    _target(root, target.relative_to(root))
    _require_absent(target, "atomic persistent target")

    temporary = target.parent / (
        f".{target.name}.tmp-{os.getpid()}-{secrets.token_hex(16)}"
    )
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor: int | None = None
    linked = False
    try:
        descriptor = os.open(temporary, flags, 0o600)
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise PersistentEvidenceChainV2ImplementationError(
                    "persistent write made no progress"
                )
            view = view[written:]
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = None
        try:
            os.link(temporary, target, follow_symlinks=False)
        except FileExistsError as exc:
            raise PersistentEvidenceChainV2ImplementationError(
                f"atomic persistent target already exists: {target}"
            ) from exc
        linked = True
        _fsync_directory(target.parent)
        result = _verify_exact_file(root, target, payload)
    except OSError as exc:
        raise PersistentEvidenceChainV2ImplementationError(
            f"persistent atomic write failed: {target}"
        ) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if _lexists(temporary):
            temporary.unlink()
            _fsync_directory(temporary.parent)
    if not linked:
        raise PersistentEvidenceChainV2ImplementationError(
            "persistent atomic target was not linked"
        )
    return result


def _verify_exact_file(
    root: Path,
    target: Path,
    expected: bytes,
) -> PersistentWriteResult:
    _target(root, target.relative_to(root))
    try:
        metadata = target.lstat()
    except FileNotFoundError as exc:
        raise PersistentEvidenceChainV2ImplementationError(
            f"persistent artifact is absent: {target}"
        ) from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise PersistentEvidenceChainV2ImplementationError(
            f"persistent artifact is not a regular file: {target}"
        )
    observed = target.read_bytes()
    if observed != expected:
        raise PersistentEvidenceChainV2ImplementationError(
            f"persistent artifact bytes differ: {target}"
        )
    mode = stat.S_IMODE(metadata.st_mode)
    if mode != 0o600:
        raise PersistentEvidenceChainV2ImplementationError(
            f"persistent artifact mode differs: {target}"
        )
    digest = "sha256:" + hashlib.sha256(observed).hexdigest()
    result = PersistentWriteResult(
        relative_path=target.relative_to(root).as_posix(),
        byte_count=len(observed),
        sha256=digest,
        mode=mode,
    )
    result.require()
    return result


def _require_json_object(payload: bytes) -> None:
    try:
        value = json.loads(payload.decode("utf-8", errors="strict"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise PersistentEvidenceChainV2ImplementationError(
            "persistent payload is not valid UTF-8 JSON"
        ) from exc
    if not isinstance(value, dict):
        raise PersistentEvidenceChainV2ImplementationError(
            "persistent payload JSON root differs"
        )


def _fsync_directory(directory: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    descriptor = os.open(directory, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _lexists(path: Path) -> bool:
    return os.path.lexists(path)
