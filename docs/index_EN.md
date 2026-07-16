# Research documentation

[Русская версия](index.md)

The documentation connects the research question, protocol,
[execution](glossary_EN.md#term-execution),
[evidence](glossary_EN.md#term-evidence), and bounded findings. Plans remain
separate from observations, and published results carry claim boundaries and
[artifact provenance](glossary_EN.md#term-provenance).

## Current state

As of 16 July 2026:

- Stage 1/2, Stage 3A, and Stage 3B B0 are complete and published;
- `SI-MA0` is complete with its negative `COST-MA0` result retained;
- `SI-MA1` is complete across ten `model_seed` units and passed
  `CAL-COST-MA1`;
- the final tag is `stage3b-si-ma1-confirmatory-v1`;
- the [`PC-TREF`/`PC-CATM` theoretical foundation](pc-tref-pc-catm-theoretical-foundation_EN.md)
  freezes the operational semantics required before B1/B2;
- B1/B2 preregistration is permitted after publication of this package;
- implementation, confirmatory execution, `EX-IF0`, [passive diagnostics](glossary_EN.md#term-passive-diagnostics), the
  predictor, `QWake-PC`, and final test remain future work;
- `full_stage3b_campaign_complete=false`, and the test split remains closed.

`SI-MA1` does not rewrite `SI-MA0`: observer calibration removed a positive
uncovered residual under the registered one-sided rule, but did not measure the
future `ECZ` evaluator or [control-plane cost](glossary_EN.md#term-control-plane-cost).

## Reading order

1. [Current status](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/main/STATUS_EN.md)
   contains verified state and bounded findings.
2. [Roadmap](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/main/ROADMAP_EN.md)
   defines the permitted sequence of future work.
3. The [glossary](glossary_EN.md) fixes normative meanings and Russian–English
   mappings.
4. Protocols and preregistrations define rules before execution.
5. Result directories and reports record observations after execution.
6. The [language policy](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/main/LANGUAGE_POLICY_EN.md)
   requires synchronized Russian and English versions.

## Core documents

### Cross-cutting rules

- [Research glossary](glossary_EN.md)
- [Language and terminology policy](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/main/LANGUAGE_POLICY_EN.md)
- [Research principles](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/main/RESEARCH_PRINCIPLES_EN.md)

### Research design

- [Research question](research-question_EN.md)
- [Methodology](methodology_EN.md)
- [Analysis plan](analysis-plan_EN.md)
- [Experiment protocol](experiment-protocol_EN.md)
- [Reproducibility](reproducibility_EN.md)
- [Data management](data-management_EN.md)
- [Hardware](hardware_EN.md)

### `PC-TREF`, `PC-CATM`, and Scenario A

- [Theoretical foundation after `SI-MA1`](pc-tref-pc-catm-theoretical-foundation_EN.md)
- [PC-TREF Balanced Core](pc-tref-balanced-core_EN.md)
- [PC-CATM of correction zero and error transport](pc-catm-operator-model_EN.md)
- [Primary working Scenario A](glossary_EN.md#term-primary-working-scenario) ([document](stage3b-primary-scenario-a_EN.md))
- [Realistic master's thesis plan](masters-thesis-plan_EN.md)
- [ADR-013: operational semantics and B1/B2 admission](decisions/ADR-013-pc-tref-operational-semantics_EN.md)

### Stages and results

- [Stage 2 protocol](stage-2-protocol_EN.md)
- [Stage 3 protocol](stage-3-protocol_EN.md)
- [Stage 3 readiness](stage-3-readiness_EN.md)
- [Stage 3A statistical results](stage3a-statistical-results_EN.md)
- [Stage 3B B0 validation and integrity sealing](glossary_EN.md#term-integrity-sealing) ([document](stage3b-b0-sealing_EN.md))
- [Stage 3B B0 analysis pipeline](stage3b-b0-analysis-pipeline_EN.md)
- [B0 sealed evidence](https://github.com/attractor-set/torch2pc-layerwise-thesis/tree/main/results/stage-3/profiling/b0/sealed-v1)
- [B0 engineering analysis](https://github.com/attractor-set/torch2pc-layerwise-thesis/tree/main/results/stage-3/profiling/b0/analysis-v1)
- [`SI-MA1` confirmatory evidence](https://github.com/attractor-set/torch2pc-layerwise-thesis/tree/main/results/stage-3/si-ma1/confirmatory)
- [`SI-MA1` final report](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/main/results/stage-3/si-ma1/confirmatory/si_ma1_report_EN.md)
- [`SI-MA1` final tag](https://github.com/attractor-set/torch2pc-layerwise-thesis/tree/stage3b-si-ma1-confirmatory-v1)

### Architecture and research decisions

- [ADR index](decisions/index_EN.md)
