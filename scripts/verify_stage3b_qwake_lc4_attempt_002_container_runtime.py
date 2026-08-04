#!/usr/bin/env python3
"""Verify the isolated attempt-002 container-runtime authoring package."""

from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
from typing import Final, cast

ROOT: Final = Path(__file__).resolve().parents[1]
PACKAGE_ROOT: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-attempt-002-container-runtime-authoring-v1"
)
AUTHORING: Final = PACKAGE_ROOT / "authoring.json"
PACKAGE_SUMS: Final = PACKAGE_ROOT / "SHA256SUMS"
SOURCE_SUMS: Final = PACKAGE_ROOT / "source-SHA256SUMS"
CONTRACT: Final = Path(
    "src/torch2pc_thesis/stage3b_qwake_lc4_attempt_002_contract.py"
)
WRAPPER: Final = Path(
    "src/torch2pc_thesis/stage3b_qwake_lc4_attempt_002_execution_wrapper.py"
)
BACKEND: Final = Path(
    "src/torch2pc_thesis/stage3b_qwake_lc4_attempt_002_runtime_backend.py"
)
ENTRYPOINT: Final = Path(
    "scripts/run_stage3b_qwake_lc4_attempt_002_authorized_runtime.py"
)
TEST: Final = Path(
    "tests/unit/test_stage3b_qwake_lc4_attempt_002_container_runtime.py"
)
ADR_RU: Final = Path(
    "docs/decisions/ADR-112-stage3b-qwake-lc4-e-"
    "attempt-002-container-runtime.md"
)
ADR_EN: Final = Path(
    "docs/decisions/ADR-112-stage3b-qwake-lc4-e-"
    "attempt-002-container-runtime_EN.md"
)
EXPECTED_SOURCE_HEAD: Final = "5e26c840b520c9b73fea316e25512788372d6975"
EXPECTED_TORCH2PC: Final = "b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4"
RUNTIME_SOURCES: Final = (CONTRACT, WRAPPER, BACKEND, ENTRYPOINT)
FORBIDDEN_TEXT: Final = (
    "attempt-001",
    "7da92b8f77f6dc37d42db832c5613ef6149dc488adc5b66465faa33e48ca021d",
    "stage3b-qwake-lc4-e-execution-freeze-v1",
)
FORBIDDEN_CALLS: Final = {
    "verify_materialized_execution_freeze",
    "verify_unconsumed_frozen_admission",
    "claim_execution_lease",
    "execute_authorized_runtime",
    "invoke_one_shot_host_runtime",
    "invoke_lease_bound_host_runtime",
}
FORBIDDEN_IMPORT_FRAGMENTS: Final = (
    "stage3b_qwake_lc4_execution_admission",
    "stage3b_qwake_lc4_invocation_authorization",
    "stage3b_qwake_lc4_persistent_evidence_chain_v2",
)


class VerificationError(RuntimeError):
    """Raised when the authoring package differs from its contract."""


def canonical_json(value: object) -> str:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    )


