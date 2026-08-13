from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from torch2pc_thesis.stage3b_qwake_scientific_identity_v2 import (
    RUNTIME_MANIFEST_RELATIVE_ENV,
    RUNTIME_MANIFEST_RELATIVE_LABEL,
    RUNTIME_MANIFEST_SHA256_ENV,
    RUNTIME_MANIFEST_SHA256_LABEL,
    SOURCE_COMMIT_ENV,
    SOURCE_COMMIT_LABEL,
    ScientificRuntimeIdentity,
    ScientificRuntimeIdentityError,
    runtime_identity_from_image_inspection,
    verify_runtime_manifest,
)

SHA_A = "sha256:" + "a" * 64
SHA_B = "sha256:" + "b" * 64
COMMIT = "1" * 40
ROOT = Path(__file__).resolve().parents[2]
ACTIVE_MANIFEST = Path(
    "experiments/runtime/stage3b-qwake-scientific-successor-v1/runtime-SHA256SUMS"
)


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _load_host():
    path = ROOT / "scripts/run_stage3b_qwake_scientific_campaign_host_v2.py"
    spec = importlib.util.spec_from_file_location("qwake_arch_host_subject", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_legacy_host():
    path = ROOT / "scripts/run_stage3b_qwake_scientific_campaign_host.py"
    spec = importlib.util.spec_from_file_location("qwake_arch_legacy_host_subject", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _image(runtime_sha: str = SHA_B) -> dict[str, object]:
    relative = ACTIVE_MANIFEST.as_posix()
    return {
        "Id": SHA_A,
        "Config": {
            "Labels": {
                SOURCE_COMMIT_LABEL: COMMIT,
                RUNTIME_MANIFEST_RELATIVE_LABEL: relative,
                RUNTIME_MANIFEST_SHA256_LABEL: runtime_sha,
            },
            "Env": [
                f"{SOURCE_COMMIT_ENV}={COMMIT}",
                "SOURCE_GIT_COMMIT=LEGACY_HOST_REJECTED_BY_SUCCESSOR_V2",
                f"{RUNTIME_MANIFEST_RELATIVE_ENV}={relative}",
                f"{RUNTIME_MANIFEST_SHA256_ENV}={runtime_sha}",
            ],
        },
    }


def test_image_metadata_is_single_runtime_identity_source() -> None:
    identity = runtime_identity_from_image_inspection(
        _image(),
        expected_image_digest=SHA_A,
        expected_source_commit=COMMIT,
        expected_code_manifest_sha256=SHA_B,
    )
    assert identity == ScientificRuntimeIdentity(ACTIVE_MANIFEST.as_posix(), SHA_B)

    with pytest.raises(
        ScientificRuntimeIdentityError,
        match="request runtime-manifest digest differs from immutable image",
    ):
        runtime_identity_from_image_inspection(
            _image(),
            expected_image_digest=SHA_A,
            expected_source_commit=COMMIT,
            expected_code_manifest_sha256="sha256:" + "c" * 64,
        )


def test_active_manifest_is_attempt_independent_and_exact() -> None:
    manifest = ROOT / ACTIVE_MANIFEST
    identity = ScientificRuntimeIdentity(ACTIVE_MANIFEST.as_posix(), _sha(manifest))
    paths = verify_runtime_manifest(ROOT, identity)
    assert len(paths) == 15
    assert "src/torch2pc_thesis/stage3b_qwake_scientific_identity_v2.py" in paths
    assert "scripts/verify_stage3b_qwake_scientific_runtime_identity_v2.py" in paths
    assert "attempt-001" not in identity.relative_path
    assert "attempt-002" not in identity.relative_path
    assert "attempt-003" not in identity.relative_path


def test_production_runtime_has_no_versioned_manifest_selector() -> None:
    runtime = (ROOT / "src/torch2pc_thesis/stage3b_qwake_scientific_runtime_v2.py").read_text(
        encoding="utf-8"
    )
    assert "stage3b-qwake-c1-train-only-dataset-isolation-correction-v1" not in runtime
    assert "_RUNTIME_MANIFEST_RELATIVE" not in runtime
    assert "runtime_identity_from_environment" in runtime
    assert "preflight_scientific_campaign" in runtime


def test_docker_build_contract_has_no_attempt003_wiring_and_bakes_identity() -> None:
    dockerfile = (ROOT / "Dockerfile.qwake-scientific").read_text(encoding="utf-8")
    assert "stage3b-qwake-attempt-003" not in dockerfile
    assert "QWAKE_RUNTIME_MANIFEST_RELATIVE" in dockerfile
    assert "QWAKE_RUNTIME_MANIFEST_SHA256" in dockerfile
    assert RUNTIME_MANIFEST_RELATIVE_LABEL in dockerfile
    assert RUNTIME_MANIFEST_SHA256_LABEL in dockerfile
    assert "requirements/qwake-scientific-runtime.txt" in dockerfile
    assert "requirements/rocm.txt" not in dockerfile
    assert "QWAKE_SCIENTIFIC_SOURCE_COMMIT_V2=${SOURCE_GIT_COMMIT}" in dockerfile
    assert "SOURCE_GIT_COMMIT=LEGACY_HOST_REJECTED_BY_SUCCESSOR_V2" in dockerfile


def test_host_claim_occurs_only_after_shared_preclaim_and_command_materialization() -> None:
    source = (ROOT / "scripts/run_stage3b_qwake_scientific_campaign_host_v2.py").read_text(
        encoding="utf-8"
    )
    main = source.index("def main()")
    commit_binding = source.index("_require_commit_bound_runtime_closure(", main)
    preclaim = source.index("preflight_scientific_campaign(", commit_binding)
    stage = source.index("_materialize_exact_input_stage(", preclaim)
    command = source.index("command = _docker_command(", stage)
    claim = source.index("output_root.mkdir(", command)
    docker_run = source.index("invoked = _run(command", claim)
    assert commit_binding < preclaim < stage < command < claim < docker_run
    assert "output_root.parent.mkdir" not in source
    assert "CLAIM_IS_FINAL_ADMISSION_TRANSITION=true" in source
    assert "dataset.dataset_root" not in source


def test_exact_input_stage_excludes_unbound_sibling_test_resource(tmp_path: Path) -> None:
    host = _load_host()
    split = tmp_path / "results/splits/frozen.npz"
    sibling_split = tmp_path / "results/splits/FashionMNIST_test_seed1042_subsetall.npz"
    train_images = tmp_path / "data/FashionMNIST/raw/train-images-idx3-ubyte"
    train_labels = tmp_path / "data/FashionMNIST/raw/train-labels-idx1-ubyte"
    sibling_test = tmp_path / "data/FashionMNIST/raw/t10k-images-idx3-ubyte"
    for path, raw in (
        (split, b"split"),
        (sibling_split, b"test-split"),
        (train_images, b"images"),
        (train_labels, b"labels"),
        (sibling_test, b"test"),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)

    request = SimpleNamespace(
        dataset=SimpleNamespace(
            split=SimpleNamespace(
                relative_path="results/splits/frozen.npz",
                sha256=_sha(split),
            ),
            dataset_assets=(
                SimpleNamespace(
                    relative_path="data/FashionMNIST/raw/train-images-idx3-ubyte",
                    sha256=_sha(train_images),
                ),
                SimpleNamespace(
                    relative_path="data/FashionMNIST/raw/train-labels-idx1-ubyte",
                    sha256=_sha(train_labels),
                ),
            ),
        ),
        sealed_c1_dataset=None,
        candidate_policies=(),
        frozen_policy=None,
        predecessor_receipts=(),
    )

    stage = tmp_path / "stage"
    stage.mkdir()
    mounts = host._materialize_exact_input_stage(tmp_path, request, stage)

    observed = {
        path.relative_to(stage).as_posix()
        for path in stage.rglob("*")
        if path.is_file()
    }
    assert observed == {
        "results/splits/frozen.npz",
        "data/FashionMNIST/raw/train-images-idx3-ubyte",
        "data/FashionMNIST/raw/train-labels-idx1-ubyte",
    }
    assert not (stage / "results/splits/FashionMNIST_test_seed1042_subsetall.npz").exists()
    assert not (stage / "data/FashionMNIST/raw/t10k-images-idx3-ubyte").exists()
    assert {container.as_posix() for _host, container in mounts} == {
        "/workspace/data/FashionMNIST/raw",
        "/workspace/results/splits",
    }
    assert all(str(host_path).startswith(str(stage)) for host_path, _container in mounts)


def test_builder_uses_explicit_rocm_dockerfile_and_read_only_runtime_dirs() -> None:
    builder = (ROOT / "scripts/build_stage3b_qwake_scientific_image_v2.py").read_text(
        encoding="utf-8"
    )
    dockerfile = (ROOT / "Dockerfile.qwake-scientific").read_text(encoding="utf-8")
    assert '"--file",\n                "Dockerfile.qwake-scientific"' in builder
    assert "rocm/pytorch@sha256:96a2fb24" in builder
    assert "base image must be pinned by repository digest" in builder
    assert "_require_commit_bound_sources(" in builder
    assert '"git", "ls-files", "--error-unmatch"' in builder
    assert '"git", "diff", "--name-only"' in builder
    assert "mkdir -p /workspace/results /workspace/data /workspace/external" in dockerfile
    assert "rocm/pytorch@sha256:96a2fb24" in dockerfile
    assert "--read-only" in builder
    assert "verify_stage3b_qwake_scientific_runtime_identity_v2.py" in builder




def test_successor_image_is_rejected_by_legacy_host_before_claim(monkeypatch: pytest.MonkeyPatch) -> None:
    legacy = _load_legacy_host()
    inspected = json.dumps([_image()]).encode("utf-8")
    monkeypatch.setattr(legacy, "_require_run", lambda *args, **kwargs: inspected)
    request = SimpleNamespace(image_digest=SHA_A, source_commit=COMMIT)
    with pytest.raises(legacy.ScientificHostLaunchError, match="Docker SOURCE_GIT_COMMIT differs"):
        legacy._require_exact_local_image("docker", ROOT, request)


def test_in_image_verifier_imports_exact_production_entrypoint() -> None:
    source = (
        ROOT / "scripts/verify_stage3b_qwake_scientific_runtime_identity_v2.py"
    ).read_text(encoding="utf-8")
    assert "runpy.run_path(" in source
    assert "scripts/run_stage3b_qwake_scientific_campaign_v2.py" in source
    assert "QWAKE_PRODUCTION_ENTRYPOINT_IMPORT_PREFLIGHT=PASS" in source

def test_request_freezer_derives_runtime_identity_from_image_truth() -> None:
    source = (
        ROOT / "scripts/freeze_stage3b_qwake_scientific_request_from_image_v2.py"
    ).read_text(encoding="utf-8")
    assert "runtime_identity_from_image_inspection" in source
    assert 'request["code_manifest_sha256"] = runtime_identity.sha256' in source
    assert "RUNTIME_SOURCE_MANIFEST_SHA256" not in source


def test_terminal_verifier_is_preissued_for_success_and_consumed_failure() -> None:
    source = (
        ROOT / "scripts/verify_stage3b_qwake_scientific_terminal_outcome_v2.py"
    ).read_text(encoding="utf-8")
    assert 'output / "receipt.json"' in source
    assert 'output / "host-outcome.json"' in source
    assert "terminal_consumed_failure" in source
    assert "scientific_execution_sealed" in source


def test_architecture_authoring_performs_no_execution_effect() -> None:
    # Guard the patch itself: build/run tooling is authored but this test suite
    # never invokes Docker, creates scientific authorization, or touches results.
    assert not (ROOT / "results/scientific/C1_COLLECTION/host-claim.json").exists()
    assert os.environ.get("QWAKE_ARCHITECTURE_AUTHORING_DOCKER_RUN") is None


def test_historical_frozen_production_bytes_remain_unchanged() -> None:
    expected = {
        ".dockerignore": "a009b4543334acacef670ca39c4d080f7f5a26770df7e9a7253ceea5597b282e",
        "Dockerfile.rocm": "2db033d60ae5a5a6f060f84457e48dbb2b0874f5df3a3128becef90b762ba946",
        "scripts/run_stage3b_qwake_scientific_campaign_host.py": "dc72616b0b0fa88c5945eabce2b55bb1f55c386b7ea98b6081b1838f9f56efec",
        "src/torch2pc_thesis/stage3b_qwake_scientific_runtime.py": "b796c49418dfb2adc3b07693a33328875396df173511bc92105c4a5a41dadd34",
        "tests/unit/test_stage3b_qwake_scientific_campaign.py": "193f748efed5b72f652eccfa9579afd752f507412bded855b191d60920b9dc33",
    }
    for relative, digest in expected.items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest
