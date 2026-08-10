from __future__ import annotations

import ast
import json
from dataclasses import replace
from pathlib import Path

import pytest

import torch2pc_thesis.stage3b_qwake_attempt_003_host_invocation_chain as host_chain

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src/torch2pc_thesis/stage3b_qwake_attempt_003_host_invocation_chain.py"
VERIFIER = ROOT / "scripts/verify_stage3b_qwake_attempt_003_host_invocation_chain.py"
PACKAGE = ROOT / "experiments/frozen/stage3b-qwake-attempt-003-host-invocation-chain-authoring-v1"


def _resources() -> host_chain.HostInvocationResources:
    return host_chain.HostInvocationResources.from_mapping(
        {
            "HOST_UID": "1000",
            "HOST_GID": "1000",
            "VIDEO_GID": "44",
            "RENDER_GID": "109",
            "HIP_VISIBLE_DEVICES": "0",
            "CPUSET_GPU": "0-7",
            "MEM_LIMIT": "48g",
            "SHM_SIZE": "8g",
            "TMPFS_SIZE": "4g",
            "OMP_NUM_THREADS": "8",
            "MKL_NUM_THREADS": "8",
            "OPENBLAS_NUM_THREADS": "8",
            "NUMEXPR_NUM_THREADS": "8",
        }
    )


def _inspection_json() -> str:
    return json.dumps(
        [
            {
                "Id": host_chain.IMAGE_DIGEST,
                "RepoDigests": [host_chain.IMAGE_REPO_DIGEST],
                "Architecture": "amd64",
                "Os": "linux",
                "Config": {
                    "Labels": {
                        "org.opencontainers.image.revision": host_chain.SOURCE_COMMIT,
                        "io.torch2pc.base-image": host_chain.BASE_IMAGE,
                    },
                    "Env": [
                        "PYTHONUNBUFFERED=1",
                        f"SOURCE_GIT_COMMIT={host_chain.SOURCE_COMMIT}",
                    ],
                    "WorkingDir": "/workspace",
                    "Entrypoint": list(host_chain.CONTAINER_IMAGE_ENTRYPOINT),
                },
            }
        ]
    )


def test_contract_binds_exact_frozen_identities_and_closed_effects() -> None:
    contract = host_chain.build_attempt_003_host_invocation_contract()
    assert contract.contract_id == host_chain.HOST_INVOCATION_CONTRACT_ID
    assert contract.status == host_chain.HOST_INVOCATION_STATUS
    assert contract.freeze_sha256 == host_chain.FREEZE_SHA256
    assert contract.authorization_sha256 == host_chain.AUTHORIZATION_SHA256
    assert contract.authorization_action_phrase == host_chain.AUTHORIZATION_ACTION_PHRASE
    assert contract.source_commit == host_chain.SOURCE_COMMIT
    assert contract.torch2pc_commit == host_chain.TORCH2PC_COMMIT
    assert contract.image_digest == host_chain.IMAGE_DIGEST
    assert contract.image_repo_digest == host_chain.IMAGE_REPO_DIGEST
    assert contract.host_command_constructor_authored is True
    assert contract.host_command_materialized is False
    assert contract.host_process_spawner_present is False
    assert contract.docker_run_implemented is False
    assert contract.runtime_execution_permitted is False
    assert contract.authorization_consumed is False
    assert contract.attempt_started is False
    assert contract.execution_lease_materialized is False
    assert contract.runtime_execution_performed is False


def test_contract_round_trip_is_canonical(tmp_path: Path) -> None:
    contract = host_chain.build_attempt_003_host_invocation_contract()
    path = tmp_path / "contract.json"
    path.write_text(contract.canonical_json(), encoding="utf-8")
    assert host_chain.load_attempt_003_host_invocation_contract(path) == contract


def test_contract_rejects_open_execution_surface() -> None:
    contract = host_chain.build_attempt_003_host_invocation_contract()
    with pytest.raises(
        host_chain.QWakeAttempt003HostInvocationChainError,
        match="runtime_execution_permitted",
    ):
        replace(contract, runtime_execution_permitted=True).require()
    with pytest.raises(
        host_chain.QWakeAttempt003HostInvocationChainError,
        match="contract digest differs",
    ):
        replace(contract, contract_sha256="sha256:" + "0" * 64).require()


