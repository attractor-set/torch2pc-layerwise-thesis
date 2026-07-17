"""Scientific-admission freeze for matched Stage 3B B0/B1/B2 profiling."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Final, cast

from torch2pc_thesis.stage3b_execution import (
    STAGE3B_CAMPAIGN_ID,
    Stage3BExecutionError,
    atomic_write_json,
    validate_manifest,
)

MATCHED_PROFILING_SCHEMA_VERSION: Final[int] = 1
MATCHED_PROFILING_REQUEST_ID: Final[str] = (
    "stage3b-b1-b2-matched-profiling-request-v1"
)
MATCHED_PROFILING_MANIFEST_ID: Final[str] = (
    "stage3b-b1-b2-matched-profiling-manifest-v1"
)
MATCHED_PROFILING_BASE_COMMIT: Final[str] = (
    "cc0a70f378e9d8ffe996c8f7c4bfc4d1271e5643"
)
MATCHED_PROFILING_CANDIDATES: Final[tuple[str, ...]] = (
    "stage2_baseline",
    "isolated_layer_vjp",
    "composite_vjp",
)
MATCHED_PROFILING_DECISIONS: Final[tuple[str, ...]] = ("EQ-B1", "EQ-B2")
MATCHED_PROFILING_EXPECTED_CELL_COUNT: Final[int] = 288
MATCHED_PROFILING_EXPECTED_CANDIDATE_COUNT: Final[int] = 96
MATCHED_PROFILING_EXPECTED_METHOD_COUNT: Final[int] = 144
MATCHED_PROFILING_EXPECTED_PAIR_COUNT: Final[int] = 48


class MatchedProfilingError(Stage3BExecutionError):
    """Raised when matched-profiling admission invariants are violated."""


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _string_keyed_dict(value: Mapping[object, object], *, field: str) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise MatchedProfilingError(f"{field} contains a non-string key")
        result[key] = item
    return result


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of one existing file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json_object(path: Path) -> dict[str, object]:
    """Load a JSON object and reject arrays or scalar roots."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise MatchedProfilingError(f"JSON root must be an object: {path}")
    return cast(dict[str, object], raw)


def require_opening_base_ancestor(project_root: Path) -> None:
    """Require the post-EQ merge base to remain in the current history."""
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(project_root),
            "merge-base",
            "--is-ancestor",
            MATCHED_PROFILING_BASE_COMMIT,
            "HEAD",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip()
        suffix = f": {message}" if message else ""
        raise MatchedProfilingError(
            "post-EQ merge base is not an ancestor of the current HEAD" + suffix
        )


def _relative_path(path: Path, *, project_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(project_root.resolve()))
    except ValueError as error:
        raise MatchedProfilingError(
            f"matched-profiling input must stay under project root: {path}"
        ) from error


def _validate_decision(
    decision: Mapping[str, object],
    *,
    expected_decision_id: str,
) -> None:
    if decision.get("decision_id") != expected_decision_id:
        raise MatchedProfilingError(
            f"unexpected decision_id for {expected_decision_id}: "
            f"{decision.get('decision_id')!r}"
        )
    if decision.get("status") != "pass":
        raise MatchedProfilingError(f"{expected_decision_id} must have status=pass")
    if decision.get("sealed") is not True:
        raise MatchedProfilingError(f"{expected_decision_id} must be sealed")
    if decision.get("failed_pairs") != []:
        raise MatchedProfilingError(
            f"{expected_decision_id} must have no failed pairs"
        )

    raw_gates = decision.get("gates")
    if not isinstance(raw_gates, Mapping) or not raw_gates:
        raise MatchedProfilingError(f"{expected_decision_id} gates are missing")
    for gate_id, raw_gate in raw_gates.items():
        if not isinstance(gate_id, str) or not isinstance(raw_gate, Mapping):
            raise MatchedProfilingError(
                f"{expected_decision_id} contains a malformed gate"
            )
        if raw_gate.get("passed") is not True:
            raise MatchedProfilingError(
                f"{expected_decision_id} gate did not pass: {gate_id}"
            )
        if raw_gate.get("failed_pairs") != []:
            raise MatchedProfilingError(
                f"{expected_decision_id} gate has failed pairs: {gate_id}"
            )


