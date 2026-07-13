from pathlib import Path

import pytest

from torch2pc_thesis.config import (
    ConfigurationError,
    config_sha256,
    deep_merge,
    resolve_config,
    validate_config,
)


def test_deep_merge_preserves_nested_values() -> None:
    merged = deep_merge({"a": {"x": 1, "y": 2}}, {"a": {"y": 3}})
    assert merged == {"a": {"x": 1, "y": 3}}


def test_smoke_configuration_has_no_test_access() -> None:
    config = resolve_config(
        Path("configs"),
        stage="smoke",
        method="bp",
        hardware="rx7700xt_5700x3d",
    )
    assert config["evaluation"]["use_test"] is False
    assert config["training"]["epochs"] == 1
    assert len(config_sha256(config)) == 64


def test_pilot_configuration_has_no_test_access() -> None:
    config = resolve_config("configs", stage="pilot", method="fixedpred")
    assert config["evaluation"]["use_test"] is False
    assert config["protocol"]["status"] == "pilot"


def test_final_configuration_explicitly_uses_test_after_freeze() -> None:
    config = resolve_config("configs", stage="final", method="bp")
    assert config["evaluation"]["use_test"] is True
    assert config["protocol"]["status"] == "frozen"
    assert config["selection"]["execution_order"] == "deterministic_hash_counterbalance"
    assert config["selection"]["execution_order_seed"] == 20260713


def test_test_access_is_rejected_during_pilot() -> None:
    config = resolve_config("configs", stage="pilot", method="fixedpred")
    config["evaluation"]["use_test"] = True
    with pytest.raises(ConfigurationError):
        validate_config(config)


def test_final_rejects_seed_outside_frozen_design() -> None:
    config = resolve_config("configs", stage="final", method="bp")
    config["reproducibility"]["model_seed"] = 999
    with pytest.raises(ConfigurationError):
        validate_config(config)


def test_final_rejects_dataset_outside_frozen_design() -> None:
    config = resolve_config("configs", stage="final", method="bp")
    config["data"]["dataset"] = "KMNIST"
    with pytest.raises(ConfigurationError):
        validate_config(config)


def test_pilot_rejects_seed_outside_pre_specified_design() -> None:
    config = resolve_config("configs", stage="pilot", method="fixedpred")
    config["reproducibility"]["model_seed"] = 999
    with pytest.raises(ConfigurationError):
        validate_config(config)


def test_primary_metric_must_be_consistent_across_training_and_statistics() -> None:
    config = resolve_config("configs", stage="smoke", method="bp")
    config["statistics"]["primary_metric"] = "accuracy"
    with pytest.raises(ConfigurationError):
        validate_config(config)


def test_unknown_primary_contrast_method_is_rejected() -> None:
    config = resolve_config("configs", stage="smoke", method="bp")
    config["statistics"]["primary_contrasts"] = ["unknown_vs_bp"]
    with pytest.raises(ConfigurationError):
        validate_config(config)


def test_confidence_levels_must_match_alpha() -> None:
    config = resolve_config("configs", stage="smoke", method="bp")
    config["statistics"]["difference_confidence"] = 0.90
    with pytest.raises(ConfigurationError):
        validate_config(config)


def test_control_thresholds_must_be_valid() -> None:
    config = resolve_config("configs", stage="smoke", method="bp")
    config["controls"]["thresholds"]["gpu"]["max_relative_l2"] = -1.0
    with pytest.raises(ConfigurationError):
        validate_config(config)


def test_stage_2_is_an_isolated_exact_replication_template() -> None:
    config = resolve_config("configs", stage="final_stage_2", method="bp")
    assert config["evaluation"]["use_test"] is True
    assert config["selection"]["seeds"] == list(range(10))
    assert config["selection"]["datasets"] == ["MNIST", "FashionMNIST"]
    assert config["selection"]["methods"] == [
        "bp",
        "exact",
        "fixedpred",
        "strict",
    ]
    assert config["paths"]["registry"] == "experiments/registry-stage-2.csv"
    assert config["paths"]["runs"] == "results/stage-2/runs"
    assert config["torch2pc"]["commit"] != config["comparison"]["original_torch2pc_commit"]


def test_stage3_design_stages_keep_test_disabled_and_are_not_training_stages() -> None:
    from torch2pc_thesis.config import TRAINING_STAGES

    for stage in ["stage3_profiling", "stage3_pilot", "stage3_final_template"]:
        config = resolve_config("configs", stage=stage, method="strict")
        assert config["evaluation"]["use_test"] is False
        assert stage not in TRAINING_STAGES


def test_stage3_final_template_rejects_premature_candidate_selection() -> None:
    config = resolve_config("configs", stage="stage3_final_template", method="strict")
    config["selection"]["selected_candidates"] = ["composite_vjp"]
    with pytest.raises(ConfigurationError, match="selected only after pilot freeze"):
        validate_config(config)
