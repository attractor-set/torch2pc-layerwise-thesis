"""Attempt-002 terminal failure and source-closure correction primitives."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

FAILED_ATTEMPT_ID: Final = (
    "stage3b-qwake-lc4-runtime-validation-v1-attempt-002"
)
NEXT_ATTEMPT_ID: Final = (
    "stage3b-qwake-lc4-runtime-validation-v1-attempt-003"
)
IMAGE_SOURCE_COMMIT: Final = (
    "02afcc3e79b2d456cc3f1c075d4d792a0be608f7"
)
FREEZE_MATERIALIZATION_COMMIT: Final = (
    "2f346498a28377d355b88560aa099890f829af46"
)
FIRST_REGISTRY_EXACT_COMMIT: Final = (
    "b5b29be5802641287e6e29bb42240ad9e41744b4"
)
CURRENT_OPERATION_COMMIT: Final = (
    "f633f2a8b21c64661b8f8a76d41961e922447c10"
)

VERIFIER_RELATIVE: Final = (
    "scripts/verify_stage3b_qwake_lc4_attempt_002_execution_freeze.py"
)
VERIFIER_TEST_RELATIVE: Final = (
    "tests/unit/test_stage3b_qwake_lc4_attempt_002_execution_freeze.py"
)
IMAGE_SOURCE_ABSENT_PATHS: Final = (
    VERIFIER_RELATIVE,
    VERIFIER_TEST_RELATIVE,
)
FREEZE_MATERIALIZATION_MISMATCHES: Final = {
    VERIFIER_RELATIVE: (
        "db2de557423cfde173851a01a517bfd7df12fdb627ec9a5198621225be3fc332",
        "6691eea819da03e7da06e766c6a4044441cef7a476e204cd08698afb9cb280e3",
    ),
    VERIFIER_TEST_RELATIVE: (
        "418414f0f976d9304446618bd2afe71a21dd11aac62e1aceeb5423f47b1f7b1c",
        "55f365431c2497a1f30180556b8b4dc0477f7357063d4e3eb9aa4e319fcba43d",
    ),
}


class SourceClosureCorrectionError(RuntimeError):
    """Raised when terminal-failure correction evidence differs."""


@dataclass(frozen=True)
class RegistryEntry:
    """One strict SHA-256 registry entry."""

    sha256: str
    relative: str


@dataclass(frozen=True)
class RegistryClassification:
    """Registry classification against one immutable Git commit."""

    exact: tuple[str, ...]
    absent: tuple[str, ...]
    mismatches: tuple[tuple[str, str, str], ...]

    @property
    def is_exact(self) -> bool:
        """Return whether every registry entry is byte-exact."""
        return not self.absent and not self.mismatches


def canonical_json(value: Any) -> str:
    """Return canonical JSON with one terminal newline."""
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


def sha256_object(value: Any) -> str:
    """Return a canonical semantic SHA-256."""
    return "sha256:" + hashlib.sha256(
        canonical_json(value).encode("utf-8")
    ).hexdigest()


def parse_registry(path: Path) -> tuple[RegistryEntry, ...]:
    """Parse a strict two-space SHA-256 registry."""
    if not path.is_file() or path.is_symlink():
        raise SourceClosureCorrectionError(
            f"regular registry is absent: {path}"
        )
    entries: list[RegistryEntry] = []
    observed: set[str] = set()
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        digest, separator, relative = line.partition("  ")
        if separator != "  " or len(digest) != 64:
            raise SourceClosureCorrectionError(
                f"registry line shape differs: {line_number}"
            )
        try:
            int(digest, 16)
        except ValueError as exc:
            raise SourceClosureCorrectionError(
                "registry digest is not hexadecimal"
            ) from exc
        if not relative or relative in observed:
            raise SourceClosureCorrectionError(
                "registry path is empty or duplicated"
            )
        observed.add(relative)
        entries.append(RegistryEntry(digest, relative))
    return tuple(entries)


def git_blob(root: Path, commit: str, relative: str) -> bytes | None:
    """Read one Git blob without changing the worktree."""
    completed = subprocess.run(
        ["git", "show", f"{commit}:{relative}"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return None
    return completed.stdout


def classify_registry_at_commit(
    root: Path,
    commit: str,
    entries: tuple[RegistryEntry, ...],
) -> RegistryClassification:
    """Classify every registry path against one exact commit."""
    exact: list[str] = []
    absent: list[str] = []
    mismatches: list[tuple[str, str, str]] = []
    for entry in entries:
        content = git_blob(root, commit, entry.relative)
        if content is None:
            absent.append(entry.relative)
            continue
        observed = hashlib.sha256(content).hexdigest()
        if observed == entry.sha256:
            exact.append(entry.relative)
        else:
            mismatches.append(
                (entry.relative, entry.sha256, observed)
            )
    return RegistryClassification(
        exact=tuple(exact),
        absent=tuple(absent),
        mismatches=tuple(mismatches),
    )


def verify_failed_outcome(record: Mapping[str, object]) -> None:
    """Verify exact failed-after-spawn, pre-lease semantics."""
    expected: Mapping[str, object] = {
        "status": (
            "completed_or_failed_partial_effect_no_retry_permitted"
        ),
        "process_spawned": True,
        "docker_run_invoked": True,
        "lease_v1_present": False,
        "lease_sha256": None,
        "output_root_present": False,
        "authorization_consumed": False,
        "attempt_started": False,
        "runtime_started": True,
        "automatic_retry_permitted": False,
        "error": None,
    }
    for key, value in expected.items():
        if record.get(key) != value:
            raise SourceClosureCorrectionError(
                f"failed outcome differs: {key}"
            )
    return_code = record.get("process_return_code")
    if (
        not isinstance(return_code, int)
        or isinstance(return_code, bool)
        or return_code == 0
    ):
        raise SourceClosureCorrectionError(
            "failed outcome return code differs"
        )


def verify_semantic_digest(
    record: Mapping[str, object],
    field: str,
) -> None:
    """Verify one self-contained semantic digest field."""
    observed = record.get(field)
    if not isinstance(observed, str):
        raise SourceClosureCorrectionError(
            f"semantic digest field is absent: {field}"
        )
    payload = dict(record)
    payload.pop(field)
    if sha256_object(payload) != observed:
        raise SourceClosureCorrectionError(
            f"semantic digest differs: {field}"
        )
