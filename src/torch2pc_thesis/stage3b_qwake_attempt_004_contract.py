"""Attempt-004 identities and fail-closed admission verification.

This module defines a new effect namespace for a future QW-LC4-E engineering
attempt.  Importing it has no effects.  Freeze and authorization files are
verified only when an explicit function is called; no file is created here.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Any, Final, cast

ATTEMPT_004_ID: Final = "stage3b-qwake-lc4-runtime-validation-v1-attempt-004"
ATTEMPT_004_OUTPUT_ROOT: Final = Path(
    "results/stage-3/qwake-lc4-runtime-validation-v1-attempt-004"
)
ATTEMPT_004_LEASE_V1_RELATIVE: Final = Path(
    str(ATTEMPT_004_OUTPUT_ROOT) + ".execution-lease.json"
)
ATTEMPT_004_LEASE_V2_RELATIVE: Final = Path(
    str(ATTEMPT_004_OUTPUT_ROOT) + ".execution-lease-v2.json"
)
ATTEMPT_004_DURABLE_OUTCOME_RELATIVE: Final = Path(
    str(ATTEMPT_004_OUTPUT_ROOT) + ".host-outcome.json"
)
ATTEMPT_004_FREEZE_ROOT: Final = Path(
    "experiments/frozen/stage3b-qwake-attempt-004-execution-freeze-v1"
)
ATTEMPT_004_FREEZE_RELATIVE: Final = ATTEMPT_004_FREEZE_ROOT / "execution.json"
ATTEMPT_004_AUTHORIZATION_ROOT: Final = Path(
    "experiments/frozen/stage3b-qwake-attempt-004-authorization-v1"
)
ATTEMPT_004_AUTHORIZATION_RELATIVE: Final = (
    ATTEMPT_004_AUTHORIZATION_ROOT / "authorization.json"
)
SCIENTIFIC_RUNTIME_AUTHORIZATION_RELATIVE: Final = Path(
    "experiments/frozen/stage3b-qwake-lc4-f-runtime-freeze-v1/authorization.json"
)
ATTEMPT_004_CONTRACT_RELATIVE: Final = Path(
    "src/torch2pc_thesis/stage3b_qwake_attempt_004_contract.py"
)
ATTEMPT_004_WRAPPER_RELATIVE: Final = Path(
    "src/torch2pc_thesis/stage3b_qwake_attempt_004_execution_wrapper.py"
)
ATTEMPT_004_BACKEND_RELATIVE: Final = Path(
    "src/torch2pc_thesis/stage3b_qwake_attempt_004_runtime_backend.py"
)
ATTEMPT_004_PROFILE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/stage3b_qwake_attempt_004_cpu_measurement_stabilization.py"
)
GENERIC_RUNTIME_BACKEND_RELATIVE: Final = Path(
    "src/torch2pc_thesis/stage3b_qwake_lc4_runtime_backend.py"
)
ATTEMPT_004_HOST_SPAWNER_RELATIVE: Final = Path(
    "scripts/run_stage3b_qwake_attempt_004_host_one_shot.py"
)
ATTEMPT_004_ENTRYPOINT_RELATIVE: Final = Path(
    "scripts/run_stage3b_qwake_attempt_004_authorized_runtime.py"
)
ATTEMPT_004_LEASE_ACKNOWLEDGEMENT: Final = (
    "CLAIM_QWAKE_LC4_ATTEMPT_004_FROM_CPU_STABILIZED_EXECUTION_FREEZE"
)
ATTEMPT_004_INVOCATION_ACKNOWLEDGEMENT: Final = (
    "AUTHORIZE_QWAKE_LC4_ATTEMPT_004_ONE_SHOT_ENGINEERING_INVOCATION"
)
ATTEMPT_004_FREEZE_ID: Final = (
    "stage3b-qwake-attempt-004-execution-freeze-v1"
)
ATTEMPT_004_FREEZE_STATUS: Final = (
    "cpu_stabilized_image_and_attempt_004_runtime_frozen_execution_not_started"
)
ATTEMPT_004_AUTHORIZATION_ID: Final = (
    "stage3b-qwake-attempt-004-authorization-v1"
)
ATTEMPT_004_AUTHORIZATION_STATUS: Final = (
    "effective_unconsumed_attempt_004_runtime_authorization"
)
AUTHORIZED_CELL_COUNT: Final = 168
RESERVE_PROBE_COUNT: Final = 28
EXPECTED_TORCH2PC_COMMIT: Final = "b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4"
EXPECTED_SCIENTIFIC_AUTHORIZATION_SHA256: Final = (
    "sha256:d11b662a5c5eeada5333e69c6fddf2e50726c01b4d8c78a556a68167dbdd301e"
)
EXPECTED_SCIENTIFIC_AUTHORIZATION_FILE_SHA256: Final = (
    "sha256:a380cffcfa73cb2dcf984a3cc7de013cb50d79f075677ad5e762417486f06ebd"
)
EXPECTED_GENERIC_RUNTIME_BACKEND_SHA256: Final = (
    "sha256:d9ad10efe959e19d7f1b6d61d8eddd1228cb9753fa9191823d5d1ded68e9fd72"
)
ATTEMPT_004_HOST_COMMAND_RELATIVE: Final = Path(
    str(ATTEMPT_004_OUTPUT_ROOT) + ".host-command.json"
)

__all__ = [
    "ATTEMPT_004_AUTHORIZATION_ID",
    "ATTEMPT_004_AUTHORIZATION_RELATIVE",
    "ATTEMPT_004_AUTHORIZATION_ROOT",
    "ATTEMPT_004_AUTHORIZATION_STATUS",
    "ATTEMPT_004_BACKEND_RELATIVE",
    "ATTEMPT_004_PROFILE_RELATIVE",
    "ATTEMPT_004_HOST_SPAWNER_RELATIVE",
    "GENERIC_RUNTIME_BACKEND_RELATIVE",
    "ATTEMPT_004_CONTRACT_RELATIVE",
    "ATTEMPT_004_DURABLE_OUTCOME_RELATIVE",
    "ATTEMPT_004_ENTRYPOINT_RELATIVE",
    "ATTEMPT_004_FREEZE_ID",
    "ATTEMPT_004_FREEZE_RELATIVE",
    "ATTEMPT_004_FREEZE_ROOT",
    "ATTEMPT_004_FREEZE_STATUS",
    "ATTEMPT_004_ID",
    "ATTEMPT_004_INVOCATION_ACKNOWLEDGEMENT",
    "ATTEMPT_004_LEASE_ACKNOWLEDGEMENT",
    "ATTEMPT_004_LEASE_V1_RELATIVE",
    "ATTEMPT_004_LEASE_V2_RELATIVE",
    "ATTEMPT_004_OUTPUT_ROOT",
    "ATTEMPT_004_WRAPPER_RELATIVE",
    "AUTHORIZED_CELL_COUNT",
    "RESERVE_PROBE_COUNT",
    "EXPECTED_TORCH2PC_COMMIT",
    "EXPECTED_SCIENTIFIC_AUTHORIZATION_SHA256",
    "EXPECTED_SCIENTIFIC_AUTHORIZATION_FILE_SHA256",
    "EXPECTED_GENERIC_RUNTIME_BACKEND_SHA256",
    "ATTEMPT_004_HOST_COMMAND_RELATIVE",
    "SCIENTIFIC_RUNTIME_AUTHORIZATION_RELATIVE",
    "Attempt004AdmissionIdentity",
    "Attempt004Authorization",
    "Attempt004ContractError",
    "Attempt004ExecutionFreeze",
    "build_attempt_004_admission",
    "canonical_json",
    "sha256_object",
    "verify_attempt_004_execution_freeze",
    "verify_unconsumed_attempt_004_authorization",
]


class Attempt004ContractError(RuntimeError):
    """Raised when a future attempt-004 identity fails closed."""


@dataclass(frozen=True)
class Attempt004ExecutionFreeze:
    """Exact corrected image and source identities for attempt 004."""

    schema_version: int
    freeze_id: str
    status: str
    attempt_id: str
    source_commit: str
    source_tree: str
    wrapper_commit: str
    torch2pc_commit: str
    image_digest: str
    image_repo_digest: str
    contract_sha256: str
    wrapper_sha256: str
    backend_sha256: str
    profile_sha256: str
    generic_backend_sha256: str
    host_spawner_sha256: str
    entrypoint_sha256: str
    scientific_authorization_relative: str
    scientific_authorization_sha256: str
    scientific_authorization_file_sha256: str
    output_root: str
    lease_v1_relative: str
    lease_v2_relative: str
    durable_outcome_relative: str
    authorized_cell_count: int
    reserve_probe_count: int
    execution_count: int
    runtime_execution_started: bool
    runtime_execution_performed: bool
    engineering_evidence_present: bool
    scientific_execution_open: bool
    test_dataset_access: bool
    publication_permitted: bool
    freeze_sha256: str

    def require(self) -> None:
        expected: Mapping[str, object] = {
            "schema_version": 1,
            "freeze_id": ATTEMPT_004_FREEZE_ID,
            "status": ATTEMPT_004_FREEZE_STATUS,
            "attempt_id": ATTEMPT_004_ID,
            "scientific_authorization_relative": (
                SCIENTIFIC_RUNTIME_AUTHORIZATION_RELATIVE.as_posix()
            ),
            "output_root": ATTEMPT_004_OUTPUT_ROOT.as_posix(),
            "lease_v1_relative": ATTEMPT_004_LEASE_V1_RELATIVE.as_posix(),
            "lease_v2_relative": ATTEMPT_004_LEASE_V2_RELATIVE.as_posix(),
            "durable_outcome_relative": (
                ATTEMPT_004_DURABLE_OUTCOME_RELATIVE.as_posix()
            ),
            "authorized_cell_count": AUTHORIZED_CELL_COUNT,
            "reserve_probe_count": RESERVE_PROBE_COUNT,
            "torch2pc_commit": EXPECTED_TORCH2PC_COMMIT,
            "scientific_authorization_sha256": (
                EXPECTED_SCIENTIFIC_AUTHORIZATION_SHA256
            ),
            "scientific_authorization_file_sha256": (
                EXPECTED_SCIENTIFIC_AUTHORIZATION_FILE_SHA256
            ),
            "generic_backend_sha256": EXPECTED_GENERIC_RUNTIME_BACKEND_SHA256,
            "execution_count": 1,
            "runtime_execution_started": False,
            "runtime_execution_performed": False,
            "engineering_evidence_present": False,
            "scientific_execution_open": False,
            "test_dataset_access": False,
            "publication_permitted": False,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise Attempt004ContractError(
                    f"attempt-004 freeze {field_name} differs"
                )
        for value, field_name in (
            (self.source_commit, "source_commit"),
            (self.source_tree, "source_tree"),
            (self.wrapper_commit, "wrapper_commit"),
            (self.torch2pc_commit, "torch2pc_commit"),
        ):
            _require_commit(value, field_name)
        for value, field_name in (
            (self.image_digest, "image_digest"),
            (self.contract_sha256, "contract_sha256"),
            (self.wrapper_sha256, "wrapper_sha256"),
            (self.backend_sha256, "backend_sha256"),
            (self.profile_sha256, "profile_sha256"),
            (self.generic_backend_sha256, "generic_backend_sha256"),
            (self.host_spawner_sha256, "host_spawner_sha256"),
            (self.entrypoint_sha256, "entrypoint_sha256"),
            (
                self.scientific_authorization_sha256,
                "scientific_authorization_sha256",
            ),
            (
                self.scientific_authorization_file_sha256,
                "scientific_authorization_file_sha256",
            ),
            (self.freeze_sha256, "freeze_sha256"),
        ):
            _require_sha256(value, field_name)
        if self.image_repo_digest.count("@sha256:") != 1:
            raise Attempt004ContractError("attempt-004 image repo digest differs")
        image_hex = self.image_digest.removeprefix("sha256:")
        if not self.image_repo_digest.endswith(image_hex):
            raise Attempt004ContractError(
                "attempt-004 image and repository digests differ"
            )
        if self.freeze_sha256 != sha256_object(self._payload_without_digest()):
            raise Attempt004ContractError("attempt-004 freeze digest differs")

    def _payload_without_digest(self) -> Mapping[str, object]:
        payload = asdict(self)
        payload.pop("freeze_sha256")
        return cast(Mapping[str, object], payload)

    def canonical_json(self) -> str:
        return canonical_json(self)


@dataclass(frozen=True)
class Attempt004Authorization:
    """Distinct one-shot authorization bound to the corrected freeze."""

    schema_version: int
    authorization_id: str
    status: str
    attempt_id: str
    freeze_sha256: str
    operator_identity_kind: str
    operator_identity: str
    action_phrase: str
    execution_count: int
    authorization_effective: bool
    authorization_consumed: bool
    attempt_started: bool
    runtime_execution_started: bool
    runtime_execution_performed: bool
    retry_permitted: bool
    scientific_execution_open: bool
    test_dataset_access: bool
    publication_permitted: bool
    authorization_sha256: str

    def require(self, freeze: Attempt004ExecutionFreeze) -> None:
        freeze.require()
        expected: Mapping[str, object] = {
            "schema_version": 1,
            "authorization_id": ATTEMPT_004_AUTHORIZATION_ID,
            "status": ATTEMPT_004_AUTHORIZATION_STATUS,
            "attempt_id": ATTEMPT_004_ID,
            "freeze_sha256": freeze.freeze_sha256,
            "operator_identity_kind": "local-posix-account",
            "action_phrase": ATTEMPT_004_INVOCATION_ACKNOWLEDGEMENT,
            "execution_count": 1,
            "authorization_effective": True,
            "authorization_consumed": False,
            "attempt_started": False,
            "runtime_execution_started": False,
            "runtime_execution_performed": False,
            "retry_permitted": False,
            "scientific_execution_open": False,
            "test_dataset_access": False,
            "publication_permitted": False,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise Attempt004ContractError(
                    f"attempt-004 authorization {field_name} differs"
                )
        if not self.operator_identity:
            raise Attempt004ContractError(
                "attempt-004 authorization operator identity is empty"
            )
        _require_sha256(self.authorization_sha256, "authorization_sha256")
        if self.authorization_sha256 != sha256_object(
            self._payload_without_digest()
        ):
            raise Attempt004ContractError(
                "attempt-004 authorization digest differs"
            )

    def _payload_without_digest(self) -> Mapping[str, object]:
        payload = asdict(self)
        payload.pop("authorization_sha256")
        return cast(Mapping[str, object], payload)

    def canonical_json(self) -> str:
        return canonical_json(self)


@dataclass(frozen=True)
class Attempt004AdmissionIdentity:
    """Single immutable identity carried through build, claim, and execute."""

    attempt_id: str
    freeze_sha256: str
    authorization_sha256: str
    source_commit: str
    wrapper_commit: str
    torch2pc_commit: str
    image_digest: str
    image_repo_digest: str
    scientific_authorization_sha256: str
    output_root: str
    lease_v1_relative: str
    lease_v2_relative: str
    durable_outcome_relative: str
    execution_count: int
    runtime_execution_permitted: bool
    authorization_consumed: bool
    attempt_started: bool
    retry_permitted: bool

    def require(self) -> None:
        expected: Mapping[str, object] = {
            "attempt_id": ATTEMPT_004_ID,
            "output_root": ATTEMPT_004_OUTPUT_ROOT.as_posix(),
            "lease_v1_relative": ATTEMPT_004_LEASE_V1_RELATIVE.as_posix(),
            "lease_v2_relative": ATTEMPT_004_LEASE_V2_RELATIVE.as_posix(),
            "durable_outcome_relative": (
                ATTEMPT_004_DURABLE_OUTCOME_RELATIVE.as_posix()
            ),
            "execution_count": 1,
            "runtime_execution_permitted": True,
            "authorization_consumed": False,
            "attempt_started": False,
            "retry_permitted": False,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise Attempt004ContractError(
                    f"attempt-004 admission {field_name} differs"
                )
        for value, field_name in (
            (self.freeze_sha256, "freeze_sha256"),
            (self.authorization_sha256, "authorization_sha256"),
            (
                self.scientific_authorization_sha256,
                "scientific_authorization_sha256",
            ),
            (self.image_digest, "image_digest"),
        ):
            _require_sha256(value, field_name)
        for value, field_name in (
            (self.source_commit, "source_commit"),
            (self.wrapper_commit, "wrapper_commit"),
            (self.torch2pc_commit, "torch2pc_commit"),
        ):
            _require_commit(value, field_name)
        if self.image_repo_digest.count("@sha256:") != 1:
            raise Attempt004ContractError("attempt-004 admission image differs")


def canonical_json(value: object) -> str:
    """Return canonical UTF-8 JSON with one final newline."""

    return (
        json.dumps(
            _canonicalize(value),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    )


def sha256_object(value: object) -> str:
    """Return a prefixed SHA-256 identity for canonical JSON bytes."""

    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def build_attempt_004_admission(
    freeze: Attempt004ExecutionFreeze,
    authorization: Attempt004Authorization,
) -> Attempt004AdmissionIdentity:
    """Build the single identity used through all irreversible steps."""

    freeze.require()
    authorization.require(freeze)
    admission = Attempt004AdmissionIdentity(
        attempt_id=ATTEMPT_004_ID,
        freeze_sha256=freeze.freeze_sha256,
        authorization_sha256=authorization.authorization_sha256,
        source_commit=freeze.source_commit,
        wrapper_commit=freeze.wrapper_commit,
        torch2pc_commit=freeze.torch2pc_commit,
        image_digest=freeze.image_digest,
        image_repo_digest=freeze.image_repo_digest,
        scientific_authorization_sha256=(
            freeze.scientific_authorization_sha256
        ),
        output_root=ATTEMPT_004_OUTPUT_ROOT.as_posix(),
        lease_v1_relative=ATTEMPT_004_LEASE_V1_RELATIVE.as_posix(),
        lease_v2_relative=ATTEMPT_004_LEASE_V2_RELATIVE.as_posix(),
        durable_outcome_relative=(
            ATTEMPT_004_DURABLE_OUTCOME_RELATIVE.as_posix()
        ),
        execution_count=1,
        runtime_execution_permitted=True,
        authorization_consumed=False,
        attempt_started=False,
        retry_permitted=False,
    )
    admission.require()
    return admission


def verify_attempt_004_execution_freeze(
    project_root: Path,
    *,
    require_runtime_environment: bool = True,
) -> Attempt004ExecutionFreeze:
    """Load and verify the future corrected image freeze without effects."""

    root = project_root.expanduser().resolve()
    freeze_path = root / ATTEMPT_004_FREEZE_RELATIVE
    mapping = _read_json_object(freeze_path)
    freeze = Attempt004ExecutionFreeze(**cast(dict[str, Any], mapping))
    freeze.require()

    expected_files = {
        ATTEMPT_004_CONTRACT_RELATIVE: freeze.contract_sha256,
        ATTEMPT_004_WRAPPER_RELATIVE: freeze.wrapper_sha256,
        ATTEMPT_004_BACKEND_RELATIVE: freeze.backend_sha256,
        ATTEMPT_004_PROFILE_RELATIVE: freeze.profile_sha256,
        GENERIC_RUNTIME_BACKEND_RELATIVE: freeze.generic_backend_sha256,
        ATTEMPT_004_HOST_SPAWNER_RELATIVE: freeze.host_spawner_sha256,
        ATTEMPT_004_ENTRYPOINT_RELATIVE: freeze.entrypoint_sha256,
        SCIENTIFIC_RUNTIME_AUTHORIZATION_RELATIVE: (
            freeze.scientific_authorization_file_sha256
        ),
    }
    for relative, expected_sha256 in expected_files.items():
        if _sha256_file(root / relative) != expected_sha256:
            raise Attempt004ContractError(
                f"attempt-004 frozen source differs: {relative}"
            )

    _verify_registry(
        root / ATTEMPT_004_FREEZE_ROOT / "SHA256SUMS",
        root / ATTEMPT_004_FREEZE_ROOT,
    )
    _verify_registry(
        root / ATTEMPT_004_FREEZE_ROOT / "source-SHA256SUMS",
        root,
    )

    environment = {
        "SOURCE_GIT_COMMIT": freeze.source_commit,
        "EXPERIMENT_IMAGE_DIGEST": freeze.image_digest,
        "EXPERIMENT_IMAGE_REPO_DIGEST": freeze.image_repo_digest,
    }
    if require_runtime_environment:
        for name, expected in environment.items():
            if os.environ.get(name) != expected:
                raise Attempt004ContractError(
                    f"attempt-004 runtime environment {name} differs"
                )
    return freeze


def verify_unconsumed_attempt_004_authorization(
    project_root: Path,
    freeze: Attempt004ExecutionFreeze,
) -> Attempt004Authorization:
    """Verify a distinct authorization while preserving an unstarted state."""

    root = project_root.expanduser().resolve()
    freeze.require()
    mapping = _read_json_object(root / ATTEMPT_004_AUTHORIZATION_RELATIVE)
    authorization = Attempt004Authorization(**cast(dict[str, Any], mapping))
    authorization.require(freeze)
    _verify_registry(
        root / ATTEMPT_004_AUTHORIZATION_ROOT / "SHA256SUMS",
        root / ATTEMPT_004_AUTHORIZATION_ROOT,
    )
    _verify_registry(
        root / ATTEMPT_004_AUTHORIZATION_ROOT / "source-SHA256SUMS",
        root,
    )

    for relative in (
        ATTEMPT_004_OUTPUT_ROOT,
        ATTEMPT_004_LEASE_V1_RELATIVE,
        ATTEMPT_004_LEASE_V2_RELATIVE,
        ATTEMPT_004_DURABLE_OUTCOME_RELATIVE,
    ):
        if os.path.lexists(root / relative):
            raise Attempt004ContractError(
                f"attempt-004 effect already exists: {relative}"
            )
    staging_pattern = f".{ATTEMPT_004_OUTPUT_ROOT.name}.staging-*"
    if tuple((root / ATTEMPT_004_OUTPUT_ROOT.parent).glob(staging_pattern)):
        raise Attempt004ContractError("attempt-004 staging already exists")
    return authorization


def _read_json_object(path: Path) -> dict[str, object]:
    if not path.is_file() or path.is_symlink():
        raise Attempt004ContractError(f"regular JSON file is absent: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Attempt004ContractError(f"invalid JSON file: {path}") from exc
    if not isinstance(value, dict):
        raise Attempt004ContractError(f"JSON root is not an object: {path}")
    if path.read_bytes() != canonical_json(value).encode("utf-8"):
        raise Attempt004ContractError(f"JSON serialization differs: {path}")
    return cast(dict[str, object], value)


def _verify_registry(registry_path: Path, base: Path) -> None:
    if not registry_path.is_file() or registry_path.is_symlink():
        raise Attempt004ContractError(
            f"regular registry is absent: {registry_path}"
        )
    seen: set[str] = set()
    for raw_line in registry_path.read_text(encoding="utf-8").splitlines():
        if not raw_line:
            continue
        parts = raw_line.split("  ", 1)
        if len(parts) != 2:
            raise Attempt004ContractError("registry line shape differs")
        expected, relative = parts
        _require_hex_sha256(expected, "registry digest")
        if relative in seen:
            raise Attempt004ContractError("registry path is duplicated")
        seen.add(relative)
        candidate = (base / relative).resolve()
        try:
            candidate.relative_to(base.resolve())
        except ValueError as exc:
            raise Attempt004ContractError("registry path escapes base") from exc
        if _sha256_file(candidate) != f"sha256:{expected}":
            raise Attempt004ContractError(
                f"registry file identity differs: {relative}"
            )
    if not seen:
        raise Attempt004ContractError("registry is empty")


def _sha256_file(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise Attempt004ContractError(f"regular source file is absent: {path}")
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _require_commit(value: str, field_name: str) -> None:
    invalid = any(character not in "0123456789abcdef" for character in value)
    if len(value) != 40 or invalid:
        raise Attempt004ContractError(f"{field_name} is not a commit")


def _require_sha256(value: str, field_name: str) -> None:
    if not value.startswith("sha256:") or len(value) != 71:
        raise Attempt004ContractError(f"{field_name} is not SHA-256")
    _require_hex_sha256(value.removeprefix("sha256:"), field_name)


def _require_hex_sha256(value: str, field_name: str) -> None:
    invalid = any(character not in "0123456789abcdef" for character in value)
    if len(value) != 64 or invalid:
        raise Attempt004ContractError(f"{field_name} is not hexadecimal SHA-256")


def _canonicalize(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _canonicalize(asdict(cast(Any, value)))
    if isinstance(value, Mapping):
        return {
            str(key): _canonicalize(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, tuple | list):
        return [_canonicalize(item) for item in cast(Sequence[object], value)]
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, str | int | float | bool) or value is None:
        return value
    raise Attempt004ContractError(
        f"unsupported canonical JSON value: {type(value).__name__}"
    )
