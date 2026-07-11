# Проверка репозитория

[English version](validation_EN.md)

Проверки выполняются из текущего Git commit. Статические отчеты с результатами
проверок не хранятся как постоянное утверждение в корне репозитория, поскольку
после изменения исходного кода они перестают описывать текущее состояние.

## Локальная проверка

```bash
source .venv/bin/activate
python3 -m ruff check src tests scripts/*.py
python3 -m mypy src
python3 -m pytest -q
python3 scripts/check_epistemic_language.py
python3 scripts/check_language_structure.py
python3 scripts/check_local_links.py
bash scripts/validate_repository.sh
```

## Проверка в CI

GitHub Actions выполняет те же проверки в чистом окружении с зависимостями,
ограниченными файлами `requirements/lock-dev.txt` и
`requirements/torch-cpu.txt`.

Зеленый CI подтверждает прохождение проверок для конкретного commit. Он не
подтверждает научные гипотезы и не заменяет Docker/ROCm, C0/C1, pilot или final.

## Релизные сведения

`scripts/build_release.sh` создает архив из `git archive` и записывает рядом:

- SHA-256 архива;
- версию проекта;
- полный Git commit;
- время создания метаданных.

Результаты runtime-экспериментов должны иметь собственные манифесты и связь с
`environment-lock.json`.
