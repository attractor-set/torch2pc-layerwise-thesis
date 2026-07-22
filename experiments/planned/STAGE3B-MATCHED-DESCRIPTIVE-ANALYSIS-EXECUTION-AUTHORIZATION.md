# Фиксация execution authorization описательного анализа `Stage 3B`

[English version](STAGE3B-MATCHED-DESCRIPTIVE-ANALYSIS-EXECUTION-AUTHORIZATION_EN.md)

## Назначение

Этот срез фиксирует отдельное перспективное разрешение ровно одной будущей
read-only попытки описательного анализа. Он не запускает executor, не создаёт
квитанцию попытки, не читает значения метрик и не создаёт результаты.

## Канонический пакет

Путь:
`experiments/frozen/stage3b-matched-descriptive-analysis-execution-authorization-v1/`.
Пакет содержит только:

- `authorization.json`;
- точную копию зафиксированного `runtime-preflight.json`;
- `SHA256SUMS`.

Проверка отклоняет лишние файлы, каталоги, символические ссылки, дубликаты
checksum-записей и любые несовпадения request/preflight/runtime bindings.

## Разрешённая область

Authorization фиксирует `execution_count=1`, точную операторскую фразу и один
output root. Она разрешает analysis execution, но одновременно фиксирует, что
execution ещё не выполнено, результаты отсутствуют, тестовая выборка закрыта и
публикация не разрешена.

## Операционная граница

Сам package не открывает выполнение в ветке или PR. Executor допускается только
после merge в чистую `main`, повторной проверки runtime identity, отсутствия
output root и отсутствия локальной квитанции для request digest. После claim
повтор запрещён даже при удалении output root.

```text
execution_authorization_present=true
analysis_execution_permitted=true
analysis_execution_performed=false
execution_attempt_claimed=false
analysis_results_present=false
results_publication_permitted=false
release_publication_permitted=false
```
