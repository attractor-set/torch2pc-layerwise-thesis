from __future__ import annotations

import torch
import torch.nn as nn

from torch2pc_thesis.stage3b_a1_observer import (
    OBSERVER_ROLES,
    OBSERVER_SCHEMA_ID,
    PassiveLayerObserver,
    observer_schema_manifest,
)


def test_observer_schema_manifest_freezes_counts_and_naming() -> None:
    schema = observer_schema_manifest(6)
    assert schema["observer_schema_id"] == OBSERVER_SCHEMA_ID
    assert schema["roles"] == list(OBSERVER_ROLES)
    assert schema["capture_policy"] == "first forward invocation per top-level layer"
    assert schema["additional_forward_calls"] == "counted but not captured"
    assert schema["expected_records_per_arm_run"] == 12
    assert schema["record_key_format"] == "layer-{index:02d}:{role}:00"
    assert schema["expected_occurrences_per_role"] == 1


def test_passive_observer_captures_one_detached_input_and_output_per_layer() -> None:
    model = nn.Sequential(
        nn.Linear(4, 5),
        nn.Tanh(),
        nn.Linear(5, 3),
    ).to(dtype=torch.float64)
    observer = PassiveLayerObserver(model)
    observer.start()

    outputs = model(torch.randn(2, 4, dtype=torch.float64, requires_grad=True))
    outputs.sum().backward()
    observer.close()

    validation = observer.validate(setup_rng_unchanged=True)
    assert validation.observer_schema_id == OBSERVER_SCHEMA_ID
    assert validation.top_level_layers == 3
    assert validation.expected_records == 6
    assert validation.observed_records == 6
    assert validation.input_call_counts == (1, 1, 1)
    assert validation.output_call_counts == (1, 1, 1)
    assert validation.balanced_forward_calls is True
    assert validation.passed is True
    assert {record.role for record in observer.records} == set(OBSERVER_ROLES)
    assert all(record.occurrence == 0 for record in observer.records)
    assert all(record.detached for record in observer.records)
    assert all(record.metadata_preserved for record in observer.records)


def test_passive_observer_preserves_preexisting_hooks_after_cleanup() -> None:
    model = nn.Sequential(nn.Linear(3, 2), nn.Tanh()).to(dtype=torch.float64)
    calls: list[str] = []
    existing = model[0].register_forward_hook(
        lambda _module, _args, _output: calls.append("existing")
    )
    try:
        observer = PassiveLayerObserver(model)
        observer.start()
        model(torch.randn(1, 3, dtype=torch.float64))
        observer.close()

        validation = observer.validate(setup_rng_unchanged=True)
        assert validation.cleanup_complete is True
        assert calls == ["existing"]
        assert len(model[0]._forward_hooks) == 1
    finally:
        existing.remove()


def test_passive_observer_counts_repeated_calls_but_keeps_frozen_payload() -> None:
    model = nn.Sequential(nn.Linear(2, 2), nn.Tanh()).to(dtype=torch.float64)
    observer = PassiveLayerObserver(model)
    observer.start()
    inputs = torch.randn(1, 2, dtype=torch.float64)
    model(inputs)
    model(inputs)
    observer.close()

    validation = observer.validate(setup_rng_unchanged=True)
    assert validation.expected_records == 4
    assert validation.observed_records == 4
    assert validation.input_call_counts == (2, 2)
    assert validation.output_call_counts == (2, 2)
    assert validation.balanced_forward_calls is True
    assert validation.complete is True
    assert validation.passed is True
