# Дорожная карта

[English version](ROADMAP_EN.md)

## Фазы 1–5 — завершены

1. Research scaffold и preregistration.
2. Controlled environment и validation-only pilot 96/96.
3. Stage 1 confirmatory campaign 80/80.
4. Stage 2 implementation study 80/80.
5. Public release и проверка неавторизованного доступа.

## Фаза 6. Stage 3 design-ready revision 2 — текущая

Закреплены ADR-006/007/008, RQ6–RQ11, точные hashes Stage 2, locality schema,
profiling contract, scaling MLP family, exact-shortcut control A0, core
approximation candidates C1/C2 и predict-correct candidates C4/C5. Test остаётся
выключенным.

## Фаза 7. Stage 3A profiling

- реализовать non-perturbing profiler executor;
- собрать B0/A0 locality/runtime/memory profile;
- выполнить 336 matched profiling cells;
- применить feasibility и endpoint-equivalence gates.

## Фаза 8. Stage 3B exact candidates

- B1 isolated layer VJP;
- B2 composite VJP;
- CPU float64/GPU float32 full-trajectory gates;
- attribution и выбор не более одного exact candidate.

## Фаза 9. Stage 3C core approximations

- C1 adaptive stopping;
- C2 periodic VJP refresh;
- 48-cell validation-only pilot;
- выбрать не более одного core approximation candidate.

## Фаза 10. Stage 3C2 predict-correct screening

- C4 layer-local EMA initializer + exact correction;
- C5 local secant preconditioner + exact correction;
- 27 validation-only cells;
- residual, VJP-reduction, fallback и non-inferiority gates;
- C3H/C6 остаются deferred до отдельного go/no-go.

## Фаза 11. Stage 3 freeze и final

Заморозить candidates/parameters/margin, создать environment/control artifacts и
`stage3-pilot-freeze-v1`, отдельным commit включить test, выполнить до 80 final
cells и сохранить execution/publication states раздельно.

## Фаза 12. Анализ и диссертация

Locality/runtime/memory scaling, robustness, representations, глава диссертации,
статья, replication bundle, clean-room reproduction и резерв на рецензию.

## Принцип управления объёмом

Каждая линия начинается после предыдущего контрольного рубежа. C4/C5 не
объединяются с C1/C2 или B1/B2 до завершения attribution. Отрицательные и
fallback-heavy результаты сохраняются как результаты, а не удаляются.

## Критерий завершения проектирования

Проектирование считается завершённым, когда все варианты имеют однозначные
идентификаторы, область сравнения, правила остановки и заранее заданные условия
перехода. Наличие кода само по себе не разрешает эксперимент: сначала
фиксируются среда, контрольные результаты и план исполнения. Это позволяет
отделить исследовательское решение от последующего наблюдения.
