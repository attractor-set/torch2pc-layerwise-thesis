from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast


class AssetManifestError(RuntimeError):
    pass


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json_object(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    if not source.exists():
        raise AssetManifestError(f"Required JSON artifact is missing: {source}")
    value = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssetManifestError(f"JSON artifact must contain an object: {source}")
    return cast(dict[str, Any], value)


def validate_prepared_assets(
    manifest_path: str | Path,
    *,
    verify_hashes: bool,
    data_root: str | Path = "data",
) -> dict[str, Any]:
    manifest = load_json_object(manifest_path)
    records = manifest.get("dataset_files")
    if not isinstance(records, list) or not records:
        raise AssetManifestError("Prepared-assets manifest contains no dataset files")

    root = Path(data_root).resolve()
    for item in records:
        if not isinstance(item, dict):
            raise AssetManifestError("Dataset file record must be an object")
        path = Path(str(item.get("path", "")))
        resolved = path.resolve()
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise AssetManifestError(f"Dataset file is outside {root}: {path}") from exc
        if not resolved.is_file():
            raise AssetManifestError(f"Dataset file is missing: {path}")
        expected_size = int(item.get("bytes", -1))
        if resolved.stat().st_size != expected_size:
            raise AssetManifestError(
                f"Dataset file size differs from the manifest: {path}"
            )
        expected_sha256 = str(item.get("sha256", ""))
        if len(expected_sha256) != 64:
            raise AssetManifestError(f"Invalid dataset SHA-256 record: {path}")
        if verify_hashes and sha256_file(resolved) != expected_sha256:
            raise AssetManifestError(f"Dataset file hash differs from the manifest: {path}")
    return manifest


def verify_locked_prepared_assets(
    environment_lock: dict[str, Any],
    *,
    verify_hashes: bool,
) -> dict[str, Any]:
    record = environment_lock.get("prepared_assets")
    if not isinstance(record, dict):
        raise AssetManifestError("Environment lock has no prepared-assets record")
    path = Path(str(record.get("path", "")))
    expected_sha256 = str(record.get("sha256", ""))
    if not path.is_file():
        raise AssetManifestError(f"Prepared-assets manifest is missing: {path}")
    if sha256_file(path) != expected_sha256:
        raise AssetManifestError("Prepared-assets manifest differs from the environment lock")
    manifest = validate_prepared_assets(path, verify_hashes=verify_hashes)
    observed_count = len(manifest["dataset_files"])
    if observed_count != int(record.get("dataset_file_count", -1)):
        raise AssetManifestError("Prepared dataset file count differs from the environment lock")
    return manifest
