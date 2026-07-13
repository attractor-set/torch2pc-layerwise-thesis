SHELL := /usr/bin/env bash
.DEFAULT_GOAL := help

PYTHON ?= .venv/bin/python3
STAGE ?= smoke
METHOD ?= bp
DATASET ?= MNIST
MODEL ?= lenet_classic
SEED ?= 0
ETA ?=
INFERENCE_STEPS ?=

.PHONY: help init host-check image-check pin-base-image build validate prepare pin-torch2pc \
        control-cpu control-gpu run smoke pilot select-pilot pilot-observations \
        apply-pilot-selection final-plan freeze-pilot final diagnostics report manifest docs \
        docs-en jupyter lint \
        typecheck test thesis article release clean status epistemic-check \
        freeze-environment configure-stage2 prepare-stage2 freeze-stage2-environment \
        control-stage2-cpu control-stage2-gpu stage2-plan freeze-stage2 final-stage2 \
        snapshot-stage2 report-stage2 manifest-stage2 compare-stages bundle-stage2 \
        stage3-ready stage3-plan

help:
	@printf '%s\n' \
	  'Usage: make <target> [VARIABLE=value]' \
	  '' \
	  'Environment:' \
	  '  init                  Create the local CPU development environment' \
	  '  host-check            Validate the native Ubuntu host' \
	  '  image-check           Validate the configured ROCm base image' \
	  '  pin-base-image        Pin the ROCm base image by digest' \
	  '  build                 Build the controlled Docker image' \
	  '  validate              Run repository validation in Docker' \
	  '  prepare               Prepare datasets and external dependencies' \
	  '  pin-torch2pc          Pin the external Torch2PC revision' \
	  '' \
	  'Controls and experiments:' \
	  '  control-cpu           Run the CPU numerical control gate' \
	  '  control-gpu           Run the GPU numerical control gate' \
	  '  smoke                 Run the smoke experiment' \
	  '  pilot                 Run the pilot matrix' \
	  '  pilot-observations    Export verified pilot observations' \
	  '  final-plan            Build the deterministic final execution plan' \
	  '  final                 Run the confirmatory experiment matrix' \
	  '  configure-stage2      Pin the patched Torch2PC candidate revision' \
	  '  prepare-stage2        Prepare Stage 2 assets and provenance' \
	  '  control-stage2-cpu    Run Stage 2 CPU numerical gates' \
	  '  control-stage2-gpu    Run Stage 2 GPU numerical gates' \
	  '  stage2-plan           Build the deterministic Stage 2 execution plan' \
	  '  freeze-stage2         Freeze the Stage 2 protocol evidence' \
	  '  final-stage2          Run the isolated 80-cell Stage 2 matrix' \
	  '  snapshot-stage2       Validate and snapshot the completed Stage 2 registry' \
	  '  report-stage2         Build Stage 2 reports' \
	  '  compare-stages        Build paired Stage 1 vs Stage 2 reports' \
	  '  bundle-stage2         Verify and package the complete Stage 2 replication bundle' \
	  '  diagnostics           Run diagnostic experiments' \
	  '  stage3-ready          Validate the Stage 3 design-ready scaffold' \
	  '  stage3-plan           Generate the deterministic Stage 3 design plan' \
	  '' \
	  'Quality and outputs:' \
	  '  lint                  Run Ruff' \
	  '  typecheck             Run Mypy' \
	  '  test                  Run Pytest' \
	  '  epistemic-check       Run documentation and language checks' \
	  '  report                Build experiment reports' \
	  '  manifest              Build artifact manifests' \
	  '  thesis                Build the dissertation' \
	  '  article               Build the article' \
	  '  status                Show experiment and Git status' \
	  '  clean                 Remove local generated caches'

init:
	cp -n .env.example .env || true
	bash scripts/init_environment.sh

host-check:
	bash scripts/host_preflight.sh

image-check:
	bash scripts/check_base_image.sh

pin-base-image:
	bash scripts/pin_base_image.sh

build:
	bash scripts/build_controlled_image.sh

validate:
	docker compose run --rm validate

prepare:
	docker compose run --rm prepare

pin-torch2pc:
	$(PYTHON) scripts/pin_torch2pc_commit.py

control-cpu:
	docker compose run --rm control-cpu

control-gpu:
	docker compose run --rm control-gpu

run:
	STAGE=$(STAGE) METHOD=$(METHOD) DATASET=$(DATASET) MODEL=$(MODEL) SEED=$(SEED) \
	docker compose run --rm run

smoke:
	$(MAKE) run STAGE=smoke METHOD=bp DATASET=MNIST MODEL=lenet_classic SEED=0

