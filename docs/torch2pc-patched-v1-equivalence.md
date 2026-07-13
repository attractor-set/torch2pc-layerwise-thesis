# Torch2PC patched-v1: изменения реализации и обоснование математической эквивалентности

## 1. Назначение документа

Этот документ описывает изменения, внесённые в реализацию Torch2PC для Final Stage 2, и обосновывает, почему они:

1. сохраняют математические определения исследуемых методов;
2. сохраняют вычисляемые состояния и градиенты в области эксперимента;
3. применимы к архитектуре, данным и протоколу `torch2pc-layerwise-thesis`;
4. изменяют главным образом вычислительный путь, количество повторных обходов autograd-графа и накладные расходы.

Документ не утверждает универсальную формальную эквивалентность для любых возможных PyTorch-модулей. Вывод ограничен закреплёнными версиями кода, контролируемым окружением и классом моделей, проверенным в эксперименте.

## 2. Идентификаторы сравниваемых реализаций

| Роль | Репозиторий / артефакт | Commit / SHA-256 |
|---|---|---|
| Исходная реализация Stage 1 | `external/Torch2PC-original` | `00c6c50ee3540537bbb56ab2b6567b541f42b093` |
| Исправленная реализация Stage 2 | `external/Torch2PC` | `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4` |
| Кумулятивный patch | `patches/torch2pc-patched-v1.patch` | `7ea8733d3f8f8c39251e453cf1631cd0e75b8b42da6da1e67053bebdc9f692b3` |
| Execution-source commit Stage 2 | основной репозиторий | `6d66b0a6f82c30c4fb8eca6247383ca13e0636a2` |
| Environment lock | `results/stage-2/summaries/environment-lock.json` | `0ffe23c915ee47a38d1aaa3d2eb5b8175ca8e63be25840380b19fc6bdd2b045b` |

Stage 2 повторяет матрицу Stage 1:

```text
2 datasets × 1 model × 4 methods × 10 seeds = 80 cells
```

Контролируемая интервенция — commit Torch2PC. Датасеты, splits, модель, методы, параметры обучения, seeds, epochs, batch size, image, аппаратная платформа и правила анализа сохраняются согласно Stage 2 protocol и environment lock.

## 3. Математические инварианты

Патч сохраняет следующие определения и порядок вычислений, существенные для исследуемых методов.

### 3.1. Forward-модель и функция потерь

Патч не изменяет:

- состав и порядок слоёв `torch.nn.Sequential`;
- функции слоёв;
- параметры модели;
- функцию потерь;
- входные и целевые тензоры;
- optimiser и правила обновления параметров в thesis-проекте.

Следовательно, прямое отображение модели и оптимизируемая функция остаются теми же.

### 3.2. Exact

Для Exact сохраняется связь между feed-forward activation, ошибкой и belief:

```text
belief = activation - epsilon
```

Изменение объединяет повторные вычисления в один forward и один согласованный reverse traversal. Вычисляется та же производная той же функции по тем же activation и parameter tensors. Меняется организация вызовов autograd, а не дифференцируемое выражение.

### 3.3. FixedPred

Для FixedPred сохраняются:

```text
epsilon = fixed_activation - belief
state update = epsilon - VJP(next_error)
```

Linearization point остаётся фиксированным в течение inference. Патч строит локальные VJP-графы один раз в той же фиксированной точке и повторно применяет их на inference steps. Это устраняет повторное построение эквивалентных графов и сохраняет Jacobian, к которому применяется vector-Jacobian product.

### 3.4. Strict

Для Strict сохраняются:

```text
epsilon = local_prediction - belief
state update = epsilon - VJP(next_error)
```

Ошибки повторно вычисляются на каждом inference step, а обновление выполняется в исходном обратном порядке. Патч повторно использует output уже выполненного локального forward внутри одной итерации, но не переносит prediction между различными inference steps.

### 3.5. Parameter gradients

