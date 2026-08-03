"""Pure fail-closed schema for the final QW-LC4-E consumption attempt.

The authored record may state that the attempt is prepared. It never consumes
authorization, starts the attempt, creates a lease, imports the runtime entry
point, starts a child process, inspects an image, or writes runtime output.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Final, cast

ATTEMPT_ID: Final = (
    "stage3b-qwake-lc4-e-final-engineering-invocation-authorization-"
    "consumption-attempt-v1"
)
ATTEMPT_STATUS: Final = (
    "final_engineering_invocation_authorization_consumption_attempt_"
    "prepared_merge_required_atomic_action_closed"
)
SCOPE_ID: Final = (
    "stage3b-qwake-lc4-e-final-engineering-invocation-authorization-"
    "consumption-attempt-scope-freeze-v1"
)
SCOPE_FREEZE_MERGE_COMMIT: Final = (
    "28b4627436244893195231f55f2d0d5fb2d1062e"
)
SCOPE_FREEZE_PR_HEAD: Final = (
    "17af7d6f4473af846f2d293192082074cad99cf2"
)
SCOPE_FREEZE_PR_NUMBER: Final = 173
SCOPE_FREEZE_MERGED_AT_UTC: Final = "2026-08-03T19:38:32Z"
FROZEN_TORCH2PC_COMMIT: Final = (
    "b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4"
)
AUTHORIZATION_ID: Final = (
    "stage3b-qwake-lc4-e-final-engineering-invocation-authorization-v1"
)
AUTHORIZATION_SEMANTIC_SHA256: Final = (
    "sha256:629e87c79f03cd50f4b427d66b873802a06b36efe9def502b50232a474c18014"
)
OPERATOR_IDENTITY_KIND: Final = "local-posix-account"
OPERATOR_IDENTITY: Final = "dzmitry-prychyna"
OPERATOR_ACTION_PHRASE: Final = (
    "AUTHORIZE_QWAKE_LC4_FINAL_ENGINEERING_INVOCATION_ONCE_AFTER_"
    "POST_MERGE_VERIFICATION"
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

SCOPE_PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-final-engineering-invocation-authorization-"
    "consumption-attempt-scope-freeze-v1"
)
AUTHORIZATION_PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-final-engineering-invocation-authorization-v1"
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

_EXPECTED_PACKAGE_FILES: Final[dict[Path, frozenset[str]]] = {
    SCOPE_PACKAGE_RELATIVE: frozenset({"SHA256SUMS", "scope.json"}),
    AUTHORIZATION_PACKAGE_RELATIVE: frozenset(
        {"SHA256SUMS", "authorization.json", "source-SHA256SUMS"}
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
}

_EXPECTED_FILE_SHA256: Final[dict[Path, str]] = {
    Path("experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-scope-freeze-v1/SHA256SUMS"): "ec3f5829462d43b621b9d405d87de09f255f71f9aeac012cc70c69e259aa76a4",
    Path("experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-scope-freeze-v1/scope.json"): "369c38a71e06af3ba9e0d5399724dc64f4e8d211b5fd7532100f7b322e7435c6",
    Path("experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-v1/SHA256SUMS"): "94a358ea67f46fe9559a09e7b917bed101d99c03eee269b5a86e8de0e039c760",
    Path("experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-v1/source-SHA256SUMS"): "cf42cd926b6db1f3b40167ed3b6cf2f8e5ca5a22564330125f6001bf37d6eab7",
    Path("experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-v1/authorization.json"): "33323d40daf40c39dc1d558fba5439f855c573409415504e951de41181db6a09",
    Path("src/torch2pc_thesis/stage3b_qwake_lc4_final_engineering_invocation_authorization.py"): "64e8a4c38c0fff200ef37ca4f4ad1a07d5eb157e535a2b1f7b253216a04b7431",
    Path("scripts/verify_stage3b_qwake_lc4_final_engineering_invocation_authorization.py"): "680603e798fb231faefaef086659a7977e7502780cd71499ff7d5e78fb11aecb",
    Path("tests/unit/test_stage3b_qwake_lc4_final_engineering_invocation_authorization.py"): "01329c003297cc01228714108a5fe7d696fe365429339573b9d4670ef0eddef4",
    Path("experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-admission-repository-seal-v1/SHA256SUMS"): "45b05afa00a9b43b73f08c7d6227f68d5d1c6813e0910cc2a1d7d3e3672cf1d8",
    Path("experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-admission-repository-seal-v1/receipt.json"): "0445b537efc6d8266d6a20b68ba2963090668dac6d280e9b270a0f927b8ff161",
    Path("experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-admission-authoring-v1/SHA256SUMS"): "2c353c053e0968ee87afc0f09da7c2aadb898c9ef80a274206f38650be7ff627",
    Path("experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-admission-authoring-v1/source-SHA256SUMS"): "adfb8f5dc11b6da6614f6842b3e535c68b2eb130f914e58d0c41d302854f67c9",
    Path("experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-admission-authoring-v1/admission.json"): "dfc4bcd7505328bd69d4fd88b79c8ea06caa7c8a0b8871354dc7b7488e999114",
    Path("experiments/frozen/stage3b-qwake-lc4-e-persistent-evidence-chain-v2-implementation-v1/SHA256SUMS"): "ad5e0b84d88a3e830986448ff9ee7ebeb46bdd03a5e85202471e93968a6de24f",
    Path("experiments/frozen/stage3b-qwake-lc4-e-persistent-evidence-chain-v2-implementation-v1/implementation.json"): "fdbad25b58c995ec7b1db7f6d292e3185b93352b4234cee9f6f52a05229c8473",
    Path("experiments/frozen/stage3b-qwake-lc4-e-lease-bound-host-invoker-wiring-v1/SHA256SUMS"): "89406036c617de7875c01375c67d5b1d317528307353d51975cfb3b67797be94",
    Path("experiments/frozen/stage3b-qwake-lc4-e-lease-bound-host-invoker-wiring-v1/wiring.json"): "60199510764aa4827bfb2deac69675b7d5d79e7209fa8f0aa53ba8d79a5c4ff3",
    Path("src/torch2pc_thesis/stage3b_qwake_lc4_lease_bound_host_invoker_wiring.py"): "9b665d785caa6550191b90df9795abe1d3ee2b52e52536cfa3aaa12f56e574cd",
}

_COMMIT_PATTERN: Final = re.compile(r"^[0-9a-f]{40}$")
_SHA256_PATTERN: Final = re.compile(r"^sha256:[0-9a-f]{64}$")
_UTC_PATTERN: Final = re.compile(
    r"^20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
)


class ConsumptionAttemptError(RuntimeError):
    """Raised when attempt-record validation cannot remain fail closed."""


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
        raise ConsumptionAttemptError(f"{field_name} is not a commit")


def _require_sha256(value: str, field_name: str) -> None:
    if _SHA256_PATTERN.fullmatch(value) is None:
        raise ConsumptionAttemptError(f"{field_name} is not SHA-256")


def _require_utc(value: str, field_name: str) -> None:
    if _UTC_PATTERN.fullmatch(value) is None:
        raise ConsumptionAttemptError(f"{field_name} is not canonical UTC")


@dataclass(frozen=True)
class ConsumptionAttemptSource:
    """Exact immutable source identities for attempt preparation."""

    scope_id: str
    scope_freeze_pr_number: int
    scope_freeze_pr_head: str
    scope_freeze_merge_commit: str
    scope_freeze_merged_at_utc: str
    torch2pc_commit: str
    scope_registry_sha256: str
    scope_record_sha256: str
    authorization_id: str
    authorization_semantic_sha256: str
    authorization_registry_sha256: str
    authorization_source_registry_sha256: str
    authorization_record_sha256: str
    repository_seal_registry_sha256: str
    repository_seal_receipt_sha256: str
    admission_registry_sha256: str
    admission_source_registry_sha256: str
    admission_record_sha256: str
    persistent_chain_registry_sha256: str
    persistent_chain_implementation_sha256: str
    wiring_registry_sha256: str
    wiring_record_sha256: str
    runtime_entrypoint_module_sha256: str

    def require(self) -> None:
        if self != expected_source():
            raise ConsumptionAttemptError("attempt source identities differ")


@dataclass(frozen=True)
class ConsumptionAttemptOperator:
    """Exact operator identity and separately reserved action phrase."""

    identity_kind: str
    identity: str
    action_phrase: str

    def require(self) -> None:
        if self != expected_operator():
            raise ConsumptionAttemptError(
                "attempt operator identity or phrase differs"
            )


@dataclass(frozen=True)
class ConsumptionAttemptContract:
    """Prepared-record contract; atomic action remains closed."""

    image_repo_digest: str
    runtime_entrypoint_module: str
    runtime_entrypoint: str
    output_root: str
    execution_lease_v1_relative: str
    execution_lease_v2_relative: str
    durable_host_outcome_relative: str
    attempt_limit: int
    distinct_new_attempt_record_required: bool
    attempt_record_authoring_is_nonexecuting: bool
    attempt_record_may_mark_prepared: bool
    exact_operator_identity_required: bool
    exact_operator_action_phrase_required_at_operational_boundary: bool
    scope_freeze_post_merge_verified_before_authoring: bool
    attempt_record_post_merge_verification_required_before_atomic_action: bool
    atomic_authorization_consumption_with_attempt_start_and_exclusive_lease_v2: bool
    persistent_lease_v2_required_before_entrypoint: bool
    exact_persisted_lease_bytes_required_before_entrypoint: bool
    pre_atomic_failure_must_not_consume_authorization: bool
    pre_atomic_failure_must_not_start_attempt: bool
    pre_atomic_failure_must_not_create_lease_v2: bool
    durable_host_outcome_required_for_every_terminal_class: bool
    retry_after_atomic_transition_forbidden: bool
    retry_after_consumption_forbidden: bool
    retry_after_lease_creation_forbidden: bool
    retry_after_unknown_outcome_forbidden: bool
    shell_invocation_forbidden: bool
    direct_docker_call_forbidden: bool
    direct_lower_host_invoker_call_forbidden: bool
    direct_historical_runtime_operation_call_forbidden: bool
    verifier_runtime_entrypoint_import_forbidden: bool
    negative_tests_temporary_repositories_only: bool
    scientific_campaign_authority: bool
    test_dataset_authority: bool
    publication_authority: bool
    qw5_authority: bool

    def require(self) -> None:
        if self != expected_contract():
            raise ConsumptionAttemptError("attempt contract differs")


@dataclass(frozen=True)
class ConsumptionAttemptBoundary:
    """Closed repository and runtime boundary at record-authoring time."""

    authoring_base_commit: str
    scope_record_modified: bool
    authorization_record_modified: bool
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
            raise ConsumptionAttemptError("attempt boundary differs")


@dataclass(frozen=True)
class ConsumptionAttemptGates:
    """Prepared record with atomic action still closed."""

    final_engineering_invocation_authorization_record_line_complete: bool
    final_engineering_invocation_authorization_post_merge_verified: bool
    final_engineering_invocation_authorization_consumed: bool
    final_engineering_invocation_permitted: bool
    final_engineering_invocation_started: bool
    final_engineering_invocation_performed: bool
    authorization_consumption_attempt_scope_frozen: bool
    authorization_consumption_attempt_scope_freeze_post_merge_verified: bool
    authorization_consumption_attempt_record_authoring_admissible: bool
    authorization_consumption_attempt_record_authored: bool
    authorization_consumption_attempt_record_present: bool
    authorization_consumption_attempt_prepared: bool
    authorization_consumption_attempt_post_merge_verified: bool
    authorization_consumption_attempt_atomic_action_permitted: bool
    authorization_consumption_attempt_started: bool
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
            raise ConsumptionAttemptError("attempt gates differ")


@dataclass(frozen=True)
class ConsumptionAttempt:
    """Canonical prepared attempt record pending post-merge verification."""

    schema_version: int
    attempt_id: str
    status: str
    attempt_prepared_at_utc: str
    authoring_base_commit: str
    source: ConsumptionAttemptSource
    operator: ConsumptionAttemptOperator
    contract: ConsumptionAttemptContract
    boundary: ConsumptionAttemptBoundary
    gates: ConsumptionAttemptGates
    attempt_sha256: str
    next_slice: str
    post_merge_next_slice: str

    def semantic_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop("attempt_sha256")
        return payload

    def canonical_json(self) -> str:
        return canonical_json(asdict(self))

    def require(self) -> None:
        if self.schema_version != 1:
            raise ConsumptionAttemptError("attempt schema version differs")
        if self.attempt_id != ATTEMPT_ID:
            raise ConsumptionAttemptError("attempt id differs")
        if self.status != ATTEMPT_STATUS:
            raise ConsumptionAttemptError("attempt status differs")
        _require_utc(self.attempt_prepared_at_utc, "attempt_prepared_at_utc")
        _require_commit(self.authoring_base_commit, "authoring_base_commit")
        if self.authoring_base_commit != SCOPE_FREEZE_MERGE_COMMIT:
            raise ConsumptionAttemptError("authoring base commit differs")
        self.source.require()
        self.operator.require()
        self.contract.require()
        self.boundary.require()
        self.gates.require()
        _require_sha256(self.attempt_sha256, "attempt_sha256")
        if self.attempt_sha256 != sha256_object(self.semantic_payload()):
            raise ConsumptionAttemptError("attempt semantic SHA-256 differs")
        if self.next_slice != (
            "QW-LC4-E-final-engineering-invocation-authorization-"
            "consumption-attempt-record-authoring-commit"
        ):
            raise ConsumptionAttemptError("attempt next slice differs")
        if self.post_merge_next_slice != (
            "QW-LC4-E-final-engineering-invocation-authorization-"
            "consumption-attempt-atomic-transition-scope-freeze"
        ):
            raise ConsumptionAttemptError(
                "attempt post-merge next slice differs"
            )


def expected_source() -> ConsumptionAttemptSource:
    """Return the exact frozen source identity."""

    return ConsumptionAttemptSource(
        scope_id=SCOPE_ID,
        scope_freeze_pr_number=SCOPE_FREEZE_PR_NUMBER,
        scope_freeze_pr_head=SCOPE_FREEZE_PR_HEAD,
        scope_freeze_merge_commit=SCOPE_FREEZE_MERGE_COMMIT,
        scope_freeze_merged_at_utc=SCOPE_FREEZE_MERGED_AT_UTC,
        torch2pc_commit=FROZEN_TORCH2PC_COMMIT,
        scope_registry_sha256="sha256:ec3f5829462d43b621b9d405d87de09f255f71f9aeac012cc70c69e259aa76a4",
        scope_record_sha256="sha256:369c38a71e06af3ba9e0d5399724dc64f4e8d211b5fd7532100f7b322e7435c6",
        authorization_id=AUTHORIZATION_ID,
        authorization_semantic_sha256=AUTHORIZATION_SEMANTIC_SHA256,
        authorization_registry_sha256="sha256:94a358ea67f46fe9559a09e7b917bed101d99c03eee269b5a86e8de0e039c760",
        authorization_source_registry_sha256="sha256:cf42cd926b6db1f3b40167ed3b6cf2f8e5ca5a22564330125f6001bf37d6eab7",
        authorization_record_sha256="sha256:33323d40daf40c39dc1d558fba5439f855c573409415504e951de41181db6a09",
        repository_seal_registry_sha256="sha256:45b05afa00a9b43b73f08c7d6227f68d5d1c6813e0910cc2a1d7d3e3672cf1d8",
        repository_seal_receipt_sha256="sha256:0445b537efc6d8266d6a20b68ba2963090668dac6d280e9b270a0f927b8ff161",
        admission_registry_sha256="sha256:2c353c053e0968ee87afc0f09da7c2aadb898c9ef80a274206f38650be7ff627",
        admission_source_registry_sha256="sha256:adfb8f5dc11b6da6614f6842b3e535c68b2eb130f914e58d0c41d302854f67c9",
        admission_record_sha256="sha256:dfc4bcd7505328bd69d4fd88b79c8ea06caa7c8a0b8871354dc7b7488e999114",
        persistent_chain_registry_sha256="sha256:ad5e0b84d88a3e830986448ff9ee7ebeb46bdd03a5e85202471e93968a6de24f",
        persistent_chain_implementation_sha256="sha256:fdbad25b58c995ec7b1db7f6d292e3185b93352b4234cee9f6f52a05229c8473",
        wiring_registry_sha256="sha256:89406036c617de7875c01375c67d5b1d317528307353d51975cfb3b67797be94",
        wiring_record_sha256="sha256:60199510764aa4827bfb2deac69675b7d5d79e7209fa8f0aa53ba8d79a5c4ff3",
        runtime_entrypoint_module_sha256="sha256:9b665d785caa6550191b90df9795abe1d3ee2b52e52536cfa3aaa12f56e574cd",
    )


def expected_operator() -> ConsumptionAttemptOperator:
    return ConsumptionAttemptOperator(
        identity_kind=OPERATOR_IDENTITY_KIND,
        identity=OPERATOR_IDENTITY,
        action_phrase=OPERATOR_ACTION_PHRASE,
    )


def expected_contract() -> ConsumptionAttemptContract:
    return ConsumptionAttemptContract(
        image_repo_digest=IMAGE_REPO_DIGEST,
        runtime_entrypoint_module=RUNTIME_ENTRYPOINT_MODULE,
        runtime_entrypoint=RUNTIME_ENTRYPOINT,
        output_root=OUTPUT_ROOT,
        execution_lease_v1_relative=EXECUTION_LEASE_V1_RELATIVE.as_posix(),
        execution_lease_v2_relative=EXECUTION_LEASE_V2_RELATIVE.as_posix(),
        durable_host_outcome_relative=DURABLE_HOST_OUTCOME_RELATIVE.as_posix(),
        attempt_limit=1,
        distinct_new_attempt_record_required=True,
        attempt_record_authoring_is_nonexecuting=True,
        attempt_record_may_mark_prepared=True,
        exact_operator_identity_required=True,
        exact_operator_action_phrase_required_at_operational_boundary=True,
        scope_freeze_post_merge_verified_before_authoring=True,
        attempt_record_post_merge_verification_required_before_atomic_action=True,
        atomic_authorization_consumption_with_attempt_start_and_exclusive_lease_v2=True,
        persistent_lease_v2_required_before_entrypoint=True,
        exact_persisted_lease_bytes_required_before_entrypoint=True,
        pre_atomic_failure_must_not_consume_authorization=True,
        pre_atomic_failure_must_not_start_attempt=True,
        pre_atomic_failure_must_not_create_lease_v2=True,
        durable_host_outcome_required_for_every_terminal_class=True,
        retry_after_atomic_transition_forbidden=True,
        retry_after_consumption_forbidden=True,
        retry_after_lease_creation_forbidden=True,
        retry_after_unknown_outcome_forbidden=True,
        shell_invocation_forbidden=True,
        direct_docker_call_forbidden=True,
        direct_lower_host_invoker_call_forbidden=True,
        direct_historical_runtime_operation_call_forbidden=True,
        verifier_runtime_entrypoint_import_forbidden=True,
        negative_tests_temporary_repositories_only=True,
        scientific_campaign_authority=False,
        test_dataset_authority=False,
        publication_authority=False,
        qw5_authority=False,
    )


def expected_boundary() -> ConsumptionAttemptBoundary:
    return ConsumptionAttemptBoundary(
        authoring_base_commit=SCOPE_FREEZE_MERGE_COMMIT,
        scope_record_modified=False,
        authorization_record_modified=False,
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


def expected_gates() -> ConsumptionAttemptGates:
    return ConsumptionAttemptGates(
        final_engineering_invocation_authorization_record_line_complete=True,
        final_engineering_invocation_authorization_post_merge_verified=True,
        final_engineering_invocation_authorization_consumed=False,
        final_engineering_invocation_permitted=True,
        final_engineering_invocation_started=False,
        final_engineering_invocation_performed=False,
        authorization_consumption_attempt_scope_frozen=True,
        authorization_consumption_attempt_scope_freeze_post_merge_verified=True,
        authorization_consumption_attempt_record_authoring_admissible=True,
        authorization_consumption_attempt_record_authored=True,
        authorization_consumption_attempt_record_present=True,
        authorization_consumption_attempt_prepared=True,
        authorization_consumption_attempt_post_merge_verified=False,
        authorization_consumption_attempt_atomic_action_permitted=False,
        authorization_consumption_attempt_started=False,
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


def build_consumption_attempt(
    *,
    attempt_prepared_at_utc: str,
    authoring_base_commit: str,
) -> ConsumptionAttempt:
    draft = ConsumptionAttempt(
        schema_version=1,
        attempt_id=ATTEMPT_ID,
        status=ATTEMPT_STATUS,
        attempt_prepared_at_utc=attempt_prepared_at_utc,
        authoring_base_commit=authoring_base_commit,
        source=expected_source(),
        operator=expected_operator(),
        contract=expected_contract(),
        boundary=expected_boundary(),
        gates=expected_gates(),
        attempt_sha256="sha256:" + "0" * 64,
        next_slice=(
            "QW-LC4-E-final-engineering-invocation-authorization-"
            "consumption-attempt-record-authoring-commit"
        ),
        post_merge_next_slice=(
            "QW-LC4-E-final-engineering-invocation-authorization-"
            "consumption-attempt-atomic-transition-scope-freeze"
        ),
    )
    record = replace(
        draft,
        attempt_sha256=sha256_object(draft.semantic_payload()),
    )
    record.require()
    return record


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_mapping(path: Path) -> Mapping[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, Mapping):
        raise ConsumptionAttemptError(f"JSON root is not an object: {path}")
    return cast(Mapping[str, Any], loaded)


def _verify_registry(package_root: Path, expected_files: frozenset[str]) -> None:
    entries: dict[str, str] = {}
    for line in (package_root / "SHA256SUMS").read_text(
        encoding="utf-8"
    ).splitlines():
        digest, relative = line.split("  ", 1)
        entries[relative] = digest
    if set(entries) != expected_files - {"SHA256SUMS"}:
        raise ConsumptionAttemptError(
            f"package registry scope differs: {package_root}"
        )
    for relative, digest in entries.items():
        target = package_root / relative
        if not target.is_file() or target.is_symlink():
            raise ConsumptionAttemptError(f"package entry missing: {target}")
        if _sha256_file(target) != digest:
            raise ConsumptionAttemptError(
                f"package registry digest differs: {target}"
            )


def _verify_package(
    project_root: Path,
    relative: Path,
    expected_files: frozenset[str],
) -> None:
    package_root = project_root / relative
    if not package_root.is_dir() or package_root.is_symlink():
        raise ConsumptionAttemptError(
            f"source package missing: {relative.as_posix()}"
        )
    entries = tuple(package_root.iterdir())
    observed = frozenset(entry.name for entry in entries)
    if observed != expected_files:
        raise ConsumptionAttemptError(
            f"source package scope differs: {relative.as_posix()}"
        )
    if any(entry.is_dir() or entry.is_symlink() for entry in entries):
        raise ConsumptionAttemptError(
            f"source package contains non-regular entry: {relative.as_posix()}"
        )
    _verify_registry(package_root, expected_files)


def _verify_exact_files(project_root: Path) -> None:
    for relative, expected_digest in _EXPECTED_FILE_SHA256.items():
        target = project_root / relative
        if not target.is_file() or target.is_symlink():
            raise ConsumptionAttemptError(
                f"exact source file missing: {relative.as_posix()}"
            )
        if _sha256_file(target) != expected_digest:
            raise ConsumptionAttemptError(
                f"exact source file digest differs: {relative.as_posix()}"
            )


def _verify_source_semantics(project_root: Path) -> None:
    scope = _load_mapping(project_root / SCOPE_PACKAGE_RELATIVE / "scope.json")
    scope_gates = cast(Mapping[str, Any], scope["gates"])
    scope_effects = cast(Mapping[str, Any], scope["effect_boundary"])
    contract = cast(Mapping[str, Any], scope["future_attempt_contract"])

    if scope["scope_id"] != SCOPE_ID:
        raise ConsumptionAttemptError("scope id differs")
    if scope["post_merge_next_slice"] != (
        "QW-LC4-E-final-engineering-invocation-authorization-"
        "consumption-attempt-record-authoring"
    ):
        raise ConsumptionAttemptError("scope next authoring slice differs")
    if scope_gates["authorization_consumption_attempt_scope_frozen"] is not True:
        raise ConsumptionAttemptError("attempt scope is not frozen")
    for name in (
        "authorization_consumption_attempt_record_present",
        "authorization_consumption_attempt_prepared",
        "authorization_consumption_attempt_post_merge_verified",
        "authorization_consumption_attempt_started",
        "execution_lease_v2_present",
        "runtime_output_present",
    ):
        if scope_gates[name] is not False:
            raise ConsumptionAttemptError(
                f"scope source gate is unexpectedly open: {name}"
            )
    for name in (
        "attempt_schema_created",
        "attempt_verifier_created",
        "attempt_tests_created",
        "attempt_record_created",
        "authorization_consumed",
        "consumption_attempt_prepared",
        "consumption_attempt_started",
        "invocation_command_materialized",
        "execution_lease_v2_present",
        "durable_host_outcome_present",
        "runtime_output_present",
        "docker_run_performed",
        "child_process_created",
        "model_code_invoked",
    ):
        if scope_effects[name] is not False:
            raise ConsumptionAttemptError(
                f"scope source effect is unexpectedly present: {name}"
            )
    if contract["attempt_limit"] != 1:
        raise ConsumptionAttemptError("scope attempt limit differs")
    if contract["attempt_record_authoring_is_nonexecuting"] is not True:
        raise ConsumptionAttemptError("record authoring is not non-executing")
    if contract[
        "atomic_authorization_consumption_with_attempt_start_and_exclusive_lease_v2"
    ] is not True:
        raise ConsumptionAttemptError("atomic transition is not required")

    authorization = _load_mapping(
        project_root / AUTHORIZATION_PACKAGE_RELATIVE / "authorization.json"
    )
    if authorization["authorization_id"] != AUTHORIZATION_ID:
        raise ConsumptionAttemptError("authorization id differs")
    if authorization["authorization_sha256"] != AUTHORIZATION_SEMANTIC_SHA256:
        raise ConsumptionAttemptError("authorization semantic SHA-256 differs")
    authorization_gates = cast(Mapping[str, Any], authorization["gates"])
    if authorization_gates[
        "final_engineering_invocation_authorization_consumed"
    ] is not False:
        raise ConsumptionAttemptError("authorization is already consumed")


def verify_consumption_attempt_sources(project_root: Path) -> ConsumptionAttemptSource:
    """Verify exact frozen inputs without importing the runtime entrypoint."""

    resolved = project_root.resolve()
    for relative, expected_files in _EXPECTED_PACKAGE_FILES.items():
        _verify_package(resolved, relative, expected_files)
    _verify_exact_files(resolved)
    _verify_source_semantics(resolved)
    source = expected_source()
    source.require()
    return source


def load_consumption_attempt(path: Path) -> ConsumptionAttempt:
    """Load and validate a canonical prepared attempt record."""

    raw = path.read_text(encoding="utf-8")
    mapping = json.loads(raw)
    if not isinstance(mapping, Mapping):
        raise ConsumptionAttemptError("attempt JSON root is not an object")
    record = ConsumptionAttempt(
        schema_version=cast(int, mapping["schema_version"]),
        attempt_id=cast(str, mapping["attempt_id"]),
        status=cast(str, mapping["status"]),
        attempt_prepared_at_utc=cast(str, mapping["attempt_prepared_at_utc"]),
        authoring_base_commit=cast(str, mapping["authoring_base_commit"]),
        source=ConsumptionAttemptSource(
            **cast(dict[str, Any], mapping["source"])
        ),
        operator=ConsumptionAttemptOperator(
            **cast(dict[str, Any], mapping["operator"])
        ),
        contract=ConsumptionAttemptContract(
            **cast(dict[str, Any], mapping["contract"])
        ),
        boundary=ConsumptionAttemptBoundary(
            **cast(dict[str, Any], mapping["boundary"])
        ),
        gates=ConsumptionAttemptGates(
            **cast(dict[str, Any], mapping["gates"])
        ),
        attempt_sha256=cast(str, mapping["attempt_sha256"]),
        next_slice=cast(str, mapping["next_slice"]),
        post_merge_next_slice=cast(str, mapping["post_merge_next_slice"]),
    )
    if raw != record.canonical_json():
        raise ConsumptionAttemptError("attempt JSON is not canonical")
    record.require()
    return record


def validate_consumption_attempt(
    attempt: ConsumptionAttempt,
    source: ConsumptionAttemptSource,
    project_root: Path,
    *,
    expected_authoring_base_commit: str,
) -> None:
    """Validate the prepared record and prove the operational boundary closed."""

    attempt.require()
    source.require()
    if attempt.source != source:
        raise ConsumptionAttemptError("attempt source differs from verified source")
    if attempt.authoring_base_commit != expected_authoring_base_commit:
        raise ConsumptionAttemptError("expected authoring base commit differs")
    for relative in (
        Path(OUTPUT_ROOT),
        EXECUTION_LEASE_V1_RELATIVE,
        EXECUTION_LEASE_V2_RELATIVE,
        DURABLE_HOST_OUTCOME_RELATIVE,
    ):
        target = project_root / relative
        if target.exists() or target.is_symlink():
            raise ConsumptionAttemptError(
                f"runtime boundary path already exists: {relative.as_posix()}"
            )
