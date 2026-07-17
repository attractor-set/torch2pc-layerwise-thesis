# Stage 3B B2: `composite_vjp` candidate contract

[English version](STAGE3B-B2_EN.md)

## Статус и prerequisite

B2 предварительно регистрируется только как `composite_vjp`. Реализация B2
остаётся закрытой до sealed `EQ-B1`. Автоматический переход к
`block_composite_vjp` или `chunked_composite_vjp` запрещён и требует нового
протокола.

## Структурный контракт

B2 выполняет ровно один composite state-VJP на inference sweep и охватывает все
зарегистрированные логические связи верхнего состояния. Per-layer state-VJP
внутри кандидата запрещён. Порядок обновлений, версии состояний и
parameter-VJP path должны совпадать с `stage2_baseline`.

## Траектория и прямой контроль B1/B2

Каждая matched triple `stage2_baseline`/B1/B2 восстанавливается из одного
snapshot. Smoke содержит 12 triples и 24 pairwise comparisons; confirmatory
эквивалентность — 120 triples и 240 comparisons. `EQ-B2` требует одновременно
согласия B2 с baseline и прямого согласия B2 с допущенным B1. Любое B1/B2
расхождение блокирует B2 независимо от потенциального ускорения.

## Профилирование и стоимость

После `EQ-B1` и `EQ-B2` B2 входит в ту же 96-cell ROCm/float32 matrix. Primary
timing использует `no_hooks`, structural lane — `counters_only`; observer cost
публикуется отдельно. Выбор точной реализации откладывается до отдельного
`EX-IF0` и использует сначала safety/numerical admissibility, затем Pareto rule.

## Граница с будущей политикой

B2 не содержит estimator, oracle branching, дешёвого диагностического цикла,
hysteresis или offline policy selection. Положительный `EQ-B2` только разрешает
учитывать B2 в отдельном `EX-IF0`; он не разрешает adaptive stopping, wake-up
или распределение бюджета проходов.

После `EX-IF0` политика исследуется через `A11-OFF0`, `A11-OFF1`, отдельную
preregistration predictor и shadow `QWake-PC`. Контрфактические метки
`stop`/`native_one`/`exact_one` остаются метками offline ветвей, а не действиями
B2.

## Граница утверждения

Положительный `EQ-B2` не устанавливает преимущество над B1, выигрыш времени или
памяти, переносимость на другие архитектуры, пригодность управляющего контура,
безопасность hysteresis или пропуска полных проходов.