def _decision_record(
    decision: Mapping[str, object],
    *,
    path: Path,
    project_root: Path,
    expected_decision_id: str,
) -> dict[str, object]:
    _validate_decision(decision, expected_decision_id=expected_decision_id)
    return {
        "decision_id": expected_decision_id,
        "path": _relative_path(path, project_root=project_root),
        "sha256": sha256_file(path),
        "status": "pass",
        "sealed": True,
        "failed_pairs": [],
        "candidate_id": decision.get("candidate_id"),
        "control_id": decision.get("control_id"),
        "gate_ids": sorted(cast(Mapping[str, object], decision["gates"])),
    }


def _profiling_scope(contract: Mapping[str, object], *, contract_name: str) -> dict[str, object]:
    raw_scope = contract.get("profiling_scope")
    if not isinstance(raw_scope, Mapping):
        raise MatchedProfilingError(f"{contract_name} profiling_scope is missing")
    return _string_keyed_dict(raw_scope, field=f"{contract_name} profiling_scope")


def _validate_contract_pair(
    b1_contract: Mapping[str, object],
    b2_contract: Mapping[str, object],
) -> dict[str, object]:
    b1_scope = _profiling_scope(b1_contract, contract_name="B1 contract")
    b2_scope = _profiling_scope(b2_contract, contract_name="B2 contract")
    if b1_scope != b2_scope:
        raise MatchedProfilingError("B1 and B2 profiling scopes differ")

    expected_candidates = {
        "isolated_layer_vjp": b1_contract,
        "composite_vjp": b2_contract,
    }
    for candidate_id, contract in expected_candidates.items():
        raw_candidate = contract.get("candidate")
        if not isinstance(raw_candidate, Mapping):
            raise MatchedProfilingError(f"{candidate_id} candidate contract is missing")
        if raw_candidate.get("candidate_id") != candidate_id:
            raise MatchedProfilingError(
                f"candidate contract does not identify {candidate_id}"
            )

        raw_gate_hierarchy = contract.get("gate_hierarchy")
        if not isinstance(raw_gate_hierarchy, Mapping):
            raise MatchedProfilingError(
                f"{candidate_id} gate_hierarchy is missing"
            )
        if raw_gate_hierarchy.get("matched_profiling_open_rule") != (
            "both B1 and B2 equivalence evidence are sealed"
        ):
            raise MatchedProfilingError(
                f"{candidate_id} matched-profiling open rule changed"
            )

        raw_future_boundary = contract.get("future_policy_boundary")
        if not isinstance(raw_future_boundary, Mapping):
            raise MatchedProfilingError(
                f"{candidate_id} future_policy_boundary is missing"
            )
        forbidden_flags = (
            "estimator_present",
            "oracle_branching_present",
            "cheap_diagnostic_loop_present",
            "hysteresis_policy_present",
            "offline_trace_collection_present",
        )
        for flag in forbidden_flags:
            if raw_future_boundary.get(flag) is not False:
                raise MatchedProfilingError(
                    f"{candidate_id} unexpectedly enables {flag}"
                )

    if b1_scope.get("cells_per_candidate") != MATCHED_PROFILING_EXPECTED_CANDIDATE_COUNT:
        raise MatchedProfilingError("candidate cell count differs from the frozen scope")
    if b1_scope.get("methods") != ["FixedPred", "Strict"]:
        raise MatchedProfilingError("matched profiling methods changed")
    return b1_scope


