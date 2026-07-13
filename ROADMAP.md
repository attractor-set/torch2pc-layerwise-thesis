# Дорожная карта

[English version](ROADMAP_EN.md)

## Фазы 1–5 — завершены

1. Исследовательский каркас и предварительная регистрация.
2. Контролируемая среда и validation-only pilot 96/96.
3. Подтверждающая кампания Stage 1 — 80/80.
4. Исследование реализации Stage 2 — 80/80.
5. Публичный выпуск и проверка неавторизованного доступа.

## Фаза 6 — Stage 3 design revision 2 завершена

Закреплены контракты локальности и профилирования, точные кандидаты,
основные приближения и predict-correct candidates.

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
- опубликован двуязычный bounded findings report;
- regression suite: 120 passed.

Publication tag: `stage3a-statistical-publication-v1`.

## Фаза 9 — profiling/locality preregistration и измерительная база — следующая

Создать отдельную ветку `stage3b-profiling-locality-preregistration` и до
запуска новой кампании заморозить:

- validation-only область и independent unit = model seed;
- B0/A0 profiling design;
- warm-up, device synchronization и repetition rules;
- wall-clock, CPU/GPU time, peak memory, VJP/backward attribution;
- locality taxonomy и B1/B2 gates;
- failure, exclusion и missing-data rules;
- разделение exploratory attribution и confirmatory claims.

Profiling/locality не изменяет завершённый Stage 3A evidence-набор и не
формулирует acceleration claims до прохождения measurement-validity gates.

## Фаза 10 — exact execution и mechanism attribution

После валидированного profiling выполнить B1/B2 numerical gates, определить
layer/module hotspots и только затем фиксировать exact execution candidates.

## Фаза 11 — core approximations и predict-correct

C1/C2 и C4/C5 проходят отдельные validation-only screening campaigns с
residual, fallback, non-inferiority, VJP-reduction и stability gates.

## Фаза 12 — расширенный Stage 3: freeze и final

Заморозить выбранные candidates и параметры, создать отдельные execution и
publication states и только после freeze разрешить final test evaluation.

## Фаза 13 — диссертация и статья

Объединить Stage 1/2, Stage 3A и последующие profiling/locality/acceleration
результаты; подготовить replication bundles и clean-room reproduction.
