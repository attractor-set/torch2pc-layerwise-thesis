"""Regression test for the final thesis public documentation surface."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_public_surface_contract() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/check_public_surface.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "PUBLIC_README_CURRENTNESS=PASS" in completed.stdout
    assert "PUBLIC_STATUS_PRECEDENCE=PASS" in completed.stdout
    assert "PUBLIC_ROADMAP_PRECEDENCE=PASS" in completed.stdout
    assert "PUBLIC_DOC_INDEX_CURRENTNESS=PASS" in completed.stdout
    assert "PUBLIC_STRUCTURE_CURRENTNESS=PASS" in completed.stdout
    assert "PUBLIC_SUBREADME_CURRENTNESS=PASS" in completed.stdout
    assert "THESIS_V1_PUBLIC_SURFACE=PASS" in completed.stdout
