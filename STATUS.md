# Статус исследования

[English version](STATUS_EN.md)

Stage 1/2 завершены и являются неизменяемой опубликованной базовой линией.
Активный этап — реализация Stage 3 design revision 2 по локальности, точному
исполнению и predict-correct аппроксимациям.

| Компонент | Наблюдаемый статус |
|---|---|
| Validation-only pilot | 96/96, test не вычислялся |
| Stage 1 / Stage 2 | 80/80 и 80/80 |
| Original / patched Torch2PC | `00c6c50ee3540537bbb56ab2b6567b541f42b093` / `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4` |
| Stage 2 execution / publication | `6d66b0a6f82c30c4fb8eca6247383ca13e0636a2` / `bb435432a65b76b7fc4f383b566b9a372fc346ae` |
| Stage 2 runtime | `BP ≈ Exact < FixedPred << Strict` |
| Stage 3 design | `ready_for_stage3_implementation`, revision 2 |
| Stage 3 matrices | 336 profiling, 48 core pilot, 27 accelerator screening |
| Test access | выключен до отдельного freeze |
| Stage 3 execution | заблокирован до candidate commits, gates и environment locks |

## Добавленная predict-correct линия

- A0: FixedPred `eta=1`, steps=`depth`, endpoint-equivalence control;
- C4: layer-local EMA initializer + `1/2/3/5` exact correction sweeps;
- C5: layer-scalar secant preconditioner + `1/2/3/5` exact corrections;
- C3H/C6: deferred hybrid feedback/Anderson candidates.

## Следующий шаг

Реализовать non-perturbing B0/A0 profiling executor. Затем B1/B2 и exact gates,
после чего C1/C2 core pilot. C4/C5 реализуются отдельным этапом и проходят
27-cell validation-only screening с fallback/residual guards. Stage 1/2 не
повторяются.

## Интерпретация текущего состояния

Подготовлен именно исследовательский каркас: он задаёт порядок разработки,
контрольные границы и правила отбора вариантов. Экспериментальное исполнение ещё
не началось. До запуска необходимо подтвердить численную корректность точных
вариантов, устойчивость приближённых вариантов и полную изоляцию тестовой
выборки. Такой порядок сохраняет причинную интерпретируемость результатов и не
смешивает уже опубликованные серии с новой кампанией.
