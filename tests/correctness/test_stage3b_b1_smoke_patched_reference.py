from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import torch
import torch.nn as nn

from torch2pc_thesis.stage3b_b1_equivalence import sha256_file
from torch2pc_thesis.stage3b_b1_smoke import (
    AssetRef,
    LaneControl,
    MethodControl,
    PairSpec,
    run_pair,
)

ROOT = Path(__file__).resolve().parents[2]
TORCH2PC_DIR = ROOT / "external/Torch2PC"
EXPECTED_COMMIT = "b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4"


def _prepared_reference_available() -> bool:
    if not (TORCH2PC_DIR / "TorchSeq2PC.py").is_file():
        return False
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=TORCH2PC_DIR,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0 and completed.stdout.strip() == EXPECTED_COMMIT


pytestmark = pytest.mark.skipif(
    not _prepared_reference_available(),
    reason="prepared external/Torch2PC checkout is unavailable",
)


def _model() -> nn.Sequential:
    return nn.Sequential(
        nn.Linear(4, 6),
        nn.Tanh(),
        nn.Linear(6, 5),
        nn.Tanh(),
        nn.Linear(5, 3),
    ).double()


def _builder(name: str) -> nn.Sequential:
    assert name == "lenet_classic"
    return _model()


@pytest.mark.correctness
@pytest.mark.parametrize(("method", "eta"), [("FixedPred", 0.1), ("Strict", 0.05)])
def test_smoke_pair_passes_against_actual_patched_reference(
    tmp_path: Path,
    method: str,
    eta: float,
) -> None:
    torch.manual_seed(123)
    checkpoint = tmp_path / "checkpoint.pt"
    batch = tmp_path / "batch.pt"
    torch.save(_model().state_dict(), checkpoint)
    torch.save(
        {
            "split": "validation",
            "inputs": torch.randn(8, 4, dtype=torch.float64),
            "targets": torch.randint(0, 3, (8,)),
        },
        batch,
    )
    spec = PairSpec(
        request_id="correctness",
        attempt_id="correctness-attempt",
        lane="cpu_float64",
        method=method,
        model_seed=0,
        batch_index=0,
        run_seed=77,
        checkpoint=AssetRef(str(checkpoint), sha256_file(checkpoint)),
        batch=AssetRef(str(batch), sha256_file(batch)),
        method_control=MethodControl(eta=eta, inference_steps=3),
        lane_control=LaneControl(device="cpu", dtype="float64"),
        training_mode=True,
        resolved_config_digest="a" * 64,
        source_image_digest="b" * 64,
    )
    result = run_pair(spec, torch2pc_dir=TORCH2PC_DIR, model_builder=_builder)
    assert result.pair_admissible
    assert all(bool(gate["passed"]) for gate in result.gates.values())