def _selected_cells(base_manifest: Mapping[str, object]) -> list[dict[str, object]]:
    raw_cells = base_manifest.get("cells")
    if not isinstance(raw_cells, list):
        raise MatchedProfilingError("base Stage 3B manifest cells are missing")

    selected: list[dict[str, object]] = []
    for raw_cell in raw_cells:
        if not isinstance(raw_cell, Mapping):
            raise MatchedProfilingError("base Stage 3B manifest contains a malformed cell")
        candidate_id = str(raw_cell.get("candidate_id"))
        if candidate_id not in MATCHED_PROFILING_CANDIDATES:
            continue
        cell = _string_keyed_dict(raw_cell, field="base Stage 3B manifest cell")
        source_gate_status = cell.get("candidate_gate_status")
        cell["source_candidate_gate_status"] = source_gate_status
        cell["candidate_gate_status"] = "equivalence_gate_passed"
        cell["matched_profiling_eligible"] = True
        selected.append(cell)

    candidate_counts = Counter(str(cell["candidate_id"]) for cell in selected)
    expected_candidate_counts = Counter(
        {
            candidate_id: MATCHED_PROFILING_EXPECTED_CANDIDATE_COUNT
            for candidate_id in MATCHED_PROFILING_CANDIDATES
        }
    )
    if candidate_counts != expected_candidate_counts:
        raise MatchedProfilingError(
            "matched candidate counts differ from the frozen matrix: "
            f"{dict(candidate_counts)}"
        )

    method_counts = Counter(str(cell["method"]) for cell in selected)
    if method_counts != Counter(
        {
            "fixedpred": MATCHED_PROFILING_EXPECTED_METHOD_COUNT,
            "strict": MATCHED_PROFILING_EXPECTED_METHOD_COUNT,
        }
    ):
        raise MatchedProfilingError(
            f"matched method counts differ from the frozen matrix: {dict(method_counts)}"
        )

    pair_counts = Counter(
        (str(cell["candidate_id"]), str(cell["method"])) for cell in selected
    )
    for candidate_id in MATCHED_PROFILING_CANDIDATES:
        for method in ("fixedpred", "strict"):
            if pair_counts[(candidate_id, method)] != MATCHED_PROFILING_EXPECTED_PAIR_COUNT:
                raise MatchedProfilingError(
                    "matched candidate/method count differs from the frozen matrix: "
                    f"{candidate_id}/{method}={pair_counts[(candidate_id, method)]}"
                )

    if len(selected) != MATCHED_PROFILING_EXPECTED_CELL_COUNT:
        raise MatchedProfilingError(
            f"matched profiling requires {MATCHED_PROFILING_EXPECTED_CELL_COUNT} cells"
        )
    return selected


def build_matched_manifest(
    base_manifest: Mapping[str, object],
    b1_contract: Mapping[str, object],
    b2_contract: Mapping[str, object],
) -> dict[str, object]:
    """Build the frozen 288-cell B0/B1/B2 scientific-admission manifest."""
    validate_manifest(base_manifest)
    profiling_scope = _validate_contract_pair(b1_contract, b2_contract)
    selected = _selected_cells(base_manifest)

    raw_protocol = base_manifest.get("protocol")
    if not isinstance(raw_protocol, Mapping):
        raise MatchedProfilingError("base Stage 3B protocol is missing")

    candidate_counts = Counter(str(cell["candidate_id"]) for cell in selected)
    method_counts = Counter(str(cell["method"]) for cell in selected)
    payload: dict[str, object] = {
        "schema_version": MATCHED_PROFILING_SCHEMA_VERSION,
        "manifest_id": MATCHED_PROFILING_MANIFEST_ID,
        "campaign_id": STAGE3B_CAMPAIGN_ID,
        "status": "scientific_admission_open_execution_not_authorized",
        "evidence": False,
        "execution_performed": False,
        "test_dataset_access": False,
        "full_stage3b_campaign_complete": False,
        "source_manifest_digest": base_manifest["manifest_digest"],
        "source_manifest_status": base_manifest.get("status"),
        "candidate_ids": list(MATCHED_PROFILING_CANDIDATES),
        "candidate_counts": dict(sorted(candidate_counts.items())),
        "method_counts": dict(sorted(method_counts.items())),
        "selected_cell_count": len(selected),
        "protocol": dict(raw_protocol),
        "profiling_scope": profiling_scope,
        "candidate_order_policy": (
            "preserve source Stage 3B counterbalanced order after excluding A0"
        ),
        "execution_policy": {
            "scientific_admission": "open",
            "runtime_authorization": "not_issued",
            "measurements_allowed": False,
            "candidate_aware_runner_required": True,
            "rocm_float32_primary_lane_required": True,
            "temporary_output_only_until_runtime_freeze": True,
            "committed_measurements_present": False,
        },
        "future_policy_boundary": {
            "ex_if0_open": False,
            "estimator_present": False,
            "ecz_active": False,
            "qwake_pc_active": False,
            "controller_actions_present": False,
            "offline_policy_selection_present": False,
        },
        "cells": selected,
    }
    return {**payload, "manifest_digest": _digest(payload)}


