from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import cast

import pytest

from torch2pc_thesis.stage3b_authorization import (
    B0_OPERATOR_ACKNOWLEDGEMENT,
    RuntimeProbe,
    capture_lane_preflight,
    freeze_project_environment,
    issue_campaign_authorization,
    validate_campaign_authorization,
    validate_lane_preflight,
    validate_project_freeze,
    verify_authorization_for_lane,
)
from torch2pc_thesis.stage3b_execution import (
    Stage3BExecutionError,
    generate_manifest,
)

CPU_IMAGE = "sha256:" + "1" * 64
ROCM_IMAGE = "sha256:" + "2" * 64


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
    (root / "README.md").write_text("stage3b\n", encoding="utf-8")
    _run("git", "add", "README.md", cwd=root)
    _run("git", "commit", "-m", "test baseline", cwd=root)
    commit = _run("git", "rev-parse", "HEAD", cwd=root)
    return root, commit


def _torch2pc(tmp_path: Path) -> Path:
    root = tmp_path / "Torch2PC"
    root.mkdir()
    (root / "TorchSeq2PC.py").write_text(
        "# frozen Torch2PC test source\n",
        encoding="utf-8",
    )
    return root


def _cpu_probe() -> RuntimeProbe:
    return RuntimeProbe(
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


def _rocm_probe() -> RuntimeProbe:
    return RuntimeProbe(
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


def _freeze(tmp_path: Path) -> tuple[dict[str, object], dict[str, object], Path, str, Path, Path]:
    manifest = generate_manifest()
    project_root, source_commit = _project_repo(tmp_path)
    torch2pc_dir = _torch2pc(tmp_path)
    output_root = tmp_path / "authorized-output"
    freeze = freeze_project_environment(
        manifest,
        project_root=project_root,
        torch2pc_dir=torch2pc_dir,
        output_root=output_root,
        source_commit=source_commit,
        minimum_free_bytes=1,
    )
    return freeze, manifest, project_root, source_commit, torch2pc_dir, output_root

def _preflight(
    freeze: dict[str, object],
    *,
    device: str,
    dtype: str,
    image_digest: str,
    probe: RuntimeProbe,
) -> dict[str, object]:
    return capture_lane_preflight(
        freeze,
        generate_manifest(),
        torch2pc_dir=Path(str(freeze["torch2pc_path"])),
        source_commit=str(freeze["project_source_commit"]),
        device=device,
        dtype=dtype,
        image_digest=image_digest,
        probe=probe,
    )


def _authorization(tmp_path: Path) -> tuple[
    dict[str, object],
    dict[str, object],
    str,
    Path,
    Path,
]:
    freeze, manifest, _project, commit, torch2pc_dir, output_root = _freeze(tmp_path)
    cpu = _preflight(
        freeze,
        device="cpu",
        dtype="float64",
        image_digest=CPU_IMAGE,
        probe=_cpu_probe(),
    )
    rocm = _preflight(
        freeze,
        device="rocm",
        dtype="float32",
        image_digest=ROCM_IMAGE,
        probe=_rocm_probe(),
    )
    authorization = issue_campaign_authorization(
        freeze,
        [cpu, rocm],
        operator_acknowledgement=B0_OPERATOR_ACKNOWLEDGEMENT,
    )
    return authorization, manifest, commit, torch2pc_dir, output_root


def test_freeze_project_records_canonical_non_evidence_contract(tmp_path: Path) -> None:
    freeze, _manifest, _project, commit, _torch2pc_dir, output_root = _freeze(
        tmp_path
    )

    validate_project_freeze(freeze)
    assert freeze["project_source_commit"] == commit
    assert freeze["b0_cell_count"] == 96
    assert freeze["canonical_protocol"] == {
        "warmup_steps": 20,
        "measured_steps": 50,
        "repetitions": 5,
    }
    assert freeze["output_root"] == str(output_root.resolve())
    assert freeze["evidence"] is False
    assert freeze["full_campaign_complete"] is False
    assert freeze["test_dataset_access"] is False


def test_freeze_rejects_dirty_project(tmp_path: Path) -> None:
    manifest = generate_manifest()
    project_root, commit = _project_repo(tmp_path)
    (project_root / "dirty.txt").write_text("dirty\n", encoding="utf-8")

    with pytest.raises(Stage3BExecutionError, match="worktree must be clean"):
        freeze_project_environment(
            manifest,
            project_root=project_root,
            torch2pc_dir=_torch2pc(tmp_path),
            output_root=tmp_path / "output",
            source_commit=commit,
            minimum_free_bytes=1,
        )


def test_freeze_rejects_wrong_project_commit(tmp_path: Path) -> None:
    manifest = generate_manifest()
    project_root, _commit = _project_repo(tmp_path)

    with pytest.raises(Stage3BExecutionError, match="project HEAD differs"):
        freeze_project_environment(
            manifest,
            project_root=project_root,
            torch2pc_dir=_torch2pc(tmp_path),
            output_root=tmp_path / "output",
            source_commit="0" * 40,
            minimum_free_bytes=1,
        )


def test_freeze_rejects_output_outside_tmp(tmp_path: Path) -> None:
    manifest = generate_manifest()
    project_root, commit = _project_repo(tmp_path)

    with pytest.raises(Stage3BExecutionError, match="under /tmp"):
        freeze_project_environment(
            manifest,
            project_root=project_root,
            torch2pc_dir=_torch2pc(tmp_path),
            output_root=Path("/home/stage3b-authorization-invalid"),
            source_commit=commit,
            minimum_free_bytes=1,
        )


def test_freeze_rejects_insufficient_space(tmp_path: Path) -> None:
    manifest = generate_manifest()
    project_root, commit = _project_repo(tmp_path)

    with pytest.raises(Stage3BExecutionError, match="insufficient free space"):
        freeze_project_environment(
            manifest,
            project_root=project_root,
            torch2pc_dir=_torch2pc(tmp_path),
            output_root=tmp_path / "output",
            source_commit=commit,
            minimum_free_bytes=10**30,
        )


def test_freeze_digest_detects_tampering(tmp_path: Path) -> None:
    freeze, *_rest = _freeze(tmp_path)
    freeze["manifest_digest"] = "f" * 64

    with pytest.raises(Stage3BExecutionError, match="freeze digest"):
        validate_project_freeze(freeze)


def test_cpu_lane_preflight_records_exact_runtime(tmp_path: Path) -> None:
    freeze, *_rest = _freeze(tmp_path)
    preflight = _preflight(
        freeze,
        device="cpu",
        dtype="float64",
        image_digest=CPU_IMAGE,
        probe=_cpu_probe(),
    )

    validate_lane_preflight(preflight)
    assert preflight["device"] == "cpu"
    assert preflight["dtype"] == "float64"
    assert preflight["image_digest"] == CPU_IMAGE
    assert cast(dict[str, object], preflight["runtime"])["device_name"] == "cpu"


def test_rocm_lane_preflight_requires_hip_device(tmp_path: Path) -> None:
    freeze, *_rest = _freeze(tmp_path)

    with pytest.raises(Stage3BExecutionError, match="available HIP device"):
        _preflight(
            freeze,
            device="rocm",
            dtype="float32",
            image_digest=ROCM_IMAGE,
            probe=_cpu_probe(),
        )


def test_lane_preflight_rejects_non_digest_image_identifier(tmp_path: Path) -> None:
    freeze, *_rest = _freeze(tmp_path)

    with pytest.raises(Stage3BExecutionError, match="sha256"):
        _preflight(
            freeze,
            device="cpu",
            dtype="float64",
            image_digest="control-cpu:latest",
            probe=_cpu_probe(),
        )


def test_emergency_stop_blocks_lane_preflight(tmp_path: Path) -> None:
    freeze, *_rest = _freeze(tmp_path)
    Path(str(freeze["emergency_stop_path"])).touch()

    with pytest.raises(Stage3BExecutionError, match="emergency stop is active"):
        _preflight(
            freeze,
            device="cpu",
            dtype="float64",
            image_digest=CPU_IMAGE,
            probe=_cpu_probe(),
        )


def test_authorization_requires_exact_operator_acknowledgement(tmp_path: Path) -> None:
    freeze, *_rest = _freeze(tmp_path)
    cpu = _preflight(
        freeze,
        device="cpu",
        dtype="float64",
        image_digest=CPU_IMAGE,
        probe=_cpu_probe(),
    )
    rocm = _preflight(
        freeze,
        device="rocm",
        dtype="float32",
        image_digest=ROCM_IMAGE,
        probe=_rocm_probe(),
    )

    with pytest.raises(Stage3BExecutionError, match="acknowledgement"):
        issue_campaign_authorization(
            freeze,
            [cpu, rocm],
            operator_acknowledgement="yes",
        )


def test_authorization_requires_both_distinct_lanes(tmp_path: Path) -> None:
    freeze, *_rest = _freeze(tmp_path)
    cpu = _preflight(
        freeze,
        device="cpu",
        dtype="float64",
        image_digest=CPU_IMAGE,
        probe=_cpu_probe(),
    )

    with pytest.raises(Stage3BExecutionError, match="duplicate lane"):
        issue_campaign_authorization(
            freeze,
            [cpu, dict(cpu)],
            operator_acknowledgement=B0_OPERATOR_ACKNOWLEDGEMENT,
        )


def test_authorization_envelope_is_tamper_evident(tmp_path: Path) -> None:
    authorization, *_rest = _authorization(tmp_path)
    validate_campaign_authorization(authorization)

    authorization["authorized_cell_count"] = 95
    with pytest.raises(Stage3BExecutionError, match="cell count differs"):
        validate_campaign_authorization(authorization)


def test_authorization_remains_non_evidence_until_completion(tmp_path: Path) -> None:
    authorization, *_rest = _authorization(tmp_path)

    assert authorization["execution_permitted"] is True
    assert authorization["evidence"] is False
    assert authorization["full_campaign_complete"] is False
    assert authorization["results_publication_permitted"] is False
    assert authorization["test_dataset_access"] is False


def test_runtime_lane_verification_accepts_exact_cpu_fingerprint(tmp_path: Path) -> None:
    authorization, manifest, commit, torch2pc_dir, output_root = _authorization(
        tmp_path
    )

    result = verify_authorization_for_lane(
        authorization,
        manifest,
        torch2pc_dir=torch2pc_dir,
        output_root=output_root,
        source_commit=commit,
        device="cpu",
        dtype="float64",
        image_digest=CPU_IMAGE,
        probe=_cpu_probe(),
    )

    assert result["authorization_verified"] is True
    assert result["execution_permitted"] is True
    assert result["evidence"] is False
    assert result["full_campaign_complete"] is False


def test_runtime_lane_verification_rejects_image_drift(tmp_path: Path) -> None:
    authorization, manifest, commit, torch2pc_dir, output_root = _authorization(
        tmp_path
    )

    with pytest.raises(Stage3BExecutionError, match="lane fingerprint differs"):
        verify_authorization_for_lane(
            authorization,
            manifest,
            torch2pc_dir=torch2pc_dir,
            output_root=output_root,
            source_commit=commit,
            device="cpu",
            dtype="float64",
            image_digest="sha256:" + "3" * 64,
            probe=_cpu_probe(),
        )


def test_runtime_lane_verification_rejects_source_commit_drift(tmp_path: Path) -> None:
    authorization, manifest, _commit, torch2pc_dir, output_root = _authorization(
        tmp_path
    )

    with pytest.raises(Stage3BExecutionError, match="source commit differs"):
        verify_authorization_for_lane(
            authorization,
            manifest,
            torch2pc_dir=torch2pc_dir,
            output_root=output_root,
            source_commit="f" * 40,
            device="cpu",
            dtype="float64",
            image_digest=CPU_IMAGE,
            probe=_cpu_probe(),
        )


def test_authorization_round_trips_as_json(tmp_path: Path) -> None:
    authorization, *_rest = _authorization(tmp_path)
    path = tmp_path / "authorization.json"
    path.write_text(
        json.dumps(authorization, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    loaded = json.loads(path.read_text(encoding="utf-8"))

    validate_campaign_authorization(loaded)
    assert loaded["authorization_token"] == authorization["authorization_token"]
