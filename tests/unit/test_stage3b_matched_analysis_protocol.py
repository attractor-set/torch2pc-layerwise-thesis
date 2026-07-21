from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from torch2pc_thesis import stage3b_matched_analysis as analysis
from torch2pc_thesis.stage3b_matched_analysis_protocol import (
    MAX_PEAK_MEMORY_GROWTH,
    PROTOCOL_ID,
    PROTOCOL_ROOT_RELATIVE,
    Stage3BMatchedAnalysisProtocolError,
    build_protocol,
    validate_protocol,
    write_protocol_package,
)

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_ROOT = ROOT / PROTOCOL_ROOT_RELATIVE
EXPECTED_PROTOCOL_SHA256 = (
    "074510f1212f1eceb41da8b42ab52f1fd9d816c3901f2a3b8e4e7afec59a3209"
)
EXPECTED_REGISTRY_SHA256 = (
    "a49f49f423948900221007d715e5dc174cd3b14af288ddc56f87ec5366307b63"
)


def _load_protocol() -> dict[str, object]:
    value = json.loads(
        (PROTOCOL_ROOT / "protocol.json").read_text(encoding="utf-8")
    )
    assert isinstance(value, dict)
    return value


def _keys(value: object) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, nested in value.items():
            found.add(str(key))
            found.update(_keys(nested))
    elif isinstance(value, list):
        for nested in value:
            found.update(_keys(nested))
    return found


def test_frozen_protocol_rebuilds_exactly() -> None:
    protocol = _load_protocol()

    validate_protocol(protocol, ROOT)
    assert protocol == build_protocol(ROOT)
    assert protocol["protocol_id"] == PROTOCOL_ID

    import hashlib

    assert (
        hashlib.sha256((PROTOCOL_ROOT / "protocol.json").read_bytes()).hexdigest()
        == EXPECTED_PROTOCOL_SHA256
    )
    assert (
        hashlib.sha256((PROTOCOL_ROOT / "SHA256SUMS").read_bytes()).hexdigest()
        == EXPECTED_REGISTRY_SHA256
    )


def test_protocol_package_check_and_clean_rebuild(tmp_path: Path) -> None:
    write_protocol_package(ROOT, PROTOCOL_ROOT, check=True)

    output_root = tmp_path / "frozen"
    rebuilt = write_protocol_package(ROOT, output_root)

    assert rebuilt == _load_protocol()
    assert (output_root / "protocol.json").read_bytes() == (
        PROTOCOL_ROOT / "protocol.json"
    ).read_bytes()
    assert (output_root / "SHA256SUMS").read_bytes() == (
        PROTOCOL_ROOT / "SHA256SUMS"
    ).read_bytes()


def test_protocol_is_post_collection_but_pre_analysis() -> None:
    protocol = _load_protocol()
    boundary = protocol["claim_boundary"]
    assert isinstance(boundary, dict)

    assert protocol["phase"] == "post_collection_pre_analysis"
    assert boundary["protocol_builder_uses_observed_metric_values"] is False
    assert boundary["analysis_execution_permitted"] is False
    assert boundary["analysis_results_present"] is False
    assert boundary["source_evidence_read_only"] is True
    assert boundary["results_publication_permitted"] is False
    assert boundary["release_publication_permitted"] is False
    assert boundary["test_dataset_access"] is False
    assert boundary["superiority_claim_permitted"] is False

    forbidden_result_keys = {
        "observed_speedup",
        "winner",
        "selected_candidate",
        "p_value",
        "confidence_interval",
        "observed_median",
    }
    assert _keys(protocol).isdisjoint(forbidden_result_keys)


def test_protocol_preserves_independent_unit_and_no_pseudoreplication() -> None:
    protocol = _load_protocol()
    design = protocol["design"]
    aggregation = protocol["aggregation"]
    sensitivity = protocol["missingness_and_sensitivity"]

    assert isinstance(design, dict)
    assert isinstance(aggregation, dict)
    assert isinstance(sensitivity, dict)

    assert design["independent_unit"] == "model_seed"
    assert design["model_seeds"] == [70, 71, 72]
    assert design["matched_block_count"] == 96
    assert design["matched_cell_count"] == 288
    assert design["repetitions_per_cell"] == 5

    assert aggregation["repetitions_do_not_increase_independent_n"] is True
    assert (
        aggregation["configurations_do_not_increase_independent_n_for_inferential_claims"]
        is True
    )
    assert sensitivity["p_values"] is False
    assert sensitivity["bootstrap_confidence_intervals"] is False
    assert sensitivity["post_hoc_exclusion_permitted"] is False


def test_protocol_freezes_registered_continuation_thresholds() -> None:
    protocol = _load_protocol()
    decision = protocol["engineering_decision_rule"]
    assert isinstance(decision, dict)

    assert decision["fixedpred_min_device_time_reduction"] == 0.15
    assert decision["strict_min_device_time_reduction"] == 0.20
    assert decision["maximum_device_time_regression_in_any_seed"] == 0.03
    assert decision["maximum_peak_allocated_growth"] == 0.15
    assert decision["maximum_peak_reserved_growth"] == 0.15

    assert analysis.MATCHED_CONTINUATION_THRESHOLDS == {
        "fixedpred": 0.15,
        "strict": 0.20,
    }
    assert analysis.MATCHED_MAX_MEMORY_GROWTH == MAX_PEAK_MEMORY_GROWTH


def test_protocol_freezes_pareto_rule_without_scalarization() -> None:
    protocol = _load_protocol()
    pareto = protocol["pareto_rule"]
    assert isinstance(pareto, dict)

    assert pareto["included_alternatives"] == [
        "stage2_baseline",
        "isolated_layer_vjp",
        "composite_vjp",
    ]
    assert len(cast_list(pareto["dimensions_to_minimize"])) == 7
    assert pareto["single_winner_implied"] is False
    assert pareto["missing_or_nonpositive_baseline"] == "fail_closed"


def cast_list(value: Any) -> list[object]:
    assert isinstance(value, list)
    return value



def test_protocol_freezes_scaling_metrics_and_exact_output_set() -> None:
    protocol = _load_protocol()
    design = protocol["design"]
    scaling = protocol["scaling"]
    outputs = protocol["registered_outputs"]

    assert isinstance(design, dict)
    assert isinstance(scaling, dict)
    assert isinstance(outputs, dict)

    assert design["pareto_membership_rows_expected"] == 96
    assert design["scaling_metric_count"] == 7
    assert scaling["unit"] == "candidate_method_model_seed_metric"
    assert scaling["metrics"] == [
        "device_time_ratio_to_baseline",
        "peak_allocated_ratio_to_baseline",
        "peak_reserved_ratio_to_baseline",
        "saved_tensor_bytes_ratio_to_baseline",
        "state_vjp_calls_ratio_to_baseline",
        "graph_span_ratio_to_baseline",
        "dependency_radius_ratio_to_baseline",
    ]
    assert outputs["expected_top_level_file_count"] == 18
    assert (
        outputs["output_root_policy"]
        == "new_empty_directory_fail_if_exists_or_nonempty"
    )


def test_protocol_validation_rejects_tampering() -> None:
    protocol = _load_protocol()
    tampered = json.loads(json.dumps(protocol))
    tampered["claim_boundary"]["analysis_execution_permitted"] = True

    with pytest.raises(
        Stage3BMatchedAnalysisProtocolError,
        match="differs from deterministic builder",
    ):
        validate_protocol(tampered, ROOT)
