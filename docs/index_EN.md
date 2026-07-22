# Research documentation

[Русская версия](index.md)

The documentation connects the research question, protocol,
[execution](glossary_EN.md#term-execution),
[evidence](glossary_EN.md#term-evidence), and bounded findings. Plans remain
separate from observations, and published results carry claim boundaries and
[artifact provenance](glossary_EN.md#term-provenance).

## Current state

As of 21 July 2026:

- Stage 1/2, Stage 3A, Stage 3B B0, `SI-MA0`, and `SI-MA1` are complete;
- confirmatory B1 and B2 are sealed with positive `EQ-B1` and `EQ-B2`
  decisions;
- the 288-cell [matched-profiling](glossary_EN.md#term-matched-profiling)
  campaign is complete: 288/288 cells, 96/96 blocks, and 0 failures;
- evidence is preserved in the repository and bound to immutable tag
  `stage3b-matched-profiling-evidence-v1`;
- the complete ten-asset run package is uploaded to a verified draft release;
- the post-collection/pre-analysis descriptive protocol is frozen as
  `stage3b-matched-descriptive-analysis-protocol-v1`;
- a separate implementation PR is permitted, while sealed-evidence execution,
  publication, `EX-IF0`, policy activation, and test access remain closed;
- `full_stage3b_campaign_complete=false`.

The protocol freeze occurs after data collection and is therefore not presented
as a preregistration made before data collection. It closes analytical degrees
of freedom before comparative results are computed.

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
- [Matched-profiling descriptive-analysis protocol](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/main/experiments/planned/STAGE3B-MATCHED-DESCRIPTIVE-ANALYSIS_EN.md)
- [Matched descriptive-analysis execution request](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/main/experiments/planned/STAGE3B-MATCHED-DESCRIPTIVE-ANALYSIS-EXECUTION-REQUEST_EN.md)
- [Runtime](glossary_EN.md#term-runtime): [matched descriptive-analysis preflight](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/main/experiments/planned/STAGE3B-MATCHED-DESCRIPTIVE-ANALYSIS-RUNTIME-PREFLIGHT_EN.md)
- [Sealed matched-profiling evidence](https://github.com/attractor-set/torch2pc-layerwise-thesis/tree/main/results/stage-3/profiling/matched/stage3b-matched-profiling-e1dcfb2-v1)

### Architecture and research decisions

- [ADR index](decisions/index_EN.md)
