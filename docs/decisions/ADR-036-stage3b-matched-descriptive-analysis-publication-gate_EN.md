# ADR-036: Stage 3B matched descriptive-analysis publication gate

[Русская версия](ADR-036-stage3b-matched-descriptive-analysis-publication-gate.md)

## Context

The matched-[profiling](../glossary_EN.md#term-profiling) descriptive analysis
was executed once, independently audited, and bound by an external seal. The
sealed output retains `results_publication_permitted=false` because
[execution](../glossary_EN.md#term-execution), [integrity sealing](../glossary_EN.md#term-integrity-sealing), and the
publication decision are separate lifecycle boundaries.

The draft-only workflow created a release with `--draft`, but its existing
release update path did not reassert draft state. The publication action must
therefore verify remote state independently and fail closed for a published or
immutable release.

## Decision

1. Freeze the machine-readable
   `stage3b-matched-descriptive-analysis-publication-gate-v1` gate.
2. Bind the gate to the exact output-registry and external-seal digests.
3. Preserve both B1/B2 `reject_or_revise` decisions and prohibit superiority
   claims.
4. Correct the draft release workflow so an existing release is forced back to
   draft before assets are replaced.
5. Authorize publication only through the separate immutable tag
   `stage3b-matched-descriptive-analysis-publication-v1`.
6. Require `isDraft=true` and `isImmutable=false` before publication.
7. Upload analysis, audit, and seal assets before `--draft=false`.
8. Do not mutate the 18 original files, audit package, external seal, or
   [evidence](../glossary_EN.md#term-evidence) tag.
9. Do not open `EX-IF0`, policy activation, or the test split in this ADR.

## Consequences

- Remote release state becomes an explicit fail-closed gate input.
- A retry cannot publish unless the release has been returned to draft.
- The negative engineering result can be published without becoming a
  superiority claim.
- A separate status and receipt freeze is required after successful
  publication; only then may the project proceed to `EX-IF0`.
