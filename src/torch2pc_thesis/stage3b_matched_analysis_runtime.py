"""Fail-closed runtime admission for Stage 3B matched descriptive analysis.

This module implements runtime probing, non-computational preflight validation,
future authorization-schema verification, and the executor wrapper.  It does
not contain or issue an execution authorization.  Sealed-evidence execution is
possible only when the exact frozen authorization package exists in the
repository and passes every request, runtime, source, and output-root check.
"""

from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Final, cast

import matplotlib
import numpy as np

from torch2pc_thesis.stage3b_matched_analysis import (
    AnalysisInputPaths,
    Stage3BMatchedAnalysisError,
    _generate_engine,
)
from torch2pc_thesis.stage3b_matched_analysis_execution_request import (
    PROTOCOL_RELATIVE,
    REQUEST_ROOT_RELATIVE,
    SYNTHETIC_CLI_RELATIVE,
    canonical_json_bytes,
    canonical_json_digest,
    sha256_file,
    validate_execution_request,
)

RUNTIME_PREFLIGHT_SCHEMA_VERSION: Final[int] = 1
RUNTIME_AUTHORIZATION_SCHEMA_VERSION: Final[int] = 1
RUNTIME_PREFLIGHT_ID: Final[str] = (
    "stage3b-matched-descriptive-analysis-runtime-preflight-v1"
)
RUNTIME_AUTHORIZATION_ID: Final[str] = (
    "stage3b-matched-descriptive-analysis-execution-authorization-v1"
)
RUNTIME_PREFLIGHT_STATUS: Final[str] = (
    "runtime_preflight_passed_authorization_not_issued"
)
RUNTIME_AUTHORIZATION_STATUS: Final[str] = (
    "issued_single_run_authorization"
)
RUNTIME_OPERATOR_ACKNOWLEDGEMENT: Final[str] = (
    "AUTHORIZE_STAGE3B_MATCHED_DESCRIPTIVE_ANALYSIS_SINGLE_READ_ONLY_RUN"
)
RUNTIME_MODULE_RELATIVE: Final[Path] = Path(
    "src/torch2pc_thesis/stage3b_matched_analysis_runtime.py"
)
PREFLIGHT_CLI_RELATIVE: Final[Path] = Path(
    "scripts/preflight_stage3b_matched_analysis.py"
)
EXECUTOR_CLI_RELATIVE: Final[Path] = Path(
    "scripts/execute_stage3b_matched_analysis.py"
)
ANALYSIS_MODULE_RELATIVE: Final[Path] = Path(
    "src/torch2pc_thesis/stage3b_matched_analysis.py"
)
REQUEST_MODULE_RELATIVE: Final[Path] = Path(
    "src/torch2pc_thesis/stage3b_matched_analysis_execution_request.py"
)
PROTOCOL_MODULE_RELATIVE: Final[Path] = Path(
    "src/torch2pc_thesis/stage3b_matched_analysis_protocol.py"
)
PROTOCOL_REGISTRY_RELATIVE: Final[Path] = (
    PROTOCOL_RELATIVE.parent / "SHA256SUMS"
)
AUTHORIZATION_ROOT_RELATIVE: Final[Path] = Path(
    "experiments/frozen/"
    "stage3b-matched-descriptive-analysis-execution-authorization-v1"
)
RUNTIME_PREFLIGHT_FILE_NAME: Final[str] = "runtime-preflight.json"
RUNTIME_AUTHORIZATION_FILE_NAME: Final[str] = "authorization.json"
AUTHORIZATION_REGISTRY_FILE_NAME: Final[str] = "SHA256SUMS"
EXECUTION_RECEIPT_SCHEMA_VERSION: Final[int] = 1
EXECUTION_RECEIPT_STATUS: Final[str] = "single_execution_attempt_claimed"
EXECUTION_RECEIPT_DIRECTORY: Final[Path] = Path(
    "torch2pc-thesis/stage3b-matched-analysis-execution-receipts"
)
EXPECTED_AUTHORIZATION_PACKAGE_FILES: Final[frozenset[str]] = frozenset(
    {
        RUNTIME_PREFLIGHT_FILE_NAME,
        RUNTIME_AUTHORIZATION_FILE_NAME,
        AUTHORIZATION_REGISTRY_FILE_NAME,
    }
)
EXPECTED_REQUEST_SHA256: Final[str] = (
    "4b1a4c9c1d387ee9b5d528752aa14002b07844cd99073b96476958a937c143a7"
)
EXPECTED_REQUEST_REGISTRY_SHA256: Final[str] = (
    "1a26c4b0d50fe2fd4dcc18663fded6e8ed404d8eb6a949b4a0807188c539a45a"
)
_COMMIT_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[0-9a-f]{40}$")
_SHA256_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[0-9a-f]{64}$")


class Stage3BMatchedAnalysisRuntimeError(RuntimeError):
    """Raised when runtime admission or authorization verification fails."""


