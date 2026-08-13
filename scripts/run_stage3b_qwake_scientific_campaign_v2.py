#!/usr/bin/env python3
"""Execute one preregistered QWake scientific campaign authorization.

The entrypoint loads only canonical request/authorization data.  It does not
load plugins, Python snippets, shell commands, formulas, or arbitrary backend
modules.  The host launcher must already have consumed the one-shot
authorization by materializing the exact host claim; a failed attempt is
terminal and is never retried automatically.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_scientific_campaign import (
    load_scientific_authorization,
    load_scientific_request,
)
from torch2pc_thesis.stage3b_qwake_scientific_runtime_v2 import (
    execute_scientific_campaign,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--authorization", required=True, type=Path)
    args = parser.parse_args()

    root = args.project_root.expanduser().resolve()
    request = load_scientific_request(args.request.expanduser().resolve())
    authorization = load_scientific_authorization(
        args.authorization.expanduser().resolve()
    )
    authorization.require_request(request)

    print("=== QWAKE SCIENTIFIC CAMPAIGN SUCCESSOR ENTRYPOINT ===")
    print(f"ROLE={request.role.value}")
    print(f"REQUEST_SHA256={request.request_sha256}")
    print(f"AUTHORIZATION_SHA256={authorization.authorization_sha256}")
    print(f"IMAGE_DIGEST={request.image_digest}")
    print("ARBITRARY_CODE_LOADING=false")
    print("SHELL_COMMAND_LOADING=false")
    print("TEST_DATASET_ACCESS=false")
    print("PUBLICATION_PERMITTED=false")
    receipt = execute_scientific_campaign(root, request, authorization)
    print("FINAL_STATUS=0")
    print(f"RECEIPT_SHA256={receipt.receipt_sha256}")
    print("AUTHORIZATION_CONSUMED=true")
    print("AUTOMATIC_RETRY_PERMITTED=false")


if __name__ == "__main__":
    main()
