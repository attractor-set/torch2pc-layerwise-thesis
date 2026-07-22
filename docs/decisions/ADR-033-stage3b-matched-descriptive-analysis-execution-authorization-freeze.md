# ADR-033: фиксация разрешения одного запуска описательного анализа `Stage 3B`

[English version](ADR-033-stage3b-matched-descriptive-analysis-execution-authorization-freeze_EN.md)

- **Статус:** принято
- **Дата:** 2026-07-22

## Контекст

`Execution request v1` и фактический `runtime preflight` уже зафиксированы.
`Preflight` подтвердил точную идентичность среды и отсутствие `output root`, но
намеренно сохранил `analysis_execution_permitted=false`. Для перехода к одному
вычислительному [запуску](../glossary.md#term-run) требуется отдельное перспективное решение,
принятое до чтения результатов и связанное с неизменяемыми
`request`/`preflight`/`runtime`-идентичностями.

## Решение

Зафиксировать канонический пакет
`experiments/frozen/stage3b-matched-descriptive-analysis-execution-authorization-v1/`
из трёх обычных файлов:

1. `authorization.json`;
2. точная копия `runtime-preflight.json`;
3. `SHA256SUMS`.

`Authorization` имеет SHA-256
`29f48ae7fe4f8ab92c465d939ee68c2142488bf8463f718d76c41361d9c6a76f`
и внутренний `digest`
`5e4f570d81d373637244563afed9d1765fe0d17b3d726db9282b4104c37d83c0`.
Она связывает `request digest` `5c813e10…127a2e`, `preflight digest`
`428c9a7f…901cc` и `runtime identity` `e71f0f85…007d`, фиксирует точную
операторскую фразу и разрешает ровно одну `read-only`
[попытку](../glossary.md#term-attempt).

## Граница решения

```text
execution_authorization_present=true
analysis_execution_permitted=true
analysis_execution_performed=false
execution_attempt_claimed=false
sealed_evidence_execution=false
analysis_results_present=false
results_publication_permitted=false
release_publication_permitted=false
test_dataset_access=false
```

Фиксация `authorization` не является доказательством
[выполнения](../glossary.md#term-execution). Ветка и `PR` не активируют
исполнитель: пакет должен быть слит в чистую `main`, после чего его идентичность
и текущая среда повторно проверяются отдельным `opening gate`.

## Аннулирование

`Authorization` не должна использоваться, если изменились `request`,
`preflight`, `runtime identity`, любой связанный SHA-256, `source evidence`,
`output root` или операторская граница. Наличие `output root` либо локальной
квитанции попытки также закрывает повтор. Новое разрешение требует новой версии
пакета и отдельного решения.

## Последствия

Следующий срез может только независимо проверить `merged main` и открыть один
`executor invocation`. Публикация результатов остаётся отдельным решением после
проверки 18-файлового `output contract` и повторной проверки `source` SHA-256.
