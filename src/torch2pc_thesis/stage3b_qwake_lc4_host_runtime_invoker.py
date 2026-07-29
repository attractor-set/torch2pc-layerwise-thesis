"""Pure authoring contract for the QW-LC4-E host runtime invoker.

The module binds the merged invocation-wrapper implementation to one future
host launch protocol.  It defines ordering, retry, signal, timeout, output,
and durable lease semantics as data.  It does not import subprocess, inspect
Docker, execute an argv vector, create a lease, start the runtime, consume the
one-shot authorization, write results, or publish evidence.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Final, cast

HOST_RUNTIME_INVOKER_CONTRACT_ID: Final = (
    "stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-contract-v1"
)
HOST_RUNTIME_INVOKER_CONTRACT_STATUS: Final = (
    "host_runtime_invoker_contract_authored_execution_path_absent"
)
AUTHORING_BASE_COMMIT: Final = (
    "be6486a9e3670343132f2c863a5a0cd5969ee9f6"
)
WRAPPER_IMPLEMENTATION_HEAD_COMMIT: Final = (
    "f8c1465ef326cb2dbe752c2900ab371a8b669284"
)
WRAPPER_IMPLEMENTATION_MERGE_COMMIT: Final = AUTHORING_BASE_COMMIT
WRAPPER_IMPLEMENTATION_MERGED_AT_UTC: Final = "2026-07-29T04:39:19Z"
WRAPPER_IMPLEMENTATION_PR_NUMBER: Final = 134
WRAPPER_IMPLEMENTATION_ID: Final = (
    "stage3b-qwake-lc4-e-one-shot-host-invocation-wrapper-implementation-v1"
)
WRAPPER_IMPLEMENTATION_MODULE_SHA256: Final = (
    "sha256:8f72b41538f3d66b5aaa88430a42406334ebb49ec39e462f16ae9117540426af"
)
WRAPPER_IMPLEMENTATION_VERIFIER_SHA256: Final = (
    "sha256:5ffa979432c32ac9ad019ed68aacae6f612c1c7bbab653237ddd58539a616dd1"
)
WRAPPER_IMPLEMENTATION_TEST_SHA256: Final = (
    "sha256:90a65f3e09b5317042fb861b786ecd1f2ccafb54078e28207559faa67ccc8a9b"
)
INVOCATION_WRAPPER_CONTRACT_ID: Final = (
    "stage3b-qwake-lc4-e-one-shot-host-invocation-wrapper-contract-v1"
)
INVOCATION_WRAPPER_CONTRACT_SHA256: Final = (
    "sha256:4c4cb163e8c2a33b0563cc3b9cb873a87acf8ea75bb3e807d157d51c5a4dd29b"
)
INVOCATION_AUTHORIZATION_ID: Final = (
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-authorization-v1"
)
INVOCATION_AUTHORIZATION_SHA256: Final = (
    "sha256:0a60dacc1bfd5073cf52d76f2ec33ae54f00899aad9877d44607199659fda75a"
)
IMAGE_REPO_DIGEST: Final = (
    "torch2pc-layerwise-thesis@"
    "sha256:7da92b8f77f6dc37d42db832c5613ef6149dc488adc5b66465faa33e48ca021d"
)
AUTHORIZED_OUTPUT_ROOT: Final = (
    "results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001"
)
EXECUTION_LEASE_RELATIVE: Final = (
    AUTHORIZED_OUTPUT_ROOT + ".execution-lease.json"
)
WRAPPER_IMPLEMENTATION_ROOT_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-one-shot-invocation-wrapper-implementation-v1"
)
WRAPPER_IMPLEMENTATION_RELATIVE: Final = (
    WRAPPER_IMPLEMENTATION_ROOT_RELATIVE / "implementation.json"
)
WRAPPER_IMPLEMENTATION_REGISTRY_RELATIVE: Final = (
    WRAPPER_IMPLEMENTATION_ROOT_RELATIVE / "SHA256SUMS"
)
AUTHORIZATION_ROOT_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-authorization-v1"
)
AUTHORIZATION_RELATIVE: Final = AUTHORIZATION_ROOT_RELATIVE / "authorization.json"
AUTHORIZATION_REGISTRY_RELATIVE: Final = AUTHORIZATION_ROOT_RELATIVE / "SHA256SUMS"
WRAPPER_IMPLEMENTATION_MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_invocation_wrapper_implementation.py"
)
WRAPPER_IMPLEMENTATION_VERIFIER_RELATIVE: Final = Path(
    "scripts/verify_stage3b_qwake_lc4_invocation_wrapper_implementation.py"
)
WRAPPER_IMPLEMENTATION_TEST_RELATIVE: Final = Path(
    "tests/unit/test_stage3b_qwake_lc4_invocation_wrapper_implementation.py"
)
ONE_SHOT_ENTRYPOINT_RELATIVE: Final = Path(
    "scripts/run_stage3b_qwake_lc4_authorized_runtime.py"
)
EXECUTION_WRAPPER_IMPLEMENTATION_RELATIVE: Final = Path(
    "src/torch2pc_thesis/stage3b_qwake_lc4_execution_wrapper_implementation.py"
)
EXPECTED_ONE_SHOT_ENTRYPOINT_SHA256: Final = (
    "sha256:504c3e614e199789b25c8b1927d0a35b1b95e1f3a5411e42db794fc93782cc79"
)
EXPECTED_EXECUTION_WRAPPER_IMPLEMENTATION_SHA256: Final = (
    "sha256:43e114dfdb69fa54a993a98b2a487777c40168374e61c0949e5cf862d42f7d9f"
)
IMAGE_INSPECTION_TIMEOUT_SECONDS: Final = 30
RUNTIME_TIMEOUT_SECONDS: Final = 7200
TERMINATION_GRACE_SECONDS: Final = 30
STDOUT_CAPTURE_LIMIT_BYTES: Final = 1_048_576
STDERR_CAPTURE_LIMIT_BYTES: Final = 1_048_576
HOST_OBSERVATION_ARGV_PREFIX: Final = ("docker", "image", "inspect")
HOST_EXECUTION_ARGV_PREFIX: Final = ("docker", "run")
HOST_PRELAUNCH_SEQUENCE: Final = (
    "verify_exact_unconsumed_authorization",
    "verify_repository_effect_boundary_closed",
    "inspect_exact_local_immutable_image",
    "materialize_exact_canonical_argv_in_memory",
    "reinspect_image_immediately_before_spawn",
    "rematerialize_and_compare_argv_immediately_before_spawn",
    "recheck_lease_output_and_staging_absence",
)
CONTAINER_EXECUTION_SEQUENCE: Final = (
    "start_exact_container_argv_once",
    "container_entrypoint_claims_execution_lease_atomically",
    "container_entrypoint_revalidates_persistent_lease_and_frozen_admission",
    "container_entrypoint_executes_bounded_runtime_backend",
    "container_wrapper_promotes_complete_output_without_replace",
)
TERMINAL_OUTCOME_SEQUENCE: Final = (
    "capture_bounded_stdout_and_stderr",
    "classify_zero_nonzero_timeout_or_signal_outcome",
    "preserve_execution_lease_after_any_post_claim_failure",
    "forbid_automatic_retry_after_child_spawn",
)
FORWARDED_SIGNALS: Final = ("SIGINT", "SIGTERM")

__all__ = [
    "AUTHORING_BASE_COMMIT",
    "AUTHORIZED_OUTPUT_ROOT",
    "CONTAINER_EXECUTION_SEQUENCE",
    "EXECUTION_LEASE_RELATIVE",
    "FORWARDED_SIGNALS",
    "HOST_EXECUTION_ARGV_PREFIX",
    "HOST_OBSERVATION_ARGV_PREFIX",
    "HOST_PRELAUNCH_SEQUENCE",
    "HOST_RUNTIME_INVOKER_CONTRACT_ID",
    "HOST_RUNTIME_INVOKER_CONTRACT_STATUS",
    "HostRuntimeInvokerContract",
    "IMAGE_INSPECTION_TIMEOUT_SECONDS",
    "QWakeLC4HostRuntimeInvokerError",
    "RUNTIME_TIMEOUT_SECONDS",
    "STDERR_CAPTURE_LIMIT_BYTES",
    "STDOUT_CAPTURE_LIMIT_BYTES",
    "TERMINAL_OUTCOME_SEQUENCE",
    "TERMINATION_GRACE_SECONDS",
    "WRAPPER_IMPLEMENTATION_HEAD_COMMIT",
    "WRAPPER_IMPLEMENTATION_MERGE_COMMIT",
    "build_host_runtime_invoker_contract",
    "canonical_json",
    "load_host_runtime_invoker_contract",
    "sha256_object",
    "validate_host_runtime_invoker_contract",
    "verify_host_runtime_invoker_authoring_prerequisites",
]


class QWakeLC4HostRuntimeInvokerError(RuntimeError):
    """Raised when host-runtime-invoker authoring fails closed."""


def canonical_json(value: object) -> str:
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
    return "sha256:" + hashlib.sha256(
        canonical_json(value).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class HostRuntimeInvokerContract:
    """Pure future host-invoker protocol with every effect still closed."""

    schema_version: int
    contract_id: str
    status: str
    authoring_base_commit: str
    wrapper_implementation_head_commit: str
    wrapper_implementation_merge_commit: str
    wrapper_implementation_merged_at_utc: str
    wrapper_implementation_pr_number: int
    wrapper_implementation_id: str
    wrapper_implementation_module_sha256: str
    wrapper_implementation_verifier_sha256: str
    wrapper_implementation_test_sha256: str
    invocation_wrapper_contract_id: str
    invocation_wrapper_contract_sha256: str
    invocation_authorization_id: str
    invocation_authorization_sha256: str
    image_repo_digest: str
    authorized_output_root: str
    execution_lease_relative: str
    host_observation_argv_prefix: tuple[str, ...]
    host_execution_argv_prefix: tuple[str, ...]
    host_prelaunch_sequence: tuple[str, ...]
    container_execution_sequence: tuple[str, ...]
    terminal_outcome_sequence: tuple[str, ...]
    lease_claim_owner: str
    authorization_consumed_boundary: str
    runtime_started_boundary: str
    runtime_performed_boundary: str
    image_inspection_timeout_seconds: int
    runtime_timeout_seconds: int
    termination_grace_seconds: int
    stdout_capture_limit_bytes: int
    stderr_capture_limit_bytes: int
    forwarded_signals: tuple[str, ...]
    exact_argv_only: bool
    shell_interpretation_forbidden: bool
    environment_inheritance_forbidden: bool
    working_directory_override_forbidden: bool
    single_child_spawn_per_invoker_process: bool
    automatic_retry_after_spawn_forbidden: bool
    concurrent_runtime_effects_guarded_by_atomic_lease: bool
    host_execution_lease_write_forbidden: bool
    claim_and_execute_same_container_process_required: bool
    post_claim_revalidation_required: bool
    lease_persists_after_failure: bool
    output_promotion_without_replace_required: bool
    child_process_group_required: bool
    signal_forwarding_required: bool
    timeout_is_terminal: bool
    nonzero_return_code_is_terminal: bool
    bounded_output_capture_required: bool
    command_persistence_forbidden: bool
    host_log_persistence_forbidden: bool
    host_runtime_invoker_contract_present: bool
    host_runtime_invoker_present: bool
    host_runtime_invoker_executable: bool
    host_docker_run_implemented: bool
    branch_runtime_execution_permitted: bool
    execution_lease_materialized: bool
    authorization_consumed: bool
    runtime_execution_started: bool
    runtime_execution_performed: bool
    engineering_evidence_present: bool
    scientific_execution_open: bool
    test_dataset_access: bool
    publication_permitted: bool
    local_compute_execution_open: bool
    contract_sha256: str

    def require(self) -> None:
        exact: Mapping[str, object] = {
            "schema_version": 1,
            "contract_id": HOST_RUNTIME_INVOKER_CONTRACT_ID,
            "status": HOST_RUNTIME_INVOKER_CONTRACT_STATUS,
            "authoring_base_commit": AUTHORING_BASE_COMMIT,
            "wrapper_implementation_head_commit": (
                WRAPPER_IMPLEMENTATION_HEAD_COMMIT
            ),
            "wrapper_implementation_merge_commit": (
                WRAPPER_IMPLEMENTATION_MERGE_COMMIT
            ),
            "wrapper_implementation_merged_at_utc": (
                WRAPPER_IMPLEMENTATION_MERGED_AT_UTC
            ),
            "wrapper_implementation_pr_number": (
                WRAPPER_IMPLEMENTATION_PR_NUMBER
            ),
            "wrapper_implementation_id": WRAPPER_IMPLEMENTATION_ID,
            "wrapper_implementation_module_sha256": (
                WRAPPER_IMPLEMENTATION_MODULE_SHA256
            ),
            "wrapper_implementation_verifier_sha256": (
                WRAPPER_IMPLEMENTATION_VERIFIER_SHA256
            ),
            "wrapper_implementation_test_sha256": (
                WRAPPER_IMPLEMENTATION_TEST_SHA256
            ),
            "invocation_wrapper_contract_id": INVOCATION_WRAPPER_CONTRACT_ID,
            "invocation_wrapper_contract_sha256": (
                INVOCATION_WRAPPER_CONTRACT_SHA256
            ),
            "invocation_authorization_id": INVOCATION_AUTHORIZATION_ID,
            "invocation_authorization_sha256": (
                INVOCATION_AUTHORIZATION_SHA256
            ),
            "image_repo_digest": IMAGE_REPO_DIGEST,
            "authorized_output_root": AUTHORIZED_OUTPUT_ROOT,
            "execution_lease_relative": EXECUTION_LEASE_RELATIVE,
            "host_observation_argv_prefix": HOST_OBSERVATION_ARGV_PREFIX,
            "host_execution_argv_prefix": HOST_EXECUTION_ARGV_PREFIX,
            "host_prelaunch_sequence": HOST_PRELAUNCH_SEQUENCE,
            "container_execution_sequence": CONTAINER_EXECUTION_SEQUENCE,
            "terminal_outcome_sequence": TERMINAL_OUTCOME_SEQUENCE,
            "lease_claim_owner": (
                "container_entrypoint_same_process_as_runtime"
            ),
            "authorization_consumed_boundary": (
                "atomic_execution_lease_claim"
            ),
            "runtime_started_boundary": "bounded_backend_call_started",
            "runtime_performed_boundary": (
                "complete_output_promoted_without_replace"
            ),
            "image_inspection_timeout_seconds": (
                IMAGE_INSPECTION_TIMEOUT_SECONDS
            ),
            "runtime_timeout_seconds": RUNTIME_TIMEOUT_SECONDS,
            "termination_grace_seconds": TERMINATION_GRACE_SECONDS,
            "stdout_capture_limit_bytes": STDOUT_CAPTURE_LIMIT_BYTES,
            "stderr_capture_limit_bytes": STDERR_CAPTURE_LIMIT_BYTES,
            "forwarded_signals": FORWARDED_SIGNALS,
            "exact_argv_only": True,
            "shell_interpretation_forbidden": True,
            "environment_inheritance_forbidden": True,
            "working_directory_override_forbidden": True,
            "single_child_spawn_per_invoker_process": True,
            "automatic_retry_after_spawn_forbidden": True,
            "concurrent_runtime_effects_guarded_by_atomic_lease": True,
            "host_execution_lease_write_forbidden": True,
            "claim_and_execute_same_container_process_required": True,
            "post_claim_revalidation_required": True,
            "lease_persists_after_failure": True,
            "output_promotion_without_replace_required": True,
            "child_process_group_required": True,
            "signal_forwarding_required": True,
            "timeout_is_terminal": True,
            "nonzero_return_code_is_terminal": True,
            "bounded_output_capture_required": True,
            "command_persistence_forbidden": True,
            "host_log_persistence_forbidden": True,
            "host_runtime_invoker_contract_present": True,
            "host_runtime_invoker_present": False,
            "host_runtime_invoker_executable": False,
            "host_docker_run_implemented": False,
            "branch_runtime_execution_permitted": False,
            "execution_lease_materialized": False,
            "authorization_consumed": False,
            "runtime_execution_started": False,
            "runtime_execution_performed": False,
            "engineering_evidence_present": False,
            "scientific_execution_open": False,
            "test_dataset_access": False,
            "publication_permitted": False,
            "local_compute_execution_open": False,
        }
        for field_name, expected in exact.items():
            if getattr(self, field_name) != expected:
                raise QWakeLC4HostRuntimeInvokerError(
                    f"host-runtime-invoker contract differs: {field_name}"
                )
        for value, field_name in (
            (
                self.wrapper_implementation_module_sha256,
                "wrapper_implementation_module_sha256",
            ),
            (
                self.wrapper_implementation_verifier_sha256,
                "wrapper_implementation_verifier_sha256",
            ),
            (
                self.wrapper_implementation_test_sha256,
                "wrapper_implementation_test_sha256",
            ),
            (
                self.invocation_wrapper_contract_sha256,
                "invocation_wrapper_contract_sha256",
            ),
            (
                self.invocation_authorization_sha256,
                "invocation_authorization_sha256",
            ),
            (self.contract_sha256, "contract_sha256"),
        ):
            _require_sha256(value, field_name)
        if self.contract_sha256 != sha256_object(
            self._payload_without_digest()
        ):
            raise QWakeLC4HostRuntimeInvokerError(
                "host-runtime-invoker contract digest differs"
            )

    def _payload_without_digest(self) -> Mapping[str, object]:
        payload = asdict(self)
        payload.pop("contract_sha256")
        return cast(Mapping[str, object], payload)

    def canonical_json(self) -> str:
        return canonical_json(asdict(self))


def _effect_boundary(root: Path) -> None:
    lease = root / EXECUTION_LEASE_RELATIVE
    output = root / AUTHORIZED_OUTPUT_ROOT
    if lease.exists() or lease.is_symlink():
        raise QWakeLC4HostRuntimeInvokerError(
            "repository execution lease already exists"
        )
    if output.exists() or output.is_symlink():
        raise QWakeLC4HostRuntimeInvokerError(
            "repository runtime output already exists"
        )
    staging = tuple(output.parent.glob(f".{output.name}.staging-*"))
    if staging:
        raise QWakeLC4HostRuntimeInvokerError(
            "repository runtime staging tree already exists"
        )


def verify_host_runtime_invoker_authoring_prerequisites(
    project_root: Path,
) -> tuple[str, str]:
    """Verify merged wrapper implementation, authorization, and no effects."""

    root = project_root.expanduser().resolve()
    _effect_boundary(root)
    _verify_single_file_registry(
        root / WRAPPER_IMPLEMENTATION_REGISTRY_RELATIVE,
        root / WRAPPER_IMPLEMENTATION_ROOT_RELATIVE,
        "implementation.json",
    )
    implementation = _read_json_object(
        root / WRAPPER_IMPLEMENTATION_RELATIVE
    )
    source = _as_mapping(implementation.get("source"), "source")
    contracts = _as_mapping(
        implementation.get("contracts"), "contracts"
    )
    gates = _as_mapping(implementation.get("gates"), "gates")
    expected_implementation: Mapping[str, object] = {
        "implementation_id": WRAPPER_IMPLEMENTATION_ID,
        "status": (
            "image_inspection_and_command_materialization_implemented_"
            "runtime_invoker_absent"
        ),
    }
    for field_name, expected in expected_implementation.items():
        if implementation.get(field_name) != expected:
            raise QWakeLC4HostRuntimeInvokerError(
                f"wrapper implementation differs: {field_name}"
            )
    expected_source: Mapping[str, object] = {
        "authoring_merge_commit": "7cc17c6b36cb5115e63a2b64e4bff90a525b2465",
        "authoring_head_commit": "fe8eef0bbf37df08b461fbdbf6a7c043338f3cd2",
        "implementation_base_commit": "7cc17c6b36cb5115e63a2b64e4bff90a525b2465",
        "wrapper_contract_id": INVOCATION_WRAPPER_CONTRACT_ID,
        "wrapper_contract_sha256": INVOCATION_WRAPPER_CONTRACT_SHA256,
        "authorization_sha256": INVOCATION_AUTHORIZATION_SHA256,
        "image_repo_digest": IMAGE_REPO_DIGEST,
    }
    for field_name, expected in expected_source.items():
        if source.get(field_name) != expected:
            raise QWakeLC4HostRuntimeInvokerError(
                f"wrapper implementation source differs: {field_name}"
            )
    expected_contracts: Mapping[str, object] = {
        "module_sha256": WRAPPER_IMPLEMENTATION_MODULE_SHA256,
        "verifier_sha256": WRAPPER_IMPLEMENTATION_VERIFIER_SHA256,
        "test_sha256": WRAPPER_IMPLEMENTATION_TEST_SHA256,
        "shell_invocation_forbidden": True,
        "docker_observation_only": True,
    }
    for field_name, expected in expected_contracts.items():
        if contracts.get(field_name) != expected:
            raise QWakeLC4HostRuntimeInvokerError(
                f"wrapper implementation contract differs: {field_name}"
            )
    expected_gates: Mapping[str, object] = {
        "image_inspection_implemented": True,
        "invocation_command_materialized": True,
        "invocation_command_persisted": False,
        "host_runtime_invoker_present": False,
        "execution_lease_materialized": False,
        "authorization_consumed": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "local_compute_execution_open": False,
    }
    for field_name, expected in expected_gates.items():
        if gates.get(field_name) != expected:
            raise QWakeLC4HostRuntimeInvokerError(
                f"wrapper implementation gate differs: {field_name}"
            )
    file_expectations = (
        (
            WRAPPER_IMPLEMENTATION_MODULE_RELATIVE,
            WRAPPER_IMPLEMENTATION_MODULE_SHA256,
        ),
        (
            WRAPPER_IMPLEMENTATION_VERIFIER_RELATIVE,
            WRAPPER_IMPLEMENTATION_VERIFIER_SHA256,
        ),
        (
            WRAPPER_IMPLEMENTATION_TEST_RELATIVE,
            WRAPPER_IMPLEMENTATION_TEST_SHA256,
        ),
        (
            ONE_SHOT_ENTRYPOINT_RELATIVE,
            EXPECTED_ONE_SHOT_ENTRYPOINT_SHA256,
        ),
        (
            EXECUTION_WRAPPER_IMPLEMENTATION_RELATIVE,
            EXPECTED_EXECUTION_WRAPPER_IMPLEMENTATION_SHA256,
        ),
    )
    for relative, expected in file_expectations:
        if _sha256_file(root / relative) != expected:
            raise QWakeLC4HostRuntimeInvokerError(
                f"bound source hash differs: {relative.as_posix()}"
            )
    _verify_single_file_registry(
        root / AUTHORIZATION_REGISTRY_RELATIVE,
        root / AUTHORIZATION_ROOT_RELATIVE,
        "authorization.json",
        allow_extra=True,
    )
    authorization = _read_json_object(root / AUTHORIZATION_RELATIVE)
    if authorization.get("authorization_id") != INVOCATION_AUTHORIZATION_ID:
        raise QWakeLC4HostRuntimeInvokerError(
            "invocation authorization id differs"
        )
    if (
        authorization.get("authorization_sha256")
        != INVOCATION_AUTHORIZATION_SHA256
    ):
        raise QWakeLC4HostRuntimeInvokerError(
            "invocation authorization digest differs"
        )
    authorization_gates = _as_mapping(
        authorization.get("gates"), "authorization gates"
    )
    for field_name, expected in (
        ("one_shot_invocation_authorized", True),
        ("future_lease_claim_authorized", True),
        ("future_runtime_execution_authorized", True),
        ("execution_lease_materialized", False),
        ("authorization_consumed", False),
        ("runtime_execution_started", False),
        ("runtime_execution_performed", False),
    ):
        if authorization_gates.get(field_name) != expected:
            raise QWakeLC4HostRuntimeInvokerError(
                f"invocation authorization gate differs: {field_name}"
            )
    return (
        _sha256_file(root / WRAPPER_IMPLEMENTATION_RELATIVE),
        _sha256_file(root / AUTHORIZATION_RELATIVE),
    )


def build_host_runtime_invoker_contract(
    project_root: Path,
) -> HostRuntimeInvokerContract:
    """Build the pure future host-invoker contract without an executor."""

    verify_host_runtime_invoker_authoring_prerequisites(project_root)
    payload: dict[str, object] = {
        "schema_version": 1,
        "contract_id": HOST_RUNTIME_INVOKER_CONTRACT_ID,
        "status": HOST_RUNTIME_INVOKER_CONTRACT_STATUS,
        "authoring_base_commit": AUTHORING_BASE_COMMIT,
        "wrapper_implementation_head_commit": (
            WRAPPER_IMPLEMENTATION_HEAD_COMMIT
        ),
        "wrapper_implementation_merge_commit": (
            WRAPPER_IMPLEMENTATION_MERGE_COMMIT
        ),
        "wrapper_implementation_merged_at_utc": (
            WRAPPER_IMPLEMENTATION_MERGED_AT_UTC
        ),
        "wrapper_implementation_pr_number": (
            WRAPPER_IMPLEMENTATION_PR_NUMBER
        ),
        "wrapper_implementation_id": WRAPPER_IMPLEMENTATION_ID,
        "wrapper_implementation_module_sha256": (
            WRAPPER_IMPLEMENTATION_MODULE_SHA256
        ),
        "wrapper_implementation_verifier_sha256": (
            WRAPPER_IMPLEMENTATION_VERIFIER_SHA256
        ),
        "wrapper_implementation_test_sha256": (
            WRAPPER_IMPLEMENTATION_TEST_SHA256
        ),
        "invocation_wrapper_contract_id": INVOCATION_WRAPPER_CONTRACT_ID,
        "invocation_wrapper_contract_sha256": (
            INVOCATION_WRAPPER_CONTRACT_SHA256
        ),
        "invocation_authorization_id": INVOCATION_AUTHORIZATION_ID,
        "invocation_authorization_sha256": (
            INVOCATION_AUTHORIZATION_SHA256
        ),
        "image_repo_digest": IMAGE_REPO_DIGEST,
        "authorized_output_root": AUTHORIZED_OUTPUT_ROOT,
        "execution_lease_relative": EXECUTION_LEASE_RELATIVE,
        "host_observation_argv_prefix": HOST_OBSERVATION_ARGV_PREFIX,
        "host_execution_argv_prefix": HOST_EXECUTION_ARGV_PREFIX,
        "host_prelaunch_sequence": HOST_PRELAUNCH_SEQUENCE,
        "container_execution_sequence": CONTAINER_EXECUTION_SEQUENCE,
        "terminal_outcome_sequence": TERMINAL_OUTCOME_SEQUENCE,
        "lease_claim_owner": "container_entrypoint_same_process_as_runtime",
        "authorization_consumed_boundary": "atomic_execution_lease_claim",
        "runtime_started_boundary": "bounded_backend_call_started",
        "runtime_performed_boundary": (
            "complete_output_promoted_without_replace"
        ),
        "image_inspection_timeout_seconds": IMAGE_INSPECTION_TIMEOUT_SECONDS,
        "runtime_timeout_seconds": RUNTIME_TIMEOUT_SECONDS,
        "termination_grace_seconds": TERMINATION_GRACE_SECONDS,
        "stdout_capture_limit_bytes": STDOUT_CAPTURE_LIMIT_BYTES,
        "stderr_capture_limit_bytes": STDERR_CAPTURE_LIMIT_BYTES,
        "forwarded_signals": FORWARDED_SIGNALS,
        "exact_argv_only": True,
        "shell_interpretation_forbidden": True,
        "environment_inheritance_forbidden": True,
        "working_directory_override_forbidden": True,
        "single_child_spawn_per_invoker_process": True,
        "automatic_retry_after_spawn_forbidden": True,
        "concurrent_runtime_effects_guarded_by_atomic_lease": True,
        "host_execution_lease_write_forbidden": True,
        "claim_and_execute_same_container_process_required": True,
        "post_claim_revalidation_required": True,
        "lease_persists_after_failure": True,
        "output_promotion_without_replace_required": True,
        "child_process_group_required": True,
        "signal_forwarding_required": True,
        "timeout_is_terminal": True,
        "nonzero_return_code_is_terminal": True,
        "bounded_output_capture_required": True,
        "command_persistence_forbidden": True,
        "host_log_persistence_forbidden": True,
        "host_runtime_invoker_contract_present": True,
        "host_runtime_invoker_present": False,
        "host_runtime_invoker_executable": False,
        "host_docker_run_implemented": False,
        "branch_runtime_execution_permitted": False,
        "execution_lease_materialized": False,
        "authorization_consumed": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "engineering_evidence_present": False,
        "scientific_execution_open": False,
        "test_dataset_access": False,
        "publication_permitted": False,
        "local_compute_execution_open": False,
    }
    contract = HostRuntimeInvokerContract(
        **cast(Any, payload),
        contract_sha256=sha256_object(payload),
    )
    contract.require()
    return contract


def validate_host_runtime_invoker_contract(
    contract: HostRuntimeInvokerContract,
    project_root: Path,
) -> None:
    """Rebuild the pure contract and require exact equality."""

    contract.require()
    expected = build_host_runtime_invoker_contract(project_root)
    if contract != expected:
        raise QWakeLC4HostRuntimeInvokerError(
            "host-runtime-invoker contract differs from reconstruction"
        )


def load_host_runtime_invoker_contract(
    path: Path,
) -> HostRuntimeInvokerContract:
    """Load one canonical contract record for round-trip tests only."""

    payload = _read_json_object(path)
    tuple_fields = {
        "host_observation_argv_prefix",
        "host_execution_argv_prefix",
        "host_prelaunch_sequence",
        "container_execution_sequence",
        "terminal_outcome_sequence",
        "forwarded_signals",
    }
    normalized = dict(payload)
    for field_name in tuple_fields:
        normalized[field_name] = _as_string_tuple(
            payload.get(field_name), field_name
        )
    try:
        contract = HostRuntimeInvokerContract(**cast(Any, normalized))
    except TypeError as exc:
        raise QWakeLC4HostRuntimeInvokerError(
            "host-runtime-invoker contract schema differs"
        ) from exc
    contract.require()
    if path.read_bytes() != contract.canonical_json().encode("utf-8"):
        raise QWakeLC4HostRuntimeInvokerError(
            "host-runtime-invoker serialization differs"
        )
    return contract


def _verify_single_file_registry(
    registry_path: Path,
    base: Path,
    required_relative: str,
    *,
    allow_extra: bool = False,
) -> None:
    if not registry_path.is_file() or registry_path.is_symlink():
        raise QWakeLC4HostRuntimeInvokerError(
            f"registry is absent or non-regular: {registry_path}"
        )
    entries: dict[str, str] = {}
    for raw_line in registry_path.read_text(encoding="utf-8").splitlines():
        if not raw_line:
            continue
        parts = raw_line.split("  ", 1)
        if len(parts) != 2:
            raise QWakeLC4HostRuntimeInvokerError(
                "registry line format differs"
            )
        digest, relative = parts
        if relative in entries:
            raise QWakeLC4HostRuntimeInvokerError(
                "registry contains duplicate path"
            )
        entries[relative] = "sha256:" + digest
        target = base / relative
        if _sha256_file(target) != entries[relative]:
            raise QWakeLC4HostRuntimeInvokerError(
                f"registry digest differs: {relative}"
            )
    if required_relative not in entries:
        raise QWakeLC4HostRuntimeInvokerError(
            f"registry lacks required path: {required_relative}"
        )
    if not allow_extra and set(entries) != {required_relative}:
        raise QWakeLC4HostRuntimeInvokerError(
            "single-file registry scope differs"
        )


def _read_json_object(path: Path) -> dict[str, object]:
    if not path.is_file() or path.is_symlink():
        raise QWakeLC4HostRuntimeInvokerError(
            f"JSON source is absent or non-regular: {path}"
        )
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise QWakeLC4HostRuntimeInvokerError(
            f"JSON source cannot be read: {path}"
        ) from exc
    if not isinstance(value, dict):
        raise QWakeLC4HostRuntimeInvokerError(
            f"JSON source is not an object: {path}"
        )
    return cast(dict[str, object], value)


def _sha256_file(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise QWakeLC4HostRuntimeInvokerError(
            f"bound source is absent or non-regular: {path}"
        )
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _require_sha256(value: str, field_name: str) -> None:
    if not value.startswith("sha256:") or len(value) != 71:
        raise QWakeLC4HostRuntimeInvokerError(
            f"{field_name} is not SHA-256"
        )


def _as_mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise QWakeLC4HostRuntimeInvokerError(
            f"{field_name} is not an object"
        )
    return cast(Mapping[str, object], value)


def _as_sequence(value: object, field_name: str) -> Sequence[object]:
    if isinstance(value, str | bytes) or not isinstance(value, Sequence):
        raise QWakeLC4HostRuntimeInvokerError(
            f"{field_name} is not an array"
        )
    return cast(Sequence[object], value)


def _as_string_tuple(value: object, field_name: str) -> tuple[str, ...]:
    sequence = _as_sequence(value, field_name)
    if not all(isinstance(item, str) for item in sequence):
        raise QWakeLC4HostRuntimeInvokerError(
            f"{field_name} contains a non-string item"
        )
    return tuple(cast(str, item) for item in sequence)
