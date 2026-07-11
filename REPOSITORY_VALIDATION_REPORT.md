# Отчет проверки кандидата первого коммита

[English version](REPOSITORY_VALIDATION_REPORT_EN.md)

## Область проверки

Проверка относится к структуре, исходному коду, методологическим ограничениям
и сборке документов. Она не заменяет эксперимент и не рассматривается как
подтверждение какого-либо вывода о BP или режимах Torch2PC.

## Наблюдаемые результаты статической проверки

```text
Ruff: passed
Mypy: passed
Pytest: 19 passed in 10.64s
Python syntax errors: 0
YAML errors: 0
Notebook code errors: 0
Shell syntax errors: 0
Epistemic-language findings: 0
Language pairs: 58
Broken local links: 0
Resolved configurations: 24
CITATION.cff: valid
MkDocs RU/EN: strict builds passed
Thesis: XeLaTeX build passed
Article: pdfLaTeX build passed
PDF files retained in the public repository: 0
```

## Методологические ограничения, обеспеченные структурой

- позиция автора зафиксирована как позиция нейтрального исследователя-наблюдателя;
- определения, предположения, наблюдения, статистические оценки и интерпретации разделены;
- C0/C1 являются техническими контролями, а не доказательством исследовательских гипотез;
- smoke и pilot не создают test loader и не сохраняют test predictions;
- final ограничен заранее объявленными datasets, methods, model и seed;
- параметры FixedPred и Strict сверяются с `pilot-freeze`;
- повторный успешный final-запуск той же code/config/seed комбинации не образует новую независимую повторность;
- каждая ячейка pilot matrix должна получить terminal status;
- pilot-конфигурация выбирается только по FashionMNIST validation;
- отсутствие статистически значимого различия не трактуется как эквивалентность;
- confirmatory-статус требует не менее десяти полных пар;
- per-sample predictions сохраняют исходные индексы объектов;
- code/config hashes, Docker image ID, container packages, commit Torch2PC и состояние хоста связываются через `environment-lock.json`;
- неудачные попытки сохраняются в append-only реестре.

## Не выполнено в среде подготовки архива

- сборка Docker-образа;
- запуск ROCm на RX 7700 XT;
- runtime-импорт зафиксированной версии Torch2PC;
- загрузка наборов данных и наблюдение их checksums;
- численные C0/C1;
- pilot и final.

До выполнения этих стадий репозиторий содержит предварительно специфицированный
план, исполняемый каркас и средства контроля, но не содержит эмпирического
результата диссертации.

## Плейсхолдеры перед публикацией

Необходимо заполнить автора и URL репозитория в `CITATION.cff`,
`pyproject.toml`, GitHub-шаблонах и LaTeX. Плейсхолдеры в главах сохраняются
намеренно: текст о результатах должен появиться только после эксперимента.
