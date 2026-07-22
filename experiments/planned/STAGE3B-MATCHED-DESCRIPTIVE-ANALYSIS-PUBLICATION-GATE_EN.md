# Stage 3B matched-profiling descriptive-analysis publication gate

[Русская версия](STAGE3B-MATCHED-DESCRIPTIVE-ANALYSIS-PUBLICATION-GATE.md)

Status: **gate frozen; remote publication action pending**.

## 1. Purpose

This gate authorizes bounded publication of the already sealed 18-file
descriptive-analysis output. It does not rerun the analysis, mutate sealed
files, or redefine candidate decisions.

Bound identities:

- output registry: `8baa1b55c21ed2b00bd849bbbe4f415d8b5f86d70bd9989d4ec4917765ead1da`;
- external seal: `dbb8983bd77490ca4feedc035ae31ca4cdd0764ecd89dab1b0c3d91aed0ad3cd`;
- evidence release: `stage3b-matched-profiling-evidence-v1`;
- publication action tag: `stage3b-matched-descriptive-analysis-publication-v1`.

## 2. Preconditions

The publication action fails closed if any condition is violated:

1. the output, audit, seal, or gate registry fails SHA-256 validation;
2. the 18-file output inventory differs;
3. candidate decisions differ from the frozen `reject_or_revise` records;
4. the remote evidence release is not a draft;
5. the release is already immutable;
6. the execution tag differs from the publication action tag.

If the release was published before the gate, it must first be returned to a
draft. This corrects external GitHub state without changing the Git tag,
assets, or sealed research files.

## 3. Publication assets

Before the release leaves draft state, the workflow uploads:

- a reproducible archive of the 18-file output;
- an audit and external-seal archive;
- a publication manifest;
- a separate SHA-256 registry.

The original reports preserve the state wording that existed when they were
generated. The later publication state is defined by the external audit, seal,
gate, and release record without mutating those reports.

## 4. Claim boundary after successful action

Permitted:

```text
results_publication_permitted=true
release_publication_permitted=true
```

Still prohibited:

```text
superiority_claim_permitted=false
ex_if0_opened=false
policy_activation_permitted=false
test_dataset_access=false
full_stage3b_campaign_complete=false
```

Frozen decisions:

- `isolated_layer_vjp`: `reject_or_revise`;
- `composite_vjp`: `reject_or_revise`;
- qualified configurations: `0/16` for every candidate × method pair.

## 5. Next transition

Only after the publication action succeeds and its result is separately
recorded does `EX-IF0` become the next formal transition. This gate does not
open `EX-IF0` by itself.
