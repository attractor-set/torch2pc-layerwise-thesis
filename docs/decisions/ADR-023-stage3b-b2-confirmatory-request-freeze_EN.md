# ADR-023: freezing the confirmatory `EQ-B2` request

[Русская версия](ADR-023-stage3b-b2-confirmatory-request-freeze.md)

- Status: accepted — request frozen, [execution](../glossary_EN.md#term-execution) closed
- Date: 2026-07-20

## Context

[ADR-021](ADR-021-stage3b-b2-confirmatory-preregistration_EN.md)
preregistered confirmatory `EQ-B2` as 120 matched triples and 240 direct
comparisons. [ADR-022](ADR-022-stage3b-b2-confirmatory-opening_EN.md) added
fail-closed planning, authorization, recovery, and sealing infrastructure but
intentionally created no immutable request.

A separate prospective request freeze is required before image construction and
[runtime](../glossary_EN.md#term-runtime) validation. It binds the campaign to
registered B1 inputs and B2 contracts without permitting measurements.

## Decision

Freeze the append-only package:

```text
experiments/frozen/stage3b-b2-confirmatory/request.json
experiments/frozen/stage3b-b2-confirmatory/SHA256SUMS
```

Canonical identifiers:

```text
request_id=stage3b-b2-confirmatory-120-v1
request_sha256=02c88c0778398cecedb069948e9f952c8d7be46d3d064197ae0e7f5b86314ed3
request_digest=3a824f4a7a8517a4b97341a4598ac8433e2253b45d2bb3f667722c270b06fb78
matched_triple_count=120
pairwise_comparison_count=240
run_seed_base=732000
```

The request reuses byte-for-byte:

- the three confirmatory B1 checkpoints;
- the ten B1 validation batches;
- the sealed `EQ-B1-CONFIRMATORY` decision;
- the derived B1 admission;
- the B2 preregistration and implementation contracts.

No new data selection occurs. Test-split access remains closed.

## Execution boundary

After merge, only the following is true:

```text
b2_confirmatory_request_frozen=true
runtime_authorization=not_issued
execution_started=false
results_present=false
measurements_allowed=false
```

The frozen request is not [evidence](../glossary_EN.md#term-evidence), does not
permit results publication, and creates no authorization token.

The next separate stage must:

1. build an immutable ROCm image from the clean publication commit;
2. verify the OCI revision and both lanes;
3. issue a separate fail-closed runtime authorization;
4. perform only a non-measuring dry-run before any separate smoke or
   confirmatory-execution decision.

## Preserved boundaries

This ADR does not modify:

- the historical B2 engineering smoke;
- confirmatory B1 artifacts;
- the historical [matched-profiling](../glossary_EN.md#term-matched-profiling)
  request or manifest;
- `experiments/planned/STAGE3B-B2-CONFIRMATORY-CONTRACT.json`;
- the test split;
- any file under `results/**`.

Any future request change requires a new versioned request ID and a separate
supersession record; the existing `request.json` is never rewritten.
