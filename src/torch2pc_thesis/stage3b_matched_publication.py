from __future__ import annotations

import gzip
import hashlib
import io
import json
import tarfile
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

PUBLICATION_GATE_ID = (
    "stage3b-matched-descriptive-analysis-publication-gate-v1"
)
PUBLICATION_ACTION_TAG = (
    "stage3b-matched-descriptive-analysis-publication-v1"
)
MATCHED_EVIDENCE_RELEASE_TAG = "stage3b-matched-profiling-evidence-v1"
ANALYSIS_OUTPUT_ROOT = Path(
    "results/stage-3/analysis/matched/"
    "stage3b-matched-descriptive-analysis-70d6c3c-v1"
)
ANALYSIS_AUDIT_ROOT = Path(
    "experiments/frozen/"
    "stage3b-matched-descriptive-analysis-output-audit-v1"
)
ANALYSIS_SEAL_ROOT = Path(
    "experiments/frozen/"
    "stage3b-matched-descriptive-analysis-output-seal-v1"
)
PUBLICATION_GATE_ROOT = Path(
    "experiments/frozen/"
    "stage3b-matched-descriptive-analysis-publication-gate-v1"
)
EXPECTED_OUTPUT_FILE_COUNT = 18
EXPECTED_OUTPUT_REGISTRY_SHA256 = (
    "8baa1b55c21ed2b00bd849bbbe4f415d8b5f86d70bd9989d4ec4917765ead1da"
)
EXPECTED_AUDIT_REGISTRY_SHA256 = (
    "c7984a0559c8ee2c902583abd547dec84f23116b679cdf6cfae665ca167d00c6"
)
EXPECTED_SEAL_DIGEST = (
    "dbb8983bd77490ca4feedc035ae31ca4cdd0764ecd89dab1b0c3d91aed0ad3cd"
)
EXPECTED_CANDIDATE_DECISIONS = [
    {
        "candidate_id": "isolated_layer_vjp",
        "method_statuses": {
            "fixedpred": "reject_or_revise",
            "strict": "reject_or_revise",
        },
        "status": "reject_or_revise",
    },
    {
        "candidate_id": "composite_vjp",
        "method_statuses": {
            "fixedpred": "reject_or_revise",
            "strict": "reject_or_revise",
        },
        "status": "reject_or_revise",
    },
]


class Stage3BMatchedPublicationError(RuntimeError):
    """Raised when the matched-analysis publication boundary is violated."""


@dataclass(frozen=True)
class PublicationAsset:
    path: Path
    role: str


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Stage3BMatchedPublicationError(
            f"JSON root is not an object: {path}"
        )
    return value


def _load_registry(path: Path) -> dict[str, str]:
    records: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, name = line.split(maxsplit=1)
        name = name.removeprefix("*")
        if len(digest) != 64 or name in records:
            raise Stage3BMatchedPublicationError(
                f"invalid checksum registry entry: {path}:{line}"
            )
        records[name] = digest
    return records


def _validate_registry(root: Path, registry_name: str) -> dict[str, str]:
    registry_path = root / registry_name
    if not registry_path.is_file():
        raise Stage3BMatchedPublicationError(
            f"checksum registry is missing: {registry_path}"
        )
    records = _load_registry(registry_path)
    for name, digest in records.items():
        path = root / name
        if not path.is_file() or sha256_file(path) != digest:
            raise Stage3BMatchedPublicationError(
                f"checksum verification failed: {root.name}/{name}"
            )
    return records


def _require_equal(
    observed: object,
    expected: object,
    *,
    label: str,
) -> None:
    if observed != expected:
        raise Stage3BMatchedPublicationError(
            f"{label} differs: expected={expected!r}, observed={observed!r}"
        )


