from __future__ import annotations

import hashlib
import inspect
import struct
from pathlib import Path
from typing import BinaryIO

import numpy as np
import pytest
import torch
from PIL import Image

from torch2pc_thesis.data import image_transform
from torch2pc_thesis.stage3b_qwake_scientific_campaign import (
    ArtifactBinding,
    ScientificBatchSpec,
    ScientificCampaignError,
    ScientificDataPartition,
    ScientificDatasetBinding,
    canonical_train_dataset_asset_paths,
)
from torch2pc_thesis.stage3b_qwake_scientific_runtime import (
    ScientificRuntimeError,
    _load_read_only_dataset,
)

SHA_A = "sha256:" + "a" * 64
SHA_B = "sha256:" + "b" * 64


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _write_idx_images(path: Path, images: np.ndarray) -> None:
    assert images.dtype == np.uint8
    assert images.ndim == 3
    path.parent.mkdir(parents=True, exist_ok=True)
    header = struct.pack(">IIII", 2051, images.shape[0], images.shape[1], images.shape[2])
    path.write_bytes(header + images.tobytes(order="C"))


def _write_idx_labels(path: Path, labels: np.ndarray) -> None:
    assert labels.dtype == np.uint8
    assert labels.ndim == 1
    path.parent.mkdir(parents=True, exist_ok=True)
    header = struct.pack(">II", 2049, labels.shape[0])
    path.write_bytes(header + labels.tobytes(order="C"))


def _materialized_binding(root: Path) -> ScientificDatasetBinding:
    images = np.zeros((3, 28, 28), dtype=np.uint8)
    images[0, 0, 0] = 255
    images[1, 14, 14] = 128
    images[2, 27, 27] = 64
    labels = np.asarray((2, 4, 6), dtype=np.uint8)

    image_rel, label_rel = canonical_train_dataset_asset_paths("FashionMNIST", "data")
    image_path = root / image_rel
    label_path = root / label_rel
    _write_idx_images(image_path, images)
    _write_idx_labels(label_path, labels)

    # Test resources deliberately exist as traps.  A compliant C1 loader must
    # neither bind nor open them.
    raw = root / "data/FashionMNIST/raw"
    (raw / "t10k-images-idx3-ubyte").write_bytes(b"forbidden-test-images")
    (raw / "t10k-labels-idx1-ubyte").write_bytes(b"forbidden-test-labels")

    split = root / "results/splits/frozen.npz"
    split.parent.mkdir(parents=True, exist_ok=True)
    np.savez(split, validation_idx=np.asarray((0, 2), dtype=np.int64))

    return ScientificDatasetBinding(
        dataset_name="FashionMNIST",
        dataset_root="data",
        split=ArtifactBinding("results/splits/frozen.npz", _sha256(split)),
        dataset_assets=(
            ArtifactBinding(image_rel, _sha256(image_path)),
            ArtifactBinding(label_rel, _sha256(label_path)),
        ),
        split_key="validation_idx",
        partition=ScientificDataPartition.DESIGN,
        batches=(ScientificBatchSpec("batch-000", (0, 2)),),
    )


