#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
stage="${1:?stage required}"
PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python}"
if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN=python3
fi
failures=0

run_container() {
  local label="$1"
  shift
  if "$@"; then
    printf 'Завершено: %s\n' "$label"
  else
    failures=$((failures + 1))
    printf 'Неудачная попытка сохранена: %s\n' "$label" >&2
  fi
}

case "$stage" in
  pilot)
    "$PYTHON_BIN" scripts/check_protocol_gate.py pilot
    seeds=(40 41 42)
    datasets=(MNIST FashionMNIST)
    for dataset in "${datasets[@]}"; do
      for seed in "${seeds[@]}"; do
        label="pilot $dataset bp seed=$seed"
        printf '\n=== %s ===\n' "$label"
        run_container "$label" env STAGE=pilot METHOD=bp DATASET="$dataset" SEED="$seed" \
          docker compose run --rm run
      done
      for method in fixedpred strict; do
        while read -r eta steps; do
          for seed in "${seeds[@]}"; do
            label="pilot $dataset $method eta=$eta n=$steps seed=$seed"
            printf '\n=== %s ===\n' "$label"
            run_container "$label" env \
              STAGE=pilot METHOD="$method" DATASET="$dataset" SEED="$seed" \
              docker compose run --rm run \
              torch2pc-thesis run \
                --stage pilot \
                --method "$method" \
                --dataset "$dataset" \
                --seed "$seed" \
                --eta "$eta" \
                --inference-steps "$steps"
          done
        done < <("$PYTHON_BIN" - "$method" <<'INNERPY'
import sys, yaml
from pathlib import Path
method = sys.argv[1]
config = yaml.safe_load(Path(f"configs/methods/{method}.yaml").read_text(encoding="utf-8"))
for item in config.get("search", {}).get("grid", []):
    print(item["eta"], item["inference_steps"])
INNERPY
)
      done
    done
    "$PYTHON_BIN" scripts/select_pilot.py
    printf '%s\n' "Pilot summary created. Review results/summaries/pilot_selection.json."
    printf '%s\n' "To apply the observed selection: $PYTHON_BIN scripts/select_pilot.py --apply"
    printf 'Количество сохраненных неудачных попыток: %s\n' "$failures"
    ;;
  final)
    "$PYTHON_BIN" scripts/check_protocol_gate.py final
    seeds=(0 1 2 3 4 5 6 7 8 9)
    datasets=(MNIST FashionMNIST)
    methods=(bp exact fixedpred strict)
    for dataset in "${datasets[@]}"; do
      for method in "${methods[@]}"; do
        for seed in "${seeds[@]}"; do
          label="final $dataset $method seed=$seed"
          printf '\n=== %s ===\n' "$label"
          run_container "$label" env \
            STAGE=final METHOD="$method" DATASET="$dataset" SEED="$seed" \
            docker compose run --rm run
        done
      done
    done
    printf 'Количество сохраненных неудачных попыток: %s\n' "$failures"
    if (( failures > 0 )); then
      exit 1
    fi
    ;;
  diagnostics)
    echo "Диагностический исполнитель еще не реализован. Текущая команда формирует только сводку зарегистрированных запусков." >&2
    docker compose run --rm report
    ;;
  *)
    echo "Неизвестная стадия: $stage" >&2
    exit 2
    ;;
esac