def sha256_file(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise VerificationError(f"regular file is absent: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, object]:
    if not path.is_file() or path.is_symlink():
        raise VerificationError(f"regular JSON is absent: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise VerificationError(f"JSON root differs: {path}")
    if path.read_bytes() != canonical_json(value).encode("utf-8"):
        raise VerificationError(f"JSON serialization differs: {path}")
    return cast(dict[str, object], value)


def verify_registry(path: Path, base: Path) -> tuple[str, ...]:
    if not path.is_file() or path.is_symlink():
        raise VerificationError(f"regular registry is absent: {path}")
    observed: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line:
            continue
        parts = raw_line.split("  ", 1)
        if len(parts) != 2:
            raise VerificationError("registry line shape differs")
        expected, relative = parts
        if len(expected) != 64 or any(
            character not in "0123456789abcdef" for character in expected
        ):
            raise VerificationError("registry digest differs")
        if relative in observed:
            raise VerificationError("registry path is duplicated")
        observed.append(relative)
        candidate = (base / relative).resolve()
        try:
            candidate.relative_to(base.resolve())
        except ValueError as exc:
            raise VerificationError("registry path escapes base") from exc
        if sha256_file(candidate) != expected:
            raise VerificationError(f"registry identity differs: {relative}")
    if not observed:
        raise VerificationError("registry is empty")
    return tuple(observed)


def verify_authoring_record() -> None:
    record = read_json(ROOT / AUTHORING)
    payload = dict(record)
    observed_digest = payload.pop("authoring_sha256", None)
    expected: dict[str, object] = {
        "schema_version": 1,
        "authoring_id": (
            "stage3b-qwake-lc4-e-attempt-002-container-runtime-authoring-v1"
        ),
        "status": (
            "isolated_container_runtime_authored_image_and_attempt_closed"
        ),
        "source_head": EXPECTED_SOURCE_HEAD,
        "torch2pc_commit": EXPECTED_TORCH2PC,
        "attempt_id": "stage3b-qwake-lc4-runtime-validation-v1-attempt-002",
        "container_runtime_authored": True,
        "effect_namespace_isolated": True,
        "same_admission_object_required": True,
        "atomic_lease_v1_required": True,
        "no_replace_output_promotion_required": True,
        "corrected_image_built": False,
        "execution_freeze_materialized": False,
        "authorization_issued": False,
        "lease_v1_present": False,
        "lease_v2_present": False,
        "durable_outcome_present": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "docker_invoked": False,
        "model_code_invoked": False,
        "attempt_001_modified": False,
        "qw5_opened": False,
    }
    for field_name, expected_value in expected.items():
        if payload.get(field_name) != expected_value:
            raise VerificationError(f"authoring field differs: {field_name}")
    expected_digest = "sha256:" + hashlib.sha256(
        canonical_json(payload).encode("utf-8")
    ).hexdigest()
    if observed_digest != expected_digest:
        raise VerificationError("authoring semantic digest differs")


def verify_runtime_sources() -> None:
    for relative in RUNTIME_SOURCES:
        text = (ROOT / relative).read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_TEXT:
            if forbidden in text:
                raise VerificationError(
                    f"forbidden historical identity in {relative}: {forbidden}"
                )
        tree = ast.parse(text, filename=relative.as_posix())
        imports: list[str] = []
        calls: list[tuple[int, str]] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
            elif isinstance(node, ast.Call):
                name = _call_name(node.func)
                if name:
                    calls.append((node.lineno, name))
        for imported in imports:
            if any(fragment in imported for fragment in FORBIDDEN_IMPORT_FRAGMENTS):
                raise VerificationError(
                    f"forbidden historical import in {relative}: {imported}"
                )
        for _, call_name in calls:
            if call_name in FORBIDDEN_CALLS:
                raise VerificationError(
                    f"forbidden historical call in {relative}: {call_name}"
                )

    entry_tree = ast.parse(
        (ROOT / ENTRYPOINT).read_text(encoding="utf-8"),
        filename=ENTRYPOINT.as_posix(),
    )
    functions = {
        node.name: node
        for node in entry_tree.body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    }
    function = functions.get("run_attempt_002_authorized_runtime")
    if not isinstance(function, ast.FunctionDef):
        raise VerificationError("attempt-002 runtime function is absent")
    ordered_calls = [
        name
        for _, name in sorted(
            (
                (node.lineno, _call_name(node.func))
                for node in ast.walk(function)
                if isinstance(node, ast.Call) and _call_name(node.func)
            ),
            key=lambda item: item[0],
        )
    ]
    required = [
        "verify_attempt_002_execution_freeze",
        "verify_unconsumed_attempt_002_authorization",
        "build_attempt_002_admission",
        "Attempt002RuntimeBackend",
        "build_attempt_002_lease",
        "materialize_attempt_002_lease",
        "run_claimed_attempt_002",
    ]
    cursor = 0
    for call_name in ordered_calls:
        if cursor < len(required) and call_name == required[cursor]:
            cursor += 1
    if cursor != len(required):
        raise VerificationError("attempt-002 call ordering differs")
    source = ast.unparse(function)
    for required_fragment in (
        "build_attempt_002_lease(admission",
        "materialize_attempt_002_lease(root, lease, admission)",
        "run_claimed_attempt_002(root, admission, lease",
    ):
        if required_fragment not in source:
            raise VerificationError(
                "attempt-002 admission-object reuse differs"
            )


def verify_closed_effect_boundary() -> None:
    forbidden = (
        Path("results/stage-3/qwake-lc4-runtime-validation-v1-attempt-002"),
        Path(
            "results/stage-3/"
            "qwake-lc4-runtime-validation-v1-attempt-002.execution-lease.json"
        ),
        Path(
            "results/stage-3/"
            "qwake-lc4-runtime-validation-v1-attempt-002.execution-lease-v2.json"
        ),
        Path(
            "results/stage-3/"
            "qwake-lc4-runtime-validation-v1-attempt-002.host-outcome.json"
        ),
        Path(
            "experiments/frozen/"
            "stage3b-qwake-lc4-e-attempt-002-execution-freeze-v1"
        ),
        Path(
            "experiments/frozen/"
            "stage3b-qwake-lc4-e-attempt-002-authorization-v1"
        ),
    )
    for relative in forbidden:
        if os.path.lexists(ROOT / relative):
            raise VerificationError(f"closed effect already exists: {relative}")


def _call_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def main() -> int:
    verify_authoring_record()
    package_files = verify_registry(ROOT / PACKAGE_SUMS, ROOT / PACKAGE_ROOT)
    source_files = verify_registry(ROOT / SOURCE_SUMS, ROOT)
    if set(package_files) != {"authoring.json", "source-SHA256SUMS"}:
        raise VerificationError("authoring package registry scope differs")
    expected_sources = {
        CONTRACT.as_posix(),
        WRAPPER.as_posix(),
        BACKEND.as_posix(),
        ENTRYPOINT.as_posix(),
        TEST.as_posix(),
        ADR_RU.as_posix(),
        ADR_EN.as_posix(),
        Path(__file__).resolve().relative_to(ROOT).as_posix(),
    }
    if set(source_files) != expected_sources:
        raise VerificationError("authoring source registry scope differs")
    verify_runtime_sources()
    verify_closed_effect_boundary()
    print("OK: isolated attempt-002 container runtime authoring verified")
    print("ATTEMPT_002_CONTAINER_RUNTIME_AUTHORED=true")
    print("CORRECTED_IMAGE_BUILT=false")
    print("ATTEMPT_002_AUTHORIZATION_ISSUED=false")
    print("ATTEMPT_002_CREATED=false")
    print("RUNTIME_INVOKED=false")
    print("DOCKER_INVOKED=false")
    print("QW5_OPENED=false")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except VerificationError as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1) from exc
