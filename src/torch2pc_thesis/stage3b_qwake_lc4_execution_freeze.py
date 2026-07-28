"""Fail-closed authoring contract for the QW-LC4-E execution freeze.

The module binds the merged lease/wrapper implementation to the already frozen
runtime authorization and admission. It deliberately does not implement a
concrete runtime backend, expose an execution entrypoint, create an execution
lease, start execution, write results, access the test dataset, or publish
evidence.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Final, cast

from torch2pc_thesis.stage3b_qwake_lc4_execution_admission import (
    AUTHORIZED_OUTPUT_ROOT,
    EXECUTION_LEASE_RELATIVE,
)
from torch2pc_thesis.stage3b_qwake_lc4_execution_wrapper import (
    ADMISSION_FREEZE_MERGE_COMMIT,
    AUTHORIZED_CELL_COUNT,
    FROZEN_ADMISSION_SHA256,
    FROZEN_TORCH2PC_COMMIT,
    RESERVE_PROBE_COUNT,
    RUNTIME_LANE_ORDER,
    canonical_json,
    sha256_object,
    verify_unconsumed_frozen_admission,
)

EXECUTION_FREEZE_REQUEST_ID: Final = (
    "stage3b-qwake-lc4-e-execution-freeze-request-v1"
)
EXECUTION_FREEZE_REQUEST_STATUS: Final = (
    "execution_freeze_contract_materialized_backend_and_lease_absent"
)
RUNTIME_BACKEND_CONTRACT_ID: Final = (
    "stage3b-qwake-lc4-e-runtime-backend-contract-v1"
)
ONE_SHOT_ENTRYPOINT_ID: Final = (
    "stage3b-qwake-lc4-e-one-shot-execution-entrypoint-v1"
)
IMPLEMENTATION_MERGE_COMMIT: Final = (
    "24966cd2a0380e46ab1924ff4ab8987f17e1fe9e"
)
IMPLEMENTATION_HEAD_COMMIT: Final = (
    "15588616c24d523f1c983fc205aeaae32a33958e"
)
IMPLEMENTATION_ID: Final = (
    "stage3b-qwake-lc4-e-execution-lease-wrapper-implementation-v1"
)
IMPLEMENTATION_MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_execution_wrapper_implementation.py"
)
IMPLEMENTATION_VALIDATOR_RELATIVE: Final = Path(
    "scripts/verify_stage3b_qwake_lc4_execution_wrapper_implementation.py"
)
IMPLEMENTATION_TEST_RELATIVE: Final = Path(
    "tests/unit/"
    "test_stage3b_qwake_lc4_execution_wrapper_implementation.py"
)
IMPLEMENTATION_PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-execution-lease-wrapper-implementation-v1"
)
IMPLEMENTATION_JSON_RELATIVE: Final = (
    IMPLEMENTATION_PACKAGE_RELATIVE / "implementation.json"
)
IMPLEMENTATION_REGISTRY_RELATIVE: Final = (
    IMPLEMENTATION_PACKAGE_RELATIVE / "SHA256SUMS"
)
IMPLEMENTATION_MODULE_SHA256: Final = (
    "sha256:"
    "43e114dfdb69fa54a993a98b2a487777c40168374e61c0949e5cf862d42f7d9f"
)
IMPLEMENTATION_VALIDATOR_SHA256: Final = (
    "sha256:"
    "f2aeb396b31810c59e17d669e0345f61294c5b678a5adf217fc1398019ae9ef1"
)
IMPLEMENTATION_TEST_SHA256: Final = (
    "sha256:"
    "c93648799fbd9e728a20f2f557589a78c9b9f2767be652486bd4494064c06511"
)
IMPLEMENTATION_JSON_SHA256: Final = (
    "sha256:"
    "f7cb2c72f5e9516d808f8f76802e2e560579f407aa1e155675bae2570a09b08e"
)
IMPLEMENTATION_REGISTRY_SHA256: Final = (
    "sha256:"
    "348b574bf7093edd4db263779014c256209a38b1c9e4c78f9598d0f82bf8b59a"
)

_COMMIT_PATTERN: Final = re.compile(r"^[0-9a-f]{40}$")
_SHA256_PATTERN: Final = re.compile(r"^sha256:[0-9a-f]{64}$")

__all__ = [
    "EXECUTION_FREEZE_REQUEST_ID",
    "EXECUTION_FREEZE_REQUEST_STATUS",
    "IMPLEMENTATION_HEAD_COMMIT",
    "IMPLEMENTATION_ID",
    "IMPLEMENTATION_MERGE_COMMIT",
    "ONE_SHOT_ENTRYPOINT_ID",
    "RUNTIME_BACKEND_CONTRACT_ID",
    "ExecutionFreezeRequest",
    "ExecutionFreezeSourceIdentity",
    "QWakeLC4ExecutionFreezeError",
    "build_execution_freeze_request",
    "load_execution_freeze_request",
    "validate_execution_freeze_request",
    "verify_execution_freeze_prerequisites",
]


class QWakeLC4ExecutionFreezeError(RuntimeError):
    """Raised when the QW-LC4-E execution-freeze boundary fails closed."""


@dataclass(frozen=True)
class ExecutionFreezeSourceIdentity:
    """Exact merged implementation and inherited admission identities."""

    implementation_id: str
    implementation_merge_commit: str
    implementation_head_commit: str
    torch2pc_commit: str
    admission_freeze_merge_commit: str
    admission_sha256: str
    implementation_module_path: str
    implementation_module_sha256: str
    implementation_validator_path: str
    implementation_validator_sha256: str
    implementation_test_path: str
    implementation_test_sha256: str
    implementation_json_path: str
    implementation_json_sha256: str
    implementation_registry_path: str
    implementation_registry_sha256: str
    output_root: str
    execution_lease_relative: str
    authorized_cell_count: int
    reserve_probe_count: int
    lane_order: tuple[str, ...]

    def require(self) -> None:
        exact = {
            "implementation_id": IMPLEMENTATION_ID,
            "implementation_merge_commit": IMPLEMENTATION_MERGE_COMMIT,
            "implementation_head_commit": IMPLEMENTATION_HEAD_COMMIT,
            "torch2pc_commit": FROZEN_TORCH2PC_COMMIT,
            "admission_freeze_merge_commit": (
                ADMISSION_FREEZE_MERGE_COMMIT
            ),
            "admission_sha256": FROZEN_ADMISSION_SHA256,
            "implementation_module_path": (
                IMPLEMENTATION_MODULE_RELATIVE.as_posix()
            ),
            "implementation_module_sha256": IMPLEMENTATION_MODULE_SHA256,
            "implementation_validator_path": (
                IMPLEMENTATION_VALIDATOR_RELATIVE.as_posix()
            ),
            "implementation_validator_sha256": (
                IMPLEMENTATION_VALIDATOR_SHA256
            ),
            "implementation_test_path": (
                IMPLEMENTATION_TEST_RELATIVE.as_posix()
            ),
            "implementation_test_sha256": IMPLEMENTATION_TEST_SHA256,
            "implementation_json_path": (
                IMPLEMENTATION_JSON_RELATIVE.as_posix()
            ),
            "implementation_json_sha256": IMPLEMENTATION_JSON_SHA256,
            "implementation_registry_path": (
                IMPLEMENTATION_REGISTRY_RELATIVE.as_posix()
            ),
            "implementation_registry_sha256": (
                IMPLEMENTATION_REGISTRY_SHA256
            ),
            "output_root": AUTHORIZED_OUTPUT_ROOT,
            "execution_lease_relative": (
                EXECUTION_LEASE_RELATIVE.as_posix()
            ),
        }
        for field_name, expected in exact.items():
            if getattr(self, field_name) != expected:
                raise QWakeLC4ExecutionFreezeError(
                    f"{field_name} differs"
                )
        if self.authorized_cell_count != AUTHORIZED_CELL_COUNT:
            raise QWakeLC4ExecutionFreezeError(
                "authorized cell count differs"
            )
        if self.reserve_probe_count != RESERVE_PROBE_COUNT:
            raise QWakeLC4ExecutionFreezeError(
                "reserve-probe count differs"
            )
        if self.lane_order != RUNTIME_LANE_ORDER:
            raise QWakeLC4ExecutionFreezeError(
                "runtime lane order differs"
            )
        for value, field_name in (
            (
                self.implementation_merge_commit,
                "implementation_merge_commit",
            ),
            (
                self.implementation_head_commit,
                "implementation_head_commit",
            ),
            (self.torch2pc_commit, "torch2pc_commit"),
            (
                self.admission_freeze_merge_commit,
                "admission_freeze_merge_commit",
            ),
        ):
            _require_commit(value, field_name)
        for value, field_name in (
            (self.admission_sha256, "admission_sha256"),
            (
                self.implementation_module_sha256,
                "implementation_module_sha256",
            ),
            (
                self.implementation_validator_sha256,
                "implementation_validator_sha256",
            ),
            (
                self.implementation_test_sha256,
                "implementation_test_sha256",
            ),
            (
                self.implementation_json_sha256,
                "implementation_json_sha256",
            ),
            (
                self.implementation_registry_sha256,
                "implementation_registry_sha256",
            ),
        ):
            _require_sha256(value, field_name)


@dataclass(frozen=True)
class ExecutionFreezeRequest:
    """Prospective execution freeze that keeps every runtime effect closed."""

    schema_version: int
    request_id: str
    status: str
    source: ExecutionFreezeSourceIdentity
    runtime_backend_contract_id: str
    one_shot_entrypoint_id: str
    execution_count: int
    claim_and_execute_same_process_required: bool
    no_retry_after_claim_required: bool
    atomic_output_promotion_required: bool
    canonical_backend_receipt_required: bool
    concrete_runtime_backend_present: bool
    one_shot_entrypoint_present: bool
    immutable_execution_image_present: bool
    execution_freeze_materialized: bool
    execution_lease_materialized: bool
    authorization_consumed: bool
    runtime_execution_permitted: bool
    runtime_execution_started: bool
    runtime_execution_performed: bool
    engineering_evidence_present: bool
    scientific_execution_open: bool
    test_dataset_access: bool
    publication_permitted: bool
    local_compute_execution_open: bool
    request_sha256: str

    def require(self) -> None:
        if self.schema_version != 1:
            raise QWakeLC4ExecutionFreezeError(
                "unexpected execution-freeze request schema"
            )
        if self.request_id != EXECUTION_FREEZE_REQUEST_ID:
            raise QWakeLC4ExecutionFreezeError(
                "unexpected execution-freeze request id"
            )
        if self.status != EXECUTION_FREEZE_REQUEST_STATUS:
            raise QWakeLC4ExecutionFreezeError(
                "unexpected execution-freeze request status"
            )
        self.source.require()
        if self.runtime_backend_contract_id != (
            RUNTIME_BACKEND_CONTRACT_ID
        ):
            raise QWakeLC4ExecutionFreezeError(
                "runtime-backend contract id differs"
            )
        if self.one_shot_entrypoint_id != ONE_SHOT_ENTRYPOINT_ID:
            raise QWakeLC4ExecutionFreezeError(
                "one-shot entrypoint id differs"
            )
        if self.execution_count != 1:
            raise QWakeLC4ExecutionFreezeError(
                "execution freeze is not single-attempt"
            )
        if not all(
            (
                self.claim_and_execute_same_process_required,
                self.no_retry_after_claim_required,
                self.atomic_output_promotion_required,
                self.canonical_backend_receipt_required,
            )
        ):
            raise QWakeLC4ExecutionFreezeError(
                "execution-freeze safety requirement is disabled"
            )
        if any(
            (
                self.concrete_runtime_backend_present,
                self.one_shot_entrypoint_present,
                self.immutable_execution_image_present,
                self.execution_freeze_materialized,
                self.execution_lease_materialized,
                self.authorization_consumed,
                self.runtime_execution_permitted,
                self.runtime_execution_started,
                self.runtime_execution_performed,
                self.engineering_evidence_present,
                self.scientific_execution_open,
                self.test_dataset_access,
                self.publication_permitted,
                self.local_compute_execution_open,
            )
        ):
            raise QWakeLC4ExecutionFreezeError(
                "execution-freeze authoring opened a forbidden capability"
            )
        _require_sha256(self.request_sha256, "request_sha256")
        if self.request_sha256 != sha256_object(
            self._payload_without_digest()
        ):
            raise QWakeLC4ExecutionFreezeError(
                "execution-freeze request digest differs"
            )

    def _payload_without_digest(self) -> Mapping[str, object]:
        payload = asdict(self)
        payload.pop("request_sha256")
        return cast(Mapping[str, object], payload)

    def canonical_json(self) -> str:
        return canonical_json(self)


def verify_execution_freeze_prerequisites(
    project_root: Path,
) -> ExecutionFreezeSourceIdentity:
    """Verify the exact merged implementation without opening effects."""

    root = project_root.expanduser().resolve()
    if _lexists(root / EXECUTION_LEASE_RELATIVE):
        raise QWakeLC4ExecutionFreezeError(
            "repository execution lease already exists"
        )
    if _lexists(root / AUTHORIZED_OUTPUT_ROOT):
        raise QWakeLC4ExecutionFreezeError(
            "repository runtime output already exists"
        )

    frozen_admission = verify_unconsumed_frozen_admission(root)
    if frozen_admission.freeze_merge_commit != (
        ADMISSION_FREEZE_MERGE_COMMIT
    ):
        raise QWakeLC4ExecutionFreezeError(
            "frozen admission merge commit differs"
        )
    if frozen_admission.admission_sha256 != FROZEN_ADMISSION_SHA256:
        raise QWakeLC4ExecutionFreezeError(
            "frozen admission semantic digest differs"
        )
    if frozen_admission.authorization_consumed:
        raise QWakeLC4ExecutionFreezeError(
            "frozen authorization is already consumed"
        )
    if frozen_admission.runtime_execution_started:
        raise QWakeLC4ExecutionFreezeError(
            "runtime execution has already started"
        )
    if frozen_admission.runtime_execution_performed:
        raise QWakeLC4ExecutionFreezeError(
            "runtime execution has already completed"
        )

    expected_files = {
        IMPLEMENTATION_MODULE_RELATIVE: IMPLEMENTATION_MODULE_SHA256,
        IMPLEMENTATION_VALIDATOR_RELATIVE: (
            IMPLEMENTATION_VALIDATOR_SHA256
        ),
        IMPLEMENTATION_TEST_RELATIVE: IMPLEMENTATION_TEST_SHA256,
        IMPLEMENTATION_JSON_RELATIVE: IMPLEMENTATION_JSON_SHA256,
        IMPLEMENTATION_REGISTRY_RELATIVE: (
            IMPLEMENTATION_REGISTRY_SHA256
        ),
    }
    for relative, expected in expected_files.items():
        path = root / relative
        _require_regular_file(path, label=relative.as_posix())
        if _sha256_file(path) != expected:
            raise QWakeLC4ExecutionFreezeError(
                f"{relative.as_posix()} digest differs"
            )

    registry = _read_registry(root / IMPLEMENTATION_REGISTRY_RELATIVE)
    if registry != {
        "implementation.json": IMPLEMENTATION_JSON_SHA256
    }:
        raise QWakeLC4ExecutionFreezeError(
            "implementation registry contents differ"
        )

    implementation = _read_json_object(
        root / IMPLEMENTATION_JSON_RELATIVE
    )
    if implementation.get("implementation_id") != IMPLEMENTATION_ID:
        raise QWakeLC4ExecutionFreezeError(
            "implementation manifest id differs"
        )
    if implementation.get("status") != (
        "atomic_effect_primitives_materialized_execution_not_open"
    ):
        raise QWakeLC4ExecutionFreezeError(
            "implementation manifest status differs"
        )
    gates = _as_mapping(implementation.get("gates"), "gates")
    for gate in (
        "execution_lease_schema_implemented",
        "execution_wrapper_contract_implemented",
        "execution_lease_writer_present",
        "runtime_executor_present",
        "result_writer_present",
        "lease_wrapper_implementation_materialized",
    ):
        if gates.get(gate) is not True:
            raise QWakeLC4ExecutionFreezeError(
                f"implementation capability is absent: {gate}"
            )
    for gate in (
        "execution_lease_materialized",
        "authorization_consumed",
        "runtime_execution_started",
        "runtime_execution_performed",
        "engineering_evidence_present",
        "scientific_execution_open",
        "test_dataset_access",
        "publication_permitted",
        "local_compute_execution_open",
        "qw_lc4_e_execution_permitted",
    ):
        if gates.get(gate) is not False:
            raise QWakeLC4ExecutionFreezeError(
                f"implementation effect boundary is open: {gate}"
            )

    identity = ExecutionFreezeSourceIdentity(
        implementation_id=IMPLEMENTATION_ID,
        implementation_merge_commit=IMPLEMENTATION_MERGE_COMMIT,
        implementation_head_commit=IMPLEMENTATION_HEAD_COMMIT,
        torch2pc_commit=FROZEN_TORCH2PC_COMMIT,
        admission_freeze_merge_commit=ADMISSION_FREEZE_MERGE_COMMIT,
        admission_sha256=FROZEN_ADMISSION_SHA256,
        implementation_module_path=(
            IMPLEMENTATION_MODULE_RELATIVE.as_posix()
        ),
        implementation_module_sha256=IMPLEMENTATION_MODULE_SHA256,
        implementation_validator_path=(
            IMPLEMENTATION_VALIDATOR_RELATIVE.as_posix()
        ),
        implementation_validator_sha256=(
            IMPLEMENTATION_VALIDATOR_SHA256
        ),
        implementation_test_path=(
            IMPLEMENTATION_TEST_RELATIVE.as_posix()
        ),
        implementation_test_sha256=IMPLEMENTATION_TEST_SHA256,
        implementation_json_path=(
            IMPLEMENTATION_JSON_RELATIVE.as_posix()
        ),
        implementation_json_sha256=IMPLEMENTATION_JSON_SHA256,
        implementation_registry_path=(
            IMPLEMENTATION_REGISTRY_RELATIVE.as_posix()
        ),
        implementation_registry_sha256=(
            IMPLEMENTATION_REGISTRY_SHA256
        ),
        output_root=AUTHORIZED_OUTPUT_ROOT,
        execution_lease_relative=EXECUTION_LEASE_RELATIVE.as_posix(),
        authorized_cell_count=AUTHORIZED_CELL_COUNT,
        reserve_probe_count=RESERVE_PROBE_COUNT,
        lane_order=RUNTIME_LANE_ORDER,
    )
    identity.require()
    return identity


def build_execution_freeze_request(
    project_root: Path,
) -> ExecutionFreezeRequest:
    """Build a deterministic request while all runtime effects stay closed."""

    source = verify_execution_freeze_prerequisites(project_root)
    payload: dict[str, object] = {
        "schema_version": 1,
        "request_id": EXECUTION_FREEZE_REQUEST_ID,
        "status": EXECUTION_FREEZE_REQUEST_STATUS,
        "source": asdict(source),
        "runtime_backend_contract_id": RUNTIME_BACKEND_CONTRACT_ID,
        "one_shot_entrypoint_id": ONE_SHOT_ENTRYPOINT_ID,
        "execution_count": 1,
        "claim_and_execute_same_process_required": True,
        "no_retry_after_claim_required": True,
        "atomic_output_promotion_required": True,
        "canonical_backend_receipt_required": True,
        "concrete_runtime_backend_present": False,
        "one_shot_entrypoint_present": False,
        "immutable_execution_image_present": False,
        "execution_freeze_materialized": False,
        "execution_lease_materialized": False,
        "authorization_consumed": False,
        "runtime_execution_permitted": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "engineering_evidence_present": False,
        "scientific_execution_open": False,
        "test_dataset_access": False,
        "publication_permitted": False,
        "local_compute_execution_open": False,
    }
    request = ExecutionFreezeRequest(
        schema_version=1,
        request_id=EXECUTION_FREEZE_REQUEST_ID,
        status=EXECUTION_FREEZE_REQUEST_STATUS,
        source=source,
        runtime_backend_contract_id=RUNTIME_BACKEND_CONTRACT_ID,
        one_shot_entrypoint_id=ONE_SHOT_ENTRYPOINT_ID,
        execution_count=1,
        claim_and_execute_same_process_required=True,
        no_retry_after_claim_required=True,
        atomic_output_promotion_required=True,
        canonical_backend_receipt_required=True,
        concrete_runtime_backend_present=False,
        one_shot_entrypoint_present=False,
        immutable_execution_image_present=False,
        execution_freeze_materialized=False,
        execution_lease_materialized=False,
        authorization_consumed=False,
        runtime_execution_permitted=False,
        runtime_execution_started=False,
        runtime_execution_performed=False,
        engineering_evidence_present=False,
        scientific_execution_open=False,
        test_dataset_access=False,
        publication_permitted=False,
        local_compute_execution_open=False,
        request_sha256=sha256_object(payload),
    )
    request.require()
    return request


def validate_execution_freeze_request(
    request: ExecutionFreezeRequest,
    project_root: Path,
) -> None:
    """Rebuild and compare the complete authoring request."""

    request.require()
    if request != build_execution_freeze_request(project_root):
        raise QWakeLC4ExecutionFreezeError(
            "execution-freeze request differs from repository prerequisites"
        )


def load_execution_freeze_request(
    path: Path,
) -> ExecutionFreezeRequest:
    """Load a canonical execution-freeze authoring request."""

    payload = _read_json_object(path)
    source_payload = _as_mapping(payload.get("source"), "source")
    source = ExecutionFreezeSourceIdentity(
        implementation_id=_as_str(
            source_payload.get("implementation_id"),
            "implementation_id",
        ),
        implementation_merge_commit=_as_str(
            source_payload.get("implementation_merge_commit"),
            "implementation_merge_commit",
        ),
        implementation_head_commit=_as_str(
            source_payload.get("implementation_head_commit"),
            "implementation_head_commit",
        ),
        torch2pc_commit=_as_str(
            source_payload.get("torch2pc_commit"),
            "torch2pc_commit",
        ),
        admission_freeze_merge_commit=_as_str(
            source_payload.get("admission_freeze_merge_commit"),
            "admission_freeze_merge_commit",
        ),
        admission_sha256=_as_str(
            source_payload.get("admission_sha256"),
            "admission_sha256",
        ),
        implementation_module_path=_as_str(
            source_payload.get("implementation_module_path"),
            "implementation_module_path",
        ),
        implementation_module_sha256=_as_str(
            source_payload.get("implementation_module_sha256"),
            "implementation_module_sha256",
        ),
        implementation_validator_path=_as_str(
            source_payload.get("implementation_validator_path"),
            "implementation_validator_path",
        ),
        implementation_validator_sha256=_as_str(
            source_payload.get("implementation_validator_sha256"),
            "implementation_validator_sha256",
        ),
        implementation_test_path=_as_str(
            source_payload.get("implementation_test_path"),
            "implementation_test_path",
        ),
        implementation_test_sha256=_as_str(
            source_payload.get("implementation_test_sha256"),
            "implementation_test_sha256",
        ),
        implementation_json_path=_as_str(
            source_payload.get("implementation_json_path"),
            "implementation_json_path",
        ),
        implementation_json_sha256=_as_str(
            source_payload.get("implementation_json_sha256"),
            "implementation_json_sha256",
        ),
        implementation_registry_path=_as_str(
            source_payload.get("implementation_registry_path"),
            "implementation_registry_path",
        ),
        implementation_registry_sha256=_as_str(
            source_payload.get("implementation_registry_sha256"),
            "implementation_registry_sha256",
        ),
        output_root=_as_str(
            source_payload.get("output_root"),
            "output_root",
        ),
        execution_lease_relative=_as_str(
            source_payload.get("execution_lease_relative"),
            "execution_lease_relative",
        ),
        authorized_cell_count=_as_int(
            source_payload.get("authorized_cell_count"),
            "authorized_cell_count",
        ),
        reserve_probe_count=_as_int(
            source_payload.get("reserve_probe_count"),
            "reserve_probe_count",
        ),
        lane_order=tuple(
            _as_str(item, "lane_order")
            for item in _as_sequence(
                source_payload.get("lane_order"),
                "lane_order",
            )
        ),
    )
    request = ExecutionFreezeRequest(
        schema_version=_as_int(
            payload.get("schema_version"),
            "schema_version",
        ),
        request_id=_as_str(payload.get("request_id"), "request_id"),
        status=_as_str(payload.get("status"), "status"),
        source=source,
        runtime_backend_contract_id=_as_str(
            payload.get("runtime_backend_contract_id"),
            "runtime_backend_contract_id",
        ),
        one_shot_entrypoint_id=_as_str(
            payload.get("one_shot_entrypoint_id"),
            "one_shot_entrypoint_id",
        ),
        execution_count=_as_int(
            payload.get("execution_count"),
            "execution_count",
        ),
        claim_and_execute_same_process_required=_as_bool(
            payload.get("claim_and_execute_same_process_required"),
            "claim_and_execute_same_process_required",
        ),
        no_retry_after_claim_required=_as_bool(
            payload.get("no_retry_after_claim_required"),
            "no_retry_after_claim_required",
        ),
        atomic_output_promotion_required=_as_bool(
            payload.get("atomic_output_promotion_required"),
            "atomic_output_promotion_required",
        ),
        canonical_backend_receipt_required=_as_bool(
            payload.get("canonical_backend_receipt_required"),
            "canonical_backend_receipt_required",
        ),
        concrete_runtime_backend_present=_as_bool(
            payload.get("concrete_runtime_backend_present"),
            "concrete_runtime_backend_present",
        ),
        one_shot_entrypoint_present=_as_bool(
            payload.get("one_shot_entrypoint_present"),
            "one_shot_entrypoint_present",
        ),
        immutable_execution_image_present=_as_bool(
            payload.get("immutable_execution_image_present"),
            "immutable_execution_image_present",
        ),
        execution_freeze_materialized=_as_bool(
            payload.get("execution_freeze_materialized"),
            "execution_freeze_materialized",
        ),
        execution_lease_materialized=_as_bool(
            payload.get("execution_lease_materialized"),
            "execution_lease_materialized",
        ),
        authorization_consumed=_as_bool(
            payload.get("authorization_consumed"),
            "authorization_consumed",
        ),
        runtime_execution_permitted=_as_bool(
            payload.get("runtime_execution_permitted"),
            "runtime_execution_permitted",
        ),
        runtime_execution_started=_as_bool(
            payload.get("runtime_execution_started"),
            "runtime_execution_started",
        ),
        runtime_execution_performed=_as_bool(
            payload.get("runtime_execution_performed"),
            "runtime_execution_performed",
        ),
        engineering_evidence_present=_as_bool(
            payload.get("engineering_evidence_present"),
            "engineering_evidence_present",
        ),
        scientific_execution_open=_as_bool(
            payload.get("scientific_execution_open"),
            "scientific_execution_open",
        ),
        test_dataset_access=_as_bool(
            payload.get("test_dataset_access"),
            "test_dataset_access",
        ),
        publication_permitted=_as_bool(
            payload.get("publication_permitted"),
            "publication_permitted",
        ),
        local_compute_execution_open=_as_bool(
            payload.get("local_compute_execution_open"),
            "local_compute_execution_open",
        ),
        request_sha256=_as_str(
            payload.get("request_sha256"),
            "request_sha256",
        ),
    )
    request.require()
    if path.read_bytes() != request.canonical_json().encode("utf-8"):
        raise QWakeLC4ExecutionFreezeError(
            "execution-freeze request serialization differs"
        )
    return request


def _read_registry(path: Path) -> dict[str, str]:
    _require_regular_file(path, label=path.name)
    result: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split("  ", 1)
        if len(parts) != 2:
            raise QWakeLC4ExecutionFreezeError(
                "implementation registry line differs"
            )
        digest, relative = parts
        _require_sha256("sha256:" + digest, "registry_digest")
        if relative in result:
            raise QWakeLC4ExecutionFreezeError(
                "implementation registry contains duplicate path"
            )
        result[relative] = "sha256:" + digest
    return result


def _read_json_object(path: Path) -> dict[str, Any]:
    _require_regular_file(path, label=path.name)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise QWakeLC4ExecutionFreezeError(
            f"{path.name} must contain a JSON object"
        )
    return cast(dict[str, Any], payload)


def _sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _require_regular_file(path: Path, *, label: str) -> None:
    if not path.is_file() or path.is_symlink():
        raise QWakeLC4ExecutionFreezeError(
            f"{label} is absent or non-regular"
        )


def _lexists(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def _require_commit(value: str, field_name: str) -> None:
    if not _COMMIT_PATTERN.fullmatch(value):
        raise QWakeLC4ExecutionFreezeError(
            f"{field_name} is not a full commit"
        )


def _require_sha256(value: str, field_name: str) -> None:
    if not _SHA256_PATTERN.fullmatch(value):
        raise QWakeLC4ExecutionFreezeError(
            f"{field_name} is not a sha256 identity"
        )


def _as_mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise QWakeLC4ExecutionFreezeError(
            f"{field_name} is not a mapping"
        )
    return cast(Mapping[str, object], value)


def _as_sequence(value: object, field_name: str) -> Sequence[object]:
    if not isinstance(value, list):
        raise QWakeLC4ExecutionFreezeError(
            f"{field_name} is not a list"
        )
    return cast(Sequence[object], value)


def _as_str(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise QWakeLC4ExecutionFreezeError(
            f"{field_name} is not a string"
        )
    return value


def _as_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise QWakeLC4ExecutionFreezeError(
            f"{field_name} is not an integer"
        )
    return value


def _as_bool(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise QWakeLC4ExecutionFreezeError(
            f"{field_name} is not a boolean"
        )
    return value
