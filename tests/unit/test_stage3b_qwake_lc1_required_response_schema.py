# Validate the QW-LC1 required-response schema and closed boundary.

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-lc1-required-response-schema-v1"
)
TRANSITION = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-lc1-transition-v1"
)
LC0_CONTRACT = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-lc0-semantics-scope-v1"
)
SPECIAL_CASE = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-fp-special-case-v1"
)

CONTRACT_SHA256 = (
    "sha256:"
    "c7923249c538b29a34f8ffcfcac987b9"
    "925a911eb107a085a166ab1d7ca22992"
)
REGISTRY_SHA256 = (
    "sha256:"
    "4a5dca3848bd8ffb0f70013fb5c42a6f"
    "6427dd0e1752eb950f5332207b8e269f"
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
LC0_CONTRACT_SHA256 = (
    "sha256:"
    "e68e953aa3d5c425678d54b8dd3b756e"
    "706e5cc1a1c4862d4c0ba0bda19bf3c3"
)
SPECIAL_CASE_SHA256 = (
    "sha256:"
    "968457365ddc1c94a814e0f7712d30d0"
    "154afd0c96d8464bff46a31e61ad3698"
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


def test_contract_inventory_and_checksum() -> None:
    assert sorted(
        path.name
        for path in PACKAGE.iterdir()
    ) == [
        "SHA256SUMS",
        "contract.json",
    ]
    assert _sha(PACKAGE / "contract.json") == CONTRACT_SHA256
    assert _sha(PACKAGE / "SHA256SUMS") == REGISTRY_SHA256


def test_contract_binds_transition_and_source_contracts() -> None:
    contract = _json(PACKAGE / "contract.json")
    provenance = contract["provenance"]
    assert provenance["main_commit"] == (
        "c3533fcb63ffc869faddbaa99645c9099d16d1cc"
    )
    assert provenance["main_first_parent"] == (
        "0fbd54be337665e06ad63b6d9c7f8ca978ab75ee"
    )
    assert provenance["transition_commit"] == (
        "9fcdb993c262fe34fb28af996f2373b67486effb"
    )
    assert _sha(
        TRANSITION / "receipt.json"
    ) == TRANSITION_RECEIPT_SHA256
    assert _sha(
        TRANSITION / "SHA256SUMS"
    ) == TRANSITION_REGISTRY_SHA256
    assert _sha(
        LC0_CONTRACT / "contract.json"
    ) == LC0_CONTRACT_SHA256
    assert _sha(
        SPECIAL_CASE / "contract.json"
    ) == SPECIAL_CASE_SHA256


def test_registered_domain_remains_bounded() -> None:
    contract = _json(PACKAGE / "contract.json")
    domain = contract["registered_domain"]
    assert domain == {
        "action_family": [
            "LOCAL_SWEEP",
            "ANALYTIC_COMPLETION",
        ],
        "architecture": "lenet_classic",
        "candidate_indices": "t_in_[0,K_ref]",
        "canonical_reference_action": "COMPLETE_SUFFIX",
        "decision_epoch": "after_S_t_before_sweep_t_plus_1",
        "eta": 1.0,
        "executor": "stage2_baseline",
        "generalization_claim": False,
        "method": "fixedpred",
    }


def test_required_result_has_exact_three_components() -> None:
    contract = _json(PACKAGE / "contract.json")
    required = contract["required_result"]
    assert required["response_schema_id"] == (
        "stage3b-qwake-lc1-required-response-schema-v1"
    )
    assert required["symbol"] == "R(a,s)"
    assert required["component_order"] == [
        "named_parameter_gradients",
        "endpoint_beliefs",
        "endpoint_loss",
    ]
    components = required["components"]
    assert components["named_parameter_gradients"]["kind"] == (
        "named_tensor_map"
    )
    assert components["endpoint_beliefs"]["kind"] == (
        "indexed_tensor_sequence"
    )
    assert components["endpoint_loss"]["kind"] == "scalar_tensor"
    state = required["state_reference"]
    assert state["opaque_in_qw_lc1"] is True
    assert state["identity_semantics_deferred_to"] == "QW-LC3"


def test_serialization_preserves_source_values_and_separates_digest() -> None:
    contract = _json(PACKAGE / "contract.json")
    serialization = contract["canonical_serialization"]
    assert serialization["layout"] == (
        "manifest_json_plus_payload_files"
    )
    payload = serialization["tensor_payload_encoding"]
    assert payload["byte_order"] == "little_endian"
    assert payload["memory_order"] == "C_contiguous"
    assert payload["payload_values"] == (
        "source_dtype_values_without_numeric_cast"
    )
    response_digest = serialization["response_digest"]
    assert (
        response_digest[
            "exact_digest_equality_is_sufficient_for_response_equivalence"
        ]
        is True
    )
    assert (
        response_digest[
            "exact_digest_equality_is_required_for_response_equivalence"
        ]
        is False
    )


def test_mandatory_observables_are_response_scoped() -> None:
    contract = _json(PACKAGE / "contract.json")
    observables = contract["mandatory_observables"]
    assert observables["response_level"] == [
        "response_schema_id",
        "state_id",
        "comparison_profile_id",
        "component_order",
        "component_manifest_sha256",
        "canonical_response_sha256",
        "all_entries_finite",
    ]
    assert "payload_sha256" in observables["entry_level"]
    assert observables[
        "validation_control_observables_deferred_to_qw_lc3"
    ] == [
        "transition_sequence",
        "rng_state_before",
        "rng_state_after",
        "snapshot_identity",
        "fallback_suffix_identity",
    ]


def test_response_equivalence_is_zero_safe_and_nontransitive() -> None:
    contract = _json(PACKAGE / "contract.json")
    relation = contract["response_equivalence"]
    assert relation["symbol"] == "a_i ~_R a_j"
    assert relation["comparison_value_dtype"] == "float64"
    assert relation["transitivity_assumed"] is False
    assert relation["zero_safe_rule"] == {
        "both_active": (
            "require_cosine_relative_l2_and_max_abs_limits"
        ),
        "both_zero": (
            "pass_cosine_gate_and_require_relative_l2_and_max_abs_limits"
        ),
        "one_zero": "fail",
    }
    assert relation["response_pass_rule"] == (
        "all_exact_structural_equalities_and_every_component_passes"
    )
    assert relation["pass_threshold"] == "d_R<=1"


def test_threshold_profiles_match_registered_cpu_and_rocm_gates() -> None:
    contract = _json(PACKAGE / "contract.json")
    profiles = contract["threshold_profiles"]
    assert profiles["cpu_float64_engineering"] == {
        "decision_facing": False,
        "lane": "cpu_float64",
        "max_abs": 1e-9,
        "max_relative_l2": 1e-7,
        "min_cosine": 0.99999,
        "source_dtype": "float64",
        "zero_atol": 1e-12,
    }
    assert profiles["rocm_float32_canonical"] == {
        "decision_facing": True,
        "lane": "rocm_float32",
        "max_abs": 1e-5,
        "max_relative_l2": 1e-3,
        "min_cosine": 0.999,
        "source_dtype": "float32",
        "zero_atol": 1e-7,
    }


def test_claim_and_execution_boundaries_remain_closed() -> None:
    contract = _json(PACKAGE / "contract.json")
    forbidden = set(
        contract["claim_boundary"]["forbidden_claims"]
    )
    assert "response_equivalence_established_for_analytic_candidate" in (
        forbidden
    )
    assert "cost_mapping_or_cost_equivalence_established" in forbidden
    gates = contract["gates"]
    assert gates["qw_lc1_required_response_schema_frozen"] is True
    assert gates["qw_lc1_complete"] is False
    assert gates["qw_lc2_transition_permitted"] is False
    assert gates["resource_trajectory_schema_open"] is False
    assert gates["local_compute_implementation_open"] is False
    assert gates["local_compute_execution_open"] is False
    assert gates["feature_collection_permitted"] is False
    assert gates["oracle_label_generation_open"] is False
    assert gates["policy_activation_permitted"] is False
    assert gates["scientific_execution_open"] is False
    assert gates["test_dataset_access"] is False
    assert gates["publication_permitted"] is False
    assert contract["next_slice"] == "QW-LC1-repository-freeze"


def test_status_records_frozen_required_response_schema() -> None:
    markers = (
        "qwake_qw_lc1_transition_complete=true",
        "qwake_qw_lc1_open=true",
        "qwake_qw_lc1_required_response_schema_frozen=true",
        "qwake_qw_lc1_contract_id="
        "stage3b-qwake-lc1-required-response-schema-v1",
        "qwake_qw_lc1_contract_sha256="
        "sha256:c7923249c538b29a34f8ffcfcac987b9925a911eb107a085a166ab1d7ca22992",
        "mandatory_observables_definition_frozen=true",
        "response_equivalence_operator_definition_frozen=true",
        "qwake_qw_lc1_complete=false",
        "qwake_qw_lc2_transition_permitted=false",
        "resource_trajectory_schema_open=false",
        "qwake_local_compute_implementation_open=false",
        "qwake_local_compute_execution_open=false",
        "scientific_execution_open=false",
        "test_dataset_access=false",
        "publication_permitted=false",
        "qwake_next_slice=QW-LC1-repository-freeze",
    )
    sections = (
        (
            "STATUS.md",
            "## `QW-LC1`: схема требуемого результата зафиксирована",
        ),
        (
            "STATUS_EN.md",
            "## `QW-LC1`: required-response schema frozen",
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
