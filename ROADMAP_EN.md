# Roadmap

[Русская версия](ROADMAP.md)

The phase numbers below describe the repository roadmap. Experimental campaign
names—Stage 1, Stage 2, and any future Stage 3—remain separate identifiers.

## Phase 1. Research scaffold — complete

- Neutral research stance and preregistration draft.
- Test isolation and pilot-freeze gate.
- Append-only registry, persistent splits, and checksums.
- Docker/ROCm scaffold and static validation.

## Phase 2. Environment and validation pilot — complete

- Pinned Ubuntu/ROCm environment and original Torch2PC.
- Passed scoped CPU/GPU C0/C1 gates.
- Completed the 96/96 validation-only pilot without test evaluation.
- Selected and froze FixedPred and Strict configurations.

## Phase 3. Stage 1 confirmatory campaign — complete

- Completed 80/80 cells with original Torch2PC and no failed cells.
- Opened test only during final evaluation.
- Generated results, manifests, and publication tables.
- Tag: `confirmatory-final-v1`.

## Phase 4. Stage 2 implementation study — complete

- Pinned the implementation-preserving Torch2PC patch.
- Passed scoped original-vs-patched CPU/GPU gates.
- Completed the paired 80/80 matrix.
- Observed pairwise matching Stage 1/2 quality values.
- Generated cross-version runtime analysis.
- Execution tag: `stage2-execution-v1`.
- Results tag and Release: `stage2-results-v1`.

## Phase 5. Public release — complete

- Published and verified the replication bundle.
- Synchronized public-facing documentation.
- Changed repository visibility to public.
- Verified unauthenticated access to the README, tags, Release assets, Actions,
  and Security policy.

## Phase 6. Stage 3 diagnostics — optional

Stage 3 is created only as a separately specified experiment. Candidate topics
include new performance changes, layer-wise gradients, CKA/RSA across seeds,
corruption robustness, equal-wall-clock comparison, and architecture or dataset
transfer. Stage 3 is not required to close Stage 1/2 or to make the repository
public.

## Phase 7. Dissertation and article writing — ongoing

- Use registered observations only.
- Separate results, interpretation, and limitations.
- Cite execution and publication states explicitly.
- Select a later archival/DOI release according to venue requirements.
