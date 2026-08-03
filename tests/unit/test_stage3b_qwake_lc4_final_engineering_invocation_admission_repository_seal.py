# Validate the final engineering-invocation admission repository seal.

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-final-engineering-invocation-admission-"
    "repository-seal-v1"
)
ADMISSION_PACKAGE = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-final-engineering-invocation-admission-"
    "authoring-v1"
)
MODULE = ROOT / (
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_final_engineering_invocation_admission.py"
)
VERIFIER = ROOT / (
    "scripts/"
    "verify_stage3b_qwake_lc4_final_engineering_invocation_admission.py"
)
ADMISSION_TEST = ROOT / (
    "tests/unit/"
    "test_stage3b_qwake_lc4_final_engineering_invocation_admission.py"
)

MAIN_COMMIT = "d2539eb440e758c1f29b935f8599561bec7126bc"
BASE_COMMIT = "5ee7d33b2d6a9092b2db473040b92ad8cda7e08f"
AUTHORING_COMMIT = "1ef9b741ca63ec38aafbdffda57160232196055f"
HEAD_COMMIT = "b81c11971f1e9b78e59dd39c4d182722a3001044"
RECEIPT_SHA256 = "sha256:0445b537efc6d8266d6a20b68ba2963090668dac6d280e9b270a0f927b8ff161"
ADMISSION_RECORD_SHA256 = "sha256:dfc4bcd7505328bd69d4fd88b79c8ea06caa7c8a0b8871354dc7b7488e999114"
ADMISSION_SOURCE_REGISTRY_SHA256 = (
    "sha256:adfb8f5dc11b6da6614f6842b3e535c68b2eb130f914e58d0c41d302854f67c9"
)
ADMISSION_REGISTRY_SHA256 = "sha256:2c353c053e0968ee87afc0f09da7c2aadb898c9ef80a274206f38650be7ff627"
ADMISSION_MODULE_SHA256 = "sha256:da8182fe6eb35a6d4030545ae895cc0820cb99f34db2b920813f5f4f8169708c"
ADMISSION_VERIFIER_SHA256 = "sha256:946059c4022d848978f697027c854cc0b8954e590d1e92a84c03e149b8744cad"
ADMISSION_TEST_SHA256 = "sha256:8a6c773d264300d3083e8161340bbd5355c96ee6eb6c4974ff59843deeaba73f"


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads(path.read_text(encoding="utf-8", errors="strict")),
    )


def test_repository_seal_inventory_and_checksum() -> None:
    assert sorted(path.name for path in PACKAGE.iterdir()) == [
        "SHA256SUMS",
        "receipt.json",
    ]
    assert _sha(PACKAGE / "receipt.json") == RECEIPT_SHA256
    assert (PACKAGE / "SHA256SUMS").read_text(
        encoding="utf-8", errors="strict"
    ) == RECEIPT_SHA256.removeprefix("sha256:") + "  receipt.json\n"


def test_receipt_binds_exact_pr_merge_and_admission_artifacts() -> None:
    receipt = _json(PACKAGE / "receipt.json")
    assert receipt["receipt_id"] == (
        "stage3b-qwake-lc4-e-final-engineering-invocation-admission-"
        "repository-seal-v1"
    )
    assert receipt["admission_pr_number"] == 169
    assert receipt["admission_base_commit"] == BASE_COMMIT
    assert receipt["admission_authoring_commit"] == AUTHORING_COMMIT
    assert receipt["admission_head_commit"] == HEAD_COMMIT
    assert receipt["admission_merge_commit"] == MAIN_COMMIT
    assert receipt["admission_merge_parent_1"] == BASE_COMMIT
    assert receipt["admission_merge_parent_2"] == HEAD_COMMIT
    assert receipt["admission_merged_at_utc"] == "2026-08-03T14:16:22Z"
    assert receipt["admission_commit_count"] == 2
    assert receipt["admission_file_count"] == 17
    assert receipt["merge_method"] == "merge-commit"
    assert receipt["admission_tree_preserved"] is True
    assert receipt["admission_verified_on_main"] is True
    assert receipt["admission_semantic_sha256"] == "sha256:a66fd1c74b71834026af0bd699e48bc54c5aab368f1fe02a13be164aefe7f942"
    assert receipt["admission_record_sha256"] == ADMISSION_RECORD_SHA256
    assert receipt["admission_source_registry_sha256"] == (
        ADMISSION_SOURCE_REGISTRY_SHA256
    )
    assert receipt["admission_registry_sha256"] == ADMISSION_REGISTRY_SHA256
    assert receipt["admission_module_sha256"] == ADMISSION_MODULE_SHA256
    assert receipt["admission_verifier_sha256"] == ADMISSION_VERIFIER_SHA256
    assert receipt["admission_test_sha256"] == ADMISSION_TEST_SHA256
    assert _sha(ADMISSION_PACKAGE / "admission.json") == (
        ADMISSION_RECORD_SHA256
    )
    assert _sha(ADMISSION_PACKAGE / "source-SHA256SUMS") == (
        ADMISSION_SOURCE_REGISTRY_SHA256
    )
    assert _sha(ADMISSION_PACKAGE / "SHA256SUMS") == (
        ADMISSION_REGISTRY_SHA256
    )
    assert _sha(MODULE) == ADMISSION_MODULE_SHA256
    assert _sha(VERIFIER) == ADMISSION_VERIFIER_SHA256
    assert _sha(ADMISSION_TEST) == ADMISSION_TEST_SHA256


