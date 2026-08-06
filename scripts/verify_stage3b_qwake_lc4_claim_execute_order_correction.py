#!/usr/bin/env python3
"""Verify the immutable QW-LC4 claim/execute ordering correction package."""

from __future__ import annotations

import ast
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = (
    ROOT
    / "experiments/frozen/"
    "stage3b-qwake-lc4-e-claim-execute-order-correction-v1"
)
RECORD = PACKAGE / "correction.json"
PATCH = PACKAGE / "runtime-entrypoint.patch"
CORRECTED_ENTRYPOINT = PACKAGE / "run_stage3b_qwake_lc4_authorized_runtime.py"
PACKAGE_REGISTRY = PACKAGE / "SHA256SUMS"
SOURCE_REGISTRY = PACKAGE / "source-SHA256SUMS"
ORIGINAL_ENTRYPOINT = ROOT / "scripts/run_stage3b_qwake_lc4_authorized_runtime.py"
EXPECTED_FILES = {
    "SHA256SUMS",
    "correction.json",
    "run_stage3b_qwake_lc4_authorized_runtime.py",
    "runtime-entrypoint.patch",
    "source-SHA256SUMS",
}
EXPECTED_CORRECTION_ID = (
    "stage3b-qwake-lc4-e-claim-execute-order-correction-v1"
)
EXPECTED_STATUS = (
    "entrypoint_overlay_authored_image_not_built_attempt_002_not_authorized"
)
EXPECTED_BASE_COMMIT = "26e0328bbec433d6f2ec1841ee76a8c2c4312ccc"
EXPECTED_TORCH2PC_COMMIT = "b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4"
EXPECTED_ORIGINAL_ENTRYPOINT_SHA256 = (
    "sha256:504c3e614e199789b25c8b1927d0a35b1b95e1f3a5411e42db794fc93782cc79"
)
EXPECTED_CORRECTED_ENTRYPOINT_SHA256 = (
    "sha256:010eeba2c594288a6b8edf9a698a0117c5e2539879a30cb22fe7ceb45e6bcf46"
)
EXPECTED_PATCH_SHA256 = (
    "sha256:27c3d027e019a70a3378c8f4fa1068da5d8c1a238bebd7194edb8d53280837b9"
)
EXPECTED_TERMINAL_RECEIPT_FILE_SHA256 = (
    "sha256:9004103dd1a54299a8e217422f7b2c36d47f4bca5b9a81dd8f36f99cd9b6cf66"
)
EXPECTED_TERMINAL_RECEIPT_SHA256 = (
    "sha256:649c2a723049e703c3ae1232d18ea9fbde25c393ff4b1047bfb6c5154e608f8f"
)
EXPECTED_CORRECTION_SHA256 = (
    "sha256:d3096cf40edc0ab2730f3eb500108be680f47de8e0180571266a88f7e2abdcef"
)
EXPECTED_HISTORICAL_SOURCE_SHA256 = {
    "scripts/run_stage3b_qwake_lc4_authorized_runtime.py": (
        "sha256:504c3e614e199789b25c8b1927d0a35b1b95e1f3a5411e42db794fc93782cc79"
    ),
    "src/torch2pc_thesis/stage3b_qwake_lc4_execution_admission.py": (
        "sha256:18a629558206574041262af955ffca5b8af62fbb2b79bce736f1b645b9b4bdd3"
    ),
    "src/torch2pc_thesis/stage3b_qwake_lc4_execution_wrapper.py": (
        "sha256:34980a70d76b582d70333034b4a259b50bd948bb751888f17db9a988c2c77a9b"
    ),
    "src/torch2pc_thesis/stage3b_qwake_lc4_execution_wrapper_implementation.py": (
        "sha256:43e114dfdb69fa54a993a98b2a487777c40168374e61c0949e5cf862d42f7d9f"
    ),
    "src/torch2pc_thesis/stage3b_qwake_lc4_runtime_backend.py": (
        "sha256:d9ad10efe959e19d7f1b6d61d8eddd1228cb9753fa9191823d5d1ded68e9fd72"
    ),
}

