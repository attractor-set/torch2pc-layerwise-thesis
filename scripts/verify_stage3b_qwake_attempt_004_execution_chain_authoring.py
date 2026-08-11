#!/usr/bin/env python3
"""Verify the non-executing Attempt-004 consolidated execution-chain authoring."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Final

BASE_COMMIT: Final = "60a215c53fb734bcd9cb002817cf072da75c26c8"
BASE_TREE: Final = "9d8e652ad73c85a16eac428a3cdb784e7dba93ee"
AUTHORING_COMMIT: Final = "c9d889da10274878fb2b8ea5f68c06a50c170c53"
GENERIC_BACKEND_SHA256: Final = (
    "d9ad10efe959e19d7f1b6d61d8eddd1228cb9753fa9191823d5d1ded68e9fd72"
)
PACKAGE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-attempt-004-execution-chain-authoring-v1"
)
CONTRACT: Final = PACKAGE / "contract.json"
SOURCE_SUMS: Final = PACKAGE / "source-SHA256SUMS"
PACKAGE_SUMS: Final = PACKAGE / "SHA256SUMS"
GENERIC_BACKEND: Final = Path(
    "src/torch2pc_thesis/stage3b_qwake_lc4_runtime_backend.py"
)
PROFILE: Final = Path(
    "src/torch2pc_thesis/stage3b_qwake_attempt_004_cpu_measurement_stabilization.py"
)
ATTEMPT004_CONTRACT: Final = Path(
    "src/torch2pc_thesis/stage3b_qwake_attempt_004_contract.py"
)
WRAPPER: Final = Path(
    "src/torch2pc_thesis/stage3b_qwake_attempt_004_execution_wrapper.py"
)
BACKEND: Final = Path(
    "src/torch2pc_thesis/stage3b_qwake_attempt_004_runtime_backend.py"
)
ENTRYPOINT: Final = Path(
    "scripts/run_stage3b_qwake_attempt_004_authorized_runtime.py"
)
HOST: Final = Path(
    "scripts/run_stage3b_qwake_attempt_004_host_one_shot.py"
)
TEST: Final = Path(
    "tests/unit/test_stage3b_qwake_attempt_004_execution_chain.py"
)
ADR_RU: Final = Path(
    "docs/decisions/"
    "ADR-120-stage3b-qwake-attempt-004-consolidated-execution-chain.md"
)
ADR_EN: Final = Path(
    "docs/decisions/"
    "ADR-120-stage3b-qwake-attempt-004-consolidated-execution-chain_EN.md"
)

FORBIDDEN_EFFECTS: Final = (
    Path("experiments/frozen/stage3b-qwake-attempt-004-execution-freeze-v1"),
    Path("experiments/frozen/stage3b-qwake-attempt-004-authorization-v1"),
    Path("results/stage-3/qwake-lc4-runtime-validation-v1-attempt-004"),
    Path(
        "results/stage-3/"
        "qwake-lc4-runtime-validation-v1-attempt-004.execution-lease.json"
    ),
    Path(
        "results/stage-3/"
        "qwake-lc4-runtime-validation-v1-attempt-004.host-command.json"
    ),
    Path(
        "results/stage-3/"
        "qwake-lc4-runtime-validation-v1-attempt-004.host-outcome.json"
    ),
)


class VerificationError(RuntimeError):
    pass


def canonical_json(value: object) -> bytes:
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


def sha(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise VerificationError(f"regular file absent: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_registry(path: Path) -> dict[str, str]:
    if not path.is_file() or path.is_symlink():
        raise VerificationError(f"registry absent: {path}")
    entries: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        digest, sep, relative = line.partition("  ")
        if sep != "  " or not relative:
            raise VerificationError(f"malformed registry: {path}")
        if relative in entries:
            raise VerificationError(f"duplicate registry path: {relative}")
        entries[relative] = digest
    if not entries:
        raise VerificationError(f"empty registry: {path}")
    return entries


def verify_registry(path: Path, base: Path) -> dict[str, str]:
    entries = parse_registry(path)
    for relative, digest in entries.items():
        if sha(base / relative) != digest:
            raise VerificationError(f"registry digest differs: {relative}")
    return entries


def git_blob(root: Path, commit: str, relative: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{commit}:{relative}"],
        cwd=root,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise VerificationError(
            f"historical source is absent: {commit}:{relative}"
        )
    return result.stdout


def verify_registry_at_commit(
    path: Path,
    root: Path,
    commit: str,
) -> dict[str, str]:
    entries = parse_registry(path)
    for relative, digest in entries.items():
        observed = hashlib.sha256(git_blob(root, commit, relative)).hexdigest()
        if observed != digest:
            raise VerificationError(
                f"historical registry digest differs: {relative}"
            )
    return entries


def verify(project_root: Path) -> None:
    root = project_root.expanduser().resolve()

    contract_raw = json.loads((root / CONTRACT).read_text(encoding="utf-8"))
    if not isinstance(contract_raw, dict):
        raise VerificationError("authoring contract must be an object")
    digest = contract_raw.get("contract_sha256")
    unsigned = dict(contract_raw)
    unsigned.pop("contract_sha256", None)
    expected = "sha256:" + hashlib.sha256(canonical_json(unsigned)).hexdigest()
    if digest != expected:
        raise VerificationError("authoring contract digest differs")

    expected_contract = {
        "schema_version": 1,
        "contract_id": (
            "stage3b-qwake-attempt-004-execution-chain-authoring-v1"
        ),
        "status": "execution_chain_authored_runtime_not_permitted",
        "base_commit": BASE_COMMIT,
        "base_tree": BASE_TREE,
        "attempt_id": "stage3b-qwake-lc4-runtime-validation-v1-attempt-004",
        "integration_mode": "distinct_attempt004_effect_namespace",
        "runtime_executor": "Attempt004CPUStabilizedMatrixExecutor",
        "cpu_affinity": [0],
        "torch_num_threads": 1,
        "torch_num_interop_threads": 1,
        "warmup_cell_count": 14,
        "measured_pair_count_per_candidate": 12,
        "cpu_primary_clock": "time_process_time_ns",
        "order_effect_tolerance_unchanged": True,
        "generic_runtime_backend_modified": False,
        "attempt003_identities_reused": False,
        "one_shot_spawn_count": 1,
        "automatic_retry_permitted": False,
        "authorization_consumption_owner": (
            "container_entrypoint_atomic_execution_lease"
        ),
        "runtime_execution_permitted": False,
        "authorization_materialized": False,
        "authorization_consumed": False,
        "execution_lease_materialized": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "scientific_execution_open": False,
        "test_dataset_access": False,
        "publication_permitted": False,
    }
    for key, value in expected_contract.items():
        if contract_raw.get(key) != value:
            raise VerificationError(f"authoring contract {key} differs")

    authoring_parent = subprocess.run(
        ["git", "rev-parse", f"{AUTHORING_COMMIT}^"],
        cwd=root,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    if (
        authoring_parent.returncode != 0
        or authoring_parent.stdout.strip() != BASE_COMMIT
    ):
        raise VerificationError("authoring commit parent differs")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", AUTHORING_COMMIT, "HEAD"],
        cwd=root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if ancestor.returncode != 0:
        raise VerificationError("authoring commit is not an ancestor of HEAD")

    source_registry = verify_registry_at_commit(
        root / SOURCE_SUMS,
        root,
        AUTHORING_COMMIT,
    )
    package_registry = verify_registry(root / PACKAGE_SUMS, root / PACKAGE)
    if set(package_registry) != {"contract.json", "source-SHA256SUMS"}:
        raise VerificationError("package registry scope differs")

    required_sources = {
        ATTEMPT004_CONTRACT.as_posix(),
        WRAPPER.as_posix(),
        BACKEND.as_posix(),
        ENTRYPOINT.as_posix(),
        HOST.as_posix(),
        TEST.as_posix(),
        ADR_RU.as_posix(),
        ADR_EN.as_posix(),
        PROFILE.as_posix(),
        GENERIC_BACKEND.as_posix(),
    }
    if not required_sources.issubset(source_registry):
        missing = sorted(required_sources - set(source_registry))
        raise VerificationError(f"source registry missing paths: {missing}")

    if sha(root / GENERIC_BACKEND) != GENERIC_BACKEND_SHA256:
        raise VerificationError("historical generic runtime backend changed")

    backend_text = (root / BACKEND).read_text(encoding="utf-8")
    if "Attempt004CPUStabilizedMatrixExecutor()" not in backend_text:
        raise VerificationError("Attempt-004 executor is not default backend")
    if "BoundedTorchMatrixExecutor()" in backend_text:
        raise VerificationError(
            "Attempt-004 backend bypasses stabilized executor"
        )

    host_text = (root / HOST).read_text(encoding="utf-8")
    host_tree = ast.parse(host_text)
    popen_calls = [
        node
        for node in ast.walk(host_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "subprocess"
        and node.func.attr == "Popen"
    ]
    if len(popen_calls) != 1:
        raise VerificationError("host spawner must contain exactly one Popen")
    for token in (
        'CPUSET_CPUS: Final = "0"',
        '("QWAKE_ATTEMPT_004_CPU_STABILIZATION", "1")',
        '("OMP_NUM_THREADS", "1")',
        '("MKL_NUM_THREADS", "1")',
        '("OPENBLAS_NUM_THREADS", "1")',
        '("NUMEXPR_NUM_THREADS", "1")',
        "automatic_retry_performed",
        'image_digest = record.get("Id")',
        'repo_digest = matching[0] if matching else ""',
        "freeze.image_digest,",
    ):
        if token not in host_text:
            raise VerificationError(f"host spawner invariant absent: {token}")
    for token in (
        '["git", "reset"',
        '["git", "clean"',
        "git push --force",
    ):
        if token in host_text:
            raise VerificationError(f"forbidden host mutation token: {token}")

    lang_source = (
        "<!-- LANG-SOURCE: ../../experiments/frozen/"
        "stage3b-qwake-attempt-004-execution-chain-authoring-v1/contract.json -->"
    )
    if lang_source not in (root / ADR_RU).read_text(encoding="utf-8"):
        raise VerificationError("RU LANG-SOURCE binding absent")
    if lang_source not in (root / ADR_EN).read_text(encoding="utf-8"):
        raise VerificationError("EN LANG-SOURCE binding absent")

    for relative in FORBIDDEN_EFFECTS:
        if os.path.lexists(root / relative):
            raise VerificationError(f"runtime effect exists during authoring: {relative}")

    print("ATTEMPT004_EXECUTION_CHAIN_AUTHORING_VERIFIER=PASS")
    print(f"BASE_COMMIT={BASE_COMMIT}")
    print(f"BASE_TREE={BASE_TREE}")
    print(f"AUTHORING_COMMIT={AUTHORING_COMMIT}")
    print("SOURCE_REGISTRY_VERIFICATION=authoring_commit_relative")
    print("LOCAL_IMAGE_ID_AUTHORITATIVE=true")
    print("REPO_DIGEST_OPTIONAL_OBSERVATION=true")
    print(f"GENERIC_RUNTIME_BACKEND_SHA256={GENERIC_BACKEND_SHA256}")
    print("GENERIC_RUNTIME_BACKEND_MODIFIED=false")
    print("ATTEMPT003_IDENTITIES_REUSED=false")
    print("RUNTIME_EXECUTOR=Attempt004CPUStabilizedMatrixExecutor")
    print("CPU_AFFINITY=0")
    print("TORCH_NUM_THREADS=1")
    print("TORCH_NUM_INTEROP_THREADS=1")
    print("CPU_WARMUP_CELL_COUNT=14")
    print("MEASURED_PAIR_COUNT_PER_CANDIDATE=12")
    print("CPU_PRIMARY_CLOCK=time_process_time_ns")
    print("ORDER_EFFECT_TOLERANCE_UNCHANGED=true")
    print("ONE_SHOT_SPAWN_COUNT=1")
    print("AUTOMATIC_RETRY_PERMITTED=false")
    print("RUNTIME_EXECUTION_PERMITTED=false")
    print("AUTHORIZATION_MATERIALIZED=false")
    print("AUTHORIZATION_CONSUMED=false")
    print("EXECUTION_LEASE_MATERIALIZED=false")
    print("RUNTIME_EXECUTION_STARTED=false")
    print("RUNTIME_EXECUTION_PERFORMED=false")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path("."))
    args = parser.parse_args()
    verify(args.project_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
