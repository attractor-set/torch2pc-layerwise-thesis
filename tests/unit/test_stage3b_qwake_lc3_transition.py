# Validate the QW-LC3 transition receipt and closed boundary.

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-lc3-transition-v1"
)
FREEZE = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-lc2-repository-freeze-v1"
)
CONTRACT = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-lc2-resource-cost-contract-v1"
)
RESPONSE_SCHEMA = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-lc1-required-response-schema-v1"
)

TRANSITION_RECEIPT_SHA256 = (
    "sha256:"
    "c541703f8bc1d449aed88f175b83b9fc"
    "03e2574acb5c2be715b157be68733602"
)
TRANSITION_REGISTRY_SHA256 = (
    "sha256:"
    "715ed365105aa86d165b8d4911a7a167"
    "66972c19f637e78b424398283e34663d"
)
FREEZE_RECEIPT_SHA256 = (
    "sha256:"
    "2e27d88557451e56573d621e8e2f8d5"
    "c0c2366dd40f7aa8176068dd390f28e30"
)
FREEZE_REGISTRY_SHA256 = (
    "sha256:"
    "c31061bb5ee1d8983108f8d58c8af236"
    "c22274938ad30376827e9dca93122211"
)
CONTRACT_SHA256 = (
    "sha256:"
    "313dc969ab59db20ee27976d3158fca2"
    "3ce511801e0dc7700dde0d2d002ab69d"
)
CONTRACT_REGISTRY_SHA256 = (
    "sha256:"
    "61763ad19c968dbad3eef16e5bee3a11"
    "d9dbfad74a7bf45dfc2e64cc022cf311"
)
RESPONSE_SCHEMA_SHA256 = (
    "sha256:"
    "c7923249c538b29a34f8ffcfcac987b9"
    "925a911eb107a085a166ab1d7ca22992"
)
RESPONSE_SCHEMA_REGISTRY_SHA256 = (
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


def test_transition_binds_completed_lc2_chain() -> None:
    receipt = _json(PACKAGE / "receipt.json")
    assert receipt["transition_id"] == (
        "stage3b-qwake-lc3-transition-v1"
    )
    assert receipt["main_commit"] == (
        "4f7c533047214398e7ec4dde9d58b5fc06964b90"
    )
    assert receipt["main_first_parent"] == (
        "8f24229bcf19736086fe6f0340bda26dd533936a"
    )
    assert receipt["lc2_repository_freeze_commit"] == (
        "3f4310a05de5b7cd3db0cdb5c8f7cf4bbcb09150"
    )
    assert receipt["post_merge_verification_passed"] is True
    assert receipt["lc2_repository_freeze_complete"] is True
    assert receipt["qw_lc2_complete"] is True
    assert _sha(FREEZE / "receipt.json") == FREEZE_RECEIPT_SHA256
    assert _sha(FREEZE / "SHA256SUMS") == FREEZE_REGISTRY_SHA256
    assert _sha(CONTRACT / "contract.json") == CONTRACT_SHA256
    assert _sha(CONTRACT / "SHA256SUMS") == CONTRACT_REGISTRY_SHA256
    assert _sha(RESPONSE_SCHEMA / "contract.json") == RESPONSE_SCHEMA_SHA256
    assert (
        _sha(RESPONSE_SCHEMA / "SHA256SUMS")
        == RESPONSE_SCHEMA_REGISTRY_SHA256
    )


def test_lc3_scope_is_finite_and_lc4_is_deferred() -> None:
    receipt = _json(PACKAGE / "receipt.json")
    assert receipt["qw_lc3_scope"] == [
        "matched_shadow_validation_protocol",
        "opaque_state_ref_construction_and_validation",
        "rng_snapshot_restoration_and_post_state_match",
        "complete_exact_reserve_suffix_validation",
        "repeat_order_and_paired_aggregation_protocol",
    ]
    assert set(receipt["excluded_from_qw_lc3"]) == {
        "candidate_implementation",
        "local_compute_execution",
        "feature_collection",
        "oracle_label_generation",
        "policy_activation",
        "runtime_authorization",
        "engineering_execution",
        "scientific_execution",
        "test_dataset_access",
        "publication",
    }


def test_transition_keeps_lc3_and_execution_closed() -> None:
    receipt = _json(PACKAGE / "receipt.json")
    assert receipt["qw_lc3_transition_permitted"] is True
    assert receipt["qw_lc3_transition_materialized"] is True
    assert receipt["qw_lc3_transition_complete"] is False
    assert receipt["qw_lc3_open"] is False
    assert receipt["matched_shadow_validation_protocol_open"] is False
    assert receipt["opaque_state_ref_definition_open"] is False
    assert receipt["rng_restoration_protocol_open"] is False
    assert receipt["exact_reserve_suffix_validation_open"] is False
    assert receipt["repeat_aggregation_protocol_open"] is False
    assert receipt["local_compute_implementation_open"] is False
    assert receipt["local_compute_execution_open"] is False
    assert receipt["feature_collection_permitted"] is False
    assert receipt["oracle_label_generation_open"] is False
    assert receipt["policy_activation_permitted"] is False
    assert receipt["scientific_execution_open"] is False
    assert receipt["test_dataset_access"] is False
    assert receipt["publication_permitted"] is False
    assert receipt["runtime_rerun_performed"] is False
    assert receipt["next_slice"] == "QW-LC3-transition-merge"
    assert receipt["post_merge_next_slice"] == (
        "QW-LC3-matched-shadow-validation-contract"
    )


def test_status_records_materialized_lc3_transition() -> None:
    markers = (
        "qwake_qw_lc2_repository_freeze_complete=true",
        "qwake_qw_lc2_complete=true",
        "qwake_qw_lc3_transition_permitted=true",
        "qwake_qw_lc3_transition_materialized=true",
        "qwake_qw_lc3_transition_complete=false",
        "qwake_qw_lc3_open=false",
        "matched_shadow_validation_protocol_open=false",
        "opaque_state_ref_definition_open=false",
        "rng_restoration_protocol_open=false",
        "exact_reserve_suffix_validation_open=false",
        "repeat_aggregation_protocol_open=false",
        "qwake_local_compute_implementation_open=false",
        "qwake_local_compute_execution_open=false",
        "scientific_execution_open=false",
        "test_dataset_access=false",
        "publication_permitted=false",
        "qwake_next_slice=QW-LC3-transition-merge",
        (
            "qwake_post_merge_next_slice="
            "QW-LC3-matched-shadow-validation-contract"
        ),
    )
    sections = (
        ("STATUS.md", "## `QW-LC3`: переход материализован"),
        ("STATUS_EN.md", "## `QW-LC3`: transition materialized"),
    )
    for name, heading in sections:
        text = (ROOT / name).read_text(
            encoding="utf-8", errors="strict"
        )
        section = text[text.index(heading) :]
        for marker in markers:
            assert marker in section, (name, marker)
