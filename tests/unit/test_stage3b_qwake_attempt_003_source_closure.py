from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from torch2pc_thesis.stage3b_qwake_attempt_003_source_closure import (
    DOCKERIGNORE_BEGIN,
    DOCKERIGNORE_END,
    REQUIRED_RUNTIME_PATHS,
    SourceClosureError,
    closure_dockerignore_block,
    parse_registry_bytes,
    required_dockerignore_negations,
    verify_commit_registry,
    verify_dockerignore_closure,
)


def test_required_runtime_path_set_is_closed() -> None:
    assert REQUIRED_RUNTIME_PATHS == (
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
    assert len(REQUIRED_RUNTIME_PATHS) == 13
    assert all(
        "container_runtime.py" not in path
        for path in REQUIRED_RUNTIME_PATHS
    )
    assert all(
        "execution_freeze.py" not in path
        for path in REQUIRED_RUNTIME_PATHS
    )


def test_registry_parser_requires_sorted_unique_safe_paths() -> None:
    raw = (
        b"0" * 64
        + b"  Dockerfile.rocm\n"
        + b"1" * 64
        + b"  scripts/example.py\n"
    )
    entries = parse_registry_bytes(raw)
    assert tuple(entry.path for entry in entries) == (
        "Dockerfile.rocm",
        "scripts/example.py",
    )
    with pytest.raises(SourceClosureError):
        parse_registry_bytes(
            b"0" * 64 + b"  ../escape\n"
        )


def test_dockerignore_closure_block_is_terminal_and_exact(
    tmp_path: Path,
) -> None:
    path = tmp_path / ".dockerignore"
    path.write_text(
        "results/*\n" + closure_dockerignore_block(),
        encoding="utf-8",
    )
    verify_dockerignore_closure(path)
    path.write_text(
        path.read_text(encoding="utf-8") + "results/private\n",
        encoding="utf-8",
    )
    with pytest.raises(SourceClosureError):
        verify_dockerignore_closure(path)


def test_dockerignore_negations_include_parent_chains() -> None:
    values = required_dockerignore_negations(
        ("experiments/frozen/example/file.json",)
    )
    assert "!experiments/" in values
    assert "!experiments/frozen/" in values
    assert "!experiments/frozen/example/" in values
    assert "!experiments/frozen/example/file.json" in values
    assert DOCKERIGNORE_BEGIN not in values
    assert DOCKERIGNORE_END not in values


def test_commit_gate_uses_cat_file_and_show(tmp_path: Path) -> None:
    registry = tmp_path / "runtime-SHA256SUMS"
    paths = tuple(sorted(REQUIRED_RUNTIME_PATHS))
    blobs = {
        path: f"blob:{path}\n".encode()
        for path in paths
    }
    registry.write_text(
        "".join(
            f"{hashlib.sha256(blobs[path]).hexdigest()}  {path}\n"
            for path in paths
        ),
        encoding="utf-8",
    )
    calls: list[tuple[str, ...]] = []
    commit = "a" * 40

    def runner(arguments: tuple[str, ...]) -> bytes:
        calls.append(arguments)
        object_name = arguments[-1]
        relative = object_name.split(":", 1)[1]
        if arguments[:2] == ("cat-file", "-e"):
            return b""
        if arguments[0] == "show":
            return blobs[relative]
        raise AssertionError(arguments)

    entries = verify_commit_registry(
        tmp_path,
        commit,
        runner=runner,
        registry_path=registry,
    )
    assert len(entries) == len(paths)
    assert len(calls) == len(paths) * 2
    assert all(entry.git_object_present for entry in entries)
