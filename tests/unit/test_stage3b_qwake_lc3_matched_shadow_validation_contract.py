# Validate the frozen QW-LC3 matched shadow-validation contract.

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-lc3-matched-shadow-validation-contract-v1"
)
TRANSITION = ROOT / "experiments/frozen/stage3b-qwake-lc3-transition-v1"
LC1 = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-lc1-required-response-schema-v1"
)
LC2 = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-lc2-resource-cost-contract-v1"
)

CONTRACT_SHA256 = (
    "sha256:e1512f29b3e3e3882001172df360e895e6e628b8ea8e4103b9574990775dd5d8"
)
REGISTRY_SHA256 = (
    "sha256:2b001f3002add8d55ce75b02b1caba6bd3c655d177aeb02fe09026e2054dcef1"
)
TRANSITION_RECEIPT_SHA256 = (
    "sha256:c541703f8bc1d449aed88f175b83b9fc03e2574acb5c2be715b157be68733602"
)
TRANSITION_REGISTRY_SHA256 = (
    "sha256:715ed365105aa86d165b8d4911a7a16766972c19f637e78b424398283e34663d"
)
LC1_CONTRACT_SHA256 = (
    "sha256:c7923249c538b29a34f8ffcfcac987b9925a911eb107a085a166ab1d7ca22992"
)
LC1_REGISTRY_SHA256 = (
    "sha256:4a5dca3848bd8ffb0f70013fb5c42a6f6427dd0e1752eb950f5332207b8e269f"
)
LC2_CONTRACT_SHA256 = (
    "sha256:313dc969ab59db20ee27976d3158fca23ce511801e0dc7700dde0d2d002ab69d"
)
LC2_REGISTRY_SHA256 = (
    "sha256:61763ad19c968dbad3eef16e5bee3a11d9dbfad74a7bf45dfc2e64cc022cf311"
)


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads(path.read_text(encoding="utf-8", errors="strict")),
    )


def test_contract_inventory_and_checksum() -> None:
    assert sorted(path.name for path in PACKAGE.iterdir()) == [
        "SHA256SUMS",
        "contract.json",
    ]
    assert _sha(PACKAGE / "contract.json") == CONTRACT_SHA256
    assert _sha(PACKAGE / "SHA256SUMS") == REGISTRY_SHA256


def test_contract_binds_transition_lc1_and_lc2_chain() -> None:
    contract = _json(PACKAGE / "contract.json")
    source = contract["source"]
    assert contract["contract_id"] == (
        "stage3b-qwake-lc3-matched-shadow-validation-contract-v1"
    )
    assert source["main_commit"] == (
        "a7e0c4ec1978042d68abc7437e3005e4295e75ff"
    )
    assert source["transition_commit"] == (
        "a8993e3a996317eeb44270ee37e0e879537d5d65"
    )
    assert _sha(TRANSITION / "receipt.json") == TRANSITION_RECEIPT_SHA256
    assert _sha(TRANSITION / "SHA256SUMS") == TRANSITION_REGISTRY_SHA256
    assert _sha(LC1 / "contract.json") == LC1_CONTRACT_SHA256
    assert _sha(LC1 / "SHA256SUMS") == LC1_REGISTRY_SHA256
    assert _sha(LC2 / "contract.json") == LC2_CONTRACT_SHA256
    assert _sha(LC2 / "SHA256SUMS") == LC2_REGISTRY_SHA256


def test_opaque_state_reference_is_canonical_and_fail_closed() -> None:
    contract = _json(PACKAGE / "contract.json")
    state = contract["opaque_state_reference"]
    assert state["schema_id"] == "stage3b-qwake-opaque-state-v1"
    assert state["canonical_serialization"] == {
        "manifest_character_encoding": "utf-8",
        "manifest_key_order": "lexicographic",
        "manifest_media_type": "application/json",
        "manifest_separators": [",", ":"],
        "manifest_trailing_newline": True,
        "non_finite_json_numbers_permitted": False,
        "payload_byte_order": "little_endian",
        "payload_memory_order": "C_contiguous",
        "payload_source_dtype_preserved": True,
    }
    assert state["disposable_fork_rule"].startswith("every arm")
    assert "source mutation" in state["state_mismatch_rule"]


def test_rng_inventory_restoration_and_non_interference_are_exact() -> None:
    contract = _json(PACKAGE / "contract.json")
    rng = contract["rng_restoration"]
    assert rng["snapshot_id"] == "stage3b-qwake-rng-snapshot-v1"
    assert rng["canonical_inventory"]["cpu_float64_engineering"] == [
        "python_random_global",
        "numpy_legacy_global",
        "torch_cpu_default_generator",
    ]
    assert rng["canonical_inventory"]["rocm_float32_canonical"] == [
        "python_random_global",
        "numpy_legacy_global",
        "torch_cpu_default_generator",
        "torch_rocm_all_visible_device_generators",
    ]
    assert "match exactly" in rng["pair_post_state_rule"]
    assert "restore" in rng["outer_process_non_interference"]


