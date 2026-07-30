# Validate fail-closed lease-bound host-invoker wiring.

from __future__ import annotations

import ast
import json
import os
import shutil
from dataclasses import replace
from io import BytesIO
from pathlib import Path
from typing import Any

import pytest

from torch2pc_thesis.stage3b_qwake_lc4_invocation_wrapper import (
    CONTAINER_IMAGE_ENTRYPOINT,
    build_one_shot_invocation_wrapper_contract,
)
from torch2pc_thesis.stage3b_qwake_lc4_invocation_wrapper_implementation import (
    LocalImageInspection,
    load_frozen_image_identity,
    parse_local_image_inspection,
)
from torch2pc_thesis.stage3b_qwake_lc4_lease_bound_host_invoker_wiring import (
    LEASE_BOUND_HOST_INVOKER_WIRING_ID,
    LeaseBoundHostInvokerWiringError,
    build_lease_bound_host_invoker_wiring_state,
    invoke_lease_bound_host_runtime,
    validate_lease_bound_host_invoker_wiring_state,
)
from torch2pc_thesis.stage3b_qwake_lc4_persistent_evidence_chain_v2 import (
    DURABLE_HOST_OUTCOME_RELATIVE,
    PERSISTENT_LEASE_V2_OPERATOR_ACKNOWLEDGEMENT,
    PersistentEvidenceChainV2,
    PersistentExecutionLeaseV2,
    build_persistent_execution_lease_v2,
    sha256_bytes,
    verify_persistent_evidence_chain_v2,
)
from torch2pc_thesis.stage3b_qwake_lc4_persistent_evidence_chain_v2_implementation import (
    PersistentEvidenceChainV2ImplementationError,
    persist_persistent_execution_lease_v2,
)

ROOT = Path(__file__).resolve().parents[2]
EXECUTION_COMMIT = "f" * 40


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


def _inspection(root: Path) -> LocalImageInspection:
    frozen = load_frozen_image_identity(root)
    contract = build_one_shot_invocation_wrapper_contract(root)
    raw: list[dict[str, Any]] = [
        {
            "Id": frozen.image_id,
            "RepoDigests": list(frozen.repo_digests_observed),
            "RepoTags": [frozen.image_tag],
            "Architecture": frozen.architecture,
            "Os": frozen.operating_system,
            "Created": frozen.created,
            "Size": frozen.size_bytes,
            "RootFS": {"Type": "layers", "Layers": list(frozen.rootfs_layers)},
            "Config": {
                "Labels": {
                    "org.opencontainers.image.revision": frozen.oci_revision,
                    "io.torch2pc.base-image": frozen.oci_base_image,
                },
                "Env": [f"SOURCE_GIT_COMMIT={frozen.source_git_commit_env}"],
                "Entrypoint": list(CONTAINER_IMAGE_ENTRYPOINT),
                "WorkingDir": "/workspace",
            },
        }
    ]
    return parse_local_image_inspection(
        json.dumps(raw, sort_keys=True), contract, frozen
    )


