# Готовность Stage 3

[English version](stage-3-readiness_EN.md)

## Значение статуса

`ready_for_stage3_implementation` разрешает реализацию, но не pilot/final.
`blocked_until_candidates_and_freeze` означает, что Stage 3 отсутствует из
`TRAINING_STAGES`, а test выключен.

## Проверка

```bash
PYTHONPATH=src python scripts/check_stage3_readiness.py
PYTHONPATH=src python -m torch2pc_thesis.cli stage3-check
PYTHONPATH=src python scripts/generate_stage3_design_plan.py
```

Ожидается:

- design revision 2;
- 336 profiling cells;
- 48 core validation-only pilot cells;
- 27 predict-correct accelerator-screening cells;
- final `blocked_until_stage3_freeze`.

## Переход к profiling

Требуются profiler executor, non-perturbing B0 instrumentation, A0 endpoint
control, pinned source commit, environment lock и warmup/synchronization smoke.

## Переход к core pilot

B1/B2/C1/C2 получают отдельные Torch2PC commits. B1/B2 проходят
full-trajectory CPU/GPU gates, A0 — endpoint gate, C1/C2 — finite/stability
gates. Test loader отсутствует.

## Переход к accelerator screening

- core pilot завершён и его selection artifact зафиксирован;
- C4/C5 реализованы отдельными commits;
- каждый путь выполняет хотя бы одну exact correction;
- fallback на Strict покрыт тестами;
- residual/VJP/fallback telemetry включена;
- screening environment lock зафиксирован;
- test loader отсутствует.

## Переход к final

Выбран один exact и не более одного approximation candidate, параметры и margin
заморожены, создан `stage3-pilot-freeze` manifest/tag, а final включается
отдельным commit. Execution и publication states остаются различными.

## Практическая интерпретация

Успешная проверка означает, что исследователь может начинать реализацию
профилирования по закреплённому плану. Она не подтверждает эффективность
кандидатов и не создаёт экспериментальные данные. Любое расхождение в
структуре, конфигурации или защитных правилах должно быть устранено до запуска,
чтобы последующие результаты оставались воспроизводимыми и проверяемыми.