def validate_publication_inputs(project_root: Path) -> dict[str, object]:
    root = project_root.expanduser().resolve()
    output_root = root / ANALYSIS_OUTPUT_ROOT
    audit_root = root / ANALYSIS_AUDIT_ROOT
    seal_root = root / ANALYSIS_SEAL_ROOT
    gate_root = root / PUBLICATION_GATE_ROOT

    for required_root in (output_root, audit_root, seal_root, gate_root):
        if not required_root.is_dir():
            raise Stage3BMatchedPublicationError(
                f"required publication input is missing: {required_root}"
            )

    output_files = tuple(
        sorted(path for path in output_root.iterdir() if path.is_file())
    )
    _require_equal(
        len(output_files),
        EXPECTED_OUTPUT_FILE_COUNT,
        label="analysis output file count",
    )
    output_registry = output_root / "SHA256SUMS"
    _require_equal(
        sha256_file(output_registry),
        EXPECTED_OUTPUT_REGISTRY_SHA256,
        label="analysis output registry sha256",
    )
    output_records = _validate_registry(output_root, "SHA256SUMS")
    _require_equal(
        len(output_records),
        EXPECTED_OUTPUT_FILE_COUNT - 1,
        label="analysis output registry member count",
    )

    audit_records = _validate_registry(audit_root, "SHA256SUMS")
    _require_equal(
        sha256_file(audit_root / "SHA256SUMS"),
        EXPECTED_AUDIT_REGISTRY_SHA256,
        label="audit package registry sha256",
    )
    _require_equal(
        set(audit_records),
        {
            "audit.json",
            "execution-receipt.json",
            "OUTPUT-SHA256SUMS",
        },
        label="audit package inventory",
    )
    _validate_registry(seal_root, "SHA256SUMS")
    _validate_registry(gate_root, "SHA256SUMS")

    seal = _load_json(seal_root / "seal.json")
    _require_equal(
        seal.get("seal_id"),
        "stage3b-matched-descriptive-analysis-output-seal-v1",
        label="seal id",
    )
    _require_equal(
        seal.get("seal_digest"),
        EXPECTED_SEAL_DIGEST,
        label="seal digest",
    )
    _require_equal(
        seal.get("output_registry_sha256"),
        EXPECTED_OUTPUT_REGISTRY_SHA256,
        label="sealed output registry sha256",
    )
    _require_equal(
        seal.get("audit_package_registry_sha256"),
        EXPECTED_AUDIT_REGISTRY_SHA256,
        label="sealed audit registry sha256",
    )
    claim_boundary = seal.get("claim_boundary")
    if not isinstance(claim_boundary, dict):
        raise Stage3BMatchedPublicationError("seal claim boundary is missing")
    expected_sealed_boundary = {
        "analysis_execution_performed": True,
        "analysis_output_audited": True,
        "analysis_output_evidence": True,
        "analysis_output_sealed": True,
        "analysis_results_present": True,
        "ex_if0_opened": False,
        "policy_activation_permitted": False,
        "release_publication_permitted": False,
        "results_publication_permitted": False,
        "superiority_claim_permitted": False,
        "test_dataset_access": False,
    }
    _require_equal(
        claim_boundary,
        expected_sealed_boundary,
        label="sealed claim boundary",
    )

    decision = _load_json(output_root / "engineering_decision.json")
    _require_equal(
        decision.get("candidate_decisions"),
        EXPECTED_CANDIDATE_DECISIONS,
        label="candidate decisions",
    )
    for field in (
        "ex_if0_opened",
        "policy_activation_permitted",
        "release_publication_permitted",
        "results_publication_permitted",
        "superiority_claim_permitted",
        "test_dataset_access",
    ):
        _require_equal(decision.get(field), False, label=f"decision.{field}")

    gate = _load_json(gate_root / "gate.json")
    _require_equal(
        gate.get("gate_id"),
        PUBLICATION_GATE_ID,
        label="publication gate id",
    )
    _require_equal(
        gate.get("status"),
        "publication_gate_frozen_pending_remote_action",
        label="publication gate status",
    )
    _require_equal(
        gate.get("publication_action_tag"),
        PUBLICATION_ACTION_TAG,
        label="publication action tag",
    )
    _require_equal(
        gate.get("evidence_release_tag"),
        MATCHED_EVIDENCE_RELEASE_TAG,
        label="evidence release tag",
    )
    _require_equal(
        gate.get("required_remote_release_state_before_action"),
        "draft",
        label="required pre-publication release state",
    )
    _require_equal(
        gate.get("analysis_output_registry_sha256"),
        EXPECTED_OUTPUT_REGISTRY_SHA256,
        label="gate output registry sha256",
    )
    _require_equal(
        gate.get("analysis_output_seal_digest"),
        EXPECTED_SEAL_DIGEST,
        label="gate output seal digest",
    )
    _require_equal(
        gate.get("candidate_decisions"),
        EXPECTED_CANDIDATE_DECISIONS,
        label="gate candidate decisions",
    )

    before = gate.get("claim_boundary_before_successful_action")
    after = gate.get("claim_boundary_after_successful_action")
    if not isinstance(before, dict) or not isinstance(after, dict):
        raise Stage3BMatchedPublicationError(
            "publication gate claim boundaries are missing"
        )
    _require_equal(before.get("results_publication_permitted"), False, label="before results publication")
    _require_equal(before.get("release_publication_permitted"), False, label="before release publication")
    _require_equal(after.get("results_publication_permitted"), True, label="after results publication")
    _require_equal(after.get("release_publication_permitted"), True, label="after release publication")
    for field in (
        "superiority_claim_permitted",
        "ex_if0_opened",
        "policy_activation_permitted",
        "test_dataset_access",
        "full_stage3b_campaign_complete",
    ):
        _require_equal(after.get(field), False, label=f"after.{field}")

    return {
        "gate": gate,
        "seal": seal,
        "decision": decision,
        "analysis_output_root": output_root,
        "audit_root": audit_root,
        "seal_root": seal_root,
    }


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


