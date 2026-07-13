# Torch2PC Layer-wise Thesis

[English version](README_EN.md)

![Python](https://img.shields.io/badge/Python-3.12-blue)
![PyTorch](https://img.shields.io/badge/PyTorch-2.9.1-ee4c2c)
![ROCm](https://img.shields.io/badge/ROCm-7.2.1-ED1C24)
![Лицензия](https://img.shields.io/badge/код-Apache--2.0-green)
![Статус](https://img.shields.io/badge/этап-Stage%203%20design--ready-blue)

Исследовательский репозиторий магистерской диссертации по сравнению
backpropagation и режимов predictive coding в Torch2PC. Проект организован так,
чтобы отделять предварительные предположения от наблюдений, а выводы - от
процедур, которыми они получены.

## Исследовательская позиция

В проекте принимается позиция нейтрального исследователя-наблюдателя:

- заранее не предполагается превосходство какого-либо метода;
- теоретические ожидания рассматриваются как проверяемые предположения;
- отсутствие статистически обнаруженного различия не трактуется как
  эквивалентность без отдельного equivalence-анализа;
- критерием принятия эмпирического утверждения является результат заранее
  описанного эксперимента в зафиксированной среде;
- отрицательный, смешанный или нестабильный результат сохраняется и
  рассматривается наравне с положительным;
- область вывода ограничивается исследованной реализацией, архитектурами,
  наборами данных и вычислительной средой.

Подробно: [RESEARCH_PRINCIPLES.md](RESEARCH_PRINCIPLES.md).

## Исследовательский вопрос

При каких алгоритмических и вычислительных условиях режимы `Exact`,
`FixedPred` и `Strict` в Torch2PC дают наблюдения, близкие к backpropagation,
а при каких условиях наблюдаемые различия выходят за заранее заданные
численные или статистические границы?

Сравнение планируется проводить по нескольким уровням:

- корректность реализации и контрольные численные соотношения;
- качество классификации;
- послойные градиенты;
- нейронные представления;
- устойчивость к искажениям;
- вычислительное время и память;
- воспроизводимость между независимыми запусками.

## Наблюдаемый статус на 13 июля 2026 года

Validation pilot и две подтверждающие серии завершены в закреплённой
Ubuntu/ROCm-среде:

- validation-only pilot: **96/96** terminal-ячеек, 0 failed, test не вычислялся;
- Stage 1: **80/80**, исходный Torch2PC
  `00c6c50ee3540537bbb56ab2b6567b541f42b093`;
- Stage 2: **80/80**, patched Torch2PC
  `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`;
- CPU/GPU numerical equivalence gates пройдены в закреплённой области;
- regression suite после maintenance: **63 passed**;
- парные значения test accuracy и macro-F1 Stage 1/2 совпали для всех
  datasets, методов и seeds;
- наблюдаемый порядок времени Stage 2:
  `BP ≈ Exact < FixedPred << Strict`.

Implementation-preserving patch изменил вычислительный путь, сохранив
экспериментальный протокол. По среднему total training time относительно
Stage 1 Exact выполнялся примерно на 14% быстрее, FixedPred — на 31%, Strict —
на 26%; BP остался практически неизменным. Полные парные записи находятся в
[`results/cross-version/`](results/cross-version/).

### Разделение execution и publication state

| Роль | Идентификатор |
|---|---|
| Stage 1 source lock | `140e77cc2083bf04234dcea16b95803e63cb0537` |
| Stage 2 execution source | `6d66b0a6f82c30c4fb8eca6247383ca13e0636a2` |
| Stage 2 results/publication state | `bb435432a65b76b7fc4f383b566b9a372fc346ae` |
| Stage 1 tag | `confirmatory-final-v1` |
| Stage 2 execution tag | `stage2-execution-v1` |
| Stage 2 results tag | `stage2-results-v1` |

GitHub Release
[`stage2-results-v1`](https://github.com/attractor-set/torch2pc-layerwise-thesis/releases/tag/stage2-results-v1)
содержит replication bundle, его SHA-256 и file manifest; проверено 660
manifest artifacts. Execution tag фиксирует код, использованный для запуска,
а results tag фиксирует последующее состояние публикации результатов.

Stage 1 и Stage 2 считаются завершёнными и не требуют повторного запуска.
Любое новое изменение производительности относится к отдельному Stage 3 с
новым протоколом и отдельной provenance chain.

Текущий статус: [STATUS.md](STATUS.md).

## Stage 3: design-ready

Расширенный Stage 3 исследует математическую и execution locality, точную
организацию VJP, adaptive stopping, periodic VJP refresh и масштабирование по
глубине/ширине. Подробный протокол: [docs/stage-3-protocol.md](docs/stage-3-protocol.md). Design revision 2 добавляет exact-shortcut control и отдельную predict-correct линию: дешёвая layer-local оценка с обязательными точными correction sweeps и fallback на Strict.

Текущее состояние разрешает начало реализации profiling infrastructure, но
намеренно блокирует profiling campaign, pilot и final execution:

```bash
make stage3-ready
make stage3-plan
```

Детерминированный design plan содержит 336 коротких profiling cells, 48
parameterized core validation-only pilot cells и 27 predict-correct accelerator
screening cells. Stage 3 отсутствует из `TRAINING_STAGES`, а final template
сохраняет `evaluation.use_test=false` до отдельного freeze.

## Контрольные проверки

Термины C0 и C1 используются вместо H0/H1, чтобы не смешивать технические
контроли с нулевыми статистическими гипотезами.

- **C0:** численное сопоставление градиентов `Exact` и BP;
- **C1:** численное сопоставление `FixedPred` при `eta=1`, `n>=depth` и `Exact`;
- **структурная проверка:** проверка выбранных выражений Torch2PC, связанных с
  поправкой Rosenbaum 2025.

Эти проверки ограничены конкретным commit, dtype, устройством и тестовыми
пакетами. Даже успешный результат C0/C1 не рассматривается как универсальное
доказательство эквивалентности алгоритмов.

## Воспроизведение с нуля

Следующая последовательность предназначена для независимого воспроизведения,
а не для повторного выполнения уже завершённых Stage 1/2.

```bash
cp .env.example .env
./scripts/setup_ubuntu.sh
make init
make host-check
make image-check
make pin-base-image
make build
make validate
make prepare
```

`make pin-base-image` заменяет изменяемый Docker tag в локальном `.env` на
ссылку вида `repository@sha256:...`. Финальные и pilot-образы собираются только
после такой фиксации. `.env` остается локальным и не добавляется в Git.

После просмотра скачанного checkout Torch2PC необходимо зафиксировать commit,
закоммитить изменение конфигурации и создать lock-файл окружения:

```bash
make pin-torch2pc
git add configs/base.yaml
git commit -m "research: pin Torch2PC revision"
make pin-base-image
make build
make freeze-environment
git add results/summaries/environment-lock.json
git commit -m "research: lock controlled environment"
make control-cpu
make control-gpu
```

Pilot запускается только после прохождения обоих контрольных контуров:

```bash
make pilot
# make pilot уже создает selection и компактный файл наблюдений;
# для повторной генерации доступны отдельные команды:
make select-pilot
make pilot-observations
make apply-pilot-selection
# проверить изменения configs/methods/*.yaml и закоммитить их
git add configs/methods/
git commit -m "research: apply validation-only pilot selection"
# заново собрать образ, зафиксировать окружение и повторить короткие контроли
make build
make freeze-environment
git add results/summaries/environment-lock.json
git commit -m "research: refresh environment lock after pilot selection"
make control-cpu
make control-gpu
make freeze-pilot
# закоммитить freeze manifest и создать tag pilot-freeze
```

Final запускается только после заморозки pilot-конфигурации:

```bash
make final
make report
make manifest
```

## Защита от утечки test

- `smoke` и `pilot` не создают test loader;
- test разрешен только для стадии `final`;
- final требует замороженного протокола и артефакта `pilot-freeze`;
- каждый запуск сохраняет resolved config, environment manifest, split hashes,
  per-sample predictions, метрики и уникальный `run_id`;
- `pilot_observations.csv` сохраняет компактные проверяемые наблюдения всех
  terminal-ячеек pilot без публикации checkpoints;
- попытки не перезаписывают друг друга;
- повторный успешный final-запуск той же комбинации code/config/seed блокируется,
  чтобы повторный просмотр test не учитывался как новая репликация.

## Структура

| Каталог | Назначение |
|---|---|
| `src/torch2pc_thesis/` | Исполняемая научная логика и CLI |
| `configs/` | Базовые, аппаратные, стадийные и методические конфигурации |
| `experiments/` | Append-only реестр запусков и планы экспериментов |
| `results/` | Агрегированные публичные материалы |
| `notebooks/analysis/` | Анализ зарегистрированных результатов |
| `notebooks/legacy/` | Исторический ноутбук для проверки миграции |
| `thesis/` | Русскоязычный LaTeX-каркас диссертации |
| `article/` | Англоязычный каркас статьи с суффиксом `_EN` |
| `references/` | BibTeX и матрица литературы без PDF |
| `docs/` | Протокол, решения и журнал исследования |

Полная схема: [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md).

## Воспроизводимость

Проект фиксирует или планирует фиксировать:

- Git commit проекта;
- полный commit Torch2PC;
- Docker image ID и digest базового образа;
- версии Python-пакетов;
- контрольные суммы файлов данных;
- индексы train/validation/test;
- model, split, loader и corruption seeds;
- dtype, device, число потоков и workers;
- аппаратное и системное окружение;
- конфигурацию и SHA-256 каждого запуска;
- статус успешных и неудачных запусков.

Подробно: [docs/reproducibility.md](docs/reproducibility.md).

## Язык проекта

Русский является основным языком пользовательских материалов. Английские
версии используют суффикс `_EN`. Технические идентификаторы Python, YAML,
Torch2PC и GitHub сохраняются на английском.

## Публичные и локальные материалы

В Git-репозиторий не включаются скачанные PDF, датасеты, приватные комментарии
и тяжёлые checkpoints. Публикуются код, протокол, конфигурации,
библиографические записи, агрегированные результаты и манифесты. Полный набор
raw Stage 2 artifacts распространяется отдельно через replication bundle в
GitHub Release `stage2-results-v1`.

## Лицензирование

- программный код распространяется по лицензии Apache License 2.0 — см.
  [LICENSE](LICENSE);
- оригинальный текст диссертации, статьи, документации, таблицы и рисунки
  распространяются по лицензии Creative Commons Attribution 4.0 International —
  см. [LICENSE-DOCS](LICENSE-DOCS) и [LICENSE-DOCS_EN](LICENSE-DOCS_EN);
- сторонние материалы сохраняют свои исходные лицензии и условия атрибуции —
  см. [NOTICE](NOTICE) и [NOTICE_EN](NOTICE_EN).
