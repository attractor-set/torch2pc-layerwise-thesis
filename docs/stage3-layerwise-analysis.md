# Stage 3: послойный диагностический контур

## Назначение

Этот контур добавляет два validation-only исследования:

1. **Same-state gradient probe** — BP, Exact, FixedPred и Strict получают один checkpoint и один и тот же validation batch. Optimizer step не выполняется. Градиенты сравниваются отдельно по параметрам и по верхнеуровневым слоям.
2. **Representation probe** — независимо обученные checkpoints сравниваются на одном фиксированном наборе validation samples с помощью linear CKA, RSA и полной cross-layer CKA matrix.

Диагностические запуски используют hooks и копирование тензоров, поэтому их результаты времени и памяти не являются benchmark-результатами. Stage 1/2 остаются неизменными; новые наблюдения относятся только к Stage 3.

## 1. Проверка установки

```bash
python -m pytest tests/unit/test_layerwise.py
python -m ruff check \
  src/torch2pc_thesis/layerwise.py \
  scripts/run_stage3_same_state_probe.py \
  scripts/run_stage3_representation_probe.py \
  scripts/aggregate_stage3_layerwise.py \
  tests/unit/test_layerwise.py
```

## 2. Найти checkpoint

Stage 1/2 checkpoints не хранятся в Git. Используйте распакованный replication bundle или локальные артефакты. Для канонического same-state probe берите парный BP checkpoint:

```bash
find results -type f -name 'checkpoint.pt' | sort
```

## 3. Same-state gradient probe

```bash
python scripts/run_stage3_same_state_probe.py \
  --checkpoint /absolute/path/to/checkpoint.pt \
  --checkpoint-label final \
  --output results/stage3/layerwise/pilot/seed-0/final \
  --enforce-exact-control
```

Результаты:

- `gradient_metrics.csv` — одна строка на batch, метод, scope и слой/параметр;
- `gradient_summary.csv` — среднее по probe batches внутри одной модели;
- `method_losses.csv` — диагностический loss методов;
- `metadata.json` — dataset/model/seed, hash validation indices и результат Exact-vs-BP gate.

Основные поля:

- `cosine` — совпадение направления;
- `relative_l2` — относительная ошибка полного вектора;
- `norm_ratio` — отношение нормы PC к норме BP;
- `sign_agreement` — доля совпавших знаков;
- `max_abs_difference` — максимальное абсолютное расхождение.

Модельный seed остаётся статистической единицей. Строки разных слоёв и batches не следует трактовать как независимые репликации.

## 4. Representation probe

Для корректного сравнения checkpoints должны иметь одинаковые dataset, model, split seed и validation fraction.

```bash
python scripts/run_stage3_representation_probe.py \
  --checkpoint bp=/path/to/bp/checkpoint.pt \
  --checkpoint exact=/path/to/exact/checkpoint.pt \
  --checkpoint fixedpred=/path/to/fixedpred/checkpoint.pt \
  --checkpoint strict=/path/to/strict/checkpoint.pt \
  --output results/stage3/layerwise/pilot/seed-0/final
```

Результаты:

- `representation_metrics.csv` — corresponding-layer CKA и RSA;
- `cross_layer_cka.csv` — полная матрица BP-layer × candidate-layer;
- `activations_<label>.npz` — sample-aligned activation matrices;
- `metadata.json` — список checkpoints, layers и hash validation indices.

Слои `0`, `1`, `3`, `4`, `5` соответствуют верхнеуровневым блокам текущего `lenet_classic`. При изменении модели список необходимо заморозить в отдельной Stage 3 конфигурации до confirmatory run.

## 5. Агрегация нескольких seeds

Организуйте артефакты по seed/checkpoint, затем выполните:

```bash
python scripts/aggregate_stage3_layerwise.py \
  --root results/stage3/layerwise/pilot \
  --output results/stage3/layerwise/pilot/combined
```

Скрипт объединяет таблицы, но намеренно не выполняет статистический тест. Сначала агрегируйте probe batches внутри каждого seed, затем проводите paired analysis по model seeds.

## 6. Рекомендуемый pilot

- Dataset: FashionMNIST;
- Model: `lenet_classic`;
- Seeds: 3;
- Same-state batches: 5;
- Representation samples: 1000;
- Checkpoint: final best checkpoint;
- Test loader: не создаётся.

После проверки объёма данных, устойчивости Exact control и отсутствия degenerate CKA зафиксируйте:

- layers;
- checkpoints;
- число batches/samples;
- семейства гипотез;
- пороги численной эквивалентности;
- правила исключения невалидных observations.

## 7. Ограничение первой версии

Патч анализирует доступные checkpoints и итоговые градиенты PC. Он не восстанавливает отсутствующие intermediate checkpoints Stage 1/2 и не извлекает состояние после каждой внутренней inference iteration Torch2PC.

Для trajectory analysis создайте отдельную Stage 3 training campaign с checkpoint capture на заранее заданных долях optimizer updates. Per-inference-step traces следует добавлять отдельным Torch2PC instrumentation patch после заморозки схемы наблюдений, чтобы не смешивать диагностическую корректность с изменением PC execution path.
