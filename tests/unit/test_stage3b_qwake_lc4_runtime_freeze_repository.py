from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FREEZE_ROOT = (
    PROJECT_ROOT
    / "experiments/frozen/stage3b-qwake-lc4-f-runtime-freeze-v1"
)

EXPECTED_FILES = {
    "SHA256SUMS",
    "authorization-verification-receipt.json",
    "authorization.json",
    "identity.env",
    "image-build.log",
    "manifest.json",
    "preflight.json",
    "source-SHA256SUMS",
    "static-validation-receipt.json",
    "static-validation.log",
}


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(name: str) -> dict[str, Any]:
    return json.loads((FREEZE_ROOT / name).read_text(encoding="utf-8"))


def _check_registry(registry: Path, base: Path) -> None:
    lines = registry.read_text(encoding="utf-8").splitlines()
    assert lines
    for line in lines:
        digest, relative = line.split("  ", 1)
        target = base / relative
        assert target.is_file(), relative
        assert hashlib.sha256(target.read_bytes()).hexdigest() == digest


def _values_for_key(value: Any, key: str) -> list[Any]:
    values: list[Any] = []
    if isinstance(value, dict):
        for current_key, current_value in value.items():
            if current_key == key:
                values.append(current_value)
            values.extend(_values_for_key(current_value, key))
    elif isinstance(value, list):
        for current_value in value:
            values.extend(_values_for_key(current_value, key))
    return values


def test_qwake_lc4_f_package_scope_and_registries() -> None:
    assert FREEZE_ROOT.is_dir()
    assert {
        path.name for path in FREEZE_ROOT.iterdir() if path.is_file()
    } == EXPECTED_FILES
    assert not any(path.is_symlink() for path in FREEZE_ROOT.iterdir())
    assert not any(path.is_dir() for path in FREEZE_ROOT.iterdir())

    _check_registry(FREEZE_ROOT / "SHA256SUMS", FREEZE_ROOT)
    _check_registry(FREEZE_ROOT / "source-SHA256SUMS", PROJECT_ROOT)


def test_qwake_lc4_f_manifest_boundaries() -> None:
    manifest = _load_json("manifest.json")

    assert manifest["freeze_id"] == (
        "stage3b-qwake-lc4-f-runtime-freeze-v1"
    )
    assert manifest["slice"] == "QW-LC4-F"
    assert manifest["status"] == (
        "runtime_authorization_frozen_execution_not_performed"
    )
    assert manifest["source_commit"] == (
        "51fc7537fdcb395145fc4c5a38b8918b018fe892"
    )
    assert manifest["torch2pc_commit"] == (
        "b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4"
    )
    assert manifest["image_digest"] == (
        "sha256:"
        "a31cf96e20ab45ce29fe18b68eb805bd048a02f1f8107cf680d1c174ea363929"
    )
    assert manifest["preflight_sha256"] == (
        "sha256:"
        "3a8d7817338f3b93396270ea8e1b1b2fbda768dbd5461a18f97520948a53a9e6"
    )
    assert manifest["authorization_sha256"] == (
        "sha256:"
        "d11b662a5c5eeada5333e69c6fddf2e50726c01b4d8c78a556a68167dbdd301e"
    )
    assert manifest["runtime_cell_count"] == 14
    assert manifest["authorized_cell_count"] == 168
    assert manifest["matched_pair_count"] == 168
    assert manifest["reserve_probe_count"] == 28
    assert manifest["execution_count"] == 1
    assert manifest["runtime_execution_permitted"] is True
    assert manifest["runtime_execution_performed"] is False
    assert manifest["engineering_evidence_present"] is False
    assert manifest["scientific_execution_open"] is False
    assert manifest["test_dataset_access"] is False
    assert manifest["publication_permitted"] is False
    assert manifest["image_freeze_permitted"] is False
    assert manifest["next_slice"] == "QW-LC4-F-merge"
    assert manifest["post_merge_next_slice"] == "QW-LC4-E"


