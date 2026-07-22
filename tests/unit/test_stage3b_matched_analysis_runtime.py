from __future__ import annotations

import json
import os
import shutil
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import cast

import pytest

import torch2pc_thesis.stage3b_matched_analysis_runtime as runtime
from torch2pc_thesis.stage3b_matched_analysis_runtime import (
    RUNTIME_AUTHORIZATION_ID,
    RUNTIME_AUTHORIZATION_STATUS,
    RUNTIME_OPERATOR_ACKNOWLEDGEMENT,
    RUNTIME_PREFLIGHT_ID,
    RUNTIME_PREFLIGHT_STATUS,
    MatchedAnalysisRuntimeProbe,
    Stage3BMatchedAnalysisRuntimeError,
    build_runtime_preflight,
    canonical_json_digest,
    execute_authorized_matched_analysis,
    load_frozen_authorization_package,
    validate_execution_authorization,
    validate_runtime_preflight,
    write_runtime_preflight,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_RELATIVE = Path(
    "results/stage-3/profiling/matched/"
    "stage3b-matched-profiling-e1dcfb2-v1"
)
REQUEST_RELATIVE = Path(
    "experiments/frozen/"
    "stage3b-matched-descriptive-analysis-execution-request-v1"
)
PROTOCOL_RELATIVE = Path(
    "experiments/frozen/stage3b-matched-descriptive-analysis-v1"
)


def _run(*args: str, cwd: Path) -> str:
    completed = subprocess.run(
        list(args),
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(source, destination)
    except OSError:
        shutil.copy2(source, destination)


def _fake_zstd(root: Path) -> Path:
    path = root / "bin/zstd"
    path.parent.mkdir(parents=True)
    path.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"--version\" ]; then\n"
        "  echo 'zstd synthetic runtime test v1'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"-t\" ]; then\n"
        "  exit 0\n"
        "fi\n"
        "exit 2\n",
        encoding="utf-8",
    )
    path.chmod(0o755)
    return path


@pytest.fixture(scope="module")
def runtime_project(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, str, Path]:
    root = tmp_path_factory.mktemp("stage3b-runtime-project")
    relative_files = [
        Path("src/torch2pc_thesis/stage3b_matched_analysis.py"),
        Path(
            "src/torch2pc_thesis/"
            "stage3b_matched_analysis_execution_request.py"
        ),
        Path("src/torch2pc_thesis/stage3b_matched_analysis_protocol.py"),
        Path("src/torch2pc_thesis/stage3b_matched_analysis_runtime.py"),
        Path("scripts/analyze_stage3b_matched.py"),
        Path("scripts/preflight_stage3b_matched_analysis.py"),
        Path("scripts/execute_stage3b_matched_analysis.py"),
        REQUEST_RELATIVE / "request.json",
        REQUEST_RELATIVE / "SHA256SUMS",
        PROTOCOL_RELATIVE / "protocol.json",
        PROTOCOL_RELATIVE / "SHA256SUMS",
    ]
    for relative in relative_files:
        _copy_file(PROJECT_ROOT / relative, root / relative)
    for name in (
        "SEALED-SHA256SUMS",
        "SHA256SUMS",
        "analysis_metadata.json",
        "locality_events.asset.json",
        "locality_events.jsonl.zst",
        "profiling_cells.csv",
        "profiling_repetitions.csv",
        "profiling_summary.csv",
        "seal.json",
    ):
        _copy_file(
            PROJECT_ROOT / EVIDENCE_RELATIVE / name,
            root / EVIDENCE_RELATIVE / name,
        )
    zstd = _fake_zstd(root)
    _run("git", "init", "-b", "main", cwd=root)
    _run("git", "config", "user.email", "runtime-test@example.com", cwd=root)
    _run("git", "config", "user.name", "Runtime Test", cwd=root)
    _run("git", "add", "-A", cwd=root)
    _run("git", "commit", "-m", "runtime fixture", cwd=root)
    commit = _run("git", "rev-parse", "HEAD", cwd=root)
    return root, commit, zstd


def _preflight(
    runtime_project: tuple[Path, str, Path],
) -> dict[str, object]:
    root, commit, zstd = runtime_project
    return build_runtime_preflight(
        root,
        source_commit=commit,
        captured_at_utc="2026-07-22T12:00:00Z",
        zstd_executable=str(zstd),
    )


def _request(root: Path) -> dict[str, object]:
    return cast(
        dict[str, object],
        json.loads(
            (root / REQUEST_RELATIVE / "request.json").read_text(
                encoding="utf-8"
            )
        ),
    )


def _authorization(
    preflight: dict[str, object],
    request: dict[str, object],
) -> dict[str, object]:
    runtime_identity = cast(
        dict[str, object],
        preflight["runtime_identity"],
    )
    output = cast(dict[str, object], request["output_contract"])
    payload: dict[str, object] = {
        "schema_version": 1,
        "authorization_id": RUNTIME_AUTHORIZATION_ID,
        "status": RUNTIME_AUTHORIZATION_STATUS,
        "request_id": request["request_id"],
        "request_digest": request["request_digest"],
        "preflight_id": preflight["preflight_id"],
        "preflight_digest": preflight["preflight_digest"],
        "runtime_identity_digest": runtime_identity[
            "runtime_identity_digest"
        ],
        "generated_at_utc": "2026-07-22T13:00:00Z",
        "operator_acknowledgement": RUNTIME_OPERATOR_ACKNOWLEDGEMENT,
        "execution_count": 1,
        "output_root": output["root"],
        "output_root_absent_at_issue": True,
        "source_sha256_verified_at_issue": True,
        "source_sha256_verification_required_after_execution": True,
        "authorization_package_must_be_frozen": True,
        "network_access_required": False,
        "claim_boundary": {
            "execution_authorization_present": True,
            "analysis_execution_permitted": True,
            "analysis_execution_performed": False,
            "analysis_results_present": False,
            "results_publication_permitted": False,
            "release_publication_permitted": False,
            "test_dataset_access": False,
        },
    }
    return {
        **payload,
        "authorization_digest": canonical_json_digest(payload),
    }


def _output_root(root: Path, request: Mapping[str, object]) -> Path:
    output = cast(Mapping[str, object], request["output_contract"])
    return root / cast(str, output["root"])


def _receipt_path(
    root: Path,
    request: Mapping[str, object],
) -> Path:
    return runtime._execution_receipt_path(root, request)


def _remove_execution_artifacts(
    root: Path,
    request: Mapping[str, object],
    authorization: Mapping[str, object],
) -> None:
    shutil.rmtree(_output_root(root, request), ignore_errors=True)
    _receipt_path(root, request).unlink(missing_ok=True)


def test_runtime_preflight_is_noncomputational_and_authorization_closed(
    runtime_project: tuple[Path, str, Path],
) -> None:
    root, _commit, zstd = runtime_project
    preflight = _preflight(runtime_project)

    assert preflight["preflight_id"] == RUNTIME_PREFLIGHT_ID
    assert preflight["status"] == RUNTIME_PREFLIGHT_STATUS
    boundary = cast(dict[str, object], preflight["claim_boundary"])
    source = cast(dict[str, object], preflight["source_evidence"])
    assert boundary["runtime_preflight_passed"] is True
    assert boundary["execution_authorization_present"] is False
    assert boundary["analysis_execution_permitted"] is False
    assert boundary["analysis_execution_performed"] is False
    assert boundary["analysis_results_present"] is False
    assert boundary["observed_metric_values_read"] is False
    assert source["access_mode"] == "read_only"
    assert source["zstandard_frame_tested"] is True
    assert source["observed_metric_values_read"] is False
    identity = cast(dict[str, object], preflight["runtime_identity"])
    probe = cast(dict[str, object], identity["runtime_probe"])
    assert probe["python_executable_sha256"]
    assert probe["numpy_version"]
    assert probe["numpy_module_sha256"]
    assert probe["matplotlib_version"]
    assert probe["matplotlib_module_sha256"]
    assert probe["zstd_executable_sha256"]

    validate_runtime_preflight(
        preflight,
        root,
        zstd_executable=str(zstd),
    )


def test_runtime_preflight_rejects_dirty_project(
    runtime_project: tuple[Path, str, Path],
) -> None:
    root, commit, zstd = runtime_project
    dirty = root / "dirty.txt"
    dirty.write_text("dirty\n", encoding="utf-8")
    try:
        with pytest.raises(
            Stage3BMatchedAnalysisRuntimeError,
            match="worktree must be clean",
        ):
            build_runtime_preflight(
                root,
                source_commit=commit,
                captured_at_utc="2026-07-22T12:00:00Z",
                zstd_executable=str(zstd),
            )
    finally:
        dirty.unlink()


def test_runtime_preflight_digest_tamper_is_rejected(
    runtime_project: tuple[Path, str, Path],
) -> None:
    root, _commit, zstd = runtime_project
    preflight = _preflight(runtime_project)
    preflight["captured_at_utc"] = "2026-07-22T12:00:01Z"

    with pytest.raises(
        Stage3BMatchedAnalysisRuntimeError,
        match="preflight digest differs",
    ):
        validate_runtime_preflight(
            preflight,
            root,
            zstd_executable=str(zstd),
        )


def test_runtime_probe_round_trip(
    runtime_project: tuple[Path, str, Path],
) -> None:
    preflight = _preflight(runtime_project)
    identity = cast(dict[str, object], preflight["runtime_identity"])
    record = cast(dict[str, object], identity["runtime_probe"])

    probe = MatchedAnalysisRuntimeProbe.from_record(record)

    assert probe.to_record() == record


def test_authorization_schema_binds_request_preflight_and_runtime(
    runtime_project: tuple[Path, str, Path],
) -> None:
    root, _commit, zstd = runtime_project
    preflight = _preflight(runtime_project)
    request = _request(root)
    authorization = _authorization(preflight, request)

    validate_execution_authorization(
        authorization,
        preflight,
        request,
        root,
        zstd_executable=str(zstd),
    )


def test_authorization_rejects_runtime_identity_tamper(
    runtime_project: tuple[Path, str, Path],
) -> None:
    root, _commit, zstd = runtime_project
    preflight = _preflight(runtime_project)
    request = _request(root)
    authorization = _authorization(preflight, request)
    authorization["runtime_identity_digest"] = "0" * 64
    payload = dict(authorization)
    payload.pop("authorization_digest")
    authorization["authorization_digest"] = canonical_json_digest(payload)

    with pytest.raises(
        Stage3BMatchedAnalysisRuntimeError,
        match="runtime identity differs",
    ):
        validate_execution_authorization(
            authorization,
            preflight,
            request,
            root,
            zstd_executable=str(zstd),
        )


def test_authorization_rejects_missing_operator_acknowledgement(
    runtime_project: tuple[Path, str, Path],
) -> None:
    root, _commit, zstd = runtime_project
    preflight = _preflight(runtime_project)
    request = _request(root)
    authorization = _authorization(preflight, request)
    authorization["operator_acknowledgement"] = "NOT_AUTHORIZED"
    payload = dict(authorization)
    payload.pop("authorization_digest")
    authorization["authorization_digest"] = canonical_json_digest(payload)

    with pytest.raises(
        Stage3BMatchedAnalysisRuntimeError,
        match="operator acknowledgement differs",
    ):
        validate_execution_authorization(
            authorization,
            preflight,
            request,
            root,
            zstd_executable=str(zstd),
        )


def test_frozen_authorization_package_is_absent(
    runtime_project: tuple[Path, str, Path],
) -> None:
    root, _commit, zstd = runtime_project

    with pytest.raises(
        Stage3BMatchedAnalysisRuntimeError,
        match="authorization package is absent",
    ):
        load_frozen_authorization_package(
            root,
            zstd_executable=str(zstd),
        )


def test_executor_fails_before_engine_without_frozen_authorization(
    runtime_project: tuple[Path, str, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, _commit, zstd = runtime_project
    called = False

    def forbidden_engine(*_args: object, **_kwargs: object) -> dict[str, object]:
        nonlocal called
        called = True
        raise AssertionError("engine must remain closed")

    monkeypatch.setattr(runtime, "_generate_engine", forbidden_engine)

    with pytest.raises(
        Stage3BMatchedAnalysisRuntimeError,
        match="authorization package is absent",
    ):
        execute_authorized_matched_analysis(
            root,
            zstd_executable=str(zstd),
        )

    assert called is False


def test_executor_uses_frozen_generated_timestamp_and_sealed_source_kind(
    runtime_project: tuple[Path, str, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, _commit, _zstd = runtime_project
    preflight = _preflight(runtime_project)
    request = _request(root)
    authorization = _authorization(preflight, request)
    observed: dict[str, object] = {}

    def fake_package(
        _project_root: Path,
        *,
        zstd_executable: str,
    ) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
        assert zstd_executable == "fake-zstd"
        return authorization, preflight, request

    def fake_identity(
        _project_root: Path,
        _request: dict[str, object],
    ) -> dict[str, str]:
        return {"fixture": "a" * 64}

    def fake_engine(
        _inputs: object,
        output_root: Path,
        *,
        source_kind: str,
        source_identity: dict[str, object],
        generated_at_utc: str,
    ) -> dict[str, object]:
        observed.update(
            {
                "output_root": output_root,
                "source_kind": source_kind,
                "source_identity": source_identity,
                "generated_at_utc": generated_at_utc,
            }
        )
        output_root.mkdir(parents=True)
        (output_root / "generated.txt").write_text(
            "generated\n",
            encoding="utf-8",
        )
        return {"status": "generated"}

    monkeypatch.setattr(runtime, "load_frozen_authorization_package", fake_package)
    monkeypatch.setattr(runtime, "_source_evidence_identity", fake_identity)
    monkeypatch.setattr(runtime, "_generate_engine", fake_engine)

    _remove_execution_artifacts(root, request, authorization)
    try:
        summary = execute_authorized_matched_analysis(
            root,
            zstd_executable="fake-zstd",
        )

        final_output = _output_root(root, request)
        assert summary == {"status": "generated"}
        assert observed["output_root"] != final_output
        assert (final_output / "generated.txt").is_file()
        assert _receipt_path(root, request).is_file()
        assert observed["source_kind"] == "sealed_evidence"
        assert observed["generated_at_utc"] == "2026-07-22T13:00:00Z"
        source_identity = cast(
            dict[str, object],
            observed["source_identity"],
        )
        assert source_identity["authorization_id"] == (
            RUNTIME_AUTHORIZATION_ID
        )
        assert source_identity["request_id"] == request["request_id"]
    finally:
        _remove_execution_artifacts(root, request, authorization)


def test_write_runtime_preflight_is_atomic_and_refuses_overwrite(
    runtime_project: tuple[Path, str, Path],
    tmp_path: Path,
) -> None:
    preflight = _preflight(runtime_project)
    destination = tmp_path / "runtime-preflight.json"

    write_runtime_preflight(preflight, destination)

    assert json.loads(destination.read_text(encoding="utf-8")) == preflight
    with pytest.raises(
        Stage3BMatchedAnalysisRuntimeError,
        match="output already exists",
    ):
        write_runtime_preflight(preflight, destination)


def test_executor_cli_does_not_accept_authorization_override() -> None:
    script = (PROJECT_ROOT / "scripts/execute_stage3b_matched_analysis.py").read_text(
        encoding="utf-8"
    )

    assert "--authorization" not in script
    assert "--generated-at-utc" not in script
    assert "--zstd-executable" not in script
    assert "load_frozen_authorization_package" not in script


def test_runtime_preflight_does_not_call_analysis_engine(
    runtime_project: tuple[Path, str, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, commit, zstd = runtime_project

    def forbidden_engine(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("preflight must not call the analysis engine")

    monkeypatch.setattr(runtime, "_generate_engine", forbidden_engine)

    preflight = build_runtime_preflight(
        root,
        source_commit=commit,
        captured_at_utc="2026-07-22T12:00:00Z",
        zstd_executable=str(zstd),
    )

    assert preflight["status"] == RUNTIME_PREFLIGHT_STATUS


def test_runtime_preflight_rejects_output_inventory_tamper(
    runtime_project: tuple[Path, str, Path],
) -> None:
    root, _commit, zstd = runtime_project
    preflight = _preflight(runtime_project)
    output = cast(dict[str, object], preflight["output_contract"])
    output["expected_top_level_files"] = ["unexpected.txt"] * 18
    payload = dict(preflight)
    payload.pop("preflight_digest")
    preflight["preflight_digest"] = canonical_json_digest(payload)

    with pytest.raises(
        Stage3BMatchedAnalysisRuntimeError,
        match="output inventory differs",
    ):
        validate_runtime_preflight(
            preflight,
            root,
            zstd_executable=str(zstd),
        )


def test_authorized_execution_requires_main_branch(
    runtime_project: tuple[Path, str, Path],
) -> None:
    root, _commit, zstd = runtime_project
    _run("git", "switch", "-c", "authorization-review", cwd=root)
    try:
        with pytest.raises(
            Stage3BMatchedAnalysisRuntimeError,
            match="only from the main branch",
        ):
            load_frozen_authorization_package(
                root,
                zstd_executable=str(zstd),
            )
    finally:
        _run("git", "switch", "main", cwd=root)


def test_executor_removes_output_when_post_execution_source_check_fails(
    runtime_project: tuple[Path, str, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, _commit, _zstd = runtime_project
    preflight = _preflight(runtime_project)
    request = _request(root)
    authorization = _authorization(preflight, request)
    output = cast(dict[str, object], request["output_contract"])
    output_root = root / cast(str, output["root"])
    identities = iter(
        [
            {"fixture": "a" * 64},
            {"fixture": "b" * 64},
        ]
    )

    def fake_package(
        _project_root: Path,
        *,
        zstd_executable: str,
    ) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
        assert zstd_executable == "fake-zstd"
        return authorization, preflight, request

    def fake_identity(
        _project_root: Path,
        _request: Mapping[str, object],
    ) -> dict[str, str]:
        return next(identities)

    def fake_engine(
        _inputs: object,
        destination: Path,
        *,
        source_kind: str,
        source_identity: Mapping[str, object],
        generated_at_utc: str,
    ) -> dict[str, object]:
        assert source_kind == "sealed_evidence"
        assert source_identity
        assert generated_at_utc == "2026-07-22T13:00:00Z"
        destination.mkdir(parents=True)
        (destination / "invalid.txt").write_text(
            "invalid\n",
            encoding="utf-8",
        )
        return {"status": "generated"}

    monkeypatch.setattr(runtime, "load_frozen_authorization_package", fake_package)
    monkeypatch.setattr(runtime, "_source_evidence_identity", fake_identity)
    monkeypatch.setattr(runtime, "_generate_engine", fake_engine)

    _remove_execution_artifacts(root, request, authorization)
    try:
        with pytest.raises(
            Stage3BMatchedAnalysisRuntimeError,
            match="source identity changed",
        ):
            execute_authorized_matched_analysis(
                root,
                zstd_executable="fake-zstd",
            )

        assert not output_root.exists()
        assert _receipt_path(root, request).is_file()
    finally:
        _remove_execution_artifacts(root, request, authorization)


def test_authorization_rejects_timestamp_before_preflight(
    runtime_project: tuple[Path, str, Path],
) -> None:
    root, _commit, zstd = runtime_project
    preflight = _preflight(runtime_project)
    request = _request(root)
    authorization = _authorization(preflight, request)
    authorization["generated_at_utc"] = "2026-07-22T11:59:59Z"
    payload = dict(authorization)
    payload.pop("authorization_digest")
    authorization["authorization_digest"] = canonical_json_digest(payload)

    with pytest.raises(
        Stage3BMatchedAnalysisRuntimeError,
        match="predates runtime preflight",
    ):
        validate_execution_authorization(
            authorization,
            preflight,
            request,
            root,
            zstd_executable=str(zstd),
        )


def test_registry_rejects_duplicate_entries(tmp_path: Path) -> None:
    package = tmp_path / "package"
    package.mkdir()
    payload = package / "payload.json"
    payload.write_text("{}\n", encoding="utf-8")
    digest = runtime.sha256_file(payload)
    registry = package / "SHA256SUMS"
    registry.write_text(
        f"{digest}  payload.json\n{digest}  payload.json\n",
        encoding="utf-8",
    )

    with pytest.raises(
        Stage3BMatchedAnalysisRuntimeError,
        match="duplicate checksum registry entry",
    ):
        runtime._validate_registry(
            package,
            registry,
            expected_names=frozenset({"payload.json"}),
        )


def test_authorization_inventory_rejects_directory_and_symlink(
    tmp_path: Path,
) -> None:
    package = tmp_path / "package"
    package.mkdir()
    (package / "runtime-preflight.json").write_text(
        "{}\n",
        encoding="utf-8",
    )
    (package / "authorization.json").write_text(
        "{}\n",
        encoding="utf-8",
    )
    (package / "SHA256SUMS").write_text("registry\n", encoding="utf-8")
    extra = package / "extra"
    extra.mkdir()

    with pytest.raises(
        Stage3BMatchedAnalysisRuntimeError,
        match="must be a regular file",
    ):
        runtime._exact_regular_file_inventory(package)

    extra.rmdir()
    target = tmp_path / "outside.json"
    target.write_text("{}\n", encoding="utf-8")
    (package / "runtime-preflight.json").unlink()
    (package / "runtime-preflight.json").symlink_to(target)

    with pytest.raises(
        Stage3BMatchedAnalysisRuntimeError,
        match="must be a regular file",
    ):
        runtime._exact_regular_file_inventory(package)


def test_executor_receipt_blocks_replay_after_output_removal(
    runtime_project: tuple[Path, str, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, _commit, _zstd = runtime_project
    preflight = _preflight(runtime_project)
    request = _request(root)
    authorization = _authorization(preflight, request)
    calls = 0

    def fake_package(
        _project_root: Path,
        *,
        zstd_executable: str,
    ) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
        assert zstd_executable == "fake-zstd"
        return authorization, preflight, request

    def fake_identity(
        _project_root: Path,
        _request: Mapping[str, object],
    ) -> dict[str, str]:
        return {"fixture": "a" * 64}

    def fake_engine(
        _inputs: object,
        destination: Path,
        *,
        source_kind: str,
        source_identity: Mapping[str, object],
        generated_at_utc: str,
    ) -> dict[str, object]:
        nonlocal calls
        calls += 1
        assert source_kind == "sealed_evidence"
        assert source_identity
        assert generated_at_utc == "2026-07-22T13:00:00Z"
        destination.mkdir(parents=True)
        (destination / "generated.txt").write_text(
            "generated\n",
            encoding="utf-8",
        )
        return {"status": "generated"}

    monkeypatch.setattr(runtime, "load_frozen_authorization_package", fake_package)
    monkeypatch.setattr(runtime, "_source_evidence_identity", fake_identity)
    monkeypatch.setattr(runtime, "_generate_engine", fake_engine)

    _remove_execution_artifacts(root, request, authorization)
    try:
        execute_authorized_matched_analysis(
            root,
            zstd_executable="fake-zstd",
        )
        shutil.rmtree(_output_root(root, request))

        with pytest.raises(
            Stage3BMatchedAnalysisRuntimeError,
            match="already claimed",
        ):
            execute_authorized_matched_analysis(
                root,
                zstd_executable="fake-zstd",
            )

        assert calls == 1
    finally:
        _remove_execution_artifacts(root, request, authorization)
