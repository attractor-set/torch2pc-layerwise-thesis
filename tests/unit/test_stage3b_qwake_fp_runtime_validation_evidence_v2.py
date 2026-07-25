# ruff: noqa: E501
# Validate the sealed QW-4B-E-v2 engineering evidence.

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'results/stage-3/qwake-fp-runtime-validation-v2-attempt-001'
AUDIT = ROOT / 'experiments/frozen/stage3b-qwake-fp-runtime-validation-evidence-v2'
SEAL = ROOT / 'experiments/frozen/stage3b-qwake-fp-runtime-validation-output-seal-v2'
INPUT_AUTH = ROOT / 'experiments/frozen/stage3b-qwake-fp-runtime-validation-freeze-v2/authorization.json'

EXPECTED_DIGESTS = {
    'experiments/frozen/stage3b-qwake-fp-runtime-validation-evidence-v2/OUTPUT-SHA256SUMS': '93b1d5115ff65aefb16e5c45a9aa230c6f9f0b5ab3a27545d478e4964fb99ec7',
    'experiments/frozen/stage3b-qwake-fp-runtime-validation-evidence-v2/PREPARATION_SHA256SUMS': 'd8b2b95bf730b59d200c20cfbbf7a438326daee13eab1489c434dabdc3b2c7f7',
    'experiments/frozen/stage3b-qwake-fp-runtime-validation-evidence-v2/RECOVERY_V3_SHA256SUMS': '719efbf621d443d677e25846a7e158cb913c86a162288296c2e03ff00c131b3b',
    'experiments/frozen/stage3b-qwake-fp-runtime-validation-evidence-v2/SHA256SUMS': '904f128a7db6cb8bf7f641bf1dcd8e6f3004884a16c90b21772248e3cb80852f',
    'experiments/frozen/stage3b-qwake-fp-runtime-validation-evidence-v2/admission-verification.log': '9979ead4d63d42104053d65149f98ce1ce7f2ecf256e97678af9f55ac4901877',
    'experiments/frozen/stage3b-qwake-fp-runtime-validation-evidence-v2/execution-attempt-completion.json': '5644b45e675b64bed567aeb3e3ac02cc638fd345f4c13005705e9b13311c29cf',
    'experiments/frozen/stage3b-qwake-fp-runtime-validation-evidence-v2/execution-attempt-start.json': '7f61b4a8bd02138de641d08b45cefc5c2edd6f1f56a21284f66c8f7e6e787f6e',
    'experiments/frozen/stage3b-qwake-fp-runtime-validation-evidence-v2/final-admission-verification.log': '9979ead4d63d42104053d65149f98ce1ce7f2ecf256e97678af9f55ac4901877',
    'experiments/frozen/stage3b-qwake-fp-runtime-validation-evidence-v2/manifest.json': '2e4d1e7ff0a5d8702350e8f83eb1c671c9f23ee4abe85fc81cc1932e65aa2fa2',
    'experiments/frozen/stage3b-qwake-fp-runtime-validation-evidence-v2/post-execution-adjudication-v3.json': '8bfc1e5a4d7ba736e09dcc712334a55e9b83b4145edbc069d00eaba5e589c8f8',
    'experiments/frozen/stage3b-qwake-fp-runtime-validation-evidence-v2/pre-execution-manifest.json': '1d498dba700b670485d572318a9ede085731cf607184588aeea6df7c528261e3',
    'experiments/frozen/stage3b-qwake-fp-runtime-validation-evidence-v2/recovery-output-audit-v2.log': '940743d045e07526f2977c2ca974fd5e6c8f438d160bfa9af903747fe1dc3507',
    'experiments/frozen/stage3b-qwake-fp-runtime-validation-evidence-v2/recovery-output-audit-v2.py': 'af877b6f5ae518a69f858d75bd260e7255978bb31fd09431ee11da0f265ef67c',
    'experiments/frozen/stage3b-qwake-fp-runtime-validation-evidence-v2/recovery-output-audit-v3.log': '202115191d7cc06a7ce347e646e9537066993146032fcd28f8b1fe3df263addb',
    'experiments/frozen/stage3b-qwake-fp-runtime-validation-evidence-v2/recovery-output-audit-v3.py': 'ba43fd86f323a3dc29f367c4d25e9de5880b1cbb2bfd36ca3781638b0b9de3a3',
    'experiments/frozen/stage3b-qwake-fp-runtime-validation-evidence-v2/recovery-output-audit.log': 'f3b47f8973292eafc036f7bf09512d9c27cde338e5cab21b9af1b9ff72f46d8f',
    'experiments/frozen/stage3b-qwake-fp-runtime-validation-evidence-v2/recovery-output-audit.py': 'b68165013822a1bf99c1af494768d95fe80e324d82ddd1cae3da54710d41f20a',
    'experiments/frozen/stage3b-qwake-fp-runtime-validation-evidence-v2/runtime-execution.log': 'ddf48c9d3c32613e3f482ff76b73b6b84ec4447130767fb834f91cb1202d35a6',
    'experiments/frozen/stage3b-qwake-fp-runtime-validation-evidence-v2/source-after-SHA256SUMS': '7f932691d4b5f05e78b44c774d0b0395154078e28cad1fd03887a1b61fe5ea22',
    'experiments/frozen/stage3b-qwake-fp-runtime-validation-evidence-v2/source-before-SHA256SUMS': '7f932691d4b5f05e78b44c774d0b0395154078e28cad1fd03887a1b61fe5ea22',
    'experiments/frozen/stage3b-qwake-fp-runtime-validation-evidence-v2/source-snapshot.diff': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    'experiments/frozen/stage3b-qwake-fp-runtime-validation-output-seal-v2/SHA256SUMS': 'e4ff3a5811863a2a8a34d3d86316ad84a5de0e4f5f5852949ae8e006704814c2',
    'experiments/frozen/stage3b-qwake-fp-runtime-validation-output-seal-v2/seal.json': '38fff1dee19874fb7d01163a8355672473ba6ad890029ccfd3cf0c5218987cc4',
    'results/stage-3/qwake-fp-runtime-validation-v2-attempt-001/SHA256SUMS': '93b1d5115ff65aefb16e5c45a9aa230c6f9f0b5ab3a27545d478e4964fb99ec7',
    'results/stage-3/qwake-fp-runtime-validation-v2-attempt-001/authorization.json': '4a16d5080d56db71e04ad38b5df242884055135aa992feea8fc6966eb235fabc',
    'results/stage-3/qwake-fp-runtime-validation-v2-attempt-001/pre-freeze-projection.txt': '1cd251a3816c10f51b683ffff1ed6e78f21dbf837c8c7e44ed14847cb1bfce92',
    'results/stage-3/qwake-fp-runtime-validation-v2-attempt-001/preflight.json': 'd0932f718b9444328b788323c5c37bc1df40fa7b30aa78e8709a4139a9b14a5f',
    'results/stage-3/qwake-fp-runtime-validation-v2-attempt-001/runtime-validation-report.json': '54dba01d47814dc00fa53bd69c00865bd1c47754c017c7482c895162d3a86b82',
    'results/stage-3/qwake-fp-runtime-validation-v2-attempt-001/static-validation-receipt': 'd092fa993e0bb30be4749785b185ab170c9435f8be820d0d1ad67d5f3e4b445f',
}

