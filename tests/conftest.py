"""Successor-aware historical views for immutable QW-LC4-E stage tests."""

from __future__ import annotations

import base64
import shutil
import sys
from pathlib import Path

import pytest

_PRE_CALLSITE_TEST_FILES = {
    "test_stage3b_qwake_lc4_final_execution_acknowledgement_materialization_"
    "invocation_operation_implementation.py",
    "test_stage3b_qwake_lc4_final_execution_acknowledgement_materialization_"
    "invocation_operation_callsite_authoring.py",
}
_PRE_AUTHORIZATION_TEST_FILES = {
    "test_stage3b_qwake_lc4_final_execution_acknowledgement_materialization_"
    "invocation_operation_callsite_implementation.py",
    "test_stage3b_qwake_lc4_final_execution_acknowledgement_materialization_"
    "invocation_operation_callsite_execution_authoring.py",
}
_PRE_ATTEMPT003_FREEZE_TEST_FILES = {
    "test_stage3b_qwake_attempt_003_execution_freeze_materialization.py",
}

_PRODUCTION_CALLSITE = Path(
    "scripts/invoke_stage3b_qwake_lc4_final_execution_acknowledgement_"
    "materialization_operation.py"
)
_EXECUTION_AUTHORIZATION_PACKAGE = Path(
    "experiments/frozen/stage3b-qwake-lc4-e-final-execution-"
    "acknowledgement-materialization-invocation-operation-callsite-execution-"
    "authorization-v1"
)
_ATTEMPT003_EXECUTION_FREEZE_PACKAGE = Path(
    "experiments/frozen/stage3b-qwake-attempt-003-execution-freeze-v1"
)

_HISTORICAL_CONFTEST_BYTES = base64.b64decode(
    "IiIiU3VjY2Vzc29yLWF3YXJlIGhpc3RvcmljYWwgdmlld3MgZm9yIGltbXV0YWJsZSBRVy1MQzQtRSBzdGFnZSB0ZXN0cy4iIiIKCmZyb20gX19mdXR1cmVfXyBpbXBvcnQgYW5ub3RhdGlvbnMKCmltcG9ydCBzaHV0aWwKaW1wb3J0IHN5cwpmcm9tIHBhdGhsaWIgaW1wb3J0IFBhdGgKCmltcG9ydCBweXRlc3QKCl9ISVNUT1JJQ0FMX1RFU1RfRklMRVMgPSB7CiAgICAidGVzdF9zdGFnZTNiX3F3YWtlX2xjNF9maW5hbF9leGVjdXRpb25fYWNrbm93bGVkZ2VtZW50X21hdGVyaWFsaXphdGlvbl8iCiAgICAiaW52b2NhdGlvbl9vcGVyYXRpb25faW1wbGVtZW50YXRpb24ucHkiLAogICAgInRlc3Rfc3RhZ2UzYl9xd2FrZV9sYzRfZmluYWxfZXhlY3V0aW9uX2Fja25vd2xlZGdlbWVudF9tYXRlcmlhbGl6YXRpb25fIgogICAgImludm9jYXRpb25fb3BlcmF0aW9uX2NhbGxzaXRlX2F1dGhvcmluZy5weSIsCn0KX1BST0RVQ1RJT05fQ0FMTFNJVEUgPSBQYXRoKAogICAgInNjcmlwdHMvaW52b2tlX3N0YWdlM2JfcXdha2VfbGM0X2ZpbmFsX2V4ZWN1dGlvbl9hY2tub3dsZWRnZW1lbnRfIgogICAgIm1hdGVyaWFsaXphdGlvbl9vcGVyYXRpb24ucHkiCikKCgpAcHl0ZXN0LmZpeHR1cmUoc2NvcGU9InNlc3Npb24iLCBhdXRvdXNlPVRydWUpCmRlZiBfaGlzdG9yaWNhbF9xd2FrZV9zdGFnZV92aWV3cygKICAgIHRtcF9wYXRoX2ZhY3Rvcnk6IHB5dGVzdC5UZW1wUGF0aEZhY3RvcnksCik6CiAgICByb290ID0gUGF0aChfX2ZpbGVfXykucmVzb2x2ZSgpLnBhcmVudHNbMV0KICAgIGhpc3RvcmljYWxfcm9vdCA9IHRtcF9wYXRoX2ZhY3RvcnkubWt0ZW1wKCJxd2FrZS1oaXN0b3JpY2FsLXN0YWdlLXZpZXciKSAvICJyZXBvc2l0b3J5IgogICAgc2h1dGlsLmNvcHl0cmVlKAogICAgICAgIHJvb3QsCiAgICAgICAgaGlzdG9yaWNhbF9yb290LAogICAgICAgIGlnbm9yZT1zaHV0aWwuaWdub3JlX3BhdHRlcm5zKAogICAgICAgICAgICAiLmdpdCIsCiAgICAgICAgICAgICIubXlweV9jYWNoZSIsCiAgICAgICAgICAgICIucHl0ZXN0X2NhY2hlIiwKICAgICAgICAgICAgIi5ydWZmX2NhY2hlIiwKICAgICAgICAgICAgIl9fcHljYWNoZV9fIiwKICAgICAgICAgICAgInNpdGUiLAogICAgICAgICAgICAic2l0ZV9ydSIsCiAgICAgICAgICAgICJzaXRlX2VuIiwKICAgICAgICApLAogICAgKQogICAgY2FsbHNpdGUgPSBoaXN0b3JpY2FsX3Jvb3QgLyBfUFJPRFVDVElPTl9DQUxMU0lURQogICAgaWYgY2FsbHNpdGUuZXhpc3RzKCkgb3IgY2FsbHNpdGUuaXNfc3ltbGluaygpOgogICAgICAgIGNhbGxzaXRlLnVubGluaygpCgogICAgcHJldmlvdXM6IGRpY3Rbc3RyLCBQYXRoXSA9IHt9CiAgICBmb3IgbW9kdWxlX25hbWUsIG1vZHVsZSBpbiB0dXBsZShzeXMubW9kdWxlcy5pdGVtcygpKToKICAgICAgICBtb2R1bGVfZmlsZSA9IGdldGF0dHIobW9kdWxlLCAiX19maWxlX18iLCBOb25lKQogICAgICAgIGlmIG1vZHVsZV9maWxlIGlzIE5vbmUgb3Igbm90IGhhc2F0dHIobW9kdWxlLCAiUk9PVCIpOgogICAgICAgICAgICBjb250aW51ZQogICAgICAgIGlmIFBhdGgobW9kdWxlX2ZpbGUpLm5hbWUgbm90IGluIF9ISVNUT1JJQ0FMX1RFU1RfRklMRVM6CiAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgcHJldmlvdXNbbW9kdWxlX25hbWVdID0gbW9kdWxlLlJPT1QKICAgICAgICBtb2R1bGUuUk9PVCA9IGhpc3RvcmljYWxfcm9vdAoKICAgIHlpZWxkCgogICAgZm9yIG1vZHVsZV9uYW1lLCBvcmlnaW5hbF9yb290IGluIHByZXZpb3VzLml0ZW1zKCk6CiAgICAgICAgbW9kdWxlID0gc3lzLm1vZHVsZXMuZ2V0KG1vZHVsZV9uYW1lKQogICAgICAgIGlmIG1vZHVsZSBpcyBub3QgTm9uZToKICAgICAgICAgICAgbW9kdWxlLlJPT1QgPSBvcmlnaW5hbF9yb290Cg=="
)


