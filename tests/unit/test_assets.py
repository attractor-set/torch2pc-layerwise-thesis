import json
from pathlib import Path

import pytest

from torch2pc_thesis.assets import (
    AssetManifestError,
    sha256_file,
    validate_prepared_assets,
    verify_locked_prepared_assets,
)


def _manifest(tmp_path: Path) -> tuple[Path, Path]:
    data = tmp_path / "data"
    data.mkdir()
    file_path = data / "sample.bin"
    file_path.write_bytes(b"observed-data")
    manifest_path = tmp_path / "prepared_assets.json"
    manifest_path.write_text(
        json.dumps(
            {
                "dataset_files": [
                    {
                        "path": str(file_path),
                        "bytes": file_path.stat().st_size,
                        "sha256": sha256_file(file_path),
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    return manifest_path, file_path


def test_prepared_assets_are_verified_by_hash(tmp_path: Path) -> None:
    manifest_path, file_path = _manifest(tmp_path)
    validate_prepared_assets(
        manifest_path,
        verify_hashes=True,
        data_root=file_path.parent,
    )
    file_path.write_bytes(b"changed-data")
    with pytest.raises(AssetManifestError):
        validate_prepared_assets(
            manifest_path,
            verify_hashes=True,
            data_root=file_path.parent,
        )


def test_environment_lock_binds_prepared_assets(tmp_path: Path, monkeypatch) -> None:
    manifest_path, file_path = _manifest(tmp_path)
    monkeypatch.chdir(tmp_path)
    lock = {
        "prepared_assets": {
            "path": str(manifest_path),
            "sha256": sha256_file(manifest_path),
            "dataset_file_count": 1,
        }
    }
    verify_locked_prepared_assets(lock, verify_hashes=True)
    file_path.write_bytes(b"tampered")
    with pytest.raises(AssetManifestError):
        verify_locked_prepared_assets(lock, verify_hashes=True)
