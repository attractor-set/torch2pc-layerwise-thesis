# Research status

[Русская версия](STATUS.md)

This status follows the complete validation-only pilot. Passing implementation
controls is not treated as a universal equivalence proof, and pilot validation
metrics are not confirmatory test results.

| Component | Observed status |
|---|---|
| Repository structure | Created and statically checked |
| Test isolation | Implemented; pilot records `test_evaluated=false` |
| Split persistence and SHA-256 | Implemented and observed for pilot splits |
| Torch2PC commit | Pinned to `00c6c50ee3540537bbb56ab2b6567b541f42b093` |
| Docker/ROCm runtime | Exercised on the target Ubuntu host and RX 7700 XT |
| Correction source-pattern check | Observed for the pinned `TorchSeq2PC.py` |
| C0 Exact/BP | Passed on CPU float64 and GPU float32 |
| C1 FixedPred/Exact | Passed on CPU float64 and GPU float32 |
| Validation-only pilot | 96/96 terminal cells, 0 failed, no test evaluation |
| Pilot selection | FixedPred `eta=0.1`, `n=10`; Strict `eta=0.05`, `n=20` |
| Compact pilot observations | Generate `pilot_observations.csv` before replacing the pilot lock |
| Pilot freeze | Not created yet |
| Final | Blocked until the new environment lock, C0/C1, and pilot freeze |
| CKA/RSA/robustness executor | Planned and partially implemented |
| Confirmatory dissertation results | Absent until final |
