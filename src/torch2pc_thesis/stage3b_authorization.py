"""Freeze and verify authorization inputs for the Stage 3B B0 campaign."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, cast

import torch

from torch2pc_thesis.stage3b_execution import (
    MEASURED_STEPS,
    REPETITIONS,
    STAGE3B_CAMPAIGN_ID,
    STAGE3B_EXECUTION_SCHEMA_VERSION,
    WARMUP_STEPS,
    Stage3BExecutionError,
    validate_manifest,
    validated_temporary_output_root,
)
from torch2pc_thesis.stage3b_protocol_contract import (
    B0_CANONICAL_CELL_COUNT,
    B0_CANONICAL_LANES,
    B0_ENGINEERING_CONTROL_LANES,
    B0_PROTOCOL_CONTRACT,
    B0_PROTOCOL_CONTRACT_DIGEST,
    B0_SUPPORTED_PREFLIGHT_LANES,
)

B0_AUTHORIZATION_SCHEMA_VERSION: Final[int] = 2
B0_AUTHORIZATION_SCOPE: Final[str] = "stage3b_b0_rocm_canonical_campaign"
B0_PROJECT_FREEZE_SCOPE: Final[str] = "stage3b_b0_project_freeze"
B0_LANE_PREFLIGHT_SCOPE: Final[str] = "stage3b_b0_lane_preflight"
B0_CANDIDATE_ID: Final[str] = "stage2_baseline"
B0_EXPECTED_CELL_COUNT: Final[int] = B0_CANONICAL_CELL_COUNT
B0_DEFAULT_MINIMUM_FREE_BYTES: Final[int] = 20 * 1024**3
B0_OPERATOR_ACKNOWLEDGEMENT: Final[str] = (
    "AUTHORIZE_STAGE3B_B0_ROCM_FLOAT32_CANONICAL_96_CELL_CAMPAIGN"
)
# Compatibility alias: required lanes are canonical lanes only.
B0_REQUIRED_LANES: Final[tuple[tuple[str, str], ...]] = B0_CANONICAL_LANES
B0_AUTHORIZATION_DOMAIN: Final[str] = "torch2pc-stage3b-b0-rocm-authorization-v2"

_CLEAN_COMMIT_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[0-9a-f]{40}$")
_SHA256_IDENTIFIER_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^sha256:[0-9a-f]{64}$"
)


@dataclass(frozen=True)
class RuntimeProbe:
    """Stable runtime identity used by one authorized execution lane."""

    python_version: str
    pytorch_version: str
    hip_version: str | None
    cuda_available: bool
    device_count: int
    device_name: str
    platform: str
    machine: str
    effective_uid: int
    effective_gid: int

    def to_record(self) -> dict[str, object]:
        return asdict(self)


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _utc_now() -> str:
    return datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")


def _validated_commit(source_commit: str) -> str:
    normalized = source_commit.strip().lower()
    if not _CLEAN_COMMIT_PATTERN.fullmatch(normalized):
        raise Stage3BExecutionError(
            "B0 campaign authorization requires an exact 40-character source commit"
        )
    return normalized


def _require_int(value: object, *, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise Stage3BExecutionError(f"{field} must be an integer")
    return value


def _validated_image_digest(image_digest: str) -> str:
    normalized = image_digest.strip().lower()
    if not _SHA256_IDENTIFIER_PATTERN.fullmatch(normalized):
        raise Stage3BExecutionError(
            "B0 campaign authorization requires an exact sha256:<64 hex> image digest"
        )
    return normalized


def _validated_lane(*, device: str, dtype: str) -> tuple[str, str]:
    lane = (device.strip().lower(), dtype.strip().lower())
    if lane not in B0_SUPPORTED_PREFLIGHT_LANES:
        raise Stage3BExecutionError(
            "B0 preflight lanes are limited to rocm/float32 canonical and "
            "cpu/float64 engineering control"
        )
    return lane


def _lane_role(lane: tuple[str, str]) -> str:
    if lane in B0_CANONICAL_LANES:
        return "canonical"
    if lane in B0_ENGINEERING_CONTROL_LANES:
        return "engineering_control"
    raise Stage3BExecutionError(f"unsupported B0 lane: {lane}")


def _run_git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip()
        raise Stage3BExecutionError(
            f"git {' '.join(arguments)} failed for {root}: {message}"
        )
    return completed.stdout.strip()


def _validate_output_root(
    output_root: Path,
    *,
    minimum_free_bytes: int,
    create: bool,
) -> tuple[Path, dict[str, object]]:
    if minimum_free_bytes < 1:
        raise Stage3BExecutionError("minimum_free_bytes must be positive")
    resolved = validated_temporary_output_root(output_root)
    if create:
        resolved.mkdir(parents=True, exist_ok=True)
    if not resolved.is_dir():
        raise Stage3BExecutionError(f"authorization output root is missing: {resolved}")
    stat = resolved.stat()
    if not os.access(resolved, os.R_OK | os.W_OK | os.X_OK):
        raise Stage3BExecutionError(
            "authorization output root must be readable, writable and searchable"
        )
    free_bytes = shutil.disk_usage(resolved).free
    if free_bytes < minimum_free_bytes:
        raise Stage3BExecutionError(
            "authorization output root has insufficient free space: "
            f"required={minimum_free_bytes}, observed={free_bytes}"
        )
    emergency_stop = resolved / "EMERGENCY-STOP"
    if emergency_stop.exists():
        raise Stage3BExecutionError(
            f"B0 campaign emergency stop is active: {emergency_stop}"
        )
    return resolved, {
        "observed_free_bytes": free_bytes,
        "output_owner_uid": stat.st_uid,
        "output_owner_gid": stat.st_gid,
        "emergency_stop_path": str(emergency_stop),
    }


def _resolve_torch2pc_provenance(
    torch2pc_dir: Path,
    *,
    expected_commit: str,
) -> dict[str, object]:
    resolved = torch2pc_dir.expanduser().resolve()
    source = resolved / "TorchSeq2PC.py"
    if not source.is_file():
        raise Stage3BExecutionError(f"Torch2PC source is missing: {source}")
    completed = subprocess.run(
        ["git", "-C", str(resolved), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    observed_commit = completed.stdout.strip().lower()
    if completed.returncode == 0 and observed_commit:
        if observed_commit != expected_commit:
            raise Stage3BExecutionError(
                "Torch2PC checkout commit differs from the execution manifest: "
                f"expected={expected_commit}, observed={observed_commit}"
            )
        verification = "git_checkout"
        resolved_commit = observed_commit
    else:
        verification = "manifest_pinned_source_without_git_metadata"
        resolved_commit = expected_commit
    return {
        "torch2pc_path": str(resolved),
        "torch2pc_commit": resolved_commit,
        "torch2pc_commit_verification": verification,
        "torch2pc_source_sha256": _sha256_file(source),
    }


def _canonical_protocol(manifest: Mapping[str, object]) -> dict[str, int]:
    raw_protocol = manifest.get("protocol")
    if not isinstance(raw_protocol, Mapping):
        raise Stage3BExecutionError("Stage 3B manifest protocol is missing")
    protocol = {
        "warmup_steps": int(cast(int, raw_protocol.get("warmup_steps"))),
        "measured_steps": int(cast(int, raw_protocol.get("measured_steps"))),
        "repetitions": int(cast(int, raw_protocol.get("repetitions"))),
    }
    expected = {
        "warmup_steps": WARMUP_STEPS,
        "measured_steps": MEASURED_STEPS,
        "repetitions": REPETITIONS,
    }
    if protocol != expected:
        raise Stage3BExecutionError(
            f"B0 campaign protocol differs from the preregistration: {protocol}"
        )
    return protocol


def _b0_cell_count(manifest: Mapping[str, object]) -> int:
    raw_cells = manifest.get("cells")
    if not isinstance(raw_cells, list):
        raise Stage3BExecutionError("Stage 3B manifest cells must be a list")
    count = 0
    for cell in raw_cells:
        if isinstance(cell, Mapping) and cell.get("candidate_id") == B0_CANDIDATE_ID:
            count += 1
    if count != B0_EXPECTED_CELL_COUNT:
        raise Stage3BExecutionError(
            f"B0 campaign requires {B0_EXPECTED_CELL_COUNT} cells, got {count}"
        )
    return count


def _freeze_stable_projection(record: Mapping[str, object]) -> dict[str, object]:
    keys = (
        "schema_version",
        "campaign_id",
        "freeze_scope",
        "evidence",
        "full_campaign_complete",
        "test_dataset_access",
        "project_source_commit",
        "manifest_digest",
        "candidate_id",
        "b0_cell_count",
        "canonical_protocol",
        "torch2pc_commit",
        "torch2pc_source_sha256",
        "output_root",
        "minimum_free_bytes",
        "emergency_stop_path",
        "protocol_contract_digest",
        "protocol_contract",
        "canonical_lanes",
        "engineering_control_lanes",
    )
    return {key: record[key] for key in keys}


def freeze_project_environment(
    manifest: Mapping[str, object],
    *,
    project_root: Path,
    torch2pc_dir: Path,
    output_root: Path,
    source_commit: str,
    minimum_free_bytes: int = B0_DEFAULT_MINIMUM_FREE_BYTES,
) -> dict[str, object]:
    """Freeze clean project, manifest, Torch2PC and output policy inputs."""

    validate_manifest(manifest)
    clean_commit = _validated_commit(source_commit)
    resolved_project = project_root.expanduser().resolve()
    observed_head = _run_git(resolved_project, "rev-parse", "HEAD").lower()
    if observed_head != clean_commit:
        raise Stage3BExecutionError(
            "project HEAD differs from the requested freeze commit: "
            f"expected={clean_commit}, observed={observed_head}"
        )
    status = _run_git(
        resolved_project,
        "status",
        "--porcelain=v1",
        "--untracked-files=normal",
    )
    if status:
        raise Stage3BExecutionError("project worktree must be clean before authorization")
    resolved_output, output_observation = _validate_output_root(
        output_root,
        minimum_free_bytes=minimum_free_bytes,
        create=True,
    )
    output_owner_uid = _require_int(
        output_observation["output_owner_uid"], field="output_owner_uid"
    )
    output_owner_gid = _require_int(
        output_observation["output_owner_gid"], field="output_owner_gid"
    )
    if output_owner_uid != os.geteuid() or output_owner_gid != os.getegid():
        raise Stage3BExecutionError(
            "project freeze output root must be owned by the host operator"
        )
    expected_torch2pc_commit = str(manifest["torch2pc_source_commit"])
    torch2pc = _resolve_torch2pc_provenance(
        torch2pc_dir,
        expected_commit=expected_torch2pc_commit,
    )
    stable: dict[str, object] = {
        "schema_version": B0_AUTHORIZATION_SCHEMA_VERSION,
        "campaign_id": STAGE3B_CAMPAIGN_ID,
        "freeze_scope": B0_PROJECT_FREEZE_SCOPE,
        "evidence": False,
        "full_campaign_complete": False,
        "test_dataset_access": False,
        "project_source_commit": clean_commit,
        "manifest_digest": str(manifest["manifest_digest"]),
        "candidate_id": B0_CANDIDATE_ID,
        "b0_cell_count": _b0_cell_count(manifest),
        "canonical_protocol": _canonical_protocol(manifest),
        "torch2pc_commit": str(torch2pc["torch2pc_commit"]),
        "torch2pc_source_sha256": str(torch2pc["torch2pc_source_sha256"]),
        "output_root": str(resolved_output),
        "minimum_free_bytes": minimum_free_bytes,
        "emergency_stop_path": str(output_observation["emergency_stop_path"]),
        "protocol_contract_digest": B0_PROTOCOL_CONTRACT_DIGEST,
        "protocol_contract": dict(B0_PROTOCOL_CONTRACT),
        "canonical_lanes": [
            {"device": device, "dtype": dtype}
            for device, dtype in B0_CANONICAL_LANES
        ],
        "engineering_control_lanes": [
            {"device": device, "dtype": dtype}
            for device, dtype in B0_ENGINEERING_CONTROL_LANES
        ],
    }
    return {
        **stable,
        "freeze_digest": _digest(stable),
        "created_at": _utc_now(),
        "project_root": str(resolved_project),
        "project_commit_verification": "git_clean_exact_head",
        "torch2pc_path": str(torch2pc["torch2pc_path"]),
        "torch2pc_commit_verification": str(
            torch2pc["torch2pc_commit_verification"]
        ),
        "observed_free_bytes": _require_int(
            output_observation["observed_free_bytes"], field="observed_free_bytes"
        ),
        "output_owner_uid": output_owner_uid,
        "output_owner_gid": output_owner_gid,
    }


def validate_project_freeze(record: Mapping[str, object]) -> None:
    """Validate a project freeze record and its stable digest."""

    if record.get("schema_version") != B0_AUTHORIZATION_SCHEMA_VERSION:
        raise Stage3BExecutionError("unsupported B0 authorization schema")
    if record.get("campaign_id") != STAGE3B_CAMPAIGN_ID:
        raise Stage3BExecutionError("unexpected B0 authorization campaign")
    if record.get("freeze_scope") != B0_PROJECT_FREEZE_SCOPE:
        raise Stage3BExecutionError("unexpected B0 project freeze scope")
    if record.get("evidence") is not False:
        raise Stage3BExecutionError("project freeze must remain non-evidence")
    if record.get("full_campaign_complete") is not False:
        raise Stage3BExecutionError("project freeze cannot mark the campaign complete")
    if record.get("test_dataset_access") is not False:
        raise Stage3BExecutionError("project freeze cannot authorize test dataset access")
    if record.get("protocol_contract_digest") != B0_PROTOCOL_CONTRACT_DIGEST:
        raise Stage3BExecutionError("project freeze uses a different B0 protocol contract")
    if record.get("protocol_contract") != B0_PROTOCOL_CONTRACT:
        raise Stage3BExecutionError("project freeze protocol contract content differs")
    if record.get("canonical_lanes") != [
        {"device": device, "dtype": dtype}
        for device, dtype in B0_CANONICAL_LANES
    ]:
        raise Stage3BExecutionError("project freeze canonical lanes differ from contract")
    if record.get("engineering_control_lanes") != [
        {"device": device, "dtype": dtype}
        for device, dtype in B0_ENGINEERING_CONTROL_LANES
    ]:
        raise Stage3BExecutionError(
            "project freeze engineering control lanes differ from contract"
        )
    _validated_commit(str(record.get("project_source_commit", "")))
    supplied = record.get("freeze_digest")
    if not isinstance(supplied, str) or supplied != _digest(
        _freeze_stable_projection(record)
    ):
        raise Stage3BExecutionError("project freeze digest does not match its content")


def _default_runtime_probe(*, device: str, dtype: str) -> RuntimeProbe:
    normalized_device, _normalized_dtype = _validated_lane(device=device, dtype=dtype)
    cuda_available = torch.cuda.is_available()
    device_count = torch.cuda.device_count() if cuda_available else 0
    if normalized_device == "rocm":
        hip_version = getattr(torch.version, "hip", None)
        if not cuda_available or not hip_version or device_count < 1:
            raise Stage3BExecutionError(
                "ROCm authorization preflight requires an available HIP device"
            )
        device_name = torch.cuda.get_device_name(0)
    else:
        hip_version = getattr(torch.version, "hip", None)
        device_name = "cpu"
    return RuntimeProbe(
        python_version=sys.version,
        pytorch_version=torch.__version__,
        hip_version=hip_version,
        cuda_available=cuda_available,
        device_count=device_count,
        device_name=device_name,
        platform=platform.platform(),
        machine=platform.machine(),
        effective_uid=os.geteuid(),
        effective_gid=os.getegid(),
    )


def _lane_stable_projection(record: Mapping[str, object]) -> dict[str, object]:
    keys = (
        "schema_version",
        "campaign_id",
        "preflight_scope",
        "evidence",
        "full_campaign_complete",
        "freeze_digest",
        "device",
        "dtype",
        "lane_role",
        "image_digest",
        "runtime",
        "output_root",
        "minimum_free_bytes",
        "output_owner_uid",
        "output_owner_gid",
        "emergency_stop_path",
    )
    return {key: record[key] for key in keys}


def capture_lane_preflight(
    freeze_record: Mapping[str, object],
    manifest: Mapping[str, object],
    *,
    torch2pc_dir: Path,
    source_commit: str,
    device: str,
    dtype: str,
    image_digest: str,
    probe: RuntimeProbe | None = None,
) -> dict[str, object]:
    """Capture one stable CPU or ROCm lane fingerprint."""

    validate_project_freeze(freeze_record)
    validate_manifest(manifest)
    clean_commit = _validated_commit(source_commit)
    if clean_commit != freeze_record.get("project_source_commit"):
        raise Stage3BExecutionError("lane source commit differs from the project freeze")
    if manifest.get("manifest_digest") != freeze_record.get("manifest_digest"):
        raise Stage3BExecutionError("lane manifest differs from the project freeze")
    torch2pc = _resolve_torch2pc_provenance(
        torch2pc_dir,
        expected_commit=str(freeze_record["torch2pc_commit"]),
    )
    if torch2pc["torch2pc_source_sha256"] != freeze_record.get(
        "torch2pc_source_sha256"
    ):
        raise Stage3BExecutionError("lane Torch2PC source differs from the project freeze")
    normalized_device, normalized_dtype = _validated_lane(device=device, dtype=dtype)
    normalized_image = _validated_image_digest(image_digest)
    minimum_free_bytes = int(cast(int, freeze_record["minimum_free_bytes"]))
    resolved_output, output_observation = _validate_output_root(
        Path(str(freeze_record["output_root"])),
        minimum_free_bytes=minimum_free_bytes,
        create=False,
    )
    observed_owner_uid = _require_int(
        output_observation["output_owner_uid"], field="output_owner_uid"
    )
    observed_owner_gid = _require_int(
        output_observation["output_owner_gid"], field="output_owner_gid"
    )
    expected_owner_uid = _require_int(
        freeze_record.get("output_owner_uid"), field="freeze output_owner_uid"
    )
    expected_owner_gid = _require_int(
        freeze_record.get("output_owner_gid"), field="freeze output_owner_gid"
    )
    if (observed_owner_uid, observed_owner_gid) != (
        expected_owner_uid,
        expected_owner_gid,
    ):
        raise Stage3BExecutionError(
            "authorization output ownership differs from the project freeze"
        )
    runtime = probe or _default_runtime_probe(
        device=normalized_device,
        dtype=normalized_dtype,
    )
    if normalized_device == "rocm" and (
        not runtime.cuda_available
        or not runtime.hip_version
        or runtime.device_count < 1
        or runtime.device_name == "cpu"
    ):
        raise Stage3BExecutionError(
            "ROCm authorization preflight requires an available HIP device"
        )
    if normalized_device == "cpu" and runtime.device_name != "cpu":
        raise Stage3BExecutionError("CPU authorization preflight must identify cpu")
    stable: dict[str, object] = {
        "schema_version": B0_AUTHORIZATION_SCHEMA_VERSION,
        "campaign_id": STAGE3B_CAMPAIGN_ID,
        "preflight_scope": B0_LANE_PREFLIGHT_SCOPE,
        "evidence": False,
        "full_campaign_complete": False,
        "freeze_digest": str(freeze_record["freeze_digest"]),
        "device": normalized_device,
        "dtype": normalized_dtype,
        "lane_role": _lane_role((normalized_device, normalized_dtype)),
        "image_digest": normalized_image,
        "runtime": runtime.to_record(),
        "output_root": str(resolved_output),
        "minimum_free_bytes": minimum_free_bytes,
        "output_owner_uid": observed_owner_uid,
        "output_owner_gid": observed_owner_gid,
        "emergency_stop_path": str(output_observation["emergency_stop_path"]),
    }
    return {
        **stable,
        "lane_preflight_digest": _digest(stable),
        "observed_at": _utc_now(),
        "observed_free_bytes": _require_int(
            output_observation["observed_free_bytes"], field="observed_free_bytes"
        ),
    }


def validate_lane_preflight(record: Mapping[str, object]) -> None:
    """Validate one lane preflight record and its stable digest."""

    if record.get("schema_version") != B0_AUTHORIZATION_SCHEMA_VERSION:
        raise Stage3BExecutionError("unsupported B0 lane preflight schema")
    if record.get("campaign_id") != STAGE3B_CAMPAIGN_ID:
        raise Stage3BExecutionError("unexpected B0 lane preflight campaign")
    if record.get("preflight_scope") != B0_LANE_PREFLIGHT_SCOPE:
        raise Stage3BExecutionError("unexpected B0 lane preflight scope")
    if record.get("evidence") is not False:
        raise Stage3BExecutionError("lane preflight must remain non-evidence")
    if record.get("full_campaign_complete") is not False:
        raise Stage3BExecutionError("lane preflight cannot mark the campaign complete")
    lane = _validated_lane(
        device=str(record.get("device", "")),
        dtype=str(record.get("dtype", "")),
    )
    if record.get("lane_role") != _lane_role(lane):
        raise Stage3BExecutionError("lane preflight role differs from protocol contract")
    _validated_image_digest(str(record.get("image_digest", "")))
    supplied = record.get("lane_preflight_digest")
    if not isinstance(supplied, str) or supplied != _digest(
        _lane_stable_projection(record)
    ):
        raise Stage3BExecutionError("lane preflight digest does not match its content")


def _authorization_payload(record: Mapping[str, object]) -> dict[str, object]:
    return {
        key: value
        for key, value in record.items()
        if key not in {"authorization_token", "authorization_digest"}
    }


def _authorization_token(payload: Mapping[str, object]) -> str:
    material = {
        "domain": B0_AUTHORIZATION_DOMAIN,
        "authorization": dict(payload),
    }
    return _digest(material)


def issue_campaign_authorization(
    freeze_record: Mapping[str, object],
    lane_preflights: Sequence[Mapping[str, object]],
    *,
    operator_acknowledgement: str,
) -> dict[str, object]:
    """Issue a ROCm-only canonical authorization envelope.

    A CPU/float64 preflight may be attached as an engineering-control record,
    but it never becomes a canonical lane and never gates campaign completion.
    """

    validate_project_freeze(freeze_record)
    if operator_acknowledgement != B0_OPERATOR_ACKNOWLEDGEMENT:
        raise Stage3BExecutionError("operator acknowledgement does not match")
    if not lane_preflights:
        raise Stage3BExecutionError(
            "authorization requires the rocm/float32 canonical preflight"
        )

    indexed: dict[tuple[str, str], Mapping[str, object]] = {}
    for preflight in lane_preflights:
        validate_lane_preflight(preflight)
        if preflight.get("freeze_digest") != freeze_record.get("freeze_digest"):
            raise Stage3BExecutionError("lane preflight uses a different project freeze")
        lane = (str(preflight["device"]), str(preflight["dtype"]))
        if lane in indexed:
            raise Stage3BExecutionError(f"duplicate lane preflight: {lane}")
        indexed[lane] = preflight

    unknown = set(indexed) - set(B0_SUPPORTED_PREFLIGHT_LANES)
    if unknown:
        raise Stage3BExecutionError(f"unsupported lane preflights: {sorted(unknown)}")
    if not set(B0_CANONICAL_LANES).issubset(indexed):
        raise Stage3BExecutionError(
            "authorization requires the rocm/float32 canonical preflight"
        )

    canonical_preflights = [
        dict(indexed[lane]) for lane in B0_CANONICAL_LANES
    ]
    control_preflights = [
        dict(indexed[lane])
        for lane in B0_ENGINEERING_CONTROL_LANES
        if lane in indexed
    ]
    payload: dict[str, object] = {
        "schema_version": B0_AUTHORIZATION_SCHEMA_VERSION,
        "campaign_id": STAGE3B_CAMPAIGN_ID,
        "authorization_scope": B0_AUTHORIZATION_SCOPE,
        "protocol_contract_digest": B0_PROTOCOL_CONTRACT_DIGEST,
        "execution_permitted": True,
        "evidence": False,
        "full_campaign_complete": False,
        "results_publication_permitted": False,
        "test_dataset_access": False,
        "candidate_id": B0_CANDIDATE_ID,
        "authorized_cell_count": B0_EXPECTED_CELL_COUNT,
        "canonical_execution_count": B0_EXPECTED_CELL_COUNT,
        "canonical_protocol": dict(
            cast(Mapping[str, int], freeze_record["canonical_protocol"])
        ),
        "canonical_lanes": [
            {"device": device, "dtype": dtype}
            for device, dtype in B0_CANONICAL_LANES
        ],
        "engineering_control_lanes": [
            {
                "device": device,
                "dtype": dtype,
                "required_for_campaign_completion": False,
                "confirmatory_performance_evidence": False,
            }
            for device, dtype in B0_ENGINEERING_CONTROL_LANES
        ],
        "project_source_commit": str(freeze_record["project_source_commit"]),
        "manifest_digest": str(freeze_record["manifest_digest"]),
        "torch2pc_commit": str(freeze_record["torch2pc_commit"]),
        "torch2pc_source_sha256": str(freeze_record["torch2pc_source_sha256"]),
        "output_root": str(freeze_record["output_root"]),
        "minimum_free_bytes": int(cast(int, freeze_record["minimum_free_bytes"])),
        "emergency_stop_path": str(freeze_record["emergency_stop_path"]),
        "resume_policy": {
            "preserve_all_attempts": True,
            "silent_overwrite": False,
            "matching_success_is_terminal": True,
            "failed_and_interrupted_attempts_require_explicit_resume": True,
        },
        "freeze_record": dict(freeze_record),
        # Backward-compatible key name used by the canonical runner. It now
        # contains canonical preflights only.
        "lane_preflights": canonical_preflights,
        "canonical_lane_preflights": canonical_preflights,
        "engineering_control_preflights": control_preflights,
        "issued_at": _utc_now(),
    }
    token = _authorization_token(payload)
    return {
        **payload,
        "authorization_token": token,
        "authorization_digest": token,
    }

def validate_campaign_authorization(record: Mapping[str, object]) -> None:
    """Validate a complete ROCm-only campaign authorization envelope."""

    if record.get("schema_version") != B0_AUTHORIZATION_SCHEMA_VERSION:
        raise Stage3BExecutionError(
            "unsupported or retired B0 campaign authorization schema"
        )
    if record.get("campaign_id") != STAGE3B_CAMPAIGN_ID:
        raise Stage3BExecutionError("unexpected B0 campaign authorization campaign")
    if record.get("authorization_scope") != B0_AUTHORIZATION_SCOPE:
        raise Stage3BExecutionError(
            "unexpected or retired B0 campaign authorization scope"
        )
    if record.get("protocol_contract_digest") != B0_PROTOCOL_CONTRACT_DIGEST:
        raise Stage3BExecutionError(
            "authorization uses a different B0 protocol contract"
        )
    if record.get("execution_permitted") is not True:
        raise Stage3BExecutionError("B0 campaign execution is not permitted")
    if record.get("evidence") is not False:
        raise Stage3BExecutionError("authorization must remain non-evidence")
    if record.get("full_campaign_complete") is not False:
        raise Stage3BExecutionError("authorization cannot mark the campaign complete")
    if record.get("results_publication_permitted") is not False:
        raise Stage3BExecutionError("authorization cannot permit results publication")
    if record.get("test_dataset_access") is not False:
        raise Stage3BExecutionError("authorization cannot permit test dataset access")

    freeze_record = record.get("freeze_record")
    if not isinstance(freeze_record, Mapping):
        raise Stage3BExecutionError("authorization freeze_record is missing")
    validate_project_freeze(freeze_record)
    expected_from_freeze = {
        "project_source_commit": freeze_record.get("project_source_commit"),
        "manifest_digest": freeze_record.get("manifest_digest"),
        "torch2pc_commit": freeze_record.get("torch2pc_commit"),
        "torch2pc_source_sha256": freeze_record.get("torch2pc_source_sha256"),
        "output_root": freeze_record.get("output_root"),
        "minimum_free_bytes": freeze_record.get("minimum_free_bytes"),
        "canonical_protocol": freeze_record.get("canonical_protocol"),
        "protocol_contract_digest": freeze_record.get("protocol_contract_digest"),
    }
    for key, expected_value in expected_from_freeze.items():
        if record.get(key) != expected_value:
            raise Stage3BExecutionError(
                f"authorization {key} differs from the project freeze"
            )
    if record.get("candidate_id") != B0_CANDIDATE_ID:
        raise Stage3BExecutionError("authorization candidate_id differs from B0")
    if record.get("authorized_cell_count") != B0_EXPECTED_CELL_COUNT:
        raise Stage3BExecutionError("authorization cell count differs from B0")
    if record.get("canonical_execution_count") != B0_EXPECTED_CELL_COUNT:
        raise Stage3BExecutionError(
            "authorization canonical execution count must remain 96"
        )
    expected_canonical_lanes = [
        {"device": device, "dtype": dtype}
        for device, dtype in B0_CANONICAL_LANES
    ]
    if record.get("canonical_lanes") != expected_canonical_lanes:
        raise Stage3BExecutionError(
            "authorization canonical lanes differ from ROCm-only contract"
        )
    expected_control_lanes = [
        {
            "device": device,
            "dtype": dtype,
            "required_for_campaign_completion": False,
            "confirmatory_performance_evidence": False,
        }
        for device, dtype in B0_ENGINEERING_CONTROL_LANES
    ]
    if record.get("engineering_control_lanes") != expected_control_lanes:
        raise Stage3BExecutionError(
            "authorization engineering control lanes differ from contract"
        )

    lane_preflights = record.get("lane_preflights")
    if not isinstance(lane_preflights, list):
        raise Stage3BExecutionError("authorization lane_preflights are missing")
    if record.get("canonical_lane_preflights") != lane_preflights:
        raise Stage3BExecutionError(
            "authorization canonical preflight aliases differ"
        )
    canonical_lanes: set[tuple[str, str]] = set()
    for preflight in lane_preflights:
        if not isinstance(preflight, Mapping):
            raise Stage3BExecutionError("authorization lane preflight is invalid")
        validate_lane_preflight(preflight)
        if preflight.get("freeze_digest") != freeze_record.get("freeze_digest"):
            raise Stage3BExecutionError("authorization lane uses a different freeze")
        lane = (str(preflight["device"]), str(preflight["dtype"]))
        if lane not in B0_CANONICAL_LANES:
            raise Stage3BExecutionError(
                "authorization canonical preflights contain a noncanonical lane"
            )
        canonical_lanes.add(lane)
    if canonical_lanes != set(B0_CANONICAL_LANES):
        raise Stage3BExecutionError(
            "authorization does not contain the rocm/float32 canonical lane"
        )

    controls = record.get("engineering_control_preflights", [])
    if not isinstance(controls, list):
        raise Stage3BExecutionError(
            "authorization engineering_control_preflights must be a list"
        )
    control_lanes: set[tuple[str, str]] = set()
    for preflight in controls:
        if not isinstance(preflight, Mapping):
            raise Stage3BExecutionError("engineering control preflight is invalid")
        validate_lane_preflight(preflight)
        if preflight.get("freeze_digest") != freeze_record.get("freeze_digest"):
            raise Stage3BExecutionError(
                "engineering control preflight uses a different freeze"
            )
        lane = (str(preflight["device"]), str(preflight["dtype"]))
        if lane not in B0_ENGINEERING_CONTROL_LANES:
            raise Stage3BExecutionError(
                "authorization contains an unsupported engineering control lane"
            )
        if lane in control_lanes:
            raise Stage3BExecutionError(
                f"duplicate engineering control preflight: {lane}"
            )
        control_lanes.add(lane)

    supplied = record.get("authorization_token")
    expected = _authorization_token(_authorization_payload(record))
    if not isinstance(supplied, str) or supplied != expected:
        raise Stage3BExecutionError("authorization token does not match its content")
    if record.get("authorization_digest") != supplied:
        raise Stage3BExecutionError("authorization digest differs from its token")

def verify_authorization_for_lane(
    authorization: Mapping[str, object],
    manifest: Mapping[str, object],
    *,
    torch2pc_dir: Path,
    output_root: Path,
    source_commit: str,
    device: str,
    dtype: str,
    image_digest: str,
    probe: RuntimeProbe | None = None,
) -> dict[str, object]:
    """Verify one canonical or optional engineering-control fingerprint."""

    validate_campaign_authorization(authorization)
    validate_manifest(manifest)
    clean_commit = _validated_commit(source_commit)
    normalized_device, normalized_dtype = _validated_lane(device=device, dtype=dtype)
    lane = (normalized_device, normalized_dtype)
    role = _lane_role(lane)
    normalized_image = _validated_image_digest(image_digest)
    if clean_commit != authorization.get("project_source_commit"):
        raise Stage3BExecutionError("runtime source commit differs from authorization")
    if manifest.get("manifest_digest") != authorization.get("manifest_digest"):
        raise Stage3BExecutionError("runtime manifest differs from authorization")
    resolved_output = validated_temporary_output_root(output_root)
    if str(resolved_output) != authorization.get("output_root"):
        raise Stage3BExecutionError("runtime output root differs from authorization")
    freeze_record = cast(Mapping[str, object], authorization["freeze_record"])
    torch2pc = _resolve_torch2pc_provenance(
        torch2pc_dir,
        expected_commit=str(authorization["torch2pc_commit"]),
    )
    if torch2pc["torch2pc_source_sha256"] != authorization.get(
        "torch2pc_source_sha256"
    ):
        raise Stage3BExecutionError("runtime Torch2PC source differs from authorization")
    current_lane = capture_lane_preflight(
        freeze_record,
        manifest,
        torch2pc_dir=torch2pc_dir,
        source_commit=clean_commit,
        device=normalized_device,
        dtype=normalized_dtype,
        image_digest=normalized_image,
        probe=probe,
    )
    if role == "canonical":
        authorized_lanes = cast(
            list[Mapping[str, object]], authorization["lane_preflights"]
        )
    else:
        authorized_lanes = cast(
            list[Mapping[str, object]],
            authorization.get("engineering_control_preflights", []),
        )
    matches = [
        item
        for item in authorized_lanes
        if item.get("device") == normalized_device
        and item.get("dtype") == normalized_dtype
    ]
    if len(matches) != 1:
        raise Stage3BExecutionError(
            f"authorization has no unique {role} fingerprint for {lane}"
        )
    if current_lane["lane_preflight_digest"] != matches[0].get(
        "lane_preflight_digest"
    ):
        raise Stage3BExecutionError("runtime lane fingerprint differs from authorization")
    return {
        "schema_version": STAGE3B_EXECUTION_SCHEMA_VERSION,
        "campaign_id": STAGE3B_CAMPAIGN_ID,
        "authorization_scope": B0_AUTHORIZATION_SCOPE,
        "authorization_verified": True,
        "authorization_token": str(authorization["authorization_token"]),
        "project_source_commit": clean_commit,
        "manifest_digest": str(manifest["manifest_digest"]),
        "device": normalized_device,
        "dtype": normalized_dtype,
        "lane_role": role,
        "image_digest": normalized_image,
        # Verification is permitted for an attached engineering-control record,
        # but only a canonical lane may be executed by the canonical runner.
        "execution_permitted": True,
        "canonical_execution_permitted": role == "canonical",
        "required_for_campaign_completion": role == "canonical",
        "confirmatory_performance_evidence": role == "canonical",
        "evidence": False,
        "full_campaign_complete": False,
        "results_publication_permitted": False,
        "test_dataset_access": False,
        "verified_at": _utc_now(),
    }