def _archive_tree(source_root: Path, output: Path, archive_root: str) -> None:
    members = [
        (path, f"{archive_root}/{path.relative_to(source_root).as_posix()}")
        for path in source_root.rglob("*")
        if path.is_file()
    ]
    _write_reproducible_tar_gz(output, members)


def _write_notes(output_root: Path, publication_commit: str) -> PublicationAsset:
    output = output_root / "PUBLICATION-NOTES.md"
    output.write_text(
        "\n".join(
            (
                "# Stage 3B matched descriptive-analysis publication v1",
                "",
                "This publication preserves the sealed 18-file output byte for byte.",
                "The original reports retain their generated-state wording; the external",
                "audit, seal, publication gate, and this release record define the later",
                "publication state without mutating those reports.",
                "",
                f"- publication action commit: `{publication_commit}`",
                f"- publication action tag: `{PUBLICATION_ACTION_TAG}`",
                f"- evidence release tag: `{MATCHED_EVIDENCE_RELEASE_TAG}`",
                f"- analysis output registry: `{EXPECTED_OUTPUT_REGISTRY_SHA256}`",
                f"- analysis output seal: `{EXPECTED_SEAL_DIGEST}`",
                "- `isolated_layer_vjp`: `reject_or_revise`",
                "- `composite_vjp`: `reject_or_revise`",
                "- qualified configurations: `0/16` for every candidate × method",
                "- results publication permitted after successful release action: `true`",
                "- superiority claims permitted: `false`",
                "- EX-IF0 opened: `false`",
                "- test dataset access: `false`",
                "- full Stage 3B campaign complete: `false`",
                "",
                "The next formal transition is a separate EX-IF0 freeze.",
                "",
            )
        ),
        encoding="utf-8",
    )
    return PublicationAsset(output, "publication_notes")


def _write_manifest(
    output_root: Path,
    assets: Iterable[PublicationAsset],
    *,
    publication_commit: str,
) -> PublicationAsset:
    output = output_root / "PUBLICATION-MANIFEST.json"
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
        "status": "publication_assets_ready",
        "publication_gate_id": PUBLICATION_GATE_ID,
        "publication_action_tag": PUBLICATION_ACTION_TAG,
        "publication_action_commit": publication_commit,
        "evidence_release_tag": MATCHED_EVIDENCE_RELEASE_TAG,
        "analysis_output_registry_sha256": EXPECTED_OUTPUT_REGISTRY_SHA256,
        "analysis_output_seal_digest": EXPECTED_SEAL_DIGEST,
        "candidate_decisions": EXPECTED_CANDIDATE_DECISIONS,
        "results_publication_permitted": True,
        "release_publication_permitted": True,
        "release_publication_complete": False,
        "superiority_claim_permitted": False,
        "ex_if0_opened": False,
        "policy_activation_permitted": False,
        "test_dataset_access": False,
        "full_stage3b_campaign_complete": False,
        "assets": records,
    }
    output.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return PublicationAsset(output, "publication_manifest")


