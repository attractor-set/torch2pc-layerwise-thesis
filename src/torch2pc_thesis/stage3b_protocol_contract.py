"""Machine-readable Stage 3B B0 protocol contract."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Final, cast

from torch2pc_thesis.stage3b_execution import Stage3BExecutionError

B0_PROTOCOL_CONTRACT_RELATIVE_PATH: Final[Path] = Path(
    "experiments/planned/STAGE3B-B0-PROTOCOL-CONTRACT.json"
)
B0_PROTOCOL_CONTRACT_SCHEMA_VERSION: Final[int] = 1
B0_PROTOCOL_CONTRACT_SCOPE: Final[str] = "stage3b_b0_rocm_canonical_v1"

_REPOSITORY_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
_DEFAULT_CONTRACT_PATH: Final[Path] = (
    _REPOSITORY_ROOT / B0_PROTOCOL_CONTRACT_RELATIVE_PATH
)


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def _contract_digest(value: Mapping[str, object]) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _lane_pairs(value: object, *, field: str) -> tuple[tuple[str, str], ...]:
    if not isinstance(value, list):
        raise Stage3BExecutionError(f"{field} must be a list")
    pairs: list[tuple[str, str]] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise Stage3BExecutionError(f"{field} entries must be objects")
        pair = (
            str(item.get("device", "")).strip().lower(),
            str(item.get("dtype", "")).strip().lower(),
        )
        if not all(pair):
            raise Stage3BExecutionError(f"{field} entries require device and dtype")
        pairs.append(pair)
    if len(pairs) != len(set(pairs)):
        raise Stage3BExecutionError(f"{field} contains duplicate lanes")
    return tuple(pairs)


def validate_b0_protocol_contract(contract: Mapping[str, object]) -> None:
    """Validate the exact ROCm-only B0 canonical design."""

    if contract.get("schema_version") != B0_PROTOCOL_CONTRACT_SCHEMA_VERSION:
        raise Stage3BExecutionError("unsupported Stage 3B B0 protocol contract")
    if contract.get("contract_scope") != B0_PROTOCOL_CONTRACT_SCOPE:
        raise Stage3BExecutionError("unexpected Stage 3B B0 protocol scope")
    if contract.get("campaign_id") != "stage3b-profiling-locality-v1":
        raise Stage3BExecutionError("unexpected Stage 3B B0 campaign id")
    if contract.get("candidate_id") != "stage2_baseline":
        raise Stage3BExecutionError("unexpected Stage 3B B0 candidate")
    if contract.get("manifest_cell_count") != 336:
        raise Stage3BExecutionError("Stage 3B manifest contract must remain 336 cells")
    if contract.get("canonical_cell_count") != 96:
        raise Stage3BExecutionError(
            "Stage 3B B0 canonical contract must remain 96 cells"
        )
    if contract.get("execution_count") != 96:
        raise Stage3BExecutionError(
            "Stage 3B B0 canonical execution count must be 96, not a lane product"
        )

    canonical_lanes = _lane_pairs(
        contract.get("canonical_lanes"), field="canonical_lanes"
    )
    if canonical_lanes != (("rocm", "float32"),):
        raise Stage3BExecutionError(
            "Stage 3B B0 canonical lane must be exactly rocm/float32"
        )

    control_lanes = _lane_pairs(
        contract.get("engineering_control_lanes"),
        field="engineering_control_lanes",
    )
    if control_lanes != (("cpu", "float64"),):
        raise Stage3BExecutionError(
            "Stage 3B B0 engineering control lane must be cpu/float64"
        )

    raw_controls = cast(
        list[Mapping[str, object]], contract["engineering_control_lanes"]
    )
    cpu_control = raw_controls[0]
    if cpu_control.get("canonical") is not False:
        raise Stage3BExecutionError("CPU control cannot be canonical")
    if cpu_control.get("required_for_campaign_completion") is not False:
        raise Stage3BExecutionError("CPU control cannot gate campaign completion")
    if cpu_control.get("confirmatory_performance_evidence") is not False:
        raise Stage3BExecutionError("CPU control cannot be confirmatory evidence")

    if contract.get("canonical_protocol") != {
        "warmup_steps": 20,
        "measured_steps": 50,
        "repetitions": 5,
    }:
        raise Stage3BExecutionError(
            "Stage 3B B0 canonical protocol must remain 20/50/5"
        )
    if contract.get("test_dataset_access") is not False:
        raise Stage3BExecutionError("Stage 3B B0 contract cannot allow test access")
    if contract.get("results_publication_permitted") is not False:
        raise Stage3BExecutionError(
            "Stage 3B B0 contract cannot permit result publication"
        )


def load_b0_protocol_contract(path: Path | None = None) -> dict[str, object]:
    """Load and validate the repository protocol contract."""

    resolved = (path or _DEFAULT_CONTRACT_PATH).expanduser().resolve()
    try:
        raw = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise Stage3BExecutionError(
            f"unable to load Stage 3B B0 protocol contract: {resolved}"
        ) from error
    if not isinstance(raw, dict):
        raise Stage3BExecutionError("Stage 3B B0 protocol contract must be an object")
    contract = cast(dict[str, object], raw)
    validate_b0_protocol_contract(contract)
    return deepcopy(contract)


B0_PROTOCOL_CONTRACT: Final[dict[str, object]] = load_b0_protocol_contract()
B0_PROTOCOL_CONTRACT_DIGEST: Final[str] = _contract_digest(B0_PROTOCOL_CONTRACT)
B0_CANONICAL_LANES: Final[tuple[tuple[str, str], ...]] = _lane_pairs(
    B0_PROTOCOL_CONTRACT["canonical_lanes"], field="canonical_lanes"
)
B0_ENGINEERING_CONTROL_LANES: Final[tuple[tuple[str, str], ...]] = _lane_pairs(
    B0_PROTOCOL_CONTRACT["engineering_control_lanes"],
    field="engineering_control_lanes",
)
B0_SUPPORTED_PREFLIGHT_LANES: Final[tuple[tuple[str, str], ...]] = (
    B0_CANONICAL_LANES + B0_ENGINEERING_CONTROL_LANES
)
B0_CANONICAL_CELL_COUNT: Final[int] = int(
    cast(int, B0_PROTOCOL_CONTRACT["canonical_cell_count"])
)
B0_CANONICAL_PROTOCOL: Final[dict[str, int]] = {
    key: int(cast(int, value))
    for key, value in cast(
        Mapping[str, object], B0_PROTOCOL_CONTRACT["canonical_protocol"]
    ).items()
}
