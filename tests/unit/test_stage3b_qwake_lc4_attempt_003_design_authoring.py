from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.verify_stage3b_qwake_lc4_attempt_003_design_authoring import (
    ATTEMPT_003_EFFECT_PATHS,
    EXPECTED_ATTEMPT_ID,
    EXPECTED_FUTURE_RUNTIME_PATHS,
    Attempt003DesignVerificationError,
    canonical_json_bytes,
    semantic_hash,
    verify,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_semantic_hash_excludes_only_its_identity_field() -> None:
    value = {
        "schema_version": 1,
        "attempt_id": EXPECTED_ATTEMPT_ID,
        "contract_sha256": "sha256:placeholder",
    }
    digest = semantic_hash(value, "contract_sha256")
    expected = {
        "attempt_id": EXPECTED_ATTEMPT_ID,
        "schema_version": 1,
    }
    assert digest == (
        "sha256:"
        + __import__("hashlib").sha256(
            canonical_json_bytes(expected)
        ).hexdigest()
    )


def test_future_runtime_source_path_set_is_explicit() -> None:
    assert len(EXPECTED_FUTURE_RUNTIME_PATHS) == 13
    assert ".dockerignore" in EXPECTED_FUTURE_RUNTIME_PATHS
    assert "Dockerfile.rocm" in EXPECTED_FUTURE_RUNTIME_PATHS
    assert any(
        "attempt_003_execution_wrapper.py" in path
        for path in EXPECTED_FUTURE_RUNTIME_PATHS
    )


def test_attempt_003_effect_path_set_is_closed() -> None:
    rendered = {path.as_posix() for path in ATTEMPT_003_EFFECT_PATHS}
    assert 'results/stage-3/qwake-lc4-runtime-validation-v1-attempt-003' in rendered
    assert 'results/stage-3/qwake-lc4-runtime-validation-v1-attempt-003.host-outcome.json' in rendered
    assert any("authorization-v1" in path for path in rendered)


def test_repository_design_authoring_verifies() -> None:
    verify(PROJECT_ROOT)


def test_noncanonical_json_is_rejected(tmp_path: Path) -> None:
    root = tmp_path
    package = root / (
        "experiments/frozen/"
        "stage3b-qwake-lc4-e-attempt-003-"
        "runtime-source-closure-design-authoring-v1"
    )
    package.mkdir(parents=True)
    (package / "authoring.json").write_text(
        json.dumps({"schema_version": 1}, indent=2),
        encoding="utf-8",
    )
    with pytest.raises(
        (Attempt003DesignVerificationError, FileNotFoundError)
    ):
        verify(root)
