from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from torch2pc_thesis.stage3b_qwake_lc4_invocation_authorization import (
    AUTHORIZED_OUTPUT_ROOT,
    EXECUTION_LEASE_RELATIVE,
    IMAGE_REPO_DIGEST,
    INVOCATION_AUTHORIZATION_ID,
)
from torch2pc_thesis.stage3b_qwake_lc4_invocation_wrapper import (
    AUTHORIZATION_HEAD_COMMIT,
    AUTHORIZATION_MERGE_COMMIT,
    CONTAINER_COMMAND_TEMPLATE,
    CONTAINER_DEVICE_BINDINGS,
    CONTAINER_IMAGE_ENTRYPOINT,
    CONTAINER_RUNTIME_ENTRYPOINT,
    CONTAINER_TMPFS_OPTIONS,
    CONTAINER_TMPFS_TARGET,
    CONTAINER_USER_TEMPLATE,
    INVOCATION_WRAPPER_CONTRACT_ID,
    INVOCATION_WRAPPER_CONTRACT_STATUS,
    QWakeLC4InvocationWrapperError,
    build_one_shot_invocation_wrapper_contract,
    load_one_shot_invocation_wrapper_contract,
    validate_one_shot_invocation_wrapper_contract,
    verify_invocation_wrapper_prerequisites,
)

ROOT = Path(__file__).resolve().parents[2]
MODULE = (
    ROOT
    / "src/torch2pc_thesis/stage3b_qwake_lc4_invocation_wrapper.py"
)
VERIFIER = (
    ROOT
    / "scripts/verify_stage3b_qwake_lc4_invocation_wrapper_authoring.py"
)
AUTHORING_ROOT = (
    ROOT
    / "experiments/frozen/"
    "stage3b-qwake-lc4-e-one-shot-invocation-wrapper-authoring-v1"
)


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def test_exact_authorization_prerequisites_are_verified() -> None:
    authorization_sha256, entrypoint_sha256 = (
        verify_invocation_wrapper_prerequisites(ROOT)
    )
    assert authorization_sha256 == (
        "sha256:0a60dacc1bfd5073cf52d76f2ec33ae54f00899aad9877d44607199659fda75a"
    )
    assert entrypoint_sha256 == (
        "sha256:504c3e614e199789b25c8b1927d0a35b1b95e1f3a5411e42db794fc93782cc79"
    )
    assert AUTHORIZATION_MERGE_COMMIT == (
        "8337d9ad0ac21a69a577ab74a73d05d69f8fa7a1"
    )
    assert AUTHORIZATION_HEAD_COMMIT == (
        "ca6363c11218575d567c5dd6cbe8818d10a86d41"
    )


