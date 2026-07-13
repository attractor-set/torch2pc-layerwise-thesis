# ADR-008: predict-correct acceleration как отдельный трек Stage 3

[English version](ADR-008-predict-correct-acceleration_EN.md)

- Статус: принято для design revision 2;
- дата: 2026-07-13;
- область: Stage 3;
- затрагивает Stage 1/2: нет.

## Контекст

Stage 2 показал порядок runtime `BP ≈ Exact < FixedPred << Strict`. Следующий
шаг может использовать не только реорганизацию точных VJP, но и схему,
аналогичную быстрым численным методам: дешёвая локальная оценка переводит
состояние ближе к решению, после чего один или несколько точных predictive-coding
sweeps выполняют коррекцию.

Torch2PC уже вычисляет VJP без явного построения полного Jacobian. Поэтому
битовые аппроксимации или построение low-rank Jacobian не считаются основным
кандидатом: они не устраняют главный источник стоимости — повторные VJP и
итерационные sweeps.

## Решение

Stage 3 получает отдельную predict-correct линию:

1. `fixedpred_finite_step_control` — точный endpoint-контроль с `eta=1` и числом
   шагов, равным глубине;
2. `predict_correct_initialization` — дешёвый layer-local initializer и
   `1/2/3/5` точных correction sweeps;
3. `local_secant_preconditioner` — локальная скалярная secant-оценка обратного
   масштаба и `1/2/3/5` точных correction sweeps;
4. `hybrid_feedback_exact_refresh` — отложенный вариант дешёвого feedback с
   периодической точной VJP-коррекцией;
5. `layer_local_anderson` — отложенный fixed-point accelerator.

Основная accelerator screening использует только первые два приближённых
кандидата и Strict. Hybrid feedback и Anderson остаются deferred до завершения
core Stage 3.

## Методологическая граница

`fixedpred_finite_step_control` может получить только endpoint-equivalence claim:
сравниваются parameter gradients и один optimizer step. Совпадение промежуточной
траектории beliefs не требуется.

Predict-correct, secant, feedback и Anderson являются algorithm-changing
кандидатами. Они проходят non-inferiority, gradient-alignment, residual,
performance и fallback gates, но не получают claim эквивалентности Stage 2.

## Безопасность исполнения

Для каждого predict-correct кандидата обязательны:

- хотя бы один точный correction sweep;
- fallback на Strict при `NaN/Inf` или росте residual;
- журналирование числа VJP, correction sweeps и fallback events;
- test access, выключенный до Stage 3 freeze;
- отдельный Torch2PC candidate commit и environment lock.

## Consequences

Положительный результат позволит оценить, какую долю стоимости Strict можно
заменить дешёвой локальной оценкой без практически значимой потери качества.
Отрицательный результат также информативен: он покажет, что точные локальные
коррекции или свежая линеаризация являются существенной частью исследованного
режима.
