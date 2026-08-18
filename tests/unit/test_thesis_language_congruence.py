"""Regression test for the RU/EN dissertation semantic-congruence gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_thesis_language_congruence() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/check_thesis_language_congruence.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "THESIS_ENGLISH_STRUCTURE=PASS" in completed.stdout
    assert "THESIS_ENGLISH_CONTENT_COVERAGE=PASS" in completed.stdout
    assert "THESIS_BILINGUAL_ABSTRACT_IDENTITY=PASS" in completed.stdout
    assert "THESIS_ENGLISH_CLAIM_STATUS_SEMANTICS=PASS" in completed.stdout
    assert "THESIS_ENGLISH_TERMINOLOGY_INVARIANCE=PASS" in completed.stdout
    assert "THESIS_LANGUAGE_CONGRUENCE=PASS" in completed.stdout
