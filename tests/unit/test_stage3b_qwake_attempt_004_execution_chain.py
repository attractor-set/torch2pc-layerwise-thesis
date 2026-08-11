from __future__ import annotations

import ast
import importlib.util
import json
import subprocess
from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest

from torch2pc_thesis.stage3b_qwake_attempt_004_contract import (
    ATTEMPT_004_HOST_COMMAND_RELATIVE,
    ATTEMPT_004_ID,
    ATTEMPT_004_INVOCATION_ACKNOWLEDGEMENT,
    ATTEMPT_004_LEASE_ACKNOWLEDGEMENT,
    ATTEMPT_004_LEASE_V1_RELATIVE,
    ATTEMPT_004_OUTPUT_ROOT,
    EXPECTED_GENERIC_RUNTIME_BACKEND_SHA256,
    EXPECTED_SCIENTIFIC_AUTHORIZATION_SHA256,
    EXPECTED_TORCH2PC_COMMIT,
    Attempt004AdmissionIdentity,
    Attempt004ContractError,
)
from torch2pc_thesis.stage3b_qwake_attempt_004_cpu_measurement_stabilization import (
    Attempt004CPUStabilizedMatrixExecutor,
)
from torch2pc_thesis.stage3b_qwake_attempt_004_execution_wrapper import (
    Attempt004ExecutionBackend,
    Attempt004ExecutionWrapperError,
    build_attempt_004_backend_receipt,
    build_attempt_004_lease,
    materialize_attempt_004_lease,
    run_claimed_attempt_004,
)
from torch2pc_thesis.stage3b_qwake_attempt_004_runtime_backend import (
    Attempt004RuntimeBackend,
)

ROOT = Path(__file__).resolve().parents[2]
HOST = ROOT / "scripts/run_stage3b_qwake_attempt_004_host_one_shot.py"
GENERIC = ROOT / "src/torch2pc_thesis/stage3b_qwake_lc4_runtime_backend.py"


def _admission() -> Attempt004AdmissionIdentity:
    admission = Attempt004AdmissionIdentity(
        attempt_id=ATTEMPT_004_ID,
        freeze_sha256="sha256:" + "1" * 64,
        authorization_sha256="sha256:" + "2" * 64,
        source_commit="3" * 40,
        wrapper_commit="3" * 40,
        torch2pc_commit=EXPECTED_TORCH2PC_COMMIT,
        image_digest="sha256:" + "4" * 64,
        image_repo_digest="",
        scientific_authorization_sha256=(
            EXPECTED_SCIENTIFIC_AUTHORIZATION_SHA256
        ),
        output_root=ATTEMPT_004_OUTPUT_ROOT.as_posix(),
        lease_v1_relative=ATTEMPT_004_LEASE_V1_RELATIVE.as_posix(),
        lease_v2_relative=(
            ATTEMPT_004_OUTPUT_ROOT.as_posix() + ".execution-lease-v2.json"
        ),
        durable_outcome_relative=(
            ATTEMPT_004_OUTPUT_ROOT.as_posix() + ".host-outcome.json"
        ),
        execution_count=1,
        runtime_execution_permitted=True,
        authorization_consumed=False,
        attempt_started=False,
        retry_permitted=False,
    )
    admission.require()
    return admission


def test_generic_runtime_backend_remains_historical() -> None:
    import hashlib

    observed = "sha256:" + hashlib.sha256(GENERIC.read_bytes()).hexdigest()
    assert observed == EXPECTED_GENERIC_RUNTIME_BACKEND_SHA256


def test_backend_defaults_to_cpu_stabilized_executor(tmp_path: Path) -> None:
    backend = Attempt004RuntimeBackend(
        project_root=tmp_path,
        torch2pc_dir=tmp_path / "external/Torch2PC",
        execution_freeze=cast(object, object()),
    )
    assert isinstance(
        backend.matrix_executor,
        Attempt004CPUStabilizedMatrixExecutor,
    )


def test_lease_is_one_shot_and_no_replace(tmp_path: Path) -> None:
    admission = _admission()
    lease = build_attempt_004_lease(
        admission,
        claimed_at_utc="2026-08-10T23:30:00Z",
        wrapper_commit=admission.wrapper_commit,
        operator_acknowledgement=ATTEMPT_004_LEASE_ACKNOWLEDGEMENT,
    )
    materialize_attempt_004_lease(tmp_path, lease, admission)

    assert (tmp_path / ATTEMPT_004_LEASE_V1_RELATIVE).is_file()
    assert lease.authorization_consumed is True
    assert lease.attempt_started is True
    assert lease.runtime_execution_started is False
    assert lease.runtime_execution_performed is False
    assert lease.retry_permitted is False

    with pytest.raises(Attempt004ExecutionWrapperError):
        materialize_attempt_004_lease(tmp_path, lease, admission)


def test_wrapper_promotes_complete_output_once(tmp_path: Path) -> None:
    admission = _admission()
    lease = build_attempt_004_lease(
        admission,
        claimed_at_utc="2026-08-10T23:30:00Z",
        wrapper_commit=admission.wrapper_commit,
        operator_acknowledgement=ATTEMPT_004_LEASE_ACKNOWLEDGEMENT,
    )
    materialize_attempt_004_lease(tmp_path, lease, admission)

    class Backend:
        backend_id = "attempt004-test-backend"

        def run(self, staging_root: Path, lease_arg: object, contract: object):
            target = staging_root / "evidence.json"
            target.write_text('{"ok":true}\n', encoding="utf-8")
            return build_attempt_004_backend_receipt(
                backend_id=self.backend_id,
                lease=cast(type(lease), lease_arg),
                contract=cast(object, contract),
                output_file_count=1,
            )

    outcome = run_claimed_attempt_004(
        tmp_path,
        admission,
        lease,
        backend=cast(Attempt004ExecutionBackend, Backend()),
    )
    assert outcome.output_root == tmp_path / ATTEMPT_004_OUTPUT_ROOT
    assert (outcome.output_root / "evidence.json").is_file()
    assert (outcome.output_root / "execution-wrapper-receipt.json").is_file()

    with pytest.raises(Attempt004ExecutionWrapperError):
        run_claimed_attempt_004(
            tmp_path,
            admission,
            lease,
            backend=cast(Attempt004ExecutionBackend, Backend()),
        )


