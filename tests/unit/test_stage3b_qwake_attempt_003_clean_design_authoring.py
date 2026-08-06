from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERIFIER_PATH = ROOT / 'scripts/verify_stage3b_qwake_attempt_003_clean_design_authoring.py'
CONTRACT_PATH = ROOT / 'experiments/frozen/stage3b-qwake-attempt-003-clean-source-closure-design-authoring-v1/contract.json'
SOURCE_REGISTRY = ROOT / 'experiments/frozen/stage3b-qwake-attempt-003-clean-source-closure-design-authoring-v1/source-SHA256SUMS'


def load_verifier():
    spec = importlib.util.spec_from_file_location(
        "clean_attempt_003_design_verifier",
        VERIFIER_PATH,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_clean_design_authoring_verifies() -> None:
    module = load_verifier()
    module.verify(ROOT)


def test_language_map_is_not_byte_bound() -> None:
    registry = SOURCE_REGISTRY.read_text(encoding="utf-8")
    assert "docs/language-map.csv" not in registry


def test_contract_has_exact_clean_runtime_source_set() -> None:
    contract = json.loads(
        CONTRACT_PATH.read_text(encoding="utf-8")
    )
    paths = contract["runtime_source_registry_required_paths"]
    assert len(paths) == 13
    assert paths == sorted(paths)
    assert all("attempt_002" not in path for path in paths)
    assert all("attempt-002" not in path for path in paths)


def test_design_has_no_effect_permissions() -> None:
    contract = json.loads(
        CONTRACT_PATH.read_text(encoding="utf-8")
    )
    assert contract["implementation_authored"] is False
    assert contract["docker_build_invoked"] is False
    assert contract["runtime_invoked"] is False
    assert contract["authorization_issued"] is False
    assert contract["lease_or_outcome_created"] is False
    assert contract["remote_main_modified"] is False
