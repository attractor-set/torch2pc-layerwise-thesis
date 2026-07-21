from __future__ import annotations

import json
from pathlib import Path

from torch2pc_thesis.stage3b_b1_equivalence import (
    canonical_json_digest,
    sha256_file,
)
from torch2pc_thesis.stage3b_b2_confirmatory import (
    build_triple_specs,
    load_and_validate_confirmatory_request,
)

ROOT = Path(__file__).resolve().parents[2]
REQUEST_ROOT = ROOT / "experiments/frozen/stage3b-b2-confirmatory"
REQUEST_PATH = REQUEST_ROOT / "request.json"
SHA256SUMS_PATH = REQUEST_ROOT / "SHA256SUMS"

REQUEST_SHA256 = "02c88c0778398cecedb069948e9f952c8d7be46d3d064197ae0e7f5b86314ed3"
REQUEST_DIGEST = "3a824f4a7a8517a4b97341a4598ac8433e2253b45d2bb3f667722c270b06fb78"
MATCHED_REQUEST_SHA256 = "7c23c9ced5c838e7c3a2ad539d6a5839e986b79ca84ab9c16b14fecfaf819f5e"
MATCHED_MANIFEST_SHA256 = "6950470b4188b8c85226649ec631c739eef9cb8a8ef0b3410a82fb0a5106b79d"


def test_frozen_confirmatory_b2_request_is_valid_and_complete() -> None:
    request = load_and_validate_confirmatory_request(REQUEST_PATH)
    specs = build_triple_specs(request)

    assert sha256_file(REQUEST_PATH) == REQUEST_SHA256
    assert canonical_json_digest(request) == REQUEST_DIGEST
    assert request["request_id"] == "stage3b-b2-confirmatory-120-v1"
    assert request["scope"] == "confirmatory"
    assert request["matched_triple_count"] == 120
    assert request["pairwise_comparison_count"] == 240
    assert request["run_seed_base"] == 732000
    assert request["test_split_access"] is False
    assert request["evidence"] is False
    assert request["results_publication_permitted"] is False

    assert len(specs) == 120
    assert len({spec.pair_id for spec in specs}) == 120


def test_frozen_request_keeps_execution_closed() -> None:
    request = load_and_validate_confirmatory_request(REQUEST_PATH)

    assert request["execution_boundary"] == {
        "request_frozen": True,
        "runtime_authorization_issued": False,
        "execution_started": False,
        "results_present": False,
        "eq_b2_confirmatory_sealed": False,
        "derived_eq_b2_admission_present": False,
        "matched_profiling_refrozen": False,
        "matched_profiling_execution_open": False,
    }


def test_frozen_request_checksum_registry_is_exact() -> None:
    assert SHA256SUMS_PATH.read_text(encoding="utf-8").splitlines() == [
        f"{REQUEST_SHA256}  request.json"
    ]


def test_frozen_request_has_no_duplicate_json_keys() -> None:
    def reject_duplicate_keys(
        pairs: list[tuple[str, object]],
    ) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    json.loads(
        REQUEST_PATH.read_text(encoding="utf-8"),
        object_pairs_hook=reject_duplicate_keys,
    )


def test_historical_matched_profiling_opening_is_unchanged() -> None:
    request = ROOT / (
        "experiments/planned/"
        "STAGE3B-B1-B2-MATCHED-PROFILING-REQUEST.json"
    )
    manifest = ROOT / (
        "experiments/planned/"
        "STAGE3B-B1-B2-MATCHED-PROFILING-MANIFEST.json"
    )

    assert sha256_file(request) == MATCHED_REQUEST_SHA256
    assert sha256_file(manifest) == MATCHED_MANIFEST_SHA256


def test_status_and_roadmap_keep_runtime_closed() -> None:
    for name in ("STATUS.md", "STATUS_EN.md", "ROADMAP.md", "ROADMAP_EN.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "b2_confirmatory_request_frozen=true" in text
        assert "runtime_authorization=issued_consumed" in text
        assert "measurements_allowed=false" in text
        assert "matched_profiling_analysis_open=false" in text
