from __future__ import annotations

import hashlib
import json
import os
import subprocess
from copy import deepcopy
from pathlib import Path
from typing import cast

import pytest

from torch2pc_thesis.stage3b_execution import (
    Stage3BExecutionError,
    generate_manifest,
)
from torch2pc_thesis.stage3b_matched_authorization import (
    MATCHED_AUTHORIZED_CELL_COUNT,
    MATCHED_DISPATCH_SYMBOLS,
    MATCHED_OPERATOR_ACKNOWLEDGEMENT,
    MatchedRuntimeProbe,
    capture_matched_lane_preflight,
    freeze_matched_project_environment,
    issue_matched_campaign_authorization,
    validate_matched_campaign_authorization,
    validate_matched_lane_preflight,
    validate_matched_project_freeze,
    verify_matched_authorization_for_lane,
)
from torch2pc_thesis.stage3b_matched_profiling import (
    MATCHED_PROFILING_CANDIDATES,
    load_json_object,
    validate_matched_request,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MATCHED_MANIFEST_PATH = (
    PROJECT_ROOT
    / "experiments/planned/STAGE3B-B1-B2-MATCHED-PROFILING-MANIFEST.json"
)
MATCHED_REQUEST_PATH = (
    PROJECT_ROOT
    / "experiments/planned/STAGE3B-B1-B2-MATCHED-PROFILING-REQUEST.json"
)
ROCM_IMAGE = "sha256:" + "2" * 64


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run(*args: str, cwd: Path) -> str:
    completed = subprocess.run(
        list(args),
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _project_repo(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "project"
    root.mkdir()
    _run("git", "init", cwd=root)
    _run("git", "config", "user.email", "test@example.com", cwd=root)
    _run("git", "config", "user.name", "Stage3B Test", cwd=root)
    (root / "README.md").write_text("matched stage3b\n", encoding="utf-8")
    _run("git", "add", "README.md", cwd=root)
    _run("git", "commit", "-m", "test baseline", cwd=root)
    return root, _run("git", "rev-parse", "HEAD", cwd=root)


def _torch2pc(tmp_path: Path) -> Path:
    root = tmp_path / "Torch2PC"
    root.mkdir()
    (root / "TorchSeq2PC.py").write_text(
        "# frozen Torch2PC test source\n",
        encoding="utf-8",
    )
    return root


def _rocm_probe() -> MatchedRuntimeProbe:
    return MatchedRuntimeProbe(
        python_version="3.12.13",
        pytorch_version="2.7.1+rocm6.3",
        hip_version="6.3.42131",
        cuda_available=True,
        device_count=1,
        device_name="AMD Radeon RX 7700 XT",
        platform="Linux-test",
        machine="x86_64",
        effective_uid=os.geteuid(),
        effective_gid=os.getegid(),
    )


def _opening_inputs(
    tmp_path: Path,
) -> tuple[dict[str, object], dict[str, object], dict[str, object], Path]:
    matched_manifest = load_json_object(MATCHED_MANIFEST_PATH)
    request = deepcopy(load_json_object(MATCHED_REQUEST_PATH))
    base_manifest = generate_manifest()
    assert base_manifest["manifest_digest"] == matched_manifest[
        "source_manifest_digest"
    ]

    base_path = tmp_path / "STAGE3B-EXECUTION-MANIFEST.json"
    base_path.write_text(
        json.dumps(base_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    source_artifacts = cast(dict[str, object], request["source_artifacts"])
    execution_manifest = cast(
        dict[str, object], source_artifacts["execution_manifest"]
    )
    execution_manifest["sha256"] = _sha256_file(base_path)
    payload = dict(request)
    payload.pop("request_digest")
    request["request_digest"] = _digest(payload)
    validate_matched_request(request)
    return matched_manifest, request, base_manifest, base_path


def _freeze(
    tmp_path: Path,
) -> tuple[
    dict[str, object],
    dict[str, object],
    dict[str, object],
    dict[str, object],
    Path,
    Path,
    str,
    Path,
    Path,
]:
    matched_manifest, request, base_manifest, base_path = _opening_inputs(tmp_path)
    project_root, source_commit = _project_repo(tmp_path)
    torch2pc_dir = _torch2pc(tmp_path)
    output_root = tmp_path / "matched-authorization-output"
    freeze = freeze_matched_project_environment(
        matched_manifest,
        request,
        base_manifest,
        base_manifest_path=base_path,
        project_root=project_root,
        torch2pc_dir=torch2pc_dir,
        output_root=output_root,
        source_commit=source_commit,
        minimum_free_bytes=1,
    )
    return (
        freeze,
        matched_manifest,
        request,
        base_manifest,
        base_path,
        project_root,
        source_commit,
        torch2pc_dir,
        output_root,
    )


def _preflight(
    freeze: dict[str, object],
    matched_manifest: dict[str, object],
    request: dict[str, object],
    base_manifest: dict[str, object],
    base_path: Path,
    project_root: Path,
    source_commit: str,
    torch2pc_dir: Path,
) -> dict[str, object]:
    return cast(
        dict[str, object],
        capture_matched_lane_preflight(
        freeze,
        matched_manifest,
        request,
        base_manifest,
        base_manifest_path=base_path,
        project_root=project_root,
        torch2pc_dir=torch2pc_dir,
        source_commit=source_commit,
        image_digest=ROCM_IMAGE,
        probe=_rocm_probe(),
        dispatch_symbols=MATCHED_DISPATCH_SYMBOLS,
        ),
    )


def _authorization(
    tmp_path: Path,
) -> tuple[
    dict[str, object],
    dict[str, object],
    dict[str, object],
    dict[str, object],
    Path,
    Path,
    str,
    Path,
    Path,
]:
    (
        freeze,
        matched_manifest,
        request,
        base_manifest,
        base_path,
        project_root,
        source_commit,
        torch2pc_dir,
        output_root,
    ) = _freeze(tmp_path)
    preflight = _preflight(
        freeze,
        matched_manifest,
        request,
        base_manifest,
        base_path,
        project_root,
        source_commit,
        torch2pc_dir,
    )
    authorization = issue_matched_campaign_authorization(
        freeze,
        preflight,
        operator_acknowledgement=MATCHED_OPERATOR_ACKNOWLEDGEMENT,
        execution_runner_ready=True,
    )
    return (
        authorization,
        matched_manifest,
        request,
        base_manifest,
        base_path,
        project_root,
        source_commit,
        torch2pc_dir,
        output_root,
    )


def test_freeze_records_exact_matched_non_evidence_contract(tmp_path: Path) -> None:
    freeze, *_rest = _freeze(tmp_path)

    validate_matched_project_freeze(freeze)
    assert freeze["authorized_cell_count"] == MATCHED_AUTHORIZED_CELL_COUNT
    assert freeze["canonical_execution_count"] == 288
    assert freeze["admitted_candidates"] == list(MATCHED_PROFILING_CANDIDATES)
    assert freeze["canonical_lanes"] == [
        {"device": "rocm", "dtype": "float32"}
    ]
    assert freeze["evidence"] is False
    assert freeze["results_publication_permitted"] is False
    assert freeze["test_dataset_access"] is False


def test_freeze_rejects_dirty_project(tmp_path: Path) -> None:
    matched_manifest, request, base_manifest, base_path = _opening_inputs(tmp_path)
    project_root, source_commit = _project_repo(tmp_path)
    (project_root / "dirty.txt").write_text("dirty\n", encoding="utf-8")

    with pytest.raises(Stage3BExecutionError, match="worktree must be clean"):
        freeze_matched_project_environment(
            matched_manifest,
            request,
            base_manifest,
            base_manifest_path=base_path,
            project_root=project_root,
            torch2pc_dir=_torch2pc(tmp_path),
            output_root=tmp_path / "output",
            source_commit=source_commit,
            minimum_free_bytes=1,
        )


def test_freeze_rejects_execution_manifest_file_drift(tmp_path: Path) -> None:
    matched_manifest, request, base_manifest, base_path = _opening_inputs(tmp_path)
    base_path.write_text("{}\n", encoding="utf-8")
    project_root, source_commit = _project_repo(tmp_path)

    with pytest.raises(Stage3BExecutionError, match="sha256 differs"):
        freeze_matched_project_environment(
            matched_manifest,
            request,
            base_manifest,
            base_manifest_path=base_path,
            project_root=project_root,
            torch2pc_dir=_torch2pc(tmp_path),
            output_root=tmp_path / "output",
            source_commit=source_commit,
            minimum_free_bytes=1,
        )


def test_preflight_records_rocm_and_candidate_dispatch(tmp_path: Path) -> None:
    (
        freeze,
        matched_manifest,
        request,
        base_manifest,
        base_path,
        project_root,
        source_commit,
        torch2pc_dir,
        _output_root,
    ) = _freeze(tmp_path)

    preflight = _preflight(
        freeze,
        matched_manifest,
        request,
        base_manifest,
        base_path,
        project_root,
        source_commit,
        torch2pc_dir,
    )

    validate_matched_lane_preflight(preflight)
    assert preflight["device"] == "rocm"
    assert preflight["dtype"] == "float32"
    assert preflight["dispatch_verified_symbols"] == list(
        MATCHED_DISPATCH_SYMBOLS
    )
    assert preflight["evidence"] is False


def test_preflight_requires_available_hip_device(tmp_path: Path) -> None:
    (
        freeze,
        matched_manifest,
        request,
        base_manifest,
        base_path,
        project_root,
        source_commit,
        torch2pc_dir,
        _output_root,
    ) = _freeze(tmp_path)
    invalid_probe = MatchedRuntimeProbe(
        python_version="3.12.13",
        pytorch_version="2.7.1+cpu",
        hip_version=None,
        cuda_available=False,
        device_count=0,
        device_name="cpu",
        platform="Linux-test",
        machine="x86_64",
        effective_uid=os.geteuid(),
        effective_gid=os.getegid(),
    )

    with pytest.raises(Stage3BExecutionError, match="available HIP device"):
        capture_matched_lane_preflight(
            freeze,
            matched_manifest,
            request,
            base_manifest,
            base_manifest_path=base_path,
            project_root=project_root,
            torch2pc_dir=torch2pc_dir,
            source_commit=source_commit,
            image_digest=ROCM_IMAGE,
            probe=invalid_probe,
            dispatch_symbols=MATCHED_DISPATCH_SYMBOLS,
        )


def test_authorization_requires_exact_operator_acknowledgement(
    tmp_path: Path,
) -> None:
    (
        freeze,
        matched_manifest,
        request,
        base_manifest,
        base_path,
        project_root,
        source_commit,
        torch2pc_dir,
        _output_root,
    ) = _freeze(tmp_path)
    preflight = _preflight(
        freeze,
        matched_manifest,
        request,
        base_manifest,
        base_path,
        project_root,
        source_commit,
        torch2pc_dir,
    )

    with pytest.raises(Stage3BExecutionError, match="acknowledgement"):
        issue_matched_campaign_authorization(
            freeze,
            preflight,
            operator_acknowledgement="yes",
            execution_runner_ready=True,
        )


def test_authorization_uses_ready_executable_runner_by_default(
    tmp_path: Path,
) -> None:
    (
        freeze,
        matched_manifest,
        request,
        base_manifest,
        base_path,
        project_root,
        source_commit,
        torch2pc_dir,
        _output_root,
    ) = _freeze(tmp_path)
    preflight = _preflight(
        freeze,
        matched_manifest,
        request,
        base_manifest,
        base_path,
        project_root,
        source_commit,
        torch2pc_dir,
    )

    authorization = issue_matched_campaign_authorization(
        freeze,
        preflight,
        operator_acknowledgement=MATCHED_OPERATOR_ACKNOWLEDGEMENT,
    )

    assert authorization["runtime_authorization"] == "issued"
    assert authorization["execution_permitted"] is True


def test_authorization_can_still_be_blocked_by_explicit_readiness_override(
    tmp_path: Path,
) -> None:
    (
        freeze,
        matched_manifest,
        request,
        base_manifest,
        base_path,
        project_root,
        source_commit,
        torch2pc_dir,
        _output_root,
    ) = _freeze(tmp_path)
    preflight = _preflight(
        freeze,
        matched_manifest,
        request,
        base_manifest,
        base_path,
        project_root,
        source_commit,
        torch2pc_dir,
    )

    with pytest.raises(Stage3BExecutionError, match="runner is not ready"):
        issue_matched_campaign_authorization(
            freeze,
            preflight,
            operator_acknowledgement=MATCHED_OPERATOR_ACKNOWLEDGEMENT,
            execution_runner_ready=False,
        )


def test_authorization_is_tamper_evident_and_non_evidence(tmp_path: Path) -> None:
    authorization, *_rest = _authorization(tmp_path)

    validate_matched_campaign_authorization(authorization)
    assert authorization["runtime_authorization"] == "issued"
    assert authorization["measurements_allowed"] is True
    assert authorization["execution_permitted"] is True
    assert authorization["authorized_cell_count"] == 288
    assert authorization["evidence"] is False
    assert authorization["full_stage3b_campaign_complete"] is False
    assert authorization["results_publication_permitted"] is False
    assert authorization["test_dataset_access"] is False

    authorization["authorized_cell_count"] = 287
    with pytest.raises(Stage3BExecutionError, match="cell count must remain 288"):
        validate_matched_campaign_authorization(authorization)


def test_runtime_verification_accepts_exact_fingerprint(tmp_path: Path) -> None:
    (
        authorization,
        matched_manifest,
        request,
        base_manifest,
        base_path,
        project_root,
        source_commit,
        torch2pc_dir,
        output_root,
    ) = _authorization(tmp_path)

    result = verify_matched_authorization_for_lane(
        authorization,
        matched_manifest,
        request,
        base_manifest,
        base_manifest_path=base_path,
        project_root=project_root,
        torch2pc_dir=torch2pc_dir,
        output_root=output_root,
        source_commit=source_commit,
        image_digest=ROCM_IMAGE,
        probe=_rocm_probe(),
        dispatch_symbols=MATCHED_DISPATCH_SYMBOLS,
    )

    assert result["authorization_verified"] is True
    assert result["measurements_allowed"] is True
    assert result["execution_permitted"] is True
    assert result["evidence"] is False


def test_runtime_verification_rejects_image_drift(tmp_path: Path) -> None:
    (
        authorization,
        matched_manifest,
        request,
        base_manifest,
        base_path,
        project_root,
        source_commit,
        torch2pc_dir,
        output_root,
    ) = _authorization(tmp_path)

    with pytest.raises(Stage3BExecutionError, match="fingerprint differs"):
        verify_matched_authorization_for_lane(
            authorization,
            matched_manifest,
            request,
            base_manifest,
            base_manifest_path=base_path,
            project_root=project_root,
            torch2pc_dir=torch2pc_dir,
            output_root=output_root,
            source_commit=source_commit,
            image_digest="sha256:" + "3" * 64,
            probe=_rocm_probe(),
            dispatch_symbols=MATCHED_DISPATCH_SYMBOLS,
        )
