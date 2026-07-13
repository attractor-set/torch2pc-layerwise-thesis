# Research status

[Русская версия](STATUS.md)

Status after the validation pilot and two completed 80-cell confirmatory
campaigns. Stage 1 uses the original Torch2PC implementation; Stage 2 uses the
pinned implementation-preserving patch. Numerical controls remain scoped to the
pinned experimental domain and are not treated as a universal proof for
arbitrary models or environments.

| Component | Observed status |
|---|---|
| Validation-only pilot | 96/96 terminal cells, 0 failed, no test evaluation |
| Stage 1 final | 80/80 completed, 0 failed |
| Stage 2 final | 80/80 completed, 0 failed |
| Model and data | `lenet_classic`, MNIST, and FashionMNIST |
| Original Torch2PC | `00c6c50ee3540537bbb56ab2b6567b541f42b093` |
| Patched Torch2PC | `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4` |
| Stage 1 source lock | `140e77cc2083bf04234dcea16b95803e63cb0537` |
| Stage 2 execution source | `6d66b0a6f82c30c4fb8eca6247383ca13e0636a2` |
| Stage 2 results state | `bb435432a65b76b7fc4f383b566b9a372fc346ae` |
| CPU/GPU equivalence gates | Passed |
| Regression suite | 63 passed |
| Stage 1 / Stage 2 quality | Paired test accuracy and macro-F1 values matched |
| Stage 2 performance | `BP ≈ Exact < FixedPred << Strict` |
| Cross-version analysis | `results/cross-version/` |
| Torch2PC equivalence audit | `docs/torch2pc-patched-v1-equivalence.md` |

## Publication state

- Stage 1 tag: `confirmatory-final-v1`;
- Stage 2 execution tag: `stage2-execution-v1`;
- Stage 2 results tag: `stage2-results-v1`;
- the `stage2-results-v1` GitHub Release is published;
- the replication bundle contains the raw Stage 2 artifacts;
- the archive SHA-256 and file manifest are published with the bundle;
- 660 manifest artifacts were verified.

The execution commit and publication state are distinct provenance points:
`6d66b0a6...` identifies the code used for Stage 2 execution, while
`bb435432...` identifies the later state containing the assembled and published
results.

## Next step

Public visibility was completed on 13 July 2026. Unauthenticated access to the
README, tags, Release assets, Actions, and Security policy was verified.

Stage 1 and Stage 2 are closed. Stage 3 remains an optional, separate campaign
for new performance changes or extended diagnostics.
