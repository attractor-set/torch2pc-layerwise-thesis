from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

import torch2pc_thesis.stage3b_qwake_lc4_invocation_wrapper as authoring
import torch2pc_thesis.stage3b_qwake_lc4_invocation_wrapper_implementation as implementation
from torch2pc_thesis.stage3b_qwake_lc4_invocation_authorization import (
    IMAGE_DIGEST,
    IMAGE_REPO_DIGEST,
    IMAGE_TAG,
    INVOCATION_OPERATOR_ACKNOWLEDGEMENT,
)
from torch2pc_thesis.stage3b_qwake_lc4_invocation_wrapper import (
    CONTAINER_IMAGE_ENTRYPOINT,
    CONTAINER_RUNTIME_ENTRYPOINT,
)
from torch2pc_thesis.stage3b_qwake_lc4_invocation_wrapper_implementation import (
    FIXTURE_CLAIMED_AT_UTC,
    FROZEN_IMAGE_INSPECTION_SHA256,
    INVOCATION_WRAPPER_IMPLEMENTATION_ID,
    INVOCATION_WRAPPER_IMPLEMENTATION_STATUS,
    QWakeLC4InvocationImplementationError,
    load_frozen_image_identity,
    load_host_invocation_resources,
    materialize_one_shot_invocation,
    parse_local_image_inspection,
    validate_materialized_one_shot_invocation,
)

ROOT = Path(__file__).resolve().parents[2]
MODULE = (
    ROOT
    / "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_invocation_wrapper_implementation.py"
)
VERIFIER = (
    ROOT
    / "scripts/"
    "verify_stage3b_qwake_lc4_invocation_wrapper_implementation.py"
)
IMPLEMENTATION_ROOT = (
    ROOT
    / "experiments/frozen/"
    "stage3b-qwake-lc4-e-one-shot-invocation-wrapper-implementation-v1"
)
AUTHORIZATION_SHA256 = (
    "sha256:0a60dacc1bfd5073cf52d76f2ec33ae54f00899aad9877d44607199659fda75a"
)
ENTRYPOINT_SHA256 = (
    "sha256:504c3e614e199789b25c8b1927d0a35b1b95e1f3a5411e42db794fc93782cc79"
)


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _contract(
    monkeypatch: pytest.MonkeyPatch,
) -> authoring.OneShotInvocationWrapperContract:
    monkeypatch.setattr(
        authoring,
        "verify_invocation_wrapper_prerequisites",
        lambda _root: (AUTHORIZATION_SHA256, ENTRYPOINT_SHA256),
    )
    return authoring.build_one_shot_invocation_wrapper_contract(ROOT)


def _raw_image_record() -> str:
    frozen = load_frozen_image_identity(ROOT)
    payload: list[dict[str, Any]] = [
        {
            "Id": frozen.image_id,
            "RepoDigests": list(frozen.repo_digests_observed),
            "RepoTags": [frozen.image_tag],
            "Architecture": frozen.architecture,
            "Os": frozen.operating_system,
            "Created": frozen.created,
            "Size": frozen.size_bytes,
            "RootFS": {
                "Type": "layers",
                "Layers": list(frozen.rootfs_layers),
            },
            "Config": {
                "Labels": {
                    "org.opencontainers.image.revision": frozen.oci_revision,
                    "io.torch2pc.base-image": frozen.oci_base_image,
                },
                "Env": [
                    f"SOURCE_GIT_COMMIT={frozen.source_git_commit_env}",
                    "PYTHONUNBUFFERED=1",
                ],
                "Entrypoint": list(CONTAINER_IMAGE_ENTRYPOINT),
                "WorkingDir": "/workspace",
            },
        }
    ]
    return json.dumps(payload, sort_keys=True)


