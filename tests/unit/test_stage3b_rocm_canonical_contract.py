from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from torch2pc_thesis.stage3b_authorization import (
    B0_AUTHORIZATION_SCHEMA_VERSION,
    B0_AUTHORIZATION_SCOPE,
    B0_OPERATOR_ACKNOWLEDGEMENT,
    RuntimeProbe,
    capture_lane_preflight,
    freeze_project_environment,
    issue_campaign_authorization,
    validate_campaign_authorization,
    verify_authorization_for_lane,
)
from torch2pc_thesis.stage3b_canonical import plan_authorized_lane
from torch2pc_thesis.stage3b_execution import (
    Stage3BExecutionError,
    generate_manifest,
)
from torch2pc_thesis.stage3b_protocol_contract import (
    B0_CANONICAL_CELL_COUNT,
    B0_CANONICAL_LANES,
    B0_ENGINEERING_CONTROL_LANES,
    B0_PROTOCOL_CONTRACT,
    B0_PROTOCOL_CONTRACT_DIGEST,
    validate_b0_protocol_contract,
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
    return root, _run("git", "rev-parse", "HEAD", cwd=root)


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


def _freeze(
    tmp_path: Path,
) -> tuple[dict[str, object], dict[str, object], str, Path, Path]:
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
    return freeze, manifest, source_commit, torch2pc_dir, output_root


def _preflight(
    freeze: dict[str, object],
    manifest: dict[str, object],
    *,
    torch2pc_dir: Path,
    source_commit: str,
    device: str,
    dtype: str,
    image_digest: str,
    probe: RuntimeProbe,
) -> dict[str, object]:
    return capture_lane_preflight(
        freeze,
        manifest,
        torch2pc_dir=torch2pc_dir,
        source_commit=source_commit,
        device=device,
        dtype=dtype,
        image_digest=image_digest,
        probe=probe,
    )


def _rocm_authorization(
    tmp_path: Path,
    *,
    include_cpu_control: bool = False,
) -> tuple[dict[str, object], dict[str, object], str, Path, Path]:
    freeze, manifest, commit, torch2pc_dir, output_root = _freeze(tmp_path)
    rocm = _preflight(
        freeze,
        manifest,
        torch2pc_dir=torch2pc_dir,
        source_commit=commit,
        device="rocm",
        dtype="float32",
        image_digest=ROCM_IMAGE,
        probe=_rocm_probe(),
    )
    preflights = [rocm]
    if include_cpu_control:
        preflights.insert(
            0,
            _preflight(
                freeze,
                manifest,
                torch2pc_dir=torch2pc_dir,
                source_commit=commit,
                device="cpu",
                dtype="float64",
                image_digest=CPU_IMAGE,
                probe=_cpu_probe(),
            ),
        )
    authorization = issue_campaign_authorization(
        freeze,
        preflights,
        operator_acknowledgement=B0_OPERATOR_ACKNOWLEDGEMENT,
    )
    return authorization, manifest, commit, torch2pc_dir, output_root


def test_machine_readable_contract_has_one_rocm_canonical_lane() -> None:
    validate_b0_protocol_contract(B0_PROTOCOL_CONTRACT)
    assert B0_PROTOCOL_CONTRACT_DIGEST
    assert B0_PROTOCOL_CONTRACT["contract_scope"] == (
        "stage3b_b0_rocm_canonical_v1"
    )
    assert B0_CANONICAL_LANES == (("rocm", "float32"),)
    assert B0_ENGINEERING_CONTROL_LANES == (("cpu", "float64"),)
    assert B0_CANONICAL_CELL_COUNT == 96
    assert B0_PROTOCOL_CONTRACT["execution_count"] == 96
    assert B0_PROTOCOL_CONTRACT["canonical_protocol"] == {
        "warmup_steps": 20,
        "measured_steps": 50,
        "repetitions": 5,
    }


def test_manifest_remains_336_cells_with_96_b0_cells() -> None:
    manifest = generate_manifest()
    cells = manifest["cells"]
    assert isinstance(cells, list)
    assert len(cells) == 336
    assert sum(
        1
        for cell in cells
        if isinstance(cell, dict) and cell.get("candidate_id") == "stage2_baseline"
    ) == 96


def test_freeze_records_rocm_canonical_and_cpu_control_roles(tmp_path: Path) -> None:
    freeze, *_rest = _freeze(tmp_path)
    assert freeze["protocol_contract_digest"] == B0_PROTOCOL_CONTRACT_DIGEST
    assert freeze["canonical_lanes"] == [
        {"device": "rocm", "dtype": "float32"}
    ]
    assert freeze["engineering_control_lanes"] == [
        {"device": "cpu", "dtype": "float64"}
    ]


def test_rocm_preflight_alone_is_sufficient_for_authorization(
    tmp_path: Path,
) -> None:
    authorization, *_rest = _rocm_authorization(tmp_path)
    validate_campaign_authorization(authorization)
    assert authorization["schema_version"] == B0_AUTHORIZATION_SCHEMA_VERSION
    assert authorization["authorization_scope"] == B0_AUTHORIZATION_SCOPE
    assert authorization["canonical_lanes"] == [
        {"device": "rocm", "dtype": "float32"}
    ]
    assert authorization["canonical_execution_count"] == 96
    assert len(authorization["lane_preflights"]) == 1
    assert authorization["engineering_control_preflights"] == []


def test_cpu_preflight_alone_cannot_authorize_campaign(tmp_path: Path) -> None:
    freeze, manifest, commit, torch2pc_dir, _output_root = _freeze(tmp_path)
    cpu = _preflight(
        freeze,
        manifest,
        torch2pc_dir=torch2pc_dir,
        source_commit=commit,
        device="cpu",
        dtype="float64",
        image_digest=CPU_IMAGE,
        probe=_cpu_probe(),
    )
    with pytest.raises(Stage3BExecutionError, match="rocm/float32 canonical"):
        issue_campaign_authorization(
            freeze,
            [cpu],
            operator_acknowledgement=B0_OPERATOR_ACKNOWLEDGEMENT,
        )


def test_optional_cpu_preflight_is_not_a_canonical_lane(tmp_path: Path) -> None:
    authorization, *_rest = _rocm_authorization(
        tmp_path,
        include_cpu_control=True,
    )
    canonical = authorization["lane_preflights"]
    controls = authorization["engineering_control_preflights"]
    assert isinstance(canonical, list)
    assert isinstance(controls, list)
    assert [(item["device"], item["dtype"]) for item in canonical] == [
        ("rocm", "float32")
    ]
    assert [(item["device"], item["dtype"]) for item in controls] == [
        ("cpu", "float64")
    ]


def test_legacy_schema_one_authorization_is_retired(tmp_path: Path) -> None:
    authorization, *_rest = _rocm_authorization(tmp_path)
    authorization["schema_version"] = 1
    with pytest.raises(Stage3BExecutionError, match="retired"):
        validate_campaign_authorization(authorization)


def test_cpu_control_verification_never_permits_canonical_execution(
    tmp_path: Path,
) -> None:
    authorization, manifest, commit, torch2pc_dir, output_root = (
        _rocm_authorization(tmp_path, include_cpu_control=True)
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
    assert result["lane_role"] == "engineering_control"
    assert result["canonical_execution_permitted"] is False
    assert result["required_for_campaign_completion"] is False
    assert result["confirmatory_performance_evidence"] is False


def test_production_canonical_planner_rejects_cpu_before_creating_state(
    tmp_path: Path,
) -> None:
    authorization, manifest, commit, torch2pc_dir, output_root = (
        _rocm_authorization(tmp_path, include_cpu_control=True)
    )
    with pytest.raises(Stage3BExecutionError, match="limited to rocm/float32"):
        plan_authorized_lane(
            authorization,
            manifest,
            output_root=output_root,
            device="cpu",
            dtype="float64",
            torch2pc_dir=torch2pc_dir,
            source_commit=commit,
            image_digest=CPU_IMAGE,
        )
    assert not (output_root / "canonical" / "lanes" / "cpu-float64").exists()
    assert not (output_root / "canonical" / "locks").exists()


def test_rocm_canonical_plan_contains_exactly_96_executions(
    tmp_path: Path,
) -> None:
    authorization, manifest, commit, torch2pc_dir, output_root = (
        _rocm_authorization(tmp_path)
    )
    plan = plan_authorized_lane(
        authorization,
        manifest,
        output_root=output_root,
        device="rocm",
        dtype="float32",
        torch2pc_dir=torch2pc_dir,
        source_commit=commit,
        image_digest=ROCM_IMAGE,
        probe=_rocm_probe(),
    )
    assert len(plan.cells) == 96
    assert len(plan.selected_cell_ids) == 96
    assert plan.device == "rocm"
    assert plan.dtype == "float32"


def test_canonical_cli_rejects_cpu_before_loading_authorization() -> None:
    root = Path(__file__).resolve().parents[2]
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/run_stage3b_b0_campaign.py",
            "--dry-run",
            "--authorization",
            "/tmp/missing-authorization.json",
            "--device",
            "cpu",
            "--dtype",
            "float64",
            "--source-commit",
            "0" * 40,
            "--image-digest",
            CPU_IMAGE,
        ],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 2
    assert "limited to --device rocm --dtype float32" in completed.stderr


def test_adr_records_cpu_oom_and_exclusion_from_evidence() -> None:
    root = Path(__file__).resolve().parents[2]
    adr = (
        root
        / "docs/decisions/ADR-009-stage3b-rocm-canonical-lane_EN.md"
    ).read_text(encoding="utf-8")
    assert "memory-cgroup OOM killer" in adr
    assert "21 completed cells" in adr
    assert "excluded from confirmatory results" in adr
