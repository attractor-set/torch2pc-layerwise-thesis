# Финализация публикации Stage 3A

Скрипт `scripts/finalize_stage3a_publication.py` синхронизирует статусную
документацию с завершённой layer-wise кампанией, заменяет агрегатор на
metadata-aware реализацию, создаёт двуязычные completion records и добавляет
неизменяющую первичные данные provenance correction note.

Исходный `COMPOSE_RESOLVED.yaml` сохраняется: исправление документирует
устаревшую переменную, не переписывая исторический snapshot.

После запуска необходимо повторно выполнить агрегирование из raw-каталога,
проверить row counts и hashes, затем добавить publication files в Git.