EXPECTED_SOURCE_PATHS = {
    "scripts/run_stage3b_qwake_lc4_authorized_runtime.py",
    "scripts/verify_stage3b_qwake_lc4_claim_execute_order_correction.py",
    "src/torch2pc_thesis/stage3b_qwake_lc4_execution_admission.py",
    "src/torch2pc_thesis/stage3b_qwake_lc4_execution_wrapper.py",
    "src/torch2pc_thesis/stage3b_qwake_lc4_execution_wrapper_implementation.py",
    "src/torch2pc_thesis/stage3b_qwake_lc4_runtime_backend.py",
    "tests/unit/test_stage3b_qwake_lc4_claim_execute_order_correction.py",
}

EXPECTED_CALL_ORDER = [
    "verify_materialized_execution_freeze",
    "verify_operator_acknowledgement",
    "capture_unconsumed_frozen_admission",
    "construct_runtime_backend",
    "build_prospective_lease_from_captured_admission",
    "materialize_lease_from_same_captured_admission",
    "run_claimed_wrapper_with_same_captured_admission",
]


class VerificationError(RuntimeError):
    """Raised when the correction package differs from its exact contract."""


def canonical_json(value: object) -> str:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    )


def sha256_bytes(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise VerificationError(f"non-regular file: {path}")
    return sha256_bytes(path.read_bytes())


def read_json(path: Path) -> dict[str, Any]:
    try:
        value: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise VerificationError(f"cannot decode JSON: {path}") from exc
    if not isinstance(value, dict):
        raise VerificationError(f"JSON root is not an object: {path}")
    return value


def read_registry(path: Path) -> dict[str, str]:
    registry: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        try:
            digest, relative = line.split("  ", 1)
        except ValueError as exc:
            raise VerificationError("invalid registry line") from exc
        relative_path = Path(relative)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise VerificationError(f"unsafe registry path: {relative}")
        if len(digest) != 64 or any(
            char not in "0123456789abcdef" for char in digest
        ):
            raise VerificationError(f"invalid registry digest: {relative}")
        if relative in registry:
            raise VerificationError(f"duplicate registry path: {relative}")
        registry[relative] = digest
    if not registry:
        raise VerificationError(f"empty registry: {path}")
    return registry


def verify_registry(path: Path, base: Path) -> set[str]:
    registry = read_registry(path)
    resolved_base = base.resolve()
    for relative, expected in registry.items():
        target = (base / relative).resolve()
        if target != resolved_base and resolved_base not in target.parents:
            raise VerificationError(f"registry path leaves base: {relative}")
        observed = sha256_file(target).removeprefix("sha256:")
        if observed != expected:
            raise VerificationError(f"registry digest differs: {relative}")
    return set(registry)


def verify_record() -> dict[str, Any]:
    record = read_json(RECORD)
    expected_top_level = {
        "schema_version",
        "correction_id",
        "status",
        "authored_at_utc",
        "source",
        "defect",
        "contract",
        "gates",
        "next_slice",
        "correction_sha256",
    }
    if set(record) != expected_top_level:
        raise VerificationError("correction record field set differs")

    semantic = dict(record)
    observed_semantic = semantic.pop("correction_sha256", None)
    expected_semantic = sha256_bytes(canonical_json(semantic).encode("utf-8"))
    if observed_semantic != expected_semantic:
        raise VerificationError("correction semantic digest differs")
    if observed_semantic != EXPECTED_CORRECTION_SHA256:
        raise VerificationError("correction semantic identity differs")
    if RECORD.read_text(encoding="utf-8") != canonical_json(record):
        raise VerificationError("correction record serialization differs")

    expected_source = {
        "base_commit": EXPECTED_BASE_COMMIT,
        "torch2pc_commit": EXPECTED_TORCH2PC_COMMIT,
        "original_entrypoint_path": (
            "scripts/run_stage3b_qwake_lc4_authorized_runtime.py"
        ),
        "original_entrypoint_sha256": EXPECTED_ORIGINAL_ENTRYPOINT_SHA256,
        "corrected_entrypoint_path": (
            "experiments/frozen/"
            "stage3b-qwake-lc4-e-claim-execute-order-correction-v1/"
            "run_stage3b_qwake_lc4_authorized_runtime.py"
        ),
        "corrected_entrypoint_sha256": EXPECTED_CORRECTED_ENTRYPOINT_SHA256,
        "patch_path": (
            "experiments/frozen/"
            "stage3b-qwake-lc4-e-claim-execute-order-correction-v1/"
            "runtime-entrypoint.patch"
        ),
        "patch_sha256": EXPECTED_PATCH_SHA256,
        "patch_apply_mode": "git_apply_unidiff_zero",
    }
    expected_defect = {
        "attempt_id": "qwake-lc4-runtime-validation-v1-attempt-001",
        "termination_class": "nonzero_return_code",
        "return_code": 1,
        "child_spawn_count": 1,
        "terminal_receipt_file_sha256": (
            EXPECTED_TERMINAL_RECEIPT_FILE_SHA256
        ),
        "terminal_receipt_sha256": EXPECTED_TERMINAL_RECEIPT_SHA256,
        "failure": "post_claim_reentry_into_unconsumed_admission_validation",
    }
    expected_contract = {
        "call_order": EXPECTED_CALL_ORDER,
        "historical_entrypoint_preserved": True,
        "correction_applied_only_during_corrected_image_build": True,
        "same_admission_identity_used_for_build_materialize_and_execute": True,
        "lease_claim_atomicity_preserved": True,
        "output_promotion_noreplace_preserved": True,
        "attempt_001_terminal_evidence_preserved": True,
        "attempt_002_required": True,
        "post_claim_unconsumed_admission_revalidation": False,
        "attempt_001_retry_permitted": False,
    }
    expected_gates = {
        "attempt_001_reuse_permitted": False,
        "attempt_002_authorized": False,
        "corrected_execution_freeze_materialized": False,
        "corrected_image_built": False,
        "engineering_evidence_present": False,
        "historical_source_modified": False,
        "publication_permitted": False,
        "qw5_opened": False,
        "runtime_execution_performed": False,
        "runtime_execution_started": False,
        "scientific_execution_open": False,
        "test_dataset_access": False,
    }
    expected_exact = {
        "schema_version": 1,
        "correction_id": EXPECTED_CORRECTION_ID,
        "status": EXPECTED_STATUS,
        "authored_at_utc": "2026-08-04T12:58:04Z",
        "source": expected_source,
        "defect": expected_defect,
        "contract": expected_contract,
        "gates": expected_gates,
        "next_slice": (
            "QW-LC4-E-claim-execute-order-correction-"
            "image-and-attempt-002-materialization"
        ),
        "correction_sha256": EXPECTED_CORRECTION_SHA256,
    }
    if record != expected_exact:
        raise VerificationError("correction record differs from exact contract")
    return record


def verify_patch_reconstruction() -> None:
    with tempfile.TemporaryDirectory(prefix="qwake-lc4-correction-") as raw:
        temporary = Path(raw)
        target = temporary / "scripts/run_stage3b_qwake_lc4_authorized_runtime.py"
        target.parent.mkdir(parents=True)
        shutil.copyfile(ORIGINAL_ENTRYPOINT, target)
        completed = subprocess.run(
            ("git", "apply", "--unidiff-zero", "--check", str(PATCH)),
            cwd=temporary,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode == 0:
            completed = subprocess.run(
                ("git", "apply", "--unidiff-zero", str(PATCH)),
                cwd=temporary,
                capture_output=True,
                text=True,
                check=False,
            )
        if completed.returncode != 0:
            raise VerificationError(
                "entrypoint patch cannot be reconstructed: "
                + completed.stderr.strip()
            )
        if target.read_bytes() != CORRECTED_ENTRYPOINT.read_bytes():
            raise VerificationError("patch output differs from corrected entrypoint")


def verify_corrected_ast() -> None:
    tree = ast.parse(CORRECTED_ENTRYPOINT.read_text(encoding="utf-8"))
    imported = [
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    ]
    required = {
        "build_prospective_execution_lease",
        "materialize_execution_lease",
        "run_claimed_execution_wrapper",
        "verify_unconsumed_frozen_admission",
    }
    if not required <= set(imported):
        raise VerificationError("corrected entrypoint imports are incomplete")
    forbidden = {"claim_execution_lease", "execute_authorized_runtime"}
    if forbidden & set(imported):
        raise VerificationError("legacy post-claim path remains imported")
    if any(
        isinstance(node, ast.Name) and node.id in forbidden
        for node in ast.walk(tree)
    ):
        raise VerificationError("legacy post-claim symbol remains referenced")

    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    }
    function = functions.get("run_corrected_one_shot_authorized_runtime")
    if not isinstance(function, ast.FunctionDef):
        raise VerificationError("corrected one-shot function is absent")

    calls_by_name: dict[str, list[ast.Call]] = {}
    for node in ast.walk(function):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            calls_by_name.setdefault(node.func.id, []).append(node)
    ordered = [
        "verify_materialized_execution_freeze",
        "verify_unconsumed_frozen_admission",
        "QWakeLC4RuntimeBackend",
        "build_prospective_execution_lease",
        "materialize_execution_lease",
        "run_claimed_execution_wrapper",
    ]
    for name in ordered:
        if len(calls_by_name.get(name, [])) != 1:
            raise VerificationError(f"corrected call count differs: {name}")
    positions = [calls_by_name[name][0].lineno for name in ordered]
    if positions != sorted(positions) or len(set(positions)) != len(positions):
        raise VerificationError("corrected calls are not ordered")

    verify_admission = calls_by_name["verify_unconsumed_frozen_admission"][0]
    assignment = next(
        (
            node
            for node in function.body
            if isinstance(node, ast.Assign) and node.value is verify_admission
        ),
        None,
    )
    if assignment is None or len(assignment.targets) != 1:
        raise VerificationError("captured admission assignment differs")
    target = assignment.targets[0]
    if not isinstance(target, ast.Name) or target.id != "frozen_admission":
        raise VerificationError("captured admission variable differs")

    build_call = calls_by_name["build_prospective_execution_lease"][0]
    materialize_call = calls_by_name["materialize_execution_lease"][0]
    run_call = calls_by_name["run_claimed_execution_wrapper"][0]
    required_admission_arguments = (
        (build_call, 0),
        (materialize_call, 2),
        (run_call, 1),
    )
    for call, position in required_admission_arguments:
        if len(call.args) <= position:
            raise VerificationError("captured admission argument is absent")
        argument = call.args[position]
        if not isinstance(argument, ast.Name) or argument.id != "frozen_admission":
            raise VerificationError("captured admission identity is not reused")


def main() -> int:
    if not PACKAGE.is_dir() or PACKAGE.is_symlink():
        raise VerificationError("correction package is absent or symbolic")
    observed_files = {
        path.name
        for path in PACKAGE.iterdir()
        if path.is_file() and not path.is_symlink()
    }
    if observed_files != EXPECTED_FILES:
        raise VerificationError("correction package file set differs")
    if any(path.is_dir() or path.is_symlink() for path in PACKAGE.iterdir()):
        raise VerificationError("correction package contains a non-regular entry")

    package_scope = verify_registry(PACKAGE_REGISTRY, PACKAGE)
    if package_scope != EXPECTED_FILES - {"SHA256SUMS"}:
        raise VerificationError("correction package registry scope differs")
    source_scope = verify_registry(SOURCE_REGISTRY, ROOT)
    if source_scope != EXPECTED_SOURCE_PATHS:
        raise VerificationError("correction source registry scope differs")
    verify_record()

    for relative, expected_sha256 in EXPECTED_HISTORICAL_SOURCE_SHA256.items():
        if sha256_file(ROOT / relative) != expected_sha256:
            raise VerificationError(f"historical source changed: {relative}")
    if sha256_file(CORRECTED_ENTRYPOINT) != EXPECTED_CORRECTED_ENTRYPOINT_SHA256:
        raise VerificationError("corrected entrypoint identity differs")
    if sha256_file(PATCH) != EXPECTED_PATCH_SHA256:
        raise VerificationError("correction patch identity differs")

    verify_patch_reconstruction()
    verify_corrected_ast()

    print(f"CORRECTION_ID={EXPECTED_CORRECTION_ID}")
    print(f"CORRECTION_STATUS={EXPECTED_STATUS}")
    print("HISTORICAL_ENTRYPOINT_PRESERVED=true")
    print("PATCH_RECONSTRUCTS_CORRECTED_ENTRYPOINT=true")
    print("SAME_ADMISSION_IDENTITY_REUSED_AFTER_CLAIM=true")
    print("POST_CLAIM_UNCONSUMED_REVALIDATION_PRESENT=false")
    print("ATTEMPT_001_RETRY_PERMITTED=false")
    print("CORRECTED_IMAGE_BUILT=false")
    print("ATTEMPT_002_AUTHORIZED=false")
    print("RUNTIME_EXECUTION_PERFORMED=false")
    print("QW5_OPENED=false")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except VerificationError as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1) from exc
