from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

from tests.unit.test_stage3b_b2_smoke import request_payload
from torch2pc_thesis.stage3b_b2_smoke import CANDIDATE_ID

SCRIPT = Path("scripts/run_stage3b_b2_smoke.py")


def _load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("run_stage3b_b2_smoke", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_runner_dry_run_lists_all_twelve_triples(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    request_path = tmp_path / "request.json"
    request_path.write_text(json.dumps(request_payload()), encoding="utf-8")
    module = _load_script()
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "--request", str(request_path)])

    status = module.main()
    payload = json.loads(capsys.readouterr().out)

    assert status == 0
    assert payload["execute"] is False
    assert payload["matched_triples"] == 12
    assert payload["pairwise_comparisons"] == 24
    assert len(payload["selected_pairs"]) == 12


def test_runner_dry_run_filters_rocm_lane(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    request_path = tmp_path / "request.json"
    request = request_payload()
    request["resolved_config"]["candidate_id"] = CANDIDATE_ID
    request_path.write_text(json.dumps(request), encoding="utf-8")
    module = _load_script()
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(SCRIPT),
            "--request",
            str(request_path),
            "--lane",
            "rocm_float32",
        ],
    )

    status = module.main()
    payload = json.loads(capsys.readouterr().out)

    assert status == 0
    assert payload["matched_triples"] == 6
    assert payload["pairwise_comparisons"] == 12
    assert all(
        pair_id.startswith("rocm_float32__") for pair_id in payload["selected_pairs"]
    )
