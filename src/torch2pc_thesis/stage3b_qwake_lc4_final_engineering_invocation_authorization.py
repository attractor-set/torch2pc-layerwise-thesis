"""Pure fail-closed schema for the final QW-LC4-E one-shot authorization.

The authored record may state that authorization was issued, but effective
invocation authority remains closed until merge and independent post-merge
verification. This module never imports or invokes the runtime entrypoint,
creates a lease, starts a child process, inspects an image, or writes runtime
output.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Final, cast

FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_ID: Final = (
    "stage3b-qwake-lc4-e-final-engineering-invocation-authorization-v1"
)
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_STATUS: Final = (
    "final_engineering_invocation_authorization_issued_merge_required_effective_authority_closed"
)
AUTHORIZATION_SCOPE_ID: Final = (
    "stage3b-qwake-lc4-e-final-engineering-invocation-authorization-"
    "authoring-scope-freeze-v1"
)
AUTHORIZATION_SCOPE_FREEZE_MERGE_COMMIT: Final = (
    "61f190db2fbd4bf0ee8a58cac8b6841fbecc6cdd"
)
AUTHORIZATION_SCOPE_FREEZE_PR_HEAD: Final = (
    "6093a18156036d8aa470c88844b0580cd3926c4e"
)
AUTHORIZATION_SCOPE_FREEZE_PR_NUMBER: Final = 171
AUTHORIZATION_SCOPE_FREEZE_MERGED_AT_UTC: Final = (
    "2026-08-03T17:17:04Z"
)
FROZEN_TORCH2PC_COMMIT: Final = (
    "b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4"
)
AUTHORIZATION_OPERATOR_IDENTITY_KIND: Final = "local-posix-account"
AUTHORIZATION_OPERATOR_IDENTITY: Final = "dzmitry-prychyna"
AUTHORIZATION_ACTION_PHRASE: Final = (
    "AUTHORIZE_QWAKE_LC4_FINAL_ENGINEERING_INVOCATION_ONCE_AFTER_POST_MERGE_VERIFICATION"
)
IMAGE_REPO_DIGEST: Final = (
    "torch2pc-layerwise-thesis@sha256:"
    "7da92b8f77f6dc37d42db832c5613ef6149dc488adc5b66465faa33e48ca021d"
)
RUNTIME_ENTRYPOINT_MODULE: Final = (
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_lease_bound_host_invoker_wiring.py"
)
RUNTIME_ENTRYPOINT: Final = "invoke_lease_bound_host_runtime"
OUTPUT_ROOT: Final = (
    "results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001"
)
EXECUTION_LEASE_V1_RELATIVE: Final = Path(
    OUTPUT_ROOT + ".execution-lease.json"
)
EXECUTION_LEASE_V2_RELATIVE: Final = Path(
    OUTPUT_ROOT + ".execution-lease-v2.json"
)
DURABLE_HOST_OUTCOME_RELATIVE: Final = Path(
    OUTPUT_ROOT + ".host-outcome.json"
)

AUTHORIZATION_SCOPE_PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-final-engineering-invocation-authorization-"
    "authoring-scope-freeze-v1"
)
REPOSITORY_SEAL_PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-final-engineering-invocation-admission-"
    "repository-seal-v1"
)
ADMISSION_PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-final-engineering-invocation-admission-authoring-v1"
)
PERSISTENT_CHAIN_PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-persistent-evidence-chain-v2-implementation-v1"
)
WIRING_PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-lease-bound-host-invoker-wiring-v1"
)
HISTORICAL_ENGINEERING_AUTHORIZATION_PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-authorization-v1"
)
HISTORICAL_ACKNOWLEDGEMENT_AUTHORIZATION_PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-final-execution-acknowledgement-materialization-"
    "invocation-operation-callsite-execution-authorization-v1"
)

_EXPECTED_PACKAGE_FILES: Final[dict[Path, frozenset[str]]] = {
    AUTHORIZATION_SCOPE_PACKAGE_RELATIVE: frozenset(
        {"SHA256SUMS", "scope.json"}
    ),
    REPOSITORY_SEAL_PACKAGE_RELATIVE: frozenset(
        {"SHA256SUMS", "receipt.json"}
    ),
    ADMISSION_PACKAGE_RELATIVE: frozenset(
        {"SHA256SUMS", "admission.json", "source-SHA256SUMS"}
    ),
    PERSISTENT_CHAIN_PACKAGE_RELATIVE: frozenset(
        {
            "SHA256SUMS",
            "authoring-merge-validation.json",
            "implementation.json",
            "source-SHA256SUMS",
        }
    ),
    WIRING_PACKAGE_RELATIVE: frozenset(
        {
            "SHA256SUMS",
            "implementation-merge-validation.json",
            "source-SHA256SUMS",
            "wiring.json",
        }
    ),
    HISTORICAL_ENGINEERING_AUTHORIZATION_PACKAGE_RELATIVE: frozenset(
        {"SHA256SUMS", "authorization.json", "identity.env", "source-SHA256SUMS"}
    ),
    HISTORICAL_ACKNOWLEDGEMENT_AUTHORIZATION_PACKAGE_RELATIVE: frozenset(
        {
            "SHA256SUMS",
            "authorization.json",
            "execution-authoring-merge-validation.json",
            "operation.json",
            "source-SHA256SUMS",
        }
    ),
}

_EXPECTED_FILE_SHA256: Final[dict[Path, str]] = {
    Path("experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-authoring-scope-freeze-v1/SHA256SUMS"): "b1c5b79e150085ff512349e8ca051c673ad72f9255ab7ae933c69b9ea6371c8a",
    Path("experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-authoring-scope-freeze-v1/scope.json"): "9aa30b84dc055a5411e6885c999f47e0f37b10fc413a79d168084efd832da47a",
    Path("experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-admission-repository-seal-v1/SHA256SUMS"): "45b05afa00a9b43b73f08c7d6227f68d5d1c6813e0910cc2a1d7d3e3672cf1d8",
    Path("experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-admission-repository-seal-v1/receipt.json"): "0445b537efc6d8266d6a20b68ba2963090668dac6d280e9b270a0f927b8ff161",
    Path("experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-admission-authoring-v1/SHA256SUMS"): "2c353c053e0968ee87afc0f09da7c2aadb898c9ef80a274206f38650be7ff627",
    Path("experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-admission-authoring-v1/source-SHA256SUMS"): "adfb8f5dc11b6da6614f6842b3e535c68b2eb130f914e58d0c41d302854f67c9",
    Path("experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-admission-authoring-v1/admission.json"): "dfc4bcd7505328bd69d4fd88b79c8ea06caa7c8a0b8871354dc7b7488e999114",
    Path("src/torch2pc_thesis/stage3b_qwake_lc4_final_engineering_invocation_admission.py"): "da8182fe6eb35a6d4030545ae895cc0820cb99f34db2b920813f5f4f8169708c",
    Path("scripts/verify_stage3b_qwake_lc4_final_engineering_invocation_admission.py"): "946059c4022d848978f697027c854cc0b8954e590d1e92a84c03e149b8744cad",
    Path("tests/unit/test_stage3b_qwake_lc4_final_engineering_invocation_admission.py"): "8a6c773d264300d3083e8161340bbd5355c96ee6eb6c4974ff59843deeaba73f",
    Path("experiments/frozen/stage3b-qwake-lc4-e-persistent-evidence-chain-v2-implementation-v1/SHA256SUMS"): "ad5e0b84d88a3e830986448ff9ee7ebeb46bdd03a5e85202471e93968a6de24f",
    Path("experiments/frozen/stage3b-qwake-lc4-e-persistent-evidence-chain-v2-implementation-v1/implementation.json"): "fdbad25b58c995ec7b1db7f6d292e3185b93352b4234cee9f6f52a05229c8473",
    Path("experiments/frozen/stage3b-qwake-lc4-e-lease-bound-host-invoker-wiring-v1/SHA256SUMS"): "89406036c617de7875c01375c67d5b1d317528307353d51975cfb3b67797be94",
    Path("experiments/frozen/stage3b-qwake-lc4-e-lease-bound-host-invoker-wiring-v1/wiring.json"): "60199510764aa4827bfb2deac69675b7d5d79e7209fa8f0aa53ba8d79a5c4ff3",
    Path("src/torch2pc_thesis/stage3b_qwake_lc4_lease_bound_host_invoker_wiring.py"): "9b665d785caa6550191b90df9795abe1d3ee2b52e52536cfa3aaa12f56e574cd",
    Path("experiments/frozen/stage3b-qwake-lc4-e-one-shot-engineering-invocation-authorization-v1/SHA256SUMS"): "9a47f79e9607db98a2c7c224c25cbeee920974d4c339eef4ef82d4f9aa7c8f83",
    Path("experiments/frozen/stage3b-qwake-lc4-e-one-shot-engineering-invocation-authorization-v1/authorization.json"): "e7b58ad04a932b36a0eaea5a276e95c593d4e88e303e05dadbb25eaf3eb5c999",
    Path("experiments/frozen/stage3b-qwake-lc4-e-final-execution-acknowledgement-materialization-invocation-operation-callsite-execution-authorization-v1/SHA256SUMS"): "9253ffea4d576f4b0a8732005dcace67adf1b9ac78c4bbe523ae2017762eec57",
    Path("experiments/frozen/stage3b-qwake-lc4-e-final-execution-acknowledgement-materialization-invocation-operation-callsite-execution-authorization-v1/authorization.json"): "561b864c08be9d4d33985fb94f7882abf77c9c4316cff2a8d1feee9cbf0e23a4",
}

_COMMIT_PATTERN: Final = re.compile(r"^[0-9a-f]{40}$")
_SHA256_PATTERN: Final = re.compile(r"^sha256:[0-9a-f]{64}$")
_UTC_PATTERN: Final = re.compile(
    r"^20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
)

__all__ = [
    "AUTHORIZATION_ACTION_PHRASE",
    "AUTHORIZATION_OPERATOR_IDENTITY",
    "AUTHORIZATION_OPERATOR_IDENTITY_KIND",
    "AUTHORIZATION_SCOPE_FREEZE_MERGE_COMMIT",
    "AUTHORIZATION_SCOPE_FREEZE_MERGED_AT_UTC",
    "AUTHORIZATION_SCOPE_FREEZE_PR_HEAD",
    "AUTHORIZATION_SCOPE_FREEZE_PR_NUMBER",
    "AUTHORIZATION_SCOPE_ID",
    "DURABLE_HOST_OUTCOME_RELATIVE",
    "EXECUTION_LEASE_V1_RELATIVE",
    "EXECUTION_LEASE_V2_RELATIVE",
    "FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_ID",
    "FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_STATUS",
    "FROZEN_TORCH2PC_COMMIT",
    "FinalEngineeringInvocationAuthorization",
    "FinalEngineeringInvocationAuthorizationBoundary",
    "FinalEngineeringInvocationAuthorizationContract",
    "FinalEngineeringInvocationAuthorizationError",
    "FinalEngineeringInvocationAuthorizationGates",
    "FinalEngineeringInvocationAuthorizationOperator",
    "FinalEngineeringInvocationAuthorizationSource",
    "IMAGE_REPO_DIGEST",
    "OUTPUT_ROOT",
    "RUNTIME_ENTRYPOINT",
    "RUNTIME_ENTRYPOINT_MODULE",
    "build_final_engineering_invocation_authorization",
    "canonical_json",
    "load_final_engineering_invocation_authorization",
    "sha256_object",
    "validate_final_engineering_invocation_authorization",
    "verify_final_engineering_invocation_authorization_sources",
]


class FinalEngineeringInvocationAuthorizationError(RuntimeError):
    """Raised when authorization validation cannot remain fail closed."""


def canonical_json(value: object) -> str:
    """Return canonical UTF-8 JSON with one terminal newline."""

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"


def sha256_object(value: object) -> str:
    """Hash canonical JSON without terminal formatting ambiguity."""

    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _require_commit(value: str, field_name: str) -> None:
    if _COMMIT_PATTERN.fullmatch(value) is None:
        raise FinalEngineeringInvocationAuthorizationError(
            f"{field_name} is not a commit"
        )


def _require_sha256(value: str, field_name: str) -> None:
    if _SHA256_PATTERN.fullmatch(value) is None:
        raise FinalEngineeringInvocationAuthorizationError(
            f"{field_name} is not SHA-256"
        )


def _require_utc(value: str, field_name: str) -> None:
    if _UTC_PATTERN.fullmatch(value) is None:
        raise FinalEngineeringInvocationAuthorizationError(
            f"{field_name} is not canonical UTC"
        )


@dataclass(frozen=True)
class FinalEngineeringInvocationAuthorizationSource:
    """Exact immutable source identities for the new authorization."""

    scope_id: str
    scope_freeze_merge_commit: str
    scope_freeze_pr_head: str
    scope_freeze_pr_number: int
    scope_freeze_merged_at_utc: str
    torch2pc_commit: str
    scope_registry_sha256: str
    scope_file_sha256: str
    repository_seal_registry_sha256: str
    repository_seal_receipt_sha256: str
    admission_id: str
    admission_semantic_sha256: str
    admission_registry_sha256: str
    admission_source_registry_sha256: str
    admission_record_sha256: str
    persistent_chain_registry_sha256: str
    persistent_chain_implementation_sha256: str
    wiring_registry_sha256: str
    wiring_record_sha256: str
    runtime_entrypoint_module_sha256: str
    historical_engineering_authorization_registry_sha256: str
    historical_engineering_authorization_record_sha256: str
    historical_acknowledgement_authorization_registry_sha256: str
    historical_acknowledgement_authorization_record_sha256: str

    def require(self) -> None:
        if self != expected_source():
            raise FinalEngineeringInvocationAuthorizationError(
                "authorization source identities differ"
            )


@dataclass(frozen=True)
class FinalEngineeringInvocationAuthorizationOperator:
    """Exact operator identity and separately reserved action phrase."""

    identity_kind: str
    identity: str
    action_phrase: str

    def require(self) -> None:
        if self != expected_operator():
            raise FinalEngineeringInvocationAuthorizationError(
                "authorization operator identity or phrase differs"
            )


@dataclass(frozen=True)
class FinalEngineeringInvocationAuthorizationContract:
    """One-shot authorization contract; effective authority is still closed."""

    image_repo_digest: str
    runtime_entrypoint_module: str
    runtime_entrypoint: str
    output_root: str
    execution_lease_v1_relative: str
    execution_lease_v2_relative: str
    durable_host_outcome_relative: str
    invocation_limit: int
    distinct_new_authorization_required: bool
    exact_operator_identity_required: bool
    separate_operator_action_phrase_required: bool
    authorization_post_merge_verified_before_invocation: bool
    post_merge_verification_required_before_effective_authority: bool
    atomic_consumption_with_attempt_start_and_exclusive_lease_v2: bool
    persistent_lease_v2_required_before_entrypoint: bool
    durable_host_outcome_required_for_every_terminal_class: bool
    historical_engineering_authorization_reuse_forbidden: bool
    acknowledgement_authorization_reuse_forbidden: bool
    retry_after_consumption_forbidden: bool
    retry_after_lease_creation_forbidden: bool
    retry_after_unknown_outcome_forbidden: bool
    shell_invocation_forbidden: bool
    direct_docker_call_forbidden: bool
    direct_lower_host_invoker_call_forbidden: bool
    direct_historical_runtime_operation_call_forbidden: bool
    scientific_campaign_authority: bool
    test_dataset_authority: bool
    publication_authority: bool
    qw5_authority: bool
    verifier_runtime_entrypoint_import_forbidden: bool
    negative_tests_temporary_repositories_only: bool

    def require(self) -> None:
        if self != expected_contract():
            raise FinalEngineeringInvocationAuthorizationError(
                "authorization contract differs"
            )


@dataclass(frozen=True)
class FinalEngineeringInvocationAuthorizationBoundary:
    """Closed repository and runtime boundary at record-authoring time."""

    authoring_base_commit: str
    output_root_absent: bool
    execution_lease_v1_absent: bool
    execution_lease_v2_absent: bool
    durable_host_outcome_absent: bool
    runtime_output_absent: bool
    invocation_command_absent: bool
    image_inspection_performed: bool
    docker_run_performed: bool
    child_process_created: bool
    model_code_invoked: bool
    existing_frozen_package_modified: bool

    def require(self) -> None:
        if self != expected_boundary():
            raise FinalEngineeringInvocationAuthorizationError(
                "authorization boundary differs"
            )


@dataclass(frozen=True)
class FinalEngineeringInvocationAuthorizationGates:
    """Authored and issued record with effective invocation authority closed."""

    final_engineering_invocation_admission_repository_seal_complete: bool
    final_engineering_invocation_authorization_authoring_scope_frozen: bool
    final_engineering_invocation_authorization_authored: bool
    final_engineering_invocation_authorization_record_present: bool
    final_engineering_invocation_authorization_issued: bool
    final_engineering_invocation_authorization_post_merge_verified: bool
    final_engineering_invocation_authorization_consumed: bool
    final_engineering_invocation_permitted: bool
    final_engineering_invocation_started: bool
    final_engineering_invocation_performed: bool
    operator_phrase_reserved: bool
    invocation_command_materialized: bool
    execution_lease_v1_present: bool
    execution_lease_v2_present: bool
    durable_host_outcome_present: bool
    runtime_output_present: bool
    extension_engineering_report_present: bool
    qw_lc4_e_complete: bool
    qw5_transition_permitted: bool
    qw5_scientific_image_freeze_open: bool
    local_compute_execution_open: bool
    test_dataset_access: bool
    publication_permitted: bool

    def require(self) -> None:
        if self != expected_gates():
            raise FinalEngineeringInvocationAuthorizationError(
                "authorization gates differ"
            )


@dataclass(frozen=True)
class FinalEngineeringInvocationAuthorization:
    """Canonical issued authorization record pending post-merge verification."""

    schema_version: int
    authorization_id: str
    status: str
    authorization_issued_at_utc: str
    authoring_base_commit: str
    source: FinalEngineeringInvocationAuthorizationSource
    operator: FinalEngineeringInvocationAuthorizationOperator
    contract: FinalEngineeringInvocationAuthorizationContract
    boundary: FinalEngineeringInvocationAuthorizationBoundary
    gates: FinalEngineeringInvocationAuthorizationGates
    authorization_sha256: str
    next_slice: str
    post_merge_next_slice: str

    def semantic_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop("authorization_sha256")
        return payload

    def canonical_json(self) -> str:
        return canonical_json(asdict(self))

    def require(self) -> None:
        if self.schema_version != 1:
            raise FinalEngineeringInvocationAuthorizationError(
                "authorization schema version differs"
            )
        if self.authorization_id != FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_ID:
            raise FinalEngineeringInvocationAuthorizationError(
                "authorization id differs"
            )
        if self.status != FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_STATUS:
            raise FinalEngineeringInvocationAuthorizationError(
                "authorization status differs"
            )
        _require_utc(
            self.authorization_issued_at_utc,
            "authorization_issued_at_utc",
        )
        _require_commit(self.authoring_base_commit, "authoring_base_commit")
        if self.authoring_base_commit != AUTHORIZATION_SCOPE_FREEZE_MERGE_COMMIT:
            raise FinalEngineeringInvocationAuthorizationError(
                "authoring base commit differs"
            )
        self.source.require()
        self.operator.require()
        self.contract.require()
        self.boundary.require()
        self.gates.require()
        _require_sha256(self.authorization_sha256, "authorization_sha256")
        if self.authorization_sha256 != sha256_object(self.semantic_payload()):
            raise FinalEngineeringInvocationAuthorizationError(
                "authorization semantic SHA-256 differs"
            )
        if (
            self.next_slice
            != "QW-LC4-E-final-engineering-invocation-authorization-record-authoring-commit"
        ):
            raise FinalEngineeringInvocationAuthorizationError(
                "authorization next slice differs"
            )
        if (
            self.post_merge_next_slice
            != "QW-LC4-E-final-engineering-invocation-authorization-consumption-attempt-scope-freeze"
        ):
            raise FinalEngineeringInvocationAuthorizationError(
                "authorization post-merge next slice differs"
            )


def expected_source() -> FinalEngineeringInvocationAuthorizationSource:
    """Return the exact frozen source identity."""

    return FinalEngineeringInvocationAuthorizationSource(
        scope_id=AUTHORIZATION_SCOPE_ID,
        scope_freeze_merge_commit=AUTHORIZATION_SCOPE_FREEZE_MERGE_COMMIT,
        scope_freeze_pr_head=AUTHORIZATION_SCOPE_FREEZE_PR_HEAD,
        scope_freeze_pr_number=AUTHORIZATION_SCOPE_FREEZE_PR_NUMBER,
        scope_freeze_merged_at_utc=AUTHORIZATION_SCOPE_FREEZE_MERGED_AT_UTC,
        torch2pc_commit=FROZEN_TORCH2PC_COMMIT,
        scope_registry_sha256="sha256:b1c5b79e150085ff512349e8ca051c673ad72f9255ab7ae933c69b9ea6371c8a",
        scope_file_sha256="sha256:9aa30b84dc055a5411e6885c999f47e0f37b10fc413a79d168084efd832da47a",
        repository_seal_registry_sha256="sha256:45b05afa00a9b43b73f08c7d6227f68d5d1c6813e0910cc2a1d7d3e3672cf1d8",
        repository_seal_receipt_sha256="sha256:0445b537efc6d8266d6a20b68ba2963090668dac6d280e9b270a0f927b8ff161",
        admission_id="stage3b-qwake-lc4-e-final-engineering-invocation-admission-v1",
        admission_semantic_sha256="sha256:a66fd1c74b71834026af0bd699e48bc54c5aab368f1fe02a13be164aefe7f942",
        admission_registry_sha256="sha256:2c353c053e0968ee87afc0f09da7c2aadb898c9ef80a274206f38650be7ff627",
        admission_source_registry_sha256="sha256:adfb8f5dc11b6da6614f6842b3e535c68b2eb130f914e58d0c41d302854f67c9",
        admission_record_sha256="sha256:dfc4bcd7505328bd69d4fd88b79c8ea06caa7c8a0b8871354dc7b7488e999114",
        persistent_chain_registry_sha256="sha256:ad5e0b84d88a3e830986448ff9ee7ebeb46bdd03a5e85202471e93968a6de24f",
        persistent_chain_implementation_sha256="sha256:fdbad25b58c995ec7b1db7f6d292e3185b93352b4234cee9f6f52a05229c8473",
        wiring_registry_sha256="sha256:89406036c617de7875c01375c67d5b1d317528307353d51975cfb3b67797be94",
        wiring_record_sha256="sha256:60199510764aa4827bfb2deac69675b7d5d79e7209fa8f0aa53ba8d79a5c4ff3",
        runtime_entrypoint_module_sha256="sha256:9b665d785caa6550191b90df9795abe1d3ee2b52e52536cfa3aaa12f56e574cd",
        historical_engineering_authorization_registry_sha256="sha256:9a47f79e9607db98a2c7c224c25cbeee920974d4c339eef4ef82d4f9aa7c8f83",
        historical_engineering_authorization_record_sha256="sha256:e7b58ad04a932b36a0eaea5a276e95c593d4e88e303e05dadbb25eaf3eb5c999",
        historical_acknowledgement_authorization_registry_sha256="sha256:9253ffea4d576f4b0a8732005dcace67adf1b9ac78c4bbe523ae2017762eec57",
        historical_acknowledgement_authorization_record_sha256="sha256:561b864c08be9d4d33985fb94f7882abf77c9c4316cff2a8d1feee9cbf0e23a4",
    )


def expected_operator() -> FinalEngineeringInvocationAuthorizationOperator:
    """Return the exact operator binding."""

    return FinalEngineeringInvocationAuthorizationOperator(
        identity_kind=AUTHORIZATION_OPERATOR_IDENTITY_KIND,
        identity=AUTHORIZATION_OPERATOR_IDENTITY,
        action_phrase=AUTHORIZATION_ACTION_PHRASE,
    )


def expected_contract() -> FinalEngineeringInvocationAuthorizationContract:
    """Return the exact one-shot contract."""

    return FinalEngineeringInvocationAuthorizationContract(
        image_repo_digest=IMAGE_REPO_DIGEST,
        runtime_entrypoint_module=RUNTIME_ENTRYPOINT_MODULE,
        runtime_entrypoint=RUNTIME_ENTRYPOINT,
        output_root=OUTPUT_ROOT,
        execution_lease_v1_relative=EXECUTION_LEASE_V1_RELATIVE.as_posix(),
        execution_lease_v2_relative=EXECUTION_LEASE_V2_RELATIVE.as_posix(),
        durable_host_outcome_relative=DURABLE_HOST_OUTCOME_RELATIVE.as_posix(),
        invocation_limit=1,
        distinct_new_authorization_required=True,
        exact_operator_identity_required=True,
        separate_operator_action_phrase_required=True,
        authorization_post_merge_verified_before_invocation=True,
        post_merge_verification_required_before_effective_authority=True,
        atomic_consumption_with_attempt_start_and_exclusive_lease_v2=True,
        persistent_lease_v2_required_before_entrypoint=True,
        durable_host_outcome_required_for_every_terminal_class=True,
        historical_engineering_authorization_reuse_forbidden=True,
        acknowledgement_authorization_reuse_forbidden=True,
        retry_after_consumption_forbidden=True,
        retry_after_lease_creation_forbidden=True,
        retry_after_unknown_outcome_forbidden=True,
        shell_invocation_forbidden=True,
        direct_docker_call_forbidden=True,
        direct_lower_host_invoker_call_forbidden=True,
        direct_historical_runtime_operation_call_forbidden=True,
        scientific_campaign_authority=False,
        test_dataset_authority=False,
        publication_authority=False,
        qw5_authority=False,
        verifier_runtime_entrypoint_import_forbidden=True,
        negative_tests_temporary_repositories_only=True,
    )


def expected_boundary() -> FinalEngineeringInvocationAuthorizationBoundary:
    """Return the exact closed authoring boundary."""

    return FinalEngineeringInvocationAuthorizationBoundary(
        authoring_base_commit=AUTHORIZATION_SCOPE_FREEZE_MERGE_COMMIT,
        output_root_absent=True,
        execution_lease_v1_absent=True,
        execution_lease_v2_absent=True,
        durable_host_outcome_absent=True,
        runtime_output_absent=True,
        invocation_command_absent=True,
        image_inspection_performed=False,
        docker_run_performed=False,
        child_process_created=False,
        model_code_invoked=False,
        existing_frozen_package_modified=False,
    )


def expected_gates() -> FinalEngineeringInvocationAuthorizationGates:
    """Return the exact issued-but-ineffective gate state."""

    return FinalEngineeringInvocationAuthorizationGates(
        final_engineering_invocation_admission_repository_seal_complete=True,
        final_engineering_invocation_authorization_authoring_scope_frozen=True,
        final_engineering_invocation_authorization_authored=True,
        final_engineering_invocation_authorization_record_present=True,
        final_engineering_invocation_authorization_issued=True,
        final_engineering_invocation_authorization_post_merge_verified=False,
        final_engineering_invocation_authorization_consumed=False,
        final_engineering_invocation_permitted=False,
        final_engineering_invocation_started=False,
        final_engineering_invocation_performed=False,
        operator_phrase_reserved=True,
        invocation_command_materialized=False,
        execution_lease_v1_present=False,
        execution_lease_v2_present=False,
        durable_host_outcome_present=False,
        runtime_output_present=False,
        extension_engineering_report_present=False,
        qw_lc4_e_complete=False,
        qw5_transition_permitted=False,
        qw5_scientific_image_freeze_open=False,
        local_compute_execution_open=False,
        test_dataset_access=False,
        publication_permitted=False,
    )


def build_final_engineering_invocation_authorization(
    *,
    authorization_issued_at_utc: str,
    authoring_base_commit: str,
) -> FinalEngineeringInvocationAuthorization:
    """Build the canonical issued record with effective authority closed."""

    draft = FinalEngineeringInvocationAuthorization(
        schema_version=1,
        authorization_id=FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_ID,
        status=FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_STATUS,
        authorization_issued_at_utc=authorization_issued_at_utc,
        authoring_base_commit=authoring_base_commit,
        source=expected_source(),
        operator=expected_operator(),
        contract=expected_contract(),
        boundary=expected_boundary(),
        gates=expected_gates(),
        authorization_sha256="sha256:" + "0" * 64,
        next_slice=(
            "QW-LC4-E-final-engineering-invocation-"
            "authorization-record-authoring-commit"
        ),
        post_merge_next_slice=(
            "QW-LC4-E-final-engineering-invocation-"
            "authorization-consumption-attempt-scope-freeze"
        ),
    )
    completed = replace(
        draft,
        authorization_sha256=sha256_object(draft.semantic_payload()),
    )
    completed.require()
    return completed


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_mapping(path: Path) -> Mapping[str, Any]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FinalEngineeringInvocationAuthorizationError(
            f"cannot load JSON: {path}"
        ) from exc
    if not isinstance(loaded, Mapping):
        raise FinalEngineeringInvocationAuthorizationError(
            f"JSON root is not an object: {path}"
        )
    return cast(Mapping[str, Any], loaded)


def _verify_registry(package_root: Path, expected_files: frozenset[str]) -> None:
    registry = package_root / "SHA256SUMS"
    lines = registry.read_text(encoding="utf-8").splitlines()
    entries: dict[str, str] = {}
    for line in lines:
        digest, relative = line.split("  ", 1)
        entries[relative] = digest
    if set(entries) != expected_files - {"SHA256SUMS"}:
        raise FinalEngineeringInvocationAuthorizationError(
            f"package registry scope differs: {package_root}"
        )
    for relative, digest in entries.items():
        target = package_root / relative
        if not target.is_file() or target.is_symlink():
            raise FinalEngineeringInvocationAuthorizationError(
                f"package entry missing: {target}"
            )
        if _sha256_file(target) != digest:
            raise FinalEngineeringInvocationAuthorizationError(
                f"package registry digest differs: {target}"
            )


def _verify_package(
    project_root: Path,
    relative: Path,
    expected_files: frozenset[str],
) -> None:
    package_root = project_root / relative
    if not package_root.is_dir() or package_root.is_symlink():
        raise FinalEngineeringInvocationAuthorizationError(
            f"source package missing: {relative.as_posix()}"
        )
    observed = frozenset(entry.name for entry in package_root.iterdir())
    if observed != expected_files:
        raise FinalEngineeringInvocationAuthorizationError(
            f"source package scope differs: {relative.as_posix()}"
        )
    if any(entry.is_dir() or entry.is_symlink() for entry in package_root.iterdir()):
        raise FinalEngineeringInvocationAuthorizationError(
            f"source package contains non-regular entry: {relative.as_posix()}"
        )
    _verify_registry(package_root, expected_files)


def _verify_exact_files(project_root: Path) -> None:
    for relative, expected_digest in _EXPECTED_FILE_SHA256.items():
        target = project_root / relative
        if not target.is_file() or target.is_symlink():
            raise FinalEngineeringInvocationAuthorizationError(
                f"exact source file missing: {relative.as_posix()}"
            )
        if _sha256_file(target) != expected_digest:
            raise FinalEngineeringInvocationAuthorizationError(
                f"exact source file digest differs: {relative.as_posix()}"
            )


def _verify_source_semantics(project_root: Path) -> None:
    scope = _load_mapping(
        project_root / AUTHORIZATION_SCOPE_PACKAGE_RELATIVE / "scope.json"
    )
    effects = cast(Mapping[str, Any], scope["effect_boundary"])
    gates = cast(Mapping[str, Any], scope["gates"])
    contract = cast(Mapping[str, Any], scope["future_authorization_contract"])

    if scope["scope_id"] != AUTHORIZATION_SCOPE_ID:
        raise FinalEngineeringInvocationAuthorizationError("scope id differs")
    if scope["post_merge_next_slice"] != (
        "QW-LC4-E-final-engineering-invocation-authorization-record-authoring"
    ):
        raise FinalEngineeringInvocationAuthorizationError(
            "scope next authoring slice differs"
        )
    if gates["final_engineering_invocation_authorization_authoring_scope_frozen"] is not True:
        raise FinalEngineeringInvocationAuthorizationError(
            "authorization scope freeze is not complete"
        )
    for name in (
        "final_engineering_invocation_authorization_authored",
        "final_engineering_invocation_authorization_record_present",
        "final_engineering_invocation_authorization_issued",
        "final_engineering_invocation_authorization_post_merge_verified",
        "final_engineering_invocation_authorization_consumed",
        "final_engineering_invocation_permitted",
        "final_engineering_invocation_started",
        "final_engineering_invocation_performed",
    ):
        if gates[name] is not False:
            raise FinalEngineeringInvocationAuthorizationError(
                f"scope source gate is unexpectedly open: {name}"
            )
    for name in (
        "authorization_schema_created",
        "authorization_verifier_created",
        "authorization_tests_created",
        "authorization_record_created",
        "authorization_issued",
        "authorization_consumed",
        "operator_phrase_reserved",
        "invocation_command_materialized",
        "execution_lease_v1_present",
        "execution_lease_v2_present",
        "durable_host_outcome_present",
        "runtime_output_present",
        "docker_run_performed",
        "child_process_created",
        "model_code_invoked",
    ):
        if effects[name] is not False:
            raise FinalEngineeringInvocationAuthorizationError(
                f"scope source effect is unexpectedly present: {name}"
            )
    if contract["distinct_new_authorization_required"] is not True:
        raise FinalEngineeringInvocationAuthorizationError(
            "distinct authorization is not required"
        )
    if contract["invocation_limit"] != 1:
        raise FinalEngineeringInvocationAuthorizationError(
            "scope invocation limit differs"
        )

    admission = _load_mapping(
        project_root / ADMISSION_PACKAGE_RELATIVE / "admission.json"
    )
    if admission["admission_id"] != expected_source().admission_id:
        raise FinalEngineeringInvocationAuthorizationError("admission id differs")
    if admission["admission_sha256"] != expected_source().admission_semantic_sha256:
        raise FinalEngineeringInvocationAuthorizationError(
            "admission semantic SHA-256 differs"
        )
    admission_gates = cast(Mapping[str, Any], admission["gates"])
    if admission_gates["final_engineering_invocation_admission_authored"] is not True:
        raise FinalEngineeringInvocationAuthorizationError(
            "admission is not authored"
        )
    for name in (
        "final_engineering_invocation_authorization_issued",
        "final_engineering_invocation_authorization_consumed",
        "final_engineering_invocation_permitted",
        "final_engineering_invocation_started",
        "final_engineering_invocation_performed",
    ):
        if admission_gates[name] is not False:
            raise FinalEngineeringInvocationAuthorizationError(
                f"admission source gate is unexpectedly open: {name}"
            )

    historical = _load_mapping(
        project_root
        / HISTORICAL_ENGINEERING_AUTHORIZATION_PACKAGE_RELATIVE
        / "authorization.json"
    )
    if historical["authorization_id"] == FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_ID:
        raise FinalEngineeringInvocationAuthorizationError(
            "new authorization reuses historical engineering id"
        )

    acknowledgement = _load_mapping(
        project_root
        / HISTORICAL_ACKNOWLEDGEMENT_AUTHORIZATION_PACKAGE_RELATIVE
        / "authorization.json"
    )
    if acknowledgement["authorization_id"] == FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_ID:
        raise FinalEngineeringInvocationAuthorizationError(
            "new authorization reuses acknowledgement id"
        )


def verify_final_engineering_invocation_authorization_sources(
    project_root: Path,
) -> FinalEngineeringInvocationAuthorizationSource:
    """Verify exact frozen inputs without importing the runtime entrypoint."""

    resolved = project_root.resolve()
    for relative, expected_files in _EXPECTED_PACKAGE_FILES.items():
        _verify_package(resolved, relative, expected_files)
    _verify_exact_files(resolved)
    _verify_source_semantics(resolved)
    source = expected_source()
    source.require()
    return source


def load_final_engineering_invocation_authorization(
    path: Path,
) -> FinalEngineeringInvocationAuthorization:
    """Load and validate a canonical authorization record."""

    raw = path.read_text(encoding="utf-8")
    mapping = json.loads(raw)
    if not isinstance(mapping, Mapping):
        raise FinalEngineeringInvocationAuthorizationError(
            "authorization JSON root is not an object"
        )
    source = FinalEngineeringInvocationAuthorizationSource(
        **cast(dict[str, Any], mapping["source"])
    )
    operator = FinalEngineeringInvocationAuthorizationOperator(
        **cast(dict[str, Any], mapping["operator"])
    )
    contract = FinalEngineeringInvocationAuthorizationContract(
        **cast(dict[str, Any], mapping["contract"])
    )
    boundary = FinalEngineeringInvocationAuthorizationBoundary(
        **cast(dict[str, Any], mapping["boundary"])
    )
    gates = FinalEngineeringInvocationAuthorizationGates(
        **cast(dict[str, Any], mapping["gates"])
    )
    record = FinalEngineeringInvocationAuthorization(
        schema_version=cast(int, mapping["schema_version"]),
        authorization_id=cast(str, mapping["authorization_id"]),
        status=cast(str, mapping["status"]),
        authorization_issued_at_utc=cast(
            str,
            mapping["authorization_issued_at_utc"],
        ),
        authoring_base_commit=cast(str, mapping["authoring_base_commit"]),
        source=source,
        operator=operator,
        contract=contract,
        boundary=boundary,
        gates=gates,
        authorization_sha256=cast(str, mapping["authorization_sha256"]),
        next_slice=cast(str, mapping["next_slice"]),
        post_merge_next_slice=cast(str, mapping["post_merge_next_slice"]),
    )
    if raw != record.canonical_json():
        raise FinalEngineeringInvocationAuthorizationError(
            "authorization JSON is not canonical"
        )
    record.require()
    return record


def validate_final_engineering_invocation_authorization(
    authorization: FinalEngineeringInvocationAuthorization,
    source: FinalEngineeringInvocationAuthorizationSource,
    project_root: Path,
    *,
    expected_authoring_base_commit: str,
) -> None:
    """Validate record and preserve the closed runtime boundary."""

    authorization.require()
    source.require()
    if authorization.source != source:
        raise FinalEngineeringInvocationAuthorizationError(
            "authorization source differs from verified source"
        )
    if authorization.authoring_base_commit != expected_authoring_base_commit:
        raise FinalEngineeringInvocationAuthorizationError(
            "authorization authoring base differs"
        )
    for relative in (
        Path(OUTPUT_ROOT),
        EXECUTION_LEASE_V1_RELATIVE,
        EXECUTION_LEASE_V2_RELATIVE,
        DURABLE_HOST_OUTCOME_RELATIVE,
    ):
        target = project_root / relative
        if target.exists() or target.is_symlink():
            raise FinalEngineeringInvocationAuthorizationError(
                f"runtime boundary path already exists: {relative.as_posix()}"
            )