def test_dataset_binding_accepts_only_exact_uncompressed_train_idx_pair() -> None:
    image_rel, label_rel = canonical_train_dataset_asset_paths("FashionMNIST", "data")
    valid = (
        ArtifactBinding(image_rel, SHA_A),
        ArtifactBinding(label_rel, SHA_B),
    )
    binding = ScientificDatasetBinding(
        dataset_name="FashionMNIST",
        dataset_root="data",
        split=ArtifactBinding("results/splits/frozen.npz", SHA_A),
        dataset_assets=valid,
        split_key="validation_idx",
        partition=ScientificDataPartition.DESIGN,
        batches=(ScientificBatchSpec("batch-000", (0,)),),
    )
    assert tuple(item.relative_path for item in binding.dataset_assets) == (image_rel, label_rel)

    with pytest.raises(ScientificCampaignError, match="train-only IDX"):
        ScientificDatasetBinding(
            dataset_name="FashionMNIST",
            dataset_root="data",
            split=ArtifactBinding("results/splits/frozen.npz", SHA_A),
            dataset_assets=(
                ArtifactBinding("data/FashionMNIST/raw/t10k-images-idx3-ubyte", SHA_A),
                ArtifactBinding("data/FashionMNIST/raw/t10k-labels-idx1-ubyte", SHA_B),
            ),
            split_key="validation_idx",
            partition=ScientificDataPartition.DESIGN,
            batches=(ScientificBatchSpec("batch-000", (0,)),),
        )

    with pytest.raises(ScientificCampaignError, match="unique and sorted|train-only IDX"):
        ScientificDatasetBinding(
            dataset_name="FashionMNIST",
            dataset_root="data",
            split=ArtifactBinding("results/splits/frozen.npz", SHA_A),
            dataset_assets=tuple(reversed(valid)),
            split_key="validation_idx",
            partition=ScientificDataPartition.DESIGN,
            batches=(ScientificBatchSpec("batch-000", (0,)),),
        )


def test_train_only_loader_never_opens_t10k_resources(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    binding = _materialized_binding(tmp_path)
    original_open = Path.open
    opened: list[str] = []

    def guarded_open(
        self: Path,
        mode: str = "r",
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> BinaryIO:
        relative = self.relative_to(tmp_path).as_posix() if self.is_relative_to(tmp_path) else str(self)
        if "t10k" in self.name:
            raise AssertionError(f"test resource opened: {relative}")
        opened.append(relative)
        return original_open(self, mode, buffering, encoding, errors, newline)  # type: ignore[return-value]

    monkeypatch.setattr(Path, "open", guarded_open)
    dataset, allowed = _load_read_only_dataset(tmp_path, binding)

    assert allowed == {0, 2}
    assert len(dataset) == 3
    assert all("t10k" not in item for item in opened)
    assert "data/FashionMNIST/raw/train-images-idx3-ubyte" in opened
    assert "data/FashionMNIST/raw/train-labels-idx1-ubyte" in opened


def test_train_only_idx_transform_matches_canonical_zero_pad_and_scale(tmp_path: Path) -> None:
    binding = _materialized_binding(tmp_path)
    dataset, _allowed = _load_read_only_dataset(tmp_path, binding)

    image, target = dataset[0]
    expected = torch.zeros((1, 32, 32), dtype=torch.float32)
    expected[0, 2, 2] = 1.0

    assert image.dtype == torch.float32
    assert image.shape == (1, 32, 32)
    assert torch.equal(image, expected)
    assert target == 2

    raw = np.zeros((28, 28), dtype=np.uint8)
    raw[0, 0] = 255
    torchvision_equivalent = image_transform()(Image.fromarray(raw))
    assert torch.equal(image, torchvision_equivalent)


def test_train_only_loader_rejects_malformed_idx_without_fallback(tmp_path: Path) -> None:
    binding = _materialized_binding(tmp_path)
    image_rel, _label_rel = canonical_train_dataset_asset_paths("FashionMNIST", "data")
    image_path = tmp_path / image_rel
    image_path.write_bytes(struct.pack(">IIII", 9999, 3, 28, 28) + bytes(3 * 28 * 28))
    bad_binding = ScientificDatasetBinding(
        dataset_name=binding.dataset_name,
        dataset_root=binding.dataset_root,
        split=binding.split,
        dataset_assets=(
            ArtifactBinding(image_rel, _sha256(image_path)),
            binding.dataset_assets[1],
        ),
        split_key=binding.split_key,
        partition=binding.partition,
        batches=binding.batches,
    )

    with pytest.raises(ScientificRuntimeError, match="IDX magic"):
        _load_read_only_dataset(tmp_path, bad_binding)


def test_scientific_runtime_has_no_torchvision_dataset_constructor_surface() -> None:
    import torch2pc_thesis.stage3b_qwake_scientific_runtime as runtime

    source = inspect.getsource(runtime)
    assert "DATASETS" not in source
    assert "image_transform" not in source
    assert "torchvision" not in source
    assert "train=False" not in source
    assert "download=" not in source