def _resources() -> dict[str, str]:
    return {
        "HOST_UID": "1000",
        "HOST_GID": "1000",
        "VIDEO_GID": "44",
        "RENDER_GID": "109",
        "HIP_VISIBLE_DEVICES": "0",
        "CPUSET_GPU": "0-7",
        "MEM_LIMIT": "48g",
        "SHM_SIZE": "8gb",
        "TMPFS_SIZE": "8g",
        "OMP_NUM_THREADS": "4",
        "MKL_NUM_THREADS": "4",
        "OPENBLAS_NUM_THREADS": "4",
        "NUMEXPR_NUM_THREADS": "4",
    }


def _materialization_root(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    (root / "experiments/frozen").mkdir(parents=True)
    (root / "external/Torch2PC").mkdir(parents=True)
    (root / "results").mkdir(parents=True)
    return root


def _prepare_materialization(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> tuple[
    Path,
    authoring.OneShotInvocationWrapperContract,
    implementation.FrozenImageIdentity,
    implementation.LocalImageInspection,
]:
    contract = _contract(monkeypatch)
    frozen = load_frozen_image_identity(ROOT)
    inspection = parse_local_image_inspection(
        _raw_image_record(), contract, frozen
    )
    root = _materialization_root(tmp_path)
    monkeypatch.setattr(
        implementation,
        "load_frozen_image_identity",
        lambda _root: frozen,
    )
    return root, contract, frozen, inspection


def test_frozen_image_identity_is_exact() -> None:
    frozen = load_frozen_image_identity(ROOT)
    assert frozen.record_sha256 == FROZEN_IMAGE_INSPECTION_SHA256
    assert frozen.image_tag == IMAGE_TAG
    assert frozen.image_digest == IMAGE_DIGEST
    assert frozen.image_repo_digest == IMAGE_REPO_DIGEST
    assert frozen.image_id == IMAGE_DIGEST
    assert frozen.architecture == "amd64"
    assert frozen.operating_system == "linux"
    assert len(frozen.rootfs_layers) == 16


def test_exact_local_image_inspection_is_normalized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contract = _contract(monkeypatch)
    frozen = load_frozen_image_identity(ROOT)
    inspection = parse_local_image_inspection(
        _raw_image_record(), contract, frozen
    )
    assert inspection.image_reference == IMAGE_REPO_DIGEST
    assert inspection.image_id == IMAGE_DIGEST
    assert inspection.repo_digests == (IMAGE_REPO_DIGEST,)
    assert inspection.repo_tags == (IMAGE_TAG,)
    assert inspection.oci_revision == frozen.oci_revision
    assert inspection.source_git_commit_env == frozen.source_git_commit_env
    assert inspection.image_entrypoint == CONTAINER_IMAGE_ENTRYPOINT
    assert inspection.working_dir == "/workspace"
    assert inspection.inspection_sha256.startswith("sha256:")


def test_image_identity_mismatch_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contract = _contract(monkeypatch)
    frozen = load_frozen_image_identity(ROOT)
    raw = json.loads(_raw_image_record())
    raw[0]["Id"] = "sha256:" + "0" * 64
    with pytest.raises(
        QWakeLC4InvocationImplementationError,
        match="image_id",
    ):
        parse_local_image_inspection(json.dumps(raw), contract, frozen)

    raw = json.loads(_raw_image_record())
    raw[0]["Config"]["Labels"][
        "org.opencontainers.image.revision"
    ] = "0" * 40
    with pytest.raises(
        QWakeLC4InvocationImplementationError,
        match="oci_revision",
    ):
        parse_local_image_inspection(json.dumps(raw), contract, frozen)

    raw = json.loads(_raw_image_record())
    raw[0]["Config"]["Entrypoint"] = ["/bin/sh"]
    with pytest.raises(
        QWakeLC4InvocationImplementationError,
        match="image_entrypoint",
    ):
        parse_local_image_inspection(json.dumps(raw), contract, frozen)


def test_host_resource_inputs_are_exact_and_canonical() -> None:
    resources = load_host_invocation_resources(_resources())
    assert resources.cpuset_gpu == "0-7"
    assert resources.hip_visible_devices == "0"
    assert resources.mem_limit == "48g"
    assert resources.tmpfs_size == "8g"

    values = _resources()
    values["EXTRA"] = "forbidden"
    with pytest.raises(
        QWakeLC4InvocationImplementationError,
        match="key set differs",
    ):
        load_host_invocation_resources(values)

    values = _resources()
    values["CPUSET_GPU"] = "0,1,2,3"
    with pytest.raises(
        QWakeLC4InvocationImplementationError,
        match="CPUSET_GPU is not canonical",
    ):
        load_host_invocation_resources(values)

    values = _resources()
    values["MEM_LIMIT"] = "0g"
    with pytest.raises(
        QWakeLC4InvocationImplementationError,
        match="MEM_LIMIT",
    ):
        load_host_invocation_resources(values)


def test_command_materialization_is_deterministic_and_effect_free(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root, contract, _frozen, inspection = _prepare_materialization(
        monkeypatch, tmp_path
    )
    first = materialize_one_shot_invocation(
        root,
        image_inspection=inspection,
        host_resources=_resources(),
        claimed_at_utc=FIXTURE_CLAIMED_AT_UTC,
        operator_acknowledgement=INVOCATION_OPERATOR_ACKNOWLEDGEMENT,
    )
    second = materialize_one_shot_invocation(
        root,
        image_inspection=inspection,
        host_resources=_resources(),
        claimed_at_utc=FIXTURE_CLAIMED_AT_UTC,
        operator_acknowledgement=INVOCATION_OPERATOR_ACKNOWLEDGEMENT,
    )
    validate_materialized_one_shot_invocation(
        first,
        root,
        image_inspection=inspection,
        host_resources=_resources(),
        claimed_at_utc=FIXTURE_CLAIMED_AT_UTC,
        operator_acknowledgement=INVOCATION_OPERATOR_ACKNOWLEDGEMENT,
    )
    assert first == second
    assert first.implementation_id == INVOCATION_WRAPPER_IMPLEMENTATION_ID
    assert first.status == INVOCATION_WRAPPER_IMPLEMENTATION_STATUS
    assert first.argv[:3] == ("docker", "run", "--pull=never")
    assert "--network" in first.argv
    assert "none" in first.argv
    assert "--read-only" in first.argv
    assert "--privileged" not in first.argv
    assert "--volume" not in first.argv
    assert "-v" not in first.argv
    assert first.argv.count("--device") == 2
    assert first.argv.count("--mount") == 3
    image_index = first.argv.index(IMAGE_REPO_DIGEST)
    assert first.argv[image_index + 1 :] == (
        "python",
        CONTAINER_RUNTIME_ENTRYPOINT,
        "--project-root",
        "/workspace",
        "--torch2pc-dir",
        "/workspace/external/Torch2PC",
        "--claimed-at-utc",
        FIXTURE_CLAIMED_AT_UTC,
        "--operator-acknowledgement",
        contract.lease_operator_acknowledgement,
    )
    assert first.image_inspection_implemented is True
    assert first.invocation_command_materialized is True
    assert first.invocation_command_persisted is False
    assert first.host_runtime_invoker_present is False
    assert first.execution_lease_materialized is False
    assert first.runtime_execution_performed is False
    assert not (root / contract.execution_lease_relative).exists()
    assert not (root / contract.output_root).exists()


def test_acknowledgement_timestamp_and_mutation_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root, _contract_value, _frozen, inspection = _prepare_materialization(
        monkeypatch, tmp_path
    )
    with pytest.raises(
        QWakeLC4InvocationImplementationError,
        match="acknowledgement differs",
    ):
        materialize_one_shot_invocation(
            root,
            image_inspection=inspection,
            host_resources=_resources(),
            claimed_at_utc=FIXTURE_CLAIMED_AT_UTC,
            operator_acknowledgement="wrong",
        )
    with pytest.raises(
        QWakeLC4InvocationImplementationError,
        match="RFC3339",
    ):
        materialize_one_shot_invocation(
            root,
            image_inspection=inspection,
            host_resources=_resources(),
            claimed_at_utc="2026-07-29 03:36:18",
            operator_acknowledgement=INVOCATION_OPERATOR_ACKNOWLEDGEMENT,
        )
    materialized = materialize_one_shot_invocation(
        root,
        image_inspection=inspection,
        host_resources=_resources(),
        claimed_at_utc=FIXTURE_CLAIMED_AT_UTC,
        operator_acknowledgement=INVOCATION_OPERATOR_ACKNOWLEDGEMENT,
    )
    with pytest.raises(
        QWakeLC4InvocationImplementationError,
        match="digest differs",
    ):
        replace(
            materialized,
            argv=materialized.argv + ("unexpected",),
        ).require()


def test_implementation_surfaces_only_inspect_and_never_invoke() -> None:
    sources = (
        MODULE.read_text(encoding="utf-8"),
        VERIFIER.read_text(encoding="utf-8"),
    )
    combined = "\n".join(sources)
    forbidden_markers = (
        "subprocess.Popen(",
        "os.system(",
        "shell=True",
        "run_one_shot_authorized_runtime",
        "claim_execution_lease(",
        "execute_authorized_runtime(",
        "materialize_execution_lease(",
        "write_engineering_evidence",
        "publish_result",
        "load_test_dataset",
    )
    assert all(marker not in combined for marker in forbidden_markers)
    assert combined.count("subprocess.run(") == 1
    assert '"image",\n        "inspect"' in sources[0]

    for source in sources:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = tuple(alias.name for alias in node.names)
                assert all(
                    name != "torch" and not name.startswith("torch.")
                    for name in imported
                )
            if isinstance(node, ast.ImportFrom):
                imported_from = node.module or ""
                assert (
                    imported_from != "torch"
                    and not imported_from.startswith("torch.")
                )
                assert not imported_from.endswith(
                    "stage3b_qwake_lc4_runtime_backend"
                )


def test_implementation_package_and_documentation_are_registered() -> None:
    implementation_path = IMPLEMENTATION_ROOT / "implementation.json"
    registry = IMPLEMENTATION_ROOT / "SHA256SUMS"
    assert implementation_path.is_file()
    assert registry.is_file()

    entries: dict[str, str] = {}
    for line in registry.read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        entries[relative] = digest
    assert entries == {
        "implementation.json": hashlib.sha256(
            implementation_path.read_bytes()
        ).hexdigest()
    }

    payload = json.loads(implementation_path.read_text(encoding="utf-8"))
    assert payload["implementation_id"] == (
        "stage3b-qwake-lc4-e-one-shot-host-invocation-wrapper-implementation-v1"
    )
    assert payload["status"] == (
        "image_inspection_and_command_materialization_implemented_"
        "runtime_invoker_absent"
    )
    assert payload["source"]["implementation_base_commit"] == (
        "7cc17c6b36cb5115e63a2b64e4bff90a525b2465"
    )
    assert payload["contracts"]["module_sha256"] == _sha256(MODULE)
    assert payload["contracts"]["verifier_sha256"] == _sha256(VERIFIER)
    assert payload["contracts"]["test_sha256"] == _sha256(Path(__file__))
    assert payload["gates"]["image_inspection_implemented"] is True
    assert payload["gates"]["invocation_command_materialized"] is True
    assert payload["gates"]["invocation_command_persisted"] is False
    assert payload["gates"]["host_runtime_invoker_present"] is False
    assert payload["gates"]["execution_lease_materialized"] is False
    assert payload["gates"]["runtime_execution_performed"] is False

    required_paths = (
        ROOT
        / "docs/decisions/"
        "ADR-073-stage3b-qwake-lc4-e-one-shot-invocation-wrapper-implementation.md",
        ROOT
        / "docs/decisions/"
        "ADR-073-stage3b-qwake-lc4-e-one-shot-invocation-wrapper-implementation_EN.md",
    )
    assert all(path.is_file() for path in required_paths)
