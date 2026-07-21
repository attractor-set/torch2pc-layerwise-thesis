from __future__ import annotations

import gzip
import hashlib
import io
import json
import shutil
import subprocess
import tarfile
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from torch2pc_thesis.stage3b_matched_sealing import MATCHED_SEALED_FILES

MATCHED_RELEASE_TAG = "stage3b-matched-profiling-evidence-v1"
MATCHED_RESULT_ROOT = Path(
    "results/stage-3/profiling/matched/stage3b-matched-profiling-e1dcfb2-v1"
)
MATCHED_EXECUTION_SOURCE_COMMIT = "e1dcfb26823e1191b98d2aa2a598499b13197583"
MATCHED_IMAGE_DIGEST = (
    "sha256:3c269b4278026b5b69968b3265b506ce626f2baf693859989de3371d639da4d0"
)
MATCHED_LOCALITY_SOURCE_NAME = "locality_events.jsonl"
MATCHED_LOCALITY_ARCHIVE_NAME = "locality_events.jsonl.zst"
MATCHED_LOCALITY_ASSET_NAME = (
    "stage3b-matched-profiling-locality-events-v1.jsonl.zst"
)
MATCHED_LOCALITY_MANIFEST_NAME = "locality_events.asset.json"
MATCHED_SEALED_REGISTRY_NAME = "SEALED-SHA256SUMS"
MATCHED_REPOSITORY_REGISTRY_NAME = "SHA256SUMS"
MATCHED_LOCALITY_UNCOMPRESSED_SIZE_BYTES = 6_544_044_000
MATCHED_LOCALITY_UNCOMPRESSED_SHA256 = (
    "3228baaa0f6479b1b4296f96632bd2d99c49642dc38f28f5ed7bc978d9dc538a"
)
MATCHED_LOCALITY_COMPRESSED_SHA256 = (
    "59a1479d66f170970b4d0f2b0712b8a825ccca01eab677c887a9046fc4c16f76"
)
MAX_GIT_EVIDENCE_ASSET_BYTES = 100_000_000
MAX_RUNTIME_ARCHIVE_BYTES = 1_900_000_000

MATCHED_REPOSITORY_CONTENT_FILES = (
    "analysis_metadata.json",
    "attempt-history.jsonl",
    "block-correctness.jsonl",
    "environment-lock.json",
    MATCHED_LOCALITY_ARCHIVE_NAME,
    MATCHED_LOCALITY_MANIFEST_NAME,
    "profiling_cells.csv",
    "profiling_repetitions.csv",
    "profiling_summary.csv",
    "runtime-inventory.json",
    MATCHED_SEALED_REGISTRY_NAME,
    "seal.json",
)
MATCHED_REPOSITORY_FILES = (
    MATCHED_REPOSITORY_REGISTRY_NAME,
    *MATCHED_REPOSITORY_CONTENT_FILES,
)


class Stage3BMatchedReleaseError(RuntimeError):
    """Raised when a release package violates its frozen provenance contract."""


