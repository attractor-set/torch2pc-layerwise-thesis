# Validate the QW-LC1 transition receipt and closed boundary.

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-lc1-transition-v1"
)
REPOSITORY_FREEZE = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-lc0-repository-freeze-v1"
)
CONTRACT = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-lc0-semantics-scope-v1"
)

TRANSITION_RECEIPT_SHA256 = (
    "sha256:"
    "9cafcad4d6ee3245c48ca2ff531dc598"
    "5ea4e670cb465fdcfaf2b99d376d5db4"
)
TRANSITION_REGISTRY_SHA256 = (
    "sha256:"
    "16ba50cdf788938fa0ba739a4a21723ee"
    "2454e45b7e796adad8c46617d22fec7"
)
REPOSITORY_FREEZE_RECEIPT_SHA256 = (
    "sha256:"
    "b8a98f16e50223fa6bdc1b4ad18d7c3"
    "59e968eef3684295119410b50093364a1"
)
REPOSITORY_FREEZE_REGISTRY_SHA256 = (
    "sha256:"
    "84358706da9e3e2d31f178776172ed6c"
    "2e75e057b787df12394a46936f43935b"
)
CONTRACT_SHA256 = (
    "sha256:"
    "e68e953aa3d5c425678d54b8dd3b756e"
    "706e5cc1a1c4862d4c0ba0bda19bf3c3"
)
CONTRACT_REGISTRY_SHA256 = (
    "sha256:"
    "dc84bed1e99526b4267ab982e3ac32fc"
    "704b628a3fb6194f6b6662649e0e4119"
)


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def _json(path: Path) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads(
            path.read_text(
                encoding="utf-8",
                errors="strict",
            )
        ),
    )


def test_transition_inventory_and_checksum() -> None:
    assert sorted(
        path.name
        for path in PACKAGE.iterdir()
    ) == [
        "SHA256SUMS",
        "receipt.json",
    ]
    assert _sha(
        PACKAGE / "receipt.json"
    ) == TRANSITION_RECEIPT_SHA256
    assert _sha(
        PACKAGE / "SHA256SUMS"
    ) == TRANSITION_REGISTRY_SHA256


def test_transition_binds_completed_lc0_chain() -> None:
    receipt = _json(PACKAGE / "receipt.json")
    assert receipt["transition_id"] == (
        "stage3b-qwake-lc1-transition-v1"
    )
    assert receipt["main_commit"] == (
        "0fbd54be337665e06ad63b6d9c7f8ca978ab75ee"
    )
    assert receipt["main_first_parent"] == (
        "8429f54257685a879b0a44499d5fa81eab7310ea"
    )
    assert receipt["repository_freeze_commit"] == (
        "9c940a66e9290d145887fcbefe728c1424ca6036"
    )
    assert receipt["semantics_scope_freeze_commit"] == (
        "715308451ac3e696d4c2209276d36853f6799d6f"
    )
    assert receipt["post_merge_verification_passed"] is True
    assert receipt["qw_lc0_repository_freeze_complete"] is True
    assert _sha(
        REPOSITORY_FREEZE / "receipt.json"
    ) == REPOSITORY_FREEZE_RECEIPT_SHA256
    assert _sha(
        REPOSITORY_FREEZE / "SHA256SUMS"
    ) == REPOSITORY_FREEZE_REGISTRY_SHA256
    assert _sha(
        CONTRACT / "contract.json"
    ) == CONTRACT_SHA256
    assert _sha(
        CONTRACT / "SHA256SUMS"
    ) == CONTRACT_REGISTRY_SHA256


def test_lc1_scope_is_finite_and_cost_is_deferred() -> None:
    receipt = _json(PACKAGE / "receipt.json")
    assert receipt["qw_lc1_scope"] == [
        "canonical_required_response_schema",
        "mandatory_observables",
        "response_equivalence_operator",
    ]
    assert set(receipt["excluded_from_qw_lc1"]) == {
        "resource_trajectory_schema",
        "measurement_to_cost_mapping",
        "cost_equivalence_operator",
        "local_compute_implementation",
        "local_compute_execution",
        "feature_collection",
        "oracle_label_generation",
        "policy_activation",
        "scientific_execution",
        "test_dataset_access",
        "publication",
    }


def test_transition_keeps_lc1_and_execution_closed() -> None:
    receipt = _json(PACKAGE / "receipt.json")
    assert receipt["qw_lc1_transition_permitted"] is True
    assert receipt["qw_lc1_transition_materialized"] is True
    assert receipt["qw_lc1_transition_complete"] is False
    assert receipt["qw_lc1_open"] is False
    assert receipt["qw_lc1_required_response_schema_open"] is False
    assert receipt["mandatory_observables_definition_open"] is False
    assert (
        receipt["response_equivalence_operator_definition_open"]
        is False
    )
    assert receipt["resource_trajectory_schema_open"] is False
    assert receipt["local_compute_implementation_open"] is False
    assert receipt["local_compute_execution_open"] is False
    assert receipt["feature_collection_permitted"] is False
    assert receipt["oracle_label_generation_open"] is False
    assert receipt["policy_activation_permitted"] is False
    assert receipt["scientific_execution_open"] is False
    assert receipt["test_dataset_access"] is False
    assert receipt["publication_permitted"] is False
    assert receipt["runtime_rerun_performed"] is False
    assert receipt["next_slice"] == "QW-LC1-transition-merge"
    assert receipt["post_merge_next_slice"] == (
        "QW-LC1-required-response-schema"
    )


def test_status_records_materialized_lc1_transition() -> None:
    markers = (
        "qwake_qw_lc0_repository_freeze_complete=true",
        "qwake_qw_lc1_transition_permitted=true",
        "qwake_qw_lc1_transition_materialized=true",
        "qwake_qw_lc1_transition_complete=false",
        "qwake_qw_lc1_open=false",
        "qwake_qw_lc1_required_response_schema_open=false",
        "mandatory_observables_definition_open=false",
        "response_equivalence_operator_definition_open=false",
        "resource_trajectory_schema_open=false",
        "qwake_local_compute_implementation_open=false",
        "qwake_local_compute_execution_open=false",
        "scientific_execution_open=false",
        "test_dataset_access=false",
        "publication_permitted=false",
        "qwake_next_slice=QW-LC1-transition-merge",
        "qwake_post_merge_next_slice=QW-LC1-required-response-schema",
    )
    sections = (
        (
            "STATUS.md",
            "## `QW-LC1`: переход материализован",
        ),
        (
            "STATUS_EN.md",
            "## `QW-LC1`: transition materialized",
        ),
    )
    for name, heading in sections:
        text = (ROOT / name).read_text(
            encoding="utf-8",
            errors="strict",
        )
        section = text[text.index(heading):]
        for marker in markers:
            assert marker in section, (name, marker)
