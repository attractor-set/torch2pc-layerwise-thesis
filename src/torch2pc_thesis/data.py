from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import numpy as np
import torch
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms

from torch2pc_thesis.reproducibility import seed_worker


@dataclass(frozen=True)
class DataBundle:
    train: DataLoader[Any]
    validation: DataLoader[Any]
    test: DataLoader[Any] | None
    train_indices: np.ndarray
    validation_indices: np.ndarray
    test_indices: np.ndarray | None
    split_files: tuple[Path, ...]
    split_sha256: dict[str, str]


DATASETS: dict[str, type[Any]] = {
    "MNIST": datasets.MNIST,
    "FashionMNIST": datasets.FashionMNIST,
    "KMNIST": datasets.KMNIST,
    "EMNIST": datasets.EMNIST,
}


def image_transform() -> transforms.Compose:
    return transforms.Compose([transforms.Pad(2), transforms.ToTensor()])


def dataset_targets(dataset: Any) -> np.ndarray:
    targets = getattr(dataset, "targets", None)
    if targets is None:
        raise ValueError("Dataset does not expose targets")
    if torch.is_tensor(targets):
        return cast(np.ndarray, targets.cpu().numpy().astype(int))
    return np.asarray(targets, dtype=int)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stratified_subset_indices(
    targets: np.ndarray,
    size: int | None,
    seed: int,
) -> np.ndarray:
    all_indices = np.arange(len(targets))
    if size is None or size >= len(targets):
        return all_indices
    selected, _ = train_test_split(
        all_indices,
        train_size=size,
        random_state=seed,
        stratify=targets,
    )
    return np.sort(selected)


def _load_or_create_split(
    path: Path,
    expected: dict[str, np.ndarray],
) -> dict[str, np.ndarray]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        loaded = np.load(path)
        result = {key: loaded[key] for key in loaded.files}
        if set(result) != set(expected):
            raise RuntimeError(f"Split schema mismatch: {path}")
        for key, value in expected.items():
            if not np.array_equal(result[key], value):
                raise RuntimeError(
                    f"Existing split differs from deterministic reconstruction: {path}:{key}"
                )
        return result
    np.savez(path, **expected)  # type: ignore[arg-type]
    return expected


def build_dataloaders(
    config: dict[str, Any],
    *,
    include_test: bool,
    download: bool = False,
) -> DataBundle:
    data_cfg = config["data"]
    train_cfg = config["training"]
    rep_cfg = config["reproducibility"]
    runtime_cfg = config["runtime"]

    name = str(data_cfg["dataset"])
    try:
        dataset_cls = DATASETS[name]
    except KeyError as exc:
        raise ValueError(f"Unknown dataset: {name}") from exc

    root = str(data_cfg["root"])
    kwargs = {"split": "digits"} if name == "EMNIST" else {}
    full_train = dataset_cls(
        root=root,
        train=True,
        download=download,
        transform=image_transform(),
        **kwargs,
    )
    full_test = None
    if include_test:
        full_test = dataset_cls(
            root=root,
            train=False,
            download=download,
            transform=image_transform(),
            **kwargs,
        )

    targets = dataset_targets(full_train)
    selected = stratified_subset_indices(
        targets,
        data_cfg.get("train_subset"),
        int(rep_cfg["split_seed"]),
    )
    train_idx, validation_idx = train_test_split(
        selected,
        test_size=float(data_cfg["validation_fraction"]),
        random_state=int(rep_cfg["split_seed"]),
        stratify=targets[selected],
    )
    train_idx = np.sort(train_idx)
    validation_idx = np.sort(validation_idx)

    subset_label = "all" if data_cfg.get("train_subset") is None else str(data_cfg["train_subset"])
    fraction_label = str(data_cfg["validation_fraction"]).replace(".", "p")
    split_dir = Path(data_cfg["split_dir"])
    train_validation_path = split_dir / (
        f"{name}_train-validation_seed{rep_cfg['split_seed']}_"
        f"subset{subset_label}_val{fraction_label}.npz"
    )
    _load_or_create_split(
        train_validation_path,
        {"train_idx": train_idx, "validation_idx": validation_idx},
    )

    split_files = [train_validation_path]
    test_idx = np.asarray([], dtype=int)
    if full_test is not None:
        test_idx = stratified_subset_indices(
            dataset_targets(full_test),
            data_cfg.get("test_subset"),
            int(rep_cfg["split_seed"]) + 1000,
        )
        test_subset_label = (
            "all" if data_cfg.get("test_subset") is None else str(data_cfg["test_subset"])
        )
        test_path = split_dir / (
            f"{name}_test_seed{int(rep_cfg['split_seed']) + 1000}_"
            f"subset{test_subset_label}.npz"
        )
        _load_or_create_split(test_path, {"test_idx": test_idx})
        split_files.append(test_path)

    generator = torch.Generator()
    generator.manual_seed(int(rep_cfg["loader_seed"]))
    workers = int(runtime_cfg["loader_workers"])
    pin_memory = str(runtime_cfg["device"]).lower() in {"gpu", "cuda", "rocm"}
    common = {
        "batch_size": int(train_cfg["batch_size"]),
        "num_workers": workers,
        "pin_memory": pin_memory,
        "worker_init_fn": seed_worker,
        "persistent_workers": workers > 0,
    }

    train_loader = DataLoader(
        Subset(full_train, train_idx.tolist()),
        shuffle=True,
        generator=generator,
        **common,
    )
    validation_loader = DataLoader(
        Subset(full_train, validation_idx.tolist()),
        shuffle=False,
        **common,
    )
    test_loader = None
    if full_test is not None:
        test_loader = DataLoader(
            Subset(full_test, test_idx.tolist()),
            shuffle=False,
            **common,
        )

    return DataBundle(
        train=train_loader,
        validation=validation_loader,
        test=test_loader,
        train_indices=train_idx.copy(),
        validation_indices=validation_idx.copy(),
        test_indices=test_idx.copy() if full_test is not None else None,
        split_files=tuple(split_files),
        split_sha256={path.name: sha256_file(path) for path in split_files},
    )
