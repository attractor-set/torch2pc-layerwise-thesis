#!/usr/bin/env python3
"""Freeze a QWake scientific request by deriving runtime identity from image truth."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_scientific_campaign import load_scientific_request
from torch2pc_thesis.stage3b_qwake_scientific_identity_v2 import (
    SOURCE_COMMIT_ENV,
    SOURCE_COMMIT_LABEL,
    runtime_identity_from_image_inspection,
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


def _environment_map(config: dict[str, object]) -> dict[str, str]:
    values = config.get("Env")
    if not isinstance(values, list):
        raise RuntimeError("Docker image environment is absent")
    result: dict[str, str] = {}
    for item in values:
        if isinstance(item, str) and "=" in item:
            name, value = item.split("=", 1)
            result[name] = value
    return result


def _write_exclusive(path: Path, raw: bytes) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request-template", required=True, type=Path)
    parser.add_argument("--image-inspection", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    raw_inspection = json.loads(args.image_inspection.read_text(encoding="utf-8"))
    if (
        not isinstance(raw_inspection, list)
        or len(raw_inspection) != 1
        or not isinstance(raw_inspection[0], dict)
    ):
        raise RuntimeError("image inspection cardinality differs")
    image = raw_inspection[0]
    image_digest = image.get("Id")
    if (
        not isinstance(image_digest, str)
        or re.fullmatch(r"sha256:[0-9a-f]{64}", image_digest) is None
    ):
        raise RuntimeError("image digest is absent or malformed")
    config = image.get("Config")
    if not isinstance(config, dict):
        raise RuntimeError("Docker image Config is absent")
    labels = config.get("Labels")
    if not isinstance(labels, dict):
        raise RuntimeError("Docker image labels are absent")
    env = _environment_map(config)
    source_commit = labels.get(SOURCE_COMMIT_LABEL)
    if (
        not isinstance(source_commit, str)
        or re.fullmatch(r"[0-9a-f]{40}", source_commit) is None
        or env.get(SOURCE_COMMIT_ENV) != source_commit
    ):
        raise RuntimeError("image source-commit label/environment identity differs")

    runtime_identity = runtime_identity_from_image_inspection(
        image,
        expected_image_digest=image_digest,
        expected_source_commit=source_commit,
    )

    template_raw = args.request_template.read_bytes()
    template = json.loads(template_raw.decode("utf-8", errors="strict"))
    if not isinstance(template, dict):
        raise RuntimeError("request template must be a JSON object")
    if template_raw != _canonical_bytes(template):
        raise RuntimeError("request template must be canonical JSON")

    request = dict(template)
    request["source_commit"] = source_commit
    request["image_digest"] = image_digest
    request["code_manifest_sha256"] = runtime_identity.sha256
    request.pop("request_sha256", None)
    request["request_sha256"] = "sha256:" + hashlib.sha256(_canonical_bytes(request)).hexdigest()
    raw = _canonical_bytes(request)

    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    _write_exclusive(output, raw)
    loaded = load_scientific_request(output)
    if loaded.source_commit != source_commit:
        raise RuntimeError("frozen request source commit differs")
    if loaded.image_digest != image_digest:
        raise RuntimeError("frozen request image digest differs")
    if loaded.code_manifest_sha256 != runtime_identity.sha256:
        raise RuntimeError("frozen request runtime identity differs")

    print("QWAKE_SCIENTIFIC_REQUEST_FREEZE=PASS")
    print(f"REQUEST_SHA256={loaded.request_sha256}")
    print(f"IMAGE_DIGEST={image_digest}")
    print(f"SOURCE_COMMIT={source_commit}")
    print(f"RUNTIME_MANIFEST_RELATIVE={runtime_identity.relative_path}")
    print(f"RUNTIME_MANIFEST_SHA256={runtime_identity.sha256}")
    print("RUNTIME_IDENTITY_DERIVED_FROM_IMAGE=true")
    print("SCIENTIFIC_AUTHORIZATION_ISSUED=false")
    print("SCIENTIFIC_EXECUTION_PERFORMED=false")


if __name__ == "__main__":
    main()