@dataclass(frozen=True)
class MatchedAnalysisRuntimeProbe:
    """Stable, non-metric runtime identity captured before authorization."""

    python_version: str
    python_implementation: str
    python_executable: str
    python_executable_sha256: str
    platform: str
    system: str
    machine: str
    effective_uid: int
    effective_gid: int
    numpy_version: str
    numpy_module: str
    numpy_module_sha256: str
    matplotlib_version: str
    matplotlib_module: str
    matplotlib_module_sha256: str
    zstd_executable: str
    zstd_executable_sha256: str
    zstd_version: str

    def to_record(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_record(
        cls,
        value: Mapping[str, object],
    ) -> MatchedAnalysisRuntimeProbe:
        def require_string(name: str) -> str:
            item = value.get(name)
            if not isinstance(item, str) or not item:
                raise Stage3BMatchedAnalysisRuntimeError(
                    f"runtime probe field is invalid: {name}"
                )
            return item

        def require_integer(name: str) -> int:
            item = value.get(name)
            if not isinstance(item, int) or isinstance(item, bool):
                raise Stage3BMatchedAnalysisRuntimeError(
                    f"runtime probe field must be an integer: {name}"
                )
            return item

        return cls(
            python_version=require_string("python_version"),
            python_implementation=require_string("python_implementation"),
            python_executable=require_string("python_executable"),
            python_executable_sha256=require_string(
                "python_executable_sha256"
            ),
            platform=require_string("platform"),
            system=require_string("system"),
            machine=require_string("machine"),
            effective_uid=require_integer("effective_uid"),
            effective_gid=require_integer("effective_gid"),
            numpy_version=require_string("numpy_version"),
            numpy_module=require_string("numpy_module"),
            numpy_module_sha256=require_string("numpy_module_sha256"),
            matplotlib_version=require_string("matplotlib_version"),
            matplotlib_module=require_string("matplotlib_module"),
            matplotlib_module_sha256=require_string(
                "matplotlib_module_sha256"
            ),
            zstd_executable=require_string("zstd_executable"),
            zstd_executable_sha256=require_string(
                "zstd_executable_sha256"
            ),
            zstd_version=require_string("zstd_version"),
        )


def _load_json_object(path: Path) -> dict[str, object]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Stage3BMatchedAnalysisRuntimeError(
            f"cannot read JSON object: {path}"
        ) from exc
    if not isinstance(raw, dict):
        raise Stage3BMatchedAnalysisRuntimeError(
            f"expected JSON object: {path}"
        )
    return cast(dict[str, object], raw)


def _require_mapping(value: object, *, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise Stage3BMatchedAnalysisRuntimeError(f"{field} must be an object")
    for key in value:
        if not isinstance(key, str):
            raise Stage3BMatchedAnalysisRuntimeError(
                f"{field} contains a non-string key"
            )
    return cast(Mapping[str, object], value)


def _require_string(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise Stage3BMatchedAnalysisRuntimeError(
            f"{field} must be a non-empty string"
        )
    return value


def _require_bool(value: object, *, field: str) -> bool:
    if not isinstance(value, bool):
        raise Stage3BMatchedAnalysisRuntimeError(f"{field} must be boolean")
    return value


def _require_regular_file(path: Path, *, field: str) -> None:
    if path.is_symlink() or not path.is_file():
        raise Stage3BMatchedAnalysisRuntimeError(
            f"{field} must be a regular file: {path}"
        )


def _validated_commit(value: object, *, field: str) -> str:
    commit = _require_string(value, field=field).lower()
    if not _COMMIT_PATTERN.fullmatch(commit):
        raise Stage3BMatchedAnalysisRuntimeError(
            f"{field} must be a 40-character lowercase commit"
        )
    return commit


def _validated_digest(value: object, *, field: str) -> str:
    digest = _require_string(value, field=field).lower()
    if not _SHA256_PATTERN.fullmatch(digest):
        raise Stage3BMatchedAnalysisRuntimeError(
            f"{field} must be a lowercase SHA-256 digest"
        )
    return digest


def _validated_timestamp(value: object, *, field: str) -> datetime:
    timestamp = _require_string(value, field=field)
    if not timestamp.endswith("Z"):
        raise Stage3BMatchedAnalysisRuntimeError(
            f"{field} must be a UTC timestamp ending in Z"
        )
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as exc:
        raise Stage3BMatchedAnalysisRuntimeError(
            f"{field} is not a valid ISO-8601 timestamp"
        ) from exc
    offset = parsed.utcoffset()
    if offset is None or offset.total_seconds() != 0:
        raise Stage3BMatchedAnalysisRuntimeError(f"{field} must use UTC")
    return parsed


def _run_git(project_root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(project_root), *arguments],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip()
        raise Stage3BMatchedAnalysisRuntimeError(
            f"git {' '.join(arguments)} failed: {message}"
        )
    return completed.stdout.strip()


def _require_clean_project(project_root: Path) -> str:
    resolved = project_root.expanduser().resolve()
    head = _validated_commit(
        _run_git(resolved, "rev-parse", "HEAD"),
        field="project HEAD",
    )
    status = _run_git(
        resolved,
        "status",
        "--porcelain=v1",
        "--untracked-files=normal",
    )
    if status:
        raise Stage3BMatchedAnalysisRuntimeError(
            "project worktree must be clean for runtime admission"
        )
    return head


def _require_exact_source_commit(
    project_root: Path,
    expected_commit: str,
) -> None:
    observed = _require_clean_project(project_root)
    if observed != expected_commit:
        raise Stage3BMatchedAnalysisRuntimeError(
            "runtime-preflight project commit differs: "
            f"expected={expected_commit}, observed={observed}"
        )


def _require_source_ancestor(
    project_root: Path,
    source_commit: str,
) -> None:
    _require_clean_project(project_root)
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(project_root),
            "merge-base",
            "--is-ancestor",
            source_commit,
            "HEAD",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise Stage3BMatchedAnalysisRuntimeError(
            "runtime-preflight source commit is not an ancestor of HEAD"
        )


def _require_main_branch(project_root: Path) -> None:
    branch = _run_git(project_root, "branch", "--show-current")
    if branch != "main":
        raise Stage3BMatchedAnalysisRuntimeError(
            "authorized analysis may execute only from the main branch"
        )


def _require_tracked_files(
    project_root: Path,
    relative_paths: tuple[Path, ...],
) -> None:
    for relative in relative_paths:
        _require_regular_file(
            project_root / relative,
            field="authorization package entry",
        )
        observed = _run_git(
            project_root,
            "ls-files",
            "--error-unmatch",
            relative.as_posix(),
        )
        if observed != relative.as_posix():
            raise Stage3BMatchedAnalysisRuntimeError(
                f"authorization package file is not tracked: {relative}"
            )


def _exact_regular_file_inventory(root: Path) -> frozenset[str]:
    names: set[str] = set()
    for entry in root.iterdir():
        _require_regular_file(entry, field="authorization package entry")
        names.add(entry.name)
    return frozenset(names)


def _validate_registry(
    root: Path,
    registry: Path,
    *,
    expected_names: frozenset[str] | None = None,
) -> None:
    _require_regular_file(registry, field="checksum registry")
    lines = [
        line.strip()
        for line in registry.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    observed_names: set[str] = set()
    for line in lines:
        try:
            expected, relative_name = line.split(maxsplit=1)
        except ValueError as exc:
            raise Stage3BMatchedAnalysisRuntimeError(
                f"invalid checksum registry line: {line!r}"
            ) from exc
        _validated_digest(expected, field="registry SHA-256")
        relative_name = relative_name.lstrip("*")
        if relative_name in observed_names:
            raise Stage3BMatchedAnalysisRuntimeError(
                f"duplicate checksum registry entry: {relative_name}"
            )
        if Path(relative_name).name != relative_name:
            raise Stage3BMatchedAnalysisRuntimeError(
                "authorization registry entries must be top-level files"
            )
        target = root / relative_name
        _require_regular_file(target, field="checksum registry target")
        observed = sha256_file(target)
        if observed != expected:
            raise Stage3BMatchedAnalysisRuntimeError(
                f"registry digest differs for {relative_name}"
            )
        observed_names.add(relative_name)
    if expected_names is not None and observed_names != expected_names:
        raise Stage3BMatchedAnalysisRuntimeError(
            "authorization package checksum inventory differs"
        )


def _validate_request_registry(project_root: Path) -> None:
    request_root = project_root / REQUEST_ROOT_RELATIVE
    _validate_registry(
        request_root,
        request_root / "SHA256SUMS",
        expected_names=frozenset({"request.json"}),
    )


def _request(project_root: Path) -> dict[str, object]:
    root = project_root.expanduser().resolve()
    request_path = root / REQUEST_ROOT_RELATIVE / "request.json"
    registry_path = root / REQUEST_ROOT_RELATIVE / "SHA256SUMS"
    _require_regular_file(
        request_path,
        field="frozen execution-request file",
    )
    _require_regular_file(
        registry_path,
        field="frozen execution-request registry",
    )
    if sha256_file(request_path) != EXPECTED_REQUEST_SHA256:
        raise Stage3BMatchedAnalysisRuntimeError(
            "frozen execution-request SHA-256 differs"
        )
    if sha256_file(registry_path) != EXPECTED_REQUEST_REGISTRY_SHA256:
        raise Stage3BMatchedAnalysisRuntimeError(
            "frozen execution-request registry SHA-256 differs"
        )
    _validate_request_registry(root)
    request = _load_json_object(request_path)
    validate_execution_request(request, root)
    return request


def _source_evidence_identity(
    project_root: Path,
    request: Mapping[str, object],
) -> dict[str, str]:
    source = _require_mapping(
        request.get("source_evidence"),
        field="request source_evidence",
    )
    source_root = project_root / _require_string(
        source.get("root"),
        field="request source_evidence.root",
    )
    expected = _require_mapping(
        source.get("expected_sha256"),
        field="request source_evidence.expected_sha256",
    )
    observed: dict[str, str] = {}
    for name, expected_digest_raw in sorted(expected.items()):
        expected_digest = _validated_digest(
            expected_digest_raw,
            field=f"source SHA-256 for {name}",
        )
        path = source_root / name
        _require_regular_file(path, field="sealed source file")
        digest = sha256_file(path)
        if digest != expected_digest:
            raise Stage3BMatchedAnalysisRuntimeError(
                f"sealed source SHA-256 differs for {name}"
            )
        observed[name] = digest
    return observed


def _resolved_zstd_executable(executable: str) -> str:
    resolved = shutil.which(executable)
    if resolved is None:
        raise Stage3BMatchedAnalysisRuntimeError(
            "zstd executable is unavailable"
        )
    return str(Path(resolved).resolve())


def _zstd_version(executable: str) -> str:
    completed = subprocess.run(
        [executable, "--version"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise Stage3BMatchedAnalysisRuntimeError(
            "zstd executable is unavailable"
        )
    version = completed.stdout.strip() or completed.stderr.strip()
    if not version:
        raise Stage3BMatchedAnalysisRuntimeError(
            "zstd version output is empty"
        )
    return version


def _resolved_module_file(value: str | None, *, field: str) -> Path:
    if value is None:
        raise Stage3BMatchedAnalysisRuntimeError(
            f"runtime dependency module path is unavailable: {field}"
        )
    path = Path(value).resolve()
    _require_regular_file(path, field=field)
    return path


def capture_runtime_probe(
    *,
    zstd_executable: str = "zstd",
) -> MatchedAnalysisRuntimeProbe:
    """Capture runtime identity without reading any observed metric value."""

    resolved_python = Path(sys.executable).resolve()
    _require_regular_file(resolved_python, field="Python executable")
    numpy_module = _resolved_module_file(
        np.__file__,
        field="NumPy module",
    )
    matplotlib_module = _resolved_module_file(
        matplotlib.__file__,
        field="Matplotlib module",
    )
    resolved_zstd = Path(
        _resolved_zstd_executable(zstd_executable)
    ).resolve()
    _require_regular_file(resolved_zstd, field="Zstandard executable")
    return MatchedAnalysisRuntimeProbe(
        python_version=platform.python_version(),
        python_implementation=platform.python_implementation(),
        python_executable=str(resolved_python),
        python_executable_sha256=sha256_file(resolved_python),
        platform=platform.platform(),
        system=platform.system(),
        machine=platform.machine(),
        effective_uid=os.geteuid(),
        effective_gid=os.getegid(),
        numpy_version=np.__version__,
        numpy_module=str(numpy_module),
        numpy_module_sha256=sha256_file(numpy_module),
        matplotlib_version=matplotlib.__version__,
        matplotlib_module=str(matplotlib_module),
        matplotlib_module_sha256=sha256_file(matplotlib_module),
        zstd_executable=str(resolved_zstd),
        zstd_executable_sha256=sha256_file(resolved_zstd),
        zstd_version=_zstd_version(str(resolved_zstd)),
    )


def _verify_zstd_frame(
    archive: Path,
    *,
    zstd_executable: str,
) -> None:
    completed = subprocess.run(
        [zstd_executable, "-t", "--quiet", str(archive)],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip()
        raise Stage3BMatchedAnalysisRuntimeError(
            f"locality Zstandard frame validation failed: {message}"
        )


def _runtime_file_identity(project_root: Path) -> dict[str, str]:
    paths = (
        ANALYSIS_MODULE_RELATIVE,
        REQUEST_MODULE_RELATIVE,
        PROTOCOL_MODULE_RELATIVE,
        RUNTIME_MODULE_RELATIVE,
        PREFLIGHT_CLI_RELATIVE,
        EXECUTOR_CLI_RELATIVE,
        SYNTHETIC_CLI_RELATIVE,
        REQUEST_ROOT_RELATIVE / "request.json",
        REQUEST_ROOT_RELATIVE / "SHA256SUMS",
        PROTOCOL_RELATIVE,
        PROTOCOL_REGISTRY_RELATIVE,
    )
    identity: dict[str, str] = {}
    for relative in paths:
        path = project_root / relative
        _require_regular_file(path, field="runtime-bound file")
        identity[relative.as_posix()] = sha256_file(path)
    return identity


def _runtime_identity(
    project_root: Path,
    *,
    source_commit: str,
    probe: MatchedAnalysisRuntimeProbe,
    request: Mapping[str, object],
) -> dict[str, object]:
    identity: dict[str, object] = {
        "source_commit": source_commit,
        "request_id": request["request_id"],
        "request_digest": request["request_digest"],
        "runtime_probe": probe.to_record(),
        "bound_files_sha256": _runtime_file_identity(project_root),
        "network_access_required": False,
        "observed_metric_values_read": False,
        "test_dataset_access": False,
    }
    return {**identity, "runtime_identity_digest": canonical_json_digest(identity)}


def _output_contract(request: Mapping[str, object]) -> Mapping[str, object]:
    contract = _require_mapping(
        request.get("output_contract"),
        field="request output_contract",
    )
    if contract.get("expected_top_level_file_count") != 18:
        raise Stage3BMatchedAnalysisRuntimeError(
            "request output count differs"
        )
    names = contract.get("expected_top_level_files")
    if not isinstance(names, list) or len(names) != 18:
        raise Stage3BMatchedAnalysisRuntimeError(
            "request output inventory differs"
        )
    return contract


def build_runtime_preflight(
    project_root: Path,
    *,
    source_commit: str,
    captured_at_utc: str,
    probe: MatchedAnalysisRuntimeProbe | None = None,
    zstd_executable: str = "zstd",
) -> dict[str, object]:
    """Build a non-computational runtime preflight for later freezing."""

    root = project_root.expanduser().resolve()
    clean_commit = _validated_commit(
        source_commit,
        field="runtime source_commit",
    )
    _validated_timestamp(captured_at_utc, field="captured_at_utc")
    _require_exact_source_commit(root, clean_commit)
    request = _request(root)
    contract = _output_contract(request)
    output_root = root / _require_string(
        contract.get("root"),
        field="request output_contract.root",
    )
    if output_root.exists():
        raise Stage3BMatchedAnalysisRuntimeError(
            f"requested output root already exists: {output_root}"
        )
    source_identity = _source_evidence_identity(root, request)
    source = _require_mapping(
        request.get("source_evidence"),
        field="request source_evidence",
    )
    evidence_root = root / _require_string(
        source.get("root"),
        field="request source_evidence.root",
    )
    locality_archive = evidence_root / "locality_events.jsonl.zst"
    resolved_zstd = _resolved_zstd_executable(zstd_executable)
    active_probe = probe or capture_runtime_probe(
        zstd_executable=resolved_zstd
    )
    if active_probe.zstd_executable != resolved_zstd:
        raise Stage3BMatchedAnalysisRuntimeError(
            "runtime probe zstd executable differs"
        )
    _verify_zstd_frame(
        locality_archive,
        zstd_executable=active_probe.zstd_executable,
    )
    runtime_identity = _runtime_identity(
        root,
        source_commit=clean_commit,
        probe=active_probe,
        request=request,
    )
    payload: dict[str, object] = {
        "schema_version": RUNTIME_PREFLIGHT_SCHEMA_VERSION,
        "preflight_id": RUNTIME_PREFLIGHT_ID,
        "status": RUNTIME_PREFLIGHT_STATUS,
        "captured_at_utc": captured_at_utc,
        "request_id": request["request_id"],
        "request_digest": request["request_digest"],
        "runtime_identity": runtime_identity,
        "source_evidence": {
            "root": source["root"],
            "access_mode": "read_only",
            "verified_sha256": source_identity,
            "zstandard_frame_tested": True,
            "observed_metric_values_read": False,
        },
        "output_contract": {
            "root": contract["root"],
            "root_absent": True,
            "expected_top_level_file_count": 18,
            "expected_top_level_files": contract[
                "expected_top_level_files"
            ],
        },
        "claim_boundary": {
            "runtime_preflight_implemented": True,
            "runtime_preflight_passed": True,
            "execution_authorization_present": False,
            "analysis_execution_permitted": False,
            "analysis_execution_performed": False,
            "analysis_results_present": False,
            "results_publication_permitted": False,
            "release_publication_permitted": False,
            "source_evidence_read_only": True,
            "observed_metric_values_read": False,
            "test_dataset_access": False,
        },
    }
    return {**payload, "preflight_digest": canonical_json_digest(payload)}


def validate_runtime_preflight(
    preflight: Mapping[str, object],
    project_root: Path,
    *,
    zstd_executable: str = "zstd",
) -> None:
    """Validate a frozen runtime preflight against the current runtime."""

    root = project_root.expanduser().resolve()
    payload = dict(preflight)
    digest = _validated_digest(
        payload.pop("preflight_digest", None),
        field="preflight_digest",
    )
    if canonical_json_digest(payload) != digest:
        raise Stage3BMatchedAnalysisRuntimeError(
            "runtime preflight digest differs"
        )
    if preflight.get("schema_version") != RUNTIME_PREFLIGHT_SCHEMA_VERSION:
        raise Stage3BMatchedAnalysisRuntimeError(
            "runtime preflight schema differs"
        )
    if preflight.get("preflight_id") != RUNTIME_PREFLIGHT_ID:
        raise Stage3BMatchedAnalysisRuntimeError(
            "runtime preflight ID differs"
        )
    if preflight.get("status") != RUNTIME_PREFLIGHT_STATUS:
        raise Stage3BMatchedAnalysisRuntimeError(
            "runtime preflight status differs"
        )
    _validated_timestamp(
        preflight.get("captured_at_utc"),
        field="preflight captured_at_utc",
    )
    request = _request(root)
    if preflight.get("request_id") != request.get("request_id"):
        raise Stage3BMatchedAnalysisRuntimeError(
            "runtime preflight request ID differs"
        )
    if preflight.get("request_digest") != request.get("request_digest"):
        raise Stage3BMatchedAnalysisRuntimeError(
            "runtime preflight request digest differs"
        )
    runtime_identity = _require_mapping(
        preflight.get("runtime_identity"),
        field="runtime preflight identity",
    )
    source_commit = _validated_commit(
        runtime_identity.get("source_commit"),
        field="runtime identity source_commit",
    )
    _require_source_ancestor(root, source_commit)
    recorded_probe = MatchedAnalysisRuntimeProbe.from_record(
        _require_mapping(
            runtime_identity.get("runtime_probe"),
            field="runtime probe",
        )
    )
    current_probe = capture_runtime_probe(
        zstd_executable=zstd_executable
    )
    if current_probe != recorded_probe:
        raise Stage3BMatchedAnalysisRuntimeError(
            "current runtime probe differs from frozen preflight"
        )
    recorded_files = _require_mapping(
        runtime_identity.get("bound_files_sha256"),
        field="runtime bound files",
    )
    current_files = _runtime_file_identity(root)
    if dict(recorded_files) != current_files:
        raise Stage3BMatchedAnalysisRuntimeError(
            "runtime-bound file identity differs"
        )
    identity_payload = dict(runtime_identity)
    identity_digest = _validated_digest(
        identity_payload.pop("runtime_identity_digest", None),
        field="runtime identity digest",
    )
    if canonical_json_digest(identity_payload) != identity_digest:
        raise Stage3BMatchedAnalysisRuntimeError(
            "runtime identity digest differs"
        )
    if runtime_identity.get("request_id") != request.get("request_id"):
        raise Stage3BMatchedAnalysisRuntimeError(
            "runtime identity request ID differs"
        )
    if runtime_identity.get("request_digest") != request.get("request_digest"):
        raise Stage3BMatchedAnalysisRuntimeError(
            "runtime identity request digest differs"
        )
    for key in (
        "network_access_required",
        "observed_metric_values_read",
        "test_dataset_access",
    ):
        if runtime_identity.get(key) is not False:
            raise Stage3BMatchedAnalysisRuntimeError(
                f"runtime identity boundary unexpectedly open: {key}"
            )
    source_identity = _source_evidence_identity(root, request)
    source_record = _require_mapping(
        preflight.get("source_evidence"),
        field="runtime preflight source_evidence",
    )
    if source_record.get("access_mode") != "read_only":
        raise Stage3BMatchedAnalysisRuntimeError(
            "runtime preflight source access differs"
        )
    if source_record.get("observed_metric_values_read") is not False:
        raise Stage3BMatchedAnalysisRuntimeError(
            "runtime preflight metric-read boundary differs"
        )
    source_request = _require_mapping(
        request.get("source_evidence"),
        field="request source_evidence",
    )
    if source_record.get("root") != source_request.get("root"):
        raise Stage3BMatchedAnalysisRuntimeError(
            "runtime preflight source root differs"
        )
    if source_record.get("zstandard_frame_tested") is not True:
        raise Stage3BMatchedAnalysisRuntimeError(
            "runtime preflight Zstandard boundary differs"
        )
    verified = _require_mapping(
        source_record.get("verified_sha256"),
        field="runtime preflight verified SHA-256",
    )
    if dict(verified) != source_identity:
        raise Stage3BMatchedAnalysisRuntimeError(
            "runtime preflight source identity differs"
        )
    source = _require_mapping(
        request.get("source_evidence"),
        field="request source_evidence",
    )
    evidence_root = root / _require_string(
        source.get("root"),
        field="request source_evidence.root",
    )
    _verify_zstd_frame(
        evidence_root / "locality_events.jsonl.zst",
        zstd_executable=current_probe.zstd_executable,
    )
    contract = _output_contract(request)
    preflight_output = _require_mapping(
        preflight.get("output_contract"),
        field="runtime preflight output_contract",
    )
    if preflight_output.get("root") != contract.get("root"):
        raise Stage3BMatchedAnalysisRuntimeError(
            "runtime preflight output root differs"
        )
    if preflight_output.get("root_absent") is not True:
        raise Stage3BMatchedAnalysisRuntimeError(
            "runtime preflight output-root absence differs"
        )
    if preflight_output.get("expected_top_level_file_count") != 18:
        raise Stage3BMatchedAnalysisRuntimeError(
            "runtime preflight output count differs"
        )
    if preflight_output.get("expected_top_level_files") != contract.get(
        "expected_top_level_files"
    ):
        raise Stage3BMatchedAnalysisRuntimeError(
            "runtime preflight output inventory differs"
        )
    output_root = root / _require_string(
        contract.get("root"),
        field="request output_contract.root",
    )
    if output_root.exists():
        raise Stage3BMatchedAnalysisRuntimeError(
            f"requested output root already exists: {output_root}"
        )
    boundary = _require_mapping(
        preflight.get("claim_boundary"),
        field="runtime preflight claim_boundary",
    )
    for key in (
        "runtime_preflight_implemented",
        "runtime_preflight_passed",
        "source_evidence_read_only",
    ):
        if boundary.get(key) is not True:
            raise Stage3BMatchedAnalysisRuntimeError(
                f"runtime preflight boundary is not closed correctly: {key}"
            )
    required_false = (
        "execution_authorization_present",
        "analysis_execution_permitted",
        "analysis_execution_performed",
        "analysis_results_present",
        "results_publication_permitted",
        "release_publication_permitted",
        "observed_metric_values_read",
        "test_dataset_access",
    )
    for key in required_false:
        if boundary.get(key) is not False:
            raise Stage3BMatchedAnalysisRuntimeError(
                f"runtime preflight boundary unexpectedly open: {key}"
            )


def validate_execution_authorization(
    authorization: Mapping[str, object],
    preflight: Mapping[str, object],
    request: Mapping[str, object],
    project_root: Path,
    *,
    zstd_executable: str = "zstd",
) -> None:
    """Validate future authorization; this function never issues one."""

    root = project_root.expanduser().resolve()
    validate_execution_request(request, root)
    validate_runtime_preflight(
        preflight,
        root,
        zstd_executable=zstd_executable,
    )
    payload = dict(authorization)
    digest = _validated_digest(
        payload.pop("authorization_digest", None),
        field="authorization_digest",
    )
    if canonical_json_digest(payload) != digest:
        raise Stage3BMatchedAnalysisRuntimeError(
            "execution authorization digest differs"
        )
    if authorization.get("schema_version") != RUNTIME_AUTHORIZATION_SCHEMA_VERSION:
        raise Stage3BMatchedAnalysisRuntimeError(
            "execution authorization schema differs"
        )
    if authorization.get("authorization_id") != RUNTIME_AUTHORIZATION_ID:
        raise Stage3BMatchedAnalysisRuntimeError(
            "execution authorization ID differs"
        )
    if authorization.get("status") != RUNTIME_AUTHORIZATION_STATUS:
        raise Stage3BMatchedAnalysisRuntimeError(
            "execution authorization status differs"
        )
    if authorization.get("request_id") != request.get("request_id"):
        raise Stage3BMatchedAnalysisRuntimeError(
            "execution authorization request ID differs"
        )
    if authorization.get("request_digest") != request.get("request_digest"):
        raise Stage3BMatchedAnalysisRuntimeError(
            "execution authorization request digest differs"
        )
    if authorization.get("preflight_id") != preflight.get("preflight_id"):
        raise Stage3BMatchedAnalysisRuntimeError(
            "execution authorization preflight ID differs"
        )
    if authorization.get("preflight_digest") != preflight.get("preflight_digest"):
        raise Stage3BMatchedAnalysisRuntimeError(
            "execution authorization preflight digest differs"
        )
    runtime_identity = _require_mapping(
        preflight.get("runtime_identity"),
        field="runtime preflight identity",
    )
    if authorization.get("runtime_identity_digest") != runtime_identity.get(
        "runtime_identity_digest"
    ):
        raise Stage3BMatchedAnalysisRuntimeError(
            "execution authorization runtime identity differs"
        )
    authorization_time = _validated_timestamp(
        authorization.get("generated_at_utc"),
        field="authorization generated_at_utc",
    )
    preflight_time = _validated_timestamp(
        preflight.get("captured_at_utc"),
        field="preflight captured_at_utc",
    )
    if authorization_time < preflight_time:
        raise Stage3BMatchedAnalysisRuntimeError(
            "execution authorization predates runtime preflight"
        )
    if authorization.get("operator_acknowledgement") != (
        RUNTIME_OPERATOR_ACKNOWLEDGEMENT
    ):
        raise Stage3BMatchedAnalysisRuntimeError(
            "execution authorization operator acknowledgement differs"
        )
    if authorization.get("execution_count") != 1:
        raise Stage3BMatchedAnalysisRuntimeError(
            "execution authorization count differs"
        )
    contract = _output_contract(request)
    if authorization.get("output_root") != contract.get("root"):
        raise Stage3BMatchedAnalysisRuntimeError(
            "execution authorization output root differs"
        )
    required_true = (
        "output_root_absent_at_issue",
        "source_sha256_verified_at_issue",
        "source_sha256_verification_required_after_execution",
        "authorization_package_must_be_frozen",
    )
    for key in required_true:
        if not _require_bool(authorization.get(key), field=key):
            raise Stage3BMatchedAnalysisRuntimeError(
                f"execution authorization flag differs: {key}"
            )
    if authorization.get("network_access_required") is not False:
        raise Stage3BMatchedAnalysisRuntimeError(
            "execution authorization network boundary differs"
        )
    boundary = _require_mapping(
        authorization.get("claim_boundary"),
        field="authorization claim_boundary",
    )
    if boundary.get("execution_authorization_present") is not True:
        raise Stage3BMatchedAnalysisRuntimeError(
            "execution authorization presence differs"
        )
    if boundary.get("analysis_execution_permitted") is not True:
        raise Stage3BMatchedAnalysisRuntimeError(
            "execution authorization permission differs"
        )
    for key in (
        "analysis_execution_performed",
        "analysis_results_present",
        "results_publication_permitted",
        "release_publication_permitted",
        "test_dataset_access",
    ):
        if boundary.get(key) is not False:
            raise Stage3BMatchedAnalysisRuntimeError(
                f"execution authorization boundary unexpectedly open: {key}"
            )
    output_root = root / _require_string(
        contract.get("root"),
        field="request output_contract.root",
    )
    if output_root.exists():
        raise Stage3BMatchedAnalysisRuntimeError(
            f"requested output root already exists: {output_root}"
        )


def load_frozen_authorization_package(
    project_root: Path,
    *,
    zstd_executable: str = "zstd",
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    """Load the exact in-repository authorization package or fail closed."""

    root = project_root.expanduser().resolve()
    _require_main_branch(root)
    package_root = root / AUTHORIZATION_ROOT_RELATIVE
    if not package_root.is_dir():
        raise Stage3BMatchedAnalysisRuntimeError(
            "frozen execution-authorization package is absent"
        )
    observed_names = _exact_regular_file_inventory(package_root)
    if observed_names != EXPECTED_AUTHORIZATION_PACKAGE_FILES:
        raise Stage3BMatchedAnalysisRuntimeError(
            "frozen execution-authorization package inventory differs"
        )
    _require_tracked_files(
        root,
        tuple(
            AUTHORIZATION_ROOT_RELATIVE / name
            for name in sorted(EXPECTED_AUTHORIZATION_PACKAGE_FILES)
        ),
    )
    _validate_registry(
        package_root,
        package_root / AUTHORIZATION_REGISTRY_FILE_NAME,
        expected_names=frozenset(
            {
                RUNTIME_PREFLIGHT_FILE_NAME,
                RUNTIME_AUTHORIZATION_FILE_NAME,
            }
        ),
    )
    preflight = _load_json_object(
        package_root / RUNTIME_PREFLIGHT_FILE_NAME
    )
    authorization = _load_json_object(
        package_root / RUNTIME_AUTHORIZATION_FILE_NAME
    )
    request = _request(root)
    validate_execution_authorization(
        authorization,
        preflight,
        request,
        root,
        zstd_executable=zstd_executable,
    )
    return authorization, preflight, request


def _atomic_write_once(
    destination: Path,
    content: bytes,
    *,
    exists_message: str,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, destination)
        except FileExistsError as exc:
            raise Stage3BMatchedAnalysisRuntimeError(
                exists_message
            ) from exc
    finally:
        temporary.unlink(missing_ok=True)


def _git_common_directory(project_root: Path) -> Path:
    value = _run_git(project_root, "rev-parse", "--git-common-dir")
    path = Path(value)
    if not path.is_absolute():
        path = project_root / path
    return path.resolve()


def _execution_receipt_path(
    project_root: Path,
    request: Mapping[str, object],
) -> Path:
    digest = _validated_digest(
        request.get("request_digest"),
        field="request_digest",
    )
    return (
        _git_common_directory(project_root)
        / EXECUTION_RECEIPT_DIRECTORY
        / f"{digest}.json"
    )


def _claim_single_execution_attempt(
    project_root: Path,
    authorization: Mapping[str, object],
    request: Mapping[str, object],
) -> Path:
    contract = _output_contract(request)
    receipt = _execution_receipt_path(project_root, request)
    payload: dict[str, object] = {
        "schema_version": EXECUTION_RECEIPT_SCHEMA_VERSION,
        "status": EXECUTION_RECEIPT_STATUS,
        "authorization_id": authorization["authorization_id"],
        "authorization_digest": authorization["authorization_digest"],
        "request_id": request["request_id"],
        "request_digest": request["request_digest"],
        "generated_at_utc": authorization["generated_at_utc"],
        "output_root": contract["root"],
        "attempt_claimed_before_computation": True,
        "results_publication_permitted": False,
    }
    _atomic_write_once(
        receipt,
        canonical_json_bytes(payload),
        exists_message=(
            "single execution attempt was already claimed for this "
            "authorization"
        ),
    )
    return receipt


def execute_authorized_matched_analysis(
    project_root: Path,
    *,
    zstd_executable: str = "zstd",
) -> dict[str, object]:
    """Consume one local attempt after frozen authorization validation."""

    root = project_root.expanduser().resolve()
    authorization, preflight, request = load_frozen_authorization_package(
        root,
        zstd_executable=zstd_executable,
    )
    source = _require_mapping(
        request.get("source_evidence"),
        field="request source_evidence",
    )
    evidence_root = root / _require_string(
        source.get("root"),
        field="request source_evidence.root",
    )
    contract = _output_contract(request)
    output_root = root / _require_string(
        contract.get("root"),
        field="request output_contract.root",
    )
    source_before = _source_evidence_identity(root, request)
    inputs = AnalysisInputPaths(
        cells=evidence_root / "profiling_cells.csv",
        repetitions=evidence_root / "profiling_repetitions.csv",
        summary=evidence_root / "profiling_summary.csv",
        locality=evidence_root / "locality_events.jsonl.zst",
    )
    runtime_identity = _require_mapping(
        preflight.get("runtime_identity"),
        field="runtime preflight identity",
    )
    source_identity: dict[str, object] = {
        "request_id": request["request_id"],
        "request_digest": request["request_digest"],
        "runtime_preflight_id": preflight["preflight_id"],
        "runtime_preflight_digest": preflight["preflight_digest"],
        "runtime_identity_digest": runtime_identity[
            "runtime_identity_digest"
        ],
        "authorization_id": authorization["authorization_id"],
        "authorization_digest": authorization["authorization_digest"],
        "release_tag": source["release_tag"],
        "release_commit": source["release_commit"],
        "verified_source_sha256": source_before,
    }
    _claim_single_execution_attempt(root, authorization, request)
    output_root.parent.mkdir(parents=True, exist_ok=True)
    staging_parent = Path(
        tempfile.mkdtemp(
            prefix=f".{output_root.name}.authorized.",
            dir=output_root.parent,
        )
    )
    staging_output = staging_parent / "output"
    try:
        summary = _generate_engine(
            inputs,
            staging_output,
            source_kind="sealed_evidence",
            source_identity=source_identity,
            generated_at_utc=_require_string(
                authorization.get("generated_at_utc"),
                field="authorization generated_at_utc",
            ),
        )
        source_after = _source_evidence_identity(root, request)
        if source_after != source_before:
            raise Stage3BMatchedAnalysisRuntimeError(
                "sealed source identity changed after execution"
            )
        if output_root.exists():
            raise Stage3BMatchedAnalysisRuntimeError(
                f"requested output root appeared during execution: "
                f"{output_root}"
            )
        staging_output.rename(output_root)
        return summary
    except Stage3BMatchedAnalysisError:
        raise
    except Stage3BMatchedAnalysisRuntimeError:
        raise
    except Exception as exc:
        raise Stage3BMatchedAnalysisRuntimeError(
            "authorized matched analysis failed"
        ) from exc
    finally:
        shutil.rmtree(staging_parent, ignore_errors=True)


def write_runtime_preflight(
    preflight: Mapping[str, object],
    output_path: Path,
) -> None:
    """Write a preflight candidate atomically without issuing authorization."""

    destination = output_path.expanduser().resolve()
    _atomic_write_once(
        destination,
        canonical_json_bytes(preflight),
        exists_message=(
            f"runtime preflight output already exists: {destination}"
        ),
    )
