# Контракт matched runner Stage 3B B1/B2

## Состояние

Для научно допущенной общей матрицы B0/B1/B2 из 288 ячеек реализован
контракт candidate-aware runner. Runtime authorization не выдана, измерения
по-прежнему запрещены.

## Диспетчеризация кандидатов

Runner фиксирует три лениво загружаемых адаптера:

- `stage2_baseline` → `torch2pc_thesis.pc_methods.load_pc_infer`;
- `isolated_layer_vjp` →
  `torch2pc_thesis.stage3b_b1_isolated_vjp.load_b1_pc_infer`;
- `composite_vjp` →
  `torch2pc_thesis.stage3b_b2_composite_vjp.load_b2_pc_infer`.

Planner проверяет опубликованные matched manifest и opening request, требует
все 96 блоков и 288 ячеек, сохраняет исходные `block_order` и
`candidate_order`, а также отображает `fixedpred`/`strict` в существующие
метки методов Torch2PC.

## Контракт восстановления и порядка

Перед каждым кандидатом matched-блока будущий runtime executor обязан
восстанавливать:

1. состояние модели;
2. состояние оптимизатора;
3. состояние RNG;
4. закреплённое состояние minibatch.

Контракт зафиксирован строкой
`restore_model_optimizer_rng_and_minibatch_before_each_candidate`. Mocked
block harness проверяет порядок восстановления и dispatch без создания
временных, memory, gradient или иных profiling evidence.

## Текущая граница

Каждая запланированная ячейка имеет disposition
`blocked_runtime_authorization`. Planner может записать только non-evidence
plan под `/tmp`.

Этот slice не:

- выдаёт ROCm/float32 runtime authorization;
- выполняет warm-up или measured steps;
- записывает profiling results;
- изменяет sealed B1/B2 evidence или contracts;
- открывает EX-IF0, estimator, active ECZ, QWake-PC, controller actions,
  offline policy selection или test-split access.

Следующий отдельный slice — project/environment freeze ROCm/float32, lane
preflight, operator acknowledgement и контракт authorization token.
