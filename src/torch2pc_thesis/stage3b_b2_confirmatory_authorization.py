"""Fail-closed authorization for the confirmatory Stage 3B B2 campaign."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final, cast

import torch

from torch2pc_thesis.stage3b_b1_equivalence import canonical_json_digest, sha256_file
from torch2pc_thesis.stage3b_b2_confirmatory import (
    B2_CONFIRMATORY_CAMPAIGN_ID,
    B2_CONFIRMATORY_ENGINEERING_SMOKE_COMPARISON_COUNT,
    B2_CONFIRMATORY_ENGINEERING_SMOKE_TRIPLE_COUNT,
    B2_CONFIRMATORY_EXPECTED_COMPARISON_COUNT,
    B2_CONFIRMATORY_EXPECTED_LANES,
    B2_CONFIRMATORY_EXPECTED_TRIPLE_COUNT,
    B2ConfirmatoryError,
    validate_confirmatory_request,
)
from torch2pc_thesis.stage3b_execution import validated_temporary_output_root

B2_CONFIRMATORY_AUTHORIZATION_SCHEMA_VERSION: Final[int] = 1
B2_CONFIRMATORY_FREEZE_SCOPE: Final[str] = "stage3b_b2_confirmatory_project_freeze"
B2_CONFIRMATORY_PREFLIGHT_SCOPE: Final[str] = "stage3b_b2_confirmatory_lane_preflight"
B2_CONFIRMATORY_AUTHORIZATION_SCOPE: Final[str] = (
    "stage3b_b2_confirmatory_cpu_float64_rocm_float32_campaign"
)
B2_CONFIRMATORY_ENGINEERING_SMOKE_AUTHORIZATION_SCOPE: Final[str] = (
    "stage3b_b2_engineering_smoke_cpu_float64_rocm_float32"
)
B2_CONFIRMATORY_AUTHORIZATION_DOMAIN: Final[str] = (
    "torch2pc-stage3b-b2-confirmatory-authorization-v1"
)
B2_CONFIRMATORY_OPERATOR_ACKNOWLEDGEMENT: Final[str] = (
    "AUTHORIZE_STAGE3B_B2_CONFIRMATORY_120_MATCHED_TRIPLES_240_COMPARISONS_CPU_FLOAT64_ROCM_FLOAT32"
)
B2_CONFIRMATORY_ENGINEERING_SMOKE_ACKNOWLEDGEMENT: Final[str] = (
    "AUTHORIZE_STAGE3B_B2_ENGINEERING_SMOKE_12_MATCHED_TRIPLES_24_COMPARISONS_CPU_FLOAT64_ROCM_FLOAT32_NON_EVIDENCE"
)
B2_CONFIRMATORY_EXECUTION_MODES: Final[tuple[str, ...]] = (
    "confirmatory",
    "engineering_smoke",
)
B2_CONFIRMATORY_DEFAULT_MINIMUM_FREE_BYTES: Final[int] = 8 * 1024**3

_COMMIT_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[0-9a-f]{40}$")
_IMAGE_PATTERN: Final[re.Pattern[str]] = re.compile(r"^sha256:[0-9a-f]{64}$")


@dataclass(frozen=True)
class B2ConfirmatoryRuntimeProbe:
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


def capture_runtime_probe() -> B2ConfirmatoryRuntimeProbe:
    device_count = torch.cuda.device_count() if torch.cuda.is_available() else 0
    device_name = torch.cuda.get_device_name(0) if device_count else "cpu"
    return B2ConfirmatoryRuntimeProbe(
        python_version=platform.python_version(),
        pytorch_version=torch.__version__,
        hip_version=getattr(torch.version, "hip", None),
        cuda_available=torch.cuda.is_available(),
        device_count=device_count,
        device_name=device_name,
        platform=platform.platform(),
        machine=platform.machine(),
        effective_uid=os.geteuid(),
        effective_gid=os.getegid(),
    )


def freeze_b2_confirmatory_project(
    request: Mapping[str, object],
    *,
    request_path: Path,
    project_root: Path,
    torch2pc_dir: Path,
    output_root: Path,
    source_commit: str,
    image_digest: str,
    execution_mode: str = "confirmatory",
    minimum_free_bytes: int = B2_CONFIRMATORY_DEFAULT_MINIMUM_FREE_BYTES,
) -> dict[str, object]:
    validate_confirmatory_request(request)
    clean_commit = _validate_commit(source_commit)
    clean_image = _validate_image_digest(image_digest)
    clean_execution_mode = _validate_execution_mode(execution_mode)
    _, _, authorized_triple_count = _execution_contract(clean_execution_mode)
    root = _validate_clean_project(project_root, clean_commit)
    output, output_record = _validate_output_root(
        output_root,
        minimum_free_bytes=minimum_free_bytes,
        create=True,
    )
    if any(output.iterdir()):
        raise B2ConfirmatoryError(f"new authorization output root must be empty: {output}")
    torch2pc = _resolve_torch2pc(
        torch2pc_dir,
        expected_commit=str(request["torch2pc_commit"]),
    )
    request_resolved = request_path.expanduser().resolve()
    try:
        request_resolved.relative_to(root)
    except ValueError as error:
        raise B2ConfirmatoryError(
            f"confirmatory request must be under project root: {request_resolved}"
        ) from error
    if not request_resolved.is_file():
        raise B2ConfirmatoryError(f"confirmatory request is missing: {request_resolved}")
    request_from_file = json.loads(request_resolved.read_text(encoding="utf-8"))
    if request_from_file != dict(request):
        raise B2ConfirmatoryError(
            "confirmatory request object differs from the frozen request file"
        )
    _verify_registered_assets(request, project_root=root)
    payload: dict[str, object] = {
        "schema_version": B2_CONFIRMATORY_AUTHORIZATION_SCHEMA_VERSION,
        "campaign_id": B2_CONFIRMATORY_CAMPAIGN_ID,
        "freeze_scope": B2_CONFIRMATORY_FREEZE_SCOPE,
        "project_source_commit": clean_commit,
        "request_path": str(request_resolved),
        "request_digest": canonical_json_digest(request),
        "request_file_sha256": sha256_file(request_resolved),
        "contract_digest": request["contract_digest"],
        "resolved_config_digest": request["resolved_config_digest"],
        "source_image_digest": clean_image,
        "execution_mode": clean_execution_mode,
        "authorized_triple_count": authorized_triple_count,
        "authorized_comparison_count": (
            B2_CONFIRMATORY_EXPECTED_COMPARISON_COUNT
            if clean_execution_mode == "confirmatory"
            else B2_CONFIRMATORY_ENGINEERING_SMOKE_COMPARISON_COUNT
        ),
        "canonical_lanes": list(B2_CONFIRMATORY_EXPECTED_LANES),
        "output_root": str(output),
        "minimum_free_bytes": minimum_free_bytes,
        **output_record,
        **torch2pc,
        "evidence": False,
        "full_confirmatory_campaign_complete": False,
        "results_publication_permitted": False,
        "test_dataset_access": False,
    }
    payload["freeze_digest"] = _digest(payload)
    return payload


def capture_b2_confirmatory_lane_preflight(
    freeze_record: Mapping[str, object],
    request: Mapping[str, object],
    *,
    project_root: Path,
    torch2pc_dir: Path,
    output_root: Path,
    source_commit: str,
    lane: str,
    image_digest: str,
    runtime_probe: B2ConfirmatoryRuntimeProbe | None = None,
) -> dict[str, object]:
    validate_freeze_record(freeze_record)
    validate_confirmatory_request(request)
    clean_commit = _validate_commit(source_commit)
    clean_image = _validate_image_digest(image_digest)
    if lane not in B2_CONFIRMATORY_EXPECTED_LANES:
        raise B2ConfirmatoryError(f"unsupported confirmatory lane: {lane}")
    _validate_freeze_binding(
        freeze_record,
        request,
        output_root=output_root,
        source_commit=clean_commit,
        image_digest=clean_image,
    )
    _validate_clean_project(project_root, clean_commit)
    _resolve_torch2pc(
        torch2pc_dir,
        expected_commit=str(request["torch2pc_commit"]),
    )
    probe = runtime_probe or capture_runtime_probe()
    _validate_runtime_for_lane(lane, probe)
    payload: dict[str, object] = {
        "schema_version": B2_CONFIRMATORY_AUTHORIZATION_SCHEMA_VERSION,
        "campaign_id": B2_CONFIRMATORY_CAMPAIGN_ID,
        "preflight_scope": B2_CONFIRMATORY_PREFLIGHT_SCOPE,
        "freeze_digest": freeze_record["freeze_digest"],
        "request_digest": freeze_record["request_digest"],
        "project_source_commit": clean_commit,
        "image_digest": clean_image,
        "execution_mode": freeze_record["execution_mode"],
        "lane": lane,
        "runtime": probe.to_record(),
        "output_root": freeze_record["output_root"],
        "minimum_free_bytes": freeze_record["minimum_free_bytes"],
        "evidence": False,
        "full_confirmatory_campaign_complete": False,
        "results_publication_permitted": False,
        "test_dataset_access": False,
    }
    payload["lane_preflight_digest"] = _digest(payload)
    return payload


def issue_b2_confirmatory_authorization(
    freeze_record: Mapping[str, object],
    lane_preflights: Sequence[Mapping[str, object]],
    *,
    operator_acknowledgement: str,
) -> dict[str, object]:
    validate_freeze_record(freeze_record)
    execution_mode = _validate_execution_mode(str(freeze_record.get("execution_mode", "")))
    authorization_scope, expected_acknowledgement, authorized_triple_count = _execution_contract(
        execution_mode
    )
    if operator_acknowledgement != expected_acknowledgement:
        raise B2ConfirmatoryError("operator acknowledgement does not match")
    if len(lane_preflights) != 2:
        raise B2ConfirmatoryError("confirmatory authorization requires exactly two lane preflights")
    by_lane: dict[str, Mapping[str, object]] = {}
    for preflight in lane_preflights:
        validate_lane_preflight(preflight)
        lane = str(preflight["lane"])
        if lane in by_lane:
            raise B2ConfirmatoryError(f"duplicate lane preflight: {lane}")
        if preflight["freeze_digest"] != freeze_record["freeze_digest"]:
            raise B2ConfirmatoryError("lane preflight freeze digest mismatch")
        if preflight["request_digest"] != freeze_record["request_digest"]:
            raise B2ConfirmatoryError("lane preflight request digest mismatch")
        if preflight["execution_mode"] != execution_mode:
            raise B2ConfirmatoryError("lane preflight execution mode mismatch")
        for preflight_key, freeze_key in (
            ("project_source_commit", "project_source_commit"),
            ("output_root", "output_root"),
            ("minimum_free_bytes", "minimum_free_bytes"),
        ):
            if preflight[preflight_key] != freeze_record[freeze_key]:
                raise B2ConfirmatoryError(
                    f"lane preflight {preflight_key} mismatch"
                )
        by_lane[lane] = preflight
    if set(by_lane) != set(B2_CONFIRMATORY_EXPECTED_LANES):
        raise B2ConfirmatoryError("authorization requires cpu_float64 and rocm_float32 preflights")
    image_digests = {str(value["image_digest"]) for value in by_lane.values()}
    if len(image_digests) != 1:
        raise B2ConfirmatoryError("lane preflights must use one immutable image")
    image_digest = next(iter(image_digests))
    if image_digest != freeze_record["source_image_digest"]:
        raise B2ConfirmatoryError("preflight image differs from frozen request image")

    token_material = {
        "domain": B2_CONFIRMATORY_AUTHORIZATION_DOMAIN,
        "freeze_digest": freeze_record["freeze_digest"],
        "lane_preflight_digests": {
            lane: by_lane[lane]["lane_preflight_digest"] for lane in B2_CONFIRMATORY_EXPECTED_LANES
        },
        "operator_acknowledgement": operator_acknowledgement,
        "execution_mode": execution_mode,
    }
    authorization_token = _digest(token_material)
    payload: dict[str, object] = {
        "schema_version": B2_CONFIRMATORY_AUTHORIZATION_SCHEMA_VERSION,
        "campaign_id": B2_CONFIRMATORY_CAMPAIGN_ID,
        "authorization_scope": authorization_scope,
        "execution_mode": execution_mode,
        "authorization_token": authorization_token,
        "freeze_digest": freeze_record["freeze_digest"],
        "request_digest": freeze_record["request_digest"],
        "project_source_commit": freeze_record["project_source_commit"],
        "torch2pc_commit": freeze_record["torch2pc_commit"],
        "image_digest": image_digest,
        "authorized_triple_count": authorized_triple_count,
        "authorized_comparison_count": (
            B2_CONFIRMATORY_EXPECTED_COMPARISON_COUNT
            if execution_mode == "confirmatory"
            else B2_CONFIRMATORY_ENGINEERING_SMOKE_COMPARISON_COUNT
        ),
        "authorized_lanes": list(B2_CONFIRMATORY_EXPECTED_LANES),
        "lane_preflight_digests": token_material["lane_preflight_digests"],
        "operator_acknowledgement": operator_acknowledgement,
        "output_root": freeze_record["output_root"],
        "emergency_stop_path": freeze_record["emergency_stop_path"],
        "minimum_free_bytes": freeze_record["minimum_free_bytes"],
        "runtime_authorization": "issued",
        "execution_permitted": True,
        "measurements_allowed": True,
        "evidence": False,
        "full_confirmatory_campaign_complete": False,
        "results_publication_permitted": False,
        "test_dataset_access": False,
    }
    payload["authorization_digest"] = _digest(payload)
    return payload


def verify_b2_confirmatory_authorization_for_lane(
    authorization: Mapping[str, object],
    request: Mapping[str, object],
    *,
    project_root: Path,
    torch2pc_dir: Path,
    output_root: Path,
    source_commit: str,
    lane: str,
    image_digest: str,
    execution_mode: str = "confirmatory",
) -> dict[str, object]:
    validate_authorization(authorization)
    validate_confirmatory_request(request)
    clean_commit = _validate_commit(source_commit)
    clean_image = _validate_image_digest(image_digest)
    clean_execution_mode = _validate_execution_mode(execution_mode)
    if authorization["execution_mode"] != clean_execution_mode:
        raise B2ConfirmatoryError("authorization execution mode mismatch")
    if lane not in B2_CONFIRMATORY_EXPECTED_LANES:
        raise B2ConfirmatoryError(f"unsupported confirmatory lane: {lane}")
    if authorization["project_source_commit"] != clean_commit:
        raise B2ConfirmatoryError("authorization source commit mismatch")
    if authorization["request_digest"] != canonical_json_digest(request):
        raise B2ConfirmatoryError("authorization request digest mismatch")
    if authorization["image_digest"] != clean_image:
        raise B2ConfirmatoryError("authorization image digest mismatch")
    if str(output_root.expanduser().resolve()) != authorization["output_root"]:
        raise B2ConfirmatoryError("authorization output root mismatch")
    if lane not in cast(Sequence[object], authorization["authorized_lanes"]):
        raise B2ConfirmatoryError(f"lane is not authorized: {lane}")
    _validate_output_root(
        output_root,
        minimum_free_bytes=cast(int, authorization["minimum_free_bytes"]),
        create=False,
    )
    emergency_stop = Path(str(authorization["emergency_stop_path"]))
    if emergency_stop.exists():
        raise B2ConfirmatoryError(f"emergency stop is active: {emergency_stop}")
    _validate_clean_project(project_root, clean_commit)
    _resolve_torch2pc(
        torch2pc_dir,
        expected_commit=str(authorization["torch2pc_commit"]),
    )
    _verify_registered_assets(request, project_root=project_root.expanduser().resolve())
    return {
        "campaign_id": B2_CONFIRMATORY_CAMPAIGN_ID,
        "authorization_verified": True,
        "authorization_token": authorization["authorization_token"],
        "execution_mode": clean_execution_mode,
        "lane": lane,
        "execution_permitted": True,
        "measurements_allowed": True,
        "evidence": False,
        "results_publication_permitted": False,
        "test_dataset_access": False,
    }


def validate_freeze_record(value: Mapping[str, object]) -> None:
    _require_equal(value, "schema_version", B2_CONFIRMATORY_AUTHORIZATION_SCHEMA_VERSION)
    _require_equal(value, "campaign_id", B2_CONFIRMATORY_CAMPAIGN_ID)
    _require_equal(value, "freeze_scope", B2_CONFIRMATORY_FREEZE_SCOPE)
    execution_mode = _validate_execution_mode(str(value.get("execution_mode", "")))
    _, _, authorized_triple_count = _execution_contract(execution_mode)
    _require_equal(value, "authorized_triple_count", authorized_triple_count)
    _require_equal(
        value,
        "authorized_comparison_count",
        B2_CONFIRMATORY_EXPECTED_COMPARISON_COUNT
        if execution_mode == "confirmatory"
        else B2_CONFIRMATORY_ENGINEERING_SMOKE_COMPARISON_COUNT,
    )
    _require_equal(value, "canonical_lanes", list(B2_CONFIRMATORY_EXPECTED_LANES))
    _validate_commit(_require_string(value, "project_source_commit"))
    _validate_image_digest(_require_string(value, "source_image_digest"))
    _require_digest(value, "request_digest")
    _require_digest(value, "request_file_sha256")
    _require_digest(value, "contract_digest")
    _require_digest(value, "resolved_config_digest")
    _validate_path_binding(value)
    _require_positive_int(value, "observed_free_bytes")
    _require_non_negative_int(value, "output_owner_uid")
    _require_non_negative_int(value, "output_owner_gid")
    _require_string(value, "request_path")
    _require_string(value, "torch2pc_path")
    _validate_commit(_require_string(value, "torch2pc_commit"))
    _require_string(value, "torch2pc_commit_verification")
    _require_digest(value, "torch2pc_source_sha256")
    _require_equal(value, "evidence", False)
    _require_equal(value, "full_confirmatory_campaign_complete", False)
    _require_equal(value, "results_publication_permitted", False)
    _require_equal(value, "test_dataset_access", False)
    supplied = _require_digest(value, "freeze_digest")
    unsigned = dict(value)
    unsigned.pop("freeze_digest", None)
    if _digest(unsigned) != supplied:
        raise B2ConfirmatoryError("freeze digest mismatch")


def validate_lane_preflight(value: Mapping[str, object]) -> None:
    _require_equal(value, "schema_version", B2_CONFIRMATORY_AUTHORIZATION_SCHEMA_VERSION)
    _require_equal(value, "campaign_id", B2_CONFIRMATORY_CAMPAIGN_ID)
    _require_equal(value, "preflight_scope", B2_CONFIRMATORY_PREFLIGHT_SCOPE)
    _validate_execution_mode(str(value.get("execution_mode", "")))
    lane = value.get("lane")
    if lane not in B2_CONFIRMATORY_EXPECTED_LANES:
        raise B2ConfirmatoryError("invalid lane preflight lane")
    _require_digest(value, "freeze_digest")
    _require_digest(value, "request_digest")
    _validate_commit(_require_string(value, "project_source_commit"))
    _validate_image_digest(_require_string(value, "image_digest"))
    _validate_path_binding(value, require_emergency_stop=False)
    probe = _runtime_probe_from_record(value.get("runtime"))
    _validate_runtime_for_lane(str(lane), probe)
    _require_equal(value, "evidence", False)
    _require_equal(value, "full_confirmatory_campaign_complete", False)
    _require_equal(value, "results_publication_permitted", False)
    _require_equal(value, "test_dataset_access", False)
    supplied = _require_digest(value, "lane_preflight_digest")
    unsigned = dict(value)
    unsigned.pop("lane_preflight_digest", None)
    if _digest(unsigned) != supplied:
        raise B2ConfirmatoryError("lane preflight digest mismatch")


def validate_authorization(value: Mapping[str, object]) -> None:
    _require_equal(value, "schema_version", B2_CONFIRMATORY_AUTHORIZATION_SCHEMA_VERSION)
    _require_equal(value, "campaign_id", B2_CONFIRMATORY_CAMPAIGN_ID)
    execution_mode = _validate_execution_mode(str(value.get("execution_mode", "")))
    authorization_scope, expected_acknowledgement, authorized_triple_count = _execution_contract(
        execution_mode
    )
    _require_equal(value, "authorization_scope", authorization_scope)
    _require_equal(value, "authorized_triple_count", authorized_triple_count)
    _require_equal(
        value,
        "authorized_comparison_count",
        B2_CONFIRMATORY_EXPECTED_COMPARISON_COUNT
        if execution_mode == "confirmatory"
        else B2_CONFIRMATORY_ENGINEERING_SMOKE_COMPARISON_COUNT,
    )
    _require_equal(value, "authorized_lanes", list(B2_CONFIRMATORY_EXPECTED_LANES))
    _require_equal(value, "execution_permitted", True)
    _require_equal(value, "measurements_allowed", True)
    _require_equal(value, "runtime_authorization", "issued")
    _require_equal(value, "evidence", False)
    _require_equal(value, "full_confirmatory_campaign_complete", False)
    _require_equal(value, "results_publication_permitted", False)
    _require_equal(value, "test_dataset_access", False)
    _require_digest(value, "freeze_digest")
    _require_digest(value, "request_digest")
    _validate_commit(_require_string(value, "project_source_commit"))
    _validate_commit(_require_string(value, "torch2pc_commit"))
    _validate_image_digest(_require_string(value, "image_digest"))
    _validate_path_binding(value)
    acknowledgement = value.get("operator_acknowledgement")
    if acknowledgement != expected_acknowledgement:
        raise B2ConfirmatoryError("authorization acknowledgement mismatch")
    raw_digests = value.get("lane_preflight_digests")
    if not isinstance(raw_digests, dict):
        raise B2ConfirmatoryError("lane preflight digest map is missing")
    if set(raw_digests) != set(B2_CONFIRMATORY_EXPECTED_LANES):
        raise B2ConfirmatoryError("lane preflight digest map is incomplete")
    lane_digests = {
        lane: _require_digest(cast(Mapping[str, object], raw_digests), lane)
        for lane in B2_CONFIRMATORY_EXPECTED_LANES
    }
    expected_token = _digest(
        {
            "domain": B2_CONFIRMATORY_AUTHORIZATION_DOMAIN,
            "freeze_digest": _require_digest(value, "freeze_digest"),
            "lane_preflight_digests": lane_digests,
            "operator_acknowledgement": acknowledgement,
            "execution_mode": execution_mode,
        }
    )
    token = _require_digest(value, "authorization_token")
    if token != expected_token:
        raise B2ConfirmatoryError("authorization token mismatch")
    supplied_digest = _require_digest(value, "authorization_digest")
    unsigned = dict(value)
    unsigned.pop("authorization_digest", None)
    if _digest(unsigned) != supplied_digest:
        raise B2ConfirmatoryError("authorization digest mismatch")


def _runtime_probe_from_record(value: object) -> B2ConfirmatoryRuntimeProbe:
    if not isinstance(value, Mapping):
        raise B2ConfirmatoryError("runtime probe is missing")
    record = cast(Mapping[str, object], value)
    hip_version = record.get("hip_version")
    if hip_version is not None and (
        not isinstance(hip_version, str) or not hip_version
    ):
        raise B2ConfirmatoryError("runtime hip_version must be null or non-empty")
    cuda_available = record.get("cuda_available")
    if not isinstance(cuda_available, bool):
        raise B2ConfirmatoryError("runtime cuda_available must be boolean")
    return B2ConfirmatoryRuntimeProbe(
        python_version=_require_string(record, "python_version"),
        pytorch_version=_require_string(record, "pytorch_version"),
        hip_version=hip_version,
        cuda_available=cuda_available,
        device_count=_require_non_negative_int(record, "device_count"),
        device_name=_require_string(record, "device_name"),
        platform=_require_string(record, "platform"),
        machine=_require_string(record, "machine"),
        effective_uid=_require_non_negative_int(record, "effective_uid"),
        effective_gid=_require_non_negative_int(record, "effective_gid"),
    )


def _validate_path_binding(
    value: Mapping[str, object],
    *,
    require_emergency_stop: bool = True,
) -> None:
    output_root = Path(_require_string(value, "output_root"))
    if not output_root.is_absolute():
        raise B2ConfirmatoryError("output_root must be absolute")
    minimum_free_bytes = _require_positive_int(value, "minimum_free_bytes")
    if "observed_free_bytes" in value:
        observed_free_bytes = _require_positive_int(value, "observed_free_bytes")
        if observed_free_bytes < minimum_free_bytes:
            raise B2ConfirmatoryError("observed_free_bytes is below minimum_free_bytes")
    if require_emergency_stop:
        emergency_stop = Path(_require_string(value, "emergency_stop_path"))
        if emergency_stop != output_root / "EMERGENCY-STOP":
            raise B2ConfirmatoryError("emergency_stop_path does not match output_root")


def _validate_execution_mode(value: str) -> str:
    if value not in B2_CONFIRMATORY_EXECUTION_MODES:
        raise B2ConfirmatoryError(f"invalid confirmatory execution mode: {value}")
    return value


def _execution_contract(execution_mode: str) -> tuple[str, str, int]:
    if execution_mode == "confirmatory":
        return (
            B2_CONFIRMATORY_AUTHORIZATION_SCOPE,
            B2_CONFIRMATORY_OPERATOR_ACKNOWLEDGEMENT,
            B2_CONFIRMATORY_EXPECTED_TRIPLE_COUNT,
        )
    if execution_mode == "engineering_smoke":
        return (
            B2_CONFIRMATORY_ENGINEERING_SMOKE_AUTHORIZATION_SCOPE,
            B2_CONFIRMATORY_ENGINEERING_SMOKE_ACKNOWLEDGEMENT,
            B2_CONFIRMATORY_ENGINEERING_SMOKE_TRIPLE_COUNT,
        )
    raise B2ConfirmatoryError(f"invalid confirmatory execution mode: {execution_mode}")


def _validate_freeze_binding(
    freeze_record: Mapping[str, object],
    request: Mapping[str, object],
    *,
    output_root: Path,
    source_commit: str,
    image_digest: str,
) -> None:
    if freeze_record["project_source_commit"] != source_commit:
        raise B2ConfirmatoryError("freeze source commit mismatch")
    if freeze_record["request_digest"] != canonical_json_digest(request):
        raise B2ConfirmatoryError("freeze request digest mismatch")
    if freeze_record["source_image_digest"] != image_digest:
        raise B2ConfirmatoryError("freeze image digest mismatch")
    if freeze_record["output_root"] != str(output_root.expanduser().resolve()):
        raise B2ConfirmatoryError("freeze output root mismatch")


def _validate_runtime_for_lane(lane: str, probe: B2ConfirmatoryRuntimeProbe) -> None:
    if lane == "cpu_float64":
        return
    if not probe.cuda_available or probe.device_count < 1:
        raise B2ConfirmatoryError("ROCm lane requires an available accelerator")
    if not probe.hip_version:
        raise B2ConfirmatoryError("ROCm lane requires a PyTorch HIP runtime")


def _validate_clean_project(project_root: Path, source_commit: str) -> Path:
    root = project_root.expanduser().resolve()
    observed = _run_git(root, "rev-parse", "HEAD").lower()
    if observed != source_commit:
        raise B2ConfirmatoryError(
            f"project HEAD mismatch: expected={source_commit}, observed={observed}"
        )
    status = _run_git(root, "status", "--porcelain=v1", "--untracked-files=normal")
    if status:
        raise B2ConfirmatoryError("project worktree must be clean")
    return root


def _validate_output_root(
    output_root: Path,
    *,
    minimum_free_bytes: int,
    create: bool,
) -> tuple[Path, dict[str, object]]:
    if minimum_free_bytes < 1:
        raise B2ConfirmatoryError("minimum_free_bytes must be positive")
    root = validated_temporary_output_root(output_root)
    if create:
        root.mkdir(parents=True, exist_ok=True)
    if not root.is_dir():
        raise B2ConfirmatoryError(f"output root is missing: {root}")
    free_bytes = shutil.disk_usage(root).free
    if free_bytes < minimum_free_bytes:
        raise B2ConfirmatoryError(
            f"insufficient free space: required={minimum_free_bytes}, observed={free_bytes}"
        )
    emergency_stop = root / "EMERGENCY-STOP"
    if emergency_stop.exists():
        raise B2ConfirmatoryError(f"emergency stop is active: {emergency_stop}")
    stat = root.stat()
    return root, {
        "observed_free_bytes": free_bytes,
        "output_owner_uid": stat.st_uid,
        "output_owner_gid": stat.st_gid,
        "emergency_stop_path": str(emergency_stop),
    }


def _resolve_torch2pc(torch2pc_dir: Path, *, expected_commit: str) -> dict[str, object]:
    root = torch2pc_dir.expanduser().resolve()
    source = root / "TorchSeq2PC.py"
    if not source.is_file():
        raise B2ConfirmatoryError(f"Torch2PC source is missing: {source}")
    completed = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    observed = completed.stdout.strip().lower()
    if completed.returncode == 0 and observed:
        if observed != expected_commit:
            raise B2ConfirmatoryError(
                f"Torch2PC commit mismatch: expected={expected_commit}, observed={observed}"
            )
        verification = "git_checkout"
    else:
        observed = expected_commit
        verification = "request_pinned_source_without_git_metadata"
    return {
        "torch2pc_path": str(root),
        "torch2pc_commit": observed,
        "torch2pc_commit_verification": verification,
        "torch2pc_source_sha256": sha256_file(source),
    }


def _verify_registered_assets(request: Mapping[str, object], *, project_root: Path) -> None:
    checkpoints = cast(Mapping[str, object], request["checkpoints"])
    batches = cast(Mapping[str, object], request["validation_batches"])
    assets: list[Mapping[str, object]] = []
    for group in (checkpoints, batches):
        for raw in group.values():
            if not isinstance(raw, dict):
                raise B2ConfirmatoryError("registered asset must be an object")
            assets.append(cast(Mapping[str, object], raw))
    for key in (
        "b1_confirmatory_decision",
        "b1_admission",
        "b1_frozen_request",
        "b1_batch_registry",
        "b2_confirmatory_contract",
        "b2_candidate_contract",
        "b2_implementation_contract",
        "b2_harness_contract",
    ):
        raw = request.get(key)
        if not isinstance(raw, dict):
            raise B2ConfirmatoryError(f"registered asset is missing: {key}")
        assets.append(cast(Mapping[str, object], raw))
    for asset in assets:
        registered = Path(str(asset["path"]))
        path = registered if registered.is_absolute() else project_root / registered
        resolved = path.expanduser().resolve()
        try:
            resolved.relative_to(project_root)
        except ValueError as error:
            raise B2ConfirmatoryError(
                f"registered asset escapes project root: {registered}"
            ) from error
        if not resolved.is_file():
            raise B2ConfirmatoryError(f"registered asset is missing: {resolved}")
        observed = sha256_file(resolved)
        if observed != asset["sha256"]:
            raise B2ConfirmatoryError(f"registered asset digest mismatch: {resolved}")


def _run_git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip()
        raise B2ConfirmatoryError(f"git {' '.join(args)} failed: {message}")
    return completed.stdout.strip()


def _validate_commit(value: str) -> str:
    normalized = value.strip().lower()
    if not _COMMIT_PATTERN.fullmatch(normalized):
        raise B2ConfirmatoryError("source commit must be 40 lowercase hex characters")
    return normalized


def _validate_image_digest(value: str) -> str:
    normalized = value.strip().lower()
    if not _IMAGE_PATTERN.fullmatch(normalized):
        raise B2ConfirmatoryError("image digest must be sha256:<64 lowercase hex>")
    return normalized


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _require_equal(mapping: Mapping[str, object], key: str, expected: object) -> None:
    observed = mapping.get(key)
    if observed != expected:
        raise B2ConfirmatoryError(f"{key}: expected {expected!r}, observed {observed!r}")


def _require_digest(mapping: Mapping[str, object], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise B2ConfirmatoryError(f"{key} must be a lowercase SHA-256 digest")
    return value


def _require_string(mapping: Mapping[str, object], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise B2ConfirmatoryError(f"{key} must be a non-empty string")
    return value


def _require_positive_int(mapping: Mapping[str, object], key: str) -> int:
    value = mapping.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise B2ConfirmatoryError(f"{key} must be a positive integer")
    return value


def _require_non_negative_int(mapping: Mapping[str, object], key: str) -> int:
    value = mapping.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise B2ConfirmatoryError(f"{key} must be a non-negative integer")
    return value
