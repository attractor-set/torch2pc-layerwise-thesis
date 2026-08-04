"""Attempt-002 identities and fail-closed admission verification.

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

ATTEMPT_002_ID: Final = "stage3b-qwake-lc4-runtime-validation-v1-attempt-002"
ATTEMPT_002_OUTPUT_ROOT: Final = Path(
    "results/stage-3/qwake-lc4-runtime-validation-v1-attempt-002"
)
ATTEMPT_002_LEASE_V1_RELATIVE: Final = Path(
    str(ATTEMPT_002_OUTPUT_ROOT) + ".execution-lease.json"
)
ATTEMPT_002_LEASE_V2_RELATIVE: Final = Path(
    str(ATTEMPT_002_OUTPUT_ROOT) + ".execution-lease-v2.json"
)
ATTEMPT_002_DURABLE_OUTCOME_RELATIVE: Final = Path(
    str(ATTEMPT_002_OUTPUT_ROOT) + ".host-outcome.json"
)
ATTEMPT_002_FREEZE_ROOT: Final = Path(
    "experiments/frozen/stage3b-qwake-lc4-e-attempt-002-execution-freeze-v1"
)
ATTEMPT_002_FREEZE_RELATIVE: Final = ATTEMPT_002_FREEZE_ROOT / "execution.json"
ATTEMPT_002_AUTHORIZATION_ROOT: Final = Path(
    "experiments/frozen/stage3b-qwake-lc4-e-attempt-002-authorization-v1"
)
ATTEMPT_002_AUTHORIZATION_RELATIVE: Final = (
    ATTEMPT_002_AUTHORIZATION_ROOT / "authorization.json"
)
SCIENTIFIC_RUNTIME_AUTHORIZATION_RELATIVE: Final = Path(
    "experiments/frozen/stage3b-qwake-lc4-f-runtime-freeze-v1/authorization.json"
)
ATTEMPT_002_CONTRACT_RELATIVE: Final = Path(
    "src/torch2pc_thesis/stage3b_qwake_lc4_attempt_002_contract.py"
)
ATTEMPT_002_WRAPPER_RELATIVE: Final = Path(
    "src/torch2pc_thesis/stage3b_qwake_lc4_attempt_002_execution_wrapper.py"
)
ATTEMPT_002_BACKEND_RELATIVE: Final = Path(
    "src/torch2pc_thesis/stage3b_qwake_lc4_attempt_002_runtime_backend.py"
)
ATTEMPT_002_ENTRYPOINT_RELATIVE: Final = Path(
    "scripts/run_stage3b_qwake_lc4_attempt_002_authorized_runtime.py"
)
ATTEMPT_002_LEASE_ACKNOWLEDGEMENT: Final = (
    "CLAIM_QWAKE_LC4_ATTEMPT_002_FROM_CORRECTED_EXECUTION_FREEZE"
)
ATTEMPT_002_INVOCATION_ACKNOWLEDGEMENT: Final = (
    "AUTHORIZE_QWAKE_LC4_ATTEMPT_002_ONE_SHOT_ENGINEERING_INVOCATION"
)
ATTEMPT_002_FREEZE_ID: Final = (
    "stage3b-qwake-lc4-e-attempt-002-execution-freeze-v1"
)
ATTEMPT_002_FREEZE_STATUS: Final = (
    "corrected_image_and_attempt_002_runtime_frozen_execution_not_started"
)
ATTEMPT_002_AUTHORIZATION_ID: Final = (
    "stage3b-qwake-lc4-e-attempt-002-authorization-v1"
)
ATTEMPT_002_AUTHORIZATION_STATUS: Final = (
    "effective_unconsumed_attempt_002_runtime_authorization"
)
AUTHORIZED_CELL_COUNT: Final = 168
RESERVE_PROBE_COUNT: Final = 28

__all__ = [
    "ATTEMPT_002_AUTHORIZATION_ID",
    "ATTEMPT_002_AUTHORIZATION_RELATIVE",
    "ATTEMPT_002_AUTHORIZATION_ROOT",
    "ATTEMPT_002_AUTHORIZATION_STATUS",
    "ATTEMPT_002_BACKEND_RELATIVE",
    "ATTEMPT_002_CONTRACT_RELATIVE",
    "ATTEMPT_002_DURABLE_OUTCOME_RELATIVE",
    "ATTEMPT_002_ENTRYPOINT_RELATIVE",
    "ATTEMPT_002_FREEZE_ID",
    "ATTEMPT_002_FREEZE_RELATIVE",
    "ATTEMPT_002_FREEZE_ROOT",
    "ATTEMPT_002_FREEZE_STATUS",
    "ATTEMPT_002_ID",
    "ATTEMPT_002_INVOCATION_ACKNOWLEDGEMENT",
    "ATTEMPT_002_LEASE_ACKNOWLEDGEMENT",
    "ATTEMPT_002_LEASE_V1_RELATIVE",
    "ATTEMPT_002_LEASE_V2_RELATIVE",
    "ATTEMPT_002_OUTPUT_ROOT",
    "ATTEMPT_002_WRAPPER_RELATIVE",
    "AUTHORIZED_CELL_COUNT",
    "RESERVE_PROBE_COUNT",
    "SCIENTIFIC_RUNTIME_AUTHORIZATION_RELATIVE",
    "Attempt002AdmissionIdentity",
    "Attempt002Authorization",
    "Attempt002ContractError",
    "Attempt002ExecutionFreeze",
    "build_attempt_002_admission",
    "canonical_json",
    "sha256_object",
    "verify_attempt_002_execution_freeze",
    "verify_unconsumed_attempt_002_authorization",
]


class Attempt002ContractError(RuntimeError):
    """Raised when a future attempt-002 identity fails closed."""


@dataclass(frozen=True)
class Attempt002ExecutionFreeze:
    """Exact corrected image and source identities for attempt 002."""

    schema_version: int
    freeze_id: str
    status: str
    attempt_id: str
    source_commit: str
    wrapper_commit: str
    torch2pc_commit: str
    image_digest: str
    image_repo_digest: str
    contract_sha256: str
    wrapper_sha256: str
    backend_sha256: str
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
            "freeze_id": ATTEMPT_002_FREEZE_ID,
            "status": ATTEMPT_002_FREEZE_STATUS,
            "attempt_id": ATTEMPT_002_ID,
            "scientific_authorization_relative": (
                SCIENTIFIC_RUNTIME_AUTHORIZATION_RELATIVE.as_posix()
            ),
            "output_root": ATTEMPT_002_OUTPUT_ROOT.as_posix(),
            "lease_v1_relative": ATTEMPT_002_LEASE_V1_RELATIVE.as_posix(),
            "lease_v2_relative": ATTEMPT_002_LEASE_V2_RELATIVE.as_posix(),
            "durable_outcome_relative": (
                ATTEMPT_002_DURABLE_OUTCOME_RELATIVE.as_posix()
            ),
            "authorized_cell_count": AUTHORIZED_CELL_COUNT,
            "reserve_probe_count": RESERVE_PROBE_COUNT,
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
                raise Attempt002ContractError(
                    f"attempt-002 freeze {field_name} differs"
                )
        for value, field_name in (
            (self.source_commit, "source_commit"),
            (self.wrapper_commit, "wrapper_commit"),
            (self.torch2pc_commit, "torch2pc_commit"),
        ):
            _require_commit(value, field_name)
        for value, field_name in (
            (self.image_digest, "image_digest"),
            (self.contract_sha256, "contract_sha256"),
            (self.wrapper_sha256, "wrapper_sha256"),
            (self.backend_sha256, "backend_sha256"),
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
            raise Attempt002ContractError("attempt-002 image repo digest differs")
        image_hex = self.image_digest.removeprefix("sha256:")
        if not self.image_repo_digest.endswith(image_hex):
            raise Attempt002ContractError(
                "attempt-002 image and repository digests differ"
            )
        if self.freeze_sha256 != sha256_object(self._payload_without_digest()):
            raise Attempt002ContractError("attempt-002 freeze digest differs")

    def _payload_without_digest(self) -> Mapping[str, object]:
        payload = asdict(self)
        payload.pop("freeze_sha256")
        return cast(Mapping[str, object], payload)

    def canonical_json(self) -> str:
        return canonical_json(self)


@dataclass(frozen=True)
class Attempt002Authorization:
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

    def require(self, freeze: Attempt002ExecutionFreeze) -> None:
        freeze.require()
        expected: Mapping[str, object] = {
            "schema_version": 1,
            "authorization_id": ATTEMPT_002_AUTHORIZATION_ID,
            "status": ATTEMPT_002_AUTHORIZATION_STATUS,
            "attempt_id": ATTEMPT_002_ID,
            "freeze_sha256": freeze.freeze_sha256,
            "operator_identity_kind": "local-posix-account",
            "action_phrase": ATTEMPT_002_INVOCATION_ACKNOWLEDGEMENT,
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
                raise Attempt002ContractError(
                    f"attempt-002 authorization {field_name} differs"
                )
        if not self.operator_identity:
            raise Attempt002ContractError(
                "attempt-002 authorization operator identity is empty"
            )
        _require_sha256(self.authorization_sha256, "authorization_sha256")
        if self.authorization_sha256 != sha256_object(
            self._payload_without_digest()
        ):
            raise Attempt002ContractError(
                "attempt-002 authorization digest differs"
            )

    def _payload_without_digest(self) -> Mapping[str, object]:
        payload = asdict(self)
        payload.pop("authorization_sha256")
        return cast(Mapping[str, object], payload)

    def canonical_json(self) -> str:
        return canonical_json(self)


@dataclass(frozen=True)
class Attempt002AdmissionIdentity:
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
            "attempt_id": ATTEMPT_002_ID,
            "output_root": ATTEMPT_002_OUTPUT_ROOT.as_posix(),
            "lease_v1_relative": ATTEMPT_002_LEASE_V1_RELATIVE.as_posix(),
            "lease_v2_relative": ATTEMPT_002_LEASE_V2_RELATIVE.as_posix(),
            "durable_outcome_relative": (
                ATTEMPT_002_DURABLE_OUTCOME_RELATIVE.as_posix()
            ),
            "execution_count": 1,
            "runtime_execution_permitted": True,
            "authorization_consumed": False,
            "attempt_started": False,
            "retry_permitted": False,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise Attempt002ContractError(
                    f"attempt-002 admission {field_name} differs"
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
            raise Attempt002ContractError("attempt-002 admission image differs")


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


def build_attempt_002_admission(
    freeze: Attempt002ExecutionFreeze,
    authorization: Attempt002Authorization,
) -> Attempt002AdmissionIdentity:
    """Build the single identity used through all irreversible steps."""

    freeze.require()
    authorization.require(freeze)
    admission = Attempt002AdmissionIdentity(
        attempt_id=ATTEMPT_002_ID,
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
        output_root=ATTEMPT_002_OUTPUT_ROOT.as_posix(),
        lease_v1_relative=ATTEMPT_002_LEASE_V1_RELATIVE.as_posix(),
        lease_v2_relative=ATTEMPT_002_LEASE_V2_RELATIVE.as_posix(),
        durable_outcome_relative=(
            ATTEMPT_002_DURABLE_OUTCOME_RELATIVE.as_posix()
        ),
        execution_count=1,
        runtime_execution_permitted=True,
        authorization_consumed=False,
        attempt_started=False,
        retry_permitted=False,
    )
    admission.require()
    return admission


def verify_attempt_002_execution_freeze(
    project_root: Path,
) -> Attempt002ExecutionFreeze:
    """Load and verify the future corrected image freeze without effects."""

    root = project_root.expanduser().resolve()
    freeze_path = root / ATTEMPT_002_FREEZE_RELATIVE
    mapping = _read_json_object(freeze_path)
    freeze = Attempt002ExecutionFreeze(**cast(dict[str, Any], mapping))
    freeze.require()

    expected_files = {
        ATTEMPT_002_CONTRACT_RELATIVE: freeze.contract_sha256,
        ATTEMPT_002_WRAPPER_RELATIVE: freeze.wrapper_sha256,
        ATTEMPT_002_BACKEND_RELATIVE: freeze.backend_sha256,
        ATTEMPT_002_ENTRYPOINT_RELATIVE: freeze.entrypoint_sha256,
        SCIENTIFIC_RUNTIME_AUTHORIZATION_RELATIVE: (
            freeze.scientific_authorization_file_sha256
        ),
    }
    for relative, expected_sha256 in expected_files.items():
        if _sha256_file(root / relative) != expected_sha256:
            raise Attempt002ContractError(
                f"attempt-002 frozen source differs: {relative}"
            )

    _verify_registry(
        root / ATTEMPT_002_FREEZE_ROOT / "SHA256SUMS",
        root / ATTEMPT_002_FREEZE_ROOT,
    )
    _verify_registry(
        root / ATTEMPT_002_FREEZE_ROOT / "source-SHA256SUMS",
        root,
    )

    environment = {
        "SOURCE_GIT_COMMIT": freeze.source_commit,
        "EXPERIMENT_IMAGE_DIGEST": freeze.image_digest,
        "EXPERIMENT_IMAGE_REPO_DIGEST": freeze.image_repo_digest,
    }
    for name, expected in environment.items():
        if os.environ.get(name) != expected:
            raise Attempt002ContractError(
                f"attempt-002 runtime environment {name} differs"
            )
    return freeze


def verify_unconsumed_attempt_002_authorization(
    project_root: Path,
    freeze: Attempt002ExecutionFreeze,
) -> Attempt002Authorization:
    """Verify a distinct authorization while preserving an unstarted state."""

    root = project_root.expanduser().resolve()
    freeze.require()
    mapping = _read_json_object(root / ATTEMPT_002_AUTHORIZATION_RELATIVE)
    authorization = Attempt002Authorization(**cast(dict[str, Any], mapping))
    authorization.require(freeze)
    _verify_registry(
        root / ATTEMPT_002_AUTHORIZATION_ROOT / "SHA256SUMS",
        root / ATTEMPT_002_AUTHORIZATION_ROOT,
    )
    _verify_registry(
        root / ATTEMPT_002_AUTHORIZATION_ROOT / "source-SHA256SUMS",
        root,
    )

    for relative in (
        ATTEMPT_002_OUTPUT_ROOT,
        ATTEMPT_002_LEASE_V1_RELATIVE,
        ATTEMPT_002_LEASE_V2_RELATIVE,
        ATTEMPT_002_DURABLE_OUTCOME_RELATIVE,
    ):
        if os.path.lexists(root / relative):
            raise Attempt002ContractError(
                f"attempt-002 effect already exists: {relative}"
            )
    staging_pattern = f".{ATTEMPT_002_OUTPUT_ROOT.name}.staging-*"
    if tuple((root / ATTEMPT_002_OUTPUT_ROOT.parent).glob(staging_pattern)):
        raise Attempt002ContractError("attempt-002 staging already exists")
    return authorization


def _read_json_object(path: Path) -> dict[str, object]:
    if not path.is_file() or path.is_symlink():
        raise Attempt002ContractError(f"regular JSON file is absent: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Attempt002ContractError(f"invalid JSON file: {path}") from exc
    if not isinstance(value, dict):
        raise Attempt002ContractError(f"JSON root is not an object: {path}")
    if path.read_bytes() != canonical_json(value).encode("utf-8"):
        raise Attempt002ContractError(f"JSON serialization differs: {path}")
    return cast(dict[str, object], value)


def _verify_registry(registry_path: Path, base: Path) -> None:
    if not registry_path.is_file() or registry_path.is_symlink():
        raise Attempt002ContractError(
            f"regular registry is absent: {registry_path}"
        )
    seen: set[str] = set()
    for raw_line in registry_path.read_text(encoding="utf-8").splitlines():
        if not raw_line:
            continue
        parts = raw_line.split("  ", 1)
        if len(parts) != 2:
            raise Attempt002ContractError("registry line shape differs")
        expected, relative = parts
        _require_hex_sha256(expected, "registry digest")
        if relative in seen:
            raise Attempt002ContractError("registry path is duplicated")
        seen.add(relative)
        candidate = (base / relative).resolve()
        try:
            candidate.relative_to(base.resolve())
        except ValueError as exc:
            raise Attempt002ContractError("registry path escapes base") from exc
        if _sha256_file(candidate) != f"sha256:{expected}":
            raise Attempt002ContractError(
                f"registry file identity differs: {relative}"
            )
    if not seen:
        raise Attempt002ContractError("registry is empty")


def _sha256_file(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise Attempt002ContractError(f"regular source file is absent: {path}")
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _require_commit(value: str, field_name: str) -> None:
    invalid = any(character not in "0123456789abcdef" for character in value)
    if len(value) != 40 or invalid:
        raise Attempt002ContractError(f"{field_name} is not a commit")


def _require_sha256(value: str, field_name: str) -> None:
    if not value.startswith("sha256:") or len(value) != 71:
        raise Attempt002ContractError(f"{field_name} is not SHA-256")
    _require_hex_sha256(value.removeprefix("sha256:"), field_name)


def _require_hex_sha256(value: str, field_name: str) -> None:
    invalid = any(character not in "0123456789abcdef" for character in value)
    if len(value) != 64 or invalid:
        raise Attempt002ContractError(f"{field_name} is not hexadecimal SHA-256")


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
    raise Attempt002ContractError(
        f"unsupported canonical JSON value: {type(value).__name__}"
    )
