# ADR-049: переход `QW-4B-E-v2` после слияния и открытие `QW-LC0`

[English version](ADR-049-stage3b-qwake-lc0-post-merge-transition_EN.md)

- Статус: принято
- Дата: 25 июля 2026 года

## Контекст

[Фиксация целостности](../glossary.md#term-integrity-sealing) `QW-4B-E-v2` записана коммитом
`26bc0ef635e13dba719d3356fe17382f0037d1df` и слита в `main` коммитом слияния
`4f23b752a40ae05de9fc7ee49c9962c44083b71d`. Точный выход проверки при [выполнении](../glossary.md#term-execution), пакет аудита и внешняя
печать повторно проверены на `main`; хэш отчёта остаётся
`sha256:54dba01d47814dc00fa53bd69c00865bd1c47754c017c7482c895162d3a86b82`.

Запечатанный результат представляет собой только инженерные [доказательные материалы](../glossary.md#term-evidence).
Разрешение использовано, повтор запрещён, научное [выполнение](../glossary.md#term-execution), тестовая выборка и
публикация закрыты.

## Решение

1. Признать доказательные материалы репозитория `QW-4B-E-v2` зафиксированными на `main`.
2. Открыть `QW-LC0` только для фиксации семантики `R/M/Γ/C`, области
   `LOCAL_COMPUTE`, границ кандидата и силы утверждений.
3. Не открывать реализацию или выполнение `LOCAL_SWEEP` и
   `ANALYTIC_COMPLETION`.
4. Не изменять `QW-4B-E-v2`, старые разрешения, выход, пакет аудита или печать.
5. Сохранить `QW-LC1`, научный образ, C1/C2/C3/R, тестовую выборку и публикацию
   закрытыми до отдельных решений.

## Проверяемая граница

```text
qwake_qw4b_e_v2_repository_evidence_sealed=true
qwake_qw4b_e_v2_repository_seal_commit=26bc0ef635e13dba719d3356fe17382f0037d1df
qwake_qw4b_e_v2_repository_merge_commit=4f23b752a40ae05de9fc7ee49c9962c44083b71d
qwake_qw4b_e_v2_post_merge_verification_passed=true
qwake_qw_lc0_transition_permitted=true
qwake_qw_lc0_open=true
qwake_qw_lc0_semantics_scope_frozen=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
qwake_scientific_image_freeze_permitted=false
test_dataset_access=false
publication_permitted=false
qwake_next_slice=QW-LC0
qwake_post_lc0_next_slice=QW-LC1
```

## Последствия

Следующим самостоятельным срезом является только `QW-LC0` для фиксации
семантики и области. Он не исполняет модель и не создаёт научные доказательные
материалы.
