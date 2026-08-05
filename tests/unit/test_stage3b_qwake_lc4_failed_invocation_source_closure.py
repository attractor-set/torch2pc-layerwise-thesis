from __future__ import annotations

import json
from pathlib import Path

import pytest

from torch2pc_thesis.stage3b_qwake_lc4_failed_invocation_source_closure import (
    FIRST_REGISTRY_EXACT_COMMIT,
    FREEZE_MATERIALIZATION_COMMIT,
    FREEZE_MATERIALIZATION_MISMATCHES,
    IMAGE_SOURCE_ABSENT_PATHS,
    IMAGE_SOURCE_COMMIT,
    SourceClosureCorrectionError,
    canonical_json,
    classify_registry_at_commit,
    parse_registry,
    sha256_object,
    verify_failed_outcome,
    verify_semantic_digest,
)

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-attempt-002-failed-invocation-"
    "source-closure-correction-v1"
)
FREEZE_REGISTRY = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-attempt-002-execution-freeze-v1/"
    "source-SHA256SUMS"
)


def test_failed_outcome_is_terminal_prelease_failure() -> None:
    verify_failed_outcome(
        {
            "status": (
                "completed_or_failed_partial_effect_no_retry_permitted"
            ),
            "process_spawned": True,
            "docker_run_invoked": True,
            "process_return_code": 1,
            "lease_v1_present": False,
            "lease_sha256": None,
            "output_root_present": False,
            "authorization_consumed": False,
            "attempt_started": False,
            "runtime_started": True,
            "automatic_retry_permitted": False,
            "error": None,
        }
    )




def test_image_source_has_two_absent_registry_paths() -> None:
    entries = parse_registry(FREEZE_REGISTRY)
    classification = classify_registry_at_commit(
        ROOT,
        IMAGE_SOURCE_COMMIT,
        entries,
    )
    assert len(classification.exact) == 10
    assert classification.absent == IMAGE_SOURCE_ABSENT_PATHS
    assert classification.mismatches == ()


def test_freeze_materialization_has_two_hash_mismatches() -> None:
    entries = parse_registry(FREEZE_REGISTRY)
    classification = classify_registry_at_commit(
        ROOT,
        FREEZE_MATERIALIZATION_COMMIT,
        entries,
    )
    observed = {
        relative: (expected, actual)
        for relative, expected, actual in classification.mismatches
    }
    assert len(classification.exact) == 10
    assert classification.absent == ()
    assert observed == FREEZE_MATERIALIZATION_MISMATCHES


def test_first_registry_exact_commit_is_byte_exact() -> None:
    entries = parse_registry(FREEZE_REGISTRY)
    classification = classify_registry_at_commit(
        ROOT,
        FIRST_REGISTRY_EXACT_COMMIT,
        entries,
    )
    assert len(classification.exact) == 12
    assert classification.is_exact


def test_committed_correction_semantic_digests() -> None:
    for filename, field in (
        ("failure.json", "failure_sha256"),
        ("correction.json", "correction_sha256"),
    ):
        value = json.loads(
            (PACKAGE / filename).read_text(encoding="utf-8")
        )
        verify_semantic_digest(value, field)


def test_semantic_digest_rejects_mutation() -> None:
    value: dict[str, object] = {"status": "ok"}
    value["record_sha256"] = sha256_object(value)
    verify_semantic_digest(value, "record_sha256")
    value["status"] = "changed"
    with pytest.raises(SourceClosureCorrectionError):
        verify_semantic_digest(value, "record_sha256")


def test_canonical_json_is_stable() -> None:
    assert canonical_json({"b": 2, "a": 1}) == '{"a":1,"b":2}\n'