def test_repository_seal_records_verified_state_and_closed_boundary() -> None:
    receipt = _json(PACKAGE / "receipt.json")
    assert receipt["final_head_checks_acceptable"] is True
    assert receipt["post_merge_ruff_passed"] is True
    assert receipt["post_merge_static_guard_count"] == 4
    assert receipt["post_merge_targeted_test_count"] == 23
    assert receipt["repository_seal_branch_open"] is True
    assert receipt["repository_seal_materialized"] is True
    assert receipt["repository_seal_complete"] is False
    assert receipt["authorization_authoring_permitted"] is False
    assert receipt["authorization_record_present"] is False
    assert receipt["authorization_issued"] is False
    assert receipt["authorization_consumed"] is False
    assert receipt["operator_phrase_reserved"] is False
    assert receipt["invocation_command_materialized"] is False
    assert receipt["invocation_permitted"] is False
    assert receipt["invocation_started"] is False
    assert receipt["invocation_performed"] is False
    assert receipt["execution_lease_v1_present"] is False
    assert receipt["execution_lease_v2_present"] is False
    assert receipt["durable_host_outcome_present"] is False
    assert receipt["runtime_output_present"] is False
    assert receipt["extension_engineering_report_present"] is False
    assert receipt["qw_lc4_e_complete"] is False
    assert receipt["qw5_transition_permitted"] is False
    assert receipt["qw5_scientific_image_freeze_open"] is False
    assert receipt["local_compute_execution_open"] is False
    assert receipt["test_dataset_access"] is False
    assert receipt["publication_permitted"] is False
    assert receipt["image_inspection_performed"] is False
    assert receipt["docker_run_performed"] is False
    assert receipt["model_code_invoked"] is False
    assert receipt["child_process_created"] is False
    assert receipt["runtime_rerun_performed"] is False
    assert receipt["runtime_entrypoint"] == "invoke_lease_bound_host_runtime"
    assert receipt["next_slice"] == (
        "QW-LC4-E-final-engineering-invocation-admission-"
        "repository-seal-merge"
    )
    assert receipt["post_merge_next_slice"] == (
        "QW-LC4-E-final-engineering-invocation-authorization-authoring"
    )


def test_status_and_documentation_record_materialized_seal() -> None:
    markers = (
        "FINAL_ENGINEERING_INVOCATION_ADMISSION_PR=169",
        "FINAL_ENGINEERING_INVOCATION_ADMISSION_PR_HEAD=" + HEAD_COMMIT,
        "FINAL_ENGINEERING_INVOCATION_ADMISSION_REPOSITORY_MAIN_COMMIT="
        + MAIN_COMMIT,
        "FINAL_ENGINEERING_INVOCATION_ADMISSION_REPOSITORY_SEAL_"
        "MATERIALIZED=true",
        "FINAL_ENGINEERING_INVOCATION_ADMISSION_REPOSITORY_SEAL_"
        "COMPLETE=false",
        "FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_AUTHORING_"
        "PERMITTED=false",
        "FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_ISSUED=false",
        "FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_CONSUMED=false",
        "FINAL_ENGINEERING_INVOCATION_PERMITTED=false",
        "FINAL_ENGINEERING_INVOCATION_STARTED=false",
        "FINAL_ENGINEERING_INVOCATION_PERFORMED=false",
        "EXECUTION_LEASE_V1_PRESENT=false",
        "EXECUTION_LEASE_V2_PRESENT=false",
        "DURABLE_HOST_OUTCOME_PRESENT=false",
        "RUNTIME_OUTPUT_PRESENT=false",
        "QW5_TRANSITION_PERMITTED=false",
        "LOCAL_COMPUTE_EXECUTION_OPEN=false",
        "PUBLICATION_PERMITTED=false",
        "NEXT_SLICE=QW-LC4-E-final-engineering-invocation-admission-"
        "repository-seal-merge",
        "POST_MERGE_NEXT_SLICE=QW-LC4-E-final-engineering-invocation-"
        "authorization-authoring",
    )
    sections = (
        (
            "STATUS.md",
            "## `QW-LC4-E`: репозиторная печать допуска финального "
            "инженерного вызова материализована",
        ),
        (
            "STATUS_EN.md",
            "## `QW-LC4-E`: final engineering-invocation admission "
            "repository seal materialized",
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
        "ADR-102-stage3b-qwake-lc4-e-final-engineering-invocation-"
        "admission-repository-seal.md"
    ).is_file()
    assert (
        ROOT
        / "docs/decisions/"
        "ADR-102-stage3b-qwake-lc4-e-final-engineering-invocation-"
        "admission-repository-seal_EN.md"
    ).is_file()
