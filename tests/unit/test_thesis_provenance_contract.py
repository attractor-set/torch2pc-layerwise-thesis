"""Regression tests for thesis provenance gate semantics."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_thesis_provenance_gates_distinguish_local_bytes_from_sealed_ids() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/build_thesis_assets.py", "--check"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    output = completed.stdout

    assert "THESIS_QWAKE_LOCAL_SOURCE_BINDINGS=2/2_PASS" in output
    assert "THESIS_QWAKE_SEALED_IDENTIFIERS_PRESENT=5/5_PASS" in output
    assert "THESIS_PROVENANCE_CONTRACT=PASS" in output
    assert "THESIS_PROVENANCE_IDENTITIES=PASS" not in output
