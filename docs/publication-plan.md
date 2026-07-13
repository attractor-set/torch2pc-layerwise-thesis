# План публикации

[English version](publication-plan_EN.md)

Основной paired analysis Stage 1/2 завершён. Публичный narrative строится вокруг
двух раздельных наблюдений:

1. в закреплённой области quality Stage 1 и Stage 2 совпало попарно;
2. implementation-preserving patch существенно изменил runtime profile, после
   чего наблюдался порядок `BP ≈ Exact < FixedPred << Strict`.

Execution source Stage 2
`6d66b0a6f82c30c4fb8eca6247383ca13e0636a2` отделяется от results/publication
state `bb435432a65b76b7fc4f383b566b9a372fc346ae`. Для воспроизведения
используются tags `stage2-execution-v1` и `stage2-results-v1`, а raw artifacts
распространяются через одноимённый GitHub Release.

Публичные claims ограничиваются `lenet_classic`, MNIST, FashionMNIST, seeds
0–9, закреплёнными commits и Ubuntu/ROCm environment. Слова о всеобщей
эквивалентности, превосходстве или новизне не используются без отдельной
эмпирической и литературной основы.

Stage 3 не требуется для публикации текущих результатов. Новые performance
changes, layer-wise diagnostics, robustness или transfer оформляются как
отдельная кампания и не переписывают Stage 1/2.

Следующий archival milestone может получить semantic version и DOI после
отдельного решения автора и проверки требований выбранной площадки.
