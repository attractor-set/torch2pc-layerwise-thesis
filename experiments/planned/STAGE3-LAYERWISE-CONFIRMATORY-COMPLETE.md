# Завершение подтверждающей Stage 3A layer-wise кампании

[English version](STAGE3-LAYERWISE-CONFIRMATORY-COMPLETE_EN.md)

## Область исполнения

- Dataset: FashionMNIST
- Architecture: `lenet_classic`
- Model seeds: 0–9
- Methods: BP, Exact, FixedPred, Strict
- Checkpoint: final
- Same-state reference: парный BP checkpoint
- Representation comparison: независимо обученные парные checkpoints
- Environment: controlled ROCm Docker image

## Контрольные рубежи

- same-state seeds: 10/10;
- representation seeds: 10/10;
- Exact–BP numerical controls: 10/10 passed;
- gradient metric rows: 2250;
- gradient summary rows: 450;
- representation metric rows: 150;
- cross-layer CKA rows: 750;
- gradient cosine defined: 2250/2250;
- representation RSA defined: 150/150;
- artifact hashes: PASS;
- unit tests: 7 passed;
- full regression suite: 97 passed;
- Mypy: PASS.

## Статистическая единица

Статистической единицей является независимо обученная модель, заданная
`model_seed`. Layers, parameters, batches, samples и layer pairs являются
повторными наблюдениями внутри seed и не считаются независимыми репликациями.

## Provenance

Raw observations созданы source commit, записанным в
`results/stage3/layerwise/confirmatory/provenance/SOURCE_COMMIT`.

Исходный `COMPOSE_RESOLVED.yaml` сохранён неизменным. Обнаруженное различие
между его устаревшим `SOURCE_GIT_COMMIT` и фактическим image revision описано
в `provenance/CORRECTION.md`.

Агрегированные representation tables получили `model_seed` из sibling
`metadata.json`; migration repair по canonical `source_file` path не менял
raw activations, gradient/CKA/RSA values, layer/sample/checkpoint selection или
numerical gates.

## Следующая фаза

Evidence готов для парного seed-level статистического анализа, коррекции
множественных сравнений, оценки эффектов, depth-trend анализа и построения
рисунков.
