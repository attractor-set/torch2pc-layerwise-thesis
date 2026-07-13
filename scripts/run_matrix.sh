#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
stage="${1:?stage required}"
PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python3}"
if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="$(command -v python3)"
fi
failures=0
declare -A pilot_terminal_attempts=()

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

read_pilot_terminal_attempts() {
  "$PYTHON_BIN" - <<'PY'
from pathlib import Path
import csv
import hashlib
import json

lock_path = Path("results/summaries/environment-lock.json")
lock = json.loads(lock_path.read_text(encoding="utf-8"))
lock_sha256 = hashlib.sha256(lock_path.read_bytes()).hexdigest()
source_commit = str(lock["image_source_git_commit"])
torch2pc_commit = str(lock["torch2pc_commit"])

latest = {}
with Path("experiments/registry.csv").open(newline="", encoding="utf-8") as stream:
    for row in csv.DictReader(stream):
        latest[row["run_id"]] = row

for row in latest.values():
    if row["stage"] != "pilot" or row["status"] not in {"completed", "failed"}:
        continue
    if row.get("git_commit") != source_commit:
        continue
    if row.get("torch2pc_commit") != torch2pc_commit:
        continue
    environment_path = Path(row["run_directory"]) / "environment.json"
    if not environment_path.is_file():
        continue
    environment = json.loads(environment_path.read_text(encoding="utf-8"))
    if environment.get("environment_lock_sha256") != lock_sha256:
        continue
    print("|".join([
        row["dataset"],
        row["model"],
        row["method"],
        row["model_seed"],
        row["eta"],
        row["inference_steps"],
    ]))
PY
}

read_final_completed_attempts() {
  "$PYTHON_BIN" - <<'PY'
from pathlib import Path
import csv
import hashlib
import json

lock_path = Path("results/summaries/environment-lock.json")
lock = json.loads(lock_path.read_text(encoding="utf-8"))
lock_sha256 = hashlib.sha256(lock_path.read_bytes()).hexdigest()
source_commit = str(lock["image_source_git_commit"])
torch2pc_commit = str(lock["torch2pc_commit"])

latest = {}
with Path("experiments/registry.csv").open(newline="", encoding="utf-8") as stream:
    for row in csv.DictReader(stream):
        latest[row["run_id"]] = row

for row in latest.values():
    if row["stage"] != "final" or row["status"] != "completed":
        continue
    if row.get("git_commit") != source_commit:
        continue
    if row.get("torch2pc_commit") != torch2pc_commit:
        continue
    if row.get("test_evaluated", "").lower() != "true":
        continue
    environment_path = Path(row["run_directory"]) / "environment.json"
    if not environment_path.is_file():
        continue
    environment = json.loads(environment_path.read_text(encoding="utf-8"))
    if environment.get("environment_lock_sha256") != lock_sha256:
        continue
    print("|".join([
        row["dataset"],
        row["model"],
        row["method"],
        row["model_seed"],
    ]))
PY
}

read_final_execution_plan() {
  "$PYTHON_BIN" - <<'PY'
from pathlib import Path
import json

path = Path("results/summaries/final_execution_plan.json")
plan = json.loads(path.read_text(encoding="utf-8"))
cells = plan.get("cells")
if not isinstance(cells, list) or len(cells) != int(plan.get("planned_cells", -1)):
    raise RuntimeError("Final execution plan is incomplete")
for cell in cells:
    print("\t".join([
        str(cell["dataset"]),
        str(cell["model"]),
        str(cell["method"]),
        str(cell["model_seed"]),
    ]))
PY
}


read_stage2_completed_attempts() {
  "$PYTHON_BIN" - <<'PY'
from pathlib import Path
import csv
import hashlib
import json

lock_path = Path("results/stage-2/summaries/environment-lock.json")
lock = json.loads(lock_path.read_text(encoding="utf-8"))
lock_sha256 = hashlib.sha256(lock_path.read_bytes()).hexdigest()
source_commit = str(lock["image_source_git_commit"])
torch2pc_commit = str(lock["torch2pc_commit"])
registry_path = Path("experiments/registry-stage-2.csv")
if not registry_path.exists():
    raise SystemExit(0)
latest = {}
with registry_path.open(newline="", encoding="utf-8") as stream:
    for row in csv.DictReader(stream):
        latest[row["run_id"]] = row
for row in latest.values():
    if row["stage"] != "final_stage_2" or row["status"] != "completed":
        continue
    if row.get("git_commit") != source_commit:
        continue
    if row.get("torch2pc_commit") != torch2pc_commit:
        continue
    if row.get("test_evaluated", "").lower() != "true":
        continue
    environment_path = Path(row["run_directory"]) / "environment.json"
    if not environment_path.is_file():
        continue
    environment = json.loads(environment_path.read_text(encoding="utf-8"))
    if environment.get("environment_lock_sha256") != lock_sha256:
        continue
    print("|".join([
        row["dataset"], row["model"], row["method"], row["model_seed"]
    ]))
PY
}