def test_qwake_lc4_f_receipt_chain() -> None:
    preflight = _load_json("preflight.json")
    authorization = _load_json("authorization.json")
    receipt = _load_json("authorization-verification-receipt.json")

    assert (
        "sha256:"
        "3a8d7817338f3b93396270ea8e1b1b2fbda768dbd5461a18f97520948a53a9e6"
        in _values_for_key(preflight, "preflight_sha256")
    )
    assert False in _values_for_key(
        preflight,
        "runtime_execution_performed",
    )
    assert (
        "sha256:"
        "d11b662a5c5eeada5333e69c6fddf2e50726c01b4d8c78a556a68167dbdd301e"
        in _values_for_key(authorization, "authorization_sha256")
    )
    assert False in _values_for_key(
        authorization,
        "runtime_execution_performed",
    )
    assert False in _values_for_key(
        authorization,
        "scientific_execution_open",
    )
    assert False in _values_for_key(
        receipt,
        "runtime_execution_performed",
    )


def test_qwake_lc4_f_exact_file_identities() -> None:
    expected = {
        "authorization-verification-receipt.json": (
            "sha256:"
            "b168cf6d6f5c6f0a7f52a49a43d5fbe219db952a01c636037a687ff8460dd4bb"
        ),
        "authorization.json": (
            "sha256:"
            "a380cffcfa73cb2dcf984a3cc7de013cb50d79f075677ad5e762417486f06ebd"
        ),
        "image-build.log": (
            "sha256:"
            "570328829853784e92c74d481f5f9891a8f653af2e83f89f7ec746ea920f884e"
        ),
        "manifest.json": (
            "sha256:"
            "4840d39d7c19133aeb3f20c572c17677f84ad2f82697dc4ad75dcccb99bb52c1"
        ),
        "preflight.json": (
            "sha256:"
            "6bf0086d28164068750ed1351e408178e6f941f1086196815559d199436151bd"
        ),
        "SHA256SUMS": (
            "sha256:"
            "8f8a0dfaaff934ac3c8f654e7e65d9460168755532547dcf924e51c6451aeb6d"
        ),
        "source-SHA256SUMS": (
            "sha256:"
            "f80fe750b26afda55be19f9f2322baade6c7f07b11ee0d0a431ad88c1136d7b0"
        ),
        "static-validation.log": (
            "sha256:"
            "62eff7f70dab1944abbcd8c3ca5da9c3ba82278b1f9284a15512c2ce7672e0f7"
        ),
        "static-validation-receipt.json": (
            "sha256:"
            "4ed9dfd08a84ea097dc6dd7eb259cb163977873c6a40c90361413eb187506e2a"
        ),
    }

    for name, digest in expected.items():
        assert _sha256(FREEZE_ROOT / name) == digest


def test_qwake_lc4_f_repository_documentation() -> None:
    marker = "ADR-063-stage3b-qwake-lc4-f-runtime-freeze"
    required = (
        PROJECT_ROOT / "STATUS.md",
        PROJECT_ROOT / "STATUS_EN.md",
        PROJECT_ROOT / "docs/qwake-local-compute-extension.md",
        PROJECT_ROOT / "docs/qwake-local-compute-extension_EN.md",
        PROJECT_ROOT / "docs/decisions/index.md",
        PROJECT_ROOT / "docs/decisions/index_EN.md",
        PROJECT_ROOT / "docs/language-map.csv",
        PROJECT_ROOT / "docs/research-log/2026-07.md",
        PROJECT_ROOT / "docs/research-log/2026-07_EN.md",
    )

    for path in required:
        assert marker in path.read_text(encoding="utf-8")

    assert (
        PROJECT_ROOT
        / "docs/decisions/ADR-063-stage3b-qwake-lc4-f-runtime-freeze.md"
    ).is_file()
    assert (
        PROJECT_ROOT
        / "docs/decisions/ADR-063-stage3b-qwake-lc4-f-runtime-freeze_EN.md"
    ).is_file()

    for path in (PROJECT_ROOT / "STATUS.md", PROJECT_ROOT / "STATUS_EN.md"):
        text = path.read_text(encoding="utf-8")
        assert "QW_LC4_F_MATERIALIZED=true" in text
        assert "QW_LC4_F_COMPLETE=false" in text
        assert "QW_LC4_E_BRANCH_PERMITTED=false" in text
        assert "LOCAL_COMPUTE_EXECUTION_OPEN=false" in text
        assert "RUNTIME_EXECUTION_PERFORMED=false" in text
