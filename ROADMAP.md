# Дорожная карта

[English version](ROADMAP_EN.md)

## Фазы 1–5 — завершены

1. Исследовательский каркас и предварительная регистрация.
2. Контролируемая среда и validation-only pilot 96/96.
3. Подтверждающая кампания Stage 1 — 80/80.
4. Исследование реализации Stage 2 — 80/80.
5. Публичный выпуск и проверка неавторизованного доступа.

## Фаза 6 — Stage 3 design revision 2 завершена

Закреплены контракты локальности и профилирования, точные кандидаты, основные
приближения и predict-correct candidates.

## Фаза 7 — Stage 3A layer-wise diagnostics завершена

- same-state gradient probes: seeds 0–9;
- independently trained representation probes: seeds 0–9;
- Exact–BP controls: 10/10 passed;
- опубликованы aggregate gradient, CKA, RSA и cross-layer evidence;
- raw observations сохраняются отдельно от Git.

## Фаза 8 — Stage 3A statistical publication завершена

- seed-level statistical unit закреплена;
- выполнены 40 gradient и 20 representation comparisons;
- применена Holm-коррекция внутри зарегистрированных семейств;
- опубликованы effect sizes, confidence intervals и Exact controls;
- выполнен confirmatory depth analysis;
- опубликованы 8 PDF figures;
- добавлены metadata и SHA-256 manifests;
- опубликован двуязычный bounded findings report.

Publication tag: `stage3a-statistical-publication-v1`.

## Фаза 9 — Stage 3B preregistration и B0 measurement baseline завершены

- profiling/locality preregistration и measurement contract заморожены;
- B0 candidate: `stage2_baseline` для `FixedPred` и `Strict`;
- ROCm/float32 canonical campaign выполнена 96/96;
- каждая cell изолирована в fresh Python child process;
- 0 failed attempts и 0 systemic resource failures;
- опубликованы 96 cell, 480 region, 48 paired и 32 configuration rows;
- validation, sealing, tag и GitHub Release завершены;
- test dataset не использовался.

Publication tag: `stage3b-b0-evidence-v1`.

Evidence boundary: `full_b0_campaign_complete=true`,
`full_stage3b_campaign_complete=false`.

## Фаза 10 — B0 statistical and engineering analysis завершена

- published sealed B0 evidence использован без повторного execution;
- `model_seed` закреплён как независимая единица, 3 seeds на configuration;
- опубликованы paired timing/memory effects, region attribution, saved tensors
  и log2 scaling summaries;
- median Strict/FixedPred device-time ratio — `2.327×`;
- median peak-allocated ratio — `1.328×`;
- dominant region — `state_inference`;
- state-inference saved-tensor ratio — `11.998×`;
- опубликованы 8 derived tables, 4 PDF figures, bilingual report, metadata и
  `SHA256SUMS`;
- decision gate разрешает candidate-specific B1/B2 equivalence work и сохраняет
  full matched profiling заблокированным.

Publication tag: `stage3b-b0-analysis-evidence-v1`.

## Фаза 11 — B1/B2 candidate-specific numerical equivalence gates — следующая

- формализовать B1 и B2 candidates относительно B0;
- реализовать candidates отдельно и без изменения B0 evidence;
- пройти cosine, relative-L2, finite-value и stability gates;
- выполнить малый profiling pilot только после equivalence acceptance;
- сохранить test access выключенным;
- отдельным decision gate определить допуск full matched B1/B2 profiling.

## Фаза 12 — mechanism attribution и matched profiling

Для прошедших B1/B2 candidates определить layer/module hotspots, graph-retention
costs и только затем выполнить зарегистрированную matched profiling matrix.
Structural locality claims требуют отдельных dependency-radius,
graph-span/lifetime, feedback-operator и orchestration-barrier measurements.

## Фаза 13 — core approximations и predict-correct

C1/C2 и C4/C5 проходят отдельные validation-only screening campaigns с
residual, fallback, non-inferiority, VJP-reduction и stability gates.

## Фаза 14 — расширенный Stage 3: freeze и final

Заморозить выбранные candidates и параметры, создать отдельные execution и
publication states и только после freeze разрешить final test evaluation.

## Фаза 15 — диссертация и статья

Объединить Stage 1/2, Stage 3A и последующие profiling/locality/acceleration
результаты; подготовить replication bundles и clean-room reproduction.
