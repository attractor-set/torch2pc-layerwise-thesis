# STAGE3-LAYERWISE-001: послойная диагностика градиентов и представлений

[English version](STAGE3-LAYERWISE-001_EN.md)

## Статус

Design-ready; validation-only pilot разрешён после применения патча и прохождения unit tests.

## Baseline

- Stage 2 execution: `6d66b0a6f82c30c4fb8eca6247383ca13e0636a2`;
- Stage 2 publication: `bb435432a65b76b7fc4f383b566b9a372fc346ae`;
- patched Torch2PC: `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`.

## Вопросы

1. Как меняются cosine similarity, relative L2 и norm ratio градиентов по глубине сети?
2. Отличается ли распределение расхождений FixedPred и Strict от численного контроля Exact–BP?
3. Насколько соответствующие и перекрёстные слои независимо обученных моделей сходны по CKA/RSA?

## Pilot

- dataset: FashionMNIST;
- model: `lenet_classic`;
- model seeds: 0, 1, 2;
- validation batches для same-state probe: 5;
- validation samples для representation probe: 1000;
- checkpoint: best validation checkpoint;
- методы: BP, Exact, FixedPred, Strict;
- test loader: выключен;
- optimizer step: отсутствует;
- timing: анализируется отдельным контуром.

## Статистическая единица

Независимо обученная модель. Batches, параметры и слои являются повторными измерениями внутри model seed и не учитываются как независимые репликации.

## Freeze после pilot

До confirmatory run фиксируются layers, checkpoint schedule, число probe batches/samples, Exact control thresholds, семейства множественных сравнений и правила обработки degenerate CKA/RSA.

## Ограничение

Первая версия работает с доступными checkpoints и итоговыми градиентами PC. Intermediate training trajectory и per-inference-step trace требуют отдельных Stage 3 instrumentation changes.
