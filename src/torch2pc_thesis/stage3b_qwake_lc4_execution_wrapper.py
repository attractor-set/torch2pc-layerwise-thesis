"""Fail-closed authoring contracts for the QW-LC4-E lease and wrapper.

The module verifies the merged admission package and constructs only
prospective, in-memory lease and execution-wrapper records. It does not create
an execution lease, import model code, start execution, write results, consume
the frozen authorization, or publish evidence.
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
    EXECUTION_ADMISSION_ID,
    EXECUTION_LEASE_RELATIVE,
    load_execution_admission,
    validate_execution_admission,
    verify_frozen_runtime_package,
)

EXECUTION_LEASE_ID: Final = "stage3b-qwake-lc4-e-execution-lease-v1"
EXECUTION_LEASE_STATUS: Final = "prospective_single_attempt_lease_not_materialized"
EXECUTION_WRAPPER_CONTRACT_ID: Final = (
    "stage3b-qwake-lc4-e-execution-wrapper-contract-v1"
)
EXECUTION_WRAPPER_CONTRACT_STATUS: Final = (
    "prospective_execution_wrapper_effects_closed"
)
EXECUTION_LEASE_OPERATOR_ACKNOWLEDGEMENT: Final = (
    "CLAIM_QWAKE_LC4_SINGLE_ENGINEERING_ATTEMPT_FROM_FROZEN_ADMISSION"
)
ADMISSION_FREEZE_ID: Final = (
    "stage3b-qwake-lc4-e-execution-admission-freeze-v1"
)
ADMISSION_FREEZE_MERGE_COMMIT: Final = (
    "12b7d24153a681f731a43e8497275016ad4e1656"
)
ADMISSION_FREEZE_HEAD_COMMIT: Final = (
    "52e8bbd54bdea70abbd9e7aff86872b69a8c341d"
)
ADMISSION_CONTROL_PLANE_COMMIT: Final = (
    "bce821dff0729629db0ccb306d8f3fd1dd9a2e13"
)
FROZEN_TORCH2PC_COMMIT: Final = (
    "b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4"
)
FROZEN_IMAGE_DIGEST: Final = (
    "sha256:"
    "a31cf96e20ab45ce29fe18b68eb805bd048a02f1f8107cf680d1c174ea363929"
)
FROZEN_AUTHORIZATION_SHA256: Final = (
    "sha256:"
    "d11b662a5c5eeada5333e69c6fddf2e50726c01b4d8c78a556a68167dbdd301e"
)
FROZEN_ADMISSION_SHA256: Final = (
    "sha256:"
    "d1ee6d022588f0a2cf0ac23f3bf8de9b27f9aad4fc1153435bd70e1ab83e296c"
)
FROZEN_ADMISSION_FILE_SHA256: Final = (
    "sha256:"
    "d819f8a7e03314242c0072e2d020a59fbe6b7f6984fda99ff0dcd306cc97ca70"
)
FROZEN_ADMISSION_RECEIPT_FILE_SHA256: Final = (
    "sha256:"
    "d4b9d33117cbf522b1c62173c7a81f9638cde703eb6b3bbb392ff46e45a17c25"
)
FROZEN_ADMISSION_PACKAGE_REGISTRY_SHA256: Final = (
    "sha256:"
    "411f3e8d62b367755a6f02070ad84bc6f37cfefad602d885674a844b57aa74cd"
)
FROZEN_ADMISSION_SOURCE_REGISTRY_SHA256: Final = (
    "sha256:"
    "01c9a29d1f80098707d6715ffd5160ad48bb497b08a71180c2b71d8e89b66504"
)
AUTHORIZED_CELL_COUNT: Final = 168
RESERVE_PROBE_COUNT: Final = 28
RUNTIME_LANE_ORDER: Final = (
    "cpu_float64_engineering",
    "rocm_float32_canonical",
)
ADMISSION_FREEZE_ROOT_RELATIVE: Final = Path(
    "experiments/frozen/stage3b-qwake-lc4-e-execution-admission-freeze-v1"
)
RUNTIME_FREEZE_ROOT_RELATIVE: Final = Path(
    "experiments/frozen/stage3b-qwake-lc4-f-runtime-freeze-v1"
)

_EXPECTED_ADMISSION_FILES: Final = frozenset(
    {
        "SHA256SUMS",
        "admission-validation.log",
        "admission.json",
        "source-SHA256SUMS",
        "verification-receipt.json",
    }
)
_COMMIT_PATTERN: Final = re.compile(r"^[0-9a-f]{40}$")
_SHA256_PATTERN: Final = re.compile(r"^sha256:[0-9a-f]{64}$")

__all__ = [
    "ADMISSION_FREEZE_HEAD_COMMIT",
    "ADMISSION_FREEZE_ID",
    "ADMISSION_FREEZE_MERGE_COMMIT",
    "AUTHORIZED_CELL_COUNT",
    "EXECUTION_LEASE_ID",
    "EXECUTION_LEASE_OPERATOR_ACKNOWLEDGEMENT",
    "EXECUTION_LEASE_STATUS",
    "EXECUTION_WRAPPER_CONTRACT_ID",
    "EXECUTION_WRAPPER_CONTRACT_STATUS",
    "FROZEN_ADMISSION_SHA256",
    "FROZEN_TORCH2PC_COMMIT",
    "RESERVE_PROBE_COUNT",
    "RUNTIME_LANE_ORDER",
    "ExecutionWrapperContract",
    "FrozenAdmissionIdentity",
    "ProspectiveExecutionLease",
    "QWakeLC4ExecutionWrapperError",
    "build_execution_wrapper_contract",
    "build_prospective_execution_lease",
    "canonical_json",
    "load_execution_wrapper_contract",
    "load_prospective_execution_lease",
    "sha256_object",
    "validate_execution_wrapper_contract",
    "validate_prospective_execution_lease",
    "verify_unconsumed_frozen_admission",
]


class QWakeLC4ExecutionWrapperError(RuntimeError):
    """Raised when lease/wrapper authoring fails closed."""


@dataclass(frozen=True)
class FrozenAdmissionIdentity:
    """Exact merged admission and runtime identities inherited by execution."""

    freeze_id: str
    freeze_merge_commit: str
    freeze_head_commit: str
    control_plane_commit: str
    admission_id: str
    admission_sha256: str
    admission_file_sha256: str
    receipt_file_sha256: str
    package_registry_sha256: str
    source_registry_sha256: str
    torch2pc_commit: str
    image_digest: str
    authorization_sha256: str
    output_root: str
    execution_lease_relative: str
    authorized_cell_count: int
    reserve_probe_count: int
    lane_order: tuple[str, ...]
    execution_count: int
    runtime_execution_permitted: bool
    authorization_consumed: bool
    runtime_execution_started: bool
    runtime_execution_performed: bool
    engineering_evidence_present: bool
    scientific_execution_open: bool
    test_dataset_access: bool
    publication_permitted: bool

    def require(self) -> None:
        expected: Mapping[str, object] = {
            "freeze_id": ADMISSION_FREEZE_ID,
            "freeze_merge_commit": ADMISSION_FREEZE_MERGE_COMMIT,
            "freeze_head_commit": ADMISSION_FREEZE_HEAD_COMMIT,
            "control_plane_commit": ADMISSION_CONTROL_PLANE_COMMIT,
            "admission_id": EXECUTION_ADMISSION_ID,
            "admission_sha256": FROZEN_ADMISSION_SHA256,
            "admission_file_sha256": FROZEN_ADMISSION_FILE_SHA256,
            "receipt_file_sha256": FROZEN_ADMISSION_RECEIPT_FILE_SHA256,
            "package_registry_sha256": (
                FROZEN_ADMISSION_PACKAGE_REGISTRY_SHA256
            ),
            "source_registry_sha256": FROZEN_ADMISSION_SOURCE_REGISTRY_SHA256,
            "torch2pc_commit": FROZEN_TORCH2PC_COMMIT,
            "image_digest": FROZEN_IMAGE_DIGEST,
            "authorization_sha256": FROZEN_AUTHORIZATION_SHA256,
            "output_root": AUTHORIZED_OUTPUT_ROOT,
            "execution_lease_relative": EXECUTION_LEASE_RELATIVE.as_posix(),
            "authorized_cell_count": AUTHORIZED_CELL_COUNT,
            "reserve_probe_count": RESERVE_PROBE_COUNT,
            "lane_order": RUNTIME_LANE_ORDER,
            "execution_count": 1,
            "runtime_execution_permitted": True,
            "authorization_consumed": False,
            "runtime_execution_started": False,
            "runtime_execution_performed": False,
            "engineering_evidence_present": False,
            "scientific_execution_open": False,
            "test_dataset_access": False,
            "publication_permitted": False,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise QWakeLC4ExecutionWrapperError(
                    f"frozen admission identity differs: {field_name}"
                )


@dataclass(frozen=True)
class ProspectiveExecutionLease:
    """Canonical one-attempt claim represented only in memory during authoring."""

    schema_version: int
    lease_id: str
    status: str
    claimed_at_utc: str
    operator_acknowledgement: str
    wrapper_commit: str
    admission_freeze_merge_commit: str
    admission_id: str
    admission_sha256: str
    admission_file_sha256: str
    torch2pc_commit: str
    image_digest: str
    authorization_sha256: str
    output_root: str
    execution_lease_relative: str
    output_root_absent_at_claim: bool
    execution_lease_absent_at_claim: bool
    execution_count: int
    authorization_consumed: bool
    runtime_execution_permitted: bool
    runtime_execution_started: bool
    runtime_execution_performed: bool
    engineering_evidence_present: bool
    scientific_execution_open: bool
    test_dataset_access: bool
    publication_permitted: bool
    lease_sha256: str

    def require(self) -> None:
        if self.schema_version != 1:
            raise QWakeLC4ExecutionWrapperError("unexpected lease schema")
        if self.lease_id != EXECUTION_LEASE_ID:
            raise QWakeLC4ExecutionWrapperError("unexpected lease id")
        if self.status != EXECUTION_LEASE_STATUS:
            raise QWakeLC4ExecutionWrapperError("unexpected lease status")
        _require_utc(self.claimed_at_utc, "claimed_at_utc")
        _require_commit(self.wrapper_commit, "wrapper_commit")
        if (
            self.operator_acknowledgement
            != EXECUTION_LEASE_OPERATOR_ACKNOWLEDGEMENT
        ):
            raise QWakeLC4ExecutionWrapperError(
                "execution lease operator acknowledgement differs"
            )
        exact_values: Mapping[str, object] = {
            "admission_freeze_merge_commit": ADMISSION_FREEZE_MERGE_COMMIT,
            "admission_id": EXECUTION_ADMISSION_ID,
            "admission_sha256": FROZEN_ADMISSION_SHA256,
            "admission_file_sha256": FROZEN_ADMISSION_FILE_SHA256,
            "torch2pc_commit": FROZEN_TORCH2PC_COMMIT,
            "image_digest": FROZEN_IMAGE_DIGEST,
            "authorization_sha256": FROZEN_AUTHORIZATION_SHA256,
            "output_root": AUTHORIZED_OUTPUT_ROOT,
            "execution_lease_relative": EXECUTION_LEASE_RELATIVE.as_posix(),
        }
        for field_name, expected in exact_values.items():
            if getattr(self, field_name) != expected:
                raise QWakeLC4ExecutionWrapperError(
                    f"prospective lease identity differs: {field_name}"
                )
        if not self.output_root_absent_at_claim:
            raise QWakeLC4ExecutionWrapperError(
                "output root existed at prospective lease claim"
            )
        if not self.execution_lease_absent_at_claim:
            raise QWakeLC4ExecutionWrapperError(
                "execution lease existed at prospective claim"
            )
        if self.execution_count != 1:
            raise QWakeLC4ExecutionWrapperError(
                "prospective lease is not single-attempt"
            )
        if not self.authorization_consumed:
            raise QWakeLC4ExecutionWrapperError(
                "prospective lease must consume the authorization"
            )
        if not self.runtime_execution_permitted:
            raise QWakeLC4ExecutionWrapperError(
                "prospective lease does not permit execution"
            )
        if any(
            (
                self.runtime_execution_started,
                self.runtime_execution_performed,
                self.engineering_evidence_present,
                self.scientific_execution_open,
                self.test_dataset_access,
                self.publication_permitted,
            )
        ):
            raise QWakeLC4ExecutionWrapperError(
                "prospective lease opened a completed or scientific capability"
            )
        _require_sha256(self.lease_sha256, "lease_sha256")
        if self.lease_sha256 != sha256_object(self._payload_without_digest()):
            raise QWakeLC4ExecutionWrapperError(
                "prospective lease digest differs"
            )

    def _payload_without_digest(self) -> Mapping[str, object]:
        payload = asdict(self)
        payload.pop("lease_sha256")
        return cast(Mapping[str, object], payload)

    def canonical_json(self) -> str:
        return canonical_json(self)


@dataclass(frozen=True)
class ExecutionWrapperContract:
    """Effect boundary required before a future concrete executor is added."""

    schema_version: int
    contract_id: str
    status: str
    wrapper_commit: str
    lease_id: str
    lease_sha256: str
    admission_freeze_merge_commit: str
    torch2pc_commit: str
    image_digest: str
    authorization_sha256: str
    output_root: str
    execution_lease_relative: str
    lane_order: tuple[str, ...]
    authorized_cell_count: int
    reserve_probe_count: int
    execution_count: int
    exclusive_atomic_lease_claim_required: bool
    lease_persists_after_failure: bool
    retry_after_claim_permitted: bool
    atomic_output_promotion_required: bool
    fail_closed_on_existing_output: bool
    fail_closed_on_existing_lease: bool
    authorization_consumed_after_claim: bool
    runtime_execution_permitted_after_claim: bool
    runtime_execution_started: bool
    runtime_execution_performed: bool
    engineering_evidence_present: bool
    scientific_execution_open: bool
    test_dataset_access: bool
    publication_permitted: bool
    contract_sha256: str

    def require(self) -> None:
        if self.schema_version != 1:
            raise QWakeLC4ExecutionWrapperError(
                "unexpected execution-wrapper contract schema"
            )
        if self.contract_id != EXECUTION_WRAPPER_CONTRACT_ID:
            raise QWakeLC4ExecutionWrapperError(
                "unexpected execution-wrapper contract id"
            )
        if self.status != EXECUTION_WRAPPER_CONTRACT_STATUS:
            raise QWakeLC4ExecutionWrapperError(
                "unexpected execution-wrapper contract status"
            )
        _require_commit(self.wrapper_commit, "wrapper_commit")
        _require_sha256(self.lease_sha256, "lease_sha256")
        exact_values: Mapping[str, object] = {
            "lease_id": EXECUTION_LEASE_ID,
            "admission_freeze_merge_commit": ADMISSION_FREEZE_MERGE_COMMIT,
            "torch2pc_commit": FROZEN_TORCH2PC_COMMIT,
            "image_digest": FROZEN_IMAGE_DIGEST,
            "authorization_sha256": FROZEN_AUTHORIZATION_SHA256,
            "output_root": AUTHORIZED_OUTPUT_ROOT,
            "execution_lease_relative": EXECUTION_LEASE_RELATIVE.as_posix(),
            "lane_order": RUNTIME_LANE_ORDER,
            "authorized_cell_count": AUTHORIZED_CELL_COUNT,
            "reserve_probe_count": RESERVE_PROBE_COUNT,
            "execution_count": 1,
            "exclusive_atomic_lease_claim_required": True,
            "lease_persists_after_failure": True,
            "retry_after_claim_permitted": False,
            "atomic_output_promotion_required": True,
            "fail_closed_on_existing_output": True,
            "fail_closed_on_existing_lease": True,
            "authorization_consumed_after_claim": True,
            "runtime_execution_permitted_after_claim": True,
            "runtime_execution_started": False,
            "runtime_execution_performed": False,
            "engineering_evidence_present": False,
            "scientific_execution_open": False,
            "test_dataset_access": False,
            "publication_permitted": False,
        }
        for field_name, expected in exact_values.items():
            if getattr(self, field_name) != expected:
                raise QWakeLC4ExecutionWrapperError(
                    f"execution-wrapper contract differs: {field_name}"
                )
        _require_sha256(self.contract_sha256, "contract_sha256")
        if self.contract_sha256 != sha256_object(
            self._payload_without_digest()
        ):
            raise QWakeLC4ExecutionWrapperError(
                "execution-wrapper contract digest differs"
            )

    def _payload_without_digest(self) -> Mapping[str, object]:
        payload = asdict(self)
        payload.pop("contract_sha256")
        return cast(Mapping[str, object], payload)

    def canonical_json(self) -> str:
        return canonical_json(self)


def verify_unconsumed_frozen_admission(
    project_root: Path,
) -> FrozenAdmissionIdentity:
    """Verify exact merged admission and preserve an unclaimed execution state."""

    root = project_root.expanduser().resolve()
    freeze_root = root / ADMISSION_FREEZE_ROOT_RELATIVE
    if not freeze_root.is_dir():
        raise QWakeLC4ExecutionWrapperError(
            "frozen execution admission package is absent"
        )
    entries = tuple(freeze_root.iterdir())
    files = {entry.name for entry in entries if entry.is_file()}
    if files != set(_EXPECTED_ADMISSION_FILES):
        raise QWakeLC4ExecutionWrapperError(
            "frozen execution admission package scope differs"
        )
    if any(entry.is_dir() or entry.is_symlink() for entry in entries):
        raise QWakeLC4ExecutionWrapperError(
            "frozen execution admission contains a non-regular entry"
        )

    _verify_registry(freeze_root / "SHA256SUMS", freeze_root)
    _verify_registry(freeze_root / "source-SHA256SUMS", root)
    if _sha256_file(freeze_root / "SHA256SUMS") != (
        FROZEN_ADMISSION_PACKAGE_REGISTRY_SHA256
    ):
        raise QWakeLC4ExecutionWrapperError(
            "frozen admission package registry identity differs"
        )
    if _sha256_file(freeze_root / "source-SHA256SUMS") != (
        FROZEN_ADMISSION_SOURCE_REGISTRY_SHA256
    ):
        raise QWakeLC4ExecutionWrapperError(
            "frozen admission source registry identity differs"
        )

    admission_path = freeze_root / "admission.json"
    receipt_path = freeze_root / "verification-receipt.json"
    if _sha256_file(admission_path) != FROZEN_ADMISSION_FILE_SHA256:
        raise QWakeLC4ExecutionWrapperError(
            "frozen admission file identity differs"
        )
    if _sha256_file(receipt_path) != (
        FROZEN_ADMISSION_RECEIPT_FILE_SHA256
    ):
        raise QWakeLC4ExecutionWrapperError(
            "frozen admission receipt identity differs"
        )

    frozen_runtime = verify_frozen_runtime_package(root)
    admission = load_execution_admission(admission_path)
    validate_execution_admission(
        admission,
        frozen_runtime,
        root,
        expected_control_plane_commit=ADMISSION_CONTROL_PLANE_COMMIT,
    )
    if admission.admission_sha256 != FROZEN_ADMISSION_SHA256:
        raise QWakeLC4ExecutionWrapperError(
            "frozen admission semantic identity differs"
        )

    receipt = _read_json_object(receipt_path)
    if receipt.get("receipt_id") != (
        "stage3b-qwake-lc4-e-execution-admission-verification-v1"
    ):
        raise QWakeLC4ExecutionWrapperError(
            "frozen admission receipt id differs"
        )
    if receipt.get("status") != (
        "execution_admission_frozen_execution_not_started"
    ):
        raise QWakeLC4ExecutionWrapperError(
            "frozen admission receipt status differs"
        )
    if receipt.get("post_merge_next_slice") != (
        "QW-LC4-E-execution-lease-and-wrapper-authoring"
    ):
        raise QWakeLC4ExecutionWrapperError(
            "frozen admission next slice differs"
        )

    source = _as_mapping(receipt.get("source"), "receipt.source")
    if source.get("control_plane_merge_commit") != (
        ADMISSION_CONTROL_PLANE_COMMIT
    ):
        raise QWakeLC4ExecutionWrapperError(
            "receipt control-plane commit differs"
        )
    if source.get("torch2pc_commit") != FROZEN_TORCH2PC_COMMIT:
        raise QWakeLC4ExecutionWrapperError(
            "receipt Torch2PC identity differs"
        )

    gates = _as_mapping(receipt.get("gates"), "receipt.gates")
    expected_gates: Mapping[str, bool] = {
        "execution_admission_issued": True,
        "admission_record_runtime_execution_permitted": True,
        "qw_lc4_e_execution_permitted": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "engineering_evidence_present": False,
        "scientific_execution_open": False,
        "test_dataset_access": False,
        "publication_permitted": False,
        "local_compute_execution_open": False,
    }
    for key, expected in expected_gates.items():
        if gates.get(key) is not expected:
            raise QWakeLC4ExecutionWrapperError(
                f"frozen admission receipt gate differs: {key}"
            )

    capabilities = _as_mapping(
        receipt.get("capabilities"),
        "receipt.capabilities",
    )
    if any(value is not False for value in capabilities.values()):
        raise QWakeLC4ExecutionWrapperError(
            "frozen admission already contains an effectful capability"
        )

    matrix = _verify_runtime_matrix(
        root / RUNTIME_FREEZE_ROOT_RELATIVE / "authorization.json"
    )
    identity = FrozenAdmissionIdentity(
        freeze_id=ADMISSION_FREEZE_ID,
        freeze_merge_commit=ADMISSION_FREEZE_MERGE_COMMIT,
        freeze_head_commit=ADMISSION_FREEZE_HEAD_COMMIT,
        control_plane_commit=admission.control_plane_commit,
        admission_id=admission.admission_id,
        admission_sha256=admission.admission_sha256,
        admission_file_sha256=_sha256_file(admission_path),
        receipt_file_sha256=_sha256_file(receipt_path),
        package_registry_sha256=_sha256_file(
            freeze_root / "SHA256SUMS"
        ),
        source_registry_sha256=_sha256_file(
            freeze_root / "source-SHA256SUMS"
        ),
        torch2pc_commit=admission.frozen_runtime.torch2pc_commit,
        image_digest=admission.frozen_runtime.image_digest,
        authorization_sha256=admission.frozen_runtime.authorization_sha256,
        output_root=admission.frozen_runtime.output_root,
        execution_lease_relative=EXECUTION_LEASE_RELATIVE.as_posix(),
        authorized_cell_count=matrix["authorized_cell_count"],
        reserve_probe_count=matrix["reserve_probe_count"],
        lane_order=matrix["lane_order"],
        execution_count=admission.execution_count,
        runtime_execution_permitted=admission.runtime_execution_permitted,
        authorization_consumed=admission.authorization_consumed,
        runtime_execution_started=admission.runtime_execution_started,
        runtime_execution_performed=admission.runtime_execution_performed,
        engineering_evidence_present=admission.engineering_evidence_present,
        scientific_execution_open=admission.scientific_execution_open,
        test_dataset_access=admission.test_dataset_access,
        publication_permitted=admission.publication_permitted,
    )
    identity.require()
    return identity


def build_prospective_execution_lease(
    frozen_admission: FrozenAdmissionIdentity,
    *,
    claimed_at_utc: str,
    wrapper_commit: str,
    operator_acknowledgement: str,
    output_root_absent_at_claim: bool,
    execution_lease_absent_at_claim: bool,
) -> ProspectiveExecutionLease:
    """Build an in-memory lease record without creating the lease file."""

    frozen_admission.require()
    if operator_acknowledgement != (
        EXECUTION_LEASE_OPERATOR_ACKNOWLEDGEMENT
    ):
        raise QWakeLC4ExecutionWrapperError(
            "operator acknowledgement does not claim QW-LC4-E"
        )
    payload: dict[str, object] = {
        "schema_version": 1,
        "lease_id": EXECUTION_LEASE_ID,
        "status": EXECUTION_LEASE_STATUS,
        "claimed_at_utc": claimed_at_utc,
        "operator_acknowledgement": operator_acknowledgement,
        "wrapper_commit": wrapper_commit,
        "admission_freeze_merge_commit": (
            frozen_admission.freeze_merge_commit
        ),
        "admission_id": frozen_admission.admission_id,
        "admission_sha256": frozen_admission.admission_sha256,
        "admission_file_sha256": frozen_admission.admission_file_sha256,
        "torch2pc_commit": frozen_admission.torch2pc_commit,
        "image_digest": frozen_admission.image_digest,
        "authorization_sha256": frozen_admission.authorization_sha256,
        "output_root": frozen_admission.output_root,
        "execution_lease_relative": (
            frozen_admission.execution_lease_relative
        ),
        "output_root_absent_at_claim": output_root_absent_at_claim,
        "execution_lease_absent_at_claim": execution_lease_absent_at_claim,
        "execution_count": 1,
        "authorization_consumed": True,
        "runtime_execution_permitted": True,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "engineering_evidence_present": False,
        "scientific_execution_open": False,
        "test_dataset_access": False,
        "publication_permitted": False,
    }
    lease = ProspectiveExecutionLease(
        schema_version=1,
        lease_id=EXECUTION_LEASE_ID,
        status=EXECUTION_LEASE_STATUS,
        claimed_at_utc=claimed_at_utc,
        operator_acknowledgement=operator_acknowledgement,
        wrapper_commit=wrapper_commit,
        admission_freeze_merge_commit=(
            frozen_admission.freeze_merge_commit
        ),
        admission_id=frozen_admission.admission_id,
        admission_sha256=frozen_admission.admission_sha256,
        admission_file_sha256=frozen_admission.admission_file_sha256,
        torch2pc_commit=frozen_admission.torch2pc_commit,
        image_digest=frozen_admission.image_digest,
        authorization_sha256=frozen_admission.authorization_sha256,
        output_root=frozen_admission.output_root,
        execution_lease_relative=(
            frozen_admission.execution_lease_relative
        ),
        output_root_absent_at_claim=output_root_absent_at_claim,
        execution_lease_absent_at_claim=execution_lease_absent_at_claim,
        execution_count=1,
        authorization_consumed=True,
        runtime_execution_permitted=True,
        runtime_execution_started=False,
        runtime_execution_performed=False,
        engineering_evidence_present=False,
        scientific_execution_open=False,
        test_dataset_access=False,
        publication_permitted=False,
        lease_sha256=sha256_object(payload),
    )
    lease.require()
    return lease


def validate_prospective_execution_lease(
    lease: ProspectiveExecutionLease,
    frozen_admission: FrozenAdmissionIdentity,
    project_root: Path,
    *,
    expected_wrapper_commit: str,
) -> None:
    """Validate an unmaterialized claim while preserving zero effects."""

    lease.require()
    frozen_admission.require()
    if lease.wrapper_commit != expected_wrapper_commit:
        raise QWakeLC4ExecutionWrapperError(
            "prospective lease wrapper commit differs"
        )
    if lease.admission_sha256 != frozen_admission.admission_sha256:
        raise QWakeLC4ExecutionWrapperError(
            "prospective lease admission identity differs"
        )
    root = project_root.expanduser().resolve()
    if (root / AUTHORIZED_OUTPUT_ROOT).exists():
        raise QWakeLC4ExecutionWrapperError(
            "authorized output root already exists"
        )
    if (root / EXECUTION_LEASE_RELATIVE).exists():
        raise QWakeLC4ExecutionWrapperError(
            "execution lease already exists"
        )


def build_execution_wrapper_contract(
    lease: ProspectiveExecutionLease,
) -> ExecutionWrapperContract:
    """Build the future wrapper effect contract without enabling effects."""

    lease.require()
    payload: dict[str, object] = {
        "schema_version": 1,
        "contract_id": EXECUTION_WRAPPER_CONTRACT_ID,
        "status": EXECUTION_WRAPPER_CONTRACT_STATUS,
        "wrapper_commit": lease.wrapper_commit,
        "lease_id": lease.lease_id,
        "lease_sha256": lease.lease_sha256,
        "admission_freeze_merge_commit": lease.admission_freeze_merge_commit,
        "torch2pc_commit": lease.torch2pc_commit,
        "image_digest": lease.image_digest,
        "authorization_sha256": lease.authorization_sha256,
        "output_root": lease.output_root,
        "execution_lease_relative": lease.execution_lease_relative,
        "lane_order": RUNTIME_LANE_ORDER,
        "authorized_cell_count": AUTHORIZED_CELL_COUNT,
        "reserve_probe_count": RESERVE_PROBE_COUNT,
        "execution_count": 1,
        "exclusive_atomic_lease_claim_required": True,
        "lease_persists_after_failure": True,
        "retry_after_claim_permitted": False,
        "atomic_output_promotion_required": True,
        "fail_closed_on_existing_output": True,
        "fail_closed_on_existing_lease": True,
        "authorization_consumed_after_claim": True,
        "runtime_execution_permitted_after_claim": True,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "engineering_evidence_present": False,
        "scientific_execution_open": False,
        "test_dataset_access": False,
        "publication_permitted": False,
    }
    contract = ExecutionWrapperContract(
        schema_version=1,
        contract_id=EXECUTION_WRAPPER_CONTRACT_ID,
        status=EXECUTION_WRAPPER_CONTRACT_STATUS,
        wrapper_commit=lease.wrapper_commit,
        lease_id=lease.lease_id,
        lease_sha256=lease.lease_sha256,
        admission_freeze_merge_commit=lease.admission_freeze_merge_commit,
        torch2pc_commit=lease.torch2pc_commit,
        image_digest=lease.image_digest,
        authorization_sha256=lease.authorization_sha256,
        output_root=lease.output_root,
        execution_lease_relative=lease.execution_lease_relative,
        lane_order=RUNTIME_LANE_ORDER,
        authorized_cell_count=AUTHORIZED_CELL_COUNT,
        reserve_probe_count=RESERVE_PROBE_COUNT,
        execution_count=1,
        exclusive_atomic_lease_claim_required=True,
        lease_persists_after_failure=True,
        retry_after_claim_permitted=False,
        atomic_output_promotion_required=True,
        fail_closed_on_existing_output=True,
        fail_closed_on_existing_lease=True,
        authorization_consumed_after_claim=True,
        runtime_execution_permitted_after_claim=True,
        runtime_execution_started=False,
        runtime_execution_performed=False,
        engineering_evidence_present=False,
        scientific_execution_open=False,
        test_dataset_access=False,
        publication_permitted=False,
        contract_sha256=sha256_object(payload),
    )
    contract.require()
    return contract


def validate_execution_wrapper_contract(
    contract: ExecutionWrapperContract,
    lease: ProspectiveExecutionLease,
) -> None:
    """Validate exact prospective lease-to-wrapper binding."""

    contract.require()
    lease.require()
    if contract.wrapper_commit != lease.wrapper_commit:
        raise QWakeLC4ExecutionWrapperError(
            "wrapper contract commit differs from lease"
        )
    if contract.lease_id != lease.lease_id:
        raise QWakeLC4ExecutionWrapperError(
            "wrapper contract lease id differs"
        )
    if contract.lease_sha256 != lease.lease_sha256:
        raise QWakeLC4ExecutionWrapperError(
            "wrapper contract lease digest differs"
        )


def load_prospective_execution_lease(path: Path) -> ProspectiveExecutionLease:
    """Load and strictly validate a prospective lease JSON object."""

    payload = _read_json_object(path)
    lease = ProspectiveExecutionLease(
        schema_version=_as_int(payload.get("schema_version"), "schema_version"),
        lease_id=_as_str(payload.get("lease_id"), "lease_id"),
        status=_as_str(payload.get("status"), "status"),
        claimed_at_utc=_as_str(payload.get("claimed_at_utc"), "claimed_at_utc"),
        operator_acknowledgement=_as_str(
            payload.get("operator_acknowledgement"),
            "operator_acknowledgement",
        ),
        wrapper_commit=_as_str(payload.get("wrapper_commit"), "wrapper_commit"),
        admission_freeze_merge_commit=_as_str(
            payload.get("admission_freeze_merge_commit"),
            "admission_freeze_merge_commit",
        ),
        admission_id=_as_str(payload.get("admission_id"), "admission_id"),
        admission_sha256=_as_str(
            payload.get("admission_sha256"),
            "admission_sha256",
        ),
        admission_file_sha256=_as_str(
            payload.get("admission_file_sha256"),
            "admission_file_sha256",
        ),
        torch2pc_commit=_as_str(
            payload.get("torch2pc_commit"),
            "torch2pc_commit",
        ),
        image_digest=_as_str(payload.get("image_digest"), "image_digest"),
        authorization_sha256=_as_str(
            payload.get("authorization_sha256"),
            "authorization_sha256",
        ),
        output_root=_as_str(payload.get("output_root"), "output_root"),
        execution_lease_relative=_as_str(
            payload.get("execution_lease_relative"),
            "execution_lease_relative",
        ),
        output_root_absent_at_claim=_as_bool(
            payload.get("output_root_absent_at_claim"),
            "output_root_absent_at_claim",
        ),
        execution_lease_absent_at_claim=_as_bool(
            payload.get("execution_lease_absent_at_claim"),
            "execution_lease_absent_at_claim",
        ),
        execution_count=_as_int(
            payload.get("execution_count"),
            "execution_count",
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
        lease_sha256=_as_str(payload.get("lease_sha256"), "lease_sha256"),
    )
    lease.require()
    return lease


def load_execution_wrapper_contract(path: Path) -> ExecutionWrapperContract:
    """Load and strictly validate a prospective wrapper contract."""

    payload = _read_json_object(path)
    lane_order_raw = _as_sequence(payload.get("lane_order"), "lane_order")
    contract = ExecutionWrapperContract(
        schema_version=_as_int(payload.get("schema_version"), "schema_version"),
        contract_id=_as_str(payload.get("contract_id"), "contract_id"),
        status=_as_str(payload.get("status"), "status"),
        wrapper_commit=_as_str(payload.get("wrapper_commit"), "wrapper_commit"),
        lease_id=_as_str(payload.get("lease_id"), "lease_id"),
        lease_sha256=_as_str(payload.get("lease_sha256"), "lease_sha256"),
        admission_freeze_merge_commit=_as_str(
            payload.get("admission_freeze_merge_commit"),
            "admission_freeze_merge_commit",
        ),
        torch2pc_commit=_as_str(
            payload.get("torch2pc_commit"),
            "torch2pc_commit",
        ),
        image_digest=_as_str(payload.get("image_digest"), "image_digest"),
        authorization_sha256=_as_str(
            payload.get("authorization_sha256"),
            "authorization_sha256",
        ),
        output_root=_as_str(payload.get("output_root"), "output_root"),
        execution_lease_relative=_as_str(
            payload.get("execution_lease_relative"),
            "execution_lease_relative",
        ),
        lane_order=tuple(_as_str(item, "lane_order item") for item in lane_order_raw),
        authorized_cell_count=_as_int(
            payload.get("authorized_cell_count"),
            "authorized_cell_count",
        ),
        reserve_probe_count=_as_int(
            payload.get("reserve_probe_count"),
            "reserve_probe_count",
        ),
        execution_count=_as_int(
            payload.get("execution_count"),
            "execution_count",
        ),
        exclusive_atomic_lease_claim_required=_as_bool(
            payload.get("exclusive_atomic_lease_claim_required"),
            "exclusive_atomic_lease_claim_required",
        ),
        lease_persists_after_failure=_as_bool(
            payload.get("lease_persists_after_failure"),
            "lease_persists_after_failure",
        ),
        retry_after_claim_permitted=_as_bool(
            payload.get("retry_after_claim_permitted"),
            "retry_after_claim_permitted",
        ),
        atomic_output_promotion_required=_as_bool(
            payload.get("atomic_output_promotion_required"),
            "atomic_output_promotion_required",
        ),
        fail_closed_on_existing_output=_as_bool(
            payload.get("fail_closed_on_existing_output"),
            "fail_closed_on_existing_output",
        ),
        fail_closed_on_existing_lease=_as_bool(
            payload.get("fail_closed_on_existing_lease"),
            "fail_closed_on_existing_lease",
        ),
        authorization_consumed_after_claim=_as_bool(
            payload.get("authorization_consumed_after_claim"),
            "authorization_consumed_after_claim",
        ),
        runtime_execution_permitted_after_claim=_as_bool(
            payload.get("runtime_execution_permitted_after_claim"),
            "runtime_execution_permitted_after_claim",
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
        contract_sha256=_as_str(
            payload.get("contract_sha256"),
            "contract_sha256",
        ),
    )
    contract.require()
    return contract


def canonical_json(value: object) -> str:
    """Return deterministic UTF-8 JSON with a trailing newline."""

    if hasattr(value, "__dataclass_fields__"):
        value = asdict(cast(Any, value))
    return (
        json.dumps(
            _canonicalize(value),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    )


def sha256_object(value: object) -> str:
    """Return a prefixed SHA-256 over canonical JSON bytes."""

    return "sha256:" + hashlib.sha256(
        canonical_json(value).encode("utf-8")
    ).hexdigest()


def _verify_runtime_matrix(path: Path) -> dict[str, Any]:
    authorization = _read_json_object(path)
    if authorization.get("authorization_sha256") != (
        FROZEN_AUTHORIZATION_SHA256
    ):
        raise QWakeLC4ExecutionWrapperError(
            "runtime authorization semantic identity differs"
        )
    cells = _as_sequence(authorization.get("cells"), "authorization.cells")
    if len(cells) != AUTHORIZED_CELL_COUNT:
        raise QWakeLC4ExecutionWrapperError(
            "runtime authorization cell count differs"
        )

    lanes: list[str] = []
    reserve_count = 0
    observed: set[tuple[str, int, int]] = set()
    for cell_raw in cells:
        cell = _as_mapping(cell_raw, "authorization cell")
        lane = _as_str(cell.get("lane"), "cell.lane")
        candidate_index = _as_int(
            cell.get("candidate_index"),
            "cell.candidate_index",
        )
        repeat_index = _as_int(
            cell.get("repeat_index"),
            "cell.repeat_index",
        )
        if lane not in RUNTIME_LANE_ORDER:
            raise QWakeLC4ExecutionWrapperError(
                "runtime authorization lane differs"
            )
        if not 0 <= candidate_index < 7:
            raise QWakeLC4ExecutionWrapperError(
                "runtime candidate index differs"
            )
        if not 0 <= repeat_index < 12:
            raise QWakeLC4ExecutionWrapperError(
                "runtime repeat index differs"
            )
        expected_order = (
            "exact_reference_then_analytic_candidate"
            if repeat_index % 2 == 0
            else "analytic_candidate_then_exact_reference"
        )
        if cell.get("arm_order") != expected_order:
            raise QWakeLC4ExecutionWrapperError(
                "runtime arm order differs"
            )
        before = _as_bool(
            cell.get("reserve_probe_before_repeat_zero"),
            "cell.reserve_probe_before_repeat_zero",
        )
        after = _as_bool(
            cell.get("reserve_probe_after_repeat_eleven"),
            "cell.reserve_probe_after_repeat_eleven",
        )
        if before != (repeat_index == 0):
            raise QWakeLC4ExecutionWrapperError(
                "before-repeat reserve probe placement differs"
            )
        if after != (repeat_index == 11):
            raise QWakeLC4ExecutionWrapperError(
                "after-repeat reserve probe placement differs"
            )
        reserve_count += int(before) + int(after)
        observed.add((lane, candidate_index, repeat_index))
        if not lanes or lanes[-1] != lane:
            lanes.append(lane)

    expected = {
        (lane, candidate_index, repeat_index)
        for lane in RUNTIME_LANE_ORDER
        for candidate_index in range(7)
        for repeat_index in range(12)
    }
    if observed != expected:
        raise QWakeLC4ExecutionWrapperError(
            "runtime authorization matrix differs"
        )
    lane_order = tuple(lanes)
    if lane_order != RUNTIME_LANE_ORDER:
        raise QWakeLC4ExecutionWrapperError(
            "runtime lane order differs"
        )
    if reserve_count != RESERVE_PROBE_COUNT:
        raise QWakeLC4ExecutionWrapperError(
            "runtime reserve-probe count differs"
        )
    return {
        "authorized_cell_count": len(cells),
        "reserve_probe_count": reserve_count,
        "lane_order": lane_order,
    }


def _verify_registry(registry_path: Path, base: Path) -> None:
    if not registry_path.is_file() or registry_path.is_symlink():
        raise QWakeLC4ExecutionWrapperError(
            f"checksum registry is absent: {registry_path}"
        )
    lines = registry_path.read_text(encoding="utf-8").splitlines()
    if not lines:
        raise QWakeLC4ExecutionWrapperError("checksum registry is empty")
    observed: set[str] = set()
    for line in lines:
        try:
            expected, relative = line.split("  ", 1)
        except ValueError as exc:
            raise QWakeLC4ExecutionWrapperError(
                "checksum registry line is malformed"
            ) from exc
        if relative in observed:
            raise QWakeLC4ExecutionWrapperError(
                f"duplicate checksum registry entry: {relative}"
            )
        target = base / relative
        if not target.is_file() or target.is_symlink():
            raise QWakeLC4ExecutionWrapperError(
                f"checksum target is not a regular file: {relative}"
            )
        if hashlib.sha256(target.read_bytes()).hexdigest() != expected:
            raise QWakeLC4ExecutionWrapperError(
                f"checksum target differs: {relative}"
            )
        observed.add(relative)


def _read_json_object(path: Path) -> dict[str, object]:
    if not path.is_file() or path.is_symlink():
        raise QWakeLC4ExecutionWrapperError(f"JSON file is absent: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise QWakeLC4ExecutionWrapperError(
            f"JSON object expected: {path}"
        )
    return cast(dict[str, object], value)


def _sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _require_commit(value: str, field_name: str) -> None:
    if not _COMMIT_PATTERN.fullmatch(value):
        raise QWakeLC4ExecutionWrapperError(
            f"{field_name} is not a commit"
        )


def _require_sha256(value: str, field_name: str) -> None:
    if not _SHA256_PATTERN.fullmatch(value):
        raise QWakeLC4ExecutionWrapperError(
            f"{field_name} is not a SHA-256 identity"
        )


def _require_utc(value: str, field_name: str) -> None:
    if not value.endswith("Z") or "T" not in value:
        raise QWakeLC4ExecutionWrapperError(
            f"{field_name} is not canonical UTC"
        )


def _as_mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise QWakeLC4ExecutionWrapperError(
            f"{field_name} must be an object"
        )
    return cast(Mapping[str, object], value)


def _as_sequence(value: object, field_name: str) -> Sequence[object]:
    if not isinstance(value, list):
        raise QWakeLC4ExecutionWrapperError(
            f"{field_name} must be an array"
        )
    return cast(Sequence[object], value)


def _as_str(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise QWakeLC4ExecutionWrapperError(
            f"{field_name} must be a non-empty string"
        )
    return value


def _as_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise QWakeLC4ExecutionWrapperError(
            f"{field_name} must be an integer"
        )
    return value


def _as_bool(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise QWakeLC4ExecutionWrapperError(
            f"{field_name} must be boolean"
        )
    return value


def _canonicalize(value: object) -> object:
    if hasattr(value, "__dataclass_fields__"):
        return _canonicalize(asdict(cast(Any, value)))
    if isinstance(value, Mapping):
        return {
            str(key): _canonicalize(item)
            for key, item in sorted(
                value.items(),
                key=lambda pair: str(pair[0]),
            )
        }
    if isinstance(value, tuple | list):
        return [_canonicalize(item) for item in value]
    if isinstance(value, Path):
        return value.as_posix()
    if value is None or isinstance(value, str | int | float | bool):
        return value
    raise QWakeLC4ExecutionWrapperError(
        f"unsupported canonical value: {type(value).__name__}"
    )