pilot:
	bash scripts/run_matrix.sh pilot

select-pilot:
	$(PYTHON) scripts/select_pilot.py

pilot-observations:
	$(PYTHON) scripts/generate_pilot_observations.py

apply-pilot-selection:
	$(PYTHON) scripts/select_pilot.py --apply

final-plan:
	$(PYTHON) scripts/generate_final_execution_plan.py

freeze-pilot:
	bash scripts/freeze_milestone.sh pilot-freeze

final:
	bash scripts/run_matrix.sh final

diagnostics:
	bash scripts/run_matrix.sh diagnostics

report:
	docker compose run --rm report

manifest:
	docker compose run --rm manifest

freeze-environment:
	bash scripts/freeze_environment.sh

docs:
	docker compose --profile dev up docs

docs-en:
	docker compose --profile dev up docs-en

jupyter:
	docker compose --profile dev up jupyter

lint:
	$(PYTHON) -m ruff check src tests scripts/*.py

typecheck:
	$(PYTHON) -m mypy src

test:
	$(PYTHON) -m pytest -q

epistemic-check:
	$(PYTHON) scripts/check_epistemic_language.py
	$(PYTHON) scripts/check_language_structure.py
	$(PYTHON) scripts/check_local_links.py

thesis:
	cd thesis && latexmk -xelatex -interaction=nonstopmode main.tex

article:
	cd article && latexmk -pdf -interaction=nonstopmode manuscript_EN.tex

release:
	bash scripts/build_release.sh

# Stage 2: exact replication of the 80-cell final matrix with a patched
# Torch2PC implementation. Stage 1 evidence remains immutable.
configure-stage2:
	@test -n "$(PATCHED_TORCH2PC_COMMIT)" || \
		(echo "PATCHED_TORCH2PC_COMMIT=<40-char SHA> is required" >&2; exit 2)
	$(PYTHON) scripts/configure_stage2.py \
		--commit "$(PATCHED_TORCH2PC_COMMIT)" \
		$(if $(PATCHED_TORCH2PC_REPOSITORY),--repository "$(PATCHED_TORCH2PC_REPOSITORY)",)

prepare-stage2:
	docker compose run --rm -e ASSET_STAGE=final_stage_2 prepare

freeze-stage2-environment:
	PYTHONPATH=src $(PYTHON) scripts/freeze_stage2_environment.py

control-stage2-cpu:
	docker compose run --rm control-cpu \
		python scripts/run_stage2_control_gate.py cpu

control-stage2-gpu:
	docker compose run --rm control-gpu \
		python scripts/run_stage2_control_gate.py gpu

stage2-plan:
	PYTHONPATH=src $(PYTHON) -m scripts.generate_stage2_execution_plan

freeze-stage2:
	PYTHONPATH=src $(PYTHON) scripts/freeze_stage2.py

final-stage2:
	bash scripts/run_matrix.sh final_stage_2

snapshot-stage2:
	PYTHONPATH=src $(PYTHON) scripts/snapshot_stage2_results.py

report-stage2:
	docker compose run --rm report \
		torch2pc-thesis report \
		--registry experiments/registry-stage-2-80-completed.csv \
		--stage final_stage_2 \
		--summary-dir results/stage-2/summaries \
		--table-dir results/stage-2/tables

manifest-stage2:
	docker compose run --rm \
		-v "$(CURDIR)/src:/workspace/src:ro" \
		manifest torch2pc-thesis manifest \
		--directory results/stage-2 \
		--output results/stage-2/summaries/results_manifest.json \
		--environment-lock results/stage-2/summaries/environment-lock.json

compare-stages:
	docker compose run --rm report \
		torch2pc-thesis compare \
		--reference-registry experiments/registry-final-80-completed.csv \
		--candidate-registry experiments/registry-stage-2-80-completed.csv \
		--output-dir results/cross-version

bundle-stage2:
	bash scripts/build_stage2_replication_bundle.sh

# Stage 3 is design-ready but remains deliberately non-executable until
# candidate implementations, numerical gates, and a separate freeze exist.
stage3-ready:
	PYTHONPATH=src $(PYTHON) scripts/check_stage3_readiness.py

stage3-plan:
	PYTHONPATH=src $(PYTHON) scripts/generate_stage3_design_plan.py

status:
	$(PYTHON) -m torch2pc_thesis.cli registry
	git status --short
	git tag --list

clean:
	docker compose down --remove-orphans
	rm -rf .pytest_cache .mypy_cache .ruff_cache build dist site_ru site_en
