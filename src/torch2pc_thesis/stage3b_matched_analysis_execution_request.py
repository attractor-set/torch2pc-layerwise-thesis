"""Frozen execution request for Stage 3B matched descriptive analysis."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Final, cast

from torch2pc_thesis.stage3b_matched_analysis import EXPECTED_OUTPUT_NAMES
from torch2pc_thesis.stage3b_matched_analysis_protocol import (
    EVIDENCE_ROOT_RELATIVE,
    EXECUTION_SOURCE_COMMIT,
    EXPECTED_EVIDENCE_SHA256,
    IMAGE_DIGEST,
    PROTOCOL_ID,
    RELEASE_COMMIT,
    RELEASE_TAG,
)

REQUEST_SCHEMA_VERSION: Final[int] = 1
REQUEST_ID: Final[str] = (
    "stage3b-matched-descriptive-analysis-execution-request-v1"
)
REQUEST_STATUS: Final[str] = (
    "frozen_execution_request_authorization_not_issued"
)
REQUEST_FREEZE_DATE: Final[str] = "2026-07-21"
REQUEST_BASE_COMMIT: Final[str] = (
    "70d6c3ca971415f57805dbf9b2ed4bbb80b2d873"
)
REQUEST_ROOT_RELATIVE: Final[Path] = Path(
    "experiments/frozen/"
    "stage3b-matched-descriptive-analysis-execution-request-v1"
)
OUTPUT_ROOT_RELATIVE: Final[Path] = Path(
    "results/stage-3/analysis/matched/"
    "stage3b-matched-descriptive-analysis-70d6c3c-v1"
)
PROTOCOL_RELATIVE: Final[Path] = Path(
    "experiments/frozen/stage3b-matched-descriptive-analysis-v1/protocol.json"
)
PROTOCOL_REGISTRY_RELATIVE: Final[Path] = Path(
    "experiments/frozen/stage3b-matched-descriptive-analysis-v1/SHA256SUMS"
)
ANALYSIS_MODULE_RELATIVE: Final[Path] = Path(
    "src/torch2pc_thesis/stage3b_matched_analysis.py"
)
SYNTHETIC_CLI_RELATIVE: Final[Path] = Path(
    "scripts/analyze_stage3b_matched.py"
)
EXPECTED_PROTOCOL_SHA256: Final[str] = (
    "074510f1212f1eceb41da8b42ab52f1fd9d816c3901f2a3b8e4e7afec59a3209"
)
EXPECTED_PROTOCOL_REGISTRY_SHA256: Final[str] = (
    "a49f49f423948900221007d715e5dc174cd3b14af288ddc56f87ec5366307b63"
)
EXPECTED_ANALYSIS_MODULE_SHA256: Final[str] = (
    "0e9f55fc337b7870923a087308f370afc54bdce97501ce462c1033062a322462"
)
EXPECTED_SYNTHETIC_CLI_SHA256: Final[str] = (
    "5a402f1588eea1e751fcf448257d549c85f2de89171e6ca2f6e87404b6c976a4"
)


class Stage3BMatchedAnalysisExecutionRequestError(RuntimeError):
    """Raised when the frozen execution request cannot be verified."""


def sha256_file(path: Path) -> str:
    """Return SHA-256 without loading the file into memory."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_bytes(value: Mapping[str, object]) -> bytes:
    """Return deterministic pretty JSON bytes."""

    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def canonical_json_digest(value: Mapping[str, object]) -> str:
    """Return the digest of canonical compact JSON."""

    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _load_json_object(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Stage3BMatchedAnalysisExecutionRequestError(
            f"cannot read JSON object: {path}"
        ) from exc
    if not isinstance(value, dict):
        raise Stage3BMatchedAnalysisExecutionRequestError(
            f"expected JSON object: {path}"
        )
    return cast(dict[str, object], value)


def _require_file_digest(
    project_root: Path,
    relative_path: Path,
    expected_digest: str,
) -> None:
    path = project_root / relative_path
    if not path.is_file():
        raise Stage3BMatchedAnalysisExecutionRequestError(
            f"required request input is missing: {path}"
        )
    observed = sha256_file(path)
    if observed != expected_digest:
        raise Stage3BMatchedAnalysisExecutionRequestError(
            f"request input digest differs for {relative_path}: "
            f"expected={expected_digest}, observed={observed}"
        )


def _protocol_identity(project_root: Path) -> dict[str, object]:
    _require_file_digest(
        project_root,
        PROTOCOL_RELATIVE,
        EXPECTED_PROTOCOL_SHA256,
    )
    _require_file_digest(
        project_root,
        PROTOCOL_REGISTRY_RELATIVE,
        EXPECTED_PROTOCOL_REGISTRY_SHA256,
    )
    protocol = _load_json_object(project_root / PROTOCOL_RELATIVE)
    boundary = protocol.get("claim_boundary")
    outputs = protocol.get("registered_outputs")
    source = protocol.get("source_evidence")
    if not isinstance(boundary, dict):
        raise Stage3BMatchedAnalysisExecutionRequestError(
            "protocol claim boundary is invalid"
        )
    if not isinstance(outputs, dict):
        raise Stage3BMatchedAnalysisExecutionRequestError(
            "protocol output contract is invalid"
        )
    if not isinstance(source, dict):
        raise Stage3BMatchedAnalysisExecutionRequestError(
            "protocol source-evidence identity is invalid"
        )
    if protocol.get("protocol_id") != PROTOCOL_ID:
        raise Stage3BMatchedAnalysisExecutionRequestError(
            "protocol ID differs"
        )
    if boundary.get("protocol_frozen") is not True:
        raise Stage3BMatchedAnalysisExecutionRequestError(
            "protocol is not frozen"
        )
    if boundary.get("analysis_execution_permitted") is not False:
        raise Stage3BMatchedAnalysisExecutionRequestError(
            "protocol unexpectedly permits execution"
        )
    if outputs.get("expected_top_level_file_count") != 18:
        raise Stage3BMatchedAnalysisExecutionRequestError(
            "protocol output count differs"
        )
    return {
        "protocol_id": PROTOCOL_ID,
        "path": PROTOCOL_RELATIVE.as_posix(),
        "sha256": EXPECTED_PROTOCOL_SHA256,
        "registry_path": PROTOCOL_REGISTRY_RELATIVE.as_posix(),
        "registry_sha256": EXPECTED_PROTOCOL_REGISTRY_SHA256,
        "frozen": True,
    }


def _implementation_identity(project_root: Path) -> dict[str, object]:
    _require_file_digest(
        project_root,
        ANALYSIS_MODULE_RELATIVE,
        EXPECTED_ANALYSIS_MODULE_SHA256,
    )
    _require_file_digest(
        project_root,
        SYNTHETIC_CLI_RELATIVE,
        EXPECTED_SYNTHETIC_CLI_SHA256,
    )
    return {
        "implementation_base_commit": REQUEST_BASE_COMMIT,
        "analysis_module": {
            "path": ANALYSIS_MODULE_RELATIVE.as_posix(),
            "sha256": EXPECTED_ANALYSIS_MODULE_SHA256,
        },
        "synthetic_cli": {
            "path": SYNTHETIC_CLI_RELATIVE.as_posix(),
            "sha256": EXPECTED_SYNTHETIC_CLI_SHA256,
            "sealed_evidence_input_exposed": False,
        },
        "analysis_core_mutation_after_request_permitted": False,
        "authorization_wrapper_may_be_added_separately": True,
    }


def build_execution_request(project_root: Path) -> dict[str, object]:
    """Build the request without inspecting observed metric values."""

    root = project_root.expanduser().resolve()
    protocol_identity = _protocol_identity(root)
    implementation_identity = _implementation_identity(root)
    output_inventory = list(EXPECTED_OUTPUT_NAMES)
    if len(output_inventory) != 18 or len(set(output_inventory)) != 18:
        raise Stage3BMatchedAnalysisExecutionRequestError(
            "registered output inventory differs"
        )

    payload: dict[str, object] = {
        "schema_version": REQUEST_SCHEMA_VERSION,
        "request_id": REQUEST_ID,
        "status": REQUEST_STATUS,
        "phase": "post_implementation_pre_authorization",
        "freeze_date": REQUEST_FREEZE_DATE,
        "request_base_commit": REQUEST_BASE_COMMIT,
        "claim_boundary": {
            "execution_request_frozen": True,
            "execution_authorization_present": False,
            "analysis_execution_permitted": False,
            "analysis_execution_performed": False,
            "analysis_results_present": False,
            "analysis_output_evidence": False,
            "source_evidence_read_only": True,
            "request_builder_uses_observed_metric_values": False,
            "results_publication_permitted": False,
            "release_publication_permitted": False,
            "test_dataset_access": False,
            "ex_if0_opened": False,
            "policy_activation_permitted": False,
            "superiority_claim_permitted": False,
            "full_stage3b_campaign_complete": False,
        },
        "protocol": protocol_identity,
        "implementation": implementation_identity,
        "source_evidence": {
            "root": EVIDENCE_ROOT_RELATIVE.as_posix(),
            "release_tag": RELEASE_TAG,
            "release_commit": RELEASE_COMMIT,
            "profiling_execution_source_commit": EXECUTION_SOURCE_COMMIT,
            "profiling_image_digest": IMAGE_DIGEST,
            "expected_sha256": dict(sorted(EXPECTED_EVIDENCE_SHA256.items())),
            "locality_uncompressed_sha256": (
                "3228baaa0f6479b1b4296f96632bd2d99c49642dc38f28f5ed7bc978d9dc538a"
            ),
            "access_mode": "read_only",
            "test_dataset_access": False,
        },
        "requested_execution": {
            "mode": "single_authorized_read_only_run",
            "maximum_execution_count": 1,
            "authorization_required": True,
            "authorization_status": "not_issued",
            "authorization_must_be_machine_readable": True,
            "authorization_must_bind_request_digest": True,
            "authorization_must_bind_runtime_identity": True,
            "authorization_must_freeze_generated_at_utc": True,
            "authorization_must_verify_output_root_absent": True,
            "authorization_must_verify_source_hashes_before_and_after": True,
            "dry_run_must_not_compute_metric_values": True,
            "network_access_required": False,
        },
        "output_contract": {
            "root": OUTPUT_ROOT_RELATIVE.as_posix(),
            "root_policy": "must_not_exist_before_authorized_execution",
            "atomic_directory_publication": True,
            "expected_top_level_file_count": 18,
            "expected_top_level_files": output_inventory,
            "checksum_registry": "SHA256SUMS",
            "seal_required_after_execution": True,
            "publication_gate_required_after_sealing": True,
            "results_publication_permitted": False,
        },
        "failure_policy": {
            "missing_or_changed_source": "fail_closed",
            "implementation_identity_mismatch": "fail_closed",
            "protocol_identity_mismatch": "fail_closed",
            "preexisting_output_root": "fail_closed",
            "partial_output": "remove_temporary_output_and_fail_closed",
            "unexpected_output_inventory": "fail_closed",
            "second_execution_attempt": "fail_closed",
            "post_hoc_exclusion": "forbidden",
        },
        "next_required_slice": (
            "separate runtime preflight and machine-readable execution "
            "authorization; no sealed-evidence analysis before merge"
        ),
    }
    return {**payload, "request_digest": canonical_json_digest(payload)}


def validate_execution_request(
    request: Mapping[str, object],
    project_root: Path,
) -> None:
    """Validate exact equality with the deterministic request builder."""

    expected = build_execution_request(project_root)
    if dict(request) != expected:
        raise Stage3BMatchedAnalysisExecutionRequestError(
            "frozen matched descriptive-analysis execution request differs "
            "from deterministic builder"
        )


def write_execution_request_package(
    project_root: Path,
    output_root: Path,
    *,
    check: bool = False,
) -> dict[str, object]:
    """Write or verify request.json and SHA256SUMS."""

    request = build_execution_request(project_root)
    request_content = canonical_json_bytes(request)
    checksum_content = (
        f"{hashlib.sha256(request_content).hexdigest()}  request.json\n"
    ).encode()
    destination = output_root.expanduser().resolve()
    expected = {
        "request.json": request_content,
        "SHA256SUMS": checksum_content,
    }
    if check:
        for name, content in expected.items():
            path = destination / name
            if not path.is_file() or path.read_bytes() != content:
                raise Stage3BMatchedAnalysisExecutionRequestError(
                    f"frozen execution-request package differs: {path}"
                )
        observed_names = {
            path.name for path in destination.iterdir() if path.is_file()
        }
        if observed_names != set(expected):
            raise Stage3BMatchedAnalysisExecutionRequestError(
                "frozen execution-request file set differs: "
                f"{sorted(observed_names)}"
            )
        return request
    if destination.exists() and any(destination.iterdir()):
        raise Stage3BMatchedAnalysisExecutionRequestError(
            f"execution-request output root is not empty: {destination}"
        )
    destination.mkdir(parents=True, exist_ok=True)
    for name, content in expected.items():
        (destination / name).write_bytes(content)
    return request
