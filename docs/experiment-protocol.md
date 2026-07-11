# Экспериментальный протокол

[English version](experiment-protocol_EN.md)

```text
static checks
-> asset preparation
-> pin Torch2PC
-> C0/C1 CPU
-> C0/C1 GPU
-> pilot validation-only grid
-> pilot freeze
-> final paired runs
-> diagnostics
-> reporting
```

Для парного сравнения совпадают split indices, model seed, loader seed,
optimizer, batch size, dtype, image, Torch2PC commit и dataset files.

Неудачный запуск получает отдельный `run_id`, сохраняет failure metadata и не
перезаписывает предыдущий запуск. Повтор не удаляет исходную ошибку.

Final блокируется при отсутствии control-gate файлов или pilot-freeze manifest.

## Повторный доступ к test

Для одной комбинации source commit, resolved configuration и model seed
разрешается один завершенный final-запуск. Технически неудачную попытку можно
повторить, но ее запись и причина сохраняются. Новый успешный запуск после
изменения кода или конфигурации считается отдельным экспериментом и не заменяет
исходный подтверждающий анализ.

## Артефакты наблюдения

Validation и test сохраняются как per-sample prediction artifacts с исходными
индексами, истинными метками, предсказаниями и вероятностями. Это позволяет
проверить агрегированные метрики независимо от исполняемого checkpoint.