def test_invocation_wrapper_contract_is_exact_and_effect_free() -> None:
    contract = build_one_shot_invocation_wrapper_contract(ROOT)
    validate_one_shot_invocation_wrapper_contract(contract, ROOT)

    assert contract.contract_id == INVOCATION_WRAPPER_CONTRACT_ID
    assert contract.status == INVOCATION_WRAPPER_CONTRACT_STATUS
    assert contract.authorization_id == INVOCATION_AUTHORIZATION_ID
    assert contract.image_repo_digest == IMAGE_REPO_DIGEST
    assert contract.container_image_entrypoint == CONTAINER_IMAGE_ENTRYPOINT
    assert contract.container_runtime_entrypoint == CONTAINER_RUNTIME_ENTRYPOINT
    assert contract.container_command_template == CONTAINER_COMMAND_TEMPLATE
    assert contract.container_user_template == CONTAINER_USER_TEMPLATE
    assert contract.device_bindings == CONTAINER_DEVICE_BINDINGS
    assert contract.tmpfs_target == CONTAINER_TMPFS_TARGET
    assert contract.tmpfs_options == CONTAINER_TMPFS_OPTIONS
    assert contract.host_environment_bindings == (
        ("HIP_VISIBLE_DEVICES", "HIP_VISIBLE_DEVICES"),
        ("OMP_NUM_THREADS", "OMP_NUM_THREADS"),
        ("MKL_NUM_THREADS", "MKL_NUM_THREADS"),
        ("OPENBLAS_NUM_THREADS", "OPENBLAS_NUM_THREADS"),
        ("NUMEXPR_NUM_THREADS", "NUMEXPR_NUM_THREADS"),
    )
    assert contract.supplementary_group_inputs == ("VIDEO_GID", "RENDER_GID")
    assert contract.cpuset_input == "CPUSET_GPU"
    assert contract.memory_limit_input == "MEM_LIMIT"
    assert contract.shm_size_input == "SHM_SIZE"
    assert contract.tmpfs_size_input == "TMPFS_SIZE"
    assert contract.image_reference_must_use_repo_digest is True
    assert contract.network_disabled is True
    assert contract.read_only_root_filesystem is True
    assert contract.tmpfs_target == "/tmp"
    assert "size=${TMPFS_SIZE}" in contract.tmpfs_options
    assert contract.project_source_bind_forbidden is True
    assert contract.test_dataset_mount_forbidden is True
    assert contract.invocation_wrapper_contract_present is True
    assert contract.host_runtime_invoker_present is False
    assert contract.branch_runtime_execution_permitted is False
    assert contract.execution_lease_materialized is False
    assert contract.authorization_consumed is False
    assert contract.runtime_execution_started is False
    assert contract.runtime_execution_performed is False

    assert tuple(
        (mount.source_kind, mount.target, mount.access)
        for mount in contract.mounts
    ) == (
        (
            "frozen_experiments",
            "/workspace/experiments/frozen",
            "read_only",
        ),
        (
            "torch2pc_checkout",
            "/workspace/external/Torch2PC",
            "read_only",
        ),
        (
            "runtime_results",
            "/workspace/results",
            "read_write",
        ),
    )


def test_invocation_wrapper_contract_round_trip(tmp_path: Path) -> None:
    contract = build_one_shot_invocation_wrapper_contract(ROOT)
    path = tmp_path / "contract.json"
    path.write_text(contract.canonical_json(), encoding="utf-8")
    assert load_one_shot_invocation_wrapper_contract(path) == contract


def test_opened_effect_or_runtime_invoker_fails_closed() -> None:
    contract = build_one_shot_invocation_wrapper_contract(ROOT)

    with pytest.raises(
        QWakeLC4InvocationWrapperError,
        match="host_runtime_invoker_present",
    ):
        replace(contract, host_runtime_invoker_present=True).require()
    with pytest.raises(
        QWakeLC4InvocationWrapperError,
        match="runtime_execution_started",
    ):
        replace(contract, runtime_execution_started=True).require()
    with pytest.raises(
        QWakeLC4InvocationWrapperError,
        match="contract digest differs",
    ):
        replace(
            contract,
            contract_sha256="sha256:" + "0" * 64,
        ).require()


def test_repository_effects_block_authoring(tmp_path: Path) -> None:
    lease_root = tmp_path / "lease-case"
    lease_root.mkdir()
    lease_path = lease_root / EXECUTION_LEASE_RELATIVE
    lease_path.parent.mkdir(parents=True)
    lease_path.write_text("{}\n", encoding="utf-8")
    with pytest.raises(
        QWakeLC4InvocationWrapperError,
        match="execution lease already exists",
    ):
        verify_invocation_wrapper_prerequisites(lease_root)

    output_root = tmp_path / "output-case"
    output_path = output_root / AUTHORIZED_OUTPUT_ROOT
    output_path.mkdir(parents=True)
    with pytest.raises(
        QWakeLC4InvocationWrapperError,
        match="runtime output already exists",
    ):
        verify_invocation_wrapper_prerequisites(output_root)


