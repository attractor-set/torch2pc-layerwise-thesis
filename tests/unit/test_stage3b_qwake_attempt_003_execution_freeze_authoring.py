from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]
VERIFIER = ROOT / (
    "scripts/verify_stage3b_qwake_attempt_003_execution_freeze_authoring.py"
)
PACKAGE = ROOT / (
    "experiments/frozen/stage3b-qwake-attempt-003-source-binding-execution-freeze-authoring-v1"
)
IMPLEMENTATION = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-attempt-003-clean-source-closure-"
    "implementation-authoring-v1/implementation.json"
)


def load_verifier() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "attempt_003_execution_freeze_authoring_verifier",
        VERIFIER,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_source_binding_authoring_verifies() -> None:
    module = load_verifier()
    module.verify(ROOT)


def test_binding_closes_pending_without_rewriting_history() -> None:
    contract = json.loads(
        (PACKAGE / "contract.json").read_text(encoding="utf-8")
    )
    implementation = json.loads(
        IMPLEMENTATION.read_text(encoding="utf-8")
    )
    assert implementation["source_commit_binding_pending"] is True
    assert contract["source_commit_binding_established"] is True
    assert contract["historical_implementation_record_rewritten"] is False
    assert contract["historical_source_commit_binding_pending_preserved"] is True


def test_exact_merge_source_and_future_wrapper_binding() -> None:
    contract = json.loads(
        (PACKAGE / "contract.json").read_text(encoding="utf-8")
    )
    assert contract["source_commit"] == "541b34a57297d2c5a82851bd846b583d4904fba6"
    assert contract["wrapper_commit_required"] == (
        "541b34a57297d2c5a82851bd846b583d4904fba6"
    )
    assert contract["merge_parent_count"] == 2
    assert contract["merge_parents"] == [
        "26e0328bbec433d6f2ec1841ee76a8c2c4312ccc",
        "4cf74c9632c537459b80e494e6ae88b0bc220c90",
    ]
    assert contract["runtime_source_path_count"] == 13


def test_execution_effects_remain_closed() -> None:
    contract = json.loads(
        (PACKAGE / "contract.json").read_text(encoding="utf-8")
    )
    for field in (
        "image_built",
        "image_identity_materialized",
        "execution_freeze_materialized",
        "authorization_issued",
        "authorization_used",
        "lease_or_outcome_created",
        "runtime_invoked",
        "model_code_invoked",
        "dataset_accessed",
        "host_invocation_chain_authored",
        "commit_created",
        "push_invoked",
        "pr_created",
        "pr_merged",
        "remote_main_modified",
        "qw5_opened",
    ):
        assert contract[field] is False


def test_language_map_is_semantic_not_byte_bound() -> None:
    source_registry = (PACKAGE / "source-SHA256SUMS").read_text(
        encoding="utf-8"
    )
    assert "docs/language-map.csv" not in source_registry
