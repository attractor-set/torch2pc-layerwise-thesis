#!/usr/bin/env python3
"""Read-only verifier for both terminal QWake scientific attempt outcomes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_scientific_campaign import (
    load_scientific_authorization,
    load_scientific_host_claim,
    load_scientific_request,
)
from torch2pc_thesis.stage3b_qwake_scientific_runtime import (
    load_campaign_execution_receipt,
)


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--authorization", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args()

    request = load_scientific_request(args.request.expanduser().resolve())
    authorization = load_scientific_authorization(args.authorization.expanduser().resolve())
    authorization.require_request(request)
    output = args.output_root.expanduser().resolve()
    claim = load_scientific_host_claim(output / "host-claim.json")
    claim.require(request, authorization)

    receipt_path = output / "receipt.json"
    failure_path = output / "host-outcome.json"
    if receipt_path.is_file() == failure_path.is_file():
        raise RuntimeError(
            "exactly one terminal success receipt or consumed-failure outcome is required"
        )

    if receipt_path.is_file():
        receipt = load_campaign_execution_receipt(receipt_path)
        if receipt.request_sha256 != request.request_sha256:
            raise RuntimeError("success receipt request identity differs")
        if receipt.authorization_sha256 != authorization.authorization_sha256:
            raise RuntimeError("success receipt authorization identity differs")
        if receipt.image_digest != request.image_digest:
            raise RuntimeError("success receipt image identity differs")
        print("TERMINAL_OUTCOME=scientific_execution_sealed")
        print(f"RECEIPT_SHA256={receipt.receipt_sha256}")
    else:
        raw = failure_path.read_bytes()
        payload = json.loads(raw.decode("utf-8", errors="strict"))
        if not isinstance(payload, dict) or raw != _canonical_bytes(payload):
            raise RuntimeError("consumed-failure outcome is not canonical")
        expected = {
            "schema_version": 1,
            "status": "terminal_consumed_failure",
            "request_sha256": request.request_sha256,
            "image_digest": request.image_digest,
            "host_claim_sha256": claim.claim_sha256,
            "authorization_consumed": True,
            "automatic_retry_permitted": False,
            "test_dataset_access": False,
            "publication_permitted": False,
        }
        for key, value in expected.items():
            if payload.get(key) != value:
                raise RuntimeError(f"consumed-failure outcome differs: {key}")
        docker_status = payload.get("docker_status")
        if not isinstance(docker_status, int) or docker_status == 0:
            raise RuntimeError("consumed-failure Docker status differs")
        print("TERMINAL_OUTCOME=terminal_consumed_failure")
        print(f"DOCKER_STATUS={docker_status}")

    print("TERMINAL_OUTCOME_VERIFIER=PASS")
    print("AUTOMATIC_RETRY_PERMITTED=false")
    print("TEST_DATASET_ACCESS=false")
    print("PUBLICATION_PERMITTED=false")


if __name__ == "__main__":
    main()
