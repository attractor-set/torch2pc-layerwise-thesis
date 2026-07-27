# Validate the QW-LC3 repository-freeze receipt.

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-lc3-repository-freeze-v1"
)
CONTRACT = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-lc3-matched-shadow-validation-contract-v1"
)
TRANSITION = ROOT / "experiments/frozen/stage3b-qwake-lc3-transition-v1"

MAIN_COMMIT = "71e73f56408c720334b8fa03e7133762c8bbcc43"
MAIN_FIRST_PARENT = "a7e0c4ec1978042d68abc7437e3005e4295e75ff"
CONTRACT_COMMIT = "fb3f1cd4a4d3b4261db1179badcc1ccacddfe936"
TRANSITION_COMMIT = "a8993e3a996317eeb44270ee37e0e879537d5d65"
CONTRACT_ID = "stage3b-qwake-lc3-matched-shadow-validation-contract-v1"
CONTRACT_SHA256 = "sha256:e1512f29b3e3e3882001172df360e895e6e628b8ea8e4103b9574990775dd5d8"
CONTRACT_REGISTRY_SHA256 = "sha256:2b001f3002add8d55ce75b02b1caba6bd3c655d177aeb02fe09026e2054dcef1"
TRANSITION_RECEIPT_SHA256 = "sha256:c541703f8bc1d449aed88f175b83b9fc03e2574acb5c2be715b157be68733602"
TRANSITION_REGISTRY_SHA256 = "sha256:715ed365105aa86d165b8d4911a7a16766972c19f637e78b424398283e34663d"
RECEIPT_FILE_SHA256 = "6b27ab3ace9ef061c76e3c4bda87943de9f1d31a5dc65f90be00863438da21cd"


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads(path.read_text(encoding="utf-8", errors="strict")),
    )


def test_repository_freeze_inventory_and_checksum() -> None:
    assert sorted(path.name for path in PACKAGE.iterdir()) == [
        "SHA256SUMS",
        "receipt.json",
    ]
    assert _sha(PACKAGE / "receipt.json") == (
        "sha256:" + RECEIPT_FILE_SHA256
    )
    assert (PACKAGE / "SHA256SUMS").read_text(
        encoding="utf-8", errors="strict"
    ) == RECEIPT_FILE_SHA256 + "  receipt.json\n"


def test_receipt_binds_merge_contract_and_transition() -> None:
    receipt = _json(PACKAGE / "receipt.json")
    assert receipt["receipt_id"] == (
        "stage3b-qwake-lc3-repository-freeze-v1"
    )
    assert receipt["status"] == (
        "lc3_contract_verified_on_main_"
        "repository_freeze_materialized_merge_required"
    )
    assert receipt["main_commit"] == MAIN_COMMIT
    assert receipt["main_first_parent"] == MAIN_FIRST_PARENT
    assert receipt["contract_commit"] == CONTRACT_COMMIT
    assert receipt["transition_commit"] == TRANSITION_COMMIT
    assert receipt["merge_method"] == "merge-commit"
    assert receipt["contract_id"] == CONTRACT_ID
    assert receipt["contract_sha256"] == CONTRACT_SHA256
    assert receipt["contract_registry_sha256"] == (
        CONTRACT_REGISTRY_SHA256
    )
    assert receipt["transition_receipt_sha256"] == (
        TRANSITION_RECEIPT_SHA256
    )
    assert receipt["transition_registry_sha256"] == (
        TRANSITION_REGISTRY_SHA256
    )
    assert _sha(CONTRACT / "contract.json") == CONTRACT_SHA256
    assert _sha(CONTRACT / "SHA256SUMS") == CONTRACT_REGISTRY_SHA256
    assert _sha(TRANSITION / "receipt.json") == TRANSITION_RECEIPT_SHA256
    assert _sha(TRANSITION / "SHA256SUMS") == TRANSITION_REGISTRY_SHA256


def test_repository_freeze_keeps_lc4_and_execution_closed() -> None:
    receipt = _json(PACKAGE / "receipt.json")
    assert receipt["contract_verified_on_main"] is True
    assert receipt["contract_tree_preserved"] is True
    assert receipt["qw_lc3_open"] is True
    assert (
        receipt["qw_lc3_matched_shadow_validation_contract_frozen"]
        is True
    )
    assert (
        receipt["qw_lc3_matched_shadow_validation_contract_merged"]
        is True
    )
    assert (
        receipt["qw_lc3_matched_shadow_validation_contract_complete"]
        is True
    )
    assert receipt["matched_shadow_validation_protocol_frozen"] is True
    assert receipt["opaque_state_ref_definition_frozen"] is True
    assert receipt["rng_restoration_protocol_frozen"] is True
    assert receipt["exact_reserve_suffix_validation_frozen"] is True
    assert receipt["repeat_aggregation_protocol_frozen"] is True
    assert receipt["qw_lc3_repository_freeze_materialized"] is True
    assert receipt["qw_lc3_repository_freeze_complete"] is False
    assert receipt["qw_lc3_complete"] is False
    assert receipt["qw_lc4_implementation_permitted"] is False
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
    assert receipt["next_slice"] == "QW-LC3-repository-freeze-merge"
    assert receipt["post_merge_next_slice"] == "QW-LC4-I"


def test_status_records_materialized_repository_freeze() -> None:
    markers = (
        "qwake_qw_lc3_matched_shadow_validation_contract_merged=true",
        "qwake_qw_lc3_matched_shadow_validation_contract_complete=true",
        "qwake_qw_lc3_repository_main_commit=" + MAIN_COMMIT,
        "qwake_qw_lc3_contract_commit=" + CONTRACT_COMMIT,
        "qwake_qw_lc3_repository_freeze_materialized=true",
        "qwake_qw_lc3_repository_freeze_complete=false",
        "qwake_qw_lc3_complete=false",
        "qwake_qw_lc4_implementation_permitted=false",
        "matched_shadow_validation_protocol_frozen=true",
        "opaque_state_ref_definition_frozen=true",
        "rng_restoration_protocol_frozen=true",
        "exact_reserve_suffix_validation_frozen=true",
        "repeat_aggregation_protocol_frozen=true",
        "qwake_local_compute_implementation_open=false",
        "qwake_local_compute_execution_open=false",
        "feature_collection_permitted=false",
        "oracle_label_generation_open=false",
        "policy_activation_permitted=false",
        "scientific_execution_open=false",
        "test_dataset_access=false",
        "publication_permitted=false",
        "runtime_rerun_performed=false",
        "qwake_next_slice=QW-LC3-repository-freeze-merge",
        "qwake_post_merge_next_slice=QW-LC4-I",
    )
    sections = (
        (
            "STATUS.md",
            "## `QW-LC3`: фиксация состояния репозитория материализована",
        ),
        (
            "STATUS_EN.md",
            "## `QW-LC3`: repository freeze materialized",
        ),
    )
    for name, heading in sections:
        text = (ROOT / name).read_text(encoding="utf-8", errors="strict")
        section = text[text.index(heading):]
        for marker in markers:
            assert marker in section, (name, marker)
