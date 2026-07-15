from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd
import torch
import torch.nn as nn
from torch.utils.hooks import RemovableHandle

OBSERVER_SCHEMA_ID = "stage3b-a1-obs-ni0-first-forward-io-v1"
OBSERVER_ROLES = ("layer_input", "layer_output")


def observer_schema_manifest(top_level_layers: int) -> dict[str, Any]:
    """Return the frozen OBS-NI0 observer schema for one model depth."""
    if top_level_layers < 1:
        raise ValueError("OBS-NI0 observer schema requires at least one layer")
    return {
        "observer_schema_id": OBSERVER_SCHEMA_ID,
        "capture_implementation": "top-level forward-pre and forward hooks",
        "capture_policy": "first forward invocation per top-level layer",
        "additional_forward_calls": "counted but not captured",
        "payload_copy": "tensor.detach().clone()",
        "roles": list(OBSERVER_ROLES),
        "records_per_top_level_layer": len(OBSERVER_ROLES),
        "expected_top_level_layers": top_level_layers,
        "expected_records_per_arm_run": top_level_layers * len(OBSERVER_ROLES),
        "record_key_format": "layer-{index:02d}:{role}:00",
        "expected_occurrences_per_role": 1,
        "cleanup_rule": "remove all observer handles and restore baseline hook ids",
        "serialization_phase": "after observed execution and hook cleanup",
    }


@dataclass(frozen=True)
class ObserverPayload:
    """One graph-free tensor captured by the passive OBS-NI0 observer."""

    key: str
    layer_index: int
    layer_name: str
    role: str
    occurrence: int
    tensor: torch.Tensor
    source_shape: tuple[int, ...]
    source_dtype: str
    source_device: str

    @property
    def finite(self) -> bool:
        if torch.is_floating_point(self.tensor) or torch.is_complex(self.tensor):
            return bool(torch.isfinite(self.tensor).all())
        return True

    @property
    def detached(self) -> bool:
        return not self.tensor.requires_grad and self.tensor.grad_fn is None

    @property
    def metadata_preserved(self) -> bool:
        return (
            tuple(int(value) for value in self.tensor.shape) == self.source_shape
            and str(self.tensor.dtype) == self.source_dtype
            and str(self.tensor.device) == self.source_device
        )

    def to_record(self) -> dict[str, Any]:
        return {
            "observer_schema_id": OBSERVER_SCHEMA_ID,
            "key": self.key,
            "layer_index": self.layer_index,
            "layer_name": self.layer_name,
            "role": self.role,
            "occurrence": self.occurrence,
            "shape": list(self.source_shape),
            "dtype": self.source_dtype,
            "device": self.source_device,
            "numel": self.tensor.numel(),
            "requires_grad": self.tensor.requires_grad,
            "grad_fn_is_none": self.tensor.grad_fn is None,
            "detached": self.detached,
            "finite": self.finite,
            "metadata_preserved": self.metadata_preserved,
        }


@dataclass(frozen=True)
class ObserverValidation:
    """Structural and lifecycle validation for one observer execution."""

    observer_schema_id: str
    top_level_layers: int
    expected_records: int
    observed_records: int
    input_call_counts: tuple[int, ...]
    output_call_counts: tuple[int, ...]
    complete: bool
    balanced_forward_calls: bool
    unique_keys: bool
    detached: bool
    finite: bool
    metadata_preserved: bool
    cleanup_complete: bool
    setup_rng_unchanged: bool

    @property
    def passed(self) -> bool:
        return (
            self.complete
            and self.balanced_forward_calls
            and self.unique_keys
            and self.detached
            and self.finite
            and self.metadata_preserved
            and self.cleanup_complete
            and self.setup_rng_unchanged
        )

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["passed"] = self.passed
        return result