def test_host_resource_validation_fails_closed() -> None:
    resources = _resources()
    assert resources.hip_visible_devices == "0"
    bad = dict(resources.as_host_mapping())
    bad["OMP_NUM_THREADS"] = "0"
    with pytest.raises(
        host_chain.QWakeAttempt003HostInvocationChainError,
        match="thread host resource differs",
    ):
        host_chain.HostInvocationResources.from_mapping(bad)


def test_local_image_inspection_binds_exact_digest_and_source() -> None:
    contract = host_chain.build_attempt_003_host_invocation_contract()
    inspection = host_chain.parse_attempt_003_local_image_inspection(
        _inspection_json(),
        contract,
    )
    assert inspection.image_id == host_chain.IMAGE_DIGEST
    assert host_chain.IMAGE_REPO_DIGEST in inspection.repo_digests
    assert inspection.source_revision == host_chain.SOURCE_COMMIT
    assert inspection.base_image == host_chain.BASE_IMAGE


def test_materialization_constructs_exact_nonexecuting_docker_argv(
    tmp_path: Path,
) -> None:
    for relative in ("experiments/frozen", "external/Torch2PC", "results"):
        (tmp_path / relative).mkdir(parents=True, exist_ok=True)
    contract = host_chain.build_attempt_003_host_invocation_contract()
    inspection = host_chain.parse_attempt_003_local_image_inspection(
        _inspection_json(),
        contract,
    )
    invocation = host_chain.materialize_attempt_003_host_invocation(
        tmp_path,
        contract,
        inspection,
        _resources(),
        claimed_at_utc="2026-08-09T22:00:00Z",
        lease_acknowledgement=host_chain.LEASE_ACKNOWLEDGEMENT,
    )
    assert invocation.argv[:2] == ("docker", "run")
    assert "--network" in invocation.argv
    assert "none" in invocation.argv
    assert "--read-only" in invocation.argv
    assert "--cap-drop" in invocation.argv
    assert "ALL" in invocation.argv
    assert host_chain.IMAGE_REPO_DIGEST in invocation.argv
    assert "/workspace/scripts/run_stage3b_qwake_attempt_003_authorized_runtime.py" in invocation.argv
    volumes = [
        invocation.argv[index + 1]
        for index, value in enumerate(invocation.argv[:-1])
        if value == "--volume"
    ]
    assert len(volumes) == 3
    assert any(value.endswith(":/workspace/experiments/frozen:ro") for value in volumes)
    assert any(value.endswith(":/workspace/external/Torch2PC:ro") for value in volumes)
    assert any(value.endswith(":/workspace/results:rw") for value in volumes)
    assert all("/workspace/data" not in value for value in invocation.argv)
    assert invocation.subprocess_spawned is False
    assert invocation.container_created is False
    assert invocation.authorization_consumed is False
    assert invocation.execution_lease_created is False
    assert invocation.runtime_execution_performed is False


def test_materialization_requires_exact_lease_acknowledgement(tmp_path: Path) -> None:
    for relative in ("experiments/frozen", "external/Torch2PC", "results"):
        (tmp_path / relative).mkdir(parents=True, exist_ok=True)
    contract = host_chain.build_attempt_003_host_invocation_contract()
    inspection = host_chain.parse_attempt_003_local_image_inspection(
        _inspection_json(),
        contract,
    )
    with pytest.raises(
        host_chain.QWakeAttempt003HostInvocationChainError,
        match="lease acknowledgement differs",
    ):
        host_chain.materialize_attempt_003_host_invocation(
            tmp_path,
            contract,
            inspection,
            _resources(),
            claimed_at_utc="2026-08-09T22:00:00Z",
            lease_acknowledgement="WRONG",
        )


def test_authoring_module_and_verifier_have_no_process_spawner() -> None:
    for path in (MODULE, VERIFIER):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(alias.name != "subprocess" for alias in node.names)
            if isinstance(node, ast.ImportFrom):
                assert node.module != "subprocess"
        assert "Popen(" not in source
        assert "docker run" not in source.casefold()


def test_authoring_package_has_exact_contract() -> None:
    contract_path = PACKAGE / "contract.json"
    assert contract_path.is_file()
    observed = host_chain.load_attempt_003_host_invocation_contract(contract_path)
    assert observed == host_chain.build_attempt_003_host_invocation_contract()