REPORT_SHA256 = 'sha256:54dba01d47814dc00fa53bd69c00865bd1c47754c017c7482c895162d3a86b82'
PREFLIGHT_SHA256 = 'sha256:79ead4a0e757272c788acd90700d61c0e5a0509fe64168f83f47dc0963ce4d00'
AUTHORIZATION_SHA256 = 'sha256:d22063efa0c458c2498577139fa322b952081d8356cd1a6511f25188b12206b6'
RECEIPT_CHAIN_SHA256 = 'sha256:9eda60c6806581fea28021546b881d939e062c017b702a175105c56a25dea05d'
CANONICAL_AUTHORIZATION_SHA256 = 'sha256:3d403e267711adc72ec425745b26cc8e34f56d5f15b1430df6f8cfb3f5c40844'


def _json(path: Path) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads(path.read_text(encoding="utf-8")),
    )


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _prefixed(path: Path) -> str:
    return "sha256:" + _sha(path)


def _canonical_json_sha(path: Path) -> str:
    value = json.loads(path.read_text(encoding="utf-8"))
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def test_exact_29_file_inventory_and_digests() -> None:
    observed: set[str] = set()
    for root in (OUTPUT, AUDIT, SEAL):
        for path in root.iterdir():
            assert path.is_file()
            observed.add(path.relative_to(ROOT).as_posix())
    assert observed == set(EXPECTED_DIGESTS)
    for name, expected in EXPECTED_DIGESTS.items():
        assert _sha(ROOT / name) == expected


def test_authorization_equivalence_and_report_boundary() -> None:
    input_auth = _json(INPUT_AUTH)
    output_auth = _json(OUTPUT / "authorization.json")
    assert input_auth == output_auth
    assert _canonical_json_sha(INPUT_AUTH) == CANONICAL_AUTHORIZATION_SHA256
    assert (
        _canonical_json_sha(OUTPUT / "authorization.json")
        == CANONICAL_AUTHORIZATION_SHA256
    )
    assert _sha(INPUT_AUTH) != _sha(OUTPUT / "authorization.json")

    report_path = OUTPUT / "runtime-validation-report.json"
    report = _json(report_path)
    assert _prefixed(report_path) == REPORT_SHA256
    assert report["status"] == "engineering_validation_sealed"
    assert report["preflight_sha256"] == PREFLIGHT_SHA256
    assert report["authorization_sha256"] == AUTHORIZATION_SHA256
    assert report["engineering_evidence_only"] is True
    assert report["scientific_evidence"] is False
    assert report["publication_permitted"] is False
    assert report["image_freeze_eligible"] is True


