"""One-shot operator wrapper for the QW-LC4-E atomic transition.

Importing, verifying, or testing this module in the repository is effect free.
The public entrypoint is effectful only when explicitly called after independent
post-merge admission. It validates the immutable operation package, verifies a
closed pre-operation boundary, materializes one UTC claim time, and delegates
exactly once to the already merged atomic-transition entrypoint. It never
imports or invokes the runtime invoker, materializes a shell command, calls
Docker, inspects an image, executes model code, or opens local compute.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from collections.abc import Mapping
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final, cast

from torch2pc_thesis.stage3b_qwake_lc4_final_engineering_invocation_authorization import (
    AUTHORIZATION_ACTION_PHRASE,
    FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_ID,
)
from torch2pc_thesis.stage3b_qwake_lc4_final_engineering_invocation_authorization_consumption_attempt import (
    ATTEMPT_ID,
)
from torch2pc_thesis.stage3b_qwake_lc4_final_engineering_invocation_authorization_consumption_attempt_atomic_transition import (
    ATOMIC_ENTRYPOINT,
    ATOMIC_TRANSITION_ID,
    DURABLE_HOST_OUTCOME_RELATIVE,
    EXECUTION_LEASE_V1_RELATIVE,
    EXECUTION_LEASE_V2_RELATIVE,
    OPERATOR_IDENTITY,
    OPERATOR_IDENTITY_KIND,
    OUTPUT_ROOT,
    AtomicTransitionCommittedError,
    AtomicTransitionError,
    AtomicTransitionResult,
    AtomicTransitionUnknownStateError,
    build_atomic_transition_admission,
    execute_final_engineering_invocation_atomic_transition_once,
    load_atomic_transition,
    verify_atomic_transition_sources,
)
from torch2pc_thesis.stage3b_qwake_lc4_persistent_evidence_chain_v2 import (
    CHAIN_RECORD_RELATIVE,
    PERSISTENT_LEASE_V2_OPERATOR_ACKNOWLEDGEMENT,
    PersistentExecutionLeaseV2,
    load_persistent_evidence_chain_v2,
)

OPERATION_ID: Final = (
    "stage3b-qwake-lc4-e-final-engineering-invocation-authorization-"
    "consumption-attempt-atomic-transition-operation-v1"
)
OPERATION_STATUS: Final = (
    "atomic_transition_operation_authored_merge_required_atomic_action_closed"
)
OPERATION_AUTHORING_BASE_COMMIT: Final = (
    "e33448d10ced2bffd1e48449e6da46b2de938141"
)
OPERATION_SCOPE_ID: Final = (
    "stage3b-qwake-lc4-e-final-engineering-invocation-authorization-"
    "consumption-attempt-atomic-transition-operation-scope-freeze-v1"
)
OPERATION_SCOPE_PR_NUMBER: Final = 177
OPERATION_SCOPE_PR_HEAD: Final = "b3aa449c138285ce065a3a2920fac19f15134207"
OPERATION_SCOPE_MERGE_COMMIT: Final = OPERATION_AUTHORING_BASE_COMMIT
OPERATION_SCOPE_MERGED_AT_UTC: Final = "2026-08-04T02:14:33Z"
TRANSITION_IMPLEMENTATION_MERGE_COMMIT: Final = (
    "3a0cf60e37de80cffdbc397616db6ad437a734e0"
)
FROZEN_TORCH2PC_COMMIT: Final = (
    "b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4"
)
OPERATION_ENTRYPOINT: Final = (
    "execute_final_engineering_invocation_atomic_transition_operation_once"
)
RUNTIME_ENTRYPOINT: Final = "invoke_lease_bound_host_runtime"

PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-"
    "authorization-consumption-attempt-atomic-transition-operation-v1"
)
OPERATION_RECORD_RELATIVE: Final = PACKAGE_RELATIVE / "operation.json"
SOURCE_REGISTRY_RELATIVE: Final = PACKAGE_RELATIVE / "source-SHA256SUMS"
REGISTRY_RELATIVE: Final = PACKAGE_RELATIVE / "SHA256SUMS"
SCOPE_PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-"
    "authorization-consumption-attempt-atomic-transition-operation-"
    "scope-freeze-v1"
)
SCOPE_RECORD_RELATIVE: Final = SCOPE_PACKAGE_RELATIVE / "scope.json"
TRANSITION_PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-"
    "authorization-consumption-attempt-atomic-transition-v1"
)
MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/stage3b_qwake_lc4_final_engineering_invocation_"
    "authorization_consumption_attempt_atomic_transition_operation.py"
)
VERIFIER_RELATIVE: Final = Path(
    "scripts/verify_stage3b_qwake_lc4_final_engineering_invocation_"
    "authorization_consumption_attempt_atomic_transition_operation.py"
)
TEST_RELATIVE: Final = Path(
    "tests/unit/test_stage3b_qwake_lc4_final_engineering_invocation_"
    "authorization_consumption_attempt_atomic_transition_operation.py"
)
ADR_RU_RELATIVE: Final = Path(
    "docs/decisions/ADR-110-stage3b-qwake-lc4-e-final-engineering-"
    "invocation-authorization-consumption-attempt-atomic-transition-"
    "operation-authoring.md"
)
ADR_EN_RELATIVE: Final = Path(
    "docs/decisions/ADR-110-stage3b-qwake-lc4-e-final-engineering-"
    "invocation-authorization-consumption-attempt-atomic-transition-"
    "operation-authoring_EN.md"
)

_EXPECTED_PACKAGE_FILES: Final = frozenset(
    {"SHA256SUMS", "operation.json", "source-SHA256SUMS"}
)
_EXPECTED_SOURCE_PATHS: Final = frozenset(
    {
        SCOPE_RECORD_RELATIVE.as_posix(),
        (SCOPE_PACKAGE_RELATIVE / "SHA256SUMS").as_posix(),
        (TRANSITION_PACKAGE_RELATIVE / "transition.json").as_posix(),
        (TRANSITION_PACKAGE_RELATIVE / "source-SHA256SUMS").as_posix(),
        (TRANSITION_PACKAGE_RELATIVE / "SHA256SUMS").as_posix(),
        "src/torch2pc_thesis/stage3b_qwake_lc4_final_engineering_invocation_authorization_consumption_attempt_atomic_transition.py",
        "scripts/verify_stage3b_qwake_lc4_final_engineering_invocation_authorization_consumption_attempt_atomic_transition.py",
        "tests/unit/test_stage3b_qwake_lc4_final_engineering_invocation_authorization_consumption_attempt_atomic_transition.py",
        "experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-v1/authorization.json",
        "experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-v1/source-SHA256SUMS",
        "experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-v1/SHA256SUMS",
        "experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-v1/attempt.json",
        "experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-v1/source-SHA256SUMS",
        "experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-v1/SHA256SUMS",
        "experiments/frozen/stage3b-qwake-lc4-e-persistent-evidence-chain-v2-authoring-v1/chain.json",
        "experiments/frozen/stage3b-qwake-lc4-e-persistent-evidence-chain-v2-authoring-v1/SHA256SUMS",
        "src/torch2pc_thesis/stage3b_qwake_lc4_persistent_evidence_chain_v2.py",
        "src/torch2pc_thesis/stage3b_qwake_lc4_persistent_evidence_chain_v2_implementation.py",
        "src/torch2pc_thesis/stage3b_qwake_lc4_lease_bound_host_invoker_wiring.py",
        MODULE_RELATIVE.as_posix(),
        VERIFIER_RELATIVE.as_posix(),
        TEST_RELATIVE.as_posix(),
        ADR_RU_RELATIVE.as_posix(),
        ADR_EN_RELATIVE.as_posix(),
    }
)
_COMMIT_PATTERN: Final = re.compile(r"^[0-9a-f]{40}$")
_SHA256_PATTERN: Final = re.compile(r"^sha256:[0-9a-f]{64}$")


class AtomicTransitionOperationError(RuntimeError):
    """Raised when the wrapper fails before a durable transition commit."""


class AtomicTransitionOperationCommittedError(AtomicTransitionOperationError):
    """Raised when an exact committed lease exists and retry is forbidden."""


class AtomicTransitionOperationUnknownStateError(AtomicTransitionOperationError):
    """Raised when a final object or boundary state is ambiguous."""


def canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"


def sha256_object(value: object) -> str:
    return "sha256:" + hashlib.sha256(
        canonical_json(value).encode("utf-8")
    ).hexdigest()


def _require_commit(value: str, field_name: str) -> None:
    if not _COMMIT_PATTERN.fullmatch(value):
        raise AtomicTransitionOperationError(f"{field_name} is not a commit")


def _require_sha256(value: str, field_name: str) -> None:
    if not _SHA256_PATTERN.fullmatch(value):
        raise AtomicTransitionOperationError(f"{field_name} is not a SHA-256 identity")


def _require_utc(value: str, field_name: str) -> None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AtomicTransitionOperationError(f"{field_name} is not UTC") from exc
    if parsed.tzinfo != UTC or not value.endswith("Z"):
        raise AtomicTransitionOperationError(f"{field_name} is not UTC")


def _utc_now_z() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass(frozen=True)
class AtomicTransitionOperationSource:
    scope_id: str
    scope_pr_number: int
    scope_pr_head: str
    scope_merge_commit: str
    scope_merged_at_utc: str
    torch2pc_commit: str
    scope_record_sha256: str
    scope_registry_sha256: str
    transition_id: str
    transition_sha256: str
    transition_implementation_merge_commit: str
    transition_record_sha256: str
    transition_source_registry_sha256: str
    transition_registry_sha256: str
    authorization_id: str
    authorization_semantic_sha256: str
    authorization_record_sha256: str
    authorization_source_registry_sha256: str
    authorization_registry_sha256: str
    attempt_id: str
    attempt_semantic_sha256: str
    attempt_record_sha256: str
    attempt_source_registry_sha256: str
    attempt_registry_sha256: str
    persistent_chain_record_sha256: str
    persistent_chain_registry_sha256: str
    persistent_chain_module_sha256: str
    persistent_writer_module_sha256: str
    runtime_entrypoint_module_sha256: str

    def require(self) -> None:
        exact: Mapping[str, object] = {
            "scope_id": OPERATION_SCOPE_ID,
            "scope_pr_number": OPERATION_SCOPE_PR_NUMBER,
            "scope_pr_head": OPERATION_SCOPE_PR_HEAD,
            "scope_merge_commit": OPERATION_SCOPE_MERGE_COMMIT,
            "scope_merged_at_utc": OPERATION_SCOPE_MERGED_AT_UTC,
            "torch2pc_commit": FROZEN_TORCH2PC_COMMIT,
            "transition_id": ATOMIC_TRANSITION_ID,
            "transition_sha256": (
                "sha256:50cafc898cc251afdba5c62daf3d924eb5b3154ae7cca527db2cb002150f054b"
            ),
            "transition_implementation_merge_commit": (
                TRANSITION_IMPLEMENTATION_MERGE_COMMIT
            ),
            "authorization_id": FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_ID,
            "authorization_semantic_sha256": (
                "sha256:629e87c79f03cd50f4b427d66b873802a06b36efe9def502b50232a474c18014"
            ),
            "attempt_id": ATTEMPT_ID,
            "attempt_semantic_sha256": (
                "sha256:ad6470c103558426312ff20f60b69dea832f3751afdf290953606366fcfff708"
            ),
        }
        for field_name, expected in exact.items():
            if getattr(self, field_name) != expected:
                raise AtomicTransitionOperationError(
                    f"operation source differs: {field_name}"
                )
        _require_utc(self.scope_merged_at_utc, "scope_merged_at_utc")
        for field_name in (
            "scope_record_sha256",
            "scope_registry_sha256",
            "transition_record_sha256",
            "transition_source_registry_sha256",
            "transition_registry_sha256",
            "authorization_record_sha256",
            "authorization_source_registry_sha256",
            "authorization_registry_sha256",
            "attempt_record_sha256",
            "attempt_source_registry_sha256",
            "attempt_registry_sha256",
            "persistent_chain_record_sha256",
            "persistent_chain_registry_sha256",
            "persistent_chain_module_sha256",
            "persistent_writer_module_sha256",
            "runtime_entrypoint_module_sha256",
        ):
            _require_sha256(getattr(self, field_name), field_name)


@dataclass(frozen=True)
class AtomicTransitionOperationContract:
    operation_entrypoint: str
    delegated_transition_entrypoint: str
    transition_implementation_merge_commit: str
    runtime_entrypoint: str
    operation_record_is_nonexecuting: bool
    operation_post_merge_verification_required_before_effect: bool
    operation_implementation_merge_commit_required: bool
    repository_head_must_equal_operation_merge_commit: bool
    clean_worktree_and_index_required: bool
    exact_torch2pc_head_required: bool
    exact_operator_identity_required: bool
    exact_authorization_action_phrase_required: bool
    exact_persistent_lease_acknowledgement_required: bool
    claimed_at_utc_materialized_once_inside_operation: bool
    delegated_transition_call_limit: int
    atomic_action_is_lease_v2_commit: bool
    runtime_invocation_after_and_outside_operation: bool
    runtime_entrypoint_import_forbidden: bool
    invocation_command_materialization_forbidden: bool
    automatic_retry_forbidden: bool
    retry_after_commit_forbidden: bool
    retry_after_unknown_outcome_forbidden: bool
    negative_tests_temporary_repositories_only: bool
    shell_invocation_forbidden: bool
    direct_docker_call_forbidden: bool
    scientific_campaign_authority: bool
    test_dataset_authority: bool
    publication_authority: bool
    qw5_authority: bool

    def require(self) -> None:
        expected = AtomicTransitionOperationContract(
            operation_entrypoint=OPERATION_ENTRYPOINT,
            delegated_transition_entrypoint=ATOMIC_ENTRYPOINT,
            transition_implementation_merge_commit=(
                TRANSITION_IMPLEMENTATION_MERGE_COMMIT
            ),
            runtime_entrypoint=RUNTIME_ENTRYPOINT,
            operation_record_is_nonexecuting=True,
            operation_post_merge_verification_required_before_effect=True,
            operation_implementation_merge_commit_required=True,
            repository_head_must_equal_operation_merge_commit=True,
            clean_worktree_and_index_required=True,
            exact_torch2pc_head_required=True,
            exact_operator_identity_required=True,
            exact_authorization_action_phrase_required=True,
            exact_persistent_lease_acknowledgement_required=True,
            claimed_at_utc_materialized_once_inside_operation=True,
            delegated_transition_call_limit=1,
            atomic_action_is_lease_v2_commit=True,
            runtime_invocation_after_and_outside_operation=True,
            runtime_entrypoint_import_forbidden=True,
            invocation_command_materialization_forbidden=True,
            automatic_retry_forbidden=True,
            retry_after_commit_forbidden=True,
            retry_after_unknown_outcome_forbidden=True,
            negative_tests_temporary_repositories_only=True,
            shell_invocation_forbidden=True,
            direct_docker_call_forbidden=True,
            scientific_campaign_authority=False,
            test_dataset_authority=False,
            publication_authority=False,
            qw5_authority=False,
        )
        if self != expected:
            raise AtomicTransitionOperationError("operation contract differs")


@dataclass(frozen=True)
class AtomicTransitionOperationBoundary:
    authoring_base_commit: str
    scope_record_modified: bool
    transition_record_modified: bool
    authorization_record_modified: bool
    attempt_record_modified: bool
    operation_module_created: bool
    operation_verifier_created: bool
    operation_tests_created: bool
    operation_record_created: bool
    admission_contract_created: bool
    operation_invoked: bool
    delegated_transition_invoked: bool
    persistent_writer_invoked: bool
    authorization_consumed: bool
    attempt_started: bool
    atomic_action_committed: bool
    execution_lease_v2_present: bool
    durable_host_outcome_present: bool
    runtime_invoked: bool
    runtime_output_present: bool
    command_materialized: bool
    child_process_created: bool
    docker_run_performed: bool
    image_inspection_performed: bool
    model_code_invoked: bool

    def require(self) -> None:
        if self.authoring_base_commit != OPERATION_AUTHORING_BASE_COMMIT:
            raise AtomicTransitionOperationError("operation authoring base differs")
        true_fields = {
            "operation_module_created",
            "operation_verifier_created",
            "operation_tests_created",
            "operation_record_created",
            "admission_contract_created",
        }
        for field_name, value in asdict(self).items():
            if field_name == "authoring_base_commit":
                continue
            expected = field_name in true_fields
            if value != expected:
                raise AtomicTransitionOperationError(
                    f"operation boundary differs: {field_name}"
                )


@dataclass(frozen=True)
class AtomicTransitionOperationGates:
    authorization_post_merge_verified: bool
    authorization_consumed: bool
    consumption_attempt_prepared: bool
    consumption_attempt_post_merge_verified: bool
    consumption_attempt_started: bool
    atomic_transition_post_merge_verified: bool
    operation_scope_frozen: bool
    operation_scope_post_merge_verified: bool
    operation_authoring_admissible: bool
    operation_authored: bool
    operation_record_present: bool
    operation_post_merge_verified: bool
    atomic_action_permitted: bool
    atomic_action_committed: bool
    execution_lease_v2_present: bool
    durable_host_outcome_present: bool
    runtime_output_present: bool
    qw5_transition_permitted: bool
    local_compute_execution_open: bool
    test_dataset_access: bool
    publication_permitted: bool

    def require(self) -> None:
        expected = AtomicTransitionOperationGates(
            authorization_post_merge_verified=True,
            authorization_consumed=False,
            consumption_attempt_prepared=True,
            consumption_attempt_post_merge_verified=True,
            consumption_attempt_started=False,
            atomic_transition_post_merge_verified=True,
            operation_scope_frozen=True,
            operation_scope_post_merge_verified=True,
            operation_authoring_admissible=True,
            operation_authored=True,
            operation_record_present=True,
            operation_post_merge_verified=False,
            atomic_action_permitted=False,
            atomic_action_committed=False,
            execution_lease_v2_present=False,
            durable_host_outcome_present=False,
            runtime_output_present=False,
            qw5_transition_permitted=False,
            local_compute_execution_open=False,
            test_dataset_access=False,
            publication_permitted=False,
        )
        if self != expected:
            raise AtomicTransitionOperationError("operation gates differ")


@dataclass(frozen=True)
class AtomicTransitionOperationRecord:
    schema_version: int
    operation_id: str
    status: str
    authored_at_utc: str
    authoring_base_commit: str
    source: AtomicTransitionOperationSource
    contract: AtomicTransitionOperationContract
    boundary: AtomicTransitionOperationBoundary
    gates: AtomicTransitionOperationGates
    operation_sha256: str
    next_slice: str
    post_merge_next_slice: str

    def _payload_without_digest(self) -> Mapping[str, object]:
        payload = asdict(self)
        payload.pop("operation_sha256")
        return cast(Mapping[str, object], payload)

    def canonical_json(self) -> str:
        return canonical_json(asdict(self))

    def require(self) -> None:
        exact: Mapping[str, object] = {
            "schema_version": 1,
            "operation_id": OPERATION_ID,
            "status": OPERATION_STATUS,
            "authoring_base_commit": OPERATION_AUTHORING_BASE_COMMIT,
            "next_slice": (
                "QW-LC4-E-final-engineering-invocation-authorization-"
                "consumption-attempt-atomic-transition-operation-authoring-commit"
            ),
            "post_merge_next_slice": (
                "QW-LC4-E-final-engineering-invocation-authorization-"
                "consumption-attempt-atomic-transition-operation-execution"
            ),
        }
        for field_name, expected in exact.items():
            if getattr(self, field_name) != expected:
                raise AtomicTransitionOperationError(
                    f"operation record differs: {field_name}"
                )
        _require_utc(self.authored_at_utc, "authored_at_utc")
        self.source.require()
        self.contract.require()
        self.boundary.require()
        self.gates.require()
        _require_sha256(self.operation_sha256, "operation_sha256")
        if self.operation_sha256 != sha256_object(self._payload_without_digest()):
            raise AtomicTransitionOperationError("operation semantic SHA-256 differs")


@dataclass(frozen=True)
class AtomicTransitionOperationAdmission:
    operation_post_merge_verified: bool
    operation_implementation_merge_commit: str
    repository_head: str
    worktree_and_index_clean: bool
    torch2pc_head: str
    operator_identity_kind: str
    operator_identity: str
    authorization_action_phrase: str
    persistent_lease_acknowledgement: str

    def require(self) -> None:
        if not self.operation_post_merge_verified:
            raise AtomicTransitionOperationError(
                "operation post-merge verification is absent"
            )
        _require_commit(
            self.operation_implementation_merge_commit,
            "operation_implementation_merge_commit",
        )
        if self.operation_implementation_merge_commit == OPERATION_AUTHORING_BASE_COMMIT:
            raise AtomicTransitionOperationError(
                "operation implementation merge commit is not terminal"
            )
        if self.repository_head != self.operation_implementation_merge_commit:
            raise AtomicTransitionOperationError("repository head differs")
        if not self.worktree_and_index_clean:
            raise AtomicTransitionOperationError("worktree or index is not clean")
        if self.torch2pc_head != FROZEN_TORCH2PC_COMMIT:
            raise AtomicTransitionOperationError("Torch2PC head differs")
        exact = {
            "operator_identity_kind": OPERATOR_IDENTITY_KIND,
            "operator_identity": OPERATOR_IDENTITY,
            "authorization_action_phrase": AUTHORIZATION_ACTION_PHRASE,
            "persistent_lease_acknowledgement": (
                PERSISTENT_LEASE_V2_OPERATOR_ACKNOWLEDGEMENT
            ),
        }
        for field_name, expected in exact.items():
            if getattr(self, field_name) != expected:
                raise AtomicTransitionOperationError(
                    f"operation admission differs: {field_name}"
                )
        if self.authorization_action_phrase == self.persistent_lease_acknowledgement:
            raise AtomicTransitionOperationError("operator phrases are not distinct")


@dataclass(frozen=True)
class AtomicTransitionOperationResult:
    claimed_at_utc: str
    transition_result: AtomicTransitionResult
    delegated_transition_call_count: int
    runtime_execution_started: bool
    retry_permitted: bool

    def require(self) -> None:
        _require_utc(self.claimed_at_utc, "claimed_at_utc")
        self.transition_result.require()
        if self.delegated_transition_call_count != 1:
            raise AtomicTransitionOperationError("delegated call count differs")
        if self.runtime_execution_started or self.retry_permitted:
            raise AtomicTransitionOperationError("operation result boundary differs")


def expected_source() -> AtomicTransitionOperationSource:
    return AtomicTransitionOperationSource(
        scope_id=OPERATION_SCOPE_ID,
        scope_pr_number=OPERATION_SCOPE_PR_NUMBER,
        scope_pr_head=OPERATION_SCOPE_PR_HEAD,
        scope_merge_commit=OPERATION_SCOPE_MERGE_COMMIT,
        scope_merged_at_utc=OPERATION_SCOPE_MERGED_AT_UTC,
        torch2pc_commit=FROZEN_TORCH2PC_COMMIT,
        scope_record_sha256="sha256:294a6930aa9187c4751e0566eeeec8298fc5b281cae1a3999c9c03655bd1e139",
        scope_registry_sha256="sha256:ad1a331dbdc3e67c9d75867e9946533ff306a5cbcdd36f23b2123f61318476a7",
        transition_id=ATOMIC_TRANSITION_ID,
        transition_sha256="sha256:50cafc898cc251afdba5c62daf3d924eb5b3154ae7cca527db2cb002150f054b",
        transition_implementation_merge_commit=TRANSITION_IMPLEMENTATION_MERGE_COMMIT,
        transition_record_sha256="sha256:e01f0dc89ccb616a484788e43cc75e225773a0de89d5705913c89dc9896430eb",
        transition_source_registry_sha256="sha256:330cc3ae00dfcc14b0d5a41a1a3bb4fc53f201606410933d0c9f7060663cf310",
        transition_registry_sha256="sha256:27ec798a00e8b398ea7b7555ac474b7f268579c3f4b8cc561b0d694bcb506c20",
        authorization_id=FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_ID,
        authorization_semantic_sha256="sha256:629e87c79f03cd50f4b427d66b873802a06b36efe9def502b50232a474c18014",
        authorization_record_sha256="sha256:33323d40daf40c39dc1d558fba5439f855c573409415504e951de41181db6a09",
        authorization_source_registry_sha256="sha256:cf42cd926b6db1f3b40167ed3b6cf2f8e5ca5a22564330125f6001bf37d6eab7",
        authorization_registry_sha256="sha256:94a358ea67f46fe9559a09e7b917bed101d99c03eee269b5a86e8de0e039c760",
        attempt_id=ATTEMPT_ID,
        attempt_semantic_sha256="sha256:ad6470c103558426312ff20f60b69dea832f3751afdf290953606366fcfff708",
        attempt_record_sha256="sha256:f03927b0cddba8e6ca41eede15ae28fd59f7823ac7892de10ab77bb339fbef87",
        attempt_source_registry_sha256="sha256:7715decb3d661c971589becba1c5933f686b9d4740fddc94ab5dd444fba9c937",
        attempt_registry_sha256="sha256:05d99847f68a4a3da7308f36f40ce61cf006c0a85ee9430d7beba34865eb314e",
        persistent_chain_record_sha256="sha256:aaacdf8d105b6ce186a84df82b8d5298f3601339cdfaedd70746632d52026dc4",
        persistent_chain_registry_sha256="sha256:e24c9dad3c7dfd632b9d0982657e69b8b04a1af07f7fb4579430c26036cb444e",
        persistent_chain_module_sha256="sha256:96bc321bdc101038671ca33a693fef553c5528e182512520596cce6e446f8d20",
        persistent_writer_module_sha256="sha256:04df58a67b4743717b80407c9ea931ef96dbcb1c143d5925dfbcf4bc9e8f5e11",
        runtime_entrypoint_module_sha256="sha256:9b665d785caa6550191b90df9795abe1d3ee2b52e52536cfa3aaa12f56e574cd",
    )


def expected_contract() -> AtomicTransitionOperationContract:
    return AtomicTransitionOperationContract(
        operation_entrypoint=OPERATION_ENTRYPOINT,
        delegated_transition_entrypoint=ATOMIC_ENTRYPOINT,
        transition_implementation_merge_commit=TRANSITION_IMPLEMENTATION_MERGE_COMMIT,
        runtime_entrypoint=RUNTIME_ENTRYPOINT,
        operation_record_is_nonexecuting=True,
        operation_post_merge_verification_required_before_effect=True,
        operation_implementation_merge_commit_required=True,
        repository_head_must_equal_operation_merge_commit=True,
        clean_worktree_and_index_required=True,
        exact_torch2pc_head_required=True,
        exact_operator_identity_required=True,
        exact_authorization_action_phrase_required=True,
        exact_persistent_lease_acknowledgement_required=True,
        claimed_at_utc_materialized_once_inside_operation=True,
        delegated_transition_call_limit=1,
        atomic_action_is_lease_v2_commit=True,
        runtime_invocation_after_and_outside_operation=True,
        runtime_entrypoint_import_forbidden=True,
        invocation_command_materialization_forbidden=True,
        automatic_retry_forbidden=True,
        retry_after_commit_forbidden=True,
        retry_after_unknown_outcome_forbidden=True,
        negative_tests_temporary_repositories_only=True,
        shell_invocation_forbidden=True,
        direct_docker_call_forbidden=True,
        scientific_campaign_authority=False,
        test_dataset_authority=False,
        publication_authority=False,
        qw5_authority=False,
    )


def expected_boundary() -> AtomicTransitionOperationBoundary:
    return AtomicTransitionOperationBoundary(
        authoring_base_commit=OPERATION_AUTHORING_BASE_COMMIT,
        scope_record_modified=False,
        transition_record_modified=False,
        authorization_record_modified=False,
        attempt_record_modified=False,
        operation_module_created=True,
        operation_verifier_created=True,
        operation_tests_created=True,
        operation_record_created=True,
        admission_contract_created=True,
        operation_invoked=False,
        delegated_transition_invoked=False,
        persistent_writer_invoked=False,
        authorization_consumed=False,
        attempt_started=False,
        atomic_action_committed=False,
        execution_lease_v2_present=False,
        durable_host_outcome_present=False,
        runtime_invoked=False,
        runtime_output_present=False,
        command_materialized=False,
        child_process_created=False,
        docker_run_performed=False,
        image_inspection_performed=False,
        model_code_invoked=False,
    )


def expected_gates() -> AtomicTransitionOperationGates:
    return AtomicTransitionOperationGates(
        authorization_post_merge_verified=True,
        authorization_consumed=False,
        consumption_attempt_prepared=True,
        consumption_attempt_post_merge_verified=True,
        consumption_attempt_started=False,
        atomic_transition_post_merge_verified=True,
        operation_scope_frozen=True,
        operation_scope_post_merge_verified=True,
        operation_authoring_admissible=True,
        operation_authored=True,
        operation_record_present=True,
        operation_post_merge_verified=False,
        atomic_action_permitted=False,
        atomic_action_committed=False,
        execution_lease_v2_present=False,
        durable_host_outcome_present=False,
        runtime_output_present=False,
        qw5_transition_permitted=False,
        local_compute_execution_open=False,
        test_dataset_access=False,
        publication_permitted=False,
    )


def build_atomic_transition_operation_record(
    *, authored_at_utc: str, authoring_base_commit: str
) -> AtomicTransitionOperationRecord:
    draft = AtomicTransitionOperationRecord(
        schema_version=1,
        operation_id=OPERATION_ID,
        status=OPERATION_STATUS,
        authored_at_utc=authored_at_utc,
        authoring_base_commit=authoring_base_commit,
        source=expected_source(),
        contract=expected_contract(),
        boundary=expected_boundary(),
        gates=expected_gates(),
        operation_sha256="sha256:" + "0" * 64,
        next_slice=(
            "QW-LC4-E-final-engineering-invocation-authorization-consumption-"
            "attempt-atomic-transition-operation-authoring-commit"
        ),
        post_merge_next_slice=(
            "QW-LC4-E-final-engineering-invocation-authorization-consumption-"
            "attempt-atomic-transition-operation-execution"
        ),
    )
    record = replace(
        draft,
        operation_sha256=sha256_object(draft._payload_without_digest()),
    )
    record.require()
    return record


def build_atomic_transition_operation_admission(
    *,
    operation_post_merge_verified: bool,
    operation_implementation_merge_commit: str,
    repository_head: str,
    worktree_and_index_clean: bool,
    torch2pc_head: str,
    operator_identity_kind: str,
    operator_identity: str,
    authorization_action_phrase: str,
    persistent_lease_acknowledgement: str,
) -> AtomicTransitionOperationAdmission:
    admission = AtomicTransitionOperationAdmission(
        operation_post_merge_verified=operation_post_merge_verified,
        operation_implementation_merge_commit=operation_implementation_merge_commit,
        repository_head=repository_head,
        worktree_and_index_clean=worktree_and_index_clean,
        torch2pc_head=torch2pc_head,
        operator_identity_kind=operator_identity_kind,
        operator_identity=operator_identity,
        authorization_action_phrase=authorization_action_phrase,
        persistent_lease_acknowledgement=persistent_lease_acknowledgement,
    )
    admission.require()
    return admission


def _sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _load_mapping(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise AtomicTransitionOperationError(f"JSON root is not an object: {path}")
    return cast(Mapping[str, Any], value)


def _load_registry(path: Path) -> dict[str, str]:
    registry: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        registry[relative] = digest
    return registry


def _verify_package(package_root: Path, expected_files: frozenset[str]) -> None:
    if not package_root.is_dir() or package_root.is_symlink():
        raise AtomicTransitionOperationError("operation package is not a directory")
    observed = {path.name for path in package_root.iterdir()}
    if observed != expected_files:
        raise AtomicTransitionOperationError("operation package file set differs")
    registry = _load_registry(package_root / "SHA256SUMS")
    if set(registry) != expected_files - {"SHA256SUMS"}:
        raise AtomicTransitionOperationError("operation package registry differs")
    for relative, digest in registry.items():
        if _sha256_file(package_root / relative) != f"sha256:{digest}":
            raise AtomicTransitionOperationError(
                f"operation package digest differs: {relative}"
            )


def _verify_source_registry(project_root: Path) -> None:
    registry = _load_registry(project_root / SOURCE_REGISTRY_RELATIVE)
    if set(registry) != _EXPECTED_SOURCE_PATHS:
        raise AtomicTransitionOperationError("operation source path set differs")
    for relative, digest in registry.items():
        path = project_root / relative
        if not path.is_file() or path.is_symlink():
            raise AtomicTransitionOperationError(
                f"operation source is not a regular file: {relative}"
            )
        if _sha256_file(path) != f"sha256:{digest}":
            raise AtomicTransitionOperationError(
                f"operation source digest differs: {relative}"
            )


def _verify_scope_semantics(project_root: Path) -> None:
    scope = _load_mapping(project_root / SCOPE_RECORD_RELATIVE)
    repository = cast(Mapping[str, Any], scope["repository"])
    inputs = cast(Mapping[str, Any], scope["admissible_inputs"])
    transition = cast(Mapping[str, Any], inputs["transition"])
    invocation = cast(Mapping[str, Any], scope["operation_invocation"])
    contract = cast(Mapping[str, Any], scope["operation_contract"])
    gates = cast(Mapping[str, Any], scope["gates"])
    effects = cast(Mapping[str, Any], scope["effect_boundary"])
    future = cast(Mapping[str, Any], scope["future_operation_authoring_surfaces"])
    exact: Mapping[str, object] = {
        "schema_version": 1,
        "scope_id": OPERATION_SCOPE_ID,
        "status": (
            "atomic_transition_operation_scope_frozen_transition_post_merge_"
            "verified_atomic_action_closed"
        ),
        "post_merge_next_slice": (
            "QW-LC4-E-final-engineering-invocation-authorization-consumption-"
            "attempt-atomic-transition-operation-authoring"
        ),
    }
    for field_name, expected in exact.items():
        if scope[field_name] != expected:
            raise AtomicTransitionOperationError(
                f"operation scope differs: {field_name}"
            )
    if repository["main_commit"] != TRANSITION_IMPLEMENTATION_MERGE_COMMIT:
        raise AtomicTransitionOperationError("scope repository commit differs")
    if transition["post_merge_verified"] is not True:
        raise AtomicTransitionOperationError("transition is not post-merge verified")
    if invocation["entrypoint"] != ATOMIC_ENTRYPOINT:
        raise AtomicTransitionOperationError("scope delegated entrypoint differs")
    if invocation["production_call_count_limit"] != 1:
        raise AtomicTransitionOperationError("scope call limit differs")
    if contract["operation_authoring_required_before_effect"] is not True:
        raise AtomicTransitionOperationError("scope authoring requirement differs")
    if gates["atomic_transition_operation_scope_frozen"] is not True:
        raise AtomicTransitionOperationError("operation scope is not frozen")
    for name in (
        "atomic_transition_operation_authored",
        "atomic_action_permitted",
        "atomic_action_committed",
        "consumption_attempt_started",
        "execution_lease_v2_present",
        "runtime_output_present",
    ):
        if gates[name] is not False:
            raise AtomicTransitionOperationError(f"scope gate is open: {name}")
    for name in (
        "operation_module_created",
        "operation_verifier_created",
        "operation_tests_created",
        "operation_record_created",
        "atomic_transition_entrypoint_invoked",
        "persistent_writer_invoked",
        "authorization_consumed",
        "attempt_started",
        "execution_lease_v2_present",
        "runtime_invoked",
    ):
        if effects[name] is not False:
            raise AtomicTransitionOperationError(f"scope effect exists: {name}")
    if future["future_entrypoint"] != OPERATION_ENTRYPOINT:
        raise AtomicTransitionOperationError("future operation entrypoint differs")


def verify_atomic_transition_operation_sources(
    project_root: Path,
) -> AtomicTransitionOperationSource:
    root = project_root.expanduser().resolve()
    _verify_package(root / PACKAGE_RELATIVE, _EXPECTED_PACKAGE_FILES)
    _verify_source_registry(root)
    _verify_package(
        root / SCOPE_PACKAGE_RELATIVE,
        frozenset({"SHA256SUMS", "scope.json"}),
    )
    _verify_scope_semantics(root)
    transition_source = verify_atomic_transition_sources(root)
    transition = load_atomic_transition(
        root / TRANSITION_PACKAGE_RELATIVE / "transition.json"
    )
    transition.require()
    transition_source.require()
    if transition.source != transition_source:
        raise AtomicTransitionOperationError("transition source differs")
    if transition.authoring_base_commit != (
        "c9958638a17802cd293c5fa79fd6074c226a85ef"
    ):
        raise AtomicTransitionOperationError("transition authoring base differs")
    source = expected_source()
    source.require()
    return source


def load_atomic_transition_operation(
    path: Path,
) -> AtomicTransitionOperationRecord:
    raw = path.read_text(encoding="utf-8")
    mapping = json.loads(raw)
    if not isinstance(mapping, Mapping):
        raise AtomicTransitionOperationError("operation JSON root is not an object")
    record = AtomicTransitionOperationRecord(
        schema_version=cast(int, mapping["schema_version"]),
        operation_id=cast(str, mapping["operation_id"]),
        status=cast(str, mapping["status"]),
        authored_at_utc=cast(str, mapping["authored_at_utc"]),
        authoring_base_commit=cast(str, mapping["authoring_base_commit"]),
        source=AtomicTransitionOperationSource(
            **cast(dict[str, Any], mapping["source"])
        ),
        contract=AtomicTransitionOperationContract(
            **cast(dict[str, Any], mapping["contract"])
        ),
        boundary=AtomicTransitionOperationBoundary(
            **cast(dict[str, Any], mapping["boundary"])
        ),
        gates=AtomicTransitionOperationGates(
            **cast(dict[str, Any], mapping["gates"])
        ),
        operation_sha256=cast(str, mapping["operation_sha256"]),
        next_slice=cast(str, mapping["next_slice"]),
        post_merge_next_slice=cast(str, mapping["post_merge_next_slice"]),
    )
    if raw != record.canonical_json():
        raise AtomicTransitionOperationError("operation JSON is not canonical")
    record.require()
    return record


def validate_atomic_transition_operation(
    operation: AtomicTransitionOperationRecord,
    source: AtomicTransitionOperationSource,
    project_root: Path,
    *,
    expected_authoring_base_commit: str,
    allow_existing_lease_v2: bool = False,
    allow_existing_boundary: bool = False,
) -> None:
    operation.require()
    source.require()
    if operation.source != source:
        raise AtomicTransitionOperationError("operation source differs")
    if operation.authoring_base_commit != expected_authoring_base_commit:
        raise AtomicTransitionOperationError("expected operation base differs")
    for relative in (
        Path(OUTPUT_ROOT),
        EXECUTION_LEASE_V1_RELATIVE,
        EXECUTION_LEASE_V2_RELATIVE,
        DURABLE_HOST_OUTCOME_RELATIVE,
    ):
        if allow_existing_boundary:
            continue
        if allow_existing_lease_v2 and relative == EXECUTION_LEASE_V2_RELATIVE:
            continue
        target = project_root / relative
        if os.path.lexists(target):
            raise AtomicTransitionOperationError(
                f"operation boundary path already exists: {relative.as_posix()}"
            )


def _classify_existing_boundary(root: Path) -> None:
    for relative in (
        Path(OUTPUT_ROOT),
        EXECUTION_LEASE_V1_RELATIVE,
        DURABLE_HOST_OUTCOME_RELATIVE,
    ):
        if os.path.lexists(root / relative):
            raise AtomicTransitionOperationUnknownStateError(
                f"operation boundary is ambiguous: {relative.as_posix()}; retry forbidden"
            )
    target = root / EXECUTION_LEASE_V2_RELATIVE
    if not os.path.lexists(target):
        return
    try:
        info = target.lstat()
        if target.is_symlink() or not stat.S_ISREG(info.st_mode):
            raise AtomicTransitionOperationError("lease v2 is not a regular file")
        if stat.S_IMODE(info.st_mode) != 0o600:
            raise AtomicTransitionOperationError("lease v2 mode differs")
        raw = target.read_text(encoding="utf-8")
        mapping = json.loads(raw)
        if not isinstance(mapping, Mapping):
            raise AtomicTransitionOperationError("lease v2 root differs")
        chain = load_persistent_evidence_chain_v2(root / CHAIN_RECORD_RELATIVE)
        lease = PersistentExecutionLeaseV2(**cast(dict[str, Any], mapping))
        lease.require(chain)
        if raw != lease.canonical_json():
            raise AtomicTransitionOperationError("lease v2 is not canonical")
        if lease.execution_commit != TRANSITION_IMPLEMENTATION_MERGE_COMMIT:
            raise AtomicTransitionOperationError("lease v2 execution commit differs")
    except Exception as exc:
        raise AtomicTransitionOperationUnknownStateError(
            "persistent lease v2 is invalid or ambiguous; retry forbidden"
        ) from exc
    raise AtomicTransitionOperationCommittedError(
        "atomic transition operation is already committed; retry forbidden"
    )


def execute_final_engineering_invocation_atomic_transition_operation_once(
    project_root: Path,
    *,
    admission: AtomicTransitionOperationAdmission,
) -> AtomicTransitionOperationResult:
    """Commit the authorization-consumption transition once without runtime.

    The caller must independently prove the exact merged operation package,
    clean repository identity, and frozen Torch2PC head. The wrapper obtains
    one claim timestamp only after all source and absence checks and delegates
    exactly once to the merged atomic-transition entrypoint.
    """

    admission.require()
    expanded = project_root.expanduser()
    if expanded.is_symlink():
        raise AtomicTransitionOperationError("project root is symbolic")
    try:
        root = expanded.resolve(strict=True)
    except FileNotFoundError as exc:
        raise AtomicTransitionOperationError("project root does not exist") from exc
    if not root.is_dir():
        raise AtomicTransitionOperationError("project root is not a directory")
    source = verify_atomic_transition_operation_sources(root)
    operation = load_atomic_transition_operation(root / OPERATION_RECORD_RELATIVE)
    validate_atomic_transition_operation(
        operation,
        source,
        root,
        expected_authoring_base_commit=OPERATION_AUTHORING_BASE_COMMIT,
        allow_existing_boundary=True,
    )
    _classify_existing_boundary(root)
    transition_admission = build_atomic_transition_admission(
        transition_post_merge_verified=True,
        implementation_merge_commit=TRANSITION_IMPLEMENTATION_MERGE_COMMIT,
        operator_identity_kind=admission.operator_identity_kind,
        operator_identity=admission.operator_identity,
        authorization_action_phrase=admission.authorization_action_phrase,
        persistent_lease_acknowledgement=(
            admission.persistent_lease_acknowledgement
        ),
    )
    claimed_at_utc = _utc_now_z()
    try:
        transition_result = (
            execute_final_engineering_invocation_atomic_transition_once(
                root,
                admission=transition_admission,
                claimed_at_utc=claimed_at_utc,
            )
        )
    except AtomicTransitionCommittedError as exc:
        raise AtomicTransitionOperationCommittedError(str(exc)) from exc
    except AtomicTransitionUnknownStateError as exc:
        raise AtomicTransitionOperationUnknownStateError(str(exc)) from exc
    except AtomicTransitionError as exc:
        raise AtomicTransitionOperationError(str(exc)) from exc
    result = AtomicTransitionOperationResult(
        claimed_at_utc=claimed_at_utc,
        transition_result=transition_result,
        delegated_transition_call_count=1,
        runtime_execution_started=False,
        retry_permitted=False,
    )
    result.require()
    return result
