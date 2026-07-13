# Дорожная карта

[English version](ROADMAP_EN.md)

## Фазы 1–5 — завершены

1. Исследовательский scaffold и preregistration.
2. Контролируемая среда и validation-only pilot 96/96.
3. Stage 1 confirmatory campaign 80/80.
4. Stage 2 implementation study 80/80.
5. Public release и проверка неавторизованного доступа.

## Фаза 6. Stage 3 design-ready — текущая

Завершено:

- scope и locality taxonomy закреплены ADR-006/ADR-007;
- RQ6–RQ10 добавлены;
- baseline hashes Stage 2 закреплены;
- design YAML, stage templates и candidate overlays добавлены;
- locality trace schema и scaling MLP family реализованы;
- deterministic design plan и readiness gate добавлены;
- test остаётся выключенным.

## Фаза 7. Stage 3A baseline profiling

- реализовать diagnostics/profiler executor;
- разметить forward, inference, state VJP, parameter VJP и optimizer step;
- собрать B0 locality/runtime/memory profile;
- проверить отсутствие perturbation training results;
- применить feasibility stop rules.

## Фаза 8. Stage 3B exact candidates

- B1 isolated layer VJP;
- B2 composite VJP;
- CPU float64 и GPU float32 equivalence gates;
- back-to-back profiling и attribution;
- выбрать не более одного exact candidate для pilot.

## Фаза 9. Stage 3C approximations

- C1 adaptive stopping;
- C2 periodic VJP refresh;
- gradient-alignment и stability gates;
- parameterized validation-only screening 48 cells;
- выбрать не более одного approximation candidate.

C3 fixed random feedback остаётся условным треком после core Stage 3.

## Фаза 10. Stage 3 freeze и final

- заморозить candidates, parameters и non-inferiority margin;
- создать Stage 3 environment lock и control artifacts;
- создать `stage3-pilot-freeze-v1`;
- отдельным commit включить test;
- выполнить до 80 final cells;
- сохранить execution и publication states раздельно.

## Фаза 11. Анализ и диссертация

- locality/runtime/memory scaling;
- robustness и representations для frozen candidates;
- экспериментальная глава и статья;
- replication bundle и clean-room reproduction;
- финальный резерв на рецензию и исправления.


## Принцип управления объёмом

Каждая следующая фаза начинается после завершения предыдущего контрольного
рубежа. Сначала собираются наблюдения о текущей реализации, затем создаётся один
кандидат, после чего проверяются корректность, устойчивость и практическая
значимость ускорения. Такой порядок сохраняет возможность установить причину
каждого изменения и уменьшает риск одновременного изменения нескольких факторов.