def validate_matched_manifest(manifest: Mapping[str, object]) -> None:
    """Validate the digest and non-execution boundaries of a matched manifest."""
    if manifest.get("schema_version") != MATCHED_PROFILING_SCHEMA_VERSION:
        raise MatchedProfilingError("unsupported matched-profiling schema")
    if manifest.get("manifest_id") != MATCHED_PROFILING_MANIFEST_ID:
        raise MatchedProfilingError("unexpected matched-profiling manifest_id")
    if manifest.get("campaign_id") != STAGE3B_CAMPAIGN_ID:
        raise MatchedProfilingError("unexpected matched-profiling campaign_id")
    if manifest.get("evidence") is not False:
        raise MatchedProfilingError("matched opening manifest must remain non-evidence")
    if manifest.get("execution_performed") is not False:
        raise MatchedProfilingError("matched opening manifest cannot record execution")
    if manifest.get("test_dataset_access") is not False:
        raise MatchedProfilingError("matched opening manifest cannot access test data")
    if manifest.get("full_stage3b_campaign_complete") is not False:
        raise MatchedProfilingError("matched opening cannot complete full Stage 3B")
    if manifest.get("selected_cell_count") != MATCHED_PROFILING_EXPECTED_CELL_COUNT:
        raise MatchedProfilingError("matched opening manifest cell count changed")

    supplied_digest = manifest.get("manifest_digest")
    if not isinstance(supplied_digest, str):
        raise MatchedProfilingError("matched manifest_digest is required")
    payload = dict(manifest)
    del payload["manifest_digest"]
    if _digest(payload) != supplied_digest:
        raise MatchedProfilingError("matched manifest_digest does not match content")


