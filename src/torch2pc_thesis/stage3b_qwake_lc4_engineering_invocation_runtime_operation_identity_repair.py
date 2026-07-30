"""Fail-closed identity repair for the merged QW-LC4-E runtime operation.

The historical ADR-081 and runtime-operation-v1 package are preserved exactly.
This module adds a non-retroactive repair record that binds the corrected
runtime-operation source, verifier, tests, and bilingual ADRs to the merged
runtime-operation commit.  Verification is effect free and keeps execution
closed until later persistent-lease and durable-outcome contracts are merged.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Final, cast

IDENTITY_REPAIR_ID: Final = (
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-"
    "runtime-operation-identity-repair-v1"
)
IDENTITY_REPAIR_STATUS: Final = (
    "runtime_operation_identity_repaired_execution_closed"
)
RUNTIME_OPERATION_ID: Final = (
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-runtime-operation-v1"
)
RUNTIME_OPERATION_SHA256: Final = (
    "sha256:0332428014f7f8385c789ba7e7c55d6c2ec03b020e3f83df9ac9714483bb6bf8"
)
RUNTIME_OPERATION_RECORD_SHA256: Final = (
    "sha256:ba9b514980bf5f8629cc6a140a0b95114689020a4cffb8bf3ce4a58fade10247"
)
RUNTIME_OPERATION_REGISTRY_SHA256: Final = (
    "sha256:d213e051076a1990b268abfd28dcb4d98c699865fc19039ebfece50761f5e46c"
)
RUNTIME_OPERATION_BASE_COMMIT: Final = (
    "494e6a0b2f10c26b49c90fbb84c23565699a4064"
)
RUNTIME_OPERATION_HEAD_COMMIT: Final = (
    "423684f3e8eaad1858161503d63d514a5eeb9e5e"
)
RUNTIME_OPERATION_MERGE_COMMIT: Final = (
    "97dacb207aa201f1fd2f43c66ae34b1adced32bb"
)
RUNTIME_OPERATION_MERGED_AT_UTC: Final = "2026-07-30T00:31:26Z"
STALE_RUNTIME_OPERATION_MODULE_SHA256: Final = (
    "sha256:eb337b1f9cd1c95570d7ec22160886a43efe2531c9c5131b7ac29a84123115a4"
)

PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-"
    "runtime-operation-identity-repair-v1"
)
RECORD_RELATIVE: Final = PACKAGE_RELATIVE / "repair.json"
REGISTRY_RELATIVE: Final = PACKAGE_RELATIVE / "SHA256SUMS"
SOURCE_REGISTRY_RELATIVE: Final = PACKAGE_RELATIVE / "source-SHA256SUMS"

RUNTIME_OPERATION_PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-runtime-operation-v1"
)
RUNTIME_OPERATION_RECORD_RELATIVE: Final = (
    RUNTIME_OPERATION_PACKAGE_RELATIVE / "operation.json"
)
RUNTIME_OPERATION_REGISTRY_RELATIVE: Final = (
    RUNTIME_OPERATION_PACKAGE_RELATIVE / "SHA256SUMS"
)
RUNTIME_OPERATION_MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_engineering_invocation_runtime_operation.py"
)
RUNTIME_OPERATION_VERIFIER_RELATIVE: Final = Path(
    "scripts/verify_stage3b_qwake_lc4_engineering_invocation_"
    "runtime_operation.py"
)
RUNTIME_OPERATION_TEST_RELATIVE: Final = Path(
    "tests/unit/test_stage3b_qwake_lc4_engineering_invocation_"
    "runtime_operation.py"
)
ADR_RU_RELATIVE: Final = Path(
    "docs/decisions/ADR-081-stage3b-qwake-lc4-e-one-shot-engineering-"
    "invocation-runtime-operation.md"
)
ADR_EN_RELATIVE: Final = Path(
    "docs/decisions/ADR-081-stage3b-qwake-lc4-e-one-shot-engineering-"
    "invocation-runtime-operation_EN.md"
)
REPAIR_MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_engineering_invocation_runtime_operation_"
    "identity_repair.py"
)
REPAIR_VERIFIER_RELATIVE: Final = Path(
    "scripts/verify_stage3b_qwake_lc4_engineering_invocation_"
    "runtime_operation_identity_repair.py"
)
REPAIR_TEST_RELATIVE: Final = Path(
    "tests/unit/test_stage3b_qwake_lc4_engineering_invocation_"
    "runtime_operation_identity_repair.py"
)
REPAIR_ADR_RU_RELATIVE: Final = Path(
    "docs/decisions/ADR-082-stage3b-qwake-lc4-e-runtime-operation-"
    "identity-repair.md"
)
REPAIR_ADR_EN_RELATIVE: Final = Path(
    "docs/decisions/ADR-082-stage3b-qwake-lc4-e-runtime-operation-"
    "identity-repair_EN.md"
)

EXECUTION_LEASE_RELATIVE: Final = Path(
    "results/stage-3/"
    "qwake-lc4-runtime-validation-v1-attempt-001.execution-lease.json"
)
OUTPUT_ROOT_RELATIVE: Final = Path(
    "results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001"
)

_EXPECTED_PACKAGE_FILES: Final = frozenset(
    {"SHA256SUMS", "repair.json", "source-SHA256SUMS"}
)
_EXPECTED_SOURCE_PATHS: Final = frozenset(
    {
        RUNTIME_OPERATION_MODULE_RELATIVE.as_posix(),
        RUNTIME_OPERATION_VERIFIER_RELATIVE.as_posix(),
        RUNTIME_OPERATION_TEST_RELATIVE.as_posix(),
        ADR_RU_RELATIVE.as_posix(),
        ADR_EN_RELATIVE.as_posix(),
        REPAIR_MODULE_RELATIVE.as_posix(),
        REPAIR_VERIFIER_RELATIVE.as_posix(),
        REPAIR_TEST_RELATIVE.as_posix(),
        REPAIR_ADR_RU_RELATIVE.as_posix(),
        REPAIR_ADR_EN_RELATIVE.as_posix(),
    }
)
_SHA256_PATTERN: Final = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT_PATTERN: Final = re.compile(r"^[0-9a-f]{40}$")

__all__ = [
    "IDENTITY_REPAIR_ID",
    "IDENTITY_REPAIR_STATUS",
    "RuntimeOperationBoundSources",
    "RuntimeOperationIdentityRepair",
    "RuntimeOperationIdentityRepairContract",
    "RuntimeOperationIdentityRepairError",
    "RuntimeOperationIdentityRepairGates",
    "RuntimeOperationIdentityRepairSource",
    "build_runtime_operation_identity_repair",
    "canonical_json",
    "load_runtime_operation_identity_repair",
    "sha256_object",
    "verify_runtime_operation_identity_repair",
]


class RuntimeOperationIdentityRepairError(RuntimeError):
    """Raised when the runtime-operation identity repair fails closed."""


def canonical_json(value: object) -> str:
    """Return canonical JSON with one terminal newline."""

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"


def sha256_object(value: object) -> str:
    """Hash a canonical JSON object without the terminal newline."""

    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class RuntimeOperationIdentityRepairSource:
    runtime_operation_id: str
    runtime_operation_sha256: str
    runtime_operation_record_sha256: str
    runtime_operation_registry_sha256: str
    runtime_operation_base_commit: str
    runtime_operation_head_commit: str
    runtime_operation_merge_commit: str
    runtime_operation_merged_at_utc: str
    stale_runtime_operation_module_sha256: str

    def require(self) -> None:
        expected = RuntimeOperationIdentityRepairSource(
            runtime_operation_id=RUNTIME_OPERATION_ID,
            runtime_operation_sha256=RUNTIME_OPERATION_SHA256,
            runtime_operation_record_sha256=RUNTIME_OPERATION_RECORD_SHA256,
            runtime_operation_registry_sha256=RUNTIME_OPERATION_REGISTRY_SHA256,
            runtime_operation_base_commit=RUNTIME_OPERATION_BASE_COMMIT,
            runtime_operation_head_commit=RUNTIME_OPERATION_HEAD_COMMIT,
            runtime_operation_merge_commit=RUNTIME_OPERATION_MERGE_COMMIT,
            runtime_operation_merged_at_utc=RUNTIME_OPERATION_MERGED_AT_UTC,
            stale_runtime_operation_module_sha256=(
                STALE_RUNTIME_OPERATION_MODULE_SHA256
            ),
        )
        if self != expected:
            raise RuntimeOperationIdentityRepairError(
                "runtime-operation identity-repair source differs"
            )
        for name in (
            "runtime_operation_base_commit",
            "runtime_operation_head_commit",
            "runtime_operation_merge_commit",
        ):
            if _COMMIT_PATTERN.fullmatch(getattr(self, name)) is None:
                raise RuntimeOperationIdentityRepairError(
                    f"{name} is not a commit"
                )


@dataclass(frozen=True)
class RuntimeOperationBoundSources:
    runtime_operation_module_path: str
    runtime_operation_module_sha256: str
    runtime_operation_verifier_path: str
    runtime_operation_verifier_sha256: str
    runtime_operation_test_path: str
    runtime_operation_test_sha256: str
    adr_ru_path: str
    adr_ru_sha256: str
    adr_en_path: str
    adr_en_sha256: str

    def require(self) -> None:
        expected_paths = {
            "runtime_operation_module_path": (
                RUNTIME_OPERATION_MODULE_RELATIVE.as_posix()
            ),
            "runtime_operation_verifier_path": (
                RUNTIME_OPERATION_VERIFIER_RELATIVE.as_posix()
            ),
            "runtime_operation_test_path": (
                RUNTIME_OPERATION_TEST_RELATIVE.as_posix()
            ),
            "adr_ru_path": ADR_RU_RELATIVE.as_posix(),
            "adr_en_path": ADR_EN_RELATIVE.as_posix(),
        }
        for field_name, expected in expected_paths.items():
            if getattr(self, field_name) != expected:
                raise RuntimeOperationIdentityRepairError(
                    f"{field_name} differs"
                )
        for field_name in (
            "runtime_operation_module_sha256",
            "runtime_operation_verifier_sha256",
            "runtime_operation_test_sha256",
            "adr_ru_sha256",
            "adr_en_sha256",
        ):
            if _SHA256_PATTERN.fullmatch(getattr(self, field_name)) is None:
                raise RuntimeOperationIdentityRepairError(
                    f"{field_name} is not SHA-256"
                )
        if (
            self.runtime_operation_module_sha256
            == STALE_RUNTIME_OPERATION_MODULE_SHA256
        ):
            raise RuntimeOperationIdentityRepairError(
                "corrected runtime-operation module still has stale identity"
            )


@dataclass(frozen=True)
class RuntimeOperationIdentityRepairContract:
    historical_v1_package_preserved: bool
    corrected_source_registry_required: bool
    runtime_operation_verifier_requires_identity_repair: bool
    stale_identity_rejected: bool
    execution_blocked_until_repair_merge: bool
    persistent_lease_v2_required_before_execution: bool
    durable_negative_host_outcome_required_before_execution: bool
    frozen_evidence_rewrite_forbidden: bool

    def require(self) -> None:
        if not all(asdict(self).values()):
            raise RuntimeOperationIdentityRepairError(
                "runtime-operation identity-repair contract differs"
            )


@dataclass(frozen=True)
class RuntimeOperationIdentityRepairGates:
    identity_repair_record_present: bool
    corrected_source_identity_bound: bool
    runtime_operation_self_identity_verified: bool
    corrected_full_validation_receipt_present: bool
    runtime_operation_identity_repair_merged: bool
    latest_authorization_bound_in_persistent_lease: bool
    durable_negative_host_outcome_defined: bool
    final_execution_acknowledged: bool
    preexecution_identity_verified: bool
    one_shot_engineering_invocation_permitted: bool
    execution_lease_materialized: bool
    authorization_consumed: bool
    runtime_execution_started: bool
    runtime_execution_performed: bool
    image_inspection_performed: bool
    invocation_command_materialized: bool
    docker_run_performed: bool
    local_compute_execution_open: bool

    def require(self) -> None:
        expected = RuntimeOperationIdentityRepairGates(
            identity_repair_record_present=True,
            corrected_source_identity_bound=True,
            runtime_operation_self_identity_verified=True,
            corrected_full_validation_receipt_present=False,
            runtime_operation_identity_repair_merged=False,
            latest_authorization_bound_in_persistent_lease=False,
            durable_negative_host_outcome_defined=False,
            final_execution_acknowledged=False,
            preexecution_identity_verified=False,
            one_shot_engineering_invocation_permitted=False,
            execution_lease_materialized=False,
            authorization_consumed=False,
            runtime_execution_started=False,
            runtime_execution_performed=False,
            image_inspection_performed=False,
            invocation_command_materialized=False,
            docker_run_performed=False,
            local_compute_execution_open=False,
        )
        if self != expected:
            raise RuntimeOperationIdentityRepairError(
                "runtime-operation identity-repair gates differ"
            )


@dataclass(frozen=True)
class RuntimeOperationIdentityRepair:
    schema_version: int
    repair_id: str
    status: str
    recorded_at_utc: str
    source: RuntimeOperationIdentityRepairSource
    bound_sources: RuntimeOperationBoundSources
    contract: RuntimeOperationIdentityRepairContract
    gates: RuntimeOperationIdentityRepairGates
    next_slice: str
    post_merge_next_slice: str
    repair_sha256: str

    def semantic_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop("repair_sha256")
        return cast(dict[str, object], payload)

    def canonical_json(self) -> str:
        return canonical_json(asdict(self))

    def require(self) -> None:
        if self.schema_version != 1:
            raise RuntimeOperationIdentityRepairError(
                "runtime-operation identity-repair schema differs"
            )
        if self.repair_id != IDENTITY_REPAIR_ID:
            raise RuntimeOperationIdentityRepairError(
                "runtime-operation identity-repair id differs"
            )
        if self.status != IDENTITY_REPAIR_STATUS:
            raise RuntimeOperationIdentityRepairError(
                "runtime-operation identity-repair status differs"
            )
        self.source.require()
        self.bound_sources.require()
        self.contract.require()
        self.gates.require()
        if self.next_slice != "QW-LC4-E-runtime-operation-identity-repair-commit":
            raise RuntimeOperationIdentityRepairError(
                "runtime-operation identity-repair next slice differs"
            )
        if self.post_merge_next_slice != "QW-LC4-E-persistent-evidence-chain-v2":
            raise RuntimeOperationIdentityRepairError(
                "runtime-operation identity-repair post-merge slice differs"
            )
        if self.repair_sha256 != sha256_object(self.semantic_payload()):
            raise RuntimeOperationIdentityRepairError(
                "runtime-operation identity-repair semantic SHA-256 differs"
            )


def build_runtime_operation_identity_repair(
    *,
    recorded_at_utc: str,
    bound_sources: RuntimeOperationBoundSources,
) -> RuntimeOperationIdentityRepair:
    """Build the canonical identity-repair record."""

    partial = RuntimeOperationIdentityRepair(
        schema_version=1,
        repair_id=IDENTITY_REPAIR_ID,
        status=IDENTITY_REPAIR_STATUS,
        recorded_at_utc=recorded_at_utc,
        source=RuntimeOperationIdentityRepairSource(
            runtime_operation_id=RUNTIME_OPERATION_ID,
            runtime_operation_sha256=RUNTIME_OPERATION_SHA256,
            runtime_operation_record_sha256=RUNTIME_OPERATION_RECORD_SHA256,
            runtime_operation_registry_sha256=RUNTIME_OPERATION_REGISTRY_SHA256,
            runtime_operation_base_commit=RUNTIME_OPERATION_BASE_COMMIT,
            runtime_operation_head_commit=RUNTIME_OPERATION_HEAD_COMMIT,
            runtime_operation_merge_commit=RUNTIME_OPERATION_MERGE_COMMIT,
            runtime_operation_merged_at_utc=RUNTIME_OPERATION_MERGED_AT_UTC,
            stale_runtime_operation_module_sha256=(
                STALE_RUNTIME_OPERATION_MODULE_SHA256
            ),
        ),
        bound_sources=bound_sources,
        contract=RuntimeOperationIdentityRepairContract(
            historical_v1_package_preserved=True,
            corrected_source_registry_required=True,
            runtime_operation_verifier_requires_identity_repair=True,
            stale_identity_rejected=True,
            execution_blocked_until_repair_merge=True,
            persistent_lease_v2_required_before_execution=True,
            durable_negative_host_outcome_required_before_execution=True,
            frozen_evidence_rewrite_forbidden=True,
        ),
        gates=RuntimeOperationIdentityRepairGates(
            identity_repair_record_present=True,
            corrected_source_identity_bound=True,
            runtime_operation_self_identity_verified=True,
            corrected_full_validation_receipt_present=False,
            runtime_operation_identity_repair_merged=False,
            latest_authorization_bound_in_persistent_lease=False,
            durable_negative_host_outcome_defined=False,
            final_execution_acknowledged=False,
            preexecution_identity_verified=False,
            one_shot_engineering_invocation_permitted=False,
            execution_lease_materialized=False,
            authorization_consumed=False,
            runtime_execution_started=False,
            runtime_execution_performed=False,
            image_inspection_performed=False,
            invocation_command_materialized=False,
            docker_run_performed=False,
            local_compute_execution_open=False,
        ),
        next_slice="QW-LC4-E-runtime-operation-identity-repair-commit",
        post_merge_next_slice="QW-LC4-E-persistent-evidence-chain-v2",
        repair_sha256="",
    )
    record = replace(
        partial,
        repair_sha256=sha256_object(partial.semantic_payload()),
    )
    record.require()
    return record


def load_runtime_operation_identity_repair(
    path: Path,
) -> RuntimeOperationIdentityRepair:
    """Load a canonical identity-repair record."""

    data = _read_json_object(path)
    record = RuntimeOperationIdentityRepair(
        schema_version=cast(int, data.get("schema_version")),
        repair_id=cast(str, data.get("repair_id")),
        status=cast(str, data.get("status")),
        recorded_at_utc=cast(str, data.get("recorded_at_utc")),
        source=RuntimeOperationIdentityRepairSource(
            **cast(Any, _as_dict(data.get("source"), "source"))
        ),
        bound_sources=RuntimeOperationBoundSources(
            **cast(Any, _as_dict(data.get("bound_sources"), "bound_sources"))
        ),
        contract=RuntimeOperationIdentityRepairContract(
            **cast(Any, _as_dict(data.get("contract"), "contract"))
        ),
        gates=RuntimeOperationIdentityRepairGates(
            **cast(Any, _as_dict(data.get("gates"), "gates"))
        ),
        next_slice=cast(str, data.get("next_slice")),
        post_merge_next_slice=cast(str, data.get("post_merge_next_slice")),
        repair_sha256=cast(str, data.get("repair_sha256")),
    )
    record.require()
    return record


def verify_runtime_operation_identity_repair(
    project_root: Path,
) -> RuntimeOperationIdentityRepair:
    """Verify the repair package and all bound sources without effects."""

    root = project_root.expanduser().resolve()
    _require_effect_boundary_closed(root)
    _verify_historical_runtime_operation(root)
    package_registry = _verify_package(root)
    source_registry = _verify_source_registry(root)
    if package_registry != {
        "repair.json": _sha256_file(root / RECORD_RELATIVE),
        "source-SHA256SUMS": _sha256_file(root / SOURCE_REGISTRY_RELATIVE),
    }:
        raise RuntimeOperationIdentityRepairError(
            "runtime-operation identity-repair package registry differs"
        )

    record_path = root / RECORD_RELATIVE
    record = load_runtime_operation_identity_repair(record_path)
    if record_path.read_text(encoding="utf-8", errors="strict") != (
        record.canonical_json()
    ):
        raise RuntimeOperationIdentityRepairError(
            "runtime-operation identity-repair record is not canonical"
        )

    bound = record.bound_sources
    expected_bound = {
        bound.runtime_operation_module_path: (
            bound.runtime_operation_module_sha256
        ),
        bound.runtime_operation_verifier_path: (
            bound.runtime_operation_verifier_sha256
        ),
        bound.runtime_operation_test_path: bound.runtime_operation_test_sha256,
        bound.adr_ru_path: bound.adr_ru_sha256,
        bound.adr_en_path: bound.adr_en_sha256,
    }
    for relative, expected_sha256 in expected_bound.items():
        if source_registry.get(relative) != expected_sha256:
            raise RuntimeOperationIdentityRepairError(
                f"bound source registry identity differs: {relative}"
            )

    expected = build_runtime_operation_identity_repair(
        recorded_at_utc=record.recorded_at_utc,
        bound_sources=RuntimeOperationBoundSources(
            runtime_operation_module_path=(
                RUNTIME_OPERATION_MODULE_RELATIVE.as_posix()
            ),
            runtime_operation_module_sha256=source_registry[
                RUNTIME_OPERATION_MODULE_RELATIVE.as_posix()
            ],
            runtime_operation_verifier_path=(
                RUNTIME_OPERATION_VERIFIER_RELATIVE.as_posix()
            ),
            runtime_operation_verifier_sha256=source_registry[
                RUNTIME_OPERATION_VERIFIER_RELATIVE.as_posix()
            ],
            runtime_operation_test_path=(
                RUNTIME_OPERATION_TEST_RELATIVE.as_posix()
            ),
            runtime_operation_test_sha256=source_registry[
                RUNTIME_OPERATION_TEST_RELATIVE.as_posix()
            ],
            adr_ru_path=ADR_RU_RELATIVE.as_posix(),
            adr_ru_sha256=source_registry[ADR_RU_RELATIVE.as_posix()],
            adr_en_path=ADR_EN_RELATIVE.as_posix(),
            adr_en_sha256=source_registry[ADR_EN_RELATIVE.as_posix()],
        ),
    )
    if record != expected:
        raise RuntimeOperationIdentityRepairError(
            "runtime-operation identity-repair record differs from reconstruction"
        )

    _verify_runtime_operation_ast(root / RUNTIME_OPERATION_MODULE_RELATIVE)
    _verify_documented_identities(root, record)
    _require_effect_boundary_closed(root)
    return record


def _verify_historical_runtime_operation(root: Path) -> None:
    package = root / RUNTIME_OPERATION_PACKAGE_RELATIVE
    if not package.is_dir() or package.is_symlink():
        raise RuntimeOperationIdentityRepairError(
            "historical runtime-operation package is absent"
        )
    observed = frozenset(path.name for path in package.iterdir())
    if observed != frozenset({"SHA256SUMS", "operation.json"}):
        raise RuntimeOperationIdentityRepairError(
            "historical runtime-operation package scope differs"
        )
    if (
        _sha256_file(root / RUNTIME_OPERATION_RECORD_RELATIVE)
        != RUNTIME_OPERATION_RECORD_SHA256
    ):
        raise RuntimeOperationIdentityRepairError(
            "historical runtime-operation record SHA-256 differs"
        )
    if (
        _sha256_file(root / RUNTIME_OPERATION_REGISTRY_RELATIVE)
        != RUNTIME_OPERATION_REGISTRY_SHA256
    ):
        raise RuntimeOperationIdentityRepairError(
            "historical runtime-operation registry SHA-256 differs"
        )
    payload = _read_json_object(root / RUNTIME_OPERATION_RECORD_RELATIVE)
    if payload.get("operation_id") != RUNTIME_OPERATION_ID:
        raise RuntimeOperationIdentityRepairError(
            "historical runtime-operation id differs"
        )
    if payload.get("operation_sha256") != RUNTIME_OPERATION_SHA256:
        raise RuntimeOperationIdentityRepairError(
            "historical runtime-operation semantic SHA-256 differs"
        )


def _verify_package(root: Path) -> dict[str, str]:
    package = root / PACKAGE_RELATIVE
    if not package.is_dir() or package.is_symlink():
        raise RuntimeOperationIdentityRepairError(
            "runtime-operation identity-repair package is absent"
        )
    observed = frozenset(path.name for path in package.iterdir())
    if observed != _EXPECTED_PACKAGE_FILES:
        raise RuntimeOperationIdentityRepairError(
            "runtime-operation identity-repair package scope differs"
        )
    registry = _read_registry(root / REGISTRY_RELATIVE)
    if frozenset(registry) != frozenset({"repair.json", "source-SHA256SUMS"}):
        raise RuntimeOperationIdentityRepairError(
            "runtime-operation identity-repair package registry scope differs"
        )
    return registry


def _verify_source_registry(root: Path) -> dict[str, str]:
    registry = _read_registry(root / SOURCE_REGISTRY_RELATIVE)
    if frozenset(registry) != _EXPECTED_SOURCE_PATHS:
        raise RuntimeOperationIdentityRepairError(
            "runtime-operation identity-repair source registry scope differs"
        )
    for relative, expected_sha256 in registry.items():
        actual = _sha256_file(root / relative)
        if actual != expected_sha256:
            raise RuntimeOperationIdentityRepairError(
                f"runtime-operation repaired source SHA-256 differs: {relative}"
            )
    return registry


def _verify_runtime_operation_ast(module_path: Path) -> None:
    tree = ast.parse(module_path.read_text(encoding="utf-8", errors="strict"))
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    }
    verifier = functions.get("verify_engineering_invocation_runtime_operation")
    executor = functions.get(
        "execute_one_shot_engineering_invocation_runtime_operation"
    )
    if verifier is None or executor is None:
        raise RuntimeOperationIdentityRepairError(
            "runtime-operation verifier or executor is absent"
        )
    verifier_calls = [
        node.func.id
        for node in ast.walk(verifier)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    ]
    if verifier_calls.count("verify_runtime_operation_identity_repair") != 1:
        raise RuntimeOperationIdentityRepairError(
            "runtime-operation verifier does not require identity repair once"
        )
    executor_calls = [
        node.func.id
        for node in ast.walk(executor)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    ]
    if executor_calls.count("invoke_one_shot_host_runtime") != 1:
        raise RuntimeOperationIdentityRepairError(
            "runtime-operation executor host invocation count differs"
        )


def _verify_documented_identities(
    root: Path,
    record: RuntimeOperationIdentityRepair,
) -> None:
    stale = record.source.stale_runtime_operation_module_sha256
    corrected = record.bound_sources.runtime_operation_module_sha256
    for relative in (ADR_RU_RELATIVE, ADR_EN_RELATIVE):
        text = (root / relative).read_text(encoding="utf-8", errors="strict")
        if stale not in text:
            raise RuntimeOperationIdentityRepairError(
                f"historical ADR no longer preserves stale identity: {relative}"
            )
    for relative in (REPAIR_ADR_RU_RELATIVE, REPAIR_ADR_EN_RELATIVE):
        text = (root / relative).read_text(encoding="utf-8", errors="strict")
        for marker in (record.repair_sha256, stale, corrected):
            if marker not in text:
                raise RuntimeOperationIdentityRepairError(
                    f"repair ADR identity marker is absent: {relative}"
                )


def _read_registry(path: Path) -> dict[str, str]:
    if not path.is_file() or path.is_symlink():
        raise RuntimeOperationIdentityRepairError(
            f"registry is absent or non-regular: {path}"
        )
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="strict").splitlines():
        if not line or "  " not in line:
            raise RuntimeOperationIdentityRepairError(
                f"registry line differs: {path}"
            )
        digest, relative = line.split("  ", 1)
        identity = "sha256:" + digest
        if _SHA256_PATTERN.fullmatch(identity) is None:
            raise RuntimeOperationIdentityRepairError(
                f"registry digest is not SHA-256: {path}"
            )
        if relative in result:
            raise RuntimeOperationIdentityRepairError(
                f"registry contains duplicate path: {relative}"
            )
        result[relative] = identity
    return result


def _require_effect_boundary_closed(root: Path) -> None:
    lease = root / EXECUTION_LEASE_RELATIVE
    output = root / OUTPUT_ROOT_RELATIVE
    if lease.exists() or lease.is_symlink():
        raise RuntimeOperationIdentityRepairError(
            "repository execution lease already exists"
        )
    if output.exists() or output.is_symlink():
        raise RuntimeOperationIdentityRepairError(
            "repository runtime output already exists"
        )
    if tuple(output.parent.glob(f".{output.name}.staging-*")):
        raise RuntimeOperationIdentityRepairError(
            "repository runtime staging tree already exists"
        )


def _read_json_object(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise RuntimeOperationIdentityRepairError(
            f"JSON source is absent or non-regular: {path}"
        )
    value = json.loads(path.read_text(encoding="utf-8", errors="strict"))
    if not isinstance(value, dict):
        raise RuntimeOperationIdentityRepairError(
            f"JSON source is not an object: {path}"
        )
    return cast(dict[str, Any], value)


def _as_dict(value: object, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RuntimeOperationIdentityRepairError(
            f"{field_name} is not an object"
        )
    return cast(dict[str, Any], value)


def _sha256_file(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise RuntimeOperationIdentityRepairError(
            f"source is absent or non-regular: {path}"
        )
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
