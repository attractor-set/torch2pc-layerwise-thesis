from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from torch2pc_thesis import (
    stage3b_qwake_lc4_attempt_002_host_invocation_chain as chain_module,
)
from torch2pc_thesis.stage3b_qwake_lc4_attempt_002_contract import (
    ATTEMPT_002_AUTHORIZATION_ROOT,
    ATTEMPT_002_INVOCATION_ACKNOWLEDGEMENT,
    ATTEMPT_002_LEASE_ACKNOWLEDGEMENT,
)
from torch2pc_thesis.stage3b_qwake_lc4_attempt_002_host_invocation_chain import (
    EXPECTED_IMAGE_DIGEST,
    EXPECTED_IMAGE_REPO_DIGEST,
    Attempt002HostInvocationChainError,
    HostInvocationResources,
    build_attempt_002_host_invocation_chain_state,
    build_attempt_002_host_invocation_contract,
    load_attempt_002_host_execution_freeze,
    load_attempt_002_host_image_identity,
    materialize_attempt_002_host_invocation,
    parse_attempt_002_local_image_inspection,
)

ROOT = Path(__file__).resolve().parents[2]
CAPTURE_INSPECT = (
    ROOT
    / "experiments/frozen/"
    "stage3b-qwake-lc4-e-attempt-002-execution-freeze-v1/"
    "image-identity.json"
)


def _inspect_payload() -> str:
    identity = json.loads(CAPTURE_INSPECT.read_text(encoding="utf-8"))
    payload = [
        {
            "Id": identity["image_digest"],
            "RepoTags": [identity["image_tag"]],
            "RepoDigests": [identity["image_repo_digest"]],
            "Architecture": identity["architecture"],
            "Os": identity["os"],
            "Size": identity["image_size_bytes"],
            "Config": {
                "Labels": {
                    "org.opencontainers.image.revision": identity["source_commit"],
                    "io.torch2pc.base-image": identity["base_image"],
                },
                "Env": [
                    f"SOURCE_GIT_COMMIT={identity['source_commit']}",
                    f"EXPERIMENT_IMAGE_DIGEST={identity['image_digest']}",
                ],
                "WorkingDir": identity["container_workdir"],
                "Entrypoint": identity["container_entrypoint"],
            },
        }
    ]
    return json.dumps(payload)


def _resources() -> HostInvocationResources:
    return HostInvocationResources.from_mapping(
        {
            "HOST_UID": "1000",
            "HOST_GID": "1000",
            "VIDEO_GID": "44",
            "RENDER_GID": "109",
            "HIP_VISIBLE_DEVICES": "0",
            "CPUSET_GPU": "0-7",
            "MEM_LIMIT": "48g",
            "SHM_SIZE": "8g",
            "TMPFS_SIZE": "2g",
            "OMP_NUM_THREADS": "8",
            "MKL_NUM_THREADS": "8",
            "OPENBLAS_NUM_THREADS": "8",
            "NUMEXPR_NUM_THREADS": "8",
        }
    )


def test_import_surface_has_no_process_spawner() -> None:
    source = Path(chain_module.__file__).read_text(encoding="utf-8")
    assert "import subprocess" not in source
    assert "subprocess." not in source
    assert "Popen(" not in source
    assert "subprocess.Popen" not in source


def test_host_image_identity_matches_execution_freeze() -> None:
    freeze = load_attempt_002_host_execution_freeze(ROOT)
    identity = load_attempt_002_host_image_identity(ROOT, freeze)
    assert identity.image_digest == EXPECTED_IMAGE_DIGEST
    assert identity.image_repo_digest == EXPECTED_IMAGE_REPO_DIGEST
    assert identity.source_commit == freeze.source_commit


def test_host_invocation_contract_is_closed_and_digest_exact() -> None:
    contract = build_attempt_002_host_invocation_contract(ROOT)
    contract.require()
    assert contract.host_command_materialization_present is True
    assert contract.host_process_spawner_present is False
    assert contract.docker_run_implemented is False
    assert contract.runtime_execution_permitted is False
    assert [mount.access for mount in contract.mounts] == [
        "read_only",
        "read_only",
        "read_write",
    ]


def test_local_image_inspection_parses_exact_identity() -> None:
    expected = load_attempt_002_host_image_identity(ROOT)
    inspection = parse_attempt_002_local_image_inspection(
        _inspect_payload(),
        expected,
    )
    assert inspection.image_id == EXPECTED_IMAGE_DIGEST
    assert EXPECTED_IMAGE_REPO_DIGEST in inspection.repo_digests


def test_local_image_inspection_rejects_digest_mutation() -> None:
    expected = load_attempt_002_host_image_identity(ROOT)
    payload = json.loads(_inspect_payload())
    payload[0]["Id"] = "sha256:" + "0" * 64
    with pytest.raises(
        Attempt002HostInvocationChainError,
        match="image_id",
    ):
        parse_attempt_002_local_image_inspection(
            json.dumps(payload),
            expected,
        )