def test_six_cells_and_disabled_effects_pass() -> None:
    report = _json(OUTPUT / "runtime-validation-report.json")
    lanes = report["lanes"]
    assert [lane["lane"] for lane in lanes] == [
        "cpu_float64_engineering",
        "rocm_float32_canonical",
    ]
    for lane in lanes:
        assert lane["nested_observations_passed"] is True
        cells = lane["cells"]
        assert [item["cell"]["pair_id"] for item in cells] == [
            "P0",
            "P1",
            "P2",
        ]
        for item in cells:
            pair = item["pair_validation"]
            assert pair["passed"] is True
            assert pair["equality_mismatches"] == []
            assert pair["initial_state_equal"] is True
            assert pair["rng_state_before_equal"] is True
            assert item["oracle_isolation_passed"] is True
            for disabled in item["disabled_capability_audits"]:
                assert disabled["enabled"] is False
                assert all(
                    value == 0
                    for value in disabled["effects"].values()
                )


def test_failure_provenance_and_adjudication_are_retained() -> None:
    first = (AUDIT / "recovery-output-audit.log").read_text(
        encoding="utf-8"
    )
    second = (AUDIT / "recovery-output-audit-v2.log").read_text(
        encoding="utf-8"
    )
    third = (AUDIT / "recovery-output-audit-v3.log").read_text(
        encoding="utf-8"
    )
    assert "RuntimeError: authorization bytes differ" in first
    assert "RuntimeError: disabled-capability audit failed" in second
    assert "OK: independent recovery-v3 audit passed" in third

    completion = _json(AUDIT / "execution-attempt-completion.json")
    assert completion["runner_status"] == 0
    assert completion["output_audit_status"] is None
    assert completion["authorization_consumed"] is True
    assert completion["engineering_evidence_present"] is False

    adjudication = _json(
        AUDIT / "post-execution-adjudication-v3.json"
    )
    assert adjudication["first_recovery_audit_status"] == 1
    assert adjudication["second_recovery_audit_status"] == 1
    assert adjudication["recovery_v3_audit_status"] == 0
    assert adjudication["runner_status"] == 0
    assert adjudication["independent_output_audit_status"] == 0
    assert adjudication["authorization_consumed"] is True
    assert adjudication["retry_permitted"] is False
    assert adjudication["runtime_rerun_performed"] is False
    assert adjudication["engineering_evidence_present"] is True
    assert adjudication["image_freeze_eligible"] is True
    assert adjudication["scientific_evidence"] is False
    assert adjudication["publication_permitted"] is False
    assert adjudication["qw_lc0_open"] is False


def test_manifest_and_external_seal_preserve_closed_boundary() -> None:
    manifest = _json(AUDIT / "manifest.json")
    assert manifest["slice"] == "QW-4B-E-v2"
    assert manifest["authorization_freeze_commit"] == '2dd699ab1d5565f00987a6806a1285f6d8918d38'
    assert manifest["authorized_source_commit"] == 'e413bb1e13cee42f702512e499f994e90df21e45'
    assert manifest["runtime_report_sha256"] == REPORT_SHA256
    assert manifest["receipt_chain_sha256"] == RECEIPT_CHAIN_SHA256
    assert manifest["post_merge_next_slice"] == "QW-LC0"
    boundary = manifest["claim_boundary"]
    assert boundary["authorization_consumed"] is True
    assert boundary["retry_permitted"] is False
    assert boundary["runtime_rerun_performed"] is False
    assert boundary["engineering_evidence_present"] is True
    assert boundary["scientific_evidence"] is False
    assert boundary["publication_permitted"] is False
    assert boundary["qw_lc0_open"] is False
    assert boundary["repository_evidence_sealed"] is False

    seal = _json(SEAL / "seal.json")
    observed_digest = seal.pop("seal_digest")
    payload = json.dumps(
        seal,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    assert hashlib.sha256(payload).hexdigest() == observed_digest
    assert seal["runtime_report_sha256"] == REPORT_SHA256
    assert seal["post_merge_transition"] == {
        "repository_evidence_sealed": True,
        "next_slice": "QW-LC0",
        "scientific_execution_open": False,
        "publication_permitted": False,
    }
