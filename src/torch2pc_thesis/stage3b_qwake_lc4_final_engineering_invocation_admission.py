"""Pure fail-closed schema for final QW-LC4-E invocation admission.

This module validates exact frozen source identities and an authored admission
record. It does not import the runtime entrypoint, inspect an image, create a
lease, write a host outcome, create an output root, or start a child process.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Final, cast

FINAL_ENGINEERING_INVOCATION_ADMISSION_ID: Final = (
    "stage3b-qwake-lc4-e-final-engineering-invocation-admission-v1"
)
FINAL_ENGINEERING_INVOCATION_ADMISSION_STATUS: Final = (
    "final_engineering_invocation_admission_authored_execution_closed"
)
FINAL_ENGINEERING_INVOCATION_SCOPE_ID: Final = (
    "stage3b-qwake-lc4-e-final-engineering-invocation-admission-"
    "authoring-scope-freeze-v1"
)
SCOPE_FREEZE_MERGE_COMMIT: Final = (
    "5ee7d33b2d6a9092b2db473040b92ad8cda7e08f"
)
SCOPE_FREEZE_PR_HEAD: Final = (
    "ec93a3f5f67a7a5a9cae2ed6d0640810d982e42c"
)
SCOPE_FREEZE_PR_NUMBER: Final = 168
SCOPE_FREEZE_MERGED_AT_UTC: Final = "2026-08-03T04:00:13Z"
FROZEN_TORCH2PC_COMMIT: Final = (
    "b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4"
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
    "stage3b-qwake-lc4-e-final-engineering-invocation-admission-"
    "authoring-scope-freeze-v1"
)
TRANSITION_PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-post-acknowledgement-transition-v1"
)
ACKNOWLEDGEMENT_PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-final-execution-acknowledgement-materialization-"
    "invocation-operation-callsite-execution-evidence-v1"
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
    TRANSITION_PACKAGE_RELATIVE: frozenset({"SHA256SUMS", "transition.json"}),
    ACKNOWLEDGEMENT_PACKAGE_RELATIVE: frozenset(
        {
            "SHA256SUMS",
            "authorization-consumption-attempt-001.json",
            "final-execution-acknowledgement.json",
            "source-identities.json",
            "verification.json",
        }
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
    SCOPE_PACKAGE_RELATIVE / "SHA256SUMS": (
        "c5ae4e35e87c6607f8c7c9ee6fe4c29e72206520cb5a154cbbb0bb0c82d8c3fc"
    ),
    SCOPE_PACKAGE_RELATIVE / "scope.json": (
        "bdfedbc1c0fca9859f90cb14390f1390e97440ff85db2a9786998fbe4df3ff61"
    ),
    TRANSITION_PACKAGE_RELATIVE / "SHA256SUMS": (
        "099625a6ca0412aa4518dd759bd615249a89f35b2e422b69d93515795f6ef50d"
    ),
    TRANSITION_PACKAGE_RELATIVE / "transition.json": (
        "a11e61e36cbd2b39719797d1d69135767aa37c625ccfe686efb92f1cb9827540"
    ),
    ACKNOWLEDGEMENT_PACKAGE_RELATIVE / "SHA256SUMS": (
        "c9606b3dc900d962153ea23451dcea93e76fc2a53b02aefb7c1d5b4e34d78138"
    ),
    ACKNOWLEDGEMENT_PACKAGE_RELATIVE / "final-execution-acknowledgement.json": (
        "8794d5c546034f06f482576eb4f7adf8ba9b3910788277cc5bbf0df6f8cf5026"
    ),
    ACKNOWLEDGEMENT_PACKAGE_RELATIVE / "verification.json": (
        "86ff355f40ef846b5926ba3e74cca1139b31b5d7c644379353d344b1b6f76124"
    ),
    PERSISTENT_CHAIN_PACKAGE_RELATIVE / "SHA256SUMS": (
        "ad5e0b84d88a3e830986448ff9ee7ebeb46bdd03a5e85202471e93968a6de24f"
    ),
    PERSISTENT_CHAIN_PACKAGE_RELATIVE / "implementation.json": (
        "fdbad25b58c995ec7b1db7f6d292e3185b93352b4234cee9f6f52a05229c8473"
    ),
    Path("src/torch2pc_thesis/stage3b_qwake_lc4_persistent_evidence_chain_v2.py"): (
        "96bc321bdc101038671ca33a693fef553c5528e182512520596cce6e446f8d20"
    ),
    Path(
        "src/torch2pc_thesis/"
        "stage3b_qwake_lc4_persistent_evidence_chain_v2_implementation.py"
    ): "04df58a67b4743717b80407c9ea931ef96dbcb1c143d5925dfbcf4bc9e8f5e11",
    WIRING_PACKAGE_RELATIVE / "SHA256SUMS": (
        "89406036c617de7875c01375c67d5b1d317528307353d51975cfb3b67797be94"
    ),
    WIRING_PACKAGE_RELATIVE / "wiring.json": (
        "60199510764aa4827bfb2deac69675b7d5d79e7209fa8f0aa53ba8d79a5c4ff3"
    ),
    Path(RUNTIME_ENTRYPOINT_MODULE): (
        "9b665d785caa6550191b90df9795abe1d3ee2b52e52536cfa3aaa12f56e574cd"
    ),
}

_COMMIT_PATTERN: Final = re.compile(r"^[0-9a-f]{40}$")
_SHA256_PATTERN: Final = re.compile(r"^sha256:[0-9a-f]{64}$")
_UTC_PATTERN: Final = re.compile(r"^20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")

__all__ = [
    "ACKNOWLEDGEMENT_PACKAGE_RELATIVE",
    "DURABLE_HOST_OUTCOME_RELATIVE",
    "EXECUTION_LEASE_V1_RELATIVE",
    "EXECUTION_LEASE_V2_RELATIVE",
    "FINAL_ENGINEERING_INVOCATION_ADMISSION_ID",
    "FINAL_ENGINEERING_INVOCATION_ADMISSION_STATUS",
    "FINAL_ENGINEERING_INVOCATION_SCOPE_ID",
    "FROZEN_TORCH2PC_COMMIT",
    "FinalEngineeringInvocationAdmission",
    "FinalEngineeringInvocationAdmissionError",
    "FinalEngineeringInvocationBoundary",
    "FinalEngineeringInvocationContract",
    "FinalEngineeringInvocationGates",
    "FinalEngineeringInvocationSource",
    "IMAGE_REPO_DIGEST",
    "OUTPUT_ROOT",
    "RUNTIME_ENTRYPOINT",
    "RUNTIME_ENTRYPOINT_MODULE",
    "SCOPE_FREEZE_MERGE_COMMIT",
    "SCOPE_FREEZE_MERGED_AT_UTC",
    "SCOPE_FREEZE_PR_HEAD",
    "SCOPE_FREEZE_PR_NUMBER",
    "build_final_engineering_invocation_admission",
    "canonical_json",
    "load_final_engineering_invocation_admission",
    "sha256_object",
    "validate_final_engineering_invocation_admission",
    "verify_final_engineering_invocation_sources",
]


class FinalEngineeringInvocationAdmissionError(RuntimeError):
    """Raised when final invocation admission validation fails closed."""


@dataclass(frozen=True)
class FinalEngineeringInvocationSource:
    """Exact identities inherited from the sealed authoring scope."""

    scope_id: str
    scope_freeze_merge_commit: str
    scope_freeze_pr_head: str
    scope_freeze_pr_number: int
    scope_freeze_merged_at_utc: str
    torch2pc_commit: str
    scope_registry_sha256: str
    scope_file_sha256: str
    transition_registry_sha256: str
    transition_file_sha256: str
    acknowledgement_registry_sha256: str
    acknowledgement_file_sha256: str
    acknowledgement_verification_sha256: str
    persistent_chain_registry_sha256: str
    persistent_chain_implementation_sha256: str
    wiring_registry_sha256: str
    wiring_file_sha256: str
    runtime_entrypoint_module_sha256: str

    def require(self) -> None:
        expected = expected_source_identity()
        if self != expected:
            raise FinalEngineeringInvocationAdmissionError(
                "admission source identities differ from the frozen scope"
            )


@dataclass(frozen=True)
class FinalEngineeringInvocationContract:
    """Prospective single-attempt contract; it is not an authorization."""

    image_repo_digest: str
    runtime_entrypoint_module: str
    runtime_entrypoint: str
    output_root: str
    execution_lease_v1_relative: str
    execution_lease_v2_relative: str
    durable_host_outcome_relative: str
    invocation_limit: int
    distinct_new_authorization_required: bool
    historical_engineering_authorization_reuse_forbidden: bool
    acknowledgement_authorization_reuse_forbidden: bool
    post_merge_verification_required_before_authorization: bool
    atomic_authorization_consumption_with_attempt_start_and_lease_v2: bool
    retry_after_consumption_forbidden: bool
    retry_after_lease_creation_forbidden: bool
    retry_after_unknown_outcome_forbidden: bool
    persistent_lease_v2_required_before_entrypoint: bool
    durable_host_outcome_required_for_every_terminal_class: bool
    direct_lower_host_invoker_call_forbidden: bool
    direct_historical_runtime_operation_call_forbidden: bool
    direct_docker_call_forbidden: bool
    subprocess_popen_direct_call_forbidden: bool
    verifier_runtime_entrypoint_import_forbidden: bool
    negative_tests_temporary_repositories_only: bool

    def require(self) -> None:
        if self != expected_contract():
            raise FinalEngineeringInvocationAdmissionError(
                "admission contract differs from the frozen scope"
            )


@dataclass(frozen=True)
class FinalEngineeringInvocationBoundary:
    """Observed closed boundary at admission-authoring time."""

    output_root_absent: bool
    execution_lease_v1_absent: bool
    execution_lease_v2_absent: bool
    durable_host_outcome_absent: bool
    authorization_record_present: bool
    authorization_issued: bool
    authorization_consumed: bool
    operator_phrase_reserved: bool
    invocation_command_materialized: bool
    image_inspection_performed: bool
    child_process_created: bool
    docker_run_performed: bool
    model_code_invoked: bool
    runtime_output_present: bool

    def require(self) -> None:
        if self != expected_boundary():
            raise FinalEngineeringInvocationAdmissionError(
                "admission boundary is not closed"
            )


@dataclass(frozen=True)
class FinalEngineeringInvocationGates:
    """Repository gates after authoring the admission record."""

    final_engineering_invocation_admission_authoring_scope_frozen: bool
    final_engineering_invocation_admission_authored: bool
    final_engineering_invocation_admission_record_present: bool
    final_engineering_invocation_authorization_issued: bool
    final_engineering_invocation_authorization_consumed: bool
    final_engineering_invocation_permitted: bool
    final_engineering_invocation_started: bool
    final_engineering_invocation_performed: bool
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
            raise FinalEngineeringInvocationAdmissionError(
                "admission gates differ from the closed authoring state"
            )


@dataclass(frozen=True)
class FinalEngineeringInvocationAdmission:
    """Canonical authored record for a future separately authorized attempt."""

    schema_version: int
    admission_id: str
    admission_sha256: str
    status: str
    authored_at_utc: str
    authoring_base_commit: str
    source: FinalEngineeringInvocationSource
    contract: FinalEngineeringInvocationContract
    boundary: FinalEngineeringInvocationBoundary
    gates: FinalEngineeringInvocationGates
    next_slice: str
    post_merge_next_slice: str

    def payload_without_digest(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("admission_sha256")
        return payload

    def canonical_json(self) -> str:
        return canonical_json(asdict(self)) + "\n"

    def require(self) -> None:
        if self.schema_version != 1:
            raise FinalEngineeringInvocationAdmissionError(
                "unexpected admission schema version"
            )
        if self.admission_id != FINAL_ENGINEERING_INVOCATION_ADMISSION_ID:
            raise FinalEngineeringInvocationAdmissionError(
                "unexpected admission id"
            )
        if self.status != FINAL_ENGINEERING_INVOCATION_ADMISSION_STATUS:
            raise FinalEngineeringInvocationAdmissionError(
                "unexpected admission status"
            )
        if not _UTC_PATTERN.fullmatch(self.authored_at_utc):
            raise FinalEngineeringInvocationAdmissionError(
                "admission authoring timestamp is not canonical UTC"
            )
        if self.authoring_base_commit != SCOPE_FREEZE_MERGE_COMMIT:
            raise FinalEngineeringInvocationAdmissionError(
                "admission authoring base commit differs"
            )
        if not _COMMIT_PATTERN.fullmatch(self.authoring_base_commit):
            raise FinalEngineeringInvocationAdmissionError(
                "admission authoring base commit is malformed"
            )
        if not _SHA256_PATTERN.fullmatch(self.admission_sha256):
            raise FinalEngineeringInvocationAdmissionError(
                "admission semantic digest is malformed"
            )
        if self.admission_sha256 != sha256_object(
            self.payload_without_digest()
        ):
            raise FinalEngineeringInvocationAdmissionError(
                "admission semantic digest differs"
            )
        self.source.require()
        self.contract.require()
        self.boundary.require()
        self.gates.require()
        if self.next_slice != (
            "QW-LC4-E-final-engineering-invocation-admission-authoring-commit"
        ):
            raise FinalEngineeringInvocationAdmissionError(
                "unexpected admission next slice"
            )
        if self.post_merge_next_slice != (
            "QW-LC4-E-final-engineering-invocation-admission-repository-seal"
        ):
            raise FinalEngineeringInvocationAdmissionError(
                "unexpected admission post-merge slice"
            )


def canonical_json(value: Mapping[str, Any] | dict[str, Any]) -> str:
    """Return deterministic compact JSON without a trailing newline."""

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def sha256_object(value: Mapping[str, Any] | dict[str, Any]) -> str:
    """Return a prefixed SHA-256 over canonical JSON bytes."""

    digest = hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def expected_source_identity() -> FinalEngineeringInvocationSource:
    return FinalEngineeringInvocationSource(
        scope_id=FINAL_ENGINEERING_INVOCATION_SCOPE_ID,
        scope_freeze_merge_commit=SCOPE_FREEZE_MERGE_COMMIT,
        scope_freeze_pr_head=SCOPE_FREEZE_PR_HEAD,
        scope_freeze_pr_number=SCOPE_FREEZE_PR_NUMBER,
        scope_freeze_merged_at_utc=SCOPE_FREEZE_MERGED_AT_UTC,
        torch2pc_commit=FROZEN_TORCH2PC_COMMIT,
        scope_registry_sha256=(
            "sha256:"
            "c5ae4e35e87c6607f8c7c9ee6fe4c29e72206520cb5a154cbbb0bb0c82d8c3fc"
        ),
        scope_file_sha256=(
            "sha256:"
            "bdfedbc1c0fca9859f90cb14390f1390e97440ff85db2a9786998fbe4df3ff61"
        ),
        transition_registry_sha256=(
            "sha256:"
            "099625a6ca0412aa4518dd759bd615249a89f35b2e422b69d93515795f6ef50d"
        ),
        transition_file_sha256=(
            "sha256:"
            "a11e61e36cbd2b39719797d1d69135767aa37c625ccfe686efb92f1cb9827540"
        ),
        acknowledgement_registry_sha256=(
            "sha256:"
            "c9606b3dc900d962153ea23451dcea93e76fc2a53b02aefb7c1d5b4e34d78138"
        ),
        acknowledgement_file_sha256=(
            "sha256:"
            "8794d5c546034f06f482576eb4f7adf8ba9b3910788277cc5bbf0df6f8cf5026"
        ),
        acknowledgement_verification_sha256=(
            "sha256:"
            "86ff355f40ef846b5926ba3e74cca1139b31b5d7c644379353d344b1b6f76124"
        ),
        persistent_chain_registry_sha256=(
            "sha256:"
            "ad5e0b84d88a3e830986448ff9ee7ebeb46bdd03a5e85202471e93968a6de24f"
        ),
        persistent_chain_implementation_sha256=(
            "sha256:"
            "fdbad25b58c995ec7b1db7f6d292e3185b93352b4234cee9f6f52a05229c8473"
        ),
        wiring_registry_sha256=(
            "sha256:"
            "89406036c617de7875c01375c67d5b1d317528307353d51975cfb3b67797be94"
        ),
        wiring_file_sha256=(
            "sha256:"
            "60199510764aa4827bfb2deac69675b7d5d79e7209fa8f0aa53ba8d79a5c4ff3"
        ),
        runtime_entrypoint_module_sha256=(
            "sha256:"
            "9b665d785caa6550191b90df9795abe1d3ee2b52e52536cfa3aaa12f56e574cd"
        ),
    )


def expected_contract() -> FinalEngineeringInvocationContract:
    return FinalEngineeringInvocationContract(
        image_repo_digest=IMAGE_REPO_DIGEST,
        runtime_entrypoint_module=RUNTIME_ENTRYPOINT_MODULE,
        runtime_entrypoint=RUNTIME_ENTRYPOINT,
        output_root=OUTPUT_ROOT,
        execution_lease_v1_relative=EXECUTION_LEASE_V1_RELATIVE.as_posix(),
        execution_lease_v2_relative=EXECUTION_LEASE_V2_RELATIVE.as_posix(),
        durable_host_outcome_relative=DURABLE_HOST_OUTCOME_RELATIVE.as_posix(),
        invocation_limit=1,
        distinct_new_authorization_required=True,
        historical_engineering_authorization_reuse_forbidden=True,
        acknowledgement_authorization_reuse_forbidden=True,
        post_merge_verification_required_before_authorization=True,
        atomic_authorization_consumption_with_attempt_start_and_lease_v2=True,
        retry_after_consumption_forbidden=True,
        retry_after_lease_creation_forbidden=True,
        retry_after_unknown_outcome_forbidden=True,
        persistent_lease_v2_required_before_entrypoint=True,
        durable_host_outcome_required_for_every_terminal_class=True,
        direct_lower_host_invoker_call_forbidden=True,
        direct_historical_runtime_operation_call_forbidden=True,
        direct_docker_call_forbidden=True,
        subprocess_popen_direct_call_forbidden=True,
        verifier_runtime_entrypoint_import_forbidden=True,
        negative_tests_temporary_repositories_only=True,
    )


def expected_boundary() -> FinalEngineeringInvocationBoundary:
    return FinalEngineeringInvocationBoundary(
        output_root_absent=True,
        execution_lease_v1_absent=True,
        execution_lease_v2_absent=True,
        durable_host_outcome_absent=True,
        authorization_record_present=False,
        authorization_issued=False,
        authorization_consumed=False,
        operator_phrase_reserved=False,
        invocation_command_materialized=False,
        image_inspection_performed=False,
        child_process_created=False,
        docker_run_performed=False,
        model_code_invoked=False,
        runtime_output_present=False,
    )


def expected_gates() -> FinalEngineeringInvocationGates:
    return FinalEngineeringInvocationGates(
        final_engineering_invocation_admission_authoring_scope_frozen=True,
        final_engineering_invocation_admission_authored=True,
        final_engineering_invocation_admission_record_present=True,
        final_engineering_invocation_authorization_issued=False,
        final_engineering_invocation_authorization_consumed=False,
        final_engineering_invocation_permitted=False,
        final_engineering_invocation_started=False,
        final_engineering_invocation_performed=False,
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


def build_final_engineering_invocation_admission(
    *,
    authored_at_utc: str,
    authoring_base_commit: str,
) -> FinalEngineeringInvocationAdmission:
    """Build the exact authored, non-authorized admission record."""

    candidate = FinalEngineeringInvocationAdmission(
        schema_version=1,
        admission_id=FINAL_ENGINEERING_INVOCATION_ADMISSION_ID,
        admission_sha256="sha256:" + "0" * 64,
        status=FINAL_ENGINEERING_INVOCATION_ADMISSION_STATUS,
        authored_at_utc=authored_at_utc,
        authoring_base_commit=authoring_base_commit,
        source=expected_source_identity(),
        contract=expected_contract(),
        boundary=expected_boundary(),
        gates=expected_gates(),
        next_slice=(
            "QW-LC4-E-final-engineering-invocation-admission-authoring-commit"
        ),
        post_merge_next_slice=(
            "QW-LC4-E-final-engineering-invocation-admission-repository-seal"
        ),
    )
    candidate = replace(
        candidate,
        admission_sha256=sha256_object(candidate.payload_without_digest()),
    )
    candidate.require()
    return candidate


def _load_mapping(path: Path) -> Mapping[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FinalEngineeringInvocationAdmissionError(
            f"cannot load JSON: {path.as_posix()}"
        ) from exc
    if not isinstance(raw, Mapping):
        raise FinalEngineeringInvocationAdmissionError(
            f"JSON object required: {path.as_posix()}"
        )
    return cast(Mapping[str, Any], raw)


def _require_keys(
    value: Mapping[str, Any],
    expected: frozenset[str],
    *,
    label: str,
) -> None:
    if frozenset(value) != expected:
        raise FinalEngineeringInvocationAdmissionError(
            f"{label} keys differ"
        )


def load_final_engineering_invocation_admission(
    path: Path,
) -> FinalEngineeringInvocationAdmission:
    """Load and validate a canonical admission JSON file."""

    payload = _load_mapping(path)
    _require_keys(
        payload,
        frozenset(
            {
                "schema_version",
                "admission_id",
                "admission_sha256",
                "status",
                "authored_at_utc",
                "authoring_base_commit",
                "source",
                "contract",
                "boundary",
                "gates",
                "next_slice",
                "post_merge_next_slice",
            }
        ),
        label="admission",
    )

    source_payload = cast(Mapping[str, Any], payload["source"])
    contract_payload = cast(Mapping[str, Any], payload["contract"])
    boundary_payload = cast(Mapping[str, Any], payload["boundary"])
    gates_payload = cast(Mapping[str, Any], payload["gates"])

    try:
        admission = FinalEngineeringInvocationAdmission(
            schema_version=int(payload["schema_version"]),
            admission_id=str(payload["admission_id"]),
            admission_sha256=str(payload["admission_sha256"]),
            status=str(payload["status"]),
            authored_at_utc=str(payload["authored_at_utc"]),
            authoring_base_commit=str(payload["authoring_base_commit"]),
            source=FinalEngineeringInvocationSource(**source_payload),
            contract=FinalEngineeringInvocationContract(**contract_payload),
            boundary=FinalEngineeringInvocationBoundary(**boundary_payload),
            gates=FinalEngineeringInvocationGates(**gates_payload),
            next_slice=str(payload["next_slice"]),
            post_merge_next_slice=str(payload["post_merge_next_slice"]),
        )
    except (TypeError, ValueError, KeyError) as exc:
        raise FinalEngineeringInvocationAdmissionError(
            "admission object cannot be constructed"
        ) from exc

    admission.require()
    if path.read_text(encoding="utf-8") != admission.canonical_json():
        raise FinalEngineeringInvocationAdmissionError(
            "admission JSON bytes are not canonical"
        )
    return admission


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _verify_registry(package_root: Path, expected_files: frozenset[str]) -> None:
    registry = package_root / "SHA256SUMS"
    observed: set[str] = set()
    for raw_line in registry.read_text(encoding="utf-8").splitlines():
        if not raw_line:
            continue
        digest, relative = raw_line.split("  ", 1)
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise FinalEngineeringInvocationAdmissionError(
                "package registry digest is malformed"
            )
        if relative in observed or relative == "SHA256SUMS":
            raise FinalEngineeringInvocationAdmissionError(
                "package registry path is invalid"
            )
        target = package_root / relative
        if target.parent != package_root or not target.is_file() or target.is_symlink():
            raise FinalEngineeringInvocationAdmissionError(
                "package registry target is invalid"
            )
        if _sha256_file(target) != digest:
            raise FinalEngineeringInvocationAdmissionError(
                "package registry digest differs"
            )
        observed.add(relative)
    if observed != set(expected_files - {"SHA256SUMS"}):
        raise FinalEngineeringInvocationAdmissionError(
            "package registry scope differs"
        )


def _verify_package(
    project_root: Path,
    relative: Path,
    expected_files: frozenset[str],
) -> None:
    package_root = project_root / relative
    if not package_root.is_dir() or package_root.is_symlink():
        raise FinalEngineeringInvocationAdmissionError(
            f"source package missing: {relative.as_posix()}"
        )
    entries = tuple(package_root.iterdir())
    files = {entry.name for entry in entries if entry.is_file() and not entry.is_symlink()}
    if files != set(expected_files):
        raise FinalEngineeringInvocationAdmissionError(
            f"source package scope differs: {relative.as_posix()}"
        )
    if any(entry.is_dir() or entry.is_symlink() for entry in entries):
        raise FinalEngineeringInvocationAdmissionError(
            f"source package contains non-regular entry: {relative.as_posix()}"
        )
    _verify_registry(package_root, expected_files)


def _verify_exact_files(project_root: Path) -> None:
    for relative, expected_digest in _EXPECTED_FILE_SHA256.items():
        path = project_root / relative
        if not path.is_file() or path.is_symlink():
            raise FinalEngineeringInvocationAdmissionError(
                f"exact source file missing: {relative.as_posix()}"
            )
        if _sha256_file(path) != expected_digest:
            raise FinalEngineeringInvocationAdmissionError(
                f"exact source file digest differs: {relative.as_posix()}"
            )


def _verify_source_semantics(project_root: Path) -> None:
    scope = _load_mapping(project_root / SCOPE_PACKAGE_RELATIVE / "scope.json")
    scope_gates = cast(Mapping[str, Any], scope["gates"])
    if scope["scope_id"] != FINAL_ENGINEERING_INVOCATION_SCOPE_ID:
        raise FinalEngineeringInvocationAdmissionError("scope id differs")
    if scope_gates["final_engineering_invocation_admission_authoring_scope_frozen"] is not True:
        raise FinalEngineeringInvocationAdmissionError("scope freeze is not complete")
    if any(
        scope_gates[name] is not False
        for name in (
            "final_engineering_invocation_admission_authored",
            "final_engineering_invocation_admission_record_present",
            "final_engineering_invocation_authorization_issued",
            "final_engineering_invocation_authorization_consumed",
            "final_engineering_invocation_permitted",
            "final_engineering_invocation_started",
            "final_engineering_invocation_performed",
            "execution_lease_v1_present",
            "execution_lease_v2_present",
            "durable_host_outcome_present",
            "runtime_output_present",
            "qw5_transition_permitted",
            "qw5_scientific_image_freeze_open",
            "local_compute_execution_open",
        )
    ):
        raise FinalEngineeringInvocationAdmissionError(
            "scope source contains an open execution gate"
        )

    transition = _load_mapping(
        project_root / TRANSITION_PACKAGE_RELATIVE / "transition.json"
    )
    transition_gates = cast(Mapping[str, Any], transition["gates"])
    if transition_gates["acknowledgement_line_complete"] is not True:
        raise FinalEngineeringInvocationAdmissionError(
            "acknowledgement transition is incomplete"
        )
    if transition_gates["acknowledgement_authorization_consumed"] is not True:
        raise FinalEngineeringInvocationAdmissionError(
            "historical acknowledgement authorization is not consumed"
        )
    if transition_gates["acknowledgement_callsite_reinvocation_forbidden"] is not True:
        raise FinalEngineeringInvocationAdmissionError(
            "historical acknowledgement reinvocation is not forbidden"
        )
    if transition_gates["acknowledgement_retry_permitted"] is not False:
        raise FinalEngineeringInvocationAdmissionError(
            "historical acknowledgement retry remains open"
        )

    verification = _load_mapping(
        project_root / ACKNOWLEDGEMENT_PACKAGE_RELATIVE / "verification.json"
    )
    if verification["authorization_consumed"] is not True:
        raise FinalEngineeringInvocationAdmissionError(
            "historical acknowledgement consumption is not verified"
        )
    if verification["execution_gate_reinvocation_forbidden"] is not True:
        raise FinalEngineeringInvocationAdmissionError(
            "historical execution gate reinvocation is not forbidden"
        )
    if verification["retry_permitted"] is not False:
        raise FinalEngineeringInvocationAdmissionError(
            "historical acknowledgement retry is not closed"
        )
    if any(
        verification[name] is not False
        for name in (
            "execution_lease_v1_present",
            "execution_lease_v2_present",
            "durable_host_outcome_present",
            "runtime_output_present",
        )
    ):
        raise FinalEngineeringInvocationAdmissionError(
            "historical acknowledgement evidence contains runtime output"
        )

    chain = _load_mapping(
        project_root / PERSISTENT_CHAIN_PACKAGE_RELATIVE / "implementation.json"
    )
    if chain["persistent_lease_v2_implementation_present"] is not True:
        raise FinalEngineeringInvocationAdmissionError(
            "persistent lease v2 implementation is absent"
        )
    if chain["durable_outcome_writer_implemented"] is not True:
        raise FinalEngineeringInvocationAdmissionError(
            "durable host outcome implementation is absent"
        )
    if chain["runtime_execution_performed"] is not False:
        raise FinalEngineeringInvocationAdmissionError(
            "persistent evidence implementation records execution"
        )

    wiring = _load_mapping(project_root / WIRING_PACKAGE_RELATIVE / "wiring.json")
    if wiring["lease_bound_host_invoker_enforced"] is not True:
        raise FinalEngineeringInvocationAdmissionError(
            "lease-bound host invoker is not enforced"
        )
    if wiring["persisted_lease_v2_required"] is not True:
        raise FinalEngineeringInvocationAdmissionError(
            "wiring does not require persisted lease v2"
        )
    if wiring["repository_direct_lower_level_call_forbidden"] is not True:
        raise FinalEngineeringInvocationAdmissionError(
            "direct lower-level host call is not forbidden"
        )
    if any(
        wiring[name] is not False
        for name in (
            "authorization_consumed",
            "docker_run_performed",
            "durable_host_outcome_present",
            "execution_lease_materialized",
            "image_inspection_performed",
            "invocation_command_materialized",
            "one_shot_engineering_invocation_permitted",
            "runtime_execution_started",
            "runtime_execution_performed",
            "local_compute_execution_open",
        )
    ):
        raise FinalEngineeringInvocationAdmissionError(
            "wiring source contains a runtime effect"
        )


def verify_final_engineering_invocation_sources(
    project_root: Path,
) -> FinalEngineeringInvocationSource:
    """Verify exact source packages without importing runtime code."""

    for relative, expected_files in _EXPECTED_PACKAGE_FILES.items():
        _verify_package(project_root, relative, expected_files)
    _verify_exact_files(project_root)
    _verify_source_semantics(project_root)
    return expected_source_identity()


def _boundary_path_present(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def validate_final_engineering_invocation_admission(
    admission: FinalEngineeringInvocationAdmission,
    source: FinalEngineeringInvocationSource,
    project_root: Path,
    *,
    expected_authoring_base_commit: str,
) -> None:
    """Validate the record and require all runtime boundary paths absent."""

    admission.require()
    source.require()
    if admission.source != source:
        raise FinalEngineeringInvocationAdmissionError(
            "record source differs from verified source"
        )
    if expected_authoring_base_commit != SCOPE_FREEZE_MERGE_COMMIT:
        raise FinalEngineeringInvocationAdmissionError(
            "expected authoring base commit differs"
        )
    if admission.authoring_base_commit != expected_authoring_base_commit:
        raise FinalEngineeringInvocationAdmissionError(
            "record authoring base commit differs"
        )

    boundary_paths = (
        Path(OUTPUT_ROOT),
        EXECUTION_LEASE_V1_RELATIVE,
        EXECUTION_LEASE_V2_RELATIVE,
        DURABLE_HOST_OUTCOME_RELATIVE,
    )
    for relative in boundary_paths:
        if _boundary_path_present(project_root / relative):
            raise FinalEngineeringInvocationAdmissionError(
                f"runtime boundary path already exists: {relative.as_posix()}"
            )
