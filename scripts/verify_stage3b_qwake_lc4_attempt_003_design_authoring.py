#!/usr/bin/env python3
"""Verify bounded attempt-003 design authoring without runtime effects."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any, Final

PACKAGE_ROOT: Final = Path('experiments/frozen/stage3b-qwake-lc4-e-attempt-003-runtime-source-closure-design-authoring-v1')
AUTHORING_PATH: Final = PACKAGE_ROOT / "authoring.json"
CONTRACT_PATH: Final = PACKAGE_ROOT / "contract.json"
SOURCE_REGISTRY_PATH: Final = PACKAGE_ROOT / "source-SHA256SUMS"
PACKAGE_REGISTRY_PATH: Final = PACKAGE_ROOT / "SHA256SUMS"

ADR_RU: Final = Path('docs/decisions/ADR-119-stage3b-qwake-lc4-e-attempt-003-runtime-source-closure-design.md')
ADR_EN: Final = Path('docs/decisions/ADR-119-stage3b-qwake-lc4-e-attempt-003-runtime-source-closure-design_EN.md')
LANGUAGE_MAP: Final = Path("docs/language-map.csv")

EXPECTED_ATTEMPT_ID: Final = 'stage3b-qwake-lc4-runtime-validation-v1-attempt-003'
EXPECTED_PARENT: Final = '9ed7763df195f23583aa8f78182398e42e2e666b'
EXPECTED_TORCH2PC: Final = 'b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4'
EXPECTED_OUTPUT_ROOT: Final = 'results/stage-3/qwake-lc4-runtime-validation-v1-attempt-003'
EXPECTED_DESIGN_ID: Final = 'stage3b-qwake-lc4-e-attempt-003-runtime-source-closure-design-authoring-v1'

EXPECTED_PACKAGE_FILES: Final = (
    "SHA256SUMS",
    "authoring.json",
    "contract.json",
    "source-SHA256SUMS",
)
EXPECTED_PACKAGE_REGISTRY_PATHS: Final = (
    "authoring.json",
    "contract.json",
    "source-SHA256SUMS",
)
EXPECTED_SOURCE_PATHS: Final = (
    'docs/decisions/ADR-119-stage3b-qwake-lc4-e-attempt-003-runtime-source-closure-design_EN.md',
    'docs/decisions/ADR-119-stage3b-qwake-lc4-e-attempt-003-runtime-source-closure-design.md',
    "docs/language-map.csv",
    'experiments/frozen/stage3b-qwake-lc4-e-attempt-003-runtime-source-closure-design-authoring-v1/contract.json',
    'scripts/verify_stage3b_qwake_lc4_attempt_003_design_authoring.py',
    'tests/unit/test_stage3b_qwake_lc4_attempt_003_design_authoring.py',
)
EXPECTED_FUTURE_RUNTIME_PATHS: Final = ('.dockerignore', 'Dockerfile.rocm', 'pyproject.toml', 'requirements/rocm.txt', 'scripts/container_entrypoint.sh', 'scripts/run_stage3b_qwake_lc4_attempt_003_authorized_runtime.py', 'scripts/verify_stage3b_qwake_lc4_attempt_003_container_runtime.py', 'scripts/verify_stage3b_qwake_lc4_attempt_003_execution_freeze.py', 'src/torch2pc_thesis/stage3b_qwake_lc4_attempt_003_contract.py', 'src/torch2pc_thesis/stage3b_qwake_lc4_attempt_003_execution_wrapper.py', 'src/torch2pc_thesis/stage3b_qwake_lc4_attempt_003_runtime_backend.py', 'tests/unit/test_stage3b_qwake_lc4_attempt_003_container_runtime.py', 'tests/unit/test_stage3b_qwake_lc4_attempt_003_execution_freeze.py')

ATTEMPT_003_EFFECT_PATHS: Final = (
    Path('results/stage-3/qwake-lc4-runtime-validation-v1-attempt-003'),
    Path('results/stage-3/qwake-lc4-runtime-validation-v1-attempt-003.execution-lease.json'),
    Path('results/stage-3/qwake-lc4-runtime-validation-v1-attempt-003.execution-lease-v2.json'),
    Path('results/stage-3/qwake-lc4-runtime-validation-v1-attempt-003.host-outcome.json'),
    Path(
        "experiments/frozen/"
        "stage3b-qwake-lc4-e-attempt-003-execution-freeze-v1"
    ),
    Path(
        "experiments/frozen/"
        "stage3b-qwake-lc4-e-attempt-003-host-invocation-chain-v1"
    ),
    Path(
        "experiments/frozen/"
        "stage3b-qwake-lc4-e-attempt-003-authorization-v1"
    ),
    Path(
        "experiments/frozen/"
        "stage3b-qwake-lc4-e-attempt-003-"
        "authorization-consumption-operation-v1"
    ),
)


class Attempt003DesignVerificationError(RuntimeError):
    """Raised when bounded design authoring fails closed."""


def canonical_json_bytes(value: Any) -> bytes:
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


def semantic_hash(value: dict[str, Any], field: str) -> str:
    payload = dict(value)
    payload.pop(field, None)
    return "sha256:" + hashlib.sha256(
        canonical_json_bytes(payload)
    ).hexdigest()


def _load_canonical_json(path: Path, hash_field: str) -> dict[str, Any]:
    raw = path.read_bytes()
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, dict):
        raise Attempt003DesignVerificationError(
            f"JSON object required: {path}"
        )
    if raw != canonical_json_bytes(value):
        raise Attempt003DesignVerificationError(
            f"noncanonical JSON: {path}"
        )
    observed = value.get(hash_field)
    expected = semantic_hash(value, hash_field)
    if observed != expected:
        raise Attempt003DesignVerificationError(
            f"semantic hash mismatch: {path}"
        )
    return value


def _read_registry(path: Path) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        digest, separator, relative = line.partition("  ")
        if (
            separator != "  "
            or len(digest) != 64
            or any(char not in "0123456789abcdef" for char in digest)
            or not relative
        ):
            raise Attempt003DesignVerificationError(
                f"invalid registry line: {path}: {line!r}"
            )
        rows.append((digest, relative))
    return rows


def _verify_registry(
    path: Path,
    base: Path,
    expected_paths: tuple[str, ...],
) -> None:
    rows = _read_registry(path)
    observed_paths = tuple(relative for _, relative in rows)
    if observed_paths != expected_paths:
        raise Attempt003DesignVerificationError(
            f"registry paths differ: {path}"
        )
    for digest, relative in rows:
        target = base / relative
        if not target.is_file() or target.is_symlink():
            raise Attempt003DesignVerificationError(
                f"regular source file required: {target}"
            )
        observed = hashlib.sha256(target.read_bytes()).hexdigest()
        if observed != digest:
            raise Attempt003DesignVerificationError(
                f"registry digest mismatch: {target}"
            )


def _verify_language_map(root: Path) -> None:
    text = (root / LANGUAGE_MAP).read_text(encoding="utf-8")
    rows = list(csv.DictReader(io.StringIO(text)))
    matches = [
        row
        for row in rows
        if row.get("russian_primary") == ADR_RU.as_posix()
        and row.get("english_version") == ADR_EN.as_posix()
    ]
    if len(matches) != 1:
        raise Attempt003DesignVerificationError(
            "ADR-119 language-map pair must occur exactly once"
        )


def _verify_adrs(root: Path) -> None:
    ru = (root / ADR_RU).read_text(encoding="utf-8")
    en = (root / ADR_EN).read_text(encoding="utf-8")
    required_ru = (
        "[попытка](../glossary.md#term-attempt)",
        "[выполнения](../glossary.md#term-execution)",
        "[запуск](../glossary.md#term-run)",
        "[набору данных](../glossary.md#term-dataset)",
    )
    required_en = (
        "[attempt](../glossary_EN.md#term-attempt)",
        "[execution](../glossary_EN.md#term-execution)",
        "[runtime](../glossary_EN.md#term-runtime)",
        "[run](../glossary_EN.md#term-run)",
        "[dataset](../glossary_EN.md#term-dataset)",
    )
    for link in required_ru:
        if ru.count(link) != 1:
            raise Attempt003DesignVerificationError(
                f"Russian ADR link differs: {link}"
            )
    for link in required_en:
        if en.count(link) != 1:
            raise Attempt003DesignVerificationError(
                f"English ADR link differs: {link}"
            )


def _verify_contract(contract: dict[str, Any]) -> None:
    if contract.get("attempt_id") != EXPECTED_ATTEMPT_ID:
        raise Attempt003DesignVerificationError("attempt id differs")
    if contract.get("attempt_kind") != "new_attempt_not_retry":
        raise Attempt003DesignVerificationError("attempt kind differs")
    if contract.get("authorized_parent_head") != EXPECTED_PARENT:
        raise Attempt003DesignVerificationError("parent head differs")
    if contract.get("torch2pc_commit") != EXPECTED_TORCH2PC:
        raise Attempt003DesignVerificationError("Torch2PC differs")
    if contract.get("output_root") != EXPECTED_OUTPUT_ROOT:
        raise Attempt003DesignVerificationError("output root differs")
    if tuple(
        contract.get("runtime_source_registry_required_paths", ())
    ) != EXPECTED_FUTURE_RUNTIME_PATHS:
        raise Attempt003DesignVerificationError(
            "future runtime source path set differs"
        )
    current = contract.get("current_slice")
    if not isinstance(current, dict):
        raise Attempt003DesignVerificationError(
            "current_slice object required"
        )
    required_false = (
        "runtime_implementation_authored",
        "runtime_source_registry_materialized",
        "image_build_permitted",
        "image_built",
        "execution_freeze_materialized",
        "host_invocation_chain_authored",
        "authorization_issued",
        "authorization_consumed",
        "lease_materialization_permitted",
        "outcome_materialization_permitted",
        "runtime_invocation_permitted",
        "model_code_invocation_permitted",
        "dataset_access_permitted",
        "pr_merge_permitted",
        "remote_main_modification_permitted",
        "qw5_opening_permitted",
    )
    if current.get("design_authoring_only") is not True:
        raise Attempt003DesignVerificationError(
            "design-only boundary differs"
        )
    for key in required_false:
        if current.get(key) is not False:
            raise Attempt003DesignVerificationError(
                f"forbidden permission differs: {key}"
            )


def verify(project_root: Path) -> None:
    root = project_root.expanduser().resolve()
    package = root / PACKAGE_ROOT
    if tuple(sorted(path.name for path in package.iterdir())) != (
        EXPECTED_PACKAGE_FILES
    ):
        raise Attempt003DesignVerificationError(
            "package file set differs"
        )

    authoring = _load_canonical_json(
        root / AUTHORING_PATH,
        "authoring_sha256",
    )
    contract = _load_canonical_json(
        root / CONTRACT_PATH,
        "contract_sha256",
    )

    if authoring.get("authoring_id") != EXPECTED_DESIGN_ID:
        raise Attempt003DesignVerificationError(
            "authoring id differs"
        )
    if authoring.get("attempt_id") != EXPECTED_ATTEMPT_ID:
        raise Attempt003DesignVerificationError(
            "authoring attempt id differs"
        )
    if authoring.get("contract_sha256") != contract.get(
        "contract_sha256"
    ):
        raise Attempt003DesignVerificationError(
            "authoring/contract identity differs"
        )
    if authoring.get("bounded_design_authoring_authorized") is not True:
        raise Attempt003DesignVerificationError(
            "bounded authoring authorization is absent"
        )
    for key in (
        "runtime_implementation_authored",
        "runtime_source_registry_materialized",
        "docker_build_invoked",
        "docker_run_invoked",
        "runtime_invoked",
        "model_code_invoked",
        "dataset_accessed",
        "lease_v1_present",
        "lease_v2_present",
        "durable_outcome_present",
        "execution_freeze_materialized",
        "host_invocation_chain_authored",
        "authorization_issued",
        "authorization_consumed",
        "attempt_002_modified",
        "attempt_003_effects_created",
        "pr_179_merge_permitted",
        "remote_main_modification_permitted",
        "qw5_opening_permitted",
    ):
        if authoring.get(key) is not False:
            raise Attempt003DesignVerificationError(
                f"authoring boundary differs: {key}"
            )

    _verify_contract(contract)
    _verify_registry(
        root / PACKAGE_REGISTRY_PATH,
        package,
        EXPECTED_PACKAGE_REGISTRY_PATHS,
    )
    _verify_registry(
        root / SOURCE_REGISTRY_PATH,
        root,
        EXPECTED_SOURCE_PATHS,
    )
    _verify_language_map(root)
    _verify_adrs(root)

    for relative in ATTEMPT_003_EFFECT_PATHS:
        if (root / relative).exists() or (root / relative).is_symlink():
            raise Attempt003DesignVerificationError(
                f"attempt-003 effect path must be absent: {relative}"
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path("."),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    verify(args.project_root)
    print("ATTEMPT_003_BOUNDED_DESIGN_AUTHORING_VERIFIED=true")
    print("RUNTIME_IMPLEMENTATION_AUTHORED=false")
    print("RUNTIME_SOURCE_REGISTRY_MATERIALIZED=false")
    print("DOCKER_BUILD_INVOKED=false")
    print("DOCKER_RUN_INVOKED=false")
    print("RUNTIME_INVOKED=false")
    print("LEASE_OR_OUTCOME_CREATED=false")
    print("AUTHORIZATION_ISSUED_OR_USED=false")
    print("ATTEMPT_003_EFFECT_PATHS_ABSENT=true")


if __name__ == "__main__":
    main()
