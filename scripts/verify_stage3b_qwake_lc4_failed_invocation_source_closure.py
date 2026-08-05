#!/usr/bin/env python3
"""Verify the terminal attempt-002 source-closure correction."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Final, cast

from torch2pc_thesis.stage3b_qwake_lc4_failed_invocation_source_closure import (
    CURRENT_OPERATION_COMMIT,
    FIRST_REGISTRY_EXACT_COMMIT,
    FREEZE_MATERIALIZATION_COMMIT,
    FREEZE_MATERIALIZATION_MISMATCHES,
    IMAGE_SOURCE_ABSENT_PATHS,
    IMAGE_SOURCE_COMMIT,
    SourceClosureCorrectionError,
    canonical_json,
    classify_registry_at_commit,
    parse_registry,
    verify_failed_outcome,
    verify_semantic_digest,
)

PACKAGE_ROOT: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-attempt-002-failed-invocation-"
    "source-closure-correction-v1"
)
FAILURE_JSON: Final = PACKAGE_ROOT / "failure.json"
CORRECTION_JSON: Final = PACKAGE_ROOT / "correction.json"
PACKAGE_REGISTRY: Final = PACKAGE_ROOT / "SHA256SUMS"
SOURCE_REGISTRY: Final = PACKAGE_ROOT / "source-SHA256SUMS"
FREEZE_SOURCE_REGISTRY: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-attempt-002-execution-freeze-v1/"
    "source-SHA256SUMS"
)
OUTCOME: Final = Path(
    "results/stage-3/"
    "qwake-lc4-runtime-validation-v1-attempt-002.host-outcome.json"
)
LEASE_V1: Final = Path(
    "results/stage-3/"
    "qwake-lc4-runtime-validation-v1-attempt-002.execution-lease.json"
)
LEASE_V2: Final = Path(
    "results/stage-3/"
    "qwake-lc4-runtime-validation-v1-attempt-002.execution-lease-v2.json"
)
OUTPUT_ROOT: Final = Path(
    "results/stage-3/qwake-lc4-runtime-validation-v1-attempt-002"
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path("."))
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    """Read canonical JSON."""
    raw = path.read_bytes()
    value = cast(dict[str, Any], json.loads(raw.decode("utf-8")))
    if raw != canonical_json(value).encode("utf-8"):
        raise SourceClosureCorrectionError(
            f"canonical JSON differs: {path}"
        )
    return value


def verify_registry(path: Path, base: Path) -> None:
    """Verify a registry relative to one base directory."""
    resolved_base = base.resolve()
    for entry in parse_registry(path):
        candidate = (base / entry.relative).resolve()
        try:
            candidate.relative_to(resolved_base)
        except ValueError as exc:
            raise SourceClosureCorrectionError(
                "registry path escapes base"
            ) from exc
        if not candidate.is_file() or candidate.is_symlink():
            raise SourceClosureCorrectionError(
                f"registry file is absent: {candidate}"
            )
        observed = hashlib.sha256(candidate.read_bytes()).hexdigest()
        if observed != entry.sha256:
            raise SourceClosureCorrectionError(
                f"registry identity differs: {entry.relative}"
            )


def verify(root: Path) -> None:
    """Verify the complete non-executing correction."""
    root = root.expanduser().resolve(strict=True)
    package = root / PACKAGE_ROOT
    if not package.is_dir() or package.is_symlink():
        raise SourceClosureCorrectionError(
            "correction package directory differs"
        )

    expected = {
        "SHA256SUMS",
        "correction.json",
        "failure.json",
        "source-SHA256SUMS",
    }
    package_entries = list(package.iterdir())
    observed = {
        entry.name
        for entry in package_entries
        if entry.is_file() and not entry.is_symlink()
    }
    if observed != expected or len(package_entries) != len(expected):
        raise SourceClosureCorrectionError(
            "correction package file set differs"
        )
    if any(entry.is_symlink() for entry in package_entries):
        raise SourceClosureCorrectionError(
            "correction package contains a symlink"
        )

    verify_registry(root / PACKAGE_REGISTRY, package)
    verify_registry(root / SOURCE_REGISTRY, root)

    outcome = read_json(root / OUTCOME)
    verify_failed_outcome(outcome)

    failure = read_json(root / FAILURE_JSON)
    verify_semantic_digest(failure, "failure_sha256")
    outcome_sha = (
        "sha256:"
        + hashlib.sha256((root / OUTCOME).read_bytes()).hexdigest()
    )
    if failure["durable_outcome_sha256"] != outcome_sha:
        raise SourceClosureCorrectionError(
            "durable outcome digest differs"
        )

    correction = read_json(root / CORRECTION_JSON)
    verify_semantic_digest(correction, "correction_sha256")
    if (
        correction["failed_invocation_sha256"]
        != failure["failure_sha256"]
    ):
        raise SourceClosureCorrectionError(
            "failure/correction linkage differs"
        )

    exact = {
        "attempt_002_terminal": True,
        "attempt_002_retry_permitted": False,
        "attempt_002_authorization_reuse_permitted": False,
        "image_source_commit": IMAGE_SOURCE_COMMIT,
        "freeze_materialization_commit": (
            FREEZE_MATERIALIZATION_COMMIT
        ),
        "first_registry_exact_commit": FIRST_REGISTRY_EXACT_COMMIT,
        "current_operation_commit": CURRENT_OPERATION_COMMIT,
        "next_attempt_id": (
            "stage3b-qwake-lc4-runtime-validation-v1-attempt-003"
        ),
        "next_attempt_effect_paths_must_be_disjoint": True,
        "new_image_required": True,
        "new_execution_freeze_required": True,
        "new_host_invocation_chain_required": True,
        "new_authorization_required": True,
        (
            "runtime_registry_and_host_source_registry_"
            "must_be_separate"
        ): True,
        "prebuild_git_blob_closure_verification_required": True,
        "build_time_runtime_registry_verification_required": True,
        "postbuild_image_closure_verification_required": True,
        "runtime_invocation_performed_by_correction": False,
        "docker_build_performed_by_correction": False,
        "docker_run_performed_by_correction": False,
        "attempt_003_created": False,
        "attempt_003_authorization_issued": False,
        "pr_merge_permitted": False,
        "qw5_opening_permitted": False,
    }
    for key, value in exact.items():
        if correction.get(key) != value:
            raise SourceClosureCorrectionError(
                f"correction field differs: {key}"
            )

    if (root / LEASE_V1).exists() or (root / LEASE_V2).exists():
        raise SourceClosureCorrectionError(
            "attempt-002 lease unexpectedly exists"
        )
    if (root / OUTPUT_ROOT).exists():
        raise SourceClosureCorrectionError(
            "attempt-002 output unexpectedly exists"
        )

    freeze_entries = parse_registry(root / FREEZE_SOURCE_REGISTRY)

    image = classify_registry_at_commit(
        root,
        IMAGE_SOURCE_COMMIT,
        freeze_entries,
    )
    if len(image.exact) != 10:
        raise SourceClosureCorrectionError(
            "image-source exact count differs"
        )
    if image.absent != IMAGE_SOURCE_ABSENT_PATHS:
        raise SourceClosureCorrectionError(
            "image-source absent path set differs"
        )
    if image.mismatches:
        raise SourceClosureCorrectionError(
            "image-source mismatch set differs"
        )

    materialized = classify_registry_at_commit(
        root,
        FREEZE_MATERIALIZATION_COMMIT,
        freeze_entries,
    )
    if len(materialized.exact) != 10 or materialized.absent:
        raise SourceClosureCorrectionError(
            "freeze-materialization classification differs"
        )
    observed_mismatches = {
        relative: (expected, observed)
        for relative, expected, observed in materialized.mismatches
    }
    if observed_mismatches != FREEZE_MATERIALIZATION_MISMATCHES:
        raise SourceClosureCorrectionError(
            "freeze-materialization mismatch set differs"
        )

    first_exact = classify_registry_at_commit(
        root,
        FIRST_REGISTRY_EXACT_COMMIT,
        freeze_entries,
    )
    if len(first_exact.exact) != 12 or not first_exact.is_exact:
        raise SourceClosureCorrectionError(
            "first registry-exact commit differs"
        )

    current = classify_registry_at_commit(
        root,
        CURRENT_OPERATION_COMMIT,
        freeze_entries,
    )
    if len(current.exact) != 12 or not current.is_exact:
        raise SourceClosureCorrectionError(
            "current operation commit registry closure differs"
        )

    print("FAILED_ATTEMPT_002_TERMINAL=true")
    print("DURABLE_FAILED_OUTCOME_VERIFIED=true")
    print("ATTEMPT_002_LEASES_AND_OUTPUT_ABSENT=true")
    print("ATTEMPT_002_RETRY_PERMITTED=false")
    print("ATTEMPT_002_AUTHORIZATION_REUSE_PERMITTED=false")
    print("IMAGE_SOURCE_CLASSIFICATION=10_exact_2_absent_0_mismatch")
    print(
        "FREEZE_MATERIALIZATION_CLASSIFICATION="
        "10_exact_0_absent_2_mismatch"
    )
    print(
        "FIRST_REGISTRY_EXACT_COMMIT="
        f"{FIRST_REGISTRY_EXACT_COMMIT}"
    )
    print("CURRENT_OPERATION_COMMIT_REGISTRY_EXACT=true")
    print("RUNTIME_HOST_REGISTRY_SPLIT_REQUIRED=true")
    print("BUILD_TIME_RUNTIME_CLOSURE_GATE_REQUIRED=true")
    print(
        "NEXT_ATTEMPT_ID="
        "stage3b-qwake-lc4-runtime-validation-v1-attempt-003"
    )
    print("RUNTIME_INVOCATION_PERFORMED=false")


def main() -> int:
    """Run the verifier."""
    args = parse_args()
    verify(args.project_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