def test_host_resource_key_set_is_exact() -> None:
    values = dict(_resources().as_host_mapping())
    values.pop("NUMEXPR_NUM_THREADS")
    with pytest.raises(
        Attempt002HostInvocationChainError,
        match="key set",
    ):
        HostInvocationResources.from_mapping(values)


def test_host_resource_values_are_canonical() -> None:
    values = dict(_resources().as_host_mapping())
    values["CPUSET_GPU"] = "0-7;rm"
    with pytest.raises(
        Attempt002HostInvocationChainError,
        match="CPUSET_GPU",
    ):
        HostInvocationResources.from_mapping(values)



def test_host_thread_count_must_be_positive() -> None:
    values = dict(_resources().as_host_mapping())
    values["OMP_NUM_THREADS"] = "0"
    with pytest.raises(
        Attempt002HostInvocationChainError,
        match="thread resource",
    ):
        HostInvocationResources.from_mapping(values)

def test_materialized_invocation_is_data_only_and_policy_exact() -> None:
    contract = build_attempt_002_host_invocation_contract(ROOT)
    identity = load_attempt_002_host_image_identity(ROOT)
    inspection = parse_attempt_002_local_image_inspection(
        _inspect_payload(),
        identity,
    )
    invocation = materialize_attempt_002_host_invocation(
        ROOT,
        contract,
        inspection,
        _resources(),
        claimed_at_utc="2026-08-04T17:30:00Z",
        invocation_acknowledgement=ATTEMPT_002_INVOCATION_ACKNOWLEDGEMENT,
        lease_acknowledgement=ATTEMPT_002_LEASE_ACKNOWLEDGEMENT,
    )
    invocation.require(contract, inspection)
    assert invocation.argv[:2] == ("docker", "run")
    assert EXPECTED_IMAGE_REPO_DIGEST in invocation.argv
    assert "--read-only" in invocation.argv
    assert invocation.subprocess_spawned is False
    assert invocation.container_created is False
    assert invocation.authorization_issued is False
    assert invocation.execution_lease_created is False


def test_materialized_invocation_contains_no_dataset_mount() -> None:
    contract = build_attempt_002_host_invocation_contract(ROOT)
    identity = load_attempt_002_host_image_identity(ROOT)
    inspection = parse_attempt_002_local_image_inspection(
        _inspect_payload(),
        identity,
    )
    invocation = materialize_attempt_002_host_invocation(
        ROOT,
        contract,
        inspection,
        _resources(),
        claimed_at_utc="2026-08-04T17:30:00Z",
        invocation_acknowledgement=ATTEMPT_002_INVOCATION_ACKNOWLEDGEMENT,
        lease_acknowledgement=ATTEMPT_002_LEASE_ACKNOWLEDGEMENT,
    )
    assert all(
        ":/workspace/data" not in argument.casefold()
        for argument in invocation.argv
    )
    assert "/workspace/data" not in invocation.argv


def test_wrong_invocation_acknowledgement_fails_closed() -> None:
    contract = build_attempt_002_host_invocation_contract(ROOT)
    identity = load_attempt_002_host_image_identity(ROOT)
    inspection = parse_attempt_002_local_image_inspection(
        _inspect_payload(),
        identity,
    )
    with pytest.raises(
        Attempt002HostInvocationChainError,
        match="invocation acknowledgement",
    ):
        materialize_attempt_002_host_invocation(
            ROOT,
            contract,
            inspection,
            _resources(),
            claimed_at_utc="2026-08-04T17:30:00Z",
            invocation_acknowledgement="WRONG",
            lease_acknowledgement=ATTEMPT_002_LEASE_ACKNOWLEDGEMENT,
        )


def test_closed_effect_boundary_rejects_authorization(tmp_path: Path) -> None:
    path = tmp_path / ATTEMPT_002_AUTHORIZATION_ROOT
    path.mkdir(parents=True)
    with pytest.raises(
        Attempt002HostInvocationChainError,
        match="closed effect exists",
    ):
        chain_module._require_effect_boundary(tmp_path)


def test_chain_state_opens_only_authorization_authoring() -> None:
    state = build_attempt_002_host_invocation_chain_state(ROOT)
    state.require()
    assert state.authorization_authoring_admissible is True
    assert state.authorization_issued is False
    assert state.host_process_spawner_present is False
    assert state.docker_run_implemented is False
    assert state.runtime_execution_started is False
    assert state.runtime_execution_performed is False


def test_contract_mutation_is_rejected() -> None:
    contract = build_attempt_002_host_invocation_contract(ROOT)
    mutated = replace(contract, docker_run_implemented=True)
    with pytest.raises(
        Attempt002HostInvocationChainError,
        match="docker_run_implemented",
    ):
        mutated.require()
