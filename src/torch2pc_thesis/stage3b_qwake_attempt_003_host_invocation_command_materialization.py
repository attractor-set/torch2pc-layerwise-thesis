"""Pure command-materialization authoring for QWake Attempt-003.

This module binds the verified host preflight to a normalized command template.
It can validate an already-constructed host invocation and can build the exact
future durable command-record bytes as data. It contains no process spawner,
performs no Docker operation, writes no file, consumes no authorization, and
does not invoke runtime or model code.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import Final, cast

from torch2pc_thesis.stage3b_qwake_attempt_003_host_invocation_chain import (
    MaterializedHostInvocation,
)

ATTEMPT_ID: Final = "stage3b-qwake-lc4-runtime-validation-v1-attempt-003"
CONTRACT_ID: Final = (
    "stage3b-qwake-attempt-003-host-invocation-command-materialization-contract-v1"
)
CONTRACT_STATUS: Final = (
    "attempt_003_host_invocation_command_materialization_authored_not_materialized"
)
AUTHORIZED_PARENT_HEAD: Final = "d63fca319436e530e8a8dbe8ce18fefa4ee70433"
AUTHORIZED_PARENT_TREE: Final = "5d54235c4dadb3affe48faf5aab9e8a47556aee6"
AUTHORIZED_BRANCH: Final = (
    "research/stage3b-qwake-attempt-003-host-invocation-command-materialization-authoring"
)
HOST_INVOCATION_CONTRACT_SHA256: Final = (
    "sha256:da89fd78683e01bdcfe85402b819a6c8e31ab3c496aa8ac9190f8d4480664191"
)
AUTHORIZATION_SHA256: Final = (
    "sha256:46baed5cebc1efe4abf68c21652775eee5c1123df09465d332c151303d890d63"
)
FREEZE_SHA256: Final = (
    "sha256:82e7509a0d2627f8b91daa34049307da573619b740a2022b72b922edcd07898e"
)
PREFLIGHT_CLAIMED_AT_UTC: Final = "2026-08-10T04:03:59Z"
PREFLIGHT_INVOCATION_SHA256: Final = (
    "sha256:fbac1c0e61b6f93395895f03dce5cb3e464e329b08990cdc8642149fff7feecd"
)
IMAGE_INSPECTION_SHA256: Final = (
    "sha256:6a8c37769fb3399ca7da4d2be3dd918944266b2fa61667cb623c9f5c5685cf36"
)
COMMAND_TEMPLATE_SHA256: Final = (
    "sha256:01fdd895e65ee59970e9a67c500ec4523e0039d468fe8e9553b0e4e2a53a7d89"
)
CLAIMED_AT_PLACEHOLDER: Final = "__ATTEMPT003_CLAIMED_AT_UTC__"
CLAIMED_AT_POLICY: Final = (
    "materialization_time_operator_supplied_rfc3339_utc_seconds"
)
EXECUTION_ROOT: Final = (
    "/home/dzmitry-prychyna/torch2pc-layerwise-thesis-attempt003-execution-root"
)
COMMAND_RECORD_RELATIVE: Final = (
    "results/stage-3/"
    "qwake-lc4-runtime-validation-v1-attempt-003.host-invocation-command.json"
)
LEASE_ACKNOWLEDGEMENT: Final = (
    "CLAIM_QWAKE_LC4_ATTEMPT_003_FROM_CORRECTED_EXECUTION_FREEZE"
)
HOST_COMMAND_RECORD_ID: Final = "stage3b-qwake-attempt-003-host-invocation-command-v1"

HOST_RESOURCES: Final = (('HOST_UID', '1000'),
 ('HOST_GID', '1000'),
 ('VIDEO_GID', '44'),
 ('RENDER_GID', '992'),
 ('HIP_VISIBLE_DEVICES', '0'),
 ('CPUSET_GPU', '0-7'),
 ('MEM_LIMIT', '48g'),
 ('SHM_SIZE', '8g'),
 ('TMPFS_SIZE', '4g'),
 ('OMP_NUM_THREADS', '8'),
 ('MKL_NUM_THREADS', '8'),
 ('OPENBLAS_NUM_THREADS', '8'),
 ('NUMEXPR_NUM_THREADS', '8'))
PREFLIGHT_ARGV: Final = ('docker',
 'run',
 '--rm',
 '--init',
 '--network',
 'none',
 '--read-only',
 '--security-opt',
 'no-new-privileges',
 '--cap-drop',
 'ALL',
 '--user',
 '1000:1000',
 '--group-add',
 '44',
 '--group-add',
 '992',
 '--device',
 '/dev/kfd:/dev/kfd:rwm',
 '--device',
 '/dev/dri:/dev/dri:rwm',
 '--cpuset-cpus',
 '0-7',
 '--memory',
 '48g',
 '--shm-size',
 '8g',
 '--tmpfs',
 '/tmp:rw,nosuid,nodev,mode=1777,size=4g',
 '--workdir',
 '/workspace',
 '--env',
 'HOME=/tmp/home',
 '--env',
 'PYTHONDONTWRITEBYTECODE=1',
 '--env',
 'PYTHONHASHSEED=0',
 '--env',
 'PYTHONUNBUFFERED=1',
 '--env',
 'SOURCE_GIT_COMMIT=541b34a57297d2c5a82851bd846b583d4904fba6',
 '--env',
 'EXPERIMENT_IMAGE_DIGEST=sha256:aec2178f1de409143553ccaecb34b2d0e4d19332040fce56742e422f770ef188',
 '--env',
 'EXPERIMENT_IMAGE_REPO_DIGEST=torch2pc-layerwise-thesis@sha256:aec2178f1de409143553ccaecb34b2d0e4d19332040fce56742e422f770ef188',
 '--env',
 'HIP_VISIBLE_DEVICES=0',
 '--env',
 'OMP_NUM_THREADS=8',
 '--env',
 'MKL_NUM_THREADS=8',
 '--env',
 'OPENBLAS_NUM_THREADS=8',
 '--env',
 'NUMEXPR_NUM_THREADS=8',
 '--volume',
 '/home/dzmitry-prychyna/torch2pc-layerwise-thesis-attempt003-execution-root/experiments/frozen:/workspace/experiments/frozen:ro',
 '--volume',
 '/home/dzmitry-prychyna/torch2pc-layerwise-thesis-attempt003-execution-root/external/Torch2PC:/workspace/external/Torch2PC:ro',
 '--volume',
 '/home/dzmitry-prychyna/torch2pc-layerwise-thesis-attempt003-execution-root/results:/workspace/results:rw',
 'torch2pc-layerwise-thesis@sha256:aec2178f1de409143553ccaecb34b2d0e4d19332040fce56742e422f770ef188',
 'python',
 '/workspace/scripts/run_stage3b_qwake_attempt_003_authorized_runtime.py',
 '--project-root',
 '/workspace',
 '--torch2pc-dir',
 '/workspace/external/Torch2PC',
 '--claimed-at-utc',
 '2026-08-10T04:03:59Z',
 '--operator-acknowledgement',
 'CLAIM_QWAKE_LC4_ATTEMPT_003_FROM_CORRECTED_EXECUTION_FREEZE')
PREFLIGHT_ENVIRONMENT: Final = (('HOME', '/tmp/home'),
 ('PYTHONDONTWRITEBYTECODE', '1'),
 ('PYTHONHASHSEED', '0'),
 ('PYTHONUNBUFFERED', '1'),
 ('SOURCE_GIT_COMMIT', '541b34a57297d2c5a82851bd846b583d4904fba6'),
 ('EXPERIMENT_IMAGE_DIGEST',
  'sha256:aec2178f1de409143553ccaecb34b2d0e4d19332040fce56742e422f770ef188'),
 ('EXPERIMENT_IMAGE_REPO_DIGEST',
  'torch2pc-layerwise-thesis@sha256:aec2178f1de409143553ccaecb34b2d0e4d19332040fce56742e422f770ef188'),
 ('HIP_VISIBLE_DEVICES', '0'),
 ('OMP_NUM_THREADS', '8'),
 ('MKL_NUM_THREADS', '8'),
 ('OPENBLAS_NUM_THREADS', '8'),
 ('NUMEXPR_NUM_THREADS', '8'))
PREFLIGHT_MOUNT_SOURCES: Final = ('/home/dzmitry-prychyna/torch2pc-layerwise-thesis-attempt003-execution-root/experiments/frozen',
 '/home/dzmitry-prychyna/torch2pc-layerwise-thesis-attempt003-execution-root/external/Torch2PC',
 '/home/dzmitry-prychyna/torch2pc-layerwise-thesis-attempt003-execution-root/results')

_CONTRACT_PAYLOAD: Final = {'schema_version': 1,
 'contract_id': 'stage3b-qwake-attempt-003-host-invocation-command-materialization-contract-v1',
 'status': 'attempt_003_host_invocation_command_materialization_authored_not_materialized',
 'attempt_id': 'stage3b-qwake-lc4-runtime-validation-v1-attempt-003',
 'authorized_parent_head': 'd63fca319436e530e8a8dbe8ce18fefa4ee70433',
 'authorized_parent_tree': '5d54235c4dadb3affe48faf5aab9e8a47556aee6',
 'authorized_branch': 'research/stage3b-qwake-attempt-003-host-invocation-command-materialization-authoring',
 'host_invocation_chain_authoring_commit': 'de9d8a299af8f60b4916cf0dacd2bc7ecb93a764',
 'host_invocation_chain_merge_commit': 'd63fca319436e530e8a8dbe8ce18fefa4ee70433',
 'host_invocation_contract_id': 'stage3b-qwake-attempt-003-host-invocation-contract-v1',
 'host_invocation_contract_sha256': 'sha256:da89fd78683e01bdcfe85402b819a6c8e31ab3c496aa8ac9190f8d4480664191',
 'authorization_sha256': 'sha256:46baed5cebc1efe4abf68c21652775eee5c1123df09465d332c151303d890d63',
 'freeze_sha256': 'sha256:82e7509a0d2627f8b91daa34049307da573619b740a2022b72b922edcd07898e',
 'source_commit': '541b34a57297d2c5a82851bd846b583d4904fba6',
 'torch2pc_commit': 'b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4',
 'image_digest': 'sha256:aec2178f1de409143553ccaecb34b2d0e4d19332040fce56742e422f770ef188',
 'image_repo_digest': 'torch2pc-layerwise-thesis@sha256:aec2178f1de409143553ccaecb34b2d0e4d19332040fce56742e422f770ef188',
 'base_image': 'rocm/pytorch@sha256:96a2fb24dec9896e2f8238178f0c49d0dcc4c7dcc597be09e4564316bd86d191',
 'image_inspection_sha256': 'sha256:6a8c37769fb3399ca7da4d2be3dd918944266b2fa61667cb623c9f5c5685cf36',
 'execution_root': '/home/dzmitry-prychyna/torch2pc-layerwise-thesis-attempt003-execution-root',
 'composite_frozen_tree_sha256': '4b50d9d8ab3b085c8c965bbffd2249476ddb3e97f8a055533cb88d24b916dfd1',
 'composite_frozen_file_count': 329,
 'composite_frozen_bytes': 13425361,
 'host_resources': [['HOST_UID', '1000'],
                    ['HOST_GID', '1000'],
                    ['VIDEO_GID', '44'],
                    ['RENDER_GID', '992'],
                    ['HIP_VISIBLE_DEVICES', '0'],
                    ['CPUSET_GPU', '0-7'],
                    ['MEM_LIMIT', '48g'],
                    ['SHM_SIZE', '8g'],
                    ['TMPFS_SIZE', '4g'],
                    ['OMP_NUM_THREADS', '8'],
                    ['MKL_NUM_THREADS', '8'],
                    ['OPENBLAS_NUM_THREADS', '8'],
                    ['NUMEXPR_NUM_THREADS', '8']],
 'preflight_observed': True,
 'preflight_claimed_at_utc': '2026-08-10T04:03:59Z',
 'preflight_claimed_at_authoritative_for_execution': False,
 'preflight_invocation_sha256': 'sha256:fbac1c0e61b6f93395895f03dce5cb3e464e329b08990cdc8642149fff7feecd',
 'preflight_argv': ['docker',
                    'run',
                    '--rm',
                    '--init',
                    '--network',
                    'none',
                    '--read-only',
                    '--security-opt',
                    'no-new-privileges',
                    '--cap-drop',
                    'ALL',
                    '--user',
                    '1000:1000',
                    '--group-add',
                    '44',
                    '--group-add',
                    '992',
                    '--device',
                    '/dev/kfd:/dev/kfd:rwm',
                    '--device',
                    '/dev/dri:/dev/dri:rwm',
                    '--cpuset-cpus',
                    '0-7',
                    '--memory',
                    '48g',
                    '--shm-size',
                    '8g',
                    '--tmpfs',
                    '/tmp:rw,nosuid,nodev,mode=1777,size=4g',
                    '--workdir',
                    '/workspace',
                    '--env',
                    'HOME=/tmp/home',
                    '--env',
                    'PYTHONDONTWRITEBYTECODE=1',
                    '--env',
                    'PYTHONHASHSEED=0',
                    '--env',
                    'PYTHONUNBUFFERED=1',
                    '--env',
                    'SOURCE_GIT_COMMIT=541b34a57297d2c5a82851bd846b583d4904fba6',
                    '--env',
                    'EXPERIMENT_IMAGE_DIGEST=sha256:aec2178f1de409143553ccaecb34b2d0e4d19332040fce56742e422f770ef188',
                    '--env',
                    'EXPERIMENT_IMAGE_REPO_DIGEST=torch2pc-layerwise-thesis@sha256:aec2178f1de409143553ccaecb34b2d0e4d19332040fce56742e422f770ef188',
                    '--env',
                    'HIP_VISIBLE_DEVICES=0',
                    '--env',
                    'OMP_NUM_THREADS=8',
                    '--env',
                    'MKL_NUM_THREADS=8',
                    '--env',
                    'OPENBLAS_NUM_THREADS=8',
                    '--env',
                    'NUMEXPR_NUM_THREADS=8',
                    '--volume',
                    '/home/dzmitry-prychyna/torch2pc-layerwise-thesis-attempt003-execution-root/experiments/frozen:/workspace/experiments/frozen:ro',
                    '--volume',
                    '/home/dzmitry-prychyna/torch2pc-layerwise-thesis-attempt003-execution-root/external/Torch2PC:/workspace/external/Torch2PC:ro',
                    '--volume',
                    '/home/dzmitry-prychyna/torch2pc-layerwise-thesis-attempt003-execution-root/results:/workspace/results:rw',
                    'torch2pc-layerwise-thesis@sha256:aec2178f1de409143553ccaecb34b2d0e4d19332040fce56742e422f770ef188',
                    'python',
                    '/workspace/scripts/run_stage3b_qwake_attempt_003_authorized_runtime.py',
                    '--project-root',
                    '/workspace',
                    '--torch2pc-dir',
                    '/workspace/external/Torch2PC',
                    '--claimed-at-utc',
                    '2026-08-10T04:03:59Z',
                    '--operator-acknowledgement',
                    'CLAIM_QWAKE_LC4_ATTEMPT_003_FROM_CORRECTED_EXECUTION_FREEZE'],
 'preflight_environment': [['HOME', '/tmp/home'],
                           ['PYTHONDONTWRITEBYTECODE', '1'],
                           ['PYTHONHASHSEED', '0'],
                           ['PYTHONUNBUFFERED', '1'],
                           ['SOURCE_GIT_COMMIT',
                            '541b34a57297d2c5a82851bd846b583d4904fba6'],
                           ['EXPERIMENT_IMAGE_DIGEST',
                            'sha256:aec2178f1de409143553ccaecb34b2d0e4d19332040fce56742e422f770ef188'],
                           ['EXPERIMENT_IMAGE_REPO_DIGEST',
                            'torch2pc-layerwise-thesis@sha256:aec2178f1de409143553ccaecb34b2d0e4d19332040fce56742e422f770ef188'],
                           ['HIP_VISIBLE_DEVICES', '0'],
                           ['OMP_NUM_THREADS', '8'],
                           ['MKL_NUM_THREADS', '8'],
                           ['OPENBLAS_NUM_THREADS', '8'],
                           ['NUMEXPR_NUM_THREADS', '8']],
 'preflight_mount_sources': ['/home/dzmitry-prychyna/torch2pc-layerwise-thesis-attempt003-execution-root/experiments/frozen',
                             '/home/dzmitry-prychyna/torch2pc-layerwise-thesis-attempt003-execution-root/external/Torch2PC',
                             '/home/dzmitry-prychyna/torch2pc-layerwise-thesis-attempt003-execution-root/results'],
 'claimed_at_policy': 'materialization_time_operator_supplied_rfc3339_utc_seconds',
 'claimed_at_placeholder': '__ATTEMPT003_CLAIMED_AT_UTC__',
 'command_template_sha256': 'sha256:01fdd895e65ee59970e9a67c500ec4523e0039d468fe8e9553b0e4e2a53a7d89',
 'lease_acknowledgement': 'CLAIM_QWAKE_LC4_ATTEMPT_003_FROM_CORRECTED_EXECUTION_FREEZE',
 'command_record_relative': 'results/stage-3/qwake-lc4-runtime-validation-v1-attempt-003.host-invocation-command.json',
 'command_record_atomic_persistence_required': True,
 'materialization_requires_exact_template_match': True,
 'materialization_requires_exact_image_inspection_match': True,
 'materialization_requires_exact_composite_root_match': True,
 'materialization_requires_fresh_claimed_at': True,
 'host_invocation_chain_authored': True,
 'host_command_constructor_authored': True,
 'command_materialization_contract_authored': True,
 'authoritative_host_command_materialized': False,
 'command_persisted': False,
 'host_process_spawner_present': False,
 'docker_run_implemented': False,
 'runtime_execution_permitted': False,
 'authorization_used': False,
 'authorization_consumed': False,
 'attempt_started': False,
 'execution_lease_materialized': False,
 'runtime_execution_started': False,
 'runtime_execution_performed': False,
 'model_code_invoked': False,
 'dataset_accessed': False,
 'publication_permitted': False,
 'post_materialization_next_gate': 'attempt003_host_invocation_process_spawner_authoring'}

__all__ = [
    "ATTEMPT_ID",
    "AUTHORIZED_BRANCH",
    "AUTHORIZED_PARENT_HEAD",
    "CLAIMED_AT_PLACEHOLDER",
    "COMMAND_RECORD_RELATIVE",
    "COMMAND_TEMPLATE_SHA256",
    "CONTRACT_ID",
    "CONTRACT_STATUS",
    "EXECUTION_ROOT",
    "HOST_RESOURCES",
    "IMAGE_INSPECTION_SHA256",
    "PREFLIGHT_CLAIMED_AT_UTC",
    "PREFLIGHT_INVOCATION_SHA256",
    "QWakeAttempt003CommandMaterializationError",
    "build_attempt_003_command_materialization_contract",
    "build_attempt_003_host_command_record",
    "build_preflight_invocation_evidence",
    "canonical_json",
    "command_template_sha256",
    "load_attempt_003_command_materialization_contract",
    "require_attempt_003_command_materialization_contract",
    "require_materialized_invocation_matches_contract",
    "sha256_object",
]


class QWakeAttempt003CommandMaterializationError(RuntimeError):
    """Raised when Attempt-003 command-materialization evidence differs."""


def canonical_json(value: object) -> str:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    )


def sha256_object(value: object) -> str:
    return "sha256:" + hashlib.sha256(
        canonical_json(value).encode("utf-8")
    ).hexdigest()


def _require_sha256(value: str, field_name: str) -> None:
    if re.fullmatch(r"sha256:[0-9a-f]{64}", value) is None:
        raise QWakeAttempt003CommandMaterializationError(
            f"invalid SHA-256 field: {field_name}"
        )


def _require_rfc3339_seconds(value: str) -> None:
    if (
        re.fullmatch(
            r"[0-9]{4}-[0-9]{2}-[0-9]{2}T"
            r"[0-9]{2}:[0-9]{2}:[0-9]{2}Z",
            value,
        )
        is None
    ):
        raise QWakeAttempt003CommandMaterializationError(
            "claimed_at_utc must be RFC3339 UTC seconds"
        )


def build_attempt_003_command_materialization_contract() -> dict[str, object]:
    payload = json.loads(canonical_json(_CONTRACT_PAYLOAD))
    payload["contract_sha256"] = sha256_object(payload)
    require_attempt_003_command_materialization_contract(payload)
    return cast(dict[str, object], payload)


def require_attempt_003_command_materialization_contract(
    contract: object,
) -> None:
    if not isinstance(contract, dict):
        raise QWakeAttempt003CommandMaterializationError(
            "command-materialization contract is not an object"
        )
    observed = dict(contract)
    digest = observed.pop("contract_sha256", None)
    if not isinstance(digest, str):
        raise QWakeAttempt003CommandMaterializationError(
            "command-materialization contract digest is absent"
        )
    _require_sha256(digest, "contract_sha256")
    if digest != sha256_object(observed):
        raise QWakeAttempt003CommandMaterializationError(
            "command-materialization contract digest differs"
        )
    expected_payload = json.loads(canonical_json(_CONTRACT_PAYLOAD))
    if observed != expected_payload:
        raise QWakeAttempt003CommandMaterializationError(
            "command-materialization contract payload differs"
        )


def load_attempt_003_command_materialization_contract(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise QWakeAttempt003CommandMaterializationError(
            "command-materialization contract JSON is invalid"
        ) from exc
    require_attempt_003_command_materialization_contract(value)
    return cast(dict[str, object], value)


def _invocation_payload(invocation: MaterializedHostInvocation) -> dict[str, object]:
    payload = asdict(invocation)
    payload.pop("invocation_sha256")
    return cast(dict[str, object], payload)


def _normalize_argv(argv: tuple[str, ...], claimed_at_utc: str) -> tuple[str, ...]:
    values = list(argv)
    matches = [index for index, value in enumerate(values) if value == "--claimed-at-utc"]
    if len(matches) != 1:
        raise QWakeAttempt003CommandMaterializationError(
            "claimed-at argv marker count differs"
        )
    index = matches[0]
    if index + 1 >= len(values) or values[index + 1] != claimed_at_utc:
        raise QWakeAttempt003CommandMaterializationError(
            "claimed-at argv value differs"
        )
    values[index + 1] = CLAIMED_AT_PLACEHOLDER
    return tuple(values)


def _template_payload(
    invocation: MaterializedHostInvocation,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "host_invocation_contract_sha256": HOST_INVOCATION_CONTRACT_SHA256,
        "image_inspection_sha256": IMAGE_INSPECTION_SHA256,
        "argv_template": _normalize_argv(
            invocation.argv,
            invocation.claimed_at_utc,
        ),
        "environment": invocation.environment,
        "mount_sources": invocation.mount_sources,
        "host_resources": HOST_RESOURCES,
        "claimed_at_policy": CLAIMED_AT_POLICY,
        "claimed_at_placeholder": CLAIMED_AT_PLACEHOLDER,
        "lease_acknowledgement": LEASE_ACKNOWLEDGEMENT,
    }


def command_template_sha256(invocation: MaterializedHostInvocation) -> str:
    return sha256_object(_template_payload(invocation))


def _require_closed_invocation(invocation: MaterializedHostInvocation) -> None:
    closed = {
        "shell_interpretation_used": False,
        "environment_inherited": False,
        "subprocess_spawned": False,
        "container_created": False,
        "authorization_consumed": False,
        "attempt_started": False,
        "execution_lease_created": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
    }
    for name, expected in closed.items():
        if getattr(invocation, name) != expected:
            raise QWakeAttempt003CommandMaterializationError(
                f"materialized host invocation opened effect: {name}"
            )


def require_materialized_invocation_matches_contract(
    invocation: MaterializedHostInvocation,
    contract: object,
    *,
    reject_preflight_claim_time: bool = True,
) -> None:
    require_attempt_003_command_materialization_contract(contract)
    _require_rfc3339_seconds(invocation.claimed_at_utc)
    _require_closed_invocation(invocation)

    if invocation.contract_sha256 != HOST_INVOCATION_CONTRACT_SHA256:
        raise QWakeAttempt003CommandMaterializationError(
            "host invocation contract digest differs"
        )
    if invocation.image_inspection_sha256 != IMAGE_INSPECTION_SHA256:
        raise QWakeAttempt003CommandMaterializationError(
            "image inspection digest differs"
        )
    expected_invocation_digest = sha256_object(_invocation_payload(invocation))
    if invocation.invocation_sha256 != expected_invocation_digest:
        raise QWakeAttempt003CommandMaterializationError(
            "host invocation digest differs"
        )
    if reject_preflight_claim_time and invocation.claimed_at_utc == PREFLIGHT_CLAIMED_AT_UTC:
        raise QWakeAttempt003CommandMaterializationError(
            "preflight claimed_at_utc is not authoritative for materialization"
        )

    preflight = build_preflight_invocation_evidence(contract)
    if _normalize_argv(
        invocation.argv,
        invocation.claimed_at_utc,
    ) != _normalize_argv(
        preflight.argv,
        preflight.claimed_at_utc,
    ):
        raise QWakeAttempt003CommandMaterializationError(
            "normalized host command template differs"
        )
    if invocation.environment != preflight.environment:
        raise QWakeAttempt003CommandMaterializationError(
            "host command environment differs"
        )
    if invocation.mount_sources != preflight.mount_sources:
        raise QWakeAttempt003CommandMaterializationError(
            "host command mount sources differ"
        )
    if command_template_sha256(invocation) != COMMAND_TEMPLATE_SHA256:
        raise QWakeAttempt003CommandMaterializationError(
            "host command template digest differs"
        )


def build_preflight_invocation_evidence(
    contract: object,
) -> MaterializedHostInvocation:
    require_attempt_003_command_materialization_contract(contract)
    typed = cast(dict[str, object], contract)
    invocation = MaterializedHostInvocation(
        schema_version=1,
        contract_sha256=HOST_INVOCATION_CONTRACT_SHA256,
        image_inspection_sha256=IMAGE_INSPECTION_SHA256,
        claimed_at_utc=PREFLIGHT_CLAIMED_AT_UTC,
        argv=tuple(cast(list[str], typed["preflight_argv"])),
        environment=tuple(
            (pair[0], pair[1])
            for pair in cast(list[list[str]], typed["preflight_environment"])
        ),
        mount_sources=tuple(cast(list[str], typed["preflight_mount_sources"])),
        shell_interpretation_used=False,
        environment_inherited=False,
        subprocess_spawned=False,
        container_created=False,
        authorization_consumed=False,
        attempt_started=False,
        execution_lease_created=False,
        runtime_execution_started=False,
        runtime_execution_performed=False,
        invocation_sha256=PREFLIGHT_INVOCATION_SHA256,
    )
    _require_closed_invocation(invocation)
    if invocation.invocation_sha256 != sha256_object(_invocation_payload(invocation)):
        raise QWakeAttempt003CommandMaterializationError(
            "preflight invocation evidence digest differs"
        )
    if command_template_sha256(invocation) != COMMAND_TEMPLATE_SHA256:
        raise QWakeAttempt003CommandMaterializationError(
            "preflight command template digest differs"
        )
    return invocation


def build_attempt_003_host_command_record(
    invocation: MaterializedHostInvocation,
    contract: object,
) -> dict[str, object]:
    require_materialized_invocation_matches_contract(invocation, contract)
    contract_typed = cast(dict[str, object], contract)
    payload: dict[str, object] = {
        "schema_version": 1,
        "record_id": HOST_COMMAND_RECORD_ID,
        "attempt_id": ATTEMPT_ID,
        "materialization_contract_sha256": contract_typed["contract_sha256"],
        "host_invocation_contract_sha256": HOST_INVOCATION_CONTRACT_SHA256,
        "image_inspection_sha256": IMAGE_INSPECTION_SHA256,
        "command_template_sha256": COMMAND_TEMPLATE_SHA256,
        "claimed_at_utc": invocation.claimed_at_utc,
        "invocation_sha256": invocation.invocation_sha256,
        "argv": invocation.argv,
        "environment": invocation.environment,
        "mount_sources": invocation.mount_sources,
        "host_resources": HOST_RESOURCES,
        "command_record_relative": COMMAND_RECORD_RELATIVE,
        "authoritative_host_command_materialized": True,
        "command_persisted": True,
        "host_process_spawned": False,
        "docker_run_invoked": False,
        "container_created": False,
        "authorization_used": False,
        "authorization_consumed": False,
        "attempt_started": False,
        "execution_lease_materialized": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "runtime_execution_permitted": False,
        "model_code_invoked": False,
        "dataset_accessed": False,
        "publication_permitted": False,
    }
    record = dict(payload)
    record["record_sha256"] = sha256_object(payload)
    return record
