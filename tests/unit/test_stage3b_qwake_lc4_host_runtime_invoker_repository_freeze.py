# Validate the QW-LC4-E host-runtime-invoker repository freeze.

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-"
    "repository-freeze-v1"
)
IMPLEMENTATION_PACKAGE = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-"
    "implementation-v1"
)
MODULE = ROOT / (
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_host_runtime_invoker_implementation.py"
)
VERIFIER = ROOT / (
    "scripts/"
    "verify_stage3b_qwake_lc4_host_runtime_invoker_implementation.py"
)
TEST = ROOT / (
    "tests/unit/"
    "test_stage3b_qwake_lc4_host_runtime_invoker_implementation.py"
)

MERGE_COMMIT = "da51c8d858c541372525125640db99062041fc20"
MERGE_PARENT_1 = "7f1655346bca77834d73a660c9857f1ff23b826c"
MERGE_PARENT_2 = "181abda36465d3a91db5970e684938266200a798"
IMPLEMENTATION_STATE_SHA256 = (
    "sha256:1f5f31d4f220bbf074736f1de0b78a5dafa2849188ac337704d5cc704668fdf4"
)
CONTRACT_SHA256 = (
    "sha256:607bf719d8a976569c50d7cfe8604ab341843dad00d3eef8784e1dc6cfd9b88d"
)
MODULE_SHA256 = (
    "sha256:dc55bc711f6126eaf7fd231439a2149e991027a751e58d2c6d3450a9d5ae9b14"
)
VERIFIER_SHA256 = (
    "sha256:eddc19915c3d258671c6a804b1f2a17cfdcecbea264295632cf7200de2742268"
)
TEST_SHA256 = (
    "sha256:b7cd39f595d8c39a9f96dde342134240d0eb5a4b6a72fe85464d0ae52144ebac"
)
IMPLEMENTATION_RECORD_SHA256 = (
    "sha256:beb24e0fda734aa4a9a74e7887349944f27805817def0f07e33618f566e505e1"
)
IMPLEMENTATION_REGISTRY_SHA256 = (
    "sha256:d04ad77ad59ee289fab4ca0bf1a0a44009c47ecb8af058ccebf77b9fe58c173a"
)
RECEIPT_SHA256 = (
    "sha256:6485bd00335fe88e961dc9aa23daf0d27c0cbaa4fc4963af7a463b1ab9c3af58"
)


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
    assert _sha(PACKAGE / "receipt.json") == RECEIPT_SHA256
    assert (PACKAGE / "SHA256SUMS").read_text(
        encoding="utf-8", errors="strict"
    ) == RECEIPT_SHA256.removeprefix("sha256:") + "  receipt.json\n"


def test_receipt_binds_exact_merge_and_implementation() -> None:
    receipt = _json(PACKAGE / "receipt.json")
    assert receipt["receipt_id"] == (
        "stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-"
        "repository-freeze-v1"
    )
    assert receipt["implementation_merge_commit"] == MERGE_COMMIT
    assert receipt["implementation_merge_parent_1"] == MERGE_PARENT_1
    assert receipt["implementation_merge_parent_2"] == MERGE_PARENT_2
    assert receipt["implementation_head_commit"] == MERGE_PARENT_2
    assert receipt["implementation_pr_number"] == 136
    assert receipt["implementation_commit_count"] == 2
    assert receipt["implementation_file_count"] == 16
    assert receipt["merge_method"] == "merge-commit"
    assert receipt["implementation_tree_preserved"] is True
    assert receipt["implementation_verified_on_main"] is True
    assert receipt["implementation_state_sha256"] == (
        IMPLEMENTATION_STATE_SHA256
    )
    assert receipt["host_runtime_invoker_contract_sha256"] == (
        CONTRACT_SHA256
    )
    assert receipt["module_sha256"] == MODULE_SHA256
    assert receipt["verifier_sha256"] == VERIFIER_SHA256
    assert receipt["test_sha256"] == TEST_SHA256
    assert receipt["implementation_record_sha256"] == (
        IMPLEMENTATION_RECORD_SHA256
    )
    assert receipt["implementation_registry_sha256"] == (
        IMPLEMENTATION_REGISTRY_SHA256
    )
    assert _sha(MODULE) == MODULE_SHA256
    assert _sha(VERIFIER) == VERIFIER_SHA256
    assert _sha(TEST) == TEST_SHA256
    assert _sha(IMPLEMENTATION_PACKAGE / "implementation.json") == (
        IMPLEMENTATION_RECORD_SHA256
    )
    assert _sha(IMPLEMENTATION_PACKAGE / "SHA256SUMS") == (
        IMPLEMENTATION_REGISTRY_SHA256
    )


