"""Regression tests for thesis terminology and symbol invariance."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_thesis_semantic_contract_is_stable() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/check_thesis_semantic_contract.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    output = completed.stdout

    assert "THESIS_TERMINOLOGY_INVARIANCE=PASS" in output
    assert "THESIS_THEORY_LAYER_SEPARATION=PASS" in output
    assert "THESIS_QWAKE_RULE_VOCABULARY=PASS" in output
    assert "THESIS_SYMBOL_NAMESPACE=PASS" in output
    assert "THESIS_TERM_FIRST_DEFINITION=PASS" in output
    assert "THESIS_CLAIM_STATUS_SEMANTICS=PASS" in output
