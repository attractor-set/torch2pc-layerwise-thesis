"""Attempt-independent runtime identity for QWake scientific execution.

The immutable image is the sole executable source of truth for the active
runtime-manifest path and digest.  Build tooling writes the same values into
OCI labels and environment metadata; host admission, request freezing and the
embedded runtime only read and verify that identity.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

RUNTIME_MANIFEST_RELATIVE_ENV: Final = "QWAKE_RUNTIME_MANIFEST_RELATIVE"
RUNTIME_MANIFEST_SHA256_ENV: Final = "QWAKE_RUNTIME_MANIFEST_SHA256"
RUNTIME_MANIFEST_RELATIVE_LABEL: Final = "io.torch2pc.qwake-runtime-manifest-relative"
RUNTIME_MANIFEST_SHA256_LABEL: Final = "io.torch2pc.qwake-runtime-manifest-sha256"
SOURCE_COMMIT_ENV: Final = "QWAKE_SCIENTIFIC_SOURCE_COMMIT_V2"
SOURCE_COMMIT_LABEL: Final = "org.opencontainers.image.revision"

_SHA256_RE: Final = re.compile(r"sha256:[0-9a-f]{64}")
_COMMIT_RE: Final = re.compile(r"[0-9a-f]{40}")


class ScientificRuntimeIdentityError(RuntimeError):
    """Raised when immutable scientific runtime identity is inconsistent."""


@dataclass(frozen=True)
class ScientificRuntimeIdentity:
    """Canonical image-bound runtime-manifest identity."""

    relative_path: str
    sha256: str

    def require(self) -> None:
        path = Path(self.relative_path)
        if path.is_absolute() or not path.parts or ".." in path.parts:
            raise ScientificRuntimeIdentityError(
                "runtime-manifest path must be confined and relative"
            )
        if _SHA256_RE.fullmatch(self.sha256) is None:
            raise ScientificRuntimeIdentityError(
                "runtime-manifest digest must be exact SHA-256"
            )


def _sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _environment_map(values: object) -> dict[str, str]:
    if not isinstance(values, list):
        raise ScientificRuntimeIdentityError("Docker image environment is absent")
    result: dict[str, str] = {}
    for item in values:
        if isinstance(item, str) and "=" in item:
            name, value = item.split("=", 1)
            result[name] = value
    return result


def runtime_identity_from_environment(environment: Mapping[str, str]) -> ScientificRuntimeIdentity:
    """Read the immutable runtime identity exposed inside the image."""

    identity = ScientificRuntimeIdentity(
        relative_path=environment.get(RUNTIME_MANIFEST_RELATIVE_ENV, ""),
        sha256=environment.get(RUNTIME_MANIFEST_SHA256_ENV, ""),
    )
    identity.require()
    return identity


def runtime_identity_from_image_inspection(
    image: Mapping[str, object],
    *,
    expected_image_digest: str | None = None,
    expected_source_commit: str | None = None,
    expected_code_manifest_sha256: str | None = None,
) -> ScientificRuntimeIdentity:
    """Derive runtime truth from one immutable ``docker image inspect`` object."""

    image_id = image.get("Id")
    if expected_image_digest is not None and image_id != expected_image_digest:
        raise ScientificRuntimeIdentityError("local Docker image ID differs")

    config = image.get("Config")
    if not isinstance(config, dict):
        raise ScientificRuntimeIdentityError("Docker image Config is absent")
    labels = config.get("Labels")
    if not isinstance(labels, dict):
        raise ScientificRuntimeIdentityError("Docker image labels are absent")
    env_map = _environment_map(config.get("Env"))

    label_relative = labels.get(RUNTIME_MANIFEST_RELATIVE_LABEL)
    label_sha256 = labels.get(RUNTIME_MANIFEST_SHA256_LABEL)
    env_relative = env_map.get(RUNTIME_MANIFEST_RELATIVE_ENV)
    env_sha256 = env_map.get(RUNTIME_MANIFEST_SHA256_ENV)
    if not all(isinstance(value, str) for value in (label_relative, label_sha256)):
        raise ScientificRuntimeIdentityError(
            "Docker image runtime-manifest labels are absent"
        )
    if label_relative != env_relative or label_sha256 != env_sha256:
        raise ScientificRuntimeIdentityError(
            "Docker image runtime-manifest label/environment identity differs"
        )

    identity = ScientificRuntimeIdentity(
        relative_path=str(label_relative),
        sha256=str(label_sha256),
    )
    identity.require()
    if (
        expected_code_manifest_sha256 is not None
        and identity.sha256 != expected_code_manifest_sha256
    ):
        raise ScientificRuntimeIdentityError(
            "request runtime-manifest digest differs from immutable image"
        )

    if expected_source_commit is not None:
        if _COMMIT_RE.fullmatch(expected_source_commit) is None:
            raise ScientificRuntimeIdentityError("expected source commit is malformed")
        if labels.get(SOURCE_COMMIT_LABEL) != expected_source_commit:
            raise ScientificRuntimeIdentityError("Docker source-revision label differs")
        if env_map.get(SOURCE_COMMIT_ENV) != expected_source_commit:
            raise ScientificRuntimeIdentityError("Docker SOURCE_GIT_COMMIT differs")
    return identity


def resolve_runtime_manifest(root: Path, identity: ScientificRuntimeIdentity) -> Path:
    """Resolve the identity path without permitting repository escape."""

    identity.require()
    resolved_root = root.expanduser().resolve()
    candidate = (resolved_root / identity.relative_path).resolve()
    try:
        candidate.relative_to(resolved_root)
    except ValueError as exc:
        raise ScientificRuntimeIdentityError(
            "runtime-manifest path escapes project root"
        ) from exc
    return candidate


def verify_runtime_manifest(
    root: Path,
    identity: ScientificRuntimeIdentity,
    *,
    required_paths: Sequence[str] = (),
    exact_inventory_root: Path | None = None,
) -> tuple[str, ...]:
    """Verify manifest bytes, every closure member and optional exact inventory.

    When ``exact_inventory_root`` is supplied, every regular file below that
    root must be either a manifest member or the manifest itself.  This is used
    by the scientific image builder to prove that ``COPY .`` cannot carry
    repository results, sibling evidence, or other unbound files into the final
    image.
    """

    manifest = resolve_runtime_manifest(root, identity)
    if not manifest.is_file() or manifest.is_symlink():
        raise ScientificRuntimeIdentityError("scientific runtime manifest is absent")
    if _sha256_file(manifest) != identity.sha256:
        raise ScientificRuntimeIdentityError("scientific runtime manifest digest differs")

    seen: set[str] = set()
    for line_number, line in enumerate(
        manifest.read_text(encoding="utf-8", errors="strict").splitlines(),
        start=1,
    ):
        digest, separator, relative = line.partition("  ")
        if (
            separator != "  "
            or re.fullmatch(r"[0-9a-f]{64}", digest) is None
            or not relative
            or relative in seen
        ):
            raise ScientificRuntimeIdentityError(
                f"malformed runtime source manifest line {line_number}"
            )
        relative_path = Path(relative)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ScientificRuntimeIdentityError(
                f"runtime source closure path is unsafe: {relative}"
            )
        seen.add(relative)
        path = (root / relative_path).resolve()
        try:
            path.relative_to(root.resolve())
        except ValueError as exc:
            raise ScientificRuntimeIdentityError(
                f"runtime source closure path escapes root: {relative}"
            ) from exc
        if not path.is_file() or path.is_symlink():
            raise ScientificRuntimeIdentityError(
                f"runtime source closure path is absent: {relative}"
            )
        if _sha256_file(path) != "sha256:" + digest:
            raise ScientificRuntimeIdentityError(
                f"runtime source closure digest differs: {relative}"
            )

    missing = sorted(set(required_paths) - seen)
    if missing:
        raise ScientificRuntimeIdentityError(
            f"runtime source manifest omits required closure paths: {missing}"
        )

    if exact_inventory_root is not None:
        inventory_root = exact_inventory_root.resolve()
        manifest_relative = manifest.relative_to(inventory_root).as_posix()
        allowed = seen | {manifest_relative}
        observed: set[str] = set()
        for path in inventory_root.rglob("*"):
            if path.is_symlink():
                raise ScientificRuntimeIdentityError(
                    f"scientific build context contains symlink: {path}"
                )
            if path.is_file():
                observed.add(path.relative_to(inventory_root).as_posix())
        extra = sorted(observed - allowed)
        missing_inventory = sorted(allowed - observed)
        if extra or missing_inventory:
            raise ScientificRuntimeIdentityError(
                "scientific build context inventory differs: "
                f"extra={extra}; missing={missing_inventory}"
            )

    return tuple(sorted(seen))
