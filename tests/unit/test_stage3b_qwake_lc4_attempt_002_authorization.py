from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from torch2pc_thesis.stage3b_qwake_lc4_attempt_002_contract import (
    ATTEMPT_002_AUTHORIZATION_RELATIVE,
    ATTEMPT_002_INVOCATION_ACKNOWLEDGEMENT,
    Attempt002ContractError,
    verify_unconsumed_attempt_002_authorization,
)
from torch2pc_thesis.stage3b_qwake_lc4_attempt_002_host_invocation_chain import (
    HOST_INVOCATION_CHAIN_AUTHORIZED_STATUS,
    build_attempt_002_host_invocation_chain_state,
    load_attempt_002_host_execution_freeze,
)

ROOT = Path(__file__).resolve().parents[2]
AUTHORIZATION = ROOT / ATTEMPT_002_AUTHORIZATION_RELATIVE


def test_authorization_record_is_canonical() -> None:
    value = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    assert AUTHORIZATION.read_text(encoding="utf-8").endswith("\n")


def test_authorization_verifies_as_unconsumed() -> None:
    freeze = load_attempt_002_host_execution_freeze(ROOT)
    authorization = verify_unconsumed_attempt_002_authorization(ROOT, freeze)
    authorization.require(freeze)
    assert authorization.authorization_effective is True
    assert authorization.authorization_consumed is False
    assert authorization.attempt_started is False


def test_authorization_is_one_shot() -> None:
    freeze = load_attempt_002_host_execution_freeze(ROOT)
    authorization = verify_unconsumed_attempt_002_authorization(ROOT, freeze)
    assert authorization.execution_count == 1
    assert authorization.retry_permitted is False


def test_authorization_is_operator_bound() -> None:
    freeze = load_attempt_002_host_execution_freeze(ROOT)
    authorization = verify_unconsumed_attempt_002_authorization(ROOT, freeze)
    assert authorization.operator_identity_kind == "local-posix-account"
    assert authorization.operator_identity == "dzmitry-prychyna"
    assert (
        authorization.action_phrase
        == ATTEMPT_002_INVOCATION_ACKNOWLEDGEMENT
    )


def test_authorization_does_not_open_scientific_execution() -> None:
    freeze = load_attempt_002_host_execution_freeze(ROOT)
    authorization = verify_unconsumed_attempt_002_authorization(ROOT, freeze)
    assert authorization.scientific_execution_open is False
    assert authorization.test_dataset_access is False
    assert authorization.publication_permitted is False


def test_host_chain_records_authorized_unconsumed_state() -> None:
    state = build_attempt_002_host_invocation_chain_state(ROOT)
    state.require()
    assert state.status == HOST_INVOCATION_CHAIN_AUTHORIZED_STATUS
    assert state.authorization_issued is True
    assert state.authorization_consumed is False
    assert state.authorization_authoring_admissible is False


def test_host_chain_keeps_runtime_effects_closed() -> None:
    state = build_attempt_002_host_invocation_chain_state(ROOT)
    assert state.host_process_spawner_present is False
    assert state.docker_run_implemented is False
    assert state.lease_v1_present is False
    assert state.lease_v2_present is False
    assert state.durable_outcome_present is False
    assert state.runtime_execution_started is False
    assert state.runtime_execution_performed is False


def test_wrong_action_phrase_is_rejected() -> None:
    freeze = load_attempt_002_host_execution_freeze(ROOT)
    authorization = verify_unconsumed_attempt_002_authorization(ROOT, freeze)
    mutated = replace(authorization, action_phrase="WRONG")
    with pytest.raises(Attempt002ContractError, match="action_phrase differs"):
        mutated.require(freeze)


def test_consumed_authorization_is_rejected() -> None:
    freeze = load_attempt_002_host_execution_freeze(ROOT)
    authorization = verify_unconsumed_attempt_002_authorization(ROOT, freeze)
    mutated = replace(authorization, authorization_consumed=True)
    with pytest.raises(
        Attempt002ContractError,
        match="authorization_consumed differs",
    ):
        mutated.require(freeze)


def test_started_attempt_is_rejected() -> None:
    freeze = load_attempt_002_host_execution_freeze(ROOT)
    authorization = verify_unconsumed_attempt_002_authorization(ROOT, freeze)
    mutated = replace(authorization, attempt_started=True)
    with pytest.raises(Attempt002ContractError, match="attempt_started differs"):
        mutated.require(freeze)


def test_retry_permission_is_rejected() -> None:
    freeze = load_attempt_002_host_execution_freeze(ROOT)
    authorization = verify_unconsumed_attempt_002_authorization(ROOT, freeze)
    mutated = replace(authorization, retry_permitted=True)
    with pytest.raises(Attempt002ContractError, match="retry_permitted differs"):
        mutated.require(freeze)


def test_authorization_digest_mutation_is_rejected() -> None:
    freeze = load_attempt_002_host_execution_freeze(ROOT)
    authorization = verify_unconsumed_attempt_002_authorization(ROOT, freeze)
    mutated = replace(
        authorization,
        authorization_sha256="sha256:" + "0" * 64,
    )
    with pytest.raises(Attempt002ContractError, match="digest differs"):
        mutated.require(freeze)