def test_repository_freeze_records_verification_and_closed_boundary() -> None:
    receipt = _json(PACKAGE / "receipt.json")
    assert receipt["ci_check_count"] == 2
    assert receipt["ci_success_count"] == 2
    assert receipt["ci_pending_count"] == 0
    assert receipt["ci_failure_count"] == 0
    assert receipt["targeted_test_count"] == 139
    assert receipt["full_test_count"] == 1186
    assert receipt["full_test_warning_count"] == 14
    assert receipt["host_runtime_invoker_implementation_present"] is True
    assert receipt["host_runtime_invoker_present"] is True
    assert receipt["host_runtime_invoker_executable"] is True
    assert receipt["host_docker_run_implemented"] is True
    assert receipt["repository_freeze_branch_open"] is True
    assert receipt["repository_freeze_materialized"] is True
    assert receipt["repository_freeze_complete"] is False
    assert receipt["one_shot_engineering_invocation_permitted"] is False
    assert receipt["branch_runtime_execution_permitted"] is False
    assert receipt["execution_lease_materialized"] is False
    assert receipt["authorization_consumed"] is False
    assert receipt["runtime_execution_started"] is False
    assert receipt["runtime_execution_performed"] is False
    assert receipt["engineering_evidence_present"] is False
    assert receipt["scientific_execution_open"] is False
    assert receipt["test_dataset_access"] is False
    assert receipt["publication_permitted"] is False
    assert receipt["local_compute_execution_open"] is False
    assert receipt["image_inspection_performed"] is False
    assert receipt["docker_run_performed"] is False
    assert receipt["runtime_rerun_performed"] is False
    assert receipt["next_slice"] == (
        "QW-LC4-E-one-shot-host-runtime-invoker-"
        "repository-freeze-merge"
    )
    assert receipt["post_merge_next_slice"] == (
        "QW-LC4-E-one-shot-engineering-invocation"
    )


def test_status_and_documentation_record_repository_freeze() -> None:
    markers = (
        "qwake_host_runtime_invoker_repository_main_commit=" + MERGE_COMMIT,
        "qwake_host_runtime_invoker_implementation_head=" + MERGE_PARENT_2,
        "qwake_host_runtime_invoker_repository_freeze_materialized=true",
        "qwake_host_runtime_invoker_repository_freeze_complete=false",
        "ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false",
        "BRANCH_RUNTIME_EXECUTION_PERMITTED=false",
        "EXECUTION_LEASE_MATERIALIZED=false",
        "AUTHORIZATION_CONSUMED=false",
        "RUNTIME_EXECUTION_STARTED=false",
        "RUNTIME_EXECUTION_PERFORMED=false",
        "LOCAL_COMPUTE_EXECUTION_OPEN=false",
        "IMAGE_INSPECTION_PERFORMED=false",
        "DOCKER_RUN_PERFORMED=false",
        "RUNTIME_RERUN_PERFORMED=false",
    )
    sections = (
        (
            "STATUS.md",
            "## `QW-LC4-E`: фиксация состояния репозитория "
            "хостового исполнителя материализована",
        ),
        (
            "STATUS_EN.md",
            "## `QW-LC4-E`: host-runtime-invoker "
            "repository freeze materialized",
        ),
    )
    for name, heading in sections:
        text = (ROOT / name).read_text(encoding="utf-8", errors="strict")
        section = text[text.index(heading):]
        for marker in markers:
            assert marker in section, (name, marker)
    assert (
        ROOT
        / "docs/decisions/"
        "ADR-076-stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-"
        "repository-freeze.md"
    ).is_file()
    assert (
        ROOT
        / "docs/decisions/"
        "ADR-076-stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-"
        "repository-freeze_EN.md"
    ).is_file()
