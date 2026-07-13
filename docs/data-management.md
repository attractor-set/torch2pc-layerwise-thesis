# План управления данными

[English version](data-management_EN.md)

## Источники

Используются публичные benchmark datasets, загружаемые через torchvision. В
репозитории хранятся только инструкции, метаданные и checksums.

## Разделение

Train/validation indices создаются детерминированно и сохраняются отдельно от
test indices. Pilot не создает test loader и не формирует test split artifact.

## Хранение

- `data/` - локальные данные, исключенные из Git;
- `results/splits/` - индексы и checksums;
- `results/runs/` - локальные артефакты попыток;
- `results/summaries/` - агрегированные материалы и компактные проверяемые pilot-наблюдения.

## Публикация

Публикуются checksums, конфигурации, агрегированные результаты и `pilot_observations.csv`, позволяющий пересчитать pilot selection без публикации checkpoints. Исходные файлы
датасетов повторно не распространяются, если лицензия и необходимость не были
отдельно проверены.
