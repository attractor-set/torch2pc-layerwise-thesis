"""Fail-closed admission schema for the single QW-LC4 engineering attempt.

This module verifies the already frozen QW-LC4-F package and a future
control-plane admission record. It does not import model code, allocate
tensors, create an execution lease, write results, or start execution.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Final, cast

EXECUTION_ADMISSION_ID: Final = (
    "stage3b-qwake-lc4-e-execution-admission-v1"
)
EXECUTION_ADMISSION_STATUS: Final = (
    "admitted_single_engineering_attempt_execution_not_started"
)
EXECUTION_OPERATOR_ACKNOWLEDGEMENT: Final = (
    "ADMIT_QWAKE_LC4_SINGLE_ENGINEERING_EXECUTION_FROM_FROZEN_AUTHORIZATION"
)
FROZEN_RUNTIME_ID: Final = "stage3b-qwake-lc4-f-runtime-freeze-v1"
FROZEN_RUNTIME_SOURCE_COMMIT: Final = (
    "51fc7537fdcb395145fc4c5a38b8918b018fe892"
)
FROZEN_RUNTIME_MERGE_COMMIT: Final = (
    "453bb4eb6a20ae52a0d10384a1c54e45cf999143"
)
FROZEN_TORCH2PC_COMMIT: Final = (
    "b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4"
)
FROZEN_IMAGE_DIGEST: Final = (
    "sha256:"
    "a31cf96e20ab45ce29fe18b68eb805bd048a02f1f8107cf680d1c174ea363929"
)
FROZEN_PREFLIGHT_SHA256: Final = (
    "sha256:"
    "3a8d7817338f3b93396270ea8e1b1b2fbda768dbd5461a18f97520948a53a9e6"
)
FROZEN_AUTHORIZATION_SHA256: Final = (
    "sha256:"
    "d11b662a5c5eeada5333e69c6fddf2e50726c01b4d8c78a556a68167dbdd301e"
)
FROZEN_MANIFEST_FILE_SHA256: Final = (
    "sha256:"
    "4840d39d7c19133aeb3f20c572c17677f84ad2f82697dc4ad75dcccb99bb52c1"
)
FROZEN_AUTHORIZATION_FILE_SHA256: Final = (
    "sha256:"
    "a380cffcfa73cb2dcf984a3cc7de013cb50d79f075677ad5e762417486f06ebd"
)
AUTHORIZED_OUTPUT_ROOT: Final = (
    "results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001"
)
FROZEN_ROOT_RELATIVE: Final = Path(
    "experiments/frozen/stage3b-qwake-lc4-f-runtime-freeze-v1"
)
EXECUTION_LEASE_RELATIVE: Final = Path(
    AUTHORIZED_OUTPUT_ROOT + ".execution-lease.json"
)

_EXPECTED_FILES: Final = frozenset(
    {
        "SHA256SUMS",
        "authorization-verification-receipt.json",
        "authorization.json",
        "identity.env",
        "image-build.log",
        "manifest.json",
        "preflight.json",
        "source-SHA256SUMS",
        "static-validation-receipt.json",
        "static-validation.log",
    }
)
_COMMIT_PATTERN: Final = re.compile(r"^[0-9a-f]{40}$")
_SHA256_PATTERN: Final = re.compile(r"^sha256:[0-9a-f]{64}$")

__all__ = [
    "AUTHORIZED_OUTPUT_ROOT",
    "EXECUTION_ADMISSION_ID",
    "EXECUTION_ADMISSION_STATUS",
    "EXECUTION_LEASE_RELATIVE",
    "EXECUTION_OPERATOR_ACKNOWLEDGEMENT",
    "FROZEN_AUTHORIZATION_FILE_SHA256",
    "FROZEN_AUTHORIZATION_SHA256",
    "FROZEN_IMAGE_DIGEST",
    "FROZEN_MANIFEST_FILE_SHA256",
    "FROZEN_PREFLIGHT_SHA256",
    "FROZEN_RUNTIME_ID",
    "FROZEN_RUNTIME_MERGE_COMMIT",
    "FROZEN_RUNTIME_SOURCE_COMMIT",
    "FROZEN_TORCH2PC_COMMIT",
    "ExecutionAdmission",
    "FrozenRuntimeIdentity",
    "QWakeLC4ExecutionAdmissionError",
    "build_execution_admission",
    "canonical_json",
    "load_execution_admission",
    "sha256_object",
    "validate_execution_admission",
    "verify_frozen_runtime_package",
]


class QWakeLC4ExecutionAdmissionError(RuntimeError):
    """Raised when the QW-LC4-E admission boundary fails closed."""


@dataclass(frozen=True)
class FrozenRuntimeIdentity:
    """Exact immutable identities inherited from QW-LC4-F."""

    freeze_id: str
    freeze_merge_commit: str
    runtime_source_commit: str
    torch2pc_commit: str
    image_digest: str
    preflight_sha256: str
    authorization_sha256: str
    authorization_file_sha256: str
    manifest_file_sha256: str
    output_root: str
    execution_count: int
    authorized_cell_count: int
    runtime_execution_permitted: bool
    runtime_execution_performed: bool
    engineering_evidence_present: bool
    scientific_execution_open: bool
    test_dataset_access: bool
    publication_permitted: bool

    def require(self) -> None:
        if self.freeze_id != FROZEN_RUNTIME_ID:
            raise QWakeLC4ExecutionAdmissionError(
                "unexpected frozen runtime id"
            )
        if self.freeze_merge_commit != FROZEN_RUNTIME_MERGE_COMMIT:
            raise QWakeLC4ExecutionAdmissionError(
                "frozen runtime merge commit differs"
            )
        if self.runtime_source_commit != FROZEN_RUNTIME_SOURCE_COMMIT:
            raise QWakeLC4ExecutionAdmissionError(
                "frozen runtime source commit differs"
            )
        if self.torch2pc_commit != FROZEN_TORCH2PC_COMMIT:
            raise QWakeLC4ExecutionAdmissionError(
                "frozen Torch2PC commit differs"
            )
        if self.image_digest != FROZEN_IMAGE_DIGEST:
            raise QWakeLC4ExecutionAdmissionError(
                "frozen image digest differs"
            )
        if self.preflight_sha256 != FROZEN_PREFLIGHT_SHA256:
            raise QWakeLC4ExecutionAdmissionError(
                "frozen preflight digest differs"
            )
        if self.authorization_sha256 != FROZEN_AUTHORIZATION_SHA256:
            raise QWakeLC4ExecutionAdmissionError(
                "frozen authorization semantic digest differs"
            )
        if self.manifest_file_sha256 != FROZEN_MANIFEST_FILE_SHA256:
            raise QWakeLC4ExecutionAdmissionError(
                "frozen manifest file digest differs"
            )
        if self.output_root != AUTHORIZED_OUTPUT_ROOT:
            raise QWakeLC4ExecutionAdmissionError(
                "authorized output root differs"
            )
        if self.execution_count != 1:
            raise QWakeLC4ExecutionAdmissionError(
                "authorization is not single-attempt"
            )
        if self.authorized_cell_count != 168:
            raise QWakeLC4ExecutionAdmissionError(
                "authorized cell count differs"
            )
        if not self.runtime_execution_permitted:
            raise QWakeLC4ExecutionAdmissionError(
                "frozen authorization does not permit engineering execution"
            )
        if any(
            (
                self.runtime_execution_performed,
                self.engineering_evidence_present,
                self.scientific_execution_open,
                self.test_dataset_access,
                self.publication_permitted,
            )
        ):
            raise QWakeLC4ExecutionAdmissionError(
                "frozen package records a forbidden completed capability"
            )
        if self.authorization_file_sha256 != (
            FROZEN_AUTHORIZATION_FILE_SHA256
        ):
            raise QWakeLC4ExecutionAdmissionError(
                "frozen authorization file digest differs"
            )


@dataclass(frozen=True)
class ExecutionAdmission:
    """Prospective one-attempt control-plane admission."""

    schema_version: int
    admission_id: str
    status: str
    admitted_at_utc: str
    control_plane_commit: str
    operator_acknowledgement: str
    frozen_runtime: FrozenRuntimeIdentity
    output_root_absent_at_admission: bool
    execution_lease_absent_at_admission: bool
    authorization_consumed: bool
    execution_count: int
    runtime_execution_permitted: bool
    runtime_execution_started: bool
    runtime_execution_performed: bool
    engineering_evidence_present: bool
    scientific_execution_open: bool
    test_dataset_access: bool
    publication_permitted: bool
    admission_sha256: str

    def require(self) -> None:
        if self.schema_version != 1:
            raise QWakeLC4ExecutionAdmissionError(
                "unexpected execution admission schema"
            )
        if self.admission_id != EXECUTION_ADMISSION_ID:
            raise QWakeLC4ExecutionAdmissionError(
                "unexpected execution admission id"
            )
        if self.status != EXECUTION_ADMISSION_STATUS:
            raise QWakeLC4ExecutionAdmissionError(
                "unexpected execution admission status"
            )
        _require_utc(self.admitted_at_utc)
        _require_commit(self.control_plane_commit, "control_plane_commit")
        if (
            self.operator_acknowledgement
            != EXECUTION_OPERATOR_ACKNOWLEDGEMENT
        ):
            raise QWakeLC4ExecutionAdmissionError(
                "execution operator acknowledgement differs"
            )
        self.frozen_runtime.require()
        if not self.output_root_absent_at_admission:
            raise QWakeLC4ExecutionAdmissionError(
                "output root existed at admission"
            )
        if not self.execution_lease_absent_at_admission:
            raise QWakeLC4ExecutionAdmissionError(
                "execution lease existed at admission"
            )
        if self.authorization_consumed:
            raise QWakeLC4ExecutionAdmissionError(
                "authorization was already consumed"
            )
        if self.execution_count != 1 or not self.runtime_execution_permitted:
            raise QWakeLC4ExecutionAdmissionError(
                "admission does not permit exactly one engineering attempt"
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
            raise QWakeLC4ExecutionAdmissionError(
                "execution admission opened a forbidden completed capability"
            )
        _require_sha256(self.admission_sha256, "admission_sha256")
        if self.admission_sha256 != sha256_object(
            self._payload_without_digest()
        ):
            raise QWakeLC4ExecutionAdmissionError(
                "execution admission digest differs"
            )

    def _payload_without_digest(self) -> Mapping[str, object]:
        payload = asdict(self)
        payload.pop("admission_sha256")
        return cast(Mapping[str, object], payload)

    def canonical_json(self) -> str:
        return canonical_json(self)


def verify_frozen_runtime_package(
    project_root: Path,
) -> FrozenRuntimeIdentity:
    """Verify exact QW-LC4-F files without re-running the frozen preflight."""

    root = project_root.expanduser().resolve()
    frozen_root = root / FROZEN_ROOT_RELATIVE
    if not frozen_root.is_dir():
        raise QWakeLC4ExecutionAdmissionError(
            "frozen runtime package is absent"
        )
    entries = tuple(frozen_root.iterdir())
    files = {item.name for item in entries if item.is_file()}
    if files != set(_EXPECTED_FILES):
        raise QWakeLC4ExecutionAdmissionError(
            "frozen runtime package scope differs"
        )
    if any(item.is_dir() or item.is_symlink() for item in entries):
        raise QWakeLC4ExecutionAdmissionError(
            "frozen runtime package contains a non-regular entry"
        )

    _verify_registry(frozen_root / "SHA256SUMS", frozen_root)
    _verify_registry(frozen_root / "source-SHA256SUMS", root)

    manifest_path = frozen_root / "manifest.json"
    authorization_path = frozen_root / "authorization.json"
    preflight_path = frozen_root / "preflight.json"
    receipt_path = frozen_root / "authorization-verification-receipt.json"

    manifest = _read_json_object(manifest_path)
    authorization = _read_json_object(authorization_path)
    preflight = _read_json_object(preflight_path)
    receipt = _read_json_object(receipt_path)

    identity = FrozenRuntimeIdentity(
        freeze_id=str(manifest["freeze_id"]),
        freeze_merge_commit=FROZEN_RUNTIME_MERGE_COMMIT,
        runtime_source_commit=str(manifest["source_commit"]),
        torch2pc_commit=str(manifest["torch2pc_commit"]),
        image_digest=str(manifest["image_digest"]),
        preflight_sha256=str(manifest["preflight_sha256"]),
        authorization_sha256=str(manifest["authorization_sha256"]),
        authorization_file_sha256=_sha256_file(authorization_path),
        manifest_file_sha256=_sha256_file(manifest_path),
        output_root=str(manifest["authorized_output_root"]),
        execution_count=_as_int(manifest["execution_count"], "execution_count"),
        authorized_cell_count=_as_int(
            manifest["authorized_cell_count"],
            "authorized_cell_count",
        ),
        runtime_execution_permitted=bool(
            manifest["runtime_execution_permitted"]
        ),
        runtime_execution_performed=bool(
            manifest["runtime_execution_performed"]
        ),
        engineering_evidence_present=bool(
            manifest["engineering_evidence_present"]
        ),
        scientific_execution_open=bool(
            manifest["scientific_execution_open"]
        ),
        test_dataset_access=bool(manifest["test_dataset_access"]),
        publication_permitted=bool(manifest["publication_permitted"]),
    )
    identity.require()

    if authorization.get("authorization_id") != (
        "stage3b-qwake-lc4-runtime-authorization-v1"
    ):
        raise QWakeLC4ExecutionAdmissionError(
            "authorization id differs"
        )
    if authorization.get("authorization_sha256") != (
        FROZEN_AUTHORIZATION_SHA256
    ):
        raise QWakeLC4ExecutionAdmissionError(
            "authorization semantic digest differs"
        )
    if authorization.get("output_root") != AUTHORIZED_OUTPUT_ROOT:
        raise QWakeLC4ExecutionAdmissionError(
            "authorization output root differs"
        )
    if authorization.get("execution_count") != 1:
        raise QWakeLC4ExecutionAdmissionError(
            "authorization execution count differs"
        )
    if authorization.get("runtime_execution_performed") is not False:
        raise QWakeLC4ExecutionAdmissionError(
            "authorization records execution"
        )

    if preflight.get("preflight_sha256") != FROZEN_PREFLIGHT_SHA256:
        raise QWakeLC4ExecutionAdmissionError(
            "preflight semantic digest differs"
        )
    if preflight.get("runtime_execution_performed") is not False:
        raise QWakeLC4ExecutionAdmissionError(
            "preflight records execution"
        )

    if receipt.get("authorization_sha256") != (
        FROZEN_AUTHORIZATION_SHA256
    ):
        raise QWakeLC4ExecutionAdmissionError(
            "authorization receipt digest differs"
        )
    if receipt.get("runtime_execution_performed") is not False:
        raise QWakeLC4ExecutionAdmissionError(
            "authorization receipt records execution"
        )
    return identity


def build_execution_admission(
    frozen_runtime: FrozenRuntimeIdentity,
    *,
    admitted_at_utc: str,
    control_plane_commit: str,
    operator_acknowledgement: str,
    output_root_absent_at_admission: bool,
    execution_lease_absent_at_admission: bool,
) -> ExecutionAdmission:
    """Build a prospective admission without starting execution."""

    if operator_acknowledgement != EXECUTION_OPERATOR_ACKNOWLEDGEMENT:
        raise QWakeLC4ExecutionAdmissionError(
            "operator acknowledgement does not admit QW-LC4-E"
        )
    frozen_runtime.require()
    payload: dict[str, object] = {
        "schema_version": 1,
        "admission_id": EXECUTION_ADMISSION_ID,
        "status": EXECUTION_ADMISSION_STATUS,
        "admitted_at_utc": admitted_at_utc,
        "control_plane_commit": control_plane_commit,
        "operator_acknowledgement": operator_acknowledgement,
        "frozen_runtime": frozen_runtime,
        "output_root_absent_at_admission": (
            output_root_absent_at_admission
        ),
        "execution_lease_absent_at_admission": (
            execution_lease_absent_at_admission
        ),
        "authorization_consumed": False,
        "execution_count": 1,
        "runtime_execution_permitted": True,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "engineering_evidence_present": False,
        "scientific_execution_open": False,
        "test_dataset_access": False,
        "publication_permitted": False,
    }
    admission = ExecutionAdmission(
        schema_version=1,
        admission_id=EXECUTION_ADMISSION_ID,
        status=EXECUTION_ADMISSION_STATUS,
        admitted_at_utc=admitted_at_utc,
        control_plane_commit=control_plane_commit,
        operator_acknowledgement=operator_acknowledgement,
        frozen_runtime=frozen_runtime,
        output_root_absent_at_admission=(
            output_root_absent_at_admission
        ),
        execution_lease_absent_at_admission=(
            execution_lease_absent_at_admission
        ),
        authorization_consumed=False,
        execution_count=1,
        runtime_execution_permitted=True,
        runtime_execution_started=False,
        runtime_execution_performed=False,
        engineering_evidence_present=False,
        scientific_execution_open=False,
        test_dataset_access=False,
        publication_permitted=False,
        admission_sha256=sha256_object(payload),
    )
    admission.require()
    return admission


def validate_execution_admission(
    admission: ExecutionAdmission,
    frozen_runtime: FrozenRuntimeIdentity,
    project_root: Path,
    *,
    expected_control_plane_commit: str,
) -> None:
    """Validate an admission while preserving an unstarted execution state."""

    admission.require()
    frozen_runtime.require()
    if admission.frozen_runtime != frozen_runtime:
        raise QWakeLC4ExecutionAdmissionError(
            "admission frozen runtime identity differs"
        )
    if admission.control_plane_commit != expected_control_plane_commit:
        raise QWakeLC4ExecutionAdmissionError(
            "admission control-plane commit differs"
        )
    root = project_root.expanduser().resolve()
    if (root / AUTHORIZED_OUTPUT_ROOT).exists():
        raise QWakeLC4ExecutionAdmissionError(
            "authorized output root already exists"
        )
    if (root / EXECUTION_LEASE_RELATIVE).exists():
        raise QWakeLC4ExecutionAdmissionError(
            "execution lease already exists"
        )


def load_execution_admission(path: Path) -> ExecutionAdmission:
    """Load and strictly validate a canonical admission JSON file."""

    payload = _read_json_object(path)
    frozen = _as_mapping(payload["frozen_runtime"], "frozen_runtime")
    admission = ExecutionAdmission(
        schema_version=_as_int(payload["schema_version"], "schema_version"),
        admission_id=str(payload["admission_id"]),
        status=str(payload["status"]),
        admitted_at_utc=str(payload["admitted_at_utc"]),
        control_plane_commit=str(payload["control_plane_commit"]),
        operator_acknowledgement=str(
            payload["operator_acknowledgement"]
        ),
        frozen_runtime=FrozenRuntimeIdentity(
            freeze_id=str(frozen["freeze_id"]),
            freeze_merge_commit=str(frozen["freeze_merge_commit"]),
            runtime_source_commit=str(frozen["runtime_source_commit"]),
            torch2pc_commit=str(frozen["torch2pc_commit"]),
            image_digest=str(frozen["image_digest"]),
            preflight_sha256=str(frozen["preflight_sha256"]),
            authorization_sha256=str(frozen["authorization_sha256"]),
            authorization_file_sha256=str(
                frozen["authorization_file_sha256"]
            ),
            manifest_file_sha256=str(
                frozen["manifest_file_sha256"]
            ),
            output_root=str(frozen["output_root"]),
            execution_count=_as_int(
                frozen["execution_count"],
                "frozen_runtime.execution_count",
            ),
            authorized_cell_count=_as_int(
                frozen["authorized_cell_count"],
                "frozen_runtime.authorized_cell_count",
            ),
            runtime_execution_permitted=bool(
                frozen["runtime_execution_permitted"]
            ),
            runtime_execution_performed=bool(
                frozen["runtime_execution_performed"]
            ),
            engineering_evidence_present=bool(
                frozen["engineering_evidence_present"]
            ),
            scientific_execution_open=bool(
                frozen["scientific_execution_open"]
            ),
            test_dataset_access=bool(frozen["test_dataset_access"]),
            publication_permitted=bool(
                frozen["publication_permitted"]
            ),
        ),
        output_root_absent_at_admission=bool(
            payload["output_root_absent_at_admission"]
        ),
        execution_lease_absent_at_admission=bool(
            payload["execution_lease_absent_at_admission"]
        ),
        authorization_consumed=bool(payload["authorization_consumed"]),
        execution_count=_as_int(payload["execution_count"], "execution_count"),
        runtime_execution_permitted=bool(
            payload["runtime_execution_permitted"]
        ),
        runtime_execution_started=bool(
            payload["runtime_execution_started"]
        ),
        runtime_execution_performed=bool(
            payload["runtime_execution_performed"]
        ),
        engineering_evidence_present=bool(
            payload["engineering_evidence_present"]
        ),
        scientific_execution_open=bool(
            payload["scientific_execution_open"]
        ),
        test_dataset_access=bool(payload["test_dataset_access"]),
        publication_permitted=bool(payload["publication_permitted"]),
        admission_sha256=str(payload["admission_sha256"]),
    )
    admission.require()
    return admission


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
    """Return prefixed SHA-256 over canonical JSON bytes."""

    return (
        "sha256:"
        + hashlib.sha256(
            canonical_json(value).encode("utf-8")
        ).hexdigest()
    )


def _verify_registry(registry_path: Path, base: Path) -> None:
    if not registry_path.is_file():
        raise QWakeLC4ExecutionAdmissionError(
            f"checksum registry is absent: {registry_path}"
        )
    lines = registry_path.read_text(encoding="utf-8").splitlines()
    if not lines:
        raise QWakeLC4ExecutionAdmissionError(
            "checksum registry is empty"
        )
    for line in lines:
        try:
            expected, relative = line.split("  ", 1)
        except ValueError as exc:
            raise QWakeLC4ExecutionAdmissionError(
                "checksum registry line is malformed"
            ) from exc
        target = base / relative
        if not target.is_file() or target.is_symlink():
            raise QWakeLC4ExecutionAdmissionError(
                f"checksum target is not a regular file: {relative}"
            )
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual != expected:
            raise QWakeLC4ExecutionAdmissionError(
                f"checksum target differs: {relative}"
            )


def _read_json_object(path: Path) -> dict[str, object]:
    if not path.is_file() or path.is_symlink():
        raise QWakeLC4ExecutionAdmissionError(
            f"JSON file is absent: {path}"
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise QWakeLC4ExecutionAdmissionError(
            f"JSON object expected: {path}"
        )
    return cast(dict[str, object], payload)


def _sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _require_commit(value: str, field_name: str) -> None:
    if not _COMMIT_PATTERN.fullmatch(value):
        raise QWakeLC4ExecutionAdmissionError(
            f"{field_name} is not a commit"
        )


def _require_sha256(value: str, field_name: str) -> None:
    if not _SHA256_PATTERN.fullmatch(value):
        raise QWakeLC4ExecutionAdmissionError(
            f"{field_name} is not a SHA-256 identity"
        )


def _require_utc(value: str) -> None:
    if not value.endswith("Z") or "T" not in value:
        raise QWakeLC4ExecutionAdmissionError(
            "admitted_at_utc is not canonical UTC"
        )



def _as_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise QWakeLC4ExecutionAdmissionError(
            f"{field_name} must be an integer"
        )
    return value

def _as_mapping(
    value: object,
    field_name: str,
) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise QWakeLC4ExecutionAdmissionError(
            f"{field_name} must be an object"
        )
    return cast(Mapping[str, object], value)


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
    raise QWakeLC4ExecutionAdmissionError(
        f"unsupported canonical value: {type(value).__name__}"
    )