До патча gradients отдельных параметров одного модуля могли вычисляться несколькими отдельными вызовами `torch.autograd.grad`. После патча параметры модуля передаются в один вызов.

Для параметров \(\theta_1,\ldots,\theta_k\) это преобразование меняет:

```text
grad(y, theta_1), ..., grad(y, theta_k)
```

на:

```text
grad(y, (theta_1, ..., theta_k))
```

Оба варианта вычисляют компоненты одной производной \(\partial y / \partial \theta\). Объединённый вызов сокращает число reverse traversals, не заменяя функцию, переменные дифференцирования или входной vector для VJP.

## 4. Подробное описание изменений

### 4.1. Корректность API и повторное использование входов

Изменения:

- пользовательский `vinit` передаётся в Strict;
- готовые Exact activations/loss корректно повторно используются;
- проверки `== None` заменены на `is None`.

В Stage 1 и Stage 2 experiment configuration используется `vinit=None`. Поэтому исправление explicit `vinit` расширяет корректность API, но не меняет исследуемый execution path.

### 4.2. Группировка parameter VJP

Изменения:

- gradients всех trainable parameters одного sequential module вычисляются совместно;
- parameterless modules пропускаются;
- локальный graph освобождается после завершения необходимого VJP.

Сохраняются:

- tensors, относительно которых берётся производная;
- scalar/vector output;
- `grad_outputs`;
- соответствие gradient конкретному параметру.

### 4.3. Single-pass Exact

Изменения:

- используется один forward;
- activation errors и parameter gradients извлекаются согласованным reverse traversal;
- устраняются повторный forward и серия отдельных reverse traversals.

Сохраняются activation values, loss, differentiated graph и итоговые derivatives.

### 4.4. Кэширование FixedPred VJP

Изменения:

- локальный graph создаётся один раз на fixed linearization point;
- pullback повторно применяется в течение `n` inference steps;
- graph освобождается после последнего использования;
- `detach()` применяется там, где требовалось отделение истории, а независимая копия storage не использовалась математикой метода.

Сохраняются fixed prediction, Jacobian в точке linearization и sequence state updates.

### 4.5. Повторное использование local forward в Strict

Изменения:

- output одного local forward используется и для prediction error, и для VJP той же итерации;
- удаляются избыточные `model.zero_grad()` внутри inference;
- сокращаются clone/copy operations;
- сохраняются повторный forward на каждом inference step и исходный reverse-order update.

`torch.autograd.grad` возвращает gradients без накопления в `.grad` параметров, поэтому удаление `zero_grad()` из этого внутреннего пути не меняет вычисляемый VJP.

### 4.6. Проверки и benchmark

В candidate добавлены:

- original-vs-patched equivalence tests;
- patched Exact-vs-BP test;
- explicit `vinit` regression test;
- CPU/GPU-compatible microbenchmark.

Локальный test suite candidate:

```text
5 passed
```

Microbenchmark используется как диагностический инструмент. Научные выводы о времени выполнения строятся по полной парной Stage 1/Stage 2 матрице.

## 5. Структурное доказательство сохранения алгоритма

Автоматизированная structural source check подтвердила в pinned candidate:

- Strict пересчитывает errors на каждой итерации;
- Strict использует `prediction - belief`;
- Strict update имеет форму `epsilon - VJP`;
- FixedPred использует `activation - belief`;
- FixedPred update имеет форму `epsilon - VJP`;
- Exact использует `activation - epsilon`.

Все структурные наблюдения имеют `true` в CPU и GPU control artifacts:

```text
results/stage-2/summaries/control_gate_cpu.json
results/stage-2/summaries/control_gate_gpu.json
```

Структурная проверка показывает, что ключевые формулы и порядок алгоритма присутствуют в candidate source. Она дополняется численным сравнением состояний и градиентов.

## 6. Численное доказательство

Контроли выполнены на model seeds `0, 1, 2`, на трёх batches для внутренних controls и одном cross-version batch на seed. Сравнивались loss, output derivative, beliefs, epsilon и parameter gradients.

