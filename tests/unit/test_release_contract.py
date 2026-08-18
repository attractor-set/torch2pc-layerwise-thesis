"""Regression test for the final thesis release contract."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_release_contract() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/check_release_contract.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "RELEASE_VERSION_SURFACES=PASS" in completed.stdout
    assert "RELEASE_FROZEN_RUNTIME_CLOSURE=PASS" in completed.stdout
    assert "RELEASE_CHANGELOG_SURFACE=PASS" in completed.stdout
    assert "RELEASE_PUBLIC_SURFACE_CONTRACT=PASS" in completed.stdout
    assert "RELEASE_WORKFLOW_CONTRACT=PASS" in completed.stdout
    assert "RELEASE_ARTIFACT_CONTRACT=PASS" in completed.stdout
    assert "THESIS_V1_RELEASE_CONTRACT=PASS" in completed.stdout
