from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FREEZE = (
    ROOT
    / "experiments"
    / "frozen"
    / "stage3b-qwake-lc2-repository-freeze-v1"
)
CONTRACT = (
    ROOT
    / "experiments"
    / "frozen"
    / "stage3b-qwake-lc2-resource-cost-contract-v1"
)


def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def receipt() -> dict[str, object]:
    return json.loads(
        (FREEZE / "receipt.json").read_text(
            encoding="utf-8",
            errors="strict",
        )
    )


def test_inventory_and_registry() -> None:
    assert sorted(path.name for path in FREEZE.iterdir()) == [
        "SHA256SUMS",
        "receipt.json",
    ]
    expected = (
        hashlib.sha256((FREEZE / "receipt.json").read_bytes()).hexdigest()
        + "  receipt.json\n"
    )
    assert (FREEZE / "SHA256SUMS").read_text(
        encoding="utf-8",
        errors="strict",
    ) == expected


def test_identity_and_digest_binding() -> None:
    data = receipt()
    assert data["receipt_id"] == (
        "stage3b-qwake-lc2-repository-freeze-v1"
    )
    assert data["main_commit"] == "8f24229bcf19736086fe6f0340bda26dd533936a"
    assert data["main_first_parent"] == "858403cbb2423ad3427ab7a042266880ca34c0b7"
    assert data["resource_cost_commit"] == "3f1682765089b0819dcaaf9bb449c4c1bd155142"
    assert data["transition_commit"] == "9e8f33a5fcf5399dcf834bdedefa5ca404f89fef"
    assert data["contract_id"] == "stage3b-qwake-lc2-resource-cost-contract-v1"
    assert data["contract_sha256"] == "sha256:313dc969ab59db20ee27976d3158fca23ce511801e0dc7700dde0d2d002ab69d"
    assert data["contract_registry_sha256"] == (
        "sha256:61763ad19c968dbad3eef16e5bee3a11d9dbfad74a7bf45dfc2e64cc022cf311"
    )
    assert sha(CONTRACT / "contract.json") == data["contract_sha256"]
    assert sha(CONTRACT / "SHA256SUMS") == (
        data["contract_registry_sha256"]
    )


def test_fail_closed_boundary() -> None:
    data = receipt()
    assert data["contract_verified_on_main"] is True
    assert data["contract_tree_preserved"] is True
    assert data["qw_lc2_resource_cost_contract_complete"] is True
    assert data["qw_lc2_repository_freeze_materialized"] is True
    assert data["qw_lc2_repository_freeze_complete"] is False
    assert data["qw_lc2_complete"] is False
    assert data["qw_lc3_transition_permitted"] is False
    assert data["local_compute_implementation_open"] is False
    assert data["local_compute_execution_open"] is False
    assert data["scientific_execution_open"] is False
    assert data["test_dataset_access"] is False
    assert data["publication_permitted"] is False
    assert data["runtime_rerun_performed"] is False


def test_status_markers() -> None:
    required = (
        "qwake_qw_lc2_repository_freeze_materialized=true",
        "qwake_qw_lc2_repository_freeze_complete=false",
        "qwake_qw_lc2_complete=false",
        "qwake_qw_lc3_transition_permitted=false",
        "qwake_local_compute_implementation_open=false",
        "qwake_local_compute_execution_open=false",
        "runtime_rerun_performed=false",
        "qwake_next_slice=QW-LC2-repository-freeze-merge",
        "qwake_post_merge_next_slice=QW-LC3-transition",
    )
    for relative in ("STATUS.md", "STATUS_EN.md"):
        text = (ROOT / relative).read_text(
            encoding="utf-8",
            errors="strict",
        )
        for marker in required:
            assert marker in text