### 6.1. CPU, float64

Предварительно заданные thresholds:

```text
minimum cosine similarity = 0.99999
maximum relative L2       = 1e-7
```

Результаты:

| Контроль | Minimum cosine | Maximum relative L2 | Maximum absolute |
|---|---:|---:|---:|
| Patched Exact vs BP | `0.999999999999997` | `0.0` | `0.0` |
| Patched FixedPred-control vs Exact | `0.9999999999999962` | `1.0959254353588235e-12` | `6.5910818469738786e-15` |
| Original vs patched Exact | `0.9999999999999951` | `0.0` | `0.0` |
| Original vs patched FixedPred | `0.9999999999999949` | `0.0` | `0.0` |
| Original vs patched Strict | `0.9999999999999901` | `0.0` | `0.0` |

Итог:

```text
gate_observed_within_thresholds = true
```

Для original-vs-patched сравнений максимальные relative-L2 и absolute differences равны нулю в проверенной CPU float64 области.

### 6.2. GPU, float32, ROCm

Предварительно заданные thresholds:

```text
minimum cosine similarity = 0.999
maximum relative L2       = 0.001
```

Результаты:

| Контроль | Minimum cosine | Maximum relative L2 | Maximum absolute |
|---|---:|---:|---:|
| Patched Exact vs BP | `0.999999463558197` | `0.0` | `0.0` |
| Patched FixedPred-control vs Exact | `0.9999996423721313` | `0.0009624222213572001` | `2.0605511963367462e-06` |
| Original vs patched Exact | `0.9999997019767761` | `0.0` | `0.0` |
| Original vs patched FixedPred | `0.9999905228614807` | `0.0` | `0.0` |
| Original vs patched Strict | `0.9999954104423523` | `0.0` | `0.0` |

Итог:

```text
gate_observed_within_thresholds = true
```

Ненулевая FixedPred-vs-Exact разница относится к сравнению двух методов в float32 и остаётся внутри заранее установленного допуска. Для прямых original-vs-patched сравнений Exact, FixedPred и Strict максимальные relative-L2 и absolute differences равны нулю в проверенной GPU области.

## 7. Почему доказательства достаточны для данного эксперимента

Stage 2 использует:

- `lenet_classic`;
- MNIST и FashionMNIST;
- методы BP, Exact, FixedPred и Strict;
- те же seeds `0..9`;
- те же dataset splits;
- те же method hyperparameters;
- тот же training pipeline;
- закреплённый PyTorch/ROCm image;
- AMD Radeon RX 7700 XT;
- patched и original commits, зафиксированные полными SHA.

Контроли выполняются на том же типе sequential architecture и на том же software/hardware stack, что и финальная матрица. Они сравнивают не только конечную scalar metric, но и промежуточные состояния и parameter gradients. Поэтому они непосредственно проверяют механизм, который влияет на обучение.

Для интерпретации Stage 2 используется следующий вывод:

> В закреплённой экспериментальной области patched-v1 сохраняет вычисляемые состояния и градиенты исходного Torch2PC в пределах заранее заданных численных допусков. Следовательно, patched-v1 может использоваться как implementation-preserving candidate для оценки влияния устранения вычислительных накладных расходов.

## 8. Что именно может измениться после патча

Ожидается изменение:

- wall-clock training time;
- mean/median epoch time;
- количества autograd traversals;
- peak allocated/reserved GPU memory;
- соотношения runtime между BP, Exact, FixedPred и Strict.

Эти изменения являются целью Stage 2 и не рассматриваются как нарушение математической эквивалентности.

Небольшие различия конечных training metrics между независимыми запусками возможны из-за float32 execution, GPU kernels и накопления округлений. Поэтому качество оценивается на полной парной матрице, а не по одной ячейке.

## 9. Ограничения вывода

Полученные доказательства не распространяются автоматически на:

