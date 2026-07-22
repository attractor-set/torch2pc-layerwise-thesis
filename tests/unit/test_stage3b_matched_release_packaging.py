from __future__ import annotations

import json
import tarfile
from pathlib import Path

import pytest

from torch2pc_thesis.stage3b_matched_release import (
    MATCHED_RELEASE_TAG,
    MATCHED_RESULT_ROOT,
    Stage3BMatchedReleaseError,
    package_matched_release,
    sha256_file,
)

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/stage3b-matched-evidence-release.yml"


def test_repository_release_package_is_draft_only_and_self_verifying(
    tmp_path: Path,
) -> None:
    output = tmp_path / "release"
    result = package_matched_release(
        ROOT,
        output,
        tag=MATCHED_RELEASE_TAG,
        mode="repository",
        release_commit="f" * 40,
    )

    assert result["status"] == "draft_only"
    assert result["packaging_mode"] == "repository"
    assert result["results_publication_permitted"] is False
    assert result["release_publication_permitted"] is False

    expected = {
        "stage3b-matched-profiling-sealed-evidence-v1.tar.gz",
        "stage3b-matched-profiling-locality-events-v1.jsonl.zst",
        "RELEASE-NOTES.md",
        "RELEASE-MANIFEST.json",
        "SHA256SUMS",
    }
    assert {path.name for path in output.iterdir()} == expected

    manifest = json.loads((output / "RELEASE-MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "draft_only"
    assert manifest["release_tag"] == MATCHED_RELEASE_TAG
    assert manifest["release_commit"] == "f" * 40
    assert manifest["packaging_mode"] == "repository"
    assert manifest["matched_cell_count"] == 288
    assert manifest["matched_block_count"] == 96
    assert manifest["release_publication_permitted"] is False

    registry = (output / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    assert len(registry) == 4
    for line in registry:
        digest, name = line.split(maxsplit=1)
        assert sha256_file(output / name) == digest

    archive = output / "stage3b-matched-profiling-sealed-evidence-v1.tar.gz"
    with tarfile.open(archive, mode="r:gz") as handle:
        names = set(handle.getnames())
    assert any(name.endswith("/seal.json") for name in names)
    assert any(name.endswith("/SHA256SUMS") for name in names)
    assert any(name.endswith("/SEALED-SHA256SUMS") for name in names)
    assert any(name.endswith("/locality_events.asset.json") for name in names)
    assert not any(name.endswith("/locality_events.jsonl.zst") for name in names)
    assert len(names) == len(tuple((ROOT / MATCHED_RESULT_ROOT).iterdir())) - 1

    locality = output / "stage3b-matched-profiling-locality-events-v1.jsonl.zst"
    assert locality.is_file()
    assert locality.stat().st_size < 100_000_000


def test_release_packager_rejects_wrong_tag(tmp_path: Path) -> None:
    with pytest.raises(Stage3BMatchedReleaseError, match="unexpected release tag"):
        package_matched_release(
            ROOT,
            tmp_path / "release",
            tag="wrong-tag",
            mode="repository",
            release_commit="f" * 40,
        )


def test_release_workflow_creates_only_a_draft_release() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert '"stage3b-matched-profiling-evidence-v1"' in text
    assert "permissions:\n  contents: write" in text
    assert "--mode repository" in text
    assert "gh release create" in text
    assert "--draft" in text
    assert "gh release upload" in text
    assert "--clobber" in text
    assert 'gh release edit "$GITHUB_REF_NAME" --draft --latest=false' in text
    assert "--draft=false" not in text
    assert "--latest=false" in text


def test_full_release_package_includes_verified_run_artifacts(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime"
    runtime_root.mkdir()
    for name, content in (
        ("CONTROL-INVENTORY.sha256", "control\n"),
        ("DRY-RUN-INVENTORY.sha256", "dry-run\n"),
        ("EXECUTION-INVENTORY.sha256", "execution\n"),
        ("SEALED-CHECKPOINT.sha256", "sealed\n"),
        ("authorization.json", "{}\n"),
    ):
        (runtime_root / name).write_text(content, encoding="utf-8")
    plan = runtime_root / "plans/dry-run.json"
    plan.parent.mkdir()
    plan.write_text("{}\n", encoding="utf-8")
    measurement = runtime_root / "matched/lanes/rocm-float32/cells/cell-0/measurements.json"
    measurement.parent.mkdir(parents=True)
    measurement.write_text("{}\n", encoding="utf-8")

    image_root = tmp_path / "image"
    image_root.mkdir()
    image_registry = image_root / "SHA256SUMS"
    image_registry.write_text("image\n", encoding="utf-8")

    sealing_root = tmp_path / "sealing"
    sealing_root.mkdir()
    sealing_log = sealing_root / "seal.log"
    sealing_log.write_text("sealed\n", encoding="utf-8")
    sealing_registry = sealing_root / "LOG-SHA256SUMS"
    sealing_registry.write_text(
        f"{sha256_file(sealing_log)}  {sealing_log.name}\n",
        encoding="utf-8",
    )

    source_record = tmp_path / "release-source-record.json"
    record = {
        "status": "prepared_not_published",
        "intended_release_tag": MATCHED_RELEASE_TAG,
        "source_commit": (
            "e1dcfb26823e1191b98d2aa2a598499b13197583"
        ),
        "image_digest": (
            "sha256:3c269b4278026b5b69968b3265b506ce626f2baf693859989de3371d639da4d0"
        ),
        "runtime_root": str(runtime_root),
        "image_checkpoint_registry_path": str(image_registry),
        "sealing_log_registry_path": str(sealing_registry),
        "sealed_checkpoint_sha256": sha256_file(
            runtime_root / "SEALED-CHECKPOINT.sha256"
        ),
        "control_inventory_sha256": sha256_file(
            runtime_root / "CONTROL-INVENTORY.sha256"
        ),
        "dry_run_inventory_sha256": sha256_file(
            runtime_root / "DRY-RUN-INVENTORY.sha256"
        ),
        "execution_inventory_sha256": sha256_file(
            runtime_root / "EXECUTION-INVENTORY.sha256"
        ),
        "image_checkpoint_registry_sha256": sha256_file(image_registry),
        "sealing_log_registry_sha256": sha256_file(sealing_registry),
        "release_publication_permitted": False,
    }
    source_record.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    source_record.with_suffix(".json.sha256").write_text(
        f"{sha256_file(source_record)}  {source_record.name}\n",
        encoding="utf-8",
    )

    output = tmp_path / "full-release"
    result = package_matched_release(
        ROOT,
        output,
        tag=MATCHED_RELEASE_TAG,
        mode="full",
        release_commit="f" * 40,
        release_source_record=source_record,
    )

    assert result["packaging_mode"] == "full"
    expected = {
        "stage3b-matched-profiling-sealed-evidence-v1.tar.gz",
        "stage3b-matched-profiling-locality-events-v1.jsonl.zst",
        "stage3b-matched-profiling-release-source-record-v1.json",
        "stage3b-matched-profiling-control-plane-v1.tar.gz",
        "stage3b-matched-profiling-runtime-records-v1.tar.gz",
        "stage3b-matched-profiling-image-checkpoint-v1.tar.gz",
        "stage3b-matched-profiling-sealing-logs-v1.tar.gz",
        "RELEASE-NOTES.md",
        "RELEASE-MANIFEST.json",
        "SHA256SUMS",
    }
    assert {path.name for path in output.iterdir()} == expected

    control = output / "stage3b-matched-profiling-control-plane-v1.tar.gz"
    with tarfile.open(control, mode="r:gz") as handle:
        control_names = set(handle.getnames())
    assert any(name.endswith("/authorization.json") for name in control_names)
    assert any(name.endswith("/plans/dry-run.json") for name in control_names)
    assert not any("/cells/" in name for name in control_names)

    runtime = output / "stage3b-matched-profiling-runtime-records-v1.tar.gz"
    with tarfile.open(runtime, mode="r:gz") as handle:
        runtime_names = set(handle.getnames())
    assert any(name.endswith("/cells/cell-0/measurements.json") for name in runtime_names)
    assert not any(name.endswith("/locality-events.jsonl") for name in runtime_names)
