# Validate the QW-LC0 repository-freeze receipt.

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-lc0-repository-freeze-v1"
)
CONTRACT = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-lc0-semantics-scope-v1"
)

MAIN_COMMIT = "8429f54257685a879b0a44499d5fa81eab7310ea"
MAIN_FIRST_PARENT = "c429aab3995908df6054e42e2ab5ed314cb3c16d"
FREEZE_COMMIT = "715308451ac3e696d4c2209276d36853f6799d6f"
TRANSITION_COMMIT = "7c8c522d2d7849ecc9983923c6f6479a67e94bda"
CONTRACT_ID = "stage3b-qwake-lc0-semantics-scope-v1"
CONTRACT_SHA256 = "sha256:e68e953aa3d5c425678d54b8dd3b756e706e5cc1a1c4862d4c0ba0bda19bf3c3"
CONTRACT_REGISTRY_SHA256 = "sha256:dc84bed1e99526b4267ab982e3ac32fc704b628a3fb6194f6b6662649e0e4119"
RECEIPT_FILE_SHA256 = "b8a98f16e50223fa6bdc1b4ad18d7c359e968eef3684295119410b50093364a1"


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


def test_receipt_binds_merge_and_contract() -> None:
    receipt = _json(PACKAGE / "receipt.json")
    assert receipt["receipt_id"] == (
        "stage3b-qwake-lc0-repository-freeze-v1"
    )
    assert receipt["status"] == (
        "lc0_contract_verified_on_main_"
        "repository_freeze_materialized_merge_required"
    )
    assert receipt["main_commit"] == MAIN_COMMIT
    assert receipt["main_first_parent"] == MAIN_FIRST_PARENT
    assert receipt["freeze_commit"] == FREEZE_COMMIT
    assert receipt["transition_commit"] == TRANSITION_COMMIT
    assert receipt["merge_method"] == "merge-commit"
    assert receipt["contract_id"] == CONTRACT_ID
    assert receipt["contract_sha256"] == CONTRACT_SHA256
    assert (
        receipt["contract_registry_sha256"]
        == CONTRACT_REGISTRY_SHA256
    )
    assert _sha(CONTRACT / "contract.json") == CONTRACT_SHA256
    assert _sha(CONTRACT / "SHA256SUMS") == (
        CONTRACT_REGISTRY_SHA256
    )


def test_repository_freeze_keeps_lc1_and_execution_closed() -> None:
    receipt = _json(PACKAGE / "receipt.json")
    assert receipt["contract_verified_on_main"] is True
    assert receipt["freeze_tree_preserved"] is True
    assert receipt["qw_lc0_semantics_scope_frozen"] is True
    assert receipt["qw_lc0_repository_freeze_materialized"] is True
    assert receipt["qw_lc0_repository_freeze_complete"] is False
    assert receipt["qw_lc1_transition_permitted"] is False
    assert receipt["qw_lc1_open"] is False
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
        "QW-LC0-repository-freeze-merge"
    )
    assert receipt["post_merge_next_slice"] == (
        "QW-LC1-transition"
    )


def test_status_records_materialized_repository_freeze() -> None:
    markers = (
        "qwake_qw_lc0_repository_main_commit=" + MAIN_COMMIT,
        "qwake_qw_lc0_repository_freeze_materialized=true",
        "qwake_qw_lc0_repository_freeze_complete=false",
        "qwake_qw_lc1_transition_permitted=false",
        "qwake_qw_lc1_open=false",
        "qwake_local_compute_implementation_open=false",
        "qwake_local_compute_execution_open=false",
        "feature_collection_permitted=false",
        "oracle_label_generation_open=false",
        "policy_activation_permitted=false",
        "scientific_execution_open=false",
        "test_dataset_access=false",
        "publication_permitted=false",
        "qwake_next_slice=QW-LC0-repository-freeze-merge",
        "qwake_post_merge_next_slice=QW-LC1-transition",
    )
    sections = (
        (
            "STATUS.md",
            "## `QW-LC0`: фиксация состояния репозитория материализована",
        ),
        (
            "STATUS_EN.md",
            "## `QW-LC0`: repository freeze materialized",
        ),
    )
    for name, heading in sections:
        text = (ROOT / name).read_text(encoding="utf-8")
        section = text[text.index(heading):]
        for marker in markers:
            assert marker in section, (name, marker)