- произвольные модели вне проверенного sequential execution path;
- stochastic layers, работающие в отличающихся режимах;
- custom autograd functions с побочными эффектами;
- модули, зависящие от mutation или aliasing tensor storage;
- higher-order gradients;
- другие версии PyTorch, ROCm или CUDA;
- другие Torch2PC commits;
- режимы explicit `vinit`, кроме отдельно добавленного regression test;
- гиперпараметры и inference procedures, не представленные в control protocol.

Для расширения области применимости требуется повторить structural и numerical controls в новом закреплённом окружении.

## 10. Воспроизводимость проверки

### 10.1. Проверка patch

```bash
sha256sum -c patches/torch2pc-patched-v1.patch.sha256

git -C external/Torch2PC diff --check \
  00c6c50ee3540537bbb56ab2b6567b541f42b093..\
b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4
```

### 10.2. Candidate tests

```bash
.venv/bin/python -m pytest -q \
  external/Torch2PC/tests/test_patch_equivalence.py
```

### 10.3. Environment lock

```bash
sha256sum results/stage-2/summaries/environment-lock.json

jq '{
  source_git_commit_at_lock_creation,
  image_source_git_commit,
  torch2pc_commit,
  torch2pc_reference_commit,
  torch2pc_worktree_clean,
  torch2pc_reference_worktree_clean
}' results/stage-2/summaries/environment-lock.json
```

### 10.4. Numerical gates

```bash
jq '{
  device,
  thresholds,
  C0_exact_vs_bp,
  C1_fixedpred_vs_exact,
  C2_C3_original_vs_patched,
  gate_observed_within_thresholds
}' results/stage-2/summaries/control_gate_cpu.json

jq '{
  device,
  thresholds,
  C0_exact_vs_bp,
  C1_fixedpred_vs_exact,
  C2_C3_original_vs_patched,
  gate_observed_within_thresholds
}' results/stage-2/summaries/control_gate_gpu.json
```

### 10.5. Stage 2 protocol

```bash
PYTHONPATH=src .venv/bin/python3 \
  -m scripts.check_stage2_protocol_gate
```

Ожидаемый результат:

```text
Protocol prerequisites observed for stage=final_stage_2
```

## 11. Связанные артефакты

- `patches/torch2pc-patched-v1.patch`
- `patches/torch2pc-patched-v1.patch.sha256`
- `docs/stage-2-protocol.md`
- `docs/stage-2-protocol_EN.md`
- `configs/stages/final_stage_2.yaml`
- `results/stage-2/summaries/prepared_assets.json`
- `results/stage-2/summaries/environment-lock.json`
- `results/stage-2/summaries/control_gate_cpu.json`
- `results/stage-2/summaries/control_gate_gpu.json`
- `results/stage-2/summaries/C0_exact_vs_bp_cpu.csv`
- `results/stage-2/summaries/C0_exact_vs_bp_gpu.csv`
- `results/stage-2/summaries/C1_fixedpred_vs_exact_cpu.csv`
- `results/stage-2/summaries/C1_fixedpred_vs_exact_gpu.csv`
- `results/stage-2/summaries/C2_C3_original_vs_patched_cpu.csv`
- `results/stage-2/summaries/C2_C3_original_vs_patched_gpu.csv`
- `results/stage-2/summaries/final_stage_2_execution_plan.json`
- `results/stage-2/summaries/stage-2-freeze_manifest.json`

## 12. Заключение

Patch `torch2pc-patched-v1` исправляет API defects и устраняет повторные forward/reverse traversals, повторное построение VJP-графов и избыточные tensor copies.

Ключевые математические определения Exact, FixedPred и Strict, порядок state updates, differentiated functions и parameter derivatives сохраняются. Это подтверждается:

1. анализом изменений;
2. structural source checks;
3. candidate regression/equivalence tests;
4. CPU float64 controls;
5. GPU float32/ROCm controls;
6. полным закреплением commits, configuration, image и environment.

В рамках Final Stage 2 patched-v1 является обоснованной implementation-preserving заменой исходной реализации для измерения вычислительной эффективности при сохранении экспериментальной математики.
