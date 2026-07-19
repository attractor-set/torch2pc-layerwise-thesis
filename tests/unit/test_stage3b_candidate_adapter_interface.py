from __future__ import annotations

import importlib
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import torch
import torch.nn as nn


@pytest.mark.parametrize(
    ("module_name", "loader_name", "pc_infer_name", "method", "steps"),
    (
        (
            "torch2pc_thesis.stage3b_b1_isolated_vjp",
            "load_b1_pc_infer",
            "pc_infer_b1",
            "FixedPred",
            7,
        ),
        (
            "torch2pc_thesis.stage3b_b2_composite_vjp",
            "load_b2_pc_infer",
            "pc_infer_b2",
            "Strict",
            9,
        ),
    ),
)
def test_candidate_adapter_accepts_canonical_pcinfer_n_keyword(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    module_name: str,
    loader_name: str,
    pc_infer_name: str,
    method: str,
    steps: int,
) -> None:
    module = importlib.import_module(module_name)
    observed: dict[str, object] = {}
    expected = object()

    def fake_load_patched_reference(*_args: Any, **_kwargs: Any) -> Any:
        return SimpleNamespace()

    def fake_pc_infer(*_args: Any, **kwargs: Any) -> Any:
        observed.update(kwargs)
        return expected

    monkeypatch.setattr(
        module,
        "load_patched_reference",
        fake_load_patched_reference,
    )
    monkeypatch.setattr(module, pc_infer_name, fake_pc_infer)

    loader = getattr(module, loader_name)
    assert callable(loader)
    adapter = loader(tmp_path)
    result = adapter(
        nn.Sequential(nn.Linear(4, 3)).double(),
        nn.CrossEntropyLoss(),
        torch.randn(2, 4, dtype=torch.float64),
        torch.randint(0, 3, (2,)),
        method,
        eta=0.2,
        n=steps,
    )

    assert result is expected
    assert observed["eta"] == 0.2
    assert observed["inference_steps"] == steps


@pytest.mark.parametrize(
    ("module_name", "loader_name"),
    (
        (
            "torch2pc_thesis.stage3b_b1_isolated_vjp",
            "load_b1_pc_infer",
        ),
        (
            "torch2pc_thesis.stage3b_b2_composite_vjp",
            "load_b2_pc_infer",
        ),
    ),
)
def test_candidate_adapter_rejects_conflicting_step_keywords(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    module_name: str,
    loader_name: str,
) -> None:
    module = importlib.import_module(module_name)

    def fake_load_patched_reference(*_args: Any, **_kwargs: Any) -> Any:
        return SimpleNamespace()

    monkeypatch.setattr(
        module,
        "load_patched_reference",
        fake_load_patched_reference,
    )

    loader = getattr(module, loader_name)
    assert callable(loader)
    adapter = loader(tmp_path)

    with pytest.raises(ValueError, match="conflicting PCInfer step counts"):
        adapter(
            nn.Sequential(nn.Linear(4, 3)).double(),
            nn.CrossEntropyLoss(),
            torch.randn(2, 4, dtype=torch.float64),
            torch.randint(0, 3, (2,)),
            "FixedPred",
            n=7,
            inference_steps=8,
        )