def _copy_repository(root: Path, target: Path) -> Path:
    shutil.copytree(
        root,
        target,
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
    return target


@pytest.fixture(scope="session", autouse=True)
def _historical_qwake_stage_views(
    tmp_path_factory: pytest.TempPathFactory,
):
    root = Path(__file__).resolve().parents[1]
    base = tmp_path_factory.mktemp("qwake-historical-stage-views")

    pre_callsite_root = _copy_repository(root, base / "pre-callsite")
    (pre_callsite_root / "tests/conftest.py").write_bytes(
        _HISTORICAL_CONFTEST_BYTES
    )
    callsite = pre_callsite_root / _PRODUCTION_CALLSITE
    if callsite.exists() or callsite.is_symlink():
        callsite.unlink()

    pre_authorization_root = _copy_repository(root, base / "pre-authorization")
    (pre_authorization_root / "tests/conftest.py").write_bytes(
        _HISTORICAL_CONFTEST_BYTES
    )
    authorization_package = pre_authorization_root / _EXECUTION_AUTHORIZATION_PACKAGE
    if authorization_package.exists() or authorization_package.is_symlink():
        shutil.rmtree(authorization_package)

    pre_attempt003_freeze_root = _copy_repository(
        root,
        base / "pre-attempt003-freeze",
    )
    (pre_attempt003_freeze_root / "tests/conftest.py").write_bytes(
        _HISTORICAL_CONFTEST_BYTES
    )
    attempt003_freeze_package = (
        pre_attempt003_freeze_root / _ATTEMPT003_EXECUTION_FREEZE_PACKAGE
    )
    if (
        attempt003_freeze_package.exists()
        or attempt003_freeze_package.is_symlink()
    ):
        shutil.rmtree(attempt003_freeze_package)

    previous: dict[str, Path] = {}
    for module_name, module in tuple(sys.modules.items()):
        module_file = getattr(module, "__file__", None)
        if module_file is None or not hasattr(module, "ROOT"):
            continue
        filename = Path(module_file).name
        replacement: Path | None = None
        if filename in _PRE_CALLSITE_TEST_FILES:
            replacement = pre_callsite_root
        elif filename in _PRE_AUTHORIZATION_TEST_FILES:
            replacement = pre_authorization_root
        elif filename in _PRE_ATTEMPT003_FREEZE_TEST_FILES:
            replacement = pre_attempt003_freeze_root
        if replacement is None:
            continue
        previous[module_name] = module.ROOT
        module.ROOT = replacement

    yield

    for module_name, original_root in previous.items():
        module = sys.modules.get(module_name)
        if module is not None:
            module.ROOT = original_root
