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