def _write_checksums(output_root: Path) -> PublicationAsset:
    output = output_root / "PUBLICATION-SHA256SUMS"
    paths = sorted(
        path
        for path in output_root.iterdir()
        if path.is_file() and path.name != output.name
    )
    output.write_text(
        "".join(f"{sha256_file(path)}  {path.name}\n" for path in paths),
        encoding="utf-8",
    )
    return PublicationAsset(output, "publication_checksum_registry")


def package_publication_assets(
    project_root: Path,
    output_root: Path,
    *,
    publication_tag: str,
    publication_commit: str,
) -> dict[str, object]:
    if publication_tag != PUBLICATION_ACTION_TAG:
        raise Stage3BMatchedPublicationError(
            f"unexpected publication tag: {publication_tag}"
        )
    output = output_root.expanduser().resolve()
    if output.exists() and any(output.iterdir()):
        raise Stage3BMatchedPublicationError(
            f"output directory is not empty: {output}"
        )
    output.mkdir(parents=True, exist_ok=True)

    validated = validate_publication_inputs(project_root)
    analysis_root = validated["analysis_output_root"]
    audit_root = validated["audit_root"]
    seal_root = validated["seal_root"]
    if not isinstance(analysis_root, Path):
        raise Stage3BMatchedPublicationError("analysis root validation failed")
    if not isinstance(audit_root, Path) or not isinstance(seal_root, Path):
        raise Stage3BMatchedPublicationError("seal root validation failed")

    analysis_archive = output / (
        "stage3b-matched-descriptive-analysis-sealed-output-v1.tar.gz"
    )
    _archive_tree(
        analysis_root,
        analysis_archive,
        "stage3b-matched-descriptive-analysis-sealed-output-v1",
    )
    provenance_archive = output / (
        "stage3b-matched-descriptive-analysis-audit-seal-v1.tar.gz"
    )
    provenance_members = [
        (
            path,
            "stage3b-matched-descriptive-analysis-audit-seal-v1/"
            f"audit/{path.relative_to(audit_root).as_posix()}",
        )
        for path in audit_root.rglob("*")
        if path.is_file()
    ] + [
        (
            path,
            "stage3b-matched-descriptive-analysis-audit-seal-v1/"
            f"seal/{path.relative_to(seal_root).as_posix()}",
        )
        for path in seal_root.rglob("*")
        if path.is_file()
    ]
    _write_reproducible_tar_gz(provenance_archive, provenance_members)

    assets: list[PublicationAsset] = [
        PublicationAsset(analysis_archive, "sealed_analysis_output"),
        PublicationAsset(provenance_archive, "audit_and_external_seal"),
    ]
    notes = _write_notes(output, publication_commit)
    assets.append(notes)
    manifest = _write_manifest(
        output,
        assets,
        publication_commit=publication_commit,
    )
    assets.append(manifest)
    checksums = _write_checksums(output)

    return {
        "status": "publication_assets_ready",
        "publication_gate_id": PUBLICATION_GATE_ID,
        "publication_action_tag": publication_tag,
        "publication_action_commit": publication_commit,
        "evidence_release_tag": MATCHED_EVIDENCE_RELEASE_TAG,
        "asset_count": len(assets) + 1,
        "output_root": str(output),
        "checksum_registry": str(checksums.path),
        "results_publication_permitted": True,
        "release_publication_permitted": True,
        "release_publication_complete": False,
        "superiority_claim_permitted": False,
        "ex_if0_opened": False,
    }