def test_matched_schedule_is_complete_balanced_and_response_first() -> None:
    contract = _json(PACKAGE / "contract.json")
    protocol = contract["matched_shadow_validation"]
    schedule = protocol["pair_schedule"]
    assert protocol["pair_count"] == 12
    assert [item["repeat_index"] for item in schedule] == list(range(12))
    assert sum(
        item["arm_order"][0] == "exact_reference" for item in schedule
    ) == 6
    assert sum(
        item["arm_order"][0] == "analytic_candidate" for item in schedule
    ) == 6
    assert protocol["response_rule"]["all_pairs_must_pass"] is True
    assert protocol["response_rule"]["majority_vote_forbidden"] is True
    assert (
        protocol["cost_rule"]["cost_superiority_required_for_contract_pass"]
        is False
    )


def test_exact_reserve_suffix_is_complete_and_candidate_independent() -> None:
    contract = _json(PACKAGE / "contract.json")
    reserve = contract["reserve_suffix_validation"]
    assert reserve["probe_count_per_validation_cell"] == 2
    assert reserve["probe_positions"] == [
        "before_repeat_0",
        "after_repeat_11",
    ]
    assert reserve["candidate_partial_state_reuse_forbidden"] is True
    assert reserve["direct_reference_response_digest_match_required"] is True
    assert "exactly equal" in reserve["suffix_rule"]
    assert "match exactly" in reserve["response_rule"]


def test_paired_aggregation_is_componentwise_and_no_repeat_is_dropped() -> None:
    contract = _json(PACKAGE / "contract.json")
    aggregate = contract["paired_aggregation"]
    assert aggregate["paired_delta_direction"] == (
        "analytic_candidate_minus_exact_reference"
    )
    assert aggregate["quantile_rule_for_twelve_values"] == {
        "median": "mean(sorted[5],sorted[6])",
        "q1": "mean(sorted[2],sorted[3])",
        "q3": "mean(sorted[8],sorted[9])",
    }
    assert aggregate["scalarization_forbidden"] is True
    assert aggregate["statistical_significance_claim_permitted"] is False
    assert "fail closed" in aggregate["missing_or_excluded_repeat_rule"]
    assert aggregate["order_effect_gate"]["pass_rule"].startswith("every")


def test_contract_opens_only_definition_and_keeps_execution_closed() -> None:
    contract = _json(PACKAGE / "contract.json")
    gates = contract["gates"]
    assert gates["qw_lc3_transition_complete"] is True
    assert gates["qw_lc3_open"] is True
    assert gates["qw_lc3_matched_shadow_validation_contract_frozen"] is True
    assert gates["matched_shadow_validation_protocol_frozen"] is True
    assert gates["opaque_state_ref_definition_frozen"] is True
    assert gates["rng_restoration_protocol_frozen"] is True
    assert gates["exact_reserve_suffix_validation_frozen"] is True
    assert gates["repeat_aggregation_protocol_frozen"] is True
    assert gates["qw_lc3_complete"] is False
    assert gates["qw_lc4_implementation_permitted"] is False
    assert gates["local_compute_implementation_open"] is False
    assert gates["local_compute_execution_open"] is False
    assert gates["feature_collection_permitted"] is False
    assert gates["oracle_label_generation_open"] is False
    assert gates["scientific_execution_open"] is False
    assert gates["test_dataset_access"] is False
    assert gates["publication_permitted"] is False
    assert contract["next_slice"] == "QW-LC3-repository-freeze"


def test_status_records_frozen_qw_lc3_contract_boundary() -> None:
    required = (
        "qwake_qw_lc3_transition_complete=true",
        "qwake_qw_lc3_open=true",
        "qwake_qw_lc3_matched_shadow_validation_contract_frozen=true",
        "qwake_qw_lc3_contract_id="
        "stage3b-qwake-lc3-matched-shadow-validation-contract-v1",
        "qwake_qw_lc3_contract_sha256="
        "sha256:e1512f29b3e3e3882001172df360e895e6e628b8ea8e4103b9574990775dd5d8",
        "matched_shadow_validation_protocol_frozen=true",
        "opaque_state_ref_definition_frozen=true",
        "rng_restoration_protocol_frozen=true",
        "exact_reserve_suffix_validation_frozen=true",
        "repeat_aggregation_protocol_frozen=true",
        "qwake_qw_lc3_complete=false",
        "qwake_qw_lc4_implementation_permitted=false",
        "qwake_local_compute_implementation_open=false",
        "qwake_local_compute_execution_open=false",
        "scientific_execution_open=false",
        "test_dataset_access=false",
        "publication_permitted=false",
        "qwake_next_slice=QW-LC3-repository-freeze",
    )
    for name in ("STATUS.md", "STATUS_EN.md"):
        text = (ROOT / name).read_text(
            encoding="utf-8",
            errors="strict",
        )
        for marker in required:
            assert marker in text
