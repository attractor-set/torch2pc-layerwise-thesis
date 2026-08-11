from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-attempt-005-success-transition-v1"
)


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads(path.read_text(encoding="utf-8", errors="strict")),
    )


def test_transition_package_is_self_sealed() -> None:
    assert sorted(path.name for path in PACKAGE.iterdir()) == [
        "SHA256SUMS",
        "receipt.json",
    ]
    line = (PACKAGE / "SHA256SUMS").read_text(encoding="utf-8").strip()
    digest, relative = line.split("  ", 1)
    assert relative == "receipt.json"
    assert _sha(PACKAGE / relative) == "sha256:" + digest


def test_attempt005_success_opens_only_qw5_freeze_boundary() -> None:
    receipt = _json(PACKAGE / "receipt.json")
    assert receipt["main_commit"] == (
        "7168d6ebf3fbc27f5b85e1e44a7e8252f28038b0"
    )
    assert receipt["main_tree"] == (
        "170503e1f1be147be13c90f43c1012e8bb291b18"
    )
    assert receipt["attempt_terminal"] is True
    assert receipt["attempt_retry_permitted"] is False
    assert receipt["validation_passed"] is True
    assert receipt["authorized_cell_count"] == 168
    assert receipt["reserve_probe_count"] == 28
    assert receipt["aggregate_count"] == 14
    assert receipt["all_response_comparisons_passed"] is True
    assert receipt["all_rng_matches_passed"] is True
    assert receipt["all_reserve_probes_passed"] is True
    assert receipt["all_order_effect_gates_passed"] is True
    assert receipt["all_pairs_complete"] is True
    assert receipt["order_effect_failure_count"] == 0
    assert receipt["cpu_order_effect_pass_count"] == 7
    assert receipt["rocm_order_effect_pass_count"] == 7
    assert receipt["qw_lc4_e_complete"] is True
    assert receipt["qw5_transition_permitted"] is True
    assert receipt["qw5_open"] is True
    assert receipt["qw5_scientific_image_freeze_open"] is True
    assert receipt["qw5_image_frozen"] is False
    assert receipt["scientific_execution_open"] is False
    assert receipt["c1_collection_open"] is False
    assert receipt["c2_calibration_open"] is False
    assert receipt["c3_confirmatory_open"] is False
    assert receipt["replication_open"] is False
    assert receipt["test_dataset_access"] is False
    assert receipt["publication_permitted"] is False
    assert receipt["runtime_rerun_performed"] is False
    assert receipt["next_slice"] == "QW-5-scientific-image-freeze"


def test_transition_binds_terminal_attempt005_report() -> None:
    receipt = _json(PACKAGE / "receipt.json")
    assert receipt["report_status"] == (
        "engineering_matrix_completed_validation_passed"
    )
    assert receipt["runtime_report_semantic_sha256"] == (
        "sha256:"
        "51cdc39650ed82ff896165fb81fefdb43"
        "a35c7a78b3dcc46d5f6627e601aa18d"
    )
    assert receipt["backend_sha256s_verified"] is True
    assert receipt["host_child_spawn_count"] == 1
    assert receipt["host_return_code"] == 0
    assert receipt["host_timed_out"] is False
    assert receipt["host_automatic_retry_performed"] is False