def test_host_spawner_has_exact_single_spawn_and_fixed_cpu_profile() -> None:
    source = HOST.read_text(encoding="utf-8")
    tree = ast.parse(source)

    popen_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "subprocess"
        and node.func.attr == "Popen"
    ]
    assert len(popen_calls) == 1

    call = popen_calls[0]
    keywords = {item.arg: item.value for item in call.keywords if item.arg}
    assert isinstance(keywords["shell"], ast.Constant)
    assert keywords["shell"].value is False
    assert isinstance(keywords["start_new_session"], ast.Constant)
    assert keywords["start_new_session"].value is True
    assert isinstance(keywords["close_fds"], ast.Constant)
    assert keywords["close_fds"].value is True

    assert '"--cpuset-cpus"' in source
    assert 'CPUSET_CPUS: Final = "0"' in source
    assert '("QWAKE_ATTEMPT_004_CPU_STABILIZATION", "1")' in source
    for name in (
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        assert f'("{name}", "1")' in source

    assert "automatic_retry_performed" in source
    assert 'image_digest = record.get("Id")' in source
    assert 'repo_digest = matching[0] if matching else ""' in source
    assert "freeze.image_digest," in source
    assert "automatic_retry_permitted" in source
    assert '["git", "reset"' not in source
    assert '["git", "clean"' not in source
    assert "git push --force" not in source


def test_host_command_is_distinct_from_authorization() -> None:
    assert ATTEMPT_004_HOST_COMMAND_RELATIVE.as_posix().endswith(
        ".host-command.json"
    )
    assert ATTEMPT_004_INVOCATION_ACKNOWLEDGEMENT == (
        "AUTHORIZE_QWAKE_LC4_ATTEMPT_004_ONE_SHOT_ENGINEERING_INVOCATION"
    )
    assert ATTEMPT_004_LEASE_ACKNOWLEDGEMENT == (
        "CLAIM_QWAKE_LC4_ATTEMPT_004_FROM_CPU_STABILIZED_EXECUTION_FREEZE"
    )

def test_repo_digest_is_optional_observational_identity() -> None:
    admission = _admission()
    replace(
        admission,
        image_repo_digest="torch2pc-layerwise-thesis@sha256:" + "5" * 64,
    ).require()

    with pytest.raises(Attempt004ContractError):
        replace(admission, image_repo_digest="not-a-repo-digest").require()


def _load_host_module():
    spec = importlib.util.spec_from_file_location(
        "attempt004_host_one_shot_test_module",
        HOST,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_image_uses_local_image_id_without_repo_digest(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    host = _load_host_module()
    source_commit = "3" * 40
    image_id = "sha256:" + "4" * 64
    inspection = [
        {
            "Id": image_id,
            "RepoDigests": [],
            "Config": {
                "Labels": {
                    "org.opencontainers.image.revision": source_commit,
                    "io.torch2pc.base-image": host.BASE_IMAGE,
                }
            },
        }
    ]

    monkeypatch.setattr(host.shutil, "which", lambda name: "/usr/bin/docker")
    monkeypatch.setattr(
        host,
        "_run",
        lambda argv, cwd, env=None: subprocess.CompletedProcess(
            argv,
            0,
            stdout=b"build-ok\n",
        ),
    )
    monkeypatch.setattr(
        host,
        "_require_command",
        lambda argv, cwd, label, env=None: json.dumps(inspection).encode(),
    )

    observed_id, repo_digest, _, _ = host._build_image(
        tmp_path,
        source_commit,
    )
    assert observed_id == image_id
    assert repo_digest == ""


def test_repo_digest_does_not_redefine_local_image_id(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    host = _load_host_module()
    source_commit = "3" * 40
    image_id = "sha256:" + "4" * 64
    repo_digest = "torch2pc-layerwise-thesis@sha256:" + "5" * 64
    inspection = [
        {
            "Id": image_id,
            "RepoDigests": [repo_digest],
            "Config": {
                "Labels": {
                    "org.opencontainers.image.revision": source_commit,
                    "io.torch2pc.base-image": host.BASE_IMAGE,
                }
            },
        }
    ]

    monkeypatch.setattr(host.shutil, "which", lambda name: "/usr/bin/docker")
    monkeypatch.setattr(
        host,
        "_run",
        lambda argv, cwd, env=None: subprocess.CompletedProcess(
            argv,
            0,
            stdout=b"build-ok\n",
        ),
    )
    monkeypatch.setattr(
        host,
        "_require_command",
        lambda argv, cwd, label, env=None: json.dumps(inspection).encode(),
    )

    observed_id, observed_repo_digest, _, _ = host._build_image(
        tmp_path,
        source_commit,
    )
    assert observed_id == image_id
    assert observed_repo_digest == repo_digest
    assert observed_id.removeprefix("sha256:") not in observed_repo_digest
