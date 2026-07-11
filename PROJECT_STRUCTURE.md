# Структура репозитория

[English version](PROJECT_STRUCTURE_EN.md)

```text
torch2pc-layerwise-thesis/
├── README.md
├── README_EN.md
├── STATUS.md
├── STATUS_EN.md
├── ROADMAP.md
├── ROADMAP_EN.md
├── LANGUAGE_POLICY.md
├── LANGUAGE_POLICY_EN.md
├── RESEARCH_PRINCIPLES.md
├── HYPOTHESES.md
├── PREREGISTRATION.md
├── FIRST_COMMIT.md
├── pyproject.toml
├── Makefile
├── Dockerfile.rocm
├── compose.yaml
├── configs/
│   ├── base.yaml
│   ├── hardware/
│   ├── methods/
│   ├── stages/
│   └── experiments/
├── src/torch2pc_thesis/
│   ├── array_types.py
│   ├── assets.py
│   ├── cli.py
│   ├── config.py
│   ├── data.py
│   ├── models.py
│   ├── pc_methods.py
│   ├── controls.py
│   ├── training.py
│   ├── metrics.py
│   ├── representations.py
│   ├── robustness.py
│   ├── statistics.py
│   ├── registry.py
│   ├── manifests.py
│   └── reporting.py
├── experiments/
│   ├── registry.csv
│   ├── planned/
│   ├── completed/
│   └── failed/
├── results/
│   ├── summaries/
│   ├── figures/
│   └── tables/
├── notebooks/
│   ├── analysis/
│   └── legacy/
├── thesis/
│   ├── main.tex
│   ├── chapters/
│   └── appendices/
├── article/
│   ├── manuscript_EN.tex
│   ├── supplementary_EN.tex
│   └── structure.md
├── references/
│   ├── bibliography.bib
│   └── literature-matrix.csv
├── docs/
│   ├── decisions/
│   ├── research-log/
│   ├── research-design/
│   ├── analysis-plan.md
│   ├── data-management.md
│   └── threats-to-validity.md
├── tests/
├── scripts/
└── .github/
```

## Назначение уровней

### Корневые методологические документы

`RESEARCH_PRINCIPLES.md`, `HYPOTHESES.md` и `PREREGISTRATION.md` фиксируют
эпистемическую позицию, вопросы, критерии и границы подтверждающего анализа до
получения final test.


### `src/`

Единственный основной источник научной логики. Ноутбуки не должны содержать
уникальные реализации обучения, метрик или статистики.

### `configs/`

Декларативное описание эксперимента. Каждый запуск сохраняет итоговую
разрешенную конфигурацию и ее SHA-256.

### `experiments/`

Управление жизненным циклом исследования. Реестр является append-only и
сохраняет неудачные запуски.

### `results/`

В Git добавляются только компактные агрегированные материалы. Сырые запуски и
checkpoints остаются локальными.

### `notebooks/analysis/`

Только анализ готовых результатов. Настройка гиперпараметров и обучение
выполняются через CLI.

### `thesis/` и `article/`

Текст подключает автоматически сформированные таблицы и рисунки. Английская
рукопись статьи явно обозначена суффиксом `_EN`.

### `docs/decisions/`

ADR фиксируют решения, влияющие на воспроизводимость и интерпретацию.

### `.github/`

Автоматические проверки, русские шаблоны по умолчанию и английские варианты
через `_EN`.

## Правило расширения

Новая возможность добавляется в следующем порядке:

```text
Issue
-> ADR при изменении протокола
-> тест
-> модуль src
-> YAML-конфигурация
-> CLI
-> документация
-> эксперимент
-> агрегированный результат
-> глава диссертации
```
