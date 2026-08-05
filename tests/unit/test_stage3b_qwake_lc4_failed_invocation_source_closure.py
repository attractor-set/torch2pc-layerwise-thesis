from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from torch2pc_thesis import (
    stage3b_qwake_lc4_failed_invocation_source_closure as source_closure,
)
from torch2pc_thesis.stage3b_qwake_lc4_failed_invocation_source_closure import (
    FIRST_REGISTRY_EXACT_COMMIT,
    FREEZE_MATERIALIZATION_COMMIT,
    FREEZE_MATERIALIZATION_MISMATCHES,
    IMAGE_SOURCE_ABSENT_PATHS,
    IMAGE_SOURCE_COMMIT,
    RegistryEntry,
    SourceClosureCorrectionError,
    canonical_json,
    classify_registry_at_commit,
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


def test_classifier_distinguishes_exact_and_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exact_content = b"exact-content"
    entries = (
        RegistryEntry(
            hashlib.sha256(exact_content).hexdigest(),
            "exact.txt",
        ),
        RegistryEntry(
            hashlib.sha256(b"absent-content").hexdigest(),
            "absent.txt",
        ),
    )

    def synthetic_blob(
        root: Path,
        commit: str,
        relative: str,
    ) -> bytes | None:
        assert root == ROOT
        assert commit == "synthetic-exact-absent"
        if relative == "exact.txt":
            return exact_content
        return None

    monkeypatch.setattr(source_closure, "git_blob", synthetic_blob)
    classification = classify_registry_at_commit(
        ROOT,
        "synthetic-exact-absent",
        entries,
    )

    assert classification.exact == ("exact.txt",)
    assert classification.absent == ("absent.txt",)
    assert classification.mismatches == ()
    assert not classification.is_exact


def test_classifier_reports_hash_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected_content = b"expected-content"
    observed_content = b"observed-content"
    expected_sha256 = hashlib.sha256(expected_content).hexdigest()
    observed_sha256 = hashlib.sha256(observed_content).hexdigest()
    entries = (
        RegistryEntry(expected_sha256, "mismatch.txt"),
    )

    def synthetic_blob(
        root: Path,
        commit: str,
        relative: str,
    ) -> bytes | None:
        assert root == ROOT
        assert commit == "synthetic-mismatch"
        assert relative == "mismatch.txt"
        return observed_content

    monkeypatch.setattr(source_closure, "git_blob", synthetic_blob)
    classification = classify_registry_at_commit(
        ROOT,
        "synthetic-mismatch",
        entries,
    )

    assert classification.exact == ()
    assert classification.absent == ()
    assert classification.mismatches == (
        (
            "mismatch.txt",
            expected_sha256,
            observed_sha256,
        ),
    )
    assert not classification.is_exact


def test_temporal_source_closure_constants_are_exact() -> None:
    assert IMAGE_SOURCE_COMMIT == (
        "02afcc3e79b2d456cc3f1c075d4d792a0be608f7"
    )
    assert FREEZE_MATERIALIZATION_COMMIT == (
        "2f346498a28377d355b88560aa099890f829af46"
    )
    assert FIRST_REGISTRY_EXACT_COMMIT == (
        "b5b29be5802641287e6e29bb42240ad9e41744b4"
    )
    assert IMAGE_SOURCE_ABSENT_PATHS == (
        (
            "scripts/"
            "verify_stage3b_qwake_lc4_attempt_002_execution_freeze.py"
        ),
        (
            "tests/unit/"
            "test_stage3b_qwake_lc4_attempt_002_execution_freeze.py"
        ),
    )
    observed_mismatches = FREEZE_MATERIALIZATION_MISMATCHES
    assert observed_mismatches == {
        IMAGE_SOURCE_ABSENT_PATHS[0]: (
            (
                "db2de557423cfde173851a01a517bfd7df12fdb627ec9a519"
                "8621225be3fc332"
            ),
            (
                "6691eea819da03e7da06e766c6a4044441cef7a476e204cd"
                "08698afb9cb280e3"
            ),
        ),
        IMAGE_SOURCE_ABSENT_PATHS[1]: (
            (
                "418414f0f976d9304446618bd2afe71a21dd11aac62e1ace"
                "eb5423f47b1f7b1c"
            ),
            (
                "55f365431c2497a1f30180556b8b4dc0477f7357063d4e3e"
                "b9aa4e319fcba43d"
            ),
        ),
    }


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