def _sandbox(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    for relative in (
        Path("docs"),
        Path("experiments/frozen"),
        Path("scripts"),
        Path("src"),
        Path("tests"),
    ):
        shutil.copytree(
            ROOT / relative,
            root / relative,
            copy_function=os.link,
        )
    (root / "external/Torch2PC").mkdir(parents=True)
    (root / "results/stage-3").mkdir(parents=True)
    return root


def _lease(
    root: Path,
) -> tuple[PersistentEvidenceChainV2, PersistentExecutionLeaseV2]:
    chain = verify_persistent_evidence_chain_v2(root)
    lease = build_persistent_execution_lease_v2(
        chain,
        claimed_at_utc="2026-07-30T13:00:00Z",
        execution_commit=EXECUTION_COMMIT,
        operator_acknowledgement=PERSISTENT_LEASE_V2_OPERATOR_ACKNOWLEDGEMENT,
        output_root_absent_at_claim=True,
        execution_lease_absent_at_claim=True,
        durable_outcome_absent_at_claim=True,
    )
    return chain, lease


class _FakeProcess:
    def __init__(
        self,
        *,
        stdout: bytes = b"OK\n",
        stderr: bytes = b"",
        return_code: int = 0,
    ) -> None:
        self.pid = 4242
        self.stdout = BytesIO(stdout)
        self.stderr = BytesIO(stderr)
        self.returncode: int | None = None
        self._return_code = return_code

    def poll(self) -> int | None:
        return self.returncode

    def wait(self, timeout: float | None = None) -> int:
        assert timeout is not None
        self.returncode = self._return_code
        return self._return_code


class _FakeSpawner:
    def __init__(self, process: _FakeProcess | None = None) -> None:
        self.process = process
        self.calls = 0

    def __call__(self, _argv: object, **_kwargs: object) -> _FakeProcess:
        self.calls += 1
        if self.process is None:
            raise OSError("synthetic spawn failure")
        return self.process


class _Clock:
    def __init__(self) -> None:
        self.values = iter(("2026-07-30T13:00:01Z", "2026-07-30T13:00:02Z"))

    def __call__(self) -> str:
        return next(self.values)


def test_wiring_state_is_exact_and_effect_free() -> None:
    state = build_lease_bound_host_invoker_wiring_state(ROOT)
    validate_lease_bound_host_invoker_wiring_state(state, ROOT)
    assert state.wiring_id == LEASE_BOUND_HOST_INVOKER_WIRING_ID
    assert state.lease_bound_host_invoker_enforced is True
    assert state.final_execution_acknowledged is False
    assert state.execution_lease_materialized is False


def test_changed_wiring_state_fails_closed() -> None:
    state = build_lease_bound_host_invoker_wiring_state(ROOT)
    with pytest.raises(LeaseBoundHostInvokerWiringError, match="one_shot_engineering_invocation_permitted"):
        replace(state, one_shot_engineering_invocation_permitted=True).require()


def test_persisted_lease_is_required_before_inspection(tmp_path: Path) -> None:
    root = _sandbox(tmp_path)
    chain, lease = _lease(root)
    calls = 0

    def inspect(_root: Path, *, timeout_seconds: float) -> LocalImageInspection:
        nonlocal calls
        calls += 1
        assert timeout_seconds > 0
        return _inspection(root)

    with pytest.raises(
        PersistentEvidenceChainV2ImplementationError,
        match="artifact is absent",
    ):
        invoke_lease_bound_host_runtime(
            root,
            chain,
            lease,
            host_resources=_resources(),
            process_spawner=_FakeSpawner(_FakeProcess()),
            image_inspector=inspect,
            signal_sender=lambda _pid, _signum: None,
            clock=_Clock(),
        )
    assert calls == 0
    assert not (root / DURABLE_HOST_OUTCOME_RELATIVE).exists()


def test_success_persists_full_stream_hashes_once(tmp_path: Path) -> None:
    root = _sandbox(tmp_path)
    chain, lease = _lease(root)
    persist_persistent_execution_lease_v2(root, chain, lease)
    stdout = b"completed\n"
    stderr = b"warning\n"
    spawner = _FakeSpawner(_FakeProcess(stdout=stdout, stderr=stderr))
    inspection = _inspection(root)
    result = invoke_lease_bound_host_runtime(
        root,
        chain,
        lease,
        host_resources=_resources(),
        process_spawner=spawner,
        image_inspector=lambda _root, timeout_seconds: inspection,
        signal_sender=lambda _pid, _signum: None,
        clock=_Clock(),
    )
    assert spawner.calls == 1
    assert result.receipt.termination_class == "success"
    assert result.receipt.stdout_sha256 == sha256_bytes(stdout)
    assert result.receipt.stderr_sha256 == sha256_bytes(stderr)
    assert result.receipt.stdout_total_bytes == len(stdout)
    assert result.receipt.stderr_total_bytes == len(stderr)
    assert result.host_outcome is not None
    assert result.terminal_error is None
    assert (root / DURABLE_HOST_OUTCOME_RELATIVE).read_text(
        encoding="utf-8"
    ) == result.receipt.canonical_json()


def test_spawn_failure_persists_terminal_receipt_without_retry(tmp_path: Path) -> None:
    root = _sandbox(tmp_path)
    chain, lease = _lease(root)
    persist_persistent_execution_lease_v2(root, chain, lease)
    spawner = _FakeSpawner()
    inspection = _inspection(root)
    result = invoke_lease_bound_host_runtime(
        root,
        chain,
        lease,
        host_resources=_resources(),
        process_spawner=spawner,
        image_inspector=lambda _root, timeout_seconds: inspection,
        signal_sender=lambda _pid, _signum: None,
        clock=_Clock(),
    )
    assert spawner.calls == 1
    assert result.receipt.termination_class == "spawn_failed"
    assert result.receipt.child_spawn_count == 0
    assert result.host_outcome is None
    assert result.terminal_error is not None


def test_prelaunch_rejection_persists_terminal_receipt(tmp_path: Path) -> None:
    root = _sandbox(tmp_path)
    chain, lease = _lease(root)
    persist_persistent_execution_lease_v2(root, chain, lease)

    def reject(_root: Path, *, timeout_seconds: float) -> LocalImageInspection:
        assert timeout_seconds > 0
        raise RuntimeError("synthetic inspection rejection")

    spawner = _FakeSpawner(_FakeProcess())
    result = invoke_lease_bound_host_runtime(
        root,
        chain,
        lease,
        host_resources=_resources(),
        process_spawner=spawner,
        image_inspector=reject,
        signal_sender=lambda _pid, _signum: None,
        clock=_Clock(),
    )
    assert spawner.calls == 0
    assert result.receipt.termination_class == "prelaunch_rejected"
    assert result.receipt.child_spawn_count == 0


def test_truncated_capture_retains_full_stream_digest(tmp_path: Path) -> None:
    root = _sandbox(tmp_path)
    chain, lease = _lease(root)
    persist_persistent_execution_lease_v2(root, chain, lease)
    payload = b"x" * (1_048_576 + 100)
    inspection = _inspection(root)
    result = invoke_lease_bound_host_runtime(
        root,
        chain,
        lease,
        host_resources=_resources(),
        process_spawner=_FakeSpawner(_FakeProcess(stdout=payload)),
        image_inspector=lambda _root, timeout_seconds: inspection,
        signal_sender=lambda _pid, _signum: None,
        clock=_Clock(),
    )
    assert result.receipt.stdout_sha256 == sha256_bytes(payload)
    assert result.receipt.stdout_total_bytes == len(payload)
    assert result.receipt.stdout_truncated is True
    assert result.receipt.stdout_captured_bytes < len(payload)


def test_invalid_output_snapshot_persists_prelaunch_rejection(
    tmp_path: Path,
) -> None:
    root = _sandbox(tmp_path)
    chain, lease = _lease(root)
    persist_persistent_execution_lease_v2(root, chain, lease)
    outside = tmp_path / "outside"
    outside.mkdir()
    output = root / chain.source.output_root
    output.symlink_to(outside, target_is_directory=True)
    spawner = _FakeSpawner(_FakeProcess())
    result = invoke_lease_bound_host_runtime(
        root,
        chain,
        lease,
        host_resources=_resources(),
        process_spawner=spawner,
        image_inspector=lambda _root, timeout_seconds: _inspection(root),
        signal_sender=lambda _pid, _signum: None,
        clock=_Clock(),
    )
    assert spawner.calls == 0
    assert result.receipt.termination_class == "prelaunch_rejected"
    assert result.receipt.output_before.present is True
    assert result.terminal_error is not None
    assert (root / DURABLE_HOST_OUTCOME_RELATIVE).is_file()


def test_existing_outcome_blocks_invocation(tmp_path: Path) -> None:
    root = _sandbox(tmp_path)
    chain, lease = _lease(root)
    persist_persistent_execution_lease_v2(root, chain, lease)
    target = root / DURABLE_HOST_OUTCOME_RELATIVE
    target.write_text("occupied\n", encoding="utf-8")
    spawner = _FakeSpawner(_FakeProcess())
    with pytest.raises(LeaseBoundHostInvokerWiringError, match="already exists"):
        invoke_lease_bound_host_runtime(
            root,
            chain,
            lease,
            host_resources=_resources(),
            process_spawner=spawner,
            image_inspector=lambda _root, timeout_seconds: _inspection(root),
            signal_sender=lambda _pid, _signum: None,
            clock=_Clock(),
        )
    assert spawner.calls == 0


def test_wiring_source_has_one_popen_and_no_import_time_execution() -> None:
    path = (
        ROOT
        / "src/torch2pc_thesis/"
        "stage3b_qwake_lc4_lease_bound_host_invoker_wiring.py"
    )
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    popen_calls = sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "subprocess"
        and node.func.attr == "Popen"
    )
    direct_calls = sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "invoke_one_shot_host_runtime"
    )
    assert popen_calls == 1
    assert direct_calls == 1
    assert "subprocess.run(" not in source
    assert "if __name__" not in source
