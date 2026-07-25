"""Validate the exact QW-4B-F-v2 runtime-authorization freeze."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, cast

from torch2pc_thesis.stage3b_qwake_fp_runtime import (
    RuntimeValidationPermissionSet,
    load_authorization,
    load_preflight,
)

ROOT = Path(__file__).resolve().parents[2]
FROZEN_ROOT = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-fp-runtime-validation-freeze-v2"
)
EXPECTED_SOURCE_COMMIT = "e413bb1e13cee42f702512e499f994e90df21e45"
EXPECTED_TORCH2PC_COMMIT = "b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4"
EXPECTED_IMAGE_DIGEST = (
    "sha256:"
    "bd91fab26df5f91a3aba90b8cad38bad"
    "ccab3a1a7bfb20efe4126a88a13236c4"
)
EXPECTED_OUTPUT_ROOT = (
    "results/stage-3/"
    "qwake-fp-runtime-validation-v2-attempt-001"
)
EXPECTED_PREFLIGHT_SHA256 = (
    "sha256:"
    "79ead4a0e757272c788acd90700d61c0e5a0509fe64168f83f47dc0963ce4d00"
)
EXPECTED_AUTHORIZATION_SHA256 = (
    "sha256:"
    "d22063efa0c458c2498577139fa322b952081d8356cd1a6511f25188b12206b6"
)
EXPECTED_RECEIPT_CHAIN_SHA256 = (
    "sha256:"
    "9eda60c6806581fea28021546b881d939e062c017b702a175105c56a25dea05d"
)
EXPECTED_FILE_SHA256: dict[str, str] = {
    "SHA256SUMS": (
        "d6d9d6b4b4fb2614e928b16c8acd355508aebee7561254505828f9479ee31a30"
    ),
    "authorization-verification-receipt.json": (
        "946e9b26fde6750e08fbdd24d66c60c6f2f49c92033cdb4c75989ccdac0ebcb5"
    ),
    "authorization-verification.log": (
        "9979ead4d63d42104053d65149f98ce1ce7f2ecf256e97678af9f55ac4901877"
    ),
    "authorization.json": (
        "15f5bd744a98671898728af397d5565b4cb68951f88c9e9a33f28d978a4c979a"
    ),
    "identity.env": (
        "bb692a859d771a78a78b06f2c84263a61804381df40bc4b78fcfcc3dab170cf2"
    ),
    "image-build.log": (
        "4a030d894f4328b0d990fa82535796ed0307259dd2427a568f9c75fb0a656b65"
    ),
    "manifest.json": (
        "a616f43e3045ce314aec5d23e6b3fb643f75707a84f859b02ab40f82fdbe0136"
    ),
    "preflight.json": (
        "d0932f718b9444328b788323c5c37bc1df40fa7b30aa78e8709a4139a9b14a5f"
    ),
    "source-SHA256SUMS": (
        "40ce845bc50dbbbdcc7aef5b4327e1325dd7bcda9c5c85a61ebb05024e045caa"
    ),
    "static-validation-receipt.json": (
        "d092fa993e0bb30be4749785b185ab170c9435f8be820d0d1ad67d5f3e4b445f"
    ),
    "static-validation.log": (
        "a656773474abb4d7d1a4b6102e09b06c961c45646f615416ded37fbc0d9aa926"
    ),
}
EXPECTED_SOURCE_SHA256: dict[str, str] = {
    "authorization-verification-receipt.json": (
        "946e9b26fde6750e08fbdd24d66c60c6f2f49c92033cdb4c75989ccdac0ebcb5"
    ),
    "authorization-verification.log": (
        "9979ead4d63d42104053d65149f98ce1ce7f2ecf256e97678af9f55ac4901877"
    ),
    "authorization.json": (
        "15f5bd744a98671898728af397d5565b4cb68951f88c9e9a33f28d978a4c979a"
    ),
    "identity.env": (
        "bb692a859d771a78a78b06f2c84263a61804381df40bc4b78fcfcc3dab170cf2"
    ),
    "image-build.log": (
        "4a030d894f4328b0d990fa82535796ed0307259dd2427a568f9c75fb0a656b65"
    ),
    "preflight.json": (
        "d0932f718b9444328b788323c5c37bc1df40fa7b30aa78e8709a4139a9b14a5f"
    ),
    "static-validation-receipt.json": (
        "d092fa993e0bb30be4749785b185ab170c9435f8be820d0d1ad67d5f3e4b445f"
    ),
    "static-validation.log": (
        "a656773474abb4d7d1a4b6102e09b06c961c45646f615416ded37fbc0d9aa926"
    ),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads(path.read_text(encoding="utf-8")),
    )


def _registry(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        assert name not in result
        result[name] = digest
    return result


def test_frozen_package_inventory_and_exact_digests() -> None:
    observed = sorted(path.name for path in FROZEN_ROOT.iterdir())
    assert observed == sorted(EXPECTED_FILE_SHA256)
    assert all(
        path.is_file() and not path.is_symlink()
        for path in FROZEN_ROOT.iterdir()
    )
    for name, expected in EXPECTED_FILE_SHA256.items():
        assert _sha256(FROZEN_ROOT / name) == expected


def test_package_and_source_registries_are_complete() -> None:
    expected_package = {
        name: value
        for name, value in EXPECTED_FILE_SHA256.items()
        if name != "SHA256SUMS"
    }
    assert _registry(FROZEN_ROOT / "SHA256SUMS") == expected_package
    assert (
        _registry(FROZEN_ROOT / "source-SHA256SUMS")
        == EXPECTED_SOURCE_SHA256
    )
    for name, expected in EXPECTED_SOURCE_SHA256.items():
        assert _sha256(FROZEN_ROOT / name) == expected


def test_preflight_and_authorization_are_strictly_bound() -> None:
    preflight = load_preflight(FROZEN_ROOT / "preflight.json")
    authorization = load_authorization(
        FROZEN_ROOT / "authorization.json"
    )
    assert preflight.preflight_sha256 == EXPECTED_PREFLIGHT_SHA256
    assert (
        preflight.source_identity.source_commit
        == EXPECTED_SOURCE_COMMIT
    )
    assert (
        preflight.source_identity.torch2pc_commit
        == EXPECTED_TORCH2PC_COMMIT
    )
    assert (
        preflight.source_identity.image_digest
        == EXPECTED_IMAGE_DIGEST
    )
    assert preflight.permissions.capabilities == frozenset()
    assert preflight.execution_authorization_present is False
    assert preflight.runtime_validation_permitted is False
    assert (
        authorization.authorization_sha256
        == EXPECTED_AUTHORIZATION_SHA256
    )
    assert authorization.preflight_sha256 == EXPECTED_PREFLIGHT_SHA256
    assert authorization.source_identity == preflight.source_identity
    assert (
        authorization.receipt_chain_sha256
        == EXPECTED_RECEIPT_CHAIN_SHA256
    )
    assert (
        authorization.permissions
        == RuntimeValidationPermissionSet.complete()
    )
    assert authorization.output_root == EXPECTED_OUTPUT_ROOT
    assert authorization.output_root_absent_at_issue is True
    assert authorization.execution_count == 1


def test_authorization_contains_exact_six_engineering_cells() -> None:
    authorization = load_authorization(
        FROZEN_ROOT / "authorization.json"
    )
    assert len(authorization.cells) == 6
    assert Counter(
        cell.lane.value for cell in authorization.cells
    ) == {
        "cpu_float64_engineering": 3,
        "rocm_float32_canonical": 3,
    }
    assert Counter(
        cell.pair_id.value for cell in authorization.cells
    ) == {
        "P0": 2,
        "P1": 2,
        "P2": 2,
    }
    assert {
        (cell.model_seed, cell.batch_id)
        for cell in authorization.cells
    } == {
        (0, "synthetic-engineering-batch-v1")
    }
    assert authorization.scientific_execution_open is False
    assert authorization.test_dataset_access is False
    assert authorization.publication_permitted is False
    assert authorization.image_freeze_permitted is False


def test_receipts_bind_logs_and_keep_execution_closed() -> None:
    preflight = load_preflight(FROZEN_ROOT / "preflight.json")
    authorization = load_authorization(
        FROZEN_ROOT / "authorization.json"
    )
    static_receipt = _load(
        FROZEN_ROOT / "static-validation-receipt.json"
    )
    verify_receipt = _load(
        FROZEN_ROOT
        / "authorization-verification-receipt.json"
    )
    assert static_receipt["schema_version"] == 2
    assert static_receipt["all_checks_passed"] is True
    assert len(static_receipt["checks"]) == 17
    assert all(
        item["passed"] is True
        for item in static_receipt["checks"]
    )
    assert (
        static_receipt["preflight_sha256"]
        == preflight.preflight_sha256
    )
    assert static_receipt["validation_log_sha256"] == (
        "sha256:"
        + _sha256(FROZEN_ROOT / "static-validation.log")
    )
    assert verify_receipt["status"] == (
        "authorization_verified_execution_not_performed"
    )
    assert verify_receipt["authorization_sha256"] == (
        authorization.authorization_sha256
    )
    assert verify_receipt["receipt_chain_sha256"] == (
        authorization.receipt_chain_sha256
    )
    assert verify_receipt[
        "authorization_verification_log_sha256"
    ] == (
        "sha256:"
        + _sha256(
            FROZEN_ROOT / "authorization-verification.log"
        )
    )
    for key in (
        "runtime_execution_performed",
        "engineering_evidence_present",
        "scientific_execution_open",
        "test_dataset_access",
        "publication_permitted",
        "image_freeze_permitted",
    ):
        assert verify_receipt[key] is False


def test_manifest_records_freeze_not_execution() -> None:
    manifest = _load(FROZEN_ROOT / "manifest.json")
    assert manifest["freeze_id"] == (
        "stage3b-qwake-fp-runtime-validation-freeze-v2"
    )
    assert manifest["slice"] == "QW-4B-F-v2"
    assert manifest["status"] == (
        "authorization_frozen_execution_not_performed"
    )
    assert manifest["source_commit"] == EXPECTED_SOURCE_COMMIT
    assert manifest["torch2pc_commit"] == EXPECTED_TORCH2PC_COMMIT
    assert manifest["image_digest"] == EXPECTED_IMAGE_DIGEST
    assert manifest["preflight_sha256"] == EXPECTED_PREFLIGHT_SHA256
    assert (
        manifest["authorization_sha256"]
        == EXPECTED_AUTHORIZATION_SHA256
    )
    assert (
        manifest["receipt_chain_sha256"]
        == EXPECTED_RECEIPT_CHAIN_SHA256
    )
    assert manifest["authorized_cell_count"] == 6
    assert manifest["execution_count"] == 1
    assert manifest["authorization_verified"] is True
    assert manifest["runtime_validation_permitted"] is True
    assert manifest["runtime_execution_performed"] is False
    assert manifest["engineering_evidence_present"] is False
    assert manifest["next_slice"] == "QW-4B-E-v2"
    assert manifest["post_baseline_next_slice"] == "QW-LC0"
    assert manifest["source_files_preserved_byte_for_byte"] is True


def test_status_and_adr_point_to_execution_slice_without_claims() -> None:
    markers = (
        "qwake_new_image_built=true",
        "qwake_new_runtime_preflight_captured=true",
        "qwake_new_runtime_authorization_issued=true",
        "qwake_runtime_authorization_verified=true",
        "qwake_runtime_validation_permitted=true",
        "qwake_runtime_execution_performed=false",
        "qwake_engineering_evidence_present=false",
        "qwake_next_slice=QW-4B-E-v2",
        "qwake_post_baseline_next_slice=QW-LC0",
    )
    for name in ("STATUS.md", "STATUS_EN.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        current = text[text.index("## `QW-4B-F-v2`") :]
        for marker in markers:
            assert marker in current

    for name in (
        "docs/decisions/"
        "ADR-047-stage3b-qwake-fp-runtime-validation-freeze-v2.md",
        "docs/decisions/"
        "ADR-047-stage3b-qwake-fp-runtime-validation-freeze-v2_EN.md",
    ):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert EXPECTED_SOURCE_COMMIT in text
        assert EXPECTED_IMAGE_DIGEST in text
        assert EXPECTED_PREFLIGHT_SHA256 in text
        assert EXPECTED_AUTHORIZATION_SHA256 in text
        assert "runtime_execution_performed=false" in text
        assert "engineering_evidence_present=false" in text
