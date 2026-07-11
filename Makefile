SHELL := /usr/bin/env bash

PYTHON ?= .venv/bin/python3
STAGE ?= smoke
METHOD ?= bp
DATASET ?= MNIST
MODEL ?= lenet_classic
SEED ?= 0
ETA ?=
INFERENCE_STEPS ?=

.PHONY: init host-check image-check pin-base-image build validate prepare pin-torch2pc \
        control-cpu control-gpu run smoke pilot select-pilot apply-pilot-selection \
        freeze-pilot final diagnostics report manifest docs docs-en jupyter lint \
        typecheck test thesis article release clean status epistemic-check \
        freeze-environment

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

apply-pilot-selection:
	$(PYTHON) scripts/select_pilot.py --apply

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

status:
	$(PYTHON) -m torch2pc_thesis.cli registry
	git status --short
	git tag --list

clean:
	docker compose down --remove-orphans
	rm -rf .pytest_cache .mypy_cache .ruff_cache build dist site_ru site_en
