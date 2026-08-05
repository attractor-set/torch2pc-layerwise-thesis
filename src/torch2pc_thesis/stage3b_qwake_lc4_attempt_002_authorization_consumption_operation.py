"""Fail-closed attempt-002 authorization-consumption operation contract.

This module is import-effect free.  It owns no process spawner, Docker call,
runtime callsite, persistent writer, or production invocation.  The operation
entrypoint validates a post-commit admission and delegates exactly once to an
explicitly supplied transition callable.  Authoring this module does not
consume authorization or start attempt 002.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final, Protocol

OPERATION_ID: Final = (
    "stage3b-qwake-lc4-e-attempt-002-authorization-consumption-operation-v1"
)
OPERATION_STATUS: Final = (
    "authorization_consumption_operation_authored_"
    "post_commit_verification_required_invocation_closed"
)
OPERATION_ENTRYPOINT: Final = (
    "execute_attempt_002_authorization_consumption_operation_once"
)
EXPECTED_AUTHORING_BASE_COMMIT: Final = (
    "fbc73df11779c987ae07e823f124130efd696da4"
)
EXPECTED_TORCH2PC_COMMIT: Final = (
    "b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4"
)
EXPECTED_AUTHORIZATION_SHA256: Final = (
    "sha256:772ebf4a1d142a93e7375a1a2832992f97ab81d8a00c52b87892225afcf1571c"
)
EXPECTED_HOST_INVOCATION_CHAIN_STATE_SHA256: Final = (
    "sha256:5be02c44c300fbbe1f3d289792cbe2e13aa0dd84fbcbe59ee64816ad9350f530"
)
EXPECTED_SCOPE_RECORD_SHA256: Final = (
    "sha256:70b46684eb6d77f2e41d331c671a27efe91b50d449059d80a981c44415e075c3"
)
ATTEMPT_002_OUTPUT_ROOT: Final = Path(
    "results/stage-3/qwake-lc4-runtime-validation-v1-attempt-002"
)
ATTEMPT_002_LEASE_V1_RELATIVE: Final = Path(
    f"{ATTEMPT_002_OUTPUT_ROOT.as_posix()}.execution-lease.json"
)
ATTEMPT_002_LEASE_V2_RELATIVE: Final = Path(
    f"{ATTEMPT_002_OUTPUT_ROOT.as_posix()}.execution-lease-v2.json"
)
ATTEMPT_002_DURABLE_OUTCOME_RELATIVE: Final = Path(
    f"{ATTEMPT_002_OUTPUT_ROOT.as_posix()}.host-outcome.json"
)
FORBIDDEN_PREEXISTING_EFFECT_PATHS: Final = (
    ATTEMPT_002_OUTPUT_ROOT,
    ATTEMPT_002_LEASE_V1_RELATIVE,
    ATTEMPT_002_LEASE_V2_RELATIVE,
    ATTEMPT_002_DURABLE_OUTCOME_RELATIVE,
)
_SHA256_RE: Final = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT_RE: Final = re.compile(r"^[0-9a-f]{40}$")
_UTC_RE: Final = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T"
    r"[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
)

__all__ = [
    "Attempt002AuthorizationConsumptionClaim",
    "Attempt002AuthorizationConsumptionOperationAdmission",
    "Attempt002AuthorizationConsumptionOperationError",
    "Attempt002AuthorizationConsumptionOperationResult",
    "Attempt002DelegatedTransition",
    "Attempt002DelegatedTransitionResult",
    "EXPECTED_AUTHORIZATION_SHA256",
    "EXPECTED_HOST_INVOCATION_CHAIN_STATE_SHA256",
    "EXPECTED_SCOPE_RECORD_SHA256",
    "EXPECTED_TORCH2PC_COMMIT",
    "FORBIDDEN_PREEXISTING_EFFECT_PATHS",
    "OPERATION_ENTRYPOINT",
    "OPERATION_ID",
    "OPERATION_STATUS",
    "build_attempt_002_authorization_consumption_operation_admission",
    "build_attempt_002_authorization_consumption_claim",
    "canonical_json",
    "execute_attempt_002_authorization_consumption_operation_once",
    "sha256_object",
]


class Attempt002AuthorizationConsumptionOperationError(RuntimeError):
    """Raised when the operation contract fails closed."""


def canonical_json(value: object) -> str:
    """Return deterministic UTF-8 JSON text."""

    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    )


def sha256_object(value: object) -> str:
    """Hash a canonical JSON value."""

    return "sha256:" + hashlib.sha256(
        canonical_json(value).encode("utf-8")
    ).hexdigest()


def _require_sha256(value: str, field: str) -> None:
    if _SHA256_RE.fullmatch(value) is None:
        raise Attempt002AuthorizationConsumptionOperationError(
            f"{field} is not an exact sha256 identity"
        )


def _require_commit(value: str, field: str) -> None:
    if _COMMIT_RE.fullmatch(value) is None:
        raise Attempt002AuthorizationConsumptionOperationError(
            f"{field} is not an exact commit identity"
        )


@dataclass(frozen=True)
class Attempt002AuthorizationConsumptionClaim:
    """Immutable claim supplied to the one delegated transition."""

    schema_version: int
    operation_id: str
    operation_implementation_commit: str
    authorization_sha256: str
    host_invocation_chain_state_sha256: str
    claimed_at_utc: str
    claim_sha256: str

    def payload(self) -> Mapping[str, object]:
        """Return the claim body without its self-hash."""

        value = asdict(self)
        value.pop("claim_sha256")
        return value

    def require(self) -> None:
        """Validate the exact claim identity and canonical self-hash."""

        _require_commit(
            self.operation_implementation_commit,
            "operation_implementation_commit",
        )
        _require_sha256(self.authorization_sha256, "authorization_sha256")
        _require_sha256(
            self.host_invocation_chain_state_sha256,
            "host_invocation_chain_state_sha256",
        )
        _require_sha256(self.claim_sha256, "claim_sha256")
        checks = (
            self.schema_version == 1,
            self.operation_id == OPERATION_ID,
            self.authorization_sha256 == EXPECTED_AUTHORIZATION_SHA256,
            self.host_invocation_chain_state_sha256
            == EXPECTED_HOST_INVOCATION_CHAIN_STATE_SHA256,
            _UTC_RE.fullmatch(self.claimed_at_utc) is not None,
            self.claim_sha256 == sha256_object(self.payload()),
        )
        if not all(checks):
            raise Attempt002AuthorizationConsumptionOperationError(
                "attempt-002 authorization-consumption claim differs"
            )


@dataclass(frozen=True)
class Attempt002AuthorizationConsumptionOperationAdmission:
    """Post-commit state required before one operation call."""

    operation_post_commit_verified: bool
    operation_implementation_commit: str
    repository_head: str
    worktree_and_index_clean: bool
    torch2pc_head: str
    authorization_sha256: str
    authorization_effective: bool
    authorization_consumed: bool
    attempt_started: bool
    output_root_present: bool
    lease_v1_present: bool
    lease_v2_present: bool
    durable_outcome_present: bool

    def require(self) -> None:
        """Reject every precondition mismatch before delegation."""

        _require_commit(
            self.operation_implementation_commit,
            "operation_implementation_commit",
        )
        _require_commit(self.repository_head, "repository_head")
        _require_commit(self.torch2pc_head, "torch2pc_head")
        _require_sha256(self.authorization_sha256, "authorization_sha256")
        checks = (
            self.operation_post_commit_verified,
            self.repository_head == self.operation_implementation_commit,
            self.worktree_and_index_clean,
            self.torch2pc_head == EXPECTED_TORCH2PC_COMMIT,
            self.authorization_sha256 == EXPECTED_AUTHORIZATION_SHA256,
            self.authorization_effective,
            not self.authorization_consumed,
            not self.attempt_started,
            not self.output_root_present,
            not self.lease_v1_present,
            not self.lease_v2_present,
            not self.durable_outcome_present,
        )
        if not all(checks):
            raise Attempt002AuthorizationConsumptionOperationError(
                "attempt-002 operation admission differs"
            )


@dataclass(frozen=True)
class Attempt002DelegatedTransitionResult:
    """Required evidence returned by the single delegated transition."""

    claim_sha256: str
    authorization_consumed: bool
    attempt_started: bool
    lease_v1_present: bool
    process_spawned: bool
    runtime_started: bool
    automatic_retry_permitted: bool

    def require(
        self,
        claim: Attempt002AuthorizationConsumptionClaim,
    ) -> None:
        """Validate successful claim-before-spawn transition semantics."""

        _require_sha256(self.claim_sha256, "claim_sha256")
        checks = (
            self.claim_sha256 == claim.claim_sha256,
            self.authorization_consumed,
            self.attempt_started,
            self.lease_v1_present,
            self.process_spawned,
            self.runtime_started,
            not self.automatic_retry_permitted,
        )
        if not all(checks):
            raise Attempt002AuthorizationConsumptionOperationError(
                "delegated transition result differs"
            )


class Attempt002DelegatedTransition(Protocol):
    """Callable boundary implemented only by a later invocation slice."""

    def __call__(
        self,
        root: Path,
        *,
        claim: Attempt002AuthorizationConsumptionClaim,
    ) -> Attempt002DelegatedTransitionResult:
        """Consume the claim and start exactly one attempt."""

        ...


@dataclass(frozen=True)
class Attempt002AuthorizationConsumptionOperationResult:
    """Validated result of one wrapper-level operation call."""

    schema_version: int
    operation_id: str
    claim_sha256: str
    delegated_transition_call_count: int
    authorization_consumed: bool
    attempt_started: bool
    lease_v1_present: bool
    process_spawned: bool
    runtime_started: bool
    automatic_retry_permitted: bool

    def require(self) -> None:
        """Validate one-shot result semantics."""

        _require_sha256(self.claim_sha256, "claim_sha256")
        checks = (
            self.schema_version == 1,
            self.operation_id == OPERATION_ID,
            self.delegated_transition_call_count == 1,
            self.authorization_consumed,
            self.attempt_started,
            self.lease_v1_present,
            self.process_spawned,
            self.runtime_started,
            not self.automatic_retry_permitted,
        )
        if not all(checks):
            raise Attempt002AuthorizationConsumptionOperationError(
                "attempt-002 operation result differs"
            )


def build_attempt_002_authorization_consumption_operation_admission(
    *,
    operation_post_commit_verified: bool,
    operation_implementation_commit: str,
    repository_head: str,
    worktree_and_index_clean: bool,
    torch2pc_head: str,
    authorization_sha256: str,
    authorization_effective: bool,
    authorization_consumed: bool,
    attempt_started: bool,
    output_root_present: bool,
    lease_v1_present: bool,
    lease_v2_present: bool,
    durable_outcome_present: bool,
) -> Attempt002AuthorizationConsumptionOperationAdmission:
    """Build and validate the explicit post-commit admission."""

    admission = Attempt002AuthorizationConsumptionOperationAdmission(
        operation_post_commit_verified=operation_post_commit_verified,
        operation_implementation_commit=operation_implementation_commit,
        repository_head=repository_head,
        worktree_and_index_clean=worktree_and_index_clean,
        torch2pc_head=torch2pc_head,
        authorization_sha256=authorization_sha256,
        authorization_effective=authorization_effective,
        authorization_consumed=authorization_consumed,
        attempt_started=attempt_started,
        output_root_present=output_root_present,
        lease_v1_present=lease_v1_present,
        lease_v2_present=lease_v2_present,
        durable_outcome_present=durable_outcome_present,
    )
    admission.require()
    return admission


def build_attempt_002_authorization_consumption_claim(
    *,
    operation_implementation_commit: str,
    claimed_at_utc: str,
) -> Attempt002AuthorizationConsumptionClaim:
    """Materialize one canonical claim entirely in memory."""

    payload: Mapping[str, object] = {
        "schema_version": 1,
        "operation_id": OPERATION_ID,
        "operation_implementation_commit": operation_implementation_commit,
        "authorization_sha256": EXPECTED_AUTHORIZATION_SHA256,
        "host_invocation_chain_state_sha256": (
            EXPECTED_HOST_INVOCATION_CHAIN_STATE_SHA256
        ),
        "claimed_at_utc": claimed_at_utc,
    }
    claim = Attempt002AuthorizationConsumptionClaim(
        schema_version=1,
        operation_id=OPERATION_ID,
        operation_implementation_commit=operation_implementation_commit,
        authorization_sha256=EXPECTED_AUTHORIZATION_SHA256,
        host_invocation_chain_state_sha256=(
            EXPECTED_HOST_INVOCATION_CHAIN_STATE_SHA256
        ),
        claimed_at_utc=claimed_at_utc,
        claim_sha256=sha256_object(payload),
    )
    claim.require()
    return claim


def _require_effect_boundary_absent(root: Path) -> None:
    for relative in FORBIDDEN_PREEXISTING_EFFECT_PATHS:
        candidate = root / relative
        if candidate.exists() or candidate.is_symlink():
            raise Attempt002AuthorizationConsumptionOperationError(
                f"preexisting attempt-002 effect path: {relative.as_posix()}"
            )


def execute_attempt_002_authorization_consumption_operation_once(
    root: Path,
    *,
    admission: Attempt002AuthorizationConsumptionOperationAdmission,
    claimed_at_utc: str,
    delegated_transition: Attempt002DelegatedTransition,
) -> Attempt002AuthorizationConsumptionOperationResult:
    """Validate, claim in memory, and delegate exactly once.

    This wrapper never retries.  The supplied delegated transition owns the
    future atomic persistence and process-spawn implementation.  No production
    callsite is authored in this slice.
    """

    resolved_root = root.resolve(strict=True)
    git_boundary = resolved_root / ".git"
    if (
        not git_boundary.exists()
        or git_boundary.is_symlink()
        or not git_boundary.is_dir()
    ):
        raise Attempt002AuthorizationConsumptionOperationError(
            "project root is not an exact temporary repository"
        )

    admission.require()
    _require_effect_boundary_absent(resolved_root)
    claim = build_attempt_002_authorization_consumption_claim(
        operation_implementation_commit=(
            admission.operation_implementation_commit
        ),
        claimed_at_utc=claimed_at_utc,
    )

    delegated_result = delegated_transition(resolved_root, claim=claim)
    delegated_result.require(claim)

    result = Attempt002AuthorizationConsumptionOperationResult(
        schema_version=1,
        operation_id=OPERATION_ID,
        claim_sha256=claim.claim_sha256,
        delegated_transition_call_count=1,
        authorization_consumed=delegated_result.authorization_consumed,
        attempt_started=delegated_result.attempt_started,
        lease_v1_present=delegated_result.lease_v1_present,
        process_spawned=delegated_result.process_spawned,
        runtime_started=delegated_result.runtime_started,
        automatic_retry_permitted=False,
    )
    result.require()
    return result