def build_matched_request(
    *,
    project_root: Path,
    base_manifest_path: Path,
    b1_contract_path: Path,
    b2_contract_path: Path,
    b1_decision_path: Path,
    b2_decision_path: Path,
    matched_manifest_path: Path,
    base_manifest: Mapping[str, object],
    b1_contract: Mapping[str, object],
    b2_contract: Mapping[str, object],
    b1_decision: Mapping[str, object],
    b2_decision: Mapping[str, object],
    matched_manifest: Mapping[str, object],
) -> dict[str, object]:
    """Build the deterministic opening request bound to sealed EQ-B1/EQ-B2."""
    validate_manifest(base_manifest)
    validate_matched_manifest(matched_manifest)
    _validate_contract_pair(b1_contract, b2_contract)

    require_opening_base_ancestor(project_root)

    decisions = [
        _decision_record(
            b1_decision,
            path=b1_decision_path,
            project_root=project_root,
            expected_decision_id="EQ-B1",
        ),
        _decision_record(
            b2_decision,
            path=b2_decision_path,
            project_root=project_root,
            expected_decision_id="EQ-B2",
        ),
    ]

    payload: dict[str, object] = {
        "schema_version": MATCHED_PROFILING_SCHEMA_VERSION,
        "request_id": MATCHED_PROFILING_REQUEST_ID,
        "campaign_id": STAGE3B_CAMPAIGN_ID,
        "status": "scientific_admission_open_execution_not_authorized",
        "evidence": False,
        "execution_performed": False,
        "test_dataset_access": False,
        "full_stage3b_campaign_complete": False,
        "opening_base_commit": MATCHED_PROFILING_BASE_COMMIT,
        "project_source_commit_policy": (
            "record exact clean implementation commit at separate runtime freeze"
        ),
        "prerequisite_rule": "sealed positive EQ-B1 and EQ-B2 are both required",
        "prerequisite_decisions": decisions,
        "source_artifacts": {
            "execution_manifest": {
                "path": _relative_path(base_manifest_path, project_root=project_root),
                "sha256": sha256_file(base_manifest_path),
                "manifest_digest": base_manifest["manifest_digest"],
            },
            "b1_contract": {
                "path": _relative_path(b1_contract_path, project_root=project_root),
                "sha256": sha256_file(b1_contract_path),
            },
            "b2_contract": {
                "path": _relative_path(b2_contract_path, project_root=project_root),
                "sha256": sha256_file(b2_contract_path),
            },
            "matched_manifest": {
                "path": _relative_path(matched_manifest_path, project_root=project_root),
                "manifest_digest": matched_manifest["manifest_digest"],
                "selected_cell_count": matched_manifest["selected_cell_count"],
            },
        },
        "admitted_candidates": list(MATCHED_PROFILING_CANDIDATES),
        "scientific_admission": "open",
        "runtime_authorization": "not_issued",
        "measurements_allowed": False,
        "next_required_slice": (
            "candidate-aware matched runner plus separate ROCm/float32 runtime freeze"
        ),
        "explicitly_closed": [
            "EX-IF0",
            "estimator",
            "active ECZ",
            "QWake-PC",
            "controller actions",
            "offline policy selection",
            "test-split access",
        ],
    }
    return {**payload, "request_digest": _digest(payload)}


def validate_matched_request(request: Mapping[str, object]) -> None:
    """Validate request digest and all closed-boundary flags."""
    if request.get("schema_version") != MATCHED_PROFILING_SCHEMA_VERSION:
        raise MatchedProfilingError("unsupported matched request schema")
    if request.get("request_id") != MATCHED_PROFILING_REQUEST_ID:
        raise MatchedProfilingError("unexpected matched request_id")
    if request.get("campaign_id") != STAGE3B_CAMPAIGN_ID:
        raise MatchedProfilingError("unexpected matched request campaign")
    if request.get("scientific_admission") != "open":
        raise MatchedProfilingError("matched scientific admission is not open")
    if request.get("runtime_authorization") != "not_issued":
        raise MatchedProfilingError("runtime authorization must remain unissued")
    if request.get("measurements_allowed") is not False:
        raise MatchedProfilingError("opening request cannot authorize measurements")
    if request.get("test_dataset_access") is not False:
        raise MatchedProfilingError("opening request cannot access test data")
    if request.get("full_stage3b_campaign_complete") is not False:
        raise MatchedProfilingError("opening request cannot complete full Stage 3B")

    supplied_digest = request.get("request_digest")
    if not isinstance(supplied_digest, str):
        raise MatchedProfilingError("matched request_digest is required")
    payload = dict(request)
    del payload["request_digest"]
    if _digest(payload) != supplied_digest:
        raise MatchedProfilingError("matched request_digest does not match content")


def write_matched_artifacts(
    *,
    manifest_path: Path,
    request_path: Path,
    manifest: Mapping[str, object],
    request: Mapping[str, object],
) -> None:
    """Validate and atomically write deterministic opening artifacts."""
    validate_matched_manifest(manifest)
    validate_matched_request(request)
    atomic_write_json(manifest_path, manifest)
    atomic_write_json(request_path, request)


def compare_json_file(path: Path, expected: Mapping[str, object]) -> None:
    """Require a committed JSON artifact to equal its deterministic rebuild."""
    observed = load_json_object(path)
    if observed != dict(expected):
        raise MatchedProfilingError(f"frozen artifact differs from rebuild: {path}")


def decision_ids(records: Sequence[Mapping[str, object]]) -> tuple[str, ...]:
    """Return decision IDs in stable order for tests and reporting."""
    return tuple(str(record.get("decision_id")) for record in records)
