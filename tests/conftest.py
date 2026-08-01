"""Successor-aware historical views for immutable QW-LC4-E stage tests."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

_HISTORICAL_TEST_FILES = {
    "test_stage3b_qwake_lc4_final_execution_acknowledgement_materialization_"
    "invocation_operation_implementation.py",
    "test_stage3b_qwake_lc4_final_execution_acknowledgement_materialization_"
    "invocation_operation_callsite_authoring.py",
}
_PRODUCTION_CALLSITE = Path(
    "scripts/invoke_stage3b_qwake_lc4_final_execution_acknowledgement_"
    "materialization_operation.py"
)


@pytest.fixture(scope="session", autouse=True)
def _historical_qwake_stage_views(
    tmp_path_factory: pytest.TempPathFactory,
):
    root = Path(__file__).resolve().parents[1]
    historical_root = tmp_path_factory.mktemp("qwake-historical-stage-view") / "repository"
    shutil.copytree(
        root,
        historical_root,
        ignore=shutil.ignore_patterns(
            ".git",
            ".mypy_cache",
            ".pytest_cache",
            ".ruff_cache",
            "__pycache__",
            "site",
            "site_ru",
            "site_en",
        ),
    )
    callsite = historical_root / _PRODUCTION_CALLSITE
    if callsite.exists() or callsite.is_symlink():
        callsite.unlink()

    previous: dict[str, Path] = {}
    for module_name, module in tuple(sys.modules.items()):
        module_file = getattr(module, "__file__", None)
        if module_file is None or not hasattr(module, "ROOT"):
            continue
        if Path(module_file).name not in _HISTORICAL_TEST_FILES:
            continue
        previous[module_name] = module.ROOT
        module.ROOT = historical_root

    yield

    for module_name, original_root in previous.items():
        module = sys.modules.get(module_name)
        if module is not None:
            module.ROOT = original_root
