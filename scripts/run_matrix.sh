#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
stage="${1:?stage required}"
PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python3}"
if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="$(command -v python3)"
fi
failures=0

read_yaml_list() {
  local file="$1"
  local dotted_path="$2"
  "$PYTHON_BIN" - "$file" "$dotted_path" <<'PY'
from pathlib import Path
import sys
import yaml

value = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))
for part in sys.argv[2].split("."):
    value = value[part]
if not isinstance(value, list) or not value:
    raise RuntimeError(f"Expected a non-empty list at {sys.argv[2]}")
for item in value:
    print(item)
PY
}

read_method_grid() {
  local method="$1"
  "$PYTHON_BIN" - "$method" <<'PY'
from pathlib import Path
import sys
import yaml

method = sys.argv[1]
config = yaml.safe_load(
    Path(f"configs/methods/{method}.yaml").read_text(encoding="utf-8")
)
for item in config.get("search", {}).get("grid", []):
    print(item["eta"], item["inference_steps"])
PY
}

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

run_experiment() {
  local stage_name="$1"
  local dataset="$2"
  local model="$3"
  local method="$4"
  local seed="$5"
  shift 5
  docker compose run --rm run \
    torch2pc-thesis run \
      --stage "$stage_name" \
      --dataset "$dataset" \
      --model "$model" \
      --method "$method" \
      --seed "$seed" \
      "$@"
}

case "$stage" in
  pilot)
    "$PYTHON_BIN" scripts/check_protocol_gate.py pilot
    mapfile -t seeds < <(read_yaml_list configs/stages/pilot.yaml selection.seeds)
    mapfile -t datasets < <(read_yaml_list configs/stages/pilot.yaml selection.datasets)
    mapfile -t models < <(read_yaml_list configs/stages/pilot.yaml selection.models)
    mapfile -t methods < <(read_yaml_list configs/stages/pilot.yaml selection.methods)

    for dataset in "${datasets[@]}"; do
      for model in "${models[@]}"; do
        for method in "${methods[@]}"; do
          if [[ "$method" == "bp" || "$method" == "exact" ]]; then
            for seed in "${seeds[@]}"; do
              label="pilot $dataset $model $method seed=$seed"
              printf '\n=== %s ===\n' "$label"
              run_container "$label" \
                run_experiment pilot "$dataset" "$model" "$method" "$seed"
            done
            continue
          fi

          while read -r eta steps; do
            [[ -n "$eta" && -n "$steps" ]] || continue
            for seed in "${seeds[@]}"; do
              label="pilot $dataset $model $method eta=$eta n=$steps seed=$seed"
              printf '\n=== %s ===\n' "$label"
              run_container "$label" \
                run_experiment pilot "$dataset" "$model" "$method" "$seed" \
                  --eta "$eta" --inference-steps "$steps"
            done
          done < <(read_method_grid "$method")
        done
      done
    done
    "$PYTHON_BIN" scripts/select_pilot.py
    printf '%s\n' "Pilot summary создан: results/summaries/pilot_selection.json"
    printf '%s\n' "Применение наблюдаемого выбора: $PYTHON_BIN scripts/select_pilot.py --apply"
    printf 'Количество сохраненных неудачных попыток: %s\n' "$failures"
    ;;
  final)
    "$PYTHON_BIN" scripts/check_protocol_gate.py final
    mapfile -t seeds < <(read_yaml_list configs/stages/final.yaml selection.seeds)
    mapfile -t datasets < <(read_yaml_list configs/stages/final.yaml selection.datasets)
    mapfile -t models < <(read_yaml_list configs/stages/final.yaml selection.models)
    mapfile -t methods < <(read_yaml_list configs/stages/final.yaml selection.methods)

    for dataset in "${datasets[@]}"; do
      for model in "${models[@]}"; do
        for method in "${methods[@]}"; do
          for seed in "${seeds[@]}"; do
            label="final $dataset $model $method seed=$seed"
            printf '\n=== %s ===\n' "$label"
            run_container "$label" \
              run_experiment final "$dataset" "$model" "$method" "$seed"
          done
        done
      done
    done
    printf 'Количество сохраненных неудачных попыток: %s\n' "$failures"
    if (( failures > 0 )); then
      exit 1
    fi
    ;;
  diagnostics)
    echo "Диагностический исполнитель еще не реализован. Команда формирует только сводку зарегистрированных запусков." >&2
    docker compose run --rm report
    ;;
  *)
    echo "Неизвестная стадия: $stage" >&2
    exit 2
    ;;
esac
