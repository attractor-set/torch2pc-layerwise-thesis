"""Atomic authorization-consumption transition for QW-LC4-E.

The module authors and implements one fail-closed commit primitive that binds
an independently verified authorization and prepared attempt to the existing
persistent execution-lease-v2 schema.  Importing or verifying this module is
effect free.  The effectful entrypoint is never called by authoring, package
verification, static checks, or repository tests outside temporary copies.
It does not import or call the runtime invoker, inspect an image, materialize a
command, invoke Docker, execute model code, or open local compute.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final, cast

from torch2pc_thesis.stage3b_qwake_lc4_final_engineering_invocation_authorization import (
    AUTHORIZATION_ACTION_PHRASE,
    FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_ID,
    FinalEngineeringInvocationAuthorization,
    load_final_engineering_invocation_authorization,
    validate_final_engineering_invocation_authorization,
    verify_final_engineering_invocation_authorization_sources,
)
from torch2pc_thesis.stage3b_qwake_lc4_final_engineering_invocation_authorization_consumption_attempt import (
    ATTEMPT_ID,
    ConsumptionAttempt,
    load_consumption_attempt,
    validate_consumption_attempt,
    verify_consumption_attempt_sources,
)
from torch2pc_thesis.stage3b_qwake_lc4_persistent_evidence_chain_v2 import (
    CHAIN_RECORD_RELATIVE,
    EXECUTION_LEASE_V2_RELATIVE,
    PERSISTENT_LEASE_V2_OPERATOR_ACKNOWLEDGEMENT,
    PersistentExecutionLeaseV2,
    build_persistent_execution_lease_v2,
    load_persistent_evidence_chain_v2,
    verify_persistent_evidence_chain_v2,
)
from torch2pc_thesis.stage3b_qwake_lc4_persistent_evidence_chain_v2_implementation import (
    PersistentEvidenceChainV2ImplementationError,
    PersistentWriteResult,
    persist_persistent_execution_lease_v2,
    verify_persisted_persistent_execution_lease_v2,
)

ATOMIC_TRANSITION_ID: Final = (
    "stage3b-qwake-lc4-e-final-engineering-invocation-authorization-"
    "consumption-attempt-atomic-transition-v1"
)
ATOMIC_TRANSITION_STATUS: Final = (
    "atomic_transition_authored_merge_required_atomic_action_closed"
)
AUTHORING_BASE_COMMIT: Final = "c9958638a17802cd293c5fa79fd6074c226a85ef"
ATOMIC_SCOPE_ID: Final = (
    "stage3b-qwake-lc4-e-final-engineering-invocation-authorization-"
    "consumption-attempt-atomic-transition-scope-freeze-v1"
)
ATOMIC_SCOPE_PR_NUMBER: Final = 175
ATOMIC_SCOPE_PR_HEAD: Final = "0bd50a21a5f72bd41d5fa7c1590b874a73b0181b"
ATOMIC_SCOPE_MERGE_COMMIT: Final = AUTHORING_BASE_COMMIT
ATOMIC_SCOPE_MERGED_AT_UTC: Final = "2026-08-03T23:58:44Z"
FROZEN_TORCH2PC_COMMIT: Final = (
    "b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4"
)
OPERATOR_IDENTITY_KIND: Final = "local-posix-account"
OPERATOR_IDENTITY: Final = "dzmitry-prychyna"
RUNTIME_ENTRYPOINT_MODULE: Final = (
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_lease_bound_host_invoker_wiring.py"
)
RUNTIME_ENTRYPOINT: Final = "invoke_lease_bound_host_runtime"
ATOMIC_ENTRYPOINT: Final = (
    "execute_final_engineering_invocation_atomic_transition_once"
)
OUTPUT_ROOT: Final = (
    "results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001"
)
EXECUTION_LEASE_V1_RELATIVE: Final = Path(OUTPUT_ROOT + ".execution-lease.json")
DURABLE_HOST_OUTCOME_RELATIVE: Final = Path(OUTPUT_ROOT + ".host-outcome.json")

PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/stage3b-qwake-lc4-e-final-engineering-"
    "invocation-authorization-consumption-attempt-atomic-transition-v1"
)
TRANSITION_RECORD_RELATIVE: Final = PACKAGE_RELATIVE / "transition.json"
SOURCE_REGISTRY_RELATIVE: Final = PACKAGE_RELATIVE / "source-SHA256SUMS"
REGISTRY_RELATIVE: Final = PACKAGE_RELATIVE / "SHA256SUMS"
ATOMIC_SCOPE_PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-"
    "authorization-consumption-attempt-atomic-transition-scope-freeze-v1"
)
ATTEMPT_PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-"
    "authorization-consumption-attempt-v1"
)
AUTHORIZATION_PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-"
    "authorization-v1"
)
MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/stage3b_qwake_lc4_final_engineering_invocation_"
    "authorization_consumption_attempt_atomic_transition.py"
)
VERIFIER_RELATIVE: Final = Path(
    "scripts/verify_stage3b_qwake_lc4_final_engineering_invocation_"
    "authorization_consumption_attempt_atomic_transition.py"
)
TEST_RELATIVE: Final = Path(
    "tests/unit/test_stage3b_qwake_lc4_final_engineering_invocation_"
    "authorization_consumption_attempt_atomic_transition.py"
)
ADR_RU_RELATIVE: Final = Path(
    "docs/decisions/ADR-108-stage3b-qwake-lc4-e-final-engineering-"
    "invocation-authorization-consumption-attempt-atomic-transition-"
    "authoring.md"
)
ADR_EN_RELATIVE: Final = Path(
    "docs/decisions/ADR-108-stage3b-qwake-lc4-e-final-engineering-"
    "invocation-authorization-consumption-attempt-atomic-transition-"
    "authoring_EN.md"
)

_EXPECTED_PACKAGE_FILES: Final = frozenset(
    {"SHA256SUMS", "source-SHA256SUMS", "transition.json"}
)
_EXPECTED_SOURCE_PATHS: Final = frozenset(
    {
        (ATOMIC_SCOPE_PACKAGE_RELATIVE / "scope.json").as_posix(),
        (ATOMIC_SCOPE_PACKAGE_RELATIVE / "SHA256SUMS").as_posix(),
        (ATTEMPT_PACKAGE_RELATIVE / "attempt.json").as_posix(),
        (ATTEMPT_PACKAGE_RELATIVE / "source-SHA256SUMS").as_posix(),
        (ATTEMPT_PACKAGE_RELATIVE / "SHA256SUMS").as_posix(),
        (AUTHORIZATION_PACKAGE_RELATIVE / "authorization.json").as_posix(),
        (AUTHORIZATION_PACKAGE_RELATIVE / "source-SHA256SUMS").as_posix(),
        (AUTHORIZATION_PACKAGE_RELATIVE / "SHA256SUMS").as_posix(),
        "experiments/frozen/stage3b-qwake-lc4-e-persistent-evidence-chain-v2-authoring-v1/chain.json",
        "experiments/frozen/stage3b-qwake-lc4-e-persistent-evidence-chain-v2-authoring-v1/SHA256SUMS",
        "experiments/frozen/stage3b-qwake-lc4-e-persistent-evidence-chain-v2-implementation-v1/implementation.json",
        "experiments/frozen/stage3b-qwake-lc4-e-persistent-evidence-chain-v2-implementation-v1/SHA256SUMS",
        "src/torch2pc_thesis/stage3b_qwake_lc4_persistent_evidence_chain_v2.py",
        "src/torch2pc_thesis/stage3b_qwake_lc4_persistent_evidence_chain_v2_implementation.py",
        RUNTIME_ENTRYPOINT_MODULE,
        MODULE_RELATIVE.as_posix(),
        VERIFIER_RELATIVE.as_posix(),
        TEST_RELATIVE.as_posix(),
        ADR_RU_RELATIVE.as_posix(),
        ADR_EN_RELATIVE.as_posix(),
    }
)
_SHA256_PATTERN: Final = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT_PATTERN: Final = re.compile(r"^[0-9a-f]{40}$")


class AtomicTransitionError(RuntimeError):
    """Raised when the transition fails before a durable commit."""


class AtomicTransitionCommittedError(AtomicTransitionError):
    """Raised when exact committed bytes exist and retry is forbidden."""


class AtomicTransitionUnknownStateError(AtomicTransitionError):
    """Raised for an invalid or ambiguous final lease-v2 object."""


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
        raise AtomicTransitionError(f"{field_name} is not a commit")


def _require_sha256(value: str, field_name: str) -> None:
    if not _SHA256_PATTERN.fullmatch(value):
        raise AtomicTransitionError(f"{field_name} is not a SHA-256 identity")


def _require_utc(value: str, field_name: str) -> None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AtomicTransitionError(f"{field_name} is not UTC") from exc
    if parsed.tzinfo != UTC or not value.endswith("Z"):
        raise AtomicTransitionError(f"{field_name} is not UTC")


@dataclass(frozen=True)
class AtomicTransitionSource:
    atomic_scope_id: str
    atomic_scope_pr_number: int
    atomic_scope_pr_head: str
    atomic_scope_merge_commit: str
    atomic_scope_merged_at_utc: str
    torch2pc_commit: str
    atomic_scope_record_sha256: str
    atomic_scope_registry_sha256: str
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
    persistent_writer_record_sha256: str
    persistent_writer_registry_sha256: str
    persistent_chain_module_sha256: str
    persistent_writer_module_sha256: str
    runtime_entrypoint_module_sha256: str

    def require(self) -> None:
        exact: Mapping[str, object] = {
            "atomic_scope_id": ATOMIC_SCOPE_ID,
            "atomic_scope_pr_number": ATOMIC_SCOPE_PR_NUMBER,
            "atomic_scope_pr_head": ATOMIC_SCOPE_PR_HEAD,
            "atomic_scope_merge_commit": ATOMIC_SCOPE_MERGE_COMMIT,
            "atomic_scope_merged_at_utc": ATOMIC_SCOPE_MERGED_AT_UTC,
            "torch2pc_commit": FROZEN_TORCH2PC_COMMIT,
            "authorization_id": FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_ID,
            "authorization_semantic_sha256": "sha256:629e87c79f03cd50f4b427d66b873802a06b36efe9def502b50232a474c18014",
            "attempt_id": ATTEMPT_ID,
            "attempt_semantic_sha256": "sha256:ad6470c103558426312ff20f60b69dea832f3751afdf290953606366fcfff708",
        }
        for field_name, expected in exact.items():
            if getattr(self, field_name) != expected:
                raise AtomicTransitionError(f"transition source differs: {field_name}")
        _require_commit(self.atomic_scope_pr_head, "atomic_scope_pr_head")
        _require_commit(self.atomic_scope_merge_commit, "atomic_scope_merge_commit")
        _require_utc(self.atomic_scope_merged_at_utc, "atomic_scope_merged_at_utc")
        for field_name, value in asdict(self).items():
            if field_name.endswith("_sha256"):
                _require_sha256(cast(str, value), field_name)


@dataclass(frozen=True)
class AtomicTransitionOperator:
    identity_kind: str
    identity: str
    authorization_action_phrase: str
    persistent_lease_acknowledgement: str
    phrases_are_distinct: bool

    def require(self) -> None:
        if self.identity_kind != OPERATOR_IDENTITY_KIND:
            raise AtomicTransitionError("operator identity kind differs")
        if self.identity != OPERATOR_IDENTITY:
            raise AtomicTransitionError("operator identity differs")
        if self.authorization_action_phrase != AUTHORIZATION_ACTION_PHRASE:
            raise AtomicTransitionError("authorization action phrase differs")
        if (
            self.persistent_lease_acknowledgement
            != PERSISTENT_LEASE_V2_OPERATOR_ACKNOWLEDGEMENT
        ):
            raise AtomicTransitionError("persistent lease acknowledgement differs")
        if not self.phrases_are_distinct:
            raise AtomicTransitionError("operator phrases are not distinct")
        if self.authorization_action_phrase == self.persistent_lease_acknowledgement:
            raise AtomicTransitionError("operator phrases collapse")


@dataclass(frozen=True)
class AtomicTransitionContract:
    atomic_entrypoint: str
    runtime_entrypoint_module: str
    runtime_entrypoint: str
    output_root: str
    execution_lease_v1_relative: str
    execution_lease_v2_relative: str
    durable_host_outcome_relative: str
    attempt_limit: int
    transition_authoring_is_nonexecuting: bool
    effectful_entrypoint_present: bool
    transition_post_merge_verification_required_before_effect: bool
    exact_transition_merge_commit_required: bool
    exact_operator_identity_required: bool
    exact_authorization_action_phrase_required: bool
    exact_persistent_lease_acknowledgement_required: bool
    authorization_and_attempt_records_immutable: bool
    existing_persistent_lease_v2_schema_reused: bool
    existing_hard_link_writer_reused: bool
    exact_persisted_lease_v2_is_single_commit_object: bool
    runtime_invocation_after_and_outside_transition: bool
    runtime_entrypoint_import_forbidden: bool
    invocation_command_materialization_forbidden: bool
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
        expected = AtomicTransitionContract(
            atomic_entrypoint=ATOMIC_ENTRYPOINT,
            runtime_entrypoint_module=RUNTIME_ENTRYPOINT_MODULE,
            runtime_entrypoint=RUNTIME_ENTRYPOINT,
            output_root=OUTPUT_ROOT,
            execution_lease_v1_relative=EXECUTION_LEASE_V1_RELATIVE.as_posix(),
            execution_lease_v2_relative=EXECUTION_LEASE_V2_RELATIVE.as_posix(),
            durable_host_outcome_relative=DURABLE_HOST_OUTCOME_RELATIVE.as_posix(),
            attempt_limit=1,
            transition_authoring_is_nonexecuting=True,
            effectful_entrypoint_present=True,
            transition_post_merge_verification_required_before_effect=True,
            exact_transition_merge_commit_required=True,
            exact_operator_identity_required=True,
            exact_authorization_action_phrase_required=True,
            exact_persistent_lease_acknowledgement_required=True,
            authorization_and_attempt_records_immutable=True,
            existing_persistent_lease_v2_schema_reused=True,
            existing_hard_link_writer_reused=True,
            exact_persisted_lease_v2_is_single_commit_object=True,
            runtime_invocation_after_and_outside_transition=True,
            runtime_entrypoint_import_forbidden=True,
            invocation_command_materialization_forbidden=True,
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
            raise AtomicTransitionError("atomic transition contract differs")


@dataclass(frozen=True)
class AtomicTransitionBoundary:
    authoring_base_commit: str
    atomic_scope_record_modified: bool
    authorization_record_modified: bool
    attempt_record_modified: bool
    transition_module_created: bool
    transition_verifier_created: bool
    transition_tests_created: bool
    transition_record_created: bool
    atomic_action_committed: bool
    authorization_consumed: bool
    attempt_started: bool
    invocation_command_absent: bool
    execution_lease_v1_absent: bool
    execution_lease_v2_absent: bool
    durable_host_outcome_absent: bool
    output_root_absent: bool
    runtime_output_absent: bool
    runtime_invoked: bool
    child_process_created: bool
    docker_run_performed: bool
    image_inspection_performed: bool
    model_code_invoked: bool

    def require(self) -> None:
        if self.authoring_base_commit != AUTHORING_BASE_COMMIT:
            raise AtomicTransitionError("transition boundary base differs")
        expected_true = (
            self.transition_module_created,
            self.transition_verifier_created,
            self.transition_tests_created,
            self.transition_record_created,
            self.invocation_command_absent,
            self.execution_lease_v1_absent,
            self.execution_lease_v2_absent,
            self.durable_host_outcome_absent,
            self.output_root_absent,
            self.runtime_output_absent,
        )
        if not all(expected_true):
            raise AtomicTransitionError("transition authoring boundary differs")
        prohibited = (
            self.atomic_scope_record_modified,
            self.authorization_record_modified,
            self.attempt_record_modified,
            self.atomic_action_committed,
            self.authorization_consumed,
            self.attempt_started,
            self.runtime_invoked,
            self.child_process_created,
            self.docker_run_performed,
            self.image_inspection_performed,
            self.model_code_invoked,
        )
        if any(prohibited):
            raise AtomicTransitionError("transition authoring effect is present")


@dataclass(frozen=True)
class AtomicTransitionGates:
    authorization_post_merge_verified: bool
    authorization_consumed: bool
    final_engineering_invocation_permitted: bool
    final_engineering_invocation_started: bool
    final_engineering_invocation_performed: bool
    consumption_attempt_prepared: bool
    consumption_attempt_post_merge_verified: bool
    atomic_transition_scope_frozen: bool
    atomic_transition_scope_freeze_post_merge_verified: bool
    atomic_transition_authoring_admissible: bool
    atomic_transition_authored: bool
    atomic_transition_record_present: bool
    atomic_transition_post_merge_verified: bool
    atomic_action_permitted: bool
    atomic_action_committed: bool
    consumption_attempt_started: bool
    invocation_command_materialized: bool
    execution_lease_v1_present: bool
    execution_lease_v2_present: bool
    durable_host_outcome_present: bool
    runtime_output_present: bool
    qw5_transition_permitted: bool
    local_compute_execution_open: bool
    test_dataset_access: bool
    publication_permitted: bool

    def require(self) -> None:
        expected = AtomicTransitionGates(
            authorization_post_merge_verified=True,
            authorization_consumed=False,
            final_engineering_invocation_permitted=True,
            final_engineering_invocation_started=False,
            final_engineering_invocation_performed=False,
            consumption_attempt_prepared=True,
            consumption_attempt_post_merge_verified=True,
            atomic_transition_scope_frozen=True,
            atomic_transition_scope_freeze_post_merge_verified=True,
            atomic_transition_authoring_admissible=True,
            atomic_transition_authored=True,
            atomic_transition_record_present=True,
            atomic_transition_post_merge_verified=False,
            atomic_action_permitted=False,
            atomic_action_committed=False,
            consumption_attempt_started=False,
            invocation_command_materialized=False,
            execution_lease_v1_present=False,
            execution_lease_v2_present=False,
            durable_host_outcome_present=False,
            runtime_output_present=False,
            qw5_transition_permitted=False,
            local_compute_execution_open=False,
            test_dataset_access=False,
            publication_permitted=False,
        )
        if self != expected:
            raise AtomicTransitionError("atomic transition gates differ")


@dataclass(frozen=True)
class AtomicTransitionRecord:
    schema_version: int
    transition_id: str
    status: str
    authored_at_utc: str
    authoring_base_commit: str
    source: AtomicTransitionSource
    operator: AtomicTransitionOperator
    contract: AtomicTransitionContract
    boundary: AtomicTransitionBoundary
    gates: AtomicTransitionGates
    transition_sha256: str
    next_slice: str
    post_merge_next_slice: str

    def semantic_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop("transition_sha256")
        return payload

    def canonical_json(self) -> str:
        return canonical_json(asdict(self))

    def require(self) -> None:
        if self.schema_version != 1:
            raise AtomicTransitionError("transition schema version differs")
        if self.transition_id != ATOMIC_TRANSITION_ID:
            raise AtomicTransitionError("transition id differs")
        if self.status != ATOMIC_TRANSITION_STATUS:
            raise AtomicTransitionError("transition status differs")
        _require_utc(self.authored_at_utc, "authored_at_utc")
        _require_commit(self.authoring_base_commit, "authoring_base_commit")
        if self.authoring_base_commit != AUTHORING_BASE_COMMIT:
            raise AtomicTransitionError("transition authoring base differs")
        self.source.require()
        self.operator.require()
        self.contract.require()
        self.boundary.require()
        self.gates.require()
        _require_sha256(self.transition_sha256, "transition_sha256")
        if self.transition_sha256 != sha256_object(self.semantic_payload()):
            raise AtomicTransitionError("transition semantic SHA-256 differs")
        if self.next_slice != (
            "QW-LC4-E-final-engineering-invocation-authorization-consumption-"
            "attempt-atomic-transition-authoring-commit"
        ):
            raise AtomicTransitionError("transition next slice differs")
        if self.post_merge_next_slice != (
            "QW-LC4-E-final-engineering-invocation-authorization-consumption-"
            "attempt-atomic-transition-operation-scope-freeze"
        ):
            raise AtomicTransitionError("transition post-merge next slice differs")


@dataclass(frozen=True)
class AtomicTransitionAdmission:
    transition_post_merge_verified: bool
    implementation_merge_commit: str
    operator_identity_kind: str
    operator_identity: str
    authorization_action_phrase: str
    persistent_lease_acknowledgement: str

    def require(self) -> None:
        if not self.transition_post_merge_verified:
            raise AtomicTransitionError("transition post-merge verification is absent")
        _require_commit(self.implementation_merge_commit, "implementation_merge_commit")
        if self.implementation_merge_commit == AUTHORING_BASE_COMMIT:
            raise AtomicTransitionError("implementation merge commit is not terminal")
        expected = AtomicTransitionOperator(
            identity_kind=self.operator_identity_kind,
            identity=self.operator_identity,
            authorization_action_phrase=self.authorization_action_phrase,
            persistent_lease_acknowledgement=self.persistent_lease_acknowledgement,
            phrases_are_distinct=(
                self.authorization_action_phrase
                != self.persistent_lease_acknowledgement
            ),
        )
        expected.require()


@dataclass(frozen=True)
class AtomicTransitionResult:
    lease: PersistentExecutionLeaseV2
    write_result: PersistentWriteResult
    authorization_consumed: bool
    attempt_started: bool
    execution_lease_v2_present: bool
    atomic_action_committed: bool
    runtime_execution_started: bool
    retry_permitted: bool

    def require(self) -> None:
        if not (
            self.authorization_consumed
            and self.attempt_started
            and self.execution_lease_v2_present
            and self.atomic_action_committed
        ):
            raise AtomicTransitionError("committed transition state differs")
        if self.runtime_execution_started or self.retry_permitted:
            raise AtomicTransitionError("post-commit transition state differs")
        if self.write_result.relative_path != EXECUTION_LEASE_V2_RELATIVE.as_posix():
            raise AtomicTransitionError("committed lease path differs")


def expected_source() -> AtomicTransitionSource:
    return AtomicTransitionSource(
        atomic_scope_id=ATOMIC_SCOPE_ID,
        atomic_scope_pr_number=ATOMIC_SCOPE_PR_NUMBER,
        atomic_scope_pr_head=ATOMIC_SCOPE_PR_HEAD,
        atomic_scope_merge_commit=ATOMIC_SCOPE_MERGE_COMMIT,
        atomic_scope_merged_at_utc=ATOMIC_SCOPE_MERGED_AT_UTC,
        torch2pc_commit=FROZEN_TORCH2PC_COMMIT,
        atomic_scope_record_sha256="sha256:fb6bdaecc2601fc531d8b277138f6bf89e36696c141abe6828aeb8d9385ebecc",
        atomic_scope_registry_sha256="sha256:4346276559fe97ea5f8a86d931f64da84792310d7f4a7e66525c7f65207107f8",
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
        persistent_writer_record_sha256="sha256:fdbad25b58c995ec7b1db7f6d292e3185b93352b4234cee9f6f52a05229c8473",
        persistent_writer_registry_sha256="sha256:ad5e0b84d88a3e830986448ff9ee7ebeb46bdd03a5e85202471e93968a6de24f",
        persistent_chain_module_sha256="sha256:96bc321bdc101038671ca33a693fef553c5528e182512520596cce6e446f8d20",
        persistent_writer_module_sha256="sha256:04df58a67b4743717b80407c9ea931ef96dbcb1c143d5925dfbcf4bc9e8f5e11",
        runtime_entrypoint_module_sha256="sha256:9b665d785caa6550191b90df9795abe1d3ee2b52e52536cfa3aaa12f56e574cd",
    )


def expected_operator() -> AtomicTransitionOperator:
    return AtomicTransitionOperator(
        identity_kind=OPERATOR_IDENTITY_KIND,
        identity=OPERATOR_IDENTITY,
        authorization_action_phrase=AUTHORIZATION_ACTION_PHRASE,
        persistent_lease_acknowledgement=(
            PERSISTENT_LEASE_V2_OPERATOR_ACKNOWLEDGEMENT
        ),
        phrases_are_distinct=True,
    )


def expected_contract() -> AtomicTransitionContract:
    return AtomicTransitionContract(
        atomic_entrypoint=ATOMIC_ENTRYPOINT,
        runtime_entrypoint_module=RUNTIME_ENTRYPOINT_MODULE,
        runtime_entrypoint=RUNTIME_ENTRYPOINT,
        output_root=OUTPUT_ROOT,
        execution_lease_v1_relative=EXECUTION_LEASE_V1_RELATIVE.as_posix(),
        execution_lease_v2_relative=EXECUTION_LEASE_V2_RELATIVE.as_posix(),
        durable_host_outcome_relative=DURABLE_HOST_OUTCOME_RELATIVE.as_posix(),
        attempt_limit=1,
        transition_authoring_is_nonexecuting=True,
        effectful_entrypoint_present=True,
        transition_post_merge_verification_required_before_effect=True,
        exact_transition_merge_commit_required=True,
        exact_operator_identity_required=True,
        exact_authorization_action_phrase_required=True,
        exact_persistent_lease_acknowledgement_required=True,
        authorization_and_attempt_records_immutable=True,
        existing_persistent_lease_v2_schema_reused=True,
        existing_hard_link_writer_reused=True,
        exact_persisted_lease_v2_is_single_commit_object=True,
        runtime_invocation_after_and_outside_transition=True,
        runtime_entrypoint_import_forbidden=True,
        invocation_command_materialization_forbidden=True,
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


def expected_boundary() -> AtomicTransitionBoundary:
    return AtomicTransitionBoundary(
        authoring_base_commit=AUTHORING_BASE_COMMIT,
        atomic_scope_record_modified=False,
        authorization_record_modified=False,
        attempt_record_modified=False,
        transition_module_created=True,
        transition_verifier_created=True,
        transition_tests_created=True,
        transition_record_created=True,
        atomic_action_committed=False,
        authorization_consumed=False,
        attempt_started=False,
        invocation_command_absent=True,
        execution_lease_v1_absent=True,
        execution_lease_v2_absent=True,
        durable_host_outcome_absent=True,
        output_root_absent=True,
        runtime_output_absent=True,
        runtime_invoked=False,
        child_process_created=False,
        docker_run_performed=False,
        image_inspection_performed=False,
        model_code_invoked=False,
    )


def expected_gates() -> AtomicTransitionGates:
    return AtomicTransitionGates(
        authorization_post_merge_verified=True,
        authorization_consumed=False,
        final_engineering_invocation_permitted=True,
        final_engineering_invocation_started=False,
        final_engineering_invocation_performed=False,
        consumption_attempt_prepared=True,
        consumption_attempt_post_merge_verified=True,
        atomic_transition_scope_frozen=True,
        atomic_transition_scope_freeze_post_merge_verified=True,
        atomic_transition_authoring_admissible=True,
        atomic_transition_authored=True,
        atomic_transition_record_present=True,
        atomic_transition_post_merge_verified=False,
        atomic_action_permitted=False,
        atomic_action_committed=False,
        consumption_attempt_started=False,
        invocation_command_materialized=False,
        execution_lease_v1_present=False,
        execution_lease_v2_present=False,
        durable_host_outcome_present=False,
        runtime_output_present=False,
        qw5_transition_permitted=False,
        local_compute_execution_open=False,
        test_dataset_access=False,
        publication_permitted=False,
    )


def build_atomic_transition_record(
    *, authored_at_utc: str, authoring_base_commit: str
) -> AtomicTransitionRecord:
    draft = AtomicTransitionRecord(
        schema_version=1,
        transition_id=ATOMIC_TRANSITION_ID,
        status=ATOMIC_TRANSITION_STATUS,
        authored_at_utc=authored_at_utc,
        authoring_base_commit=authoring_base_commit,
        source=expected_source(),
        operator=expected_operator(),
        contract=expected_contract(),
        boundary=expected_boundary(),
        gates=expected_gates(),
        transition_sha256="sha256:" + "0" * 64,
        next_slice=(
            "QW-LC4-E-final-engineering-invocation-authorization-consumption-"
            "attempt-atomic-transition-authoring-commit"
        ),
        post_merge_next_slice=(
            "QW-LC4-E-final-engineering-invocation-authorization-consumption-"
            "attempt-atomic-transition-operation-scope-freeze"
        ),
    )
    record = replace(
        draft,
        transition_sha256=sha256_object(draft.semantic_payload()),
    )
    record.require()
    return record


def build_atomic_transition_admission(
    *,
    transition_post_merge_verified: bool,
    implementation_merge_commit: str,
    operator_identity_kind: str,
    operator_identity: str,
    authorization_action_phrase: str,
    persistent_lease_acknowledgement: str,
) -> AtomicTransitionAdmission:
    admission = AtomicTransitionAdmission(
        transition_post_merge_verified=transition_post_merge_verified,
        implementation_merge_commit=implementation_merge_commit,
        operator_identity_kind=operator_identity_kind,
        operator_identity=operator_identity,
        authorization_action_phrase=authorization_action_phrase,
        persistent_lease_acknowledgement=persistent_lease_acknowledgement,
    )
    admission.require()
    return admission


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_mapping(path: Path) -> Mapping[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, Mapping):
        raise AtomicTransitionError(f"JSON root is not an object: {path}")
    return cast(Mapping[str, Any], loaded)


def _load_registry(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        entries[relative] = digest
    return entries


def _verify_package(package_root: Path, expected_files: frozenset[str]) -> None:
    if not package_root.is_dir() or package_root.is_symlink():
        raise AtomicTransitionError(f"package is absent or invalid: {package_root}")
    observed = frozenset(path.name for path in package_root.iterdir())
    if observed != expected_files:
        raise AtomicTransitionError(f"package scope differs: {package_root}")
    if any(path.is_dir() or path.is_symlink() for path in package_root.iterdir()):
        raise AtomicTransitionError(f"package contains non-regular entry: {package_root}")
    entries = _load_registry(package_root / "SHA256SUMS")
    if set(entries) != expected_files - {"SHA256SUMS"}:
        raise AtomicTransitionError(f"package registry scope differs: {package_root}")
    for relative, digest in entries.items():
        target = package_root / relative
        if _sha256_file(target) != digest:
            raise AtomicTransitionError(f"package registry digest differs: {target}")


def _verify_source_registry(project_root: Path) -> None:
    entries = _load_registry(project_root / SOURCE_REGISTRY_RELATIVE)
    if set(entries) != _EXPECTED_SOURCE_PATHS:
        raise AtomicTransitionError("transition source registry scope differs")
    for relative, digest in entries.items():
        target = project_root / relative
        if not target.is_file() or target.is_symlink():
            raise AtomicTransitionError(f"transition source is absent: {relative}")
        if _sha256_file(target) != digest:
            raise AtomicTransitionError(f"transition source digest differs: {relative}")


def _verify_atomic_scope_semantics(project_root: Path) -> None:
    scope = _load_mapping(project_root / ATOMIC_SCOPE_PACKAGE_RELATIVE / "scope.json")
    gates = cast(Mapping[str, Any], scope["gates"])
    effects = cast(Mapping[str, Any], scope["effect_boundary"])
    protocol = cast(Mapping[str, Any], scope["atomic_commit_protocol"])
    contract = cast(Mapping[str, Any], scope["atomic_transition_contract"])
    if scope["scope_id"] != ATOMIC_SCOPE_ID:
        raise AtomicTransitionError("atomic scope id differs")
    if scope["post_merge_next_slice"] != (
        "QW-LC4-E-final-engineering-invocation-authorization-consumption-"
        "attempt-atomic-transition-authoring"
    ):
        raise AtomicTransitionError("atomic scope next slice differs")
    if protocol["commit_primitive"] != "hard_link_no_replace":
        raise AtomicTransitionError("atomic scope commit primitive differs")
    if protocol["commit_point"] != (
        "successful_no_replace_hard_link_of_exact_fsynced_lease_v2_bytes_"
        "to_final_path"
    ):
        raise AtomicTransitionError("atomic scope commit point differs")
    if contract["runtime_invocation_is_after_and_outside_atomic_commit"] is not True:
        raise AtomicTransitionError("runtime boundary differs")
    if gates["authorization_consumption_attempt_atomic_transition_scope_frozen"] is not True:
        raise AtomicTransitionError("atomic scope is not frozen")
    for name in (
        "authorization_consumption_attempt_atomic_transition_authored",
        "authorization_consumption_attempt_atomic_action_permitted",
        "authorization_consumption_attempt_atomic_action_committed",
        "authorization_consumption_attempt_started",
        "execution_lease_v2_present",
        "runtime_output_present",
    ):
        if gates[name] is not False:
            raise AtomicTransitionError(f"atomic scope source gate is open: {name}")
    for name in (
        "atomic_transition_module_created",
        "atomic_transition_verifier_created",
        "atomic_transition_tests_created",
        "atomic_transition_record_created",
        "atomic_transition_committed",
        "authorization_consumed",
        "attempt_started",
        "execution_lease_v2_present",
        "runtime_output_present",
        "child_process_created",
        "docker_run_performed",
        "model_code_invoked",
    ):
        if effects[name] is not False:
            raise AtomicTransitionError(f"atomic scope source effect exists: {name}")


def verify_atomic_transition_sources(project_root: Path) -> AtomicTransitionSource:
    """Verify exact authoring inputs without importing the runtime entrypoint."""

    root = project_root.expanduser().resolve()
    _verify_package(root / PACKAGE_RELATIVE, _EXPECTED_PACKAGE_FILES)
    _verify_source_registry(root)
    _verify_package(
        root / ATOMIC_SCOPE_PACKAGE_RELATIVE,
        frozenset({"SHA256SUMS", "scope.json"}),
    )
    _verify_atomic_scope_semantics(root)
    verify_final_engineering_invocation_authorization_sources(root)
    verify_consumption_attempt_sources(root)
    source = expected_source()
    source.require()
    return source


def load_atomic_transition(path: Path) -> AtomicTransitionRecord:
    raw = path.read_text(encoding="utf-8")
    mapping = json.loads(raw)
    if not isinstance(mapping, Mapping):
        raise AtomicTransitionError("transition JSON root is not an object")
    record = AtomicTransitionRecord(
        schema_version=cast(int, mapping["schema_version"]),
        transition_id=cast(str, mapping["transition_id"]),
        status=cast(str, mapping["status"]),
        authored_at_utc=cast(str, mapping["authored_at_utc"]),
        authoring_base_commit=cast(str, mapping["authoring_base_commit"]),
        source=AtomicTransitionSource(**cast(dict[str, Any], mapping["source"])),
        operator=AtomicTransitionOperator(**cast(dict[str, Any], mapping["operator"])),
        contract=AtomicTransitionContract(**cast(dict[str, Any], mapping["contract"])),
        boundary=AtomicTransitionBoundary(**cast(dict[str, Any], mapping["boundary"])),
        gates=AtomicTransitionGates(**cast(dict[str, Any], mapping["gates"])),
        transition_sha256=cast(str, mapping["transition_sha256"]),
        next_slice=cast(str, mapping["next_slice"]),
        post_merge_next_slice=cast(str, mapping["post_merge_next_slice"]),
    )
    if raw != record.canonical_json():
        raise AtomicTransitionError("transition JSON is not canonical")
    record.require()
    return record


def validate_atomic_transition(
    transition: AtomicTransitionRecord,
    source: AtomicTransitionSource,
    project_root: Path,
    *,
    expected_authoring_base_commit: str,
    allow_existing_lease_v2: bool = False,
) -> None:
    transition.require()
    source.require()
    if transition.source != source:
        raise AtomicTransitionError("transition source differs")
    if transition.authoring_base_commit != expected_authoring_base_commit:
        raise AtomicTransitionError("expected authoring base commit differs")
    for relative in (
        Path(OUTPUT_ROOT),
        EXECUTION_LEASE_V1_RELATIVE,
        EXECUTION_LEASE_V2_RELATIVE,
        DURABLE_HOST_OUTCOME_RELATIVE,
    ):
        if allow_existing_lease_v2 and relative == EXECUTION_LEASE_V2_RELATIVE:
            continue
        target = project_root / relative
        if target.exists() or target.is_symlink():
            raise AtomicTransitionError(
                f"runtime boundary path already exists: {relative.as_posix()}"
            )


def _load_and_validate_authorization(
    project_root: Path,
    *,
    allow_existing_lease_v2: bool,
) -> FinalEngineeringInvocationAuthorization:
    source = verify_final_engineering_invocation_authorization_sources(project_root)
    authorization = load_final_engineering_invocation_authorization(
        project_root / AUTHORIZATION_PACKAGE_RELATIVE / "authorization.json"
    )
    if allow_existing_lease_v2:
        authorization.require()
        source.require()
        if authorization.source != source:
            raise AtomicTransitionError("authorization source differs")
        if authorization.authoring_base_commit != (
            "61f190db2fbd4bf0ee8a58cac8b6841fbecc6cdd"
        ):
            raise AtomicTransitionError("authorization authoring base differs")
    else:
        validate_final_engineering_invocation_authorization(
            authorization,
            source,
            project_root,
            expected_authoring_base_commit=(
                "61f190db2fbd4bf0ee8a58cac8b6841fbecc6cdd"
            ),
        )
    return authorization


def _load_and_validate_attempt(
    project_root: Path,
    *,
    allow_existing_lease_v2: bool,
) -> ConsumptionAttempt:
    source = verify_consumption_attempt_sources(project_root)
    attempt = load_consumption_attempt(
        project_root / ATTEMPT_PACKAGE_RELATIVE / "attempt.json"
    )
    if allow_existing_lease_v2:
        attempt.require()
        source.require()
        if attempt.source != source:
            raise AtomicTransitionError("attempt source differs")
        if attempt.authoring_base_commit != (
            "28b4627436244893195231f55f2d0d5fb2d1062e"
        ):
            raise AtomicTransitionError("attempt authoring base differs")
    else:
        validate_consumption_attempt(
            attempt,
            source,
            project_root,
            expected_authoring_base_commit=(
                "28b4627436244893195231f55f2d0d5fb2d1062e"
            ),
        )
    return attempt


def _lexists(path: Path) -> bool:
    return os.path.lexists(path)


def execute_final_engineering_invocation_atomic_transition_once(
    project_root: Path,
    *,
    admission: AtomicTransitionAdmission,
    claimed_at_utc: str,
) -> AtomicTransitionResult:
    """Commit the exact lease-v2 object once, without invoking runtime.

    The caller must provide independently established post-merge admission.
    On success, authorization consumption and attempt start are derived from
    the exact durable lease-v2 bytes.  The function never invokes the runtime.
    """

    admission.require()
    root = project_root.expanduser().resolve()
    source = verify_atomic_transition_sources(root)
    transition = load_atomic_transition(root / TRANSITION_RECORD_RELATIVE)
    validate_atomic_transition(
        transition,
        source,
        root,
        expected_authoring_base_commit=AUTHORING_BASE_COMMIT,
        allow_existing_lease_v2=True,
    )
    _load_and_validate_authorization(
        root, allow_existing_lease_v2=True
    )
    _load_and_validate_attempt(root, allow_existing_lease_v2=True)
    target = root / EXECUTION_LEASE_V2_RELATIVE
    if _lexists(target):
        chain = load_persistent_evidence_chain_v2(root / CHAIN_RECORD_RELATIVE)
    else:
        chain = verify_persistent_evidence_chain_v2(root)
    lease = build_persistent_execution_lease_v2(
        chain,
        claimed_at_utc=claimed_at_utc,
        execution_commit=admission.implementation_merge_commit,
        operator_acknowledgement=admission.persistent_lease_acknowledgement,
        output_root_absent_at_claim=True,
        execution_lease_absent_at_claim=True,
        durable_outcome_absent_at_claim=True,
    )
    if _lexists(target):
        try:
            verify_persisted_persistent_execution_lease_v2(root, chain, lease)
        except PersistentEvidenceChainV2ImplementationError as exc:
            raise AtomicTransitionUnknownStateError(
                "persistent lease v2 is invalid or ambiguous; retry forbidden"
            ) from exc
        raise AtomicTransitionCommittedError(
            "atomic transition is already committed; retry forbidden"
        )
    try:
        write_result = persist_persistent_execution_lease_v2(root, chain, lease)
    except PersistentEvidenceChainV2ImplementationError as exc:
        if _lexists(target):
            try:
                verify_persisted_persistent_execution_lease_v2(root, chain, lease)
            except PersistentEvidenceChainV2ImplementationError as verify_exc:
                raise AtomicTransitionUnknownStateError(
                    "atomic transition outcome is unknown; retry forbidden"
                ) from verify_exc
            raise AtomicTransitionCommittedError(
                "atomic transition committed before failure; retry forbidden"
            ) from exc
        raise AtomicTransitionError(
            "atomic transition failed before durable commit"
        ) from exc
    verified = verify_persisted_persistent_execution_lease_v2(root, chain, lease)
    if verified != write_result:
        raise AtomicTransitionUnknownStateError(
            "persisted lease verification result differs; retry forbidden"
        )
    result = AtomicTransitionResult(
        lease=lease,
        write_result=write_result,
        authorization_consumed=True,
        attempt_started=True,
        execution_lease_v2_present=True,
        atomic_action_committed=True,
        runtime_execution_started=False,
        retry_permitted=False,
    )
    result.require()
    return result