@dataclass(frozen=True)
class ReleaseAsset:
    path: Path
    role: str


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_commit(project_root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=project_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _iter_files(root: Path) -> tuple[Path, ...]:
    return tuple(sorted(path for path in root.rglob("*") if path.is_file()))


def _archive_size(paths: Iterable[Path]) -> int:
    return sum(path.stat().st_size for path in paths)


def _write_reproducible_tar_gz(
    output: Path,
    members: Iterable[tuple[Path, str]],
) -> None:
    ordered = sorted(members, key=lambda item: item[1])
    with (
        output.open("wb") as raw,
        gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as compressed,
        tarfile.open(fileobj=compressed, mode="w") as archive,
    ):
        for source, archive_name in ordered:
            data = source.read_bytes()
            info = tarfile.TarInfo(name=archive_name)
            info.size = len(data)
            info.mode = 0o644
            info.mtime = 0
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            archive.addfile(info, io.BytesIO(data))


def _load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Stage3BMatchedReleaseError(f"JSON root is not an object: {path}")
    return value


def _load_registry(path: Path) -> dict[str, str]:
    records: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, name = line.split(maxsplit=1)
        name = name.removeprefix("*")
        if len(digest) != 64 or name in records:
            raise Stage3BMatchedReleaseError(
                f"invalid checksum registry entry: {path}:{line}"
            )
        records[name] = digest
    return records


def _validate_repository_registry(evidence_root: Path) -> None:
    registry_path = evidence_root / MATCHED_REPOSITORY_REGISTRY_NAME
    if not registry_path.is_file():
        raise Stage3BMatchedReleaseError("repository evidence registry is missing")
    records = _load_registry(registry_path)
    if set(records) != set(MATCHED_REPOSITORY_CONTENT_FILES):
        raise Stage3BMatchedReleaseError("repository evidence inventory differs")
    for name, digest in records.items():
        path = evidence_root / name
        if not path.is_file() or sha256_file(path) != digest:
            raise Stage3BMatchedReleaseError(
                f"repository evidence checksum failed: {name}"
            )


def _validate_compressed_locality(evidence_root: Path) -> None:
    archive = evidence_root / MATCHED_LOCALITY_ARCHIVE_NAME
    manifest_path = evidence_root / MATCHED_LOCALITY_MANIFEST_NAME
    sealed_registry_path = evidence_root / MATCHED_SEALED_REGISTRY_NAME
    raw = evidence_root / MATCHED_LOCALITY_SOURCE_NAME

    if raw.exists():
        raise Stage3BMatchedReleaseError(
            "raw locality stream must not be stored in the repository"
        )
    if not archive.is_file() or not manifest_path.is_file():
        raise Stage3BMatchedReleaseError("compressed locality representation is incomplete")
    if archive.stat().st_size >= MAX_GIT_EVIDENCE_ASSET_BYTES:
        raise Stage3BMatchedReleaseError("compressed locality asset exceeds Git limit")
    if sha256_file(archive) != MATCHED_LOCALITY_COMPRESSED_SHA256:
        raise Stage3BMatchedReleaseError("compressed locality checksum differs")

    manifest = _load_json(manifest_path)
    expected = {
        "schema_version": 1,
        "status": "lossless_compressed_repository_representation",
        "source_name": MATCHED_LOCALITY_SOURCE_NAME,
        "repository_name": MATCHED_LOCALITY_ARCHIVE_NAME,
        "release_asset_name": MATCHED_LOCALITY_ASSET_NAME,
        "release_tag": MATCHED_RELEASE_TAG,
        "compression_format": "zstd",
        "compression_level": 19,
        "long_distance_window_log": 27,
        "uncompressed_size_bytes": MATCHED_LOCALITY_UNCOMPRESSED_SIZE_BYTES,
        "uncompressed_sha256": MATCHED_LOCALITY_UNCOMPRESSED_SHA256,
        "compressed_sha256": MATCHED_LOCALITY_COMPRESSED_SHA256,
        "evidence": True,
        "results_publication_permitted": False,
        "release_publication_permitted": False,
    }
    for key, expected_value in expected.items():
        if manifest.get(key) != expected_value:
            raise Stage3BMatchedReleaseError(
                f"locality manifest field differs: {key}"
            )
    if manifest.get("compressed_size_bytes") != archive.stat().st_size:
        raise Stage3BMatchedReleaseError("locality archive size differs")

    if not sealed_registry_path.is_file():
        raise Stage3BMatchedReleaseError("original sealed registry is missing")
    sealed_records = _load_registry(sealed_registry_path)
    if set(sealed_records) != set(MATCHED_SEALED_FILES):
        raise Stage3BMatchedReleaseError("original sealed inventory differs")
    if (
        sealed_records.get(MATCHED_LOCALITY_SOURCE_NAME)
        != MATCHED_LOCALITY_UNCOMPRESSED_SHA256
    ):
        raise Stage3BMatchedReleaseError("sealed locality checksum differs")
    for name, digest in sealed_records.items():
        if name == MATCHED_LOCALITY_SOURCE_NAME:
            continue
        path = evidence_root / name
        if not path.is_file() or sha256_file(path) != digest:
            raise Stage3BMatchedReleaseError(
                f"sealed repository member checksum failed: {name}"
            )


def validate_repository_evidence(project_root: Path) -> dict[str, object]:
    evidence_root = (project_root / MATCHED_RESULT_ROOT).resolve()
    if not evidence_root.is_dir():
        raise Stage3BMatchedReleaseError("repository evidence root is missing")
    if {path.name for path in evidence_root.iterdir()} != set(
        MATCHED_REPOSITORY_FILES
    ):
        raise Stage3BMatchedReleaseError("repository evidence file set differs")

    _validate_repository_registry(evidence_root)
    _validate_compressed_locality(evidence_root)
    seal = _load_json(evidence_root / "seal.json")
    expected = {
        "status": "sealed",
        "source_commit": MATCHED_EXECUTION_SOURCE_COMMIT,
        "sealing_source_commit": MATCHED_EXECUTION_SOURCE_COMMIT,
        "image_digest": MATCHED_IMAGE_DIGEST,
        "matched_cell_count": 288,
        "attempt_history_count": 288,
        "cross_candidate_correctness_block_count": 96,
        "retried_cell_count": 0,
        "evidence": True,
        "full_lane_complete": True,
        "full_stage3b_campaign_complete": False,
        "results_publication_permitted": False,
        "test_dataset_access": False,
    }
    for key, expected_value in expected.items():
        if seal.get(key) != expected_value:
            raise Stage3BMatchedReleaseError(
                f"seal.{key} differs: expected={expected_value!r}, "
                f"observed={seal.get(key)!r}"
            )
    if seal.get("candidate_counts") != {
        "stage2_baseline": 96,
        "isolated_layer_vjp": 96,
        "composite_vjp": 96,
    }:
        raise Stage3BMatchedReleaseError("seal candidate counts differ")
    return seal


def _evidence_asset(project_root: Path, output_root: Path) -> ReleaseAsset:
    evidence_root = (project_root / MATCHED_RESULT_ROOT).resolve()
    output = output_root / "stage3b-matched-profiling-sealed-evidence-v1.tar.gz"
    members = [
        (
            path,
            f"stage3b-matched-profiling-sealed-evidence-v1/"
            f"{path.relative_to(evidence_root)}",
        )
        for path in _iter_files(evidence_root)
        if path.name != MATCHED_LOCALITY_ARCHIVE_NAME
    ]
    _write_reproducible_tar_gz(output, members)
    return ReleaseAsset(output, "sealed_evidence")


def _locality_asset(project_root: Path, output_root: Path) -> ReleaseAsset:
    source = (project_root / MATCHED_RESULT_ROOT / MATCHED_LOCALITY_ARCHIVE_NAME).resolve()
    output = output_root / MATCHED_LOCALITY_ASSET_NAME
    shutil.copyfile(source, output)
    return ReleaseAsset(output, "locality_events")


def _source_record_asset(source_record: Path, output_root: Path) -> ReleaseAsset:
    output = output_root / "stage3b-matched-profiling-release-source-record-v1.json"
    output.write_bytes(source_record.read_bytes())
    return ReleaseAsset(output, "release_source_record")


def _control_plane_paths(runtime_root: Path) -> tuple[Path, ...]:
    selected: list[Path] = []
    for path in _iter_files(runtime_root):
        relative = path.relative_to(runtime_root)
        parts = relative.parts
        if parts and parts[0] == "sealed":
            continue
        if "cells" in parts or "blocks" in parts:
            continue
        selected.append(path)
    return tuple(selected)


def _archive_tree(
    root: Path,
    output: Path,
    archive_root: str,
    *,
    paths: Iterable[Path] | None = None,
    size_limit: int | None = None,
) -> None:
    selected = tuple(paths) if paths is not None else _iter_files(root)
    if size_limit is not None and _archive_size(selected) > size_limit:
        raise Stage3BMatchedReleaseError(
            f"release archive exceeds size limit: {output.name}"
        )
    members = [
        (path, f"{archive_root}/{path.relative_to(root)}")
        for path in selected
    ]
    _write_reproducible_tar_gz(output, members)


def _verify_recorded_sha(path: Path, expected: object, *, label: str) -> None:
    if not isinstance(expected, str) or sha256_file(path) != expected:
        raise Stage3BMatchedReleaseError(f"{label} checksum differs")


def _full_assets(
    output_root: Path,
    source_record_path: Path,
) -> tuple[ReleaseAsset, ...]:
    source_sha_path = source_record_path.with_suffix(
        source_record_path.suffix + ".sha256"
    )
    if not source_sha_path.is_file():
        raise Stage3BMatchedReleaseError("release-source checksum is missing")
    expected_source_sha = source_sha_path.read_text(encoding="utf-8").split()[0]
    if sha256_file(source_record_path) != expected_source_sha:
        raise Stage3BMatchedReleaseError("release-source checksum failed")

    record = _load_json(source_record_path)
    if record.get("status") != "prepared_not_published":
        raise Stage3BMatchedReleaseError("release source is not in draft state")
    if record.get("intended_release_tag") != MATCHED_RELEASE_TAG:
        raise Stage3BMatchedReleaseError("release tag differs")
    if record.get("source_commit") != MATCHED_EXECUTION_SOURCE_COMMIT:
        raise Stage3BMatchedReleaseError("execution source commit differs")
    if record.get("image_digest") != MATCHED_IMAGE_DIGEST:
        raise Stage3BMatchedReleaseError("image digest differs")
    if record.get("release_publication_permitted") is not False:
        raise Stage3BMatchedReleaseError("release publication must remain closed")

    runtime_root = Path(str(record["runtime_root"])).expanduser().resolve()
    image_registry = Path(
        str(record["image_checkpoint_registry_path"])
    ).expanduser().resolve()
    sealing_registry = Path(
        str(record["sealing_log_registry_path"])
    ).expanduser().resolve()
    if not runtime_root.is_dir():
        raise Stage3BMatchedReleaseError("runtime root is missing")
    if not image_registry.is_file() or not sealing_registry.is_file():
        raise Stage3BMatchedReleaseError("release provenance registry is missing")

    recorded_paths = {
        "sealed_checkpoint_sha256": runtime_root / "SEALED-CHECKPOINT.sha256",
        "control_inventory_sha256": runtime_root / "CONTROL-INVENTORY.sha256",
        "dry_run_inventory_sha256": runtime_root / "DRY-RUN-INVENTORY.sha256",
        "execution_inventory_sha256": runtime_root / "EXECUTION-INVENTORY.sha256",
        "image_checkpoint_registry_sha256": image_registry,
        "sealing_log_registry_sha256": sealing_registry,
    }
    for field, path in recorded_paths.items():
        _verify_recorded_sha(path, record.get(field), label=field)

    control_output = output_root / "stage3b-matched-profiling-control-plane-v1.tar.gz"
    _archive_tree(
        runtime_root,
        control_output,
        "stage3b-matched-profiling-control-plane-v1",
        paths=_control_plane_paths(runtime_root),
    )

    runtime_output = output_root / "stage3b-matched-profiling-runtime-records-v1.tar.gz"
    runtime_paths = tuple(
        path
        for path in _iter_files(runtime_root)
        if path.relative_to(runtime_root).parts[0] != "sealed"
        and path.name != "locality-events.jsonl"
    )
    _archive_tree(
        runtime_root,
        runtime_output,
        "stage3b-matched-profiling-runtime-records-v1",
        paths=runtime_paths,
        size_limit=MAX_RUNTIME_ARCHIVE_BYTES,
    )

    image_root = image_registry.parent
    image_output = output_root / "stage3b-matched-profiling-image-checkpoint-v1.tar.gz"
    _archive_tree(
        image_root,
        image_output,
        "stage3b-matched-profiling-image-checkpoint-v1",
    )

    sealing_root = sealing_registry.parent
    sealing_paths = [sealing_registry]
    for line in sealing_registry.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        _, name = line.split(maxsplit=1)
        candidate = sealing_root / name.removeprefix("*")
        if candidate.is_file():
            sealing_paths.append(candidate)
    sealing_output = output_root / "stage3b-matched-profiling-sealing-logs-v1.tar.gz"
    _archive_tree(
        sealing_root,
        sealing_output,
        "stage3b-matched-profiling-sealing-logs-v1",
        paths=sealing_paths,
    )

    return (
        _source_record_asset(source_record_path, output_root),
        ReleaseAsset(control_output, "control_plane"),
        ReleaseAsset(runtime_output, "runtime_records_without_locality_stream"),
        ReleaseAsset(image_output, "image_checkpoint"),
        ReleaseAsset(sealing_output, "sealing_logs"),
    )


def _write_notes(output_root: Path, release_commit: str) -> ReleaseAsset:
    output = output_root / "RELEASE-NOTES.md"
    output.write_text(
        "\n".join(
            (
                "# Stage 3B matched-profiling evidence v1",
                "",
                "This release is created as a draft evidence checkpoint.",
                "",
                f"- release commit: `{release_commit}`",
                f"- execution source commit: `{MATCHED_EXECUTION_SOURCE_COMMIT}`",
                f"- immutable image: `{MATCHED_IMAGE_DIGEST}`",
                "- matched cells: `288`",
                "- matched blocks: `96`",
                "- locality stream: lossless Zstandard asset",
                "- evidence: `true`",
                "- results publication permitted: `false`",
                "- full Stage 3B campaign complete: `false`",
                "",
                "The draft must not be published before a separate publication gate.",
                "Descriptive analysis is not part of this evidence-preservation release.",
                "",
            )
        ),
        encoding="utf-8",
    )
    return ReleaseAsset(output, "release_notes")


def _write_manifest(
    output_root: Path,
    assets: Iterable[ReleaseAsset],
    *,
    release_commit: str,
    mode: Literal["repository", "full"],
) -> ReleaseAsset:
    output = output_root / "RELEASE-MANIFEST.json"
    records = [
        {
            "name": asset.path.name,
            "role": asset.role,
            "size_bytes": asset.path.stat().st_size,
            "sha256": sha256_file(asset.path),
        }
        for asset in sorted(assets, key=lambda item: item.path.name)
    ]
    manifest = {
        "schema_version": 1,
        "status": "draft_only",
        "release_tag": MATCHED_RELEASE_TAG,
        "release_commit": release_commit,
        "execution_source_commit": MATCHED_EXECUTION_SOURCE_COMMIT,
        "image_digest": MATCHED_IMAGE_DIGEST,
        "packaging_mode": mode,
        "matched_cell_count": 288,
        "matched_block_count": 96,
        "evidence": True,
        "results_publication_permitted": False,
        "release_publication_permitted": False,
        "full_stage3b_campaign_complete": False,
        "assets": records,
    }
    output.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return ReleaseAsset(output, "release_manifest")


def _write_checksums(output_root: Path) -> ReleaseAsset:
    output = output_root / "SHA256SUMS"
    names = sorted(
        path
        for path in output_root.iterdir()
        if path.is_file() and path.name != output.name
    )
    output.write_text(
        "".join(f"{sha256_file(path)}  {path.name}\n" for path in names),
        encoding="utf-8",
    )
    return ReleaseAsset(output, "checksum_registry")


def package_matched_release(
    project_root: Path,
    output_root: Path,
    *,
    tag: str,
    mode: Literal["repository", "full"],
    release_commit: str | None = None,
    release_source_record: Path | None = None,
) -> dict[str, object]:
    root = project_root.expanduser().resolve()
    output = output_root.expanduser().resolve()
    if tag != MATCHED_RELEASE_TAG:
        raise Stage3BMatchedReleaseError(f"unexpected release tag: {tag}")
    if output.exists() and any(output.iterdir()):
        raise Stage3BMatchedReleaseError(f"output directory is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    seal = validate_repository_evidence(root)
    commit = release_commit or _git_commit(root)

    assets: list[ReleaseAsset] = [
        _evidence_asset(root, output),
        _locality_asset(root, output),
    ]
    if mode == "full":
        if release_source_record is None:
            raise Stage3BMatchedReleaseError(
                "full packaging requires --release-source-record"
            )
        assets.extend(_full_assets(output, release_source_record.expanduser().resolve()))
    notes = _write_notes(output, commit)
    assets.append(notes)
    manifest = _write_manifest(output, assets, release_commit=commit, mode=mode)
    assets.append(manifest)
    checksums = _write_checksums(output)

    return {
        "status": "draft_only",
        "release_tag": tag,
        "release_commit": commit,
        "execution_source_commit": seal["source_commit"],
        "packaging_mode": mode,
        "asset_count": len(assets) + 1,
        "output_root": str(output),
        "checksum_registry": str(checksums.path),
        "results_publication_permitted": False,
        "release_publication_permitted": False,
    }
