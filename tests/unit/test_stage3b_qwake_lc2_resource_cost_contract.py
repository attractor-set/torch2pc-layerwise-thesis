# Validate the frozen QW-LC2 resource-and-cost contract.

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-lc2-resource-cost-contract-v1"
)
TRANSITION = ROOT / (
    "experiments/frozen/stage3b-qwake-lc2-transition-v1"
)
LC1 = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-lc1-repository-freeze-v1"
)

CONTRACT_SHA256 = (
    "sha256:313dc969ab59db20ee27976d3158fca23ce511801e0dc7700dde0d2d002ab69d"
)
REGISTRY_SHA256 = (
    "sha256:61763ad19c968dbad3eef16e5bee3a11d9dbfad74a7bf45dfc2e64cc022cf311"
)
TRANSITION_RECEIPT_SHA256 = (
    "sha256:"
    "9a7e21fa573aa497e5c85ab92aade9e8"
    "4e15dc0bd05e18e948ad8fac0194df23"
)
TRANSITION_REGISTRY_SHA256 = (
    "sha256:"
    "e5991b9175ebbdc60562a4185e06464d"
    "1754d84a12aeb1415ab4e2844395775c"
)
LC1_RECEIPT_SHA256 = (
    "sha256:"
    "53080ac5c2dbcbb29c5e8ce5108280bd"
    "77c276befe8c6b867af98e687d4e902b"
)
LC1_REGISTRY_SHA256 = (
    "sha256:"
    "ff048073f59c94c023f855266352670a"
    "832440053f6078ef3acd2f3e25913068"
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


def test_contract_binds_transition_and_lc1_chain() -> None:
    contract = _json(PACKAGE / "contract.json")
    source = contract["source"]
    assert contract["contract_id"] == (
        "stage3b-qwake-lc2-resource-cost-contract-v1"
    )
    assert source["main_commit"] == (
        "858403cbb2423ad3427ab7a042266880ca34c0b7"
    )
    assert source["transition_commit"] == (
        "9e8f33a5fcf5399dcf834bdedefa5ca404f89fef"
    )
    assert _sha(TRANSITION / "receipt.json") == TRANSITION_RECEIPT_SHA256
    assert _sha(TRANSITION / "SHA256SUMS") == TRANSITION_REGISTRY_SHA256
    assert _sha(LC1 / "receipt.json") == LC1_RECEIPT_SHA256
    assert _sha(LC1 / "SHA256SUMS") == LC1_REGISTRY_SHA256


def test_resource_trajectory_schema_is_ordered_and_fail_closed() -> None:
    contract = _json(PACKAGE / "contract.json")
    trajectory = contract["resource_trajectory_schema"]
    assert trajectory["schema_id"] == (
        "stage3b-qwake-resource-trajectory-v1"
    )
    assert trajectory["interval_records"]["owner_order"] == [
        "core_compute",
        "diagnostic_mechanism",
        "observer",
        "control_plane",
        "fallback",
    ]
    assert trajectory["interval_records"]["lane_order"] == [
        "host",
        "device",
    ]
    assert trajectory["completeness"]["missing_fails_closed"] is True
    assert (
        trajectory["observer_calibration"]["mapped_overhead_rule"]
        == "max(0,raw_residual_ns)"
    )
    assert trajectory["fallback_record"]["exact_reserve_path"] == (
        "LOCAL_SWEEP"
    )


def test_phi_freezes_field_order_and_no_double_counting() -> None:
    contract = _json(PACKAGE / "contract.json")
    mapping = contract["measurement_to_cost_mapping"]
    assert mapping["field_order"] == [
        "compute_primary_time_ns",
        "latency_wall_time_ns",
        "peak_allocated_bytes",
        "peak_reserved_bytes",
        "diagnostic_primary_time_ns",
        "diagnostic_materialized_bytes",
        "observer_overhead_time_ns",
        "observer_evidence_bytes",
        "control_wall_time_ns",
        "fallback_wall_time_ns",
        "fallback_invoked",
    ]
    rules = set(mapping["no_double_counting_rules"])
    assert "interval union replaces naive duration summation" in rules
    assert "memory components are maxima and are never summed" in rules
    assert "no scalar total cost is produced" in rules


def test_cost_profiles_separate_shadow_and_end_to_end() -> None:
    contract = _json(PACKAGE / "contract.json")
    profiles = contract["cost_vector"]["profiles"]
    shadow = profiles["shadow_mechanism_v1"]
    end_to_end = profiles["end_to_end_v1"]
    assert shadow["decision_facing"] is False
    assert shadow["control_status"] == "not_executed"
    assert end_to_end["decision_facing"] is True
    assert (
        end_to_end["requires_qw_lc3_state_rng_and_fallback_validation"]
        is True
    )
    assert contract["cost_vector"]["implicit_scalarization_forbidden"] is True


def test_cost_equivalence_is_fieldwise_zero_safe_and_nontransitive() -> None:
    contract = _json(PACKAGE / "contract.json")
    equivalence = contract["cost_equivalence"]
    assert equivalence["operator_id"] == (
        "stage3b-qwake-cost-equivalence-v1"
    )
    assert equivalence["transitivity_assumed"] is False
    assert equivalence["equivalence_classes_permitted"] is False
    assert equivalence["tolerance_profiles"]["cpu_float64_engineering"] == {
        "artifact_bytes": {"atol": 0, "rtol": 0.0},
        "boolean": "exact",
        "peak_bytes": {"atol": 4096, "rtol": 0.02},
        "time_ns": {"atol": 50000, "rtol": 0.1},
    }
    assert equivalence["tolerance_profiles"]["rocm_float32_canonical"] == {
        "artifact_bytes": {"atol": 0, "rtol": 0.0},
        "boolean": "exact",
        "peak_bytes": {"atol": 4096, "rtol": 0.01},
        "time_ns": {"atol": 10000, "rtol": 0.05},
    }


def test_selection_is_response_first_pareto_and_deterministic() -> None:
    contract = _json(PACKAGE / "contract.json")
    selection = contract["selection_rule"]
    assert selection["response_admission_precedes_cost"] is True
    assert selection["pareto_rule"]["scalarization"] is None
    assert selection["deterministic_ambiguity_resolution"] == [
        "prefer fallback_invoked=false",
        "minimize latency_wall_time_ns",
        "minimize compute_primary_time_ns",
        "minimize peak_allocated_bytes",
        "lexicographically smallest action_id",
    ]
    assert selection["exact_reserve_path"] == "LOCAL_SWEEP"


def test_contract_keeps_lc3_implementation_and_execution_closed() -> None:
    contract = _json(PACKAGE / "contract.json")
    gates = contract["gates"]
    assert gates["qw_lc2_transition_complete"] is True
    assert gates["qw_lc2_open"] is True
    assert gates["qw_lc2_resource_cost_contract_frozen"] is True
    assert gates["resource_trajectory_schema_frozen"] is True
    assert gates["measurement_to_cost_mapping_frozen"] is True
    assert gates["cost_equivalence_operator_definition_frozen"] is True
    assert gates["pareto_and_tie_break_rule_frozen"] is True
    assert gates["qw_lc2_complete"] is False
    assert gates["qw_lc3_transition_permitted"] is False
    assert gates["local_compute_implementation_open"] is False
    assert gates["local_compute_execution_open"] is False
    assert gates["scientific_execution_open"] is False
    assert gates["test_dataset_access"] is False
    assert gates["publication_permitted"] is False
    assert gates["runtime_rerun_performed"] is False
    assert contract["next_slice"] == "QW-LC2-repository-freeze"


def test_status_records_frozen_resource_cost_boundary() -> None:
    required = (
        "qwake_qw_lc2_transition_complete=true",
        "qwake_qw_lc2_open=true",
        "qwake_qw_lc2_resource_cost_contract_frozen=true",
        "qwake_qw_lc2_contract_id="
        "stage3b-qwake-lc2-resource-cost-contract-v1",
        "qwake_qw_lc2_contract_sha256=sha256:313dc969ab59db20ee27976d3158fca23ce511801e0dc7700dde0d2d002ab69d",
        "resource_trajectory_schema_frozen=true",
        "measurement_to_cost_mapping_frozen=true",
        "cost_equivalence_operator_definition_frozen=true",
        "pareto_and_tie_break_rule_frozen=true",
        "qwake_qw_lc2_complete=false",
        "qwake_qw_lc3_transition_permitted=false",
        "qwake_local_compute_implementation_open=false",
        "qwake_local_compute_execution_open=false",
        "scientific_execution_open=false",
        "test_dataset_access=false",
        "publication_permitted=false",
        "qwake_next_slice=QW-LC2-repository-freeze",
    )
    for name in ("STATUS.md", "STATUS_EN.md"):
        text = (ROOT / name).read_text(
            encoding="utf-8",
            errors="strict",
        )
        for marker in required:
            assert marker in text