def test_authoring_surfaces_cannot_invoke_container_or_runtime() -> None:
    sources = (
        MODULE.read_text(encoding="utf-8"),
        VERIFIER.read_text(encoding="utf-8"),
    )
    combined = "\n".join(sources)
    forbidden_markers = (
        "subprocess.run(",
        "subprocess.Popen(",
        "os.system(",
        "docker run",
        "docker compose run",
        "run_one_shot_authorized_runtime(",
        "claim_execution_lease(",
        "execute_authorized_runtime(",
        "materialize_execution_lease(",
        "load_test_dataset",
        "write_engineering_evidence",
        "publish_result",
    )
    assert all(marker not in combined for marker in forbidden_markers)

    for source in sources:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = tuple(alias.name for alias in node.names)
                assert "subprocess" not in imported
                assert all(
                    name != "torch" and not name.startswith("torch.")
                    for name in imported
                )
            if isinstance(node, ast.ImportFrom):
                imported_from = node.module or ""
                assert imported_from != "subprocess"
                assert (
                    imported_from != "torch"
                    and not imported_from.startswith("torch.")
                )

    assert "HOST_RUNTIME_INVOKER_PRESENT=false" in sources[1]
    assert "INVOCATION_COMMAND_MATERIALIZED=false" in sources[1]
    assert "EXECUTION_LEASE_MATERIALIZED=false" in sources[1]
    assert "RUNTIME_EXECUTION_PERFORMED=false" in sources[1]


def test_authoring_package_and_documentation_are_registered() -> None:
    authoring = AUTHORING_ROOT / "authoring.json"
    registry = AUTHORING_ROOT / "SHA256SUMS"
    assert authoring.is_file()
    assert registry.is_file()

    expected, relative = registry.read_text(encoding="utf-8").strip().split("  ", 1)
    assert relative == "authoring.json"
    assert hashlib.sha256(authoring.read_bytes()).hexdigest() == expected

    payload = json.loads(authoring.read_text(encoding="utf-8"))
    assert payload["authoring_id"] == (
        "stage3b-qwake-lc4-e-one-shot-invocation-wrapper-authoring-v1"
    )
    assert payload["status"] == (
        "host_invocation_wrapper_contract_materialized_runtime_invoker_absent"
    )
    assert payload["source"]["authorization_merge_commit"] == (
        AUTHORIZATION_MERGE_COMMIT
    )
    assert payload["contracts"]["contract_id"] == (
        INVOCATION_WRAPPER_CONTRACT_ID
    )
    assert payload["contracts"]["container_command_template_present"] is True
    assert payload["contracts"]["device_binding_count"] == 2
    assert payload["contracts"]["tmpfs_target"] == "/tmp"
    assert payload["contracts"]["tmpfs_required"] is True
    assert payload["gates"]["invocation_wrapper_contract_present"] is True
    assert payload["gates"]["host_runtime_invoker_present"] is False
    assert payload["gates"]["branch_runtime_execution_permitted"] is False
    assert payload["gates"]["execution_lease_materialized"] is False
    assert payload["gates"]["runtime_execution_performed"] is False
    assert payload["post_merge_next_slice"] == (
        "QW-LC4-E-one-shot-invocation-wrapper-implementation"
    )

    assert payload["contracts"]["module_sha256"] == _sha256(MODULE)
    assert payload["contracts"]["verifier_sha256"] == _sha256(VERIFIER)
    assert payload["contracts"]["test_sha256"] == _sha256(Path(__file__))

    marker = "ADR-072-stage3b-qwake-lc4-e-one-shot-invocation-wrapper-authoring"
    required = (
        ROOT / "STATUS.md",
        ROOT / "STATUS_EN.md",
        ROOT / "docs/qwake-local-compute-extension.md",
        ROOT / "docs/qwake-local-compute-extension_EN.md",
        ROOT / "docs/decisions/index.md",
        ROOT / "docs/decisions/index_EN.md",
        ROOT / "docs/language-map.csv",
        ROOT / "docs/research-log/2026-07.md",
        ROOT / "docs/research-log/2026-07_EN.md",
    )
    for path in required:
        assert marker in path.read_text(encoding="utf-8")
