# Validate the QW-LC2 transition receipt and closed boundary.

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-lc2-transition-v1"
)
FREEZE = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-lc1-repository-freeze-v1"
)
SCHEMA = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-lc1-required-response-schema-v1"
)

TRANSITION_RECEIPT_SHA256 = (
    "sha256:"
    "9a7e21fa573aa497e5c85ab92aade9e8"
    "4e15dc0bd05e18e948ad8fac0194df23"
)
TRANSITION_REGISTRY_SHA256 = (
    "sha256:"
    "e5991b9175ebbdc60562a4185e06464d"
    "1754d84a12aeb1415ab4e2844395775c"
)
FREEZE_RECEIPT_SHA256 = (
    "sha256:"
    "53080ac5c2dbcbb29c5e8ce5108280bd"
    "77c276befe8c6b867af98e687d4e902b"
)
FREEZE_REGISTRY_SHA256 = (
    "sha256:"
    "ff048073f59c94c023f855266352670a"
    "832440053f6078ef3acd2f3e25913068"
)
SCHEMA_CONTRACT_SHA256 = (
    "sha256:"
    "c7923249c538b29a34f8ffcfcac987b9"
    "925a911eb107a085a166ab1d7ca22992"
)
SCHEMA_REGISTRY_SHA256 = (
    "sha256:"
    "4a5dca3848bd8ffb0f70013fb5c42a6"
    "f6427dd0e1752eb950f5332207b8e269f"
)


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads(path.read_text(encoding="utf-8", errors="strict")),
    )


def test_transition_inventory_and_checksum() -> None:
    assert sorted(path.name for path in PACKAGE.iterdir()) == [
        "SHA256SUMS",
        "receipt.json",
    ]
    assert _sha(PACKAGE / "receipt.json") == TRANSITION_RECEIPT_SHA256
    assert _sha(PACKAGE / "SHA256SUMS") == TRANSITION_REGISTRY_SHA256


def test_transition_binds_completed_lc1_chain() -> None:
    receipt = _json(PACKAGE / "receipt.json")
    assert receipt["transition_id"] == (
        "stage3b-qwake-lc2-transition-v1"
    )
    assert receipt["main_commit"] == (
        "9d073bc3c90eeda53ca03d0f7762b65da8749269"
    )
    assert receipt["main_first_parent"] == (
        "59e3143ba105a5b298e2cd551b221b8f6dae96f7"
    )
    assert receipt["lc1_repository_freeze_commit"] == (
        "631f940965058a7ef9071329bf3cdd02f5de8615"
    )
    assert receipt["schema_commit"] == (
        "de2b5a37583b22946073390caa244bee35dd793b"
    )
    assert receipt["post_merge_verification_passed"] is True
    assert receipt["qw_lc1_repository_freeze_complete"] is True
    assert receipt["qw_lc1_complete"] is True
    assert _sha(FREEZE / "receipt.json") == FREEZE_RECEIPT_SHA256
    assert _sha(FREEZE / "SHA256SUMS") == FREEZE_REGISTRY_SHA256
    assert _sha(SCHEMA / "contract.json") == SCHEMA_CONTRACT_SHA256
    assert _sha(SCHEMA / "SHA256SUMS") == SCHEMA_REGISTRY_SHA256


def test_lc2_scope_is_finite_and_lc3_is_deferred() -> None:
    receipt = _json(PACKAGE / "receipt.json")
    assert receipt["qw_lc2_scope"] == [
        "resource_trajectory_measurement_schema",
        "measurement_to_cost_mapping",
        "cost_vector_and_equivalence_operator",
    ]
    assert set(receipt["excluded_from_qw_lc2"]) == {
        "local_compute_implementation",
        "local_compute_execution",
        "matched_shadow_validation",
        "state_identity",
        "rng_restoration",
        "fallback_suffix_validation",
        "feature_collection",
        "oracle_label_generation",
        "policy_activation",
        "scientific_execution",
        "test_dataset_access",
        "publication",
    }


def test_transition_keeps_lc2_and_execution_closed() -> None:
    receipt = _json(PACKAGE / "receipt.json")
    assert receipt["qw_lc2_transition_permitted"] is True
    assert receipt["qw_lc2_transition_materialized"] is True
    assert receipt["qw_lc2_transition_complete"] is False
    assert receipt["qw_lc2_open"] is False
    assert receipt["resource_trajectory_schema_open"] is False
    assert receipt["measurement_to_cost_mapping_open"] is False
    assert receipt["cost_equivalence_operator_definition_open"] is False
    assert receipt["local_compute_implementation_open"] is False
    assert receipt["local_compute_execution_open"] is False
    assert receipt["feature_collection_permitted"] is False
    assert receipt["oracle_label_generation_open"] is False
    assert receipt["policy_activation_permitted"] is False
    assert receipt["scientific_execution_open"] is False
    assert receipt["test_dataset_access"] is False
    assert receipt["publication_permitted"] is False
    assert receipt["runtime_rerun_performed"] is False
    assert receipt["next_slice"] == "QW-LC2-transition-merge"
    assert receipt["post_merge_next_slice"] == (
        "QW-LC2-resource-cost-contract"
    )


def test_status_records_materialized_lc2_transition() -> None:
    markers = (
        "qwake_qw_lc1_complete=true",
        "qwake_qw_lc2_transition_permitted=true",
        "qwake_qw_lc2_transition_materialized=true",
        "qwake_qw_lc2_transition_complete=false",
        "qwake_qw_lc2_open=false",
        "resource_trajectory_schema_open=false",
        "measurement_to_cost_mapping_open=false",
        "cost_equivalence_operator_definition_open=false",
        "qwake_local_compute_implementation_open=false",
        "qwake_local_compute_execution_open=false",
        "scientific_execution_open=false",
        "test_dataset_access=false",
        "publication_permitted=false",
        "qwake_next_slice=QW-LC2-transition-merge",
        "qwake_post_merge_next_slice=QW-LC2-resource-cost-contract",
    )
    sections = (
        ("STATUS.md", "## `QW-LC2`: переход материализован"),
        ("STATUS_EN.md", "## `QW-LC2`: transition materialized"),
    )
    for name, heading in sections:
        text = (ROOT / name).read_text(
            encoding="utf-8", errors="strict"
        )
        section = text[text.index(heading) :]
        for marker in markers:
            assert marker in section, (name, marker)
