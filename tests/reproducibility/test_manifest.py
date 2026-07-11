from pathlib import Path

from torch2pc_thesis.manifests import directory_manifest


def test_manifest_orders_files(tmp_path: Path) -> None:
    (tmp_path / "b.txt").write_text("b", encoding="utf-8")
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    manifest = directory_manifest(tmp_path)
    assert [item["path"] for item in manifest["files"]] == ["a.txt", "b.txt"]
