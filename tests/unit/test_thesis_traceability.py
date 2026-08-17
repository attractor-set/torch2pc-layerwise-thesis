"""Regression tests for thesis claim-to-section traceability."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_thesis_claim_traceability_is_closed() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/check_thesis_traceability.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    output = completed.stdout

    assert "THESIS_CLAIM_TRACEABILITY_SCHEMA=PASS" in output
    assert "THESIS_CLAIM_TRACEABILITY_STATUS=PASS" in output
    assert "THESIS_CLAIM_TRACEABILITY_SECTIONS=PASS" in output
    assert "THESIS_CLAIM_LOCAL_BINDINGS=PASS" in output
    assert "THESIS_CLAIM_SURFACE_CLOSURE=PASS" in output
