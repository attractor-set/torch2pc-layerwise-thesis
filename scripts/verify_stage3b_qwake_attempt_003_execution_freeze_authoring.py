"""Verify attempt-003 merged-source binding / freeze authoring."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any, Final

PACKAGE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-attempt-003-source-binding-"
    "execution-freeze-authoring-v1"
)
ADR_RU: Final = Path(
    "docs/decisions/ADR-113-stage3b-qwake-attempt-003-"
    "source-binding-execution-freeze-authoring.md"
)
ADR_EN: Final = Path(
    "docs/decisions/ADR-113-stage3b-qwake-attempt-003-"
    "source-binding-execution-freeze-authoring_EN.md"
)
LANGUAGE_MAP: Final = Path("docs/language-map.csv")
RUNTIME_REGISTRY: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-attempt-003-clean-source-closure-"
    "implementation-authoring-v1/runtime-SHA256SUMS"
)
IMPLEMENTATION_JSON: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-attempt-003-clean-source-closure-"
    "implementation-authoring-v1/implementation.json"
)
SOURCE_COMMIT: Final = "541b34a57297d2c5a82851bd846b583d4904fba6"
PRE_MERGE_MAIN: Final = "26e0328bbec433d6f2ec1841ee76a8c2c4312ccc"
IMPLEMENTATION_COMMIT: Final = "4cf74c9632c537459b80e494e6ae88b0bc220c90"
DESIGN_COMMIT: Final = "e49cbdb2f3d87717069f8b5d10a20290c565b0be"
POST_MERGE_FREEZE_SHA256: Final = (
    "sha256:94562e74965156602df877a6b3a04b1425095c37ca8442dc121360e56dd2fe75"
)
TORCH2PC_COMMIT: Final = "b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4"
BASE_IMAGE: Final = (
    "rocm/pytorch@sha256:96a2fb24dec9896e2f8238178f0c49d0dcc4c7dcc597be09e4564316bd86d191"
)

EXPECTED_PACKAGE_FILES: Final = (
    "SHA256SUMS",
    "authoring.json",
    "contract.json",
    "source-SHA256SUMS",
)
EXPECTED_SOURCE_PATHS: Final = (
    (
        "docs/decisions/ADR-113-stage3b-qwake-attempt-003-source-binding-executio"
        "n-freeze-authoring.md"
    ),
    (
        "docs/decisions/ADR-113-stage3b-qwake-attempt-003-source-binding-executio"
        "n-freeze-authoring_EN.md"
    ),
    "experiments/frozen/stage3b-qwake-attempt-003-clean-lineage-v1/lineage.json",
    (
        "experiments/frozen/stage3b-qwake-attempt-003-clean-source-closure-design"
        "-authoring-v1/contract.json"
    ),
    (
        "experiments/frozen/stage3b-qwake-attempt-003-clean-source-closure-implem"
        "entation-authoring-v1/SHA256SUMS"
    ),
    (
        "experiments/frozen/stage3b-qwake-attempt-003-clean-source-closure-implem"
        "entation-authoring-v1/implementation.json"
    ),
    (
        "experiments/frozen/stage3b-qwake-attempt-003-clean-source-closure-implem"
        "entation-authoring-v1/runtime-SHA256SUMS"
    ),
    (
        "experiments/frozen/stage3b-qwake-attempt-003-clean-source-closure-implem"
        "entation-authoring-v1/source-SHA256SUMS"
    ),
    (
        "experiments/frozen/stage3b-qwake-attempt-003-source-binding-execution-fr"
        "eeze-authoring-v1/authoring.json"
    ),
    (
        "experiments/frozen/stage3b-qwake-attempt-003-source-binding-execution-fr"
        "eeze-authoring-v1/contract.json"
    ),
    "experiments/frozen/stage3b-qwake-lc4-f-runtime-freeze-v1/authorization.json",
    "scripts/verify_stage3b_qwake_attempt_003_execution_freeze_authoring.py",
    "tests/unit/test_stage3b_qwake_attempt_003_execution_freeze_authoring.py",
)
EXPECTED_RUNTIME_PATHS: Final = (
    ".dockerignore",
    "Dockerfile.rocm",
    "pyproject.toml",
    "requirements/rocm.txt",
    "scripts/container_entrypoint.sh",
    "scripts/run_stage3b_qwake_attempt_003_authorized_runtime.py",
    "scripts/verify_stage3b_qwake_attempt_003_buildtime_closure.py",
    "scripts/verify_stage3b_qwake_attempt_003_prebuild_closure.py",
    "src/torch2pc_thesis/stage3b_qwake_attempt_003_contract.py",
    "src/torch2pc_thesis/stage3b_qwake_attempt_003_execution_wrapper.py",
    "src/torch2pc_thesis/stage3b_qwake_attempt_003_runtime_backend.py",
    "src/torch2pc_thesis/stage3b_qwake_attempt_003_source_closure.py",
    "tests/unit/test_stage3b_qwake_attempt_003_source_closure.py",
)


class VerificationError(RuntimeError):
    """Raised when the authoring contract fails closed."""


def canonical(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def load_record(path: Path, field: str) -> dict[str, Any]:
    raw = path.read_bytes()
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, dict) or raw != canonical(value):
        raise VerificationError(f"noncanonical record: {path}")
    observed = value.get(field)
    payload = dict(value)
    payload.pop(field, None)
    expected = "sha256:" + hashlib.sha256(canonical(payload)).hexdigest()
    if observed != expected:
        raise VerificationError(f"semantic hash differs: {path}")
    return value


def read_registry(path: Path) -> tuple[tuple[str, str], ...]:
    rows: list[tuple[str, str]] = []
    for number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        digest, separator, relative = line.partition("  ")
        if separator != "  " or len(digest) != 64:
            raise VerificationError(f"registry line differs: {path}:{number}")
        pure = PurePosixPath(relative)
        if not relative or pure.is_absolute() or ".." in pure.parts:
            raise VerificationError(f"unsafe registry path: {relative}")
        rows.append((digest, relative))
    paths = tuple(relative for _, relative in rows)
    if paths != tuple(sorted(paths)) or len(paths) != len(set(paths)):
        raise VerificationError(f"registry ordering differs: {path}")
    return tuple(rows)


def verify_registry(
    path: Path,
    base: Path,
    expected_paths: tuple[str, ...],
) -> None:
    rows = read_registry(path)
    observed = tuple(relative for _, relative in rows)
    if observed != expected_paths:
        raise VerificationError(f"registry paths differ: {path}")
    for digest, relative in rows:
        target = base / relative
        if not target.is_file() or target.is_symlink():
            raise VerificationError(f"regular file required: {target}")
        if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            raise VerificationError(f"registry digest differs: {target}")


def git(root: Path, *arguments: str) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(root), *arguments],
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", errors="replace").strip()
        raise VerificationError(
            f"git command failed: {arguments!r}: {stderr}"
        )
    return completed.stdout


def verify_language_map(root: Path) -> None:
    with (root / LANGUAGE_MAP).open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    matches = [
        row
        for row in rows
        if row.get("russian_primary") == ADR_RU.as_posix()
        and row.get("english_version") == ADR_EN.as_posix()
        and row.get("status") == "required"
    ]
    if len(matches) != 1:
        raise VerificationError("exactly one ADR-113 language-map row required")


def verify(project_root: Path) -> None:
    root = project_root.expanduser().resolve()
    package = root / PACKAGE
    package_files = tuple(sorted(path.name for path in package.iterdir()))
    if package_files != EXPECTED_PACKAGE_FILES:
        raise VerificationError("authoring package file set differs")

    authoring = load_record(package / "authoring.json", "authoring_sha256")
    contract = load_record(package / "contract.json", "contract_sha256")
    implementation = load_record(
        root / IMPLEMENTATION_JSON,
        "implementation_sha256",
    )

    expected_contract = {
        "source_commit": SOURCE_COMMIT,
        "wrapper_commit_required": SOURCE_COMMIT,
        "pre_merge_main": PRE_MERGE_MAIN,
        "implementation_commit": IMPLEMENTATION_COMMIT,
        "design_commit": DESIGN_COMMIT,
        "merge_parent_count": 2,
        "merge_parents": [PRE_MERGE_MAIN, IMPLEMENTATION_COMMIT],
        "post_merge_freeze_sha256": POST_MERGE_FREEZE_SHA256,
        "torch2pc_commit": TORCH2PC_COMMIT,
        "base_image": BASE_IMAGE,
        "runtime_source_path_count": 13,
        "source_commit_binding_established": True,
        "historical_implementation_record_rewritten": False,
        "historical_source_commit_binding_pending_preserved": True,
        "image_built": False,
        "image_identity_materialized": False,
        "execution_freeze_materialized": False,
        "authorization_issued": False,
        "authorization_used": False,
        "lease_or_outcome_created": False,
        "runtime_invoked": False,
        "model_code_invoked": False,
        "dataset_accessed": False,
        "host_invocation_chain_authored": False,
        "commit_created": False,
        "push_invoked": False,
        "pr_created": False,
        "pr_merged": False,
        "remote_main_modified": False,
        "qw5_opened": False,
    }
    for field, expected in expected_contract.items():
        if contract.get(field) != expected:
            raise VerificationError(f"contract field differs: {field}")

    if implementation.get("source_commit_binding_pending") is not True:
        raise VerificationError("historical pending flag differs")
    if implementation.get("pr_merged") is not False:
        raise VerificationError("historical merge flag was rewritten")

    merge_line = git(
        root,
        "rev-list",
        "--parents",
        "-n",
        "1",
        SOURCE_COMMIT,
    ).decode("utf-8").strip()
    expected_merge = f"{SOURCE_COMMIT} {PRE_MERGE_MAIN} {IMPLEMENTATION_COMMIT}"
    if merge_line != expected_merge:
        raise VerificationError("source merge topology differs")

    parent = git(root, "rev-parse", f"{IMPLEMENTATION_COMMIT}^").decode(
        "utf-8"
    ).strip()
    if parent != DESIGN_COMMIT:
        raise VerificationError("design to implementation parent differs")

    runtime_raw = git(
        root,
        "show",
        f"{SOURCE_COMMIT}:{RUNTIME_REGISTRY.as_posix()}",
    )
    if hashlib.sha256(runtime_raw).hexdigest() != (
        "15b008c563ebd73ca0ce3b288d636e87591e7f94bce10e8c89dc2e95f2475086"
    ):
        raise VerificationError("runtime registry file identity differs")
    runtime_rows = read_registry(root / RUNTIME_REGISTRY)
    runtime_paths = tuple(relative for _, relative in runtime_rows)
    if runtime_paths != EXPECTED_RUNTIME_PATHS:
        raise VerificationError("runtime registry path set differs")
    for digest, relative in runtime_rows:
        object_name = f"{SOURCE_COMMIT}:{relative}"
        present = subprocess.run(
            ["git", "-C", str(root), "cat-file", "-e", object_name],
            capture_output=True,
            check=False,
        )
        if present.returncode != 0:
            raise VerificationError(f"runtime object missing: {relative}")
        raw = git(root, "show", object_name)
        if hashlib.sha256(raw).hexdigest() != digest:
            raise VerificationError(f"runtime object digest differs: {relative}")

    verify_registry(
        package / "source-SHA256SUMS",
        root,
        EXPECTED_SOURCE_PATHS,
    )
    verify_registry(
        package / "SHA256SUMS",
        package,
        ("authoring.json", "contract.json", "source-SHA256SUMS"),
    )
    verify_language_map(root)

    for record in (authoring, contract):
        for field in (
            "docker_build_invoked",
            "docker_run_invoked",
            "image_built",
            "execution_freeze_materialized",
            "authorization_issued",
            "authorization_used",
            "lease_or_outcome_created",
            "runtime_invoked",
            "model_code_invoked",
            "dataset_accessed",
            "host_invocation_chain_authored",
            "commit_created",
            "push_invoked",
            "pr_created",
            "pr_merged",
            "remote_main_modified",
            "qw5_opened",
        ):
            if record.get(field) is not False:
                raise VerificationError(f"authoring boundary differs: {field}")


def main() -> None:
    verify(Path("."))
    print("ATTEMPT_003_SOURCE_BINDING_AUTHORING_VERIFIED=true")
    print("SOURCE_COMMIT_BINDING_ESTABLISHED=true")
    print("RUNTIME_SOURCE_PATH_COUNT=13")
    print("EXECUTION_FREEZE_MATERIALIZED=false")
    print("IMAGE_BUILT=false")
    print("AUTHORIZATION_ISSUED=false")
    print("RUNTIME_INVOKED=false")


if __name__ == "__main__":
    main()
