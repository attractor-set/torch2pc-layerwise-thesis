# Validate the QW-LC1 repository-freeze receipt.

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-lc1-repository-freeze-v1"
)
SCHEMA = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-lc1-required-response-schema-v1"
)

MAIN_COMMIT = "59e3143ba105a5b298e2cd551b221b8f6dae96f7"
MAIN_FIRST_PARENT = "c3533fcb63ffc869faddbaa99645c9099d16d1cc"
SCHEMA_COMMIT = "de2b5a37583b22946073390caa244bee35dd793b"
TRANSITION_COMMIT = "9fcdb993c262fe34fb28af996f2373b67486effb"
SCHEMA_ID = "stage3b-qwake-lc1-required-response-schema-v1"
SCHEMA_SHA256 = "sha256:c7923249c538b29a34f8ffcfcac987b9925a911eb107a085a166ab1d7ca22992"
SCHEMA_REGISTRY_SHA256 = "sha256:4a5dca3848bd8ffb0f70013fb5c42a6f6427dd0e1752eb950f5332207b8e269f"
RECEIPT_FILE_SHA256 = "53080ac5c2dbcbb29c5e8ce5108280bd77c276befe8c6b867af98e687d4e902b"


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads(path.read_text(encoding="utf-8")),
    )


def test_repository_freeze_inventory_and_checksum() -> None:
    assert sorted(path.name for path in PACKAGE.iterdir()) == [
        "SHA256SUMS",
        "receipt.json",
    ]
    assert _sha(PACKAGE / "receipt.json") == (
        "sha256:" + RECEIPT_FILE_SHA256
    )
    assert (PACKAGE / "SHA256SUMS").read_text(encoding="utf-8") == (
        RECEIPT_FILE_SHA256 + "  receipt.json\n"
    )


def test_receipt_binds_merge_and_schema() -> None:
    receipt = _json(PACKAGE / "receipt.json")
    assert receipt["receipt_id"] == (
        "stage3b-qwake-lc1-repository-freeze-v1"
    )
    assert receipt["status"] == (
        "lc1_schema_verified_on_main_"
        "repository_freeze_materialized_merge_required"
    )
    assert receipt["main_commit"] == MAIN_COMMIT
    assert receipt["main_first_parent"] == MAIN_FIRST_PARENT
    assert receipt["schema_commit"] == SCHEMA_COMMIT
    assert receipt["transition_commit"] == TRANSITION_COMMIT
    assert receipt["merge_method"] == "merge-commit"
    assert receipt["schema_id"] == SCHEMA_ID
    assert receipt["schema_contract_sha256"] == SCHEMA_SHA256
    assert (
        receipt["schema_registry_sha256"]
        == SCHEMA_REGISTRY_SHA256
    )
    assert _sha(SCHEMA / "contract.json") == SCHEMA_SHA256
    assert _sha(SCHEMA / "SHA256SUMS") == (
        SCHEMA_REGISTRY_SHA256
    )


def test_repository_freeze_keeps_lc2_and_execution_closed() -> None:
    receipt = _json(PACKAGE / "receipt.json")
    assert receipt["schema_verified_on_main"] is True
    assert receipt["schema_tree_preserved"] is True
    assert receipt["qw_lc1_open"] is True
    assert receipt["qw_lc1_required_response_schema_frozen"] is True
    assert receipt["mandatory_observables_definition_frozen"] is True
    assert (
        receipt["response_equivalence_operator_definition_frozen"]
        is True
    )
    assert receipt["qw_lc1_repository_freeze_materialized"] is True
    assert receipt["qw_lc1_repository_freeze_complete"] is False
    assert receipt["qw_lc1_complete"] is False
    assert receipt["qw_lc2_transition_permitted"] is False
    assert receipt["resource_trajectory_schema_open"] is False
    assert receipt["measurement_to_cost_mapping_open"] is False
    assert (
        receipt["cost_equivalence_operator_definition_open"]
        is False
    )
    assert receipt["local_compute_implementation_open"] is False
    assert receipt["local_compute_execution_open"] is False
    assert receipt["feature_collection_permitted"] is False
    assert receipt["oracle_label_generation_open"] is False
    assert receipt["policy_activation_permitted"] is False
    assert receipt["scientific_image_freeze_permitted"] is False
    assert receipt["scientific_execution_open"] is False
    assert receipt["test_dataset_access"] is False
    assert receipt["publication_permitted"] is False
    assert receipt["runtime_rerun_performed"] is False
    assert receipt["next_slice"] == (
        "QW-LC1-repository-freeze-merge"
    )
    assert receipt["post_merge_next_slice"] == (
        "QW-LC2-transition"
    )


def test_status_records_materialized_repository_freeze() -> None:
    markers = (
        "qwake_qw_lc1_required_response_schema_merged=true",
        "qwake_qw_lc1_schema_main_commit=" + MAIN_COMMIT,
        "qwake_qw_lc1_schema_commit=" + SCHEMA_COMMIT,
        "qwake_qw_lc1_repository_freeze_materialized=true",
        "qwake_qw_lc1_repository_freeze_complete=false",
        "qwake_qw_lc1_complete=false",
        "qwake_qw_lc2_transition_permitted=false",
        "resource_trajectory_schema_open=false",
        "measurement_to_cost_mapping_open=false",
        "cost_equivalence_operator_definition_open=false",
        "qwake_local_compute_implementation_open=false",
        "qwake_local_compute_execution_open=false",
        "feature_collection_permitted=false",
        "oracle_label_generation_open=false",
        "policy_activation_permitted=false",
        "scientific_execution_open=false",
        "test_dataset_access=false",
        "publication_permitted=false",
        "qwake_next_slice=QW-LC1-repository-freeze-merge",
        "qwake_post_merge_next_slice=QW-LC2-transition",
    )
    sections = (
        (
            "STATUS.md",
            "## `QW-LC1`: фиксация состояния репозитория материализована",
        ),
        (
            "STATUS_EN.md",
            "## `QW-LC1`: repository freeze materialized",
        ),
    )
    for name, heading in sections:
        text = (ROOT / name).read_text(encoding="utf-8")
        section = text[text.index(heading):]
        for marker in markers:
            assert marker in section, (name, marker)