read_stage2_execution_plan() {
  "$PYTHON_BIN" - <<'PY'
from pathlib import Path
import json
path = Path("results/stage-2/summaries/final_stage_2_execution_plan.json")
plan = json.loads(path.read_text(encoding="utf-8"))
if plan.get("stage") != "final_stage_2":
    raise RuntimeError("Unexpected Stage 2 plan")
cells = plan.get("cells")
if not isinstance(cells, list) or len(cells) != int(plan.get("planned_cells", -1)):
    raise RuntimeError("Stage 2 execution plan is incomplete")
for cell in cells:
    print("\t".join([
        str(cell["dataset"]), str(cell["model"]), str(cell["method"]),
        str(cell["model_seed"]),
    ]))
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

run_pilot_cell() {
  local key="$1"
  local label="$2"
  shift 2
  if [[ -n "${pilot_terminal_attempts[$key]:-}" ]]; then
    printf 'Пропущена уже зарегистрированная terminal-попытка: %s\n' "$label"
    return
  fi
  run_container "$label" "$@"
  pilot_terminal_attempts["$key"]=1
}

run_experiment() {
  local stage_name="$1"
  local dataset="$2"
  local model="$3"
  local method="$4"
  local seed="$5"
  shift 5
  docker compose run --rm -T run \
    torch2pc-thesis run \
      --stage "$stage_name" \
      --dataset "$dataset" \
      --model "$model" \
      --method "$method" \
      --seed "$seed" \
      "$@" \
    </dev/null
}

case "$stage" in
  pilot)
    "$PYTHON_BIN" scripts/check_protocol_gate.py pilot
    mapfile -t seeds < <(read_yaml_list configs/stages/pilot.yaml selection.seeds)
    mapfile -t datasets < <(read_yaml_list configs/stages/pilot.yaml selection.datasets)
    mapfile -t models < <(read_yaml_list configs/stages/pilot.yaml selection.models)
    mapfile -t methods < <(read_yaml_list configs/stages/pilot.yaml selection.methods)
    while IFS= read -r key; do
      [[ -n "$key" ]] && pilot_terminal_attempts["$key"]=1
    done < <(read_pilot_terminal_attempts)

    for dataset in "${datasets[@]}"; do
      for model in "${models[@]}"; do
        for method in "${methods[@]}"; do
          if [[ "$method" == "bp" || "$method" == "exact" ]]; then
            for seed in "${seeds[@]}"; do
              label="pilot $dataset $model $method seed=$seed"
              printf '\n=== %s ===\n' "$label"
              key="$dataset|$model|$method|$seed||"
              run_pilot_cell "$key" "$label" \
                run_experiment pilot "$dataset" "$model" "$method" "$seed"
            done
            continue
          fi

          mapfile -t method_grid < <(read_method_grid "$method")
          for grid_item in "${method_grid[@]}"; do
            read -r eta steps <<<"$grid_item"
            [[ -n "$eta" && -n "$steps" ]] || continue
            for seed in "${seeds[@]}"; do
              label="pilot $dataset $model $method eta=$eta n=$steps seed=$seed"
              key="$dataset|$model|$method|$seed|$eta|$steps"
              printf '\n=== %s ===\n' "$label"
              run_pilot_cell "$key" "$label" \
                run_experiment pilot "$dataset" "$model" "$method" "$seed" \
                  --eta "$eta" --inference-steps "$steps"
            done
          done
        done
      done
    done
    "$PYTHON_BIN" scripts/select_pilot.py
    "$PYTHON_BIN" scripts/generate_pilot_observations.py
    printf '%s\n' "Pilot summary создан: results/summaries/pilot_selection.json"
    printf '%s\n' "Pilot observations созданы: results/summaries/pilot_observations.csv"
    printf '%s\n' "Применение наблюдаемого выбора: $PYTHON_BIN scripts/select_pilot.py --apply"
    printf 'Количество сохраненных неудачных попыток: %s\n' "$failures"
    ;;
  final)
    "$PYTHON_BIN" scripts/check_protocol_gate.py final
    declare -A final_completed_attempts=()
    while IFS= read -r key; do
      [[ -n "$key" ]] && final_completed_attempts["$key"]=1
    done < <(read_final_completed_attempts)

    while IFS=$'\t' read -r dataset model method seed; do
      [[ -n "$dataset" && -n "$model" && -n "$method" && -n "$seed" ]] || continue
      key="$dataset|$model|$method|$seed"
      label="final $dataset $model $method seed=$seed"
      if [[ -n "${final_completed_attempts[$key]:-}" ]]; then
        printf 'Пропущен уже завершенный final-запуск: %s\n' "$label"
        continue
      fi
      printf '\n=== %s ===\n' "$label"
      run_container "$label" \
        run_experiment final "$dataset" "$model" "$method" "$seed"
    done < <(read_final_execution_plan)

    printf 'Количество сохраненных неудачных попыток: %s\n' "$failures"
    if (( failures > 0 )); then
      exit 1
    fi
    ;;
  final_stage_2)
    PYTHONPATH=src "$PYTHON_BIN" scripts/check_stage2_protocol_gate.py
    declare -A stage2_completed_attempts=()
    while IFS= read -r key; do
      [[ -n "$key" ]] && stage2_completed_attempts["$key"]=1
    done < <(read_stage2_completed_attempts)

    while IFS=$'\t' read -r dataset model method seed; do
      [[ -n "$dataset" && -n "$model" && -n "$method" && -n "$seed" ]] || continue
      key="$dataset|$model|$method|$seed"
      label="final-stage-2 $dataset $model $method seed=$seed"
      if [[ -n "${stage2_completed_attempts[$key]:-}" ]]; then
        printf 'Пропущен уже завершенный Stage 2 запуск: %s\n' "$label"
        continue
      fi
      printf '\n=== %s ===\n' "$label"
      run_container "$label" \
        run_experiment final_stage_2 "$dataset" "$model" "$method" "$seed"
    done < <(read_stage2_execution_plan)

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
