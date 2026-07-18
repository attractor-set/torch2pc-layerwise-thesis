"""Freeze and verify runtime authorization for matched Stage 3B B0/B1/B2 profiling.

The contract in this module is intentionally separate from the historical
96-cell B0 authorization contract.  It authorizes only the frozen 288-cell
matched matrix, only on the ROCm/float32 canonical lane, and remains
non-evidence until a later sealing step validates completed raw records.
"""

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
    STAGE3B_CAMPAIGN_ID,
    STAGE3B_EXECUTION_SCHEMA_VERSION,
    Stage3BExecutionError,
    validate_manifest,
    validated_temporary_output_root,
)
from torch2pc_thesis.stage3b_matched_profiling import (
    MATCHED_PROFILING_CANDIDATES,
    MATCHED_PROFILING_EXPECTED_CANDIDATE_COUNT,
    MATCHED_PROFILING_EXPECTED_CELL_COUNT,
    validate_matched_manifest,
    validate_matched_request,
)
from torch2pc_thesis.stage3b_matched_runner import (
    CANDIDATE_ADAPTERS,
    MATCHED_RUNNER_EXPECTED_BLOCK_COUNT,
    MATCHED_RUNNER_EXPECTED_CELLS_PER_BLOCK,
    MATCHED_RUNNER_STATE_RESET_POLICY,
    validate_runner_inputs,
    verify_candidate_dispatch,
)

MATCHED_AUTHORIZATION_SCHEMA_VERSION: Final[int] = 1
MATCHED_AUTHORIZATION_SCOPE: Final[str] = (
    "stage3b_b1_b2_matched_rocm_canonical_campaign"
)
MATCHED_PROJECT_FREEZE_SCOPE: Final[str] = (
    "stage3b_b1_b2_matched_project_freeze"
)
MATCHED_LANE_PREFLIGHT_SCOPE: Final[str] = (
    "stage3b_b1_b2_matched_lane_preflight"
)
MATCHED_AUTHORIZATION_DOMAIN: Final[str] = (
    "torch2pc-stage3b-b1-b2-matched-rocm-authorization-v1"
)
MATCHED_OPERATOR_ACKNOWLEDGEMENT: Final[str] = (
    "AUTHORIZE_STAGE3B_B1_B2_MATCHED_ROCM_FLOAT32_CANONICAL_288_CELL_CAMPAIGN"
)
MATCHED_DEFAULT_MINIMUM_FREE_BYTES: Final[int] = 20 * 1024**3
MATCHED_CANONICAL_LANES: Final[tuple[tuple[str, str], ...]] = (
    ("rocm", "float32"),
)
MATCHED_AUTHORIZED_CELL_COUNT: Final[int] = MATCHED_PROFILING_EXPECTED_CELL_COUNT
# The matched executor verifies authorization, reconstructs identical block
# state per candidate, and isolates every cell in a fresh Python process.
MATCHED_EXECUTION_RUNNER_READY: Final[bool] = True
MATCHED_DISPATCH_SYMBOLS: Final[tuple[str, ...]] = tuple(
    f"{CANDIDATE_ADAPTERS[candidate_id].module_name}."
    f"{CANDIDATE_ADAPTERS[candidate_id].loader_name}"
    for candidate_id in MATCHED_PROFILING_CANDIDATES
)

_CLEAN_COMMIT_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[0-9a-f]{40}$")
_SHA256_IDENTIFIER_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^sha256:[0-9a-f]{64}$"
)


@dataclass(frozen=True)
class MatchedRuntimeProbe:
    """Stable runtime identity for the authorized ROCm/float32 lane."""

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


