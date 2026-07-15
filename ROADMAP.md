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

## Фаза 10 — B0 statistical and engineering analysis — следующая

В отдельной ветке `stage3b-b0-analysis-v1` выполнить:

- paired seed-level analysis `Strict` относительно `FixedPred`;
- decomposition времени по profiling regions;
- peak-memory и saved-tensor attribution;
- scaling по depth, width и batch size;
- bounded descriptive uncertainty при трёх model seeds на configuration;
- двуязычный report и decision gate для дальнейших candidates.

## Фаза 11 — exact execution и mechanism attribution

После B0 analysis пройти B1/B2 numerical gates, определить layer/module
hotspots и только затем фиксировать exact execution candidates.

## Фаза 12 — core approximations и predict-correct

C1/C2 и C4/C5 проходят отдельные validation-only screening campaigns с
residual, fallback, non-inferiority, VJP-reduction и stability gates.

## Фаза 13 — расширенный Stage 3: freeze и final

Заморозить выбранные candidates и параметры, создать отдельные execution и
publication states и только после freeze разрешить final test evaluation.

## Фаза 14 — диссертация и статья

Объединить Stage 1/2, Stage 3A и последующие profiling/locality/acceleration
результаты; подготовить replication bundles и clean-room reproduction.
