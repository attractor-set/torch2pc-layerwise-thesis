#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ -d .git ]]; then
  echo "Git-репозиторий уже существует."
else
  git init -b main
  git add .
  git commit -m "infra: initialize reproducible thesis repository"
fi

cat <<'EOF'
Следующие действия:
1. Замените TODO в CITATION.cff и pyproject.toml.
2. Создайте пустой GitHub-репозиторий.
3. Добавьте remote:
   git remote add origin git@github.com:<owner>/torch2pc-layerwise-thesis.git
4. Отправьте main:
   git push -u origin main
5. Включите Issues, Discussions, Projects и защиту ветки.
EOF