def _require_int(value: object, *, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise Stage3BExecutionError(f"{field} must be an integer")
    return value


def _validated_commit(source_commit: str) -> str:
    normalized = source_commit.strip().lower()
    if not _CLEAN_COMMIT_PATTERN.fullmatch(normalized):
        raise Stage3BExecutionError(
            "matched authorization requires an exact 40-character source commit"
        )
    return normalized


def _validated_image_digest(image_digest: str) -> str:
    normalized = image_digest.strip().lower()
    if not _SHA256_IDENTIFIER_PATTERN.fullmatch(normalized):
        raise Stage3BExecutionError(
            "matched authorization requires an exact sha256:<64 hex> image digest"
        )
    return normalized


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


def _validate_project_source(project_root: Path, *, source_commit: str) -> Path:
    clean_commit = _validated_commit(source_commit)
    resolved = project_root.expanduser().resolve()
    observed = _run_git(resolved, "rev-parse", "HEAD").lower()
    if observed != clean_commit:
        raise Stage3BExecutionError(
            "project HEAD differs from the requested matched freeze commit: "
            f"expected={clean_commit}, observed={observed}"
        )
    status = _run_git(
        resolved,
        "status",
        "--porcelain=v1",
        "--untracked-files=normal",
    )
    if status:
        raise Stage3BExecutionError(
            "project worktree must be clean before matched authorization"
        )
    return resolved


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
        raise Stage3BExecutionError(
            f"matched authorization output root is missing: {resolved}"
        )
    stat = resolved.stat()
    if not os.access(resolved, os.R_OK | os.W_OK | os.X_OK):
        raise Stage3BExecutionError(
            "matched authorization output root must be readable, writable and searchable"
        )
    free_bytes = shutil.disk_usage(resolved).free
    if free_bytes < minimum_free_bytes:
        raise Stage3BExecutionError(
            "matched authorization output root has insufficient free space: "
            f"required={minimum_free_bytes}, observed={free_bytes}"
        )
    emergency_stop = resolved / "EMERGENCY-STOP"
    if emergency_stop.exists():
        raise Stage3BExecutionError(
            f"matched campaign emergency stop is active: {emergency_stop}"
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


def _require_mapping(value: object, *, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise Stage3BExecutionError(f"{field} must be an object")
    for key in value:
        if not isinstance(key, str):
            raise Stage3BExecutionError(f"{field} contains a non-string key")
    return cast(Mapping[str, object], value)


def _candidate_adapter_contract() -> dict[str, dict[str, str]]:
    return {
        candidate_id: spec.to_record()
        for candidate_id, spec in sorted(CANDIDATE_ADAPTERS.items())
    }


def _candidate_dispatch_contract() -> dict[str, object]:
    adapters = _candidate_adapter_contract()
    return {
        "state_reset_policy": MATCHED_RUNNER_STATE_RESET_POLICY,
        "expected_block_count": MATCHED_RUNNER_EXPECTED_BLOCK_COUNT,
        "expected_cells_per_block": MATCHED_RUNNER_EXPECTED_CELLS_PER_BLOCK,
        "candidate_adapters": adapters,
        "candidate_adapter_digest": _digest(adapters),
    }


def _validate_input_linkage(
    matched_manifest: Mapping[str, object],
    request: Mapping[str, object],
    base_manifest: Mapping[str, object],
    *,
    base_manifest_path: Path,
) -> tuple[Mapping[str, object], Mapping[str, object]]:
    validate_matched_manifest(matched_manifest)
    validate_matched_request(request)
    validate_manifest(base_manifest)
    cells = validate_runner_inputs(matched_manifest, request)
    if len(cells) != MATCHED_AUTHORIZED_CELL_COUNT:
        raise Stage3BExecutionError("matched authorization requires exactly 288 cells")
    source_digest = str(base_manifest["manifest_digest"])
    if matched_manifest.get("source_manifest_digest") != source_digest:
        raise Stage3BExecutionError(
            "matched manifest source digest differs from the execution manifest"
        )
    source_artifacts = _require_mapping(
        request.get("source_artifacts"),
        field="matched request source_artifacts",
    )
    execution_manifest = _require_mapping(
        source_artifacts.get("execution_manifest"),
        field="matched request execution_manifest",
    )
    if execution_manifest.get("manifest_digest") != source_digest:
        raise Stage3BExecutionError(
            "matched request execution-manifest digest differs from the supplied base"
        )
    observed_sha256 = _sha256_file(base_manifest_path)
    if execution_manifest.get("sha256") != observed_sha256:
        raise Stage3BExecutionError(
            "matched request execution-manifest sha256 differs from the supplied file"
        )
    matched_record = _require_mapping(
        source_artifacts.get("matched_manifest"),
        field="matched request matched_manifest",
    )
    if matched_record.get("manifest_digest") != matched_manifest.get(
        "manifest_digest"
    ):
        raise Stage3BExecutionError(
            "matched request does not reference the supplied matched manifest"
        )
    if request.get("admitted_candidates") != list(MATCHED_PROFILING_CANDIDATES):
        raise Stage3BExecutionError("matched admitted candidate order changed")
    return source_artifacts, execution_manifest


def _protocol_record(matched_manifest: Mapping[str, object]) -> dict[str, object]:
    raw = _require_mapping(
        matched_manifest.get("protocol"),
        field="matched manifest protocol",
    )
    return dict(raw)


def _candidate_counts(matched_manifest: Mapping[str, object]) -> dict[str, int]:
    raw = _require_mapping(
        matched_manifest.get("candidate_counts"),
        field="matched manifest candidate_counts",
    )
    expected = {
        candidate_id: MATCHED_PROFILING_EXPECTED_CANDIDATE_COUNT
        for candidate_id in MATCHED_PROFILING_CANDIDATES
    }
    observed = {
        candidate_id: _require_int(raw.get(candidate_id), field=candidate_id)
        for candidate_id in MATCHED_PROFILING_CANDIDATES
    }
    if observed != expected:
        raise Stage3BExecutionError("matched candidate counts differ from the contract")
    return observed


def _freeze_stable_projection(record: Mapping[str, object]) -> dict[str, object]:
    keys = (
        "schema_version",
        "campaign_id",
        "freeze_scope",
        "evidence",
        "full_stage3b_campaign_complete",
        "results_publication_permitted",
        "test_dataset_access",
        "project_source_commit",
        "matched_manifest_digest",
        "opening_request_digest",
        "source_manifest_digest",
        "source_manifest_sha256",
        "admitted_candidates",
        "candidate_counts",
        "authorized_cell_count",
        "canonical_execution_count",
        "canonical_protocol",
        "candidate_dispatch_contract",
        "candidate_dispatch_contract_digest",
        "torch2pc_commit",
        "torch2pc_source_sha256",
        "output_root",
        "minimum_free_bytes",
        "emergency_stop_path",
        "canonical_lanes",
    )
    return {key: record[key] for key in keys}


def freeze_matched_project_environment(
    matched_manifest: Mapping[str, object],
    request: Mapping[str, object],
    base_manifest: Mapping[str, object],
    *,
    base_manifest_path: Path,
    project_root: Path,
    torch2pc_dir: Path,
    output_root: Path,
    source_commit: str,
    minimum_free_bytes: int = MATCHED_DEFAULT_MINIMUM_FREE_BYTES,
) -> dict[str, object]:
    """Freeze the clean source, matched artifacts, Torch2PC, and output policy."""

    _validate_input_linkage(
        matched_manifest,
        request,
        base_manifest,
        base_manifest_path=base_manifest_path,
    )
    clean_commit = _validated_commit(source_commit)
    resolved_project = _validate_project_source(
        project_root,
        source_commit=clean_commit,
    )
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
            "matched project freeze output root must be owned by the host operator"
        )
    expected_torch2pc_commit = str(base_manifest["torch2pc_source_commit"])
    torch2pc = _resolve_torch2pc_provenance(
        torch2pc_dir,
        expected_commit=expected_torch2pc_commit,
    )
    candidate_dispatch_contract = _candidate_dispatch_contract()
    stable: dict[str, object] = {
        "schema_version": MATCHED_AUTHORIZATION_SCHEMA_VERSION,
        "campaign_id": STAGE3B_CAMPAIGN_ID,
        "freeze_scope": MATCHED_PROJECT_FREEZE_SCOPE,
        "evidence": False,
        "full_stage3b_campaign_complete": False,
        "results_publication_permitted": False,
        "test_dataset_access": False,
        "project_source_commit": clean_commit,
        "matched_manifest_digest": str(matched_manifest["manifest_digest"]),
        "opening_request_digest": str(request["request_digest"]),
        "source_manifest_digest": str(base_manifest["manifest_digest"]),
        "source_manifest_sha256": _sha256_file(base_manifest_path),
        "admitted_candidates": list(MATCHED_PROFILING_CANDIDATES),
        "candidate_counts": _candidate_counts(matched_manifest),
        "authorized_cell_count": MATCHED_AUTHORIZED_CELL_COUNT,
        "canonical_execution_count": MATCHED_AUTHORIZED_CELL_COUNT,
        "canonical_protocol": _protocol_record(matched_manifest),
        "candidate_dispatch_contract": candidate_dispatch_contract,
        "candidate_dispatch_contract_digest": _digest(candidate_dispatch_contract),
        "torch2pc_commit": str(torch2pc["torch2pc_commit"]),
        "torch2pc_source_sha256": str(torch2pc["torch2pc_source_sha256"]),
        "output_root": str(resolved_output),
        "minimum_free_bytes": minimum_free_bytes,
        "emergency_stop_path": str(output_observation["emergency_stop_path"]),
        "canonical_lanes": [
            {"device": device, "dtype": dtype}
            for device, dtype in MATCHED_CANONICAL_LANES
        ],
    }
    return {
        **stable,
        "freeze_digest": _digest(stable),
        "created_at": _utc_now(),
        "project_root": str(resolved_project),
        "project_commit_verification": "git_clean_exact_head",
        "base_manifest_path": str(base_manifest_path.expanduser().resolve()),
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


def validate_matched_project_freeze(record: Mapping[str, object]) -> None:
    """Validate a matched project freeze and its stable digest."""

    if record.get("schema_version") != MATCHED_AUTHORIZATION_SCHEMA_VERSION:
        raise Stage3BExecutionError("unsupported matched authorization schema")
    if record.get("campaign_id") != STAGE3B_CAMPAIGN_ID:
        raise Stage3BExecutionError("unexpected matched authorization campaign")
    if record.get("freeze_scope") != MATCHED_PROJECT_FREEZE_SCOPE:
        raise Stage3BExecutionError("unexpected matched project freeze scope")
    if record.get("evidence") is not False:
        raise Stage3BExecutionError("matched project freeze must remain non-evidence")
    if record.get("full_stage3b_campaign_complete") is not False:
        raise Stage3BExecutionError("matched freeze cannot complete Stage 3B")
    if record.get("results_publication_permitted") is not False:
        raise Stage3BExecutionError("matched freeze cannot permit publication")
    if record.get("test_dataset_access") is not False:
        raise Stage3BExecutionError("matched freeze cannot access test data")
    if record.get("admitted_candidates") != list(MATCHED_PROFILING_CANDIDATES):
        raise Stage3BExecutionError("matched freeze candidate order changed")
    if record.get("authorized_cell_count") != MATCHED_AUTHORIZED_CELL_COUNT:
        raise Stage3BExecutionError("matched freeze cell count must remain 288")
    if record.get("canonical_execution_count") != MATCHED_AUTHORIZED_CELL_COUNT:
        raise Stage3BExecutionError("matched canonical execution count must remain 288")
    expected_counts = {
        candidate_id: MATCHED_PROFILING_EXPECTED_CANDIDATE_COUNT
        for candidate_id in MATCHED_PROFILING_CANDIDATES
    }
    if record.get("candidate_counts") != expected_counts:
        raise Stage3BExecutionError("matched freeze candidate counts changed")
    candidate_dispatch_contract = _candidate_dispatch_contract()
    if record.get("candidate_dispatch_contract") != candidate_dispatch_contract:
        raise Stage3BExecutionError("matched freeze runner contract changed")
    if record.get("candidate_dispatch_contract_digest") != _digest(candidate_dispatch_contract):
        raise Stage3BExecutionError("matched freeze runner digest changed")
    expected_lanes = [
        {"device": device, "dtype": dtype}
        for device, dtype in MATCHED_CANONICAL_LANES
    ]
    if record.get("canonical_lanes") != expected_lanes:
        raise Stage3BExecutionError("matched freeze canonical lane changed")
    _validated_commit(str(record.get("project_source_commit", "")))
    supplied = record.get("freeze_digest")
    if not isinstance(supplied, str) or supplied != _digest(
        _freeze_stable_projection(record)
    ):
        raise Stage3BExecutionError("matched project freeze digest does not match")


def _default_runtime_probe() -> MatchedRuntimeProbe:
    cuda_available = torch.cuda.is_available()
    device_count = torch.cuda.device_count() if cuda_available else 0
    hip_version = getattr(torch.version, "hip", None)
    if not cuda_available or not hip_version or device_count < 1:
        raise Stage3BExecutionError(
            "matched ROCm preflight requires an available HIP device"
        )
    return MatchedRuntimeProbe(
        python_version=sys.version,
        pytorch_version=torch.__version__,
        hip_version=hip_version,
        cuda_available=cuda_available,
        device_count=device_count,
        device_name=torch.cuda.get_device_name(0),
        platform=platform.platform(),
        machine=platform.machine(),
        effective_uid=os.geteuid(),
        effective_gid=os.getegid(),
    )


def _preflight_stable_projection(record: Mapping[str, object]) -> dict[str, object]:
    keys = (
        "schema_version",
        "campaign_id",
        "preflight_scope",
        "evidence",
        "full_stage3b_campaign_complete",
        "results_publication_permitted",
        "test_dataset_access",
        "freeze_digest",
        "device",
        "dtype",
        "lane_role",
        "image_digest",
        "runtime",
        "dispatch_verified_symbols",
        "candidate_dispatch_contract_digest",
        "output_root",
        "minimum_free_bytes",
        "output_owner_uid",
        "output_owner_gid",
        "emergency_stop_path",
    )
    return {key: record[key] for key in keys}


def capture_matched_lane_preflight(
    freeze_record: Mapping[str, object],
    matched_manifest: Mapping[str, object],
    request: Mapping[str, object],
    base_manifest: Mapping[str, object],
    *,
    base_manifest_path: Path,
    project_root: Path,
    torch2pc_dir: Path,
    source_commit: str,
    image_digest: str,
    probe: MatchedRuntimeProbe | None = None,
    dispatch_symbols: Sequence[str] | None = None,
) -> dict[str, object]:
    """Capture the sole ROCm/float32 runtime fingerprint without measurements."""

    validate_matched_project_freeze(freeze_record)
    _validate_input_linkage(
        matched_manifest,
        request,
        base_manifest,
        base_manifest_path=base_manifest_path,
    )
    clean_commit = _validated_commit(source_commit)
    _validate_project_source(project_root, source_commit=clean_commit)
    if clean_commit != freeze_record.get("project_source_commit"):
        raise Stage3BExecutionError("matched lane source commit differs from freeze")
    expected_links = {
        "matched_manifest_digest": matched_manifest.get("manifest_digest"),
        "opening_request_digest": request.get("request_digest"),
        "source_manifest_digest": base_manifest.get("manifest_digest"),
        "source_manifest_sha256": _sha256_file(base_manifest_path),
    }
    for key, expected in expected_links.items():
        if freeze_record.get(key) != expected:
            raise Stage3BExecutionError(f"matched lane {key} differs from freeze")
    torch2pc = _resolve_torch2pc_provenance(
        torch2pc_dir,
        expected_commit=str(freeze_record["torch2pc_commit"]),
    )
    if torch2pc["torch2pc_source_sha256"] != freeze_record.get(
        "torch2pc_source_sha256"
    ):
        raise Stage3BExecutionError("matched lane Torch2PC source differs from freeze")
    normalized_image = _validated_image_digest(image_digest)
    minimum_free_bytes = _require_int(
        freeze_record.get("minimum_free_bytes"),
        field="minimum_free_bytes",
    )
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
    expected_owner = (
        _require_int(
            freeze_record.get("output_owner_uid"),
            field="freeze output_owner_uid",
        ),
        _require_int(
            freeze_record.get("output_owner_gid"),
            field="freeze output_owner_gid",
        ),
    )
    if (observed_owner_uid, observed_owner_gid) != expected_owner:
        raise Stage3BExecutionError("matched output ownership differs from freeze")
    runtime = probe or _default_runtime_probe()
    if (
        not runtime.cuda_available
        or not runtime.hip_version
        or runtime.device_count < 1
        or runtime.device_name == "cpu"
    ):
        raise Stage3BExecutionError(
            "matched ROCm preflight requires an available HIP device"
        )
    verified = tuple(dispatch_symbols or verify_candidate_dispatch())
    if verified != MATCHED_DISPATCH_SYMBOLS:
        raise Stage3BExecutionError(
            "matched candidate dispatch differs from the admitted candidate order"
        )
    stable: dict[str, object] = {
        "schema_version": MATCHED_AUTHORIZATION_SCHEMA_VERSION,
        "campaign_id": STAGE3B_CAMPAIGN_ID,
        "preflight_scope": MATCHED_LANE_PREFLIGHT_SCOPE,
        "evidence": False,
        "full_stage3b_campaign_complete": False,
        "results_publication_permitted": False,
        "test_dataset_access": False,
        "freeze_digest": str(freeze_record["freeze_digest"]),
        "device": "rocm",
        "dtype": "float32",
        "lane_role": "canonical",
        "image_digest": normalized_image,
        "runtime": runtime.to_record(),
        "dispatch_verified_symbols": list(verified),
        "candidate_dispatch_contract_digest": str(freeze_record["candidate_dispatch_contract_digest"]),
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


def validate_matched_lane_preflight(record: Mapping[str, object]) -> None:
    """Validate the sole matched ROCm/float32 lane preflight."""

    if record.get("schema_version") != MATCHED_AUTHORIZATION_SCHEMA_VERSION:
        raise Stage3BExecutionError("unsupported matched preflight schema")
    if record.get("campaign_id") != STAGE3B_CAMPAIGN_ID:
        raise Stage3BExecutionError("unexpected matched preflight campaign")
    if record.get("preflight_scope") != MATCHED_LANE_PREFLIGHT_SCOPE:
        raise Stage3BExecutionError("unexpected matched preflight scope")
    if record.get("evidence") is not False:
        raise Stage3BExecutionError("matched preflight must remain non-evidence")
    if record.get("full_stage3b_campaign_complete") is not False:
        raise Stage3BExecutionError("matched preflight cannot complete Stage 3B")
    if record.get("results_publication_permitted") is not False:
        raise Stage3BExecutionError("matched preflight cannot permit publication")
    if record.get("test_dataset_access") is not False:
        raise Stage3BExecutionError("matched preflight cannot access test data")
    if (record.get("device"), record.get("dtype")) != ("rocm", "float32"):
        raise Stage3BExecutionError("matched preflight must be ROCm/float32")
    if record.get("lane_role") != "canonical":
        raise Stage3BExecutionError("matched preflight lane role changed")
    _validated_image_digest(str(record.get("image_digest", "")))
    if record.get("dispatch_verified_symbols") != list(MATCHED_DISPATCH_SYMBOLS):
        raise Stage3BExecutionError("matched preflight dispatch symbols changed")
    if record.get("candidate_dispatch_contract_digest") != _digest(_candidate_dispatch_contract()):
        raise Stage3BExecutionError("matched preflight runner digest changed")
    supplied = record.get("lane_preflight_digest")
    if not isinstance(supplied, str) or supplied != _digest(
        _preflight_stable_projection(record)
    ):
        raise Stage3BExecutionError("matched preflight digest does not match")


def _authorization_payload(record: Mapping[str, object]) -> dict[str, object]:
    return {
        key: value
        for key, value in record.items()
        if key not in {"authorization_token", "authorization_digest"}
    }


def _authorization_token(payload: Mapping[str, object]) -> str:
    return _digest(
        {
            "domain": MATCHED_AUTHORIZATION_DOMAIN,
            "authorization": dict(payload),
        }
    )


def issue_matched_campaign_authorization(
    freeze_record: Mapping[str, object],
    lane_preflight: Mapping[str, object],
    *,
    operator_acknowledgement: str,
    execution_runner_ready: bool = MATCHED_EXECUTION_RUNNER_READY,
) -> dict[str, object]:
    """Issue a non-evidence authorization for exactly 288 matched executions."""

    validate_matched_project_freeze(freeze_record)
    validate_matched_lane_preflight(lane_preflight)
    if not execution_runner_ready:
        raise Stage3BExecutionError(
            "matched executable runner is not ready; authorization remains blocked"
        )
    if operator_acknowledgement != MATCHED_OPERATOR_ACKNOWLEDGEMENT:
        raise Stage3BExecutionError("matched operator acknowledgement does not match")
    if lane_preflight.get("freeze_digest") != freeze_record.get("freeze_digest"):
        raise Stage3BExecutionError("matched preflight uses a different freeze")
    payload: dict[str, object] = {
        "schema_version": MATCHED_AUTHORIZATION_SCHEMA_VERSION,
        "campaign_id": STAGE3B_CAMPAIGN_ID,
        "authorization_scope": MATCHED_AUTHORIZATION_SCOPE,
        "runtime_authorization": "issued",
        "measurements_allowed": True,
        "execution_permitted": True,
        "evidence": False,
        "full_stage3b_campaign_complete": False,
        "results_publication_permitted": False,
        "test_dataset_access": False,
        "project_source_commit": str(freeze_record["project_source_commit"]),
        "matched_manifest_digest": str(freeze_record["matched_manifest_digest"]),
        "opening_request_digest": str(freeze_record["opening_request_digest"]),
        "source_manifest_digest": str(freeze_record["source_manifest_digest"]),
        "source_manifest_sha256": str(freeze_record["source_manifest_sha256"]),
        "admitted_candidates": list(MATCHED_PROFILING_CANDIDATES),
        "candidate_counts": dict(
            cast(Mapping[str, int], freeze_record["candidate_counts"])
        ),
        "authorized_cell_count": MATCHED_AUTHORIZED_CELL_COUNT,
        "canonical_execution_count": MATCHED_AUTHORIZED_CELL_COUNT,
        "canonical_protocol": dict(
            cast(Mapping[str, object], freeze_record["canonical_protocol"])
        ),
        "candidate_dispatch_contract": dict(
            cast(Mapping[str, object], freeze_record["candidate_dispatch_contract"])
        ),
        "candidate_dispatch_contract_digest": str(freeze_record["candidate_dispatch_contract_digest"]),
        "torch2pc_commit": str(freeze_record["torch2pc_commit"]),
        "torch2pc_source_sha256": str(freeze_record["torch2pc_source_sha256"]),
        "canonical_lanes": [
            {"device": device, "dtype": dtype}
            for device, dtype in MATCHED_CANONICAL_LANES
        ],
        "canonical_lane_preflight": dict(lane_preflight),
        "output_root": str(freeze_record["output_root"]),
        "minimum_free_bytes": _require_int(
            freeze_record.get("minimum_free_bytes"),
            field="minimum_free_bytes",
        ),
        "emergency_stop_path": str(freeze_record["emergency_stop_path"]),
        "resume_policy": {
            "preserve_all_attempts": True,
            "silent_overwrite": False,
            "matching_success_is_terminal": True,
            "failed_and_interrupted_attempts_require_explicit_resume": True,
        },
        "freeze_record": dict(freeze_record),
        "issued_at": _utc_now(),
    }
    token = _authorization_token(payload)
    return {
        **payload,
        "authorization_token": token,
        "authorization_digest": token,
    }


def validate_matched_campaign_authorization(record: Mapping[str, object]) -> None:
    """Validate a complete tamper-evident matched authorization envelope."""

    if record.get("schema_version") != MATCHED_AUTHORIZATION_SCHEMA_VERSION:
        raise Stage3BExecutionError("unsupported matched authorization schema")
    if record.get("campaign_id") != STAGE3B_CAMPAIGN_ID:
        raise Stage3BExecutionError("unexpected matched authorization campaign")
    if record.get("authorization_scope") != MATCHED_AUTHORIZATION_SCOPE:
        raise Stage3BExecutionError("unexpected matched authorization scope")
    if record.get("runtime_authorization") != "issued":
        raise Stage3BExecutionError("matched runtime authorization is not issued")
    if record.get("measurements_allowed") is not True:
        raise Stage3BExecutionError("matched authorization does not permit measurements")
    if record.get("execution_permitted") is not True:
        raise Stage3BExecutionError("matched execution is not permitted")
    if record.get("evidence") is not False:
        raise Stage3BExecutionError("matched authorization must remain non-evidence")
    if record.get("full_stage3b_campaign_complete") is not False:
        raise Stage3BExecutionError("matched authorization cannot complete Stage 3B")
    if record.get("results_publication_permitted") is not False:
        raise Stage3BExecutionError("matched authorization cannot permit publication")
    if record.get("test_dataset_access") is not False:
        raise Stage3BExecutionError("matched authorization cannot access test data")
    freeze_record = _require_mapping(
        record.get("freeze_record"),
        field="matched authorization freeze_record",
    )
    validate_matched_project_freeze(freeze_record)
    expected_from_freeze = {
        "project_source_commit": freeze_record.get("project_source_commit"),
        "matched_manifest_digest": freeze_record.get("matched_manifest_digest"),
        "opening_request_digest": freeze_record.get("opening_request_digest"),
        "source_manifest_digest": freeze_record.get("source_manifest_digest"),
        "source_manifest_sha256": freeze_record.get("source_manifest_sha256"),
        "candidate_counts": freeze_record.get("candidate_counts"),
        "canonical_protocol": freeze_record.get("canonical_protocol"),
        "candidate_dispatch_contract": freeze_record.get("candidate_dispatch_contract"),
        "candidate_dispatch_contract_digest": freeze_record.get("candidate_dispatch_contract_digest"),
        "torch2pc_commit": freeze_record.get("torch2pc_commit"),
        "torch2pc_source_sha256": freeze_record.get("torch2pc_source_sha256"),
        "output_root": freeze_record.get("output_root"),
        "minimum_free_bytes": freeze_record.get("minimum_free_bytes"),
    }
    for key, expected in expected_from_freeze.items():
        if record.get(key) != expected:
            raise Stage3BExecutionError(
                f"matched authorization {key} differs from freeze"
            )
    if record.get("admitted_candidates") != list(MATCHED_PROFILING_CANDIDATES):
        raise Stage3BExecutionError("matched authorization candidates changed")
    if record.get("authorized_cell_count") != MATCHED_AUTHORIZED_CELL_COUNT:
        raise Stage3BExecutionError("matched authorization cell count must remain 288")
    if record.get("canonical_execution_count") != MATCHED_AUTHORIZED_CELL_COUNT:
        raise Stage3BExecutionError(
            "matched authorization canonical execution count must remain 288"
        )
    expected_lanes = [
        {"device": device, "dtype": dtype}
        for device, dtype in MATCHED_CANONICAL_LANES
    ]
    if record.get("canonical_lanes") != expected_lanes:
        raise Stage3BExecutionError("matched authorization canonical lane changed")
    lane_preflight = _require_mapping(
        record.get("canonical_lane_preflight"),
        field="matched authorization canonical_lane_preflight",
    )
    validate_matched_lane_preflight(lane_preflight)
    if lane_preflight.get("freeze_digest") != freeze_record.get("freeze_digest"):
        raise Stage3BExecutionError("matched authorization preflight freeze changed")
    supplied = record.get("authorization_token")
    expected = _authorization_token(_authorization_payload(record))
    if not isinstance(supplied, str) or supplied != expected:
        raise Stage3BExecutionError("matched authorization token does not match")
    if record.get("authorization_digest") != supplied:
        raise Stage3BExecutionError("matched authorization digest differs from token")


def verify_matched_authorization_for_lane(
    authorization: Mapping[str, object],
    matched_manifest: Mapping[str, object],
    request: Mapping[str, object],
    base_manifest: Mapping[str, object],
    *,
    base_manifest_path: Path,
    project_root: Path,
    torch2pc_dir: Path,
    output_root: Path,
    source_commit: str,
    image_digest: str,
    probe: MatchedRuntimeProbe | None = None,
    dispatch_symbols: Sequence[str] | None = None,
) -> dict[str, object]:
    """Reproduce and verify the authorized ROCm/float32 fingerprint."""

    validate_matched_campaign_authorization(authorization)
    clean_commit = _validated_commit(source_commit)
    if clean_commit != authorization.get("project_source_commit"):
        raise Stage3BExecutionError("runtime source commit differs from authorization")
    resolved_output = validated_temporary_output_root(output_root)
    if str(resolved_output) != authorization.get("output_root"):
        raise Stage3BExecutionError("runtime output root differs from authorization")
    freeze_record = cast(Mapping[str, object], authorization["freeze_record"])
    current = capture_matched_lane_preflight(
        freeze_record,
        matched_manifest,
        request,
        base_manifest,
        base_manifest_path=base_manifest_path,
        project_root=project_root,
        torch2pc_dir=torch2pc_dir,
        source_commit=clean_commit,
        image_digest=image_digest,
        probe=probe,
        dispatch_symbols=dispatch_symbols,
    )
    authorized = _require_mapping(
        authorization.get("canonical_lane_preflight"),
        field="matched authorization canonical_lane_preflight",
    )
    if current["lane_preflight_digest"] != authorized.get(
        "lane_preflight_digest"
    ):
        raise Stage3BExecutionError(
            "runtime matched lane fingerprint differs from authorization"
        )
    return {
        "schema_version": STAGE3B_EXECUTION_SCHEMA_VERSION,
        "campaign_id": STAGE3B_CAMPAIGN_ID,
        "authorization_scope": MATCHED_AUTHORIZATION_SCOPE,
        "authorization_verified": True,
        "authorization_token": str(authorization["authorization_token"]),
        "project_source_commit": clean_commit,
        "matched_manifest_digest": str(matched_manifest["manifest_digest"]),
        "opening_request_digest": str(request["request_digest"]),
        "source_manifest_digest": str(base_manifest["manifest_digest"]),
        "device": "rocm",
        "dtype": "float32",
        "image_digest": _validated_image_digest(image_digest),
        "runtime_authorization": "issued",
        "measurements_allowed": True,
        "execution_permitted": True,
        "evidence": False,
        "full_stage3b_campaign_complete": False,
        "results_publication_permitted": False,
        "test_dataset_access": False,
        "verified_at": _utc_now(),
    }
