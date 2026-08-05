from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from torch2pc_thesis.stage3b_qwake_lc4_attempt_002_authorization_consumption_operation import (
    EXPECTED_AUTHORIZATION_SHA256,
    EXPECTED_TORCH2PC_COMMIT,
    Attempt002AuthorizationConsumptionClaim,
    Attempt002AuthorizationConsumptionOperationAdmission,
    Attempt002AuthorizationConsumptionOperationError,
    Attempt002DelegatedTransitionResult,
    build_attempt_002_authorization_consumption_claim,
    build_attempt_002_authorization_consumption_operation_admission,
    canonical_json,
    execute_attempt_002_authorization_consumption_operation_once,
)

IMPLEMENTATION_COMMIT = "a" * 40
CLAIMED_AT_UTC = "2026-08-05T00:25:00Z"


def _repository(tmp_path: Path) -> Path:
    (tmp_path / ".git").mkdir()
    return tmp_path


def _admission() -> Attempt002AuthorizationConsumptionOperationAdmission:
    return build_attempt_002_authorization_consumption_operation_admission(
        operation_post_commit_verified=True,
        operation_implementation_commit=IMPLEMENTATION_COMMIT,
        repository_head=IMPLEMENTATION_COMMIT,
        worktree_and_index_clean=True,
        torch2pc_head=EXPECTED_TORCH2PC_COMMIT,
        authorization_sha256=EXPECTED_AUTHORIZATION_SHA256,
        authorization_effective=True,
        authorization_consumed=False,
        attempt_started=False,
        output_root_present=False,
        lease_v1_present=False,
        lease_v2_present=False,
        durable_outcome_present=False,
    )


def test_canonical_json_is_deterministic() -> None:
    assert canonical_json({"b": 2, "a": 1}) == '{"a":1,"b":2}\n'


def test_claim_is_canonical_and_self_validating() -> None:
    claim = build_attempt_002_authorization_consumption_claim(
        operation_implementation_commit=IMPLEMENTATION_COMMIT,
        claimed_at_utc=CLAIMED_AT_UTC,
    )
    claim.require()
    assert claim.operation_implementation_commit == IMPLEMENTATION_COMMIT
    assert claim.claim_sha256.startswith("sha256:")


def test_admission_fails_closed_before_delegation(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    calls: list[str] = []

    def delegated_transition(
        project_root: Path,
        *,
        claim: Attempt002AuthorizationConsumptionClaim,
    ) -> Attempt002DelegatedTransitionResult:
        calls.append(project_root.as_posix())
        raise AssertionError(claim)

    invalid = replace(_admission(), operation_post_commit_verified=False)
    with pytest.raises(
        Attempt002AuthorizationConsumptionOperationError,
        match="admission differs",
    ):
        execute_attempt_002_authorization_consumption_operation_once(
            root,
            admission=invalid,
            claimed_at_utc=CLAIMED_AT_UTC,
            delegated_transition=delegated_transition,
        )
    assert calls == []


def test_operation_delegates_exactly_once_in_temporary_repository(
    tmp_path: Path,
) -> None:
    root = _repository(tmp_path)
    calls: list[str] = []

    def delegated_transition(
        project_root: Path,
        *,
        claim: Attempt002AuthorizationConsumptionClaim,
    ) -> Attempt002DelegatedTransitionResult:
        assert isinstance(claim, Attempt002AuthorizationConsumptionClaim)
        calls.append(project_root.as_posix())
        return Attempt002DelegatedTransitionResult(
            claim_sha256=claim.claim_sha256,
            authorization_consumed=True,
            attempt_started=True,
            lease_v1_present=True,
            process_spawned=True,
            runtime_started=True,
            automatic_retry_permitted=False,
        )

    result = execute_attempt_002_authorization_consumption_operation_once(
        root,
        admission=_admission(),
        claimed_at_utc=CLAIMED_AT_UTC,
        delegated_transition=delegated_transition,
    )
    result.require()
    assert result.delegated_transition_call_count == 1
    assert calls == [root.as_posix()]


def test_preexisting_effect_path_blocks_delegation(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    forbidden = root / (
        "results/stage-3/"
        "qwake-lc4-runtime-validation-v1-attempt-002.execution-lease.json"
    )
    forbidden.parent.mkdir(parents=True)
    forbidden.write_text("{}\n", encoding="utf-8")
    calls: list[str] = []

    def delegated_transition(
        project_root: Path,
        *,
        claim: Attempt002AuthorizationConsumptionClaim,
    ) -> Attempt002DelegatedTransitionResult:
        calls.append(project_root.as_posix())
        raise AssertionError(claim)

    with pytest.raises(
        Attempt002AuthorizationConsumptionOperationError,
        match="preexisting attempt-002 effect path",
    ):
        execute_attempt_002_authorization_consumption_operation_once(
            root,
            admission=_admission(),
            claimed_at_utc=CLAIMED_AT_UTC,
            delegated_transition=delegated_transition,
        )
    assert calls == []


def test_delegated_result_must_match_claim(tmp_path: Path) -> None:
    root = _repository(tmp_path)

    def delegated_transition(
        project_root: Path,
        *,
        claim: Attempt002AuthorizationConsumptionClaim,
    ) -> Attempt002DelegatedTransitionResult:
        assert project_root == root
        assert claim is not None
        return Attempt002DelegatedTransitionResult(
            claim_sha256="sha256:" + "0" * 64,
            authorization_consumed=True,
            attempt_started=True,
            lease_v1_present=True,
            process_spawned=True,
            runtime_started=True,
            automatic_retry_permitted=False,
        )

    with pytest.raises(
        Attempt002AuthorizationConsumptionOperationError,
        match="delegated transition result differs",
    ):
        execute_attempt_002_authorization_consumption_operation_once(
            root,
            admission=_admission(),
            claimed_at_utc=CLAIMED_AT_UTC,
            delegated_transition=delegated_transition,
        )


def test_delegate_failure_is_not_retried(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    calls = 0

    def delegated_transition(
        project_root: Path,
        *,
        claim: Attempt002AuthorizationConsumptionClaim,
    ) -> Attempt002DelegatedTransitionResult:
        nonlocal calls
        assert project_root == root
        assert claim is not None
        calls += 1
        raise RuntimeError("synthetic delegated failure")

    with pytest.raises(RuntimeError, match="synthetic delegated failure"):
        execute_attempt_002_authorization_consumption_operation_once(
            root,
            admission=_admission(),
            claimed_at_utc=CLAIMED_AT_UTC,
            delegated_transition=delegated_transition,
        )
    assert calls == 1