class PassiveLayerObserver:
    """Read-only first-forward I/O observer for top-level sequential layers.

    The observer captures only the first input and first output observed for each
    top-level layer. Later forward invocations are counted but not cloned. This
    keeps the payload schema fixed across execution paths whose internal forward
    call counts differ, including iterative FixedPred and the joint-VJP shortcut.

    Capture uses only ``tensor.detach().clone()``. The observer stores no source
    tensor and therefore retains no live autograd graph. It registers one
    forward-pre hook and one forward hook per top-level layer and removes every
    handle before validation.
    """

    def __init__(self, model: nn.Sequential) -> None:
        if not isinstance(model, nn.Sequential):
            raise TypeError("OBS-NI0 observer requires a top-level nn.Sequential model")
        if len(model) < 1:
            raise ValueError("OBS-NI0 observer requires at least one top-level layer")

        self._model = model
        self._records: list[ObserverPayload] = []
        self._occurrences: Counter[tuple[int, str]] = Counter()
        self._handles: list[RemovableHandle] = []
        self._baseline_hooks = {
            index: self._hook_ids(layer) for index, layer in enumerate(model)
        }
        self._started = False
        self._closed = False
        self._cleanup_complete = False

    @staticmethod
    def _hook_ids(layer: nn.Module) -> tuple[frozenset[int], frozenset[int]]:
        pre_hooks = getattr(layer, "_forward_pre_hooks", {})
        forward_hooks = getattr(layer, "_forward_hooks", {})
        return frozenset(pre_hooks), frozenset(forward_hooks)

    @property
    def records(self) -> tuple[ObserverPayload, ...]:
        return tuple(self._records)

    @property
    def expected_records(self) -> int:
        return len(self._model) * len(OBSERVER_ROLES)

    def start(self) -> None:
        if self._started:
            raise RuntimeError("OBS-NI0 observer has already been started")
        if self._closed:
            raise RuntimeError("OBS-NI0 observer has already been closed")

        for layer_index, layer in enumerate(self._model):
            layer_name = str(layer_index)

            def pre_hook(
                _module: nn.Module,
                args: tuple[Any, ...],
                *,
                index: int = layer_index,
                name: str = layer_name,
            ) -> None:
                if len(args) != 1 or not isinstance(args[0], torch.Tensor):
                    raise TypeError(
                        "OBS-NI0 requires each top-level layer to receive one tensor"
                    )
                self._capture(index, name, "layer_input", args[0])

            def forward_hook(
                _module: nn.Module,
                _args: tuple[Any, ...],
                output: Any,
                *,
                index: int = layer_index,
                name: str = layer_name,
            ) -> None:
                if not isinstance(output, torch.Tensor):
                    raise TypeError(
                        "OBS-NI0 requires each top-level layer to return one tensor"
                    )
                self._capture(index, name, "layer_output", output)

            self._handles.append(layer.register_forward_pre_hook(pre_hook))
            self._handles.append(layer.register_forward_hook(forward_hook))

        self._started = True

    def _capture(
        self,
        layer_index: int,
        layer_name: str,
        role: str,
        source: torch.Tensor,
    ) -> None:
        occurrence_key = (layer_index, role)
        occurrence = self._occurrences[occurrence_key]
        self._occurrences[occurrence_key] += 1
        if occurrence > 0:
            return

        key = f"layer-{layer_index:02d}:{role}:00"
        captured = source.detach().clone()
        self._records.append(
            ObserverPayload(
                key=key,
                layer_index=layer_index,
                layer_name=layer_name,
                role=role,
                occurrence=0,
                tensor=captured,
                source_shape=tuple(int(value) for value in source.shape),
                source_dtype=str(source.dtype),
                source_device=str(source.device),
            )
        )

    def close(self) -> None:
        if self._closed:
            return
        for handle in reversed(self._handles):
            handle.remove()
        self._handles.clear()
        self._closed = True
        self._cleanup_complete = all(
            self._hook_ids(layer) == self._baseline_hooks[index]
            for index, layer in enumerate(self._model)
        )

    def validate(self, *, setup_rng_unchanged: bool) -> ObserverValidation:
        if not self._closed:
            raise RuntimeError("OBS-NI0 observer must be closed before validation")

        expected_pairs = {
            (layer_index, role)
            for layer_index in range(len(self._model))
            for role in OBSERVER_ROLES
        }
        observed_pairs = Counter(
            (record.layer_index, record.role) for record in self._records
        )
        complete = (
            set(observed_pairs) == expected_pairs
            and all(observed_pairs[pair] == 1 for pair in expected_pairs)
        )
        input_call_counts = tuple(
            self._occurrences[(layer_index, "layer_input")]
            for layer_index in range(len(self._model))
        )
        output_call_counts = tuple(
            self._occurrences[(layer_index, "layer_output")]
            for layer_index in range(len(self._model))
        )
        balanced_forward_calls = input_call_counts == output_call_counts and all(
            count >= 1 for count in input_call_counts
        )
        keys = [record.key for record in self._records]

        return ObserverValidation(
            observer_schema_id=OBSERVER_SCHEMA_ID,
            top_level_layers=len(self._model),
            expected_records=self.expected_records,
            observed_records=len(self._records),
            input_call_counts=input_call_counts,
            output_call_counts=output_call_counts,
            complete=complete,
            balanced_forward_calls=balanced_forward_calls,
            unique_keys=len(keys) == len(set(keys)),
            detached=all(record.detached for record in self._records),
            finite=all(record.finite for record in self._records),
            metadata_preserved=all(
                record.metadata_preserved for record in self._records
            ),
            cleanup_complete=self._cleanup_complete,
            setup_rng_unchanged=setup_rng_unchanged,
        )

    def records_frame(self) -> pd.DataFrame:
        return pd.DataFrame.from_records(record.to_record() for record in self._records)
