# ADR-032: фиксация фактической предварительной проверки среды описательного анализа `Stage 3B`

[English version](ADR-032-stage3b-matched-descriptive-analysis-runtime-preflight-freeze_EN.md)

- **Статус:** принято
- **Дата:** 2026-07-22

## Контекст

ADR-031 реализовал закрытую при ошибке `runtime-preflight` проверку, но не
фиксировал фактическую среду. После слияния реализации в `commit`
`272a9258f70320416ff97c3da076435fd5334bc4` из чистого дерева был получен
невычислительный файл-[кандидат](../glossary.md#term-candidate). Он не разбирал наблюдённые значения метрик и
не создавал выходной каталог, `authorization` или квитанцию
[попытки](../glossary.md#term-attempt).

## Решение

Зафиксировать точный файл-кандидат как
`experiments/frozen/stage3b-matched-descriptive-analysis-runtime-preflight-v1/runtime-preflight.json`
с отдельным `SHA256SUMS`. Файл имеет SHA-256
`1722cce133e047512c2b587c9d8fba15e95457653afd2fa496f295d3b1bbced0` и
внутренние контрольные суммы:

- `preflight_digest=428c9a7fdc1baf2b86a033a12189b9b98cce4e41dbb6e87cb73d42f4e9e901cc`;
- `runtime_identity_digest=e71f0f8539231e466291843e919b412d44ec6022e4dce863785142b67abe007d`;
- `request_digest=5c813e101c17210443b63b6499c7c6fed88fe34029f438942b71ad9faf127a2e`.

Статическая проверка подтверждает канонический `JSON`, точные 11 связанных
файлов среды, 9 SHA-256 запечатанного источника, 18 уникальных имён выходов и
закрытые границы утверждений. Привязка к конкретной среде будет повторно
проверена будущим `authorization verifier` перед
[выполнением](../glossary.md#term-execution).

## Граница решения

```text
runtime_preflight_implemented=true
runtime_preflight_frozen=true
execution_authorization_present=false
execution_attempt_claimed=false
sealed_evidence_execution=false
analysis_results_present=false
results_publication_permitted=false
release_publication_permitted=false
```

Фиксация предварительной проверки не является `authorization`. Исполнитель
остаётся закрытым.

## Последствия

Следующий отдельный срез может создать машиночитаемую `authorization`, которая
должна побайтно связать эту предварительную проверку, запрос выполнения и
идентичность среды. До её слияния запрещены [выполнение](../glossary.md#term-execution), создание результатов и
публикация чернового релиза.
