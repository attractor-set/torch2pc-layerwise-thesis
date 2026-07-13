from __future__ import annotations

import hashlib

from torch2pc_thesis.manifests import directory_manifest, environment_snapshot


def test_environment_snapshot_uses_explicit_environment_lock(tmp_path, monkeypatch) -> None:
    lock = tmp_path / "environment-lock.json"
    lock.write_text('{"stage": "final_stage_2"}\n', encoding="utf-8")
    monkeypatch.setattr(
        "torch2pc_thesis.manifests.command_output",
        lambda _command: "observed",
    )

    snapshot = environment_snapshot(lock)

    assert snapshot["environment_lock_sha256"] == hashlib.sha256(lock.read_bytes()).hexdigest()


def test_environment_snapshot_reads_environment_lock_from_env(tmp_path, monkeypatch) -> None:
    lock = tmp_path / "environment-lock.json"
    lock.write_text('{"stage": "final_stage_2"}\n', encoding="utf-8")
    monkeypatch.setenv("ENVIRONMENT_LOCK_PATH", str(lock))
    monkeypatch.setattr(
        "torch2pc_thesis.manifests.command_output",
        lambda _command: "observed",
    )

    snapshot = environment_snapshot()

    assert snapshot["environment_lock_sha256"] == hashlib.sha256(lock.read_bytes()).hexdigest()


def test_directory_manifest_excludes_output_file(tmp_path) -> None:
    artifact = tmp_path / "artifact.txt"
    output = tmp_path / "results_manifest.json"
    artifact.write_text("payload\n", encoding="utf-8")
    output.write_text("old manifest\n", encoding="utf-8")

    manifest = directory_manifest(tmp_path, exclude_paths=(output,))

    assert [item["path"] for item in manifest["files"]] == ["artifact.txt"]
