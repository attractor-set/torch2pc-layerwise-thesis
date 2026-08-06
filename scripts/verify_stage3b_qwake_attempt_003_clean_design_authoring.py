"""Verify clean attempt-003 source-closure design authoring."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Final

DESIGN_ROOT: Final = Path('experiments/frozen/stage3b-qwake-attempt-003-clean-source-closure-design-authoring-v1')
LINEAGE_JSON: Final = Path('experiments/frozen/stage3b-qwake-attempt-003-clean-lineage-v1/lineage.json')
ADR_RU: Final = Path('docs/decisions/ADR-112-stage3b-qwake-attempt-003-clean-source-closure-design.md')
ADR_EN: Final = Path('docs/decisions/ADR-112-stage3b-qwake-attempt-003-clean-source-closure-design_EN.md')
LANGUAGE_MAP: Final = Path("docs/language-map.csv")

EXPECTED_PACKAGE_FILES: Final = (
    "SHA256SUMS",
    "authoring.json",
    "contract.json",
    "source-SHA256SUMS",
)

EXPECTED_SOURCE_PATHS: Final = (
    'docs/decisions/ADR-112-stage3b-qwake-attempt-003-clean-source-closure-design_EN.md',
    'docs/decisions/ADR-112-stage3b-qwake-attempt-003-clean-source-closure-design.md',
    'experiments/frozen/stage3b-qwake-attempt-003-clean-lineage-v1/lineage.json',
    'experiments/frozen/stage3b-qwake-attempt-003-clean-source-closure-design-authoring-v1/authoring.json',
    'experiments/frozen/stage3b-qwake-attempt-003-clean-source-closure-design-authoring-v1/contract.json',
    'scripts/verify_stage3b_qwake_attempt_003_clean_design_authoring.py',
    'tests/unit/test_stage3b_qwake_attempt_003_clean_design_authoring.py',
)


class CleanDesignVerificationError(RuntimeError):
    """Raised when clean design authoring fails closed."""


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
        raise CleanDesignVerificationError(
            f"noncanonical record: {path}"
        )
    observed = value[field]
    payload = dict(value)
    payload.pop(field)
    calculated = (
        "sha256:" + hashlib.sha256(canonical(payload)).hexdigest()
    )
    if observed != calculated:
        raise CleanDesignVerificationError(
            f"semantic hash differs: {path}"
        )
    return value


def read_registry(path: Path) -> tuple[tuple[str, str], ...]:
    rows: list[tuple[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        digest, separator, relative = line.partition("  ")
        if separator != "  " or len(digest) != 64:
            raise CleanDesignVerificationError(
                f"registry line differs: {path}"
            )
        rows.append((digest, relative))
    return tuple(rows)


def verify_registry(
    path: Path,
    base: Path,
    expected: tuple[str, ...],
) -> None:
    rows = read_registry(path)
    observed = tuple(relative for _, relative in rows)
    if observed != expected:
        raise CleanDesignVerificationError(
            f"registry paths differ: {path}"
        )
    for digest, relative in rows:
        target = base / relative
        if not target.is_file() or target.is_symlink():
            raise CleanDesignVerificationError(
                f"regular file required: {target}"
            )
        calculated = hashlib.sha256(target.read_bytes()).hexdigest()
        if calculated != digest:
            raise CleanDesignVerificationError(
                f"registry digest differs: {target}"
            )


def verify_language_map(root: Path) -> None:
    path = root / LANGUAGE_MAP
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    matches = [
        row
        for row in rows
        if row.get("russian_primary") == ADR_RU.as_posix()
        and row.get("english_version") == ADR_EN.as_posix()
    ]
    if len(matches) != 1:
        raise CleanDesignVerificationError(
            "exactly one semantic language-map row required"
        )


def verify(project_root: Path) -> None:
    root = project_root.expanduser().resolve()
    package = root / DESIGN_ROOT

    package_files = tuple(
        sorted(path.name for path in package.iterdir())
    )
    if package_files != EXPECTED_PACKAGE_FILES:
        raise CleanDesignVerificationError(
            "design package file set differs"
        )

    authoring = load_record(
        package / "authoring.json",
        "authoring_sha256",
    )
    contract = load_record(
        package / "contract.json",
        "contract_sha256",
    )
    lineage = load_record(
        root / LINEAGE_JSON,
        "lineage_sha256",
    )

    if authoring["lineage_commit"] != 'ef5a62a0db54e76be0e2ee0b7cc8c830b7012dcd':
        raise CleanDesignVerificationError(
            "lineage commit differs"
        )
    if contract["lineage_commit"] != 'ef5a62a0db54e76be0e2ee0b7cc8c830b7012dcd':
        raise CleanDesignVerificationError(
            "contract lineage commit differs"
        )
    if lineage["cut_point"] != '5e26c840b520c9b73fea316e25512788372d6975':
        raise CleanDesignVerificationError(
            "lineage cut point differs"
        )

    if contract["language_map_in_immutable_registry"] is not False:
        raise CleanDesignVerificationError(
            "language map must not be byte-bound"
        )

    verify_registry(
        package / "source-SHA256SUMS",
        root,
        EXPECTED_SOURCE_PATHS,
    )
    verify_registry(
        package / "SHA256SUMS",
        package,
        (
            "authoring.json",
            "contract.json",
            "source-SHA256SUMS",
        ),
    )
    verify_language_map(root)

    for record in (authoring, contract):
        for key in (
            "historical_attempt_002_transplanted",
            "implementation_authored",
            "runtime_source_registry_materialized",
            "docker_build_invoked",
            "docker_run_invoked",
            "image_created",
            "image_used",
            "runtime_invoked",
            "model_code_invoked",
            "dataset_accessed",
            "authorization_issued",
            "authorization_used",
            "lease_or_outcome_created",
            "execution_freeze_materialized",
            "host_invocation_chain_authored",
            "pr_created",
            "pr_merged",
            "remote_main_modified",
            "qw5_opened",
        ):
            if record[key] is not False:
                raise CleanDesignVerificationError(
                    f"forbidden boundary differs: {key}"
                )


def main() -> None:
    verify(Path("."))
    print("CLEAN_ATTEMPT_003_DESIGN_AUTHORING_VERIFIED=true")
    print("LANGUAGE_MAP_SEMANTIC_ONLY=true")
    print("HISTORICAL_ATTEMPT_002_TRANSPLANTED=false")
    print("IMPLEMENTATION_AUTHORED=false")
    print("DOCKER_BUILD_INVOKED=false")
    print("RUNTIME_INVOKED=false")
    print("AUTHORIZATION_ISSUED=false")


if __name__ == "__main__":
    main()
