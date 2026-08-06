"""Source-closure gates for the future attempt-003 image build.

Importing this module has no repository, Docker, runtime, model, dataset,
lease, outcome, or authorization effects.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import subprocess
from collections.abc import Callable, Iterable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Final

ATTEMPT_ID: Final = 'stage3b-qwake-lc4-runtime-validation-v1-attempt-003'
IMPLEMENTATION_PACKAGE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-attempt-003-"
    "clean-source-closure-"
    "implementation-authoring-v1"
)
RUNTIME_REGISTRY: Final = IMPLEMENTATION_PACKAGE / "runtime-SHA256SUMS"
DOCKERIGNORE_BEGIN: Final = (
    "# BEGIN QWAKE ATTEMPT-003 RUNTIME SOURCE CLOSURE"
)
DOCKERIGNORE_END: Final = (
    "# END QWAKE ATTEMPT-003 RUNTIME SOURCE CLOSURE"
)
DOCKERFILE_GATE_MARKER: Final = (
    "# QWake attempt-003 runtime source-closure gate."
)
DOCKERFILE_HASH_COMMAND: Final = (
    "sha256sum -c experiments/frozen/stage3b-qwake-attempt-003-clean-source-closure-implementation-authoring-v1/runtime-SHA256SUMS"
)
DOCKERFILE_VERIFIER_COMMAND: Final = (
    "python scripts/"
    "verify_stage3b_qwake_attempt_003_buildtime_closure.py "
    "--project-root /workspace"
)
REQUIRED_RUNTIME_PATHS: Final = (
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

GitRunner = Callable[[Sequence[str]], bytes]


class SourceClosureError(RuntimeError):
    """Raised when any source-closure gate fails closed."""


@dataclass(frozen=True, order=True)
class RegistryEntry:
    sha256: str
    path: str

    def require(self) -> None:
        if len(self.sha256) != 64 or any(
            value not in "0123456789abcdef"
            for value in self.sha256
        ):
            raise SourceClosureError(
                f"invalid SHA-256 for {self.path}"
            )
        pure = PurePosixPath(self.path)
        if (
            not self.path
            or pure.is_absolute()
            or ".." in pure.parts
            or self.path.startswith("./")
        ):
            raise SourceClosureError(
                f"unsafe registry path: {self.path!r}"
            )


@dataclass(frozen=True)
class ClosureEntry:
    path: str
    sha256: str
    byte_count: int
    git_object_present: bool
    docker_context_included: bool


@dataclass(frozen=True)
class ClosureReport:
    schema_version: int
    report_id: str
    attempt_id: str
    source_commit: str
    registry_sha256: str
    dockerignore_sha256: str
    entries: tuple[ClosureEntry, ...]
    all_git_objects_present: bool
    all_blob_hashes_exact: bool
    all_docker_context_paths_included: bool
    runtime_execution_performed: bool
    model_code_invoked: bool
    dataset_accessed: bool

    def canonical_json(self) -> str:
        return canonical_json(asdict(self))


def canonical_json(value: Any) -> str:
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


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def parse_registry_bytes(raw: bytes) -> tuple[RegistryEntry, ...]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SourceClosureError(
            "registry must be UTF-8"
        ) from exc

    entries: list[RegistryEntry] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        digest, separator, relative = line.partition("  ")
        if separator != "  ":
            raise SourceClosureError(
                f"invalid registry line {line_number}"
            )
        entry = RegistryEntry(digest, relative)
        entry.require()
        entries.append(entry)

    if not entries:
        raise SourceClosureError("registry is empty")
    if tuple(entries) != tuple(sorted(entries, key=lambda item: item.path)):
        raise SourceClosureError("registry paths are not sorted")
    paths = [entry.path for entry in entries]
    if len(paths) != len(set(paths)):
        raise SourceClosureError("registry paths are duplicated")
    return tuple(entries)


def load_registry(path: Path) -> tuple[RegistryEntry, ...]:
    if not path.is_file() or path.is_symlink():
        raise SourceClosureError(
            f"regular registry file required: {path}"
        )
    return parse_registry_bytes(path.read_bytes())


def verify_required_runtime_path_set(
    entries: Iterable[RegistryEntry],
) -> None:
    observed = tuple(entry.path for entry in entries)
    expected = tuple(sorted(REQUIRED_RUNTIME_PATHS))
    if observed != expected:
        raise SourceClosureError(
            "runtime registry path set differs"
        )


def verify_worktree_registry(
    project_root: Path,
    registry_path: Path | None = None,
) -> tuple[ClosureEntry, ...]:
    root = project_root.expanduser().resolve()
    registry = (
        registry_path
        if registry_path is not None
        else root / RUNTIME_REGISTRY
    )
    entries = load_registry(registry)
    verify_required_runtime_path_set(entries)

    result: list[ClosureEntry] = []
    for entry in entries:
        target = root / entry.path
        if not target.is_file() or target.is_symlink():
            raise SourceClosureError(
                f"regular runtime source required: {entry.path}"
            )
        raw = target.read_bytes()
        observed = sha256_bytes(raw)
        if observed != entry.sha256:
            raise SourceClosureError(
                f"runtime source digest differs: {entry.path}"
            )
        result.append(
            ClosureEntry(
                path=entry.path,
                sha256=entry.sha256,
                byte_count=len(raw),
                git_object_present=False,
                docker_context_included=True,
            )
        )
    return tuple(result)


def subprocess_git_runner(project_root: Path) -> GitRunner:
    root = project_root.expanduser().resolve()

    def run(arguments: Sequence[str]) -> bytes:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=root,
            check=False,
            capture_output=True,
        )
        if completed.returncode != 0:
            stderr = completed.stderr.decode(
                "utf-8",
                errors="replace",
            ).strip()
            raise SourceClosureError(
                f"git command failed: {arguments!r}: {stderr}"
            )
        return completed.stdout

    return run


def _require_commit(value: str) -> None:
    if len(value) != 40 or any(
        item not in "0123456789abcdef"
        for item in value
    ):
        raise SourceClosureError("exact 40-hex source commit required")


def verify_commit_registry(
    project_root: Path,
    source_commit: str,
    *,
    runner: GitRunner | None = None,
    registry_path: Path | None = None,
) -> tuple[ClosureEntry, ...]:
    _require_commit(source_commit)
    root = project_root.expanduser().resolve()
    registry = (
        registry_path
        if registry_path is not None
        else root / RUNTIME_REGISTRY
    )
    entries = load_registry(registry)
    verify_required_runtime_path_set(entries)
    git = runner or subprocess_git_runner(root)

    result: list[ClosureEntry] = []
    for entry in entries:
        object_name = f"{source_commit}:{entry.path}"
        git(("cat-file", "-e", object_name))
        raw = git(("show", object_name))
        observed = sha256_bytes(raw)
        if observed != entry.sha256:
            raise SourceClosureError(
                f"committed blob digest differs: {entry.path}"
            )
        result.append(
            ClosureEntry(
                path=entry.path,
                sha256=entry.sha256,
                byte_count=len(raw),
                git_object_present=True,
                docker_context_included=True,
            )
        )
    return tuple(result)


def required_dockerignore_negations(
    runtime_paths: Iterable[str] = REQUIRED_RUNTIME_PATHS,
) -> tuple[str, ...]:
    values: set[str] = set()
    for raw in runtime_paths:
        pure = PurePosixPath(raw)
        for index in range(1, len(pure.parts)):
            parent = PurePosixPath(*pure.parts[:index]).as_posix()
            values.add(f"!{parent}/")
        values.add(f"!{pure.as_posix()}")
    return tuple(sorted(values))


def closure_dockerignore_block() -> str:
    lines = (
        DOCKERIGNORE_BEGIN,
        *required_dockerignore_negations(),
        DOCKERIGNORE_END,
    )
    return "\n".join(lines) + "\n"


def verify_dockerignore_closure(path: Path) -> None:
    if not path.is_file() or path.is_symlink():
        raise SourceClosureError(
            "regular .dockerignore file required"
        )
    text = path.read_text(encoding="utf-8")
    if text.count(DOCKERIGNORE_BEGIN) != 1:
        raise SourceClosureError(
            "dockerignore closure begin marker differs"
        )
    if text.count(DOCKERIGNORE_END) != 1:
        raise SourceClosureError(
            "dockerignore closure end marker differs"
        )
    begin = text.index(DOCKERIGNORE_BEGIN)
    prefix = text[:begin]
    observed = text[begin:]
    expected = closure_dockerignore_block()
    if observed != expected:
        raise SourceClosureError(
            "dockerignore closure block must be exact and terminal"
        )
    if prefix and not prefix.endswith("\n"):
        raise SourceClosureError(
            "dockerignore prefix must end with newline"
        )


def verify_dockerfile_gate(path: Path) -> None:
    if not path.is_file() or path.is_symlink():
        raise SourceClosureError("regular Dockerfile required")
    text = path.read_text(encoding="utf-8")
    if text.count("COPY . /workspace") != 1:
        raise SourceClosureError(
            "exact COPY . /workspace anchor required"
        )
    for required in (
        DOCKERFILE_GATE_MARKER,
        DOCKERFILE_HASH_COMMAND,
        DOCKERFILE_VERIFIER_COMMAND,
    ):
        if text.count(required) != 1:
            raise SourceClosureError(
                f"Dockerfile gate fragment differs: {required}"
            )
    copy_index = text.index("COPY . /workspace")
    marker_index = text.index(DOCKERFILE_GATE_MARKER)
    hash_index = text.index(DOCKERFILE_HASH_COMMAND)
    verifier_index = text.index(DOCKERFILE_VERIFIER_COMMAND)
    if not (
        copy_index < marker_index < hash_index < verifier_index
    ):
        raise SourceClosureError(
            "Dockerfile closure gate ordering differs"
        )


def build_closure_report(
    *,
    source_commit: str,
    registry_raw: bytes,
    dockerignore_raw: bytes,
    entries: tuple[ClosureEntry, ...],
) -> ClosureReport:
    _require_commit(source_commit)
    if not entries:
        raise SourceClosureError("closure entries are empty")
    if any(not entry.git_object_present for entry in entries):
        raise SourceClosureError(
            "closure report requires committed Git objects"
        )
    return ClosureReport(
        schema_version=1,
        report_id=(
            "stage3b-qwake-attempt-003-"
            "prebuild-source-closure-report-v1"
        ),
        attempt_id=ATTEMPT_ID,
        source_commit=source_commit,
        registry_sha256="sha256:" + sha256_bytes(registry_raw),
        dockerignore_sha256=(
            "sha256:" + sha256_bytes(dockerignore_raw)
        ),
        entries=entries,
        all_git_objects_present=True,
        all_blob_hashes_exact=True,
        all_docker_context_paths_included=True,
        runtime_execution_performed=False,
        model_code_invoked=False,
        dataset_accessed=False,
    )


def write_report_no_replace(path: Path, report: ClosureReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
        0o644,
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(report.canonical_json())
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            path.unlink()
        raise
