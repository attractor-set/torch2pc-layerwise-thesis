# Готовность Stage 3

[English version](stage-3-readiness_EN.md)

## Значение статуса

`ready_for_stage3_implementation` означает, что исследовательский дизайн можно
реализовывать без изменения Stage 1/2. Этот статус не разрешает pilot или final.

`blocked_until_candidates_and_freeze` означает, что CLI Stage 3 обучения
намеренно отсутствует из `TRAINING_STAGES`.

## Проверка

```bash
PYTHONPATH=src python scripts/check_stage3_readiness.py
PYTHONPATH=src python -m torch2pc_thesis.cli stage3-check
PYTHONPATH=src python scripts/generate_stage3_design_plan.py
```

Ожидается:

- `status: ready_for_stage3_implementation`;
- `execution_status: blocked_until_candidates_and_freeze`;
- 288 profiling cells;
- 48 parameterized validation-only screening cells;
- final status `blocked_until_stage3_freeze`.

## Условия перехода к profiling execution

- реализован profiler executor;
- B0 instrumentation не меняет training results;
- pinned Stage 3 source commit;
- новый environment lock;
- trace schema validation проходит;
- warmup/synchronization protocol проходит smoke.

## Условия перехода к pilot

- B1/B2/C1/C2 имеют отдельные Torch2PC commits;
- exact candidates прошли CPU/GPU equivalence gates;
- approximate candidates прошли finite/stability gates;
- profiling report завершён;
- test loader отсутствует;
- pilot execution plan заморожен.

## Условия перехода к final

- один exact и не более одного approximate candidate выбраны validation-only;
- candidate parameters и non-inferiority margin заморожены;
- Stage 3 environment lock и control artifacts закреплены;
- создан `stage3-pilot-freeze` manifest и tag;
- final config включается отдельным commit;
- execution commit отличается от будущего publication state.


## Практический смысл

Положительный результат проверки означает, что исследователь может начинать
реализацию профилирования по уже описанным правилам. Отрицательный результат
указывает на отсутствующий документ, конфигурацию или защитный механизм.
Проверка не создаёт экспериментальные результаты и не открывает доступ к
тестовой выборке.
