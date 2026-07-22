# Реализация runtime preflight описательного анализа `Stage 3B`

[English version](STAGE3B-MATCHED-DESCRIPTIVE-ANALYSIS-RUNTIME-PREFLIGHT_EN.md)

## Назначение

Этот срез реализует закрытый при ошибке допуск среды для уже зафиксированного
execution request. Он не создаёт `authorization`, не выполняет анализ и не
читает наблюдённые значения метрик.

## Проверяемая идентичность

Runtime preflight связывает:

- точный Git commit и чистое рабочее дерево;
- версии, пути и SHA-256 исполняемых файлов Python и `Zstandard`;
- версии, пути модулей и SHA-256 NumPy и Matplotlib;
- SHA-256 analysis core, runtime module и обоих CLI;
- frozen protocol и execution request;
- девять SHA-256 исходных доказательных материалов;
- успешную структурную проверку `locality_events.jsonl.zst`;
- отсутствие единственного запрошенного output root.

## Будущий authorization contract

Verifier требует отдельный frozen пакет из:

1. `runtime-preflight.json`;
2. `authorization.json`;
3. `SHA256SUMS`.

Authorization должен связывать request, preflight и runtime digests,
фиксировать `generated_at_utc` не раньше runtime preflight, разрешать ровно
одну read-only попытку и сохранять публикацию закрытой. Точный пакет допускает
только три обычных файла без символических ссылок, каталогов и дубликатов в
`SHA256SUMS`.

## Executor boundary

Executor не принимает внешний путь к authorization и не принимает
`generated_at_utc`. До появления канонического frozen пакета он завершается до
вызова вычислительного ядра. После допуска он атомарно фиксирует локальную
квитанцию попытки для `request_digest`, вычисляет только во временном каталоге
и публикует `output root` лишь после повторной проверки входных SHA-256.

```text
runtime_preflight_implemented=true
runtime_preflight_frozen=true
execution_authorization_present=false
sealed_evidence_execution=false
analysis_results_present=false
results_publication_permitted=false
```
## Зафиксированный артефакт

Фактический preflight, полученный без чтения наблюдённых значений метрик,
зафиксирован в
`experiments/frozen/stage3b-matched-descriptive-analysis-runtime-preflight-v1/`.
Он связывает merge commit `272a9258f70320416ff97c3da076435fd5334bc4`,
`request_digest` `5c813e10…127a2e`, runtime identity
`e71f0f85…007d` и preflight digest `428c9a7f…901cc`. Файловый SHA-256
`runtime-preflight.json` равен
`1722cce133e047512c2b587c9d8fba15e95457653afd2fa496f295d3b1bbced0`.

Фиксация не создаёт `authorization`, не заявляет попытку выполнения и не
открывает анализ или публикацию.
