# ADR-049: `QW-4B-E-v2` post-merge transition and `QW-LC0` opening

[Russian version](ADR-049-stage3b-qwake-lc0-post-merge-transition.md)

- Status: accepted
- Date: 25 July 2026

## Context

The `QW-4B-E-v2` repository seal was recorded by commit
`26bc0ef635e13dba719d3356fe17382f0037d1df` and merged into `main` by merge commit
`4f23b752a40ae05de9fc7ee49c9962c44083b71d`. The exact [runtime](../glossary_EN.md#term-runtime) output, audit package, and external
seal were reverified on `main`; the report remains
`sha256:54dba01d47814dc00fa53bd69c00865bd1c47754c017c7482c895162d3a86b82`.

The sealed result is engineering [evidence](../glossary_EN.md#term-evidence) only. The authorization is consumed,
retry is prohibited, and scientific [execution](../glossary_EN.md#term-execution), the test split, and publication
remain closed.

## Decision

1. Admit the `QW-4B-E-v2` repository evidence as sealed on `main`.
2. Open `QW-LC0` only to freeze `R/M/Γ/C` semantics, the `LOCAL_COMPUTE`
   scope, [candidate](../glossary_EN.md#term-candidate) boundaries, and claim strength.
3. Do not open implementation or execution of `LOCAL_SWEEP` or
   `ANALYTIC_COMPLETION`.
4. Do not modify `QW-4B-E-v2`, retired authorizations, output, audit package,
   or seal.
5. Keep `QW-LC1`, the scientific image, C1/C2/C3/R, the test split, and
   publication closed pending separate decisions.

## Verifiable boundary

```text
qwake_qw4b_e_v2_repository_evidence_sealed=true
qwake_qw4b_e_v2_repository_seal_commit=26bc0ef635e13dba719d3356fe17382f0037d1df
qwake_qw4b_e_v2_repository_merge_commit=4f23b752a40ae05de9fc7ee49c9962c44083b71d
qwake_qw4b_e_v2_post_merge_verification_passed=true
qwake_qw_lc0_transition_permitted=true
qwake_qw_lc0_open=true
qwake_qw_lc0_semantics_scope_frozen=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
qwake_scientific_image_freeze_permitted=false
test_dataset_access=false
publication_permitted=false
qwake_next_slice=QW-LC0
qwake_post_lc0_next_slice=QW-LC1
```

## Consequences

The next independent slice is only the `QW-LC0` semantics-and-scope freeze. It
does not execute the model or create scientific evidence.
