SHELL := /usr/bin/env bash

STAGE ?= smoke
METHOD ?= bp
DATASET ?= MNIST
SEED ?= 0
ETA ?=
INFERENCE_STEPS ?=

.PHONY: init host-check image-check build validate prepare pin-torch2pc \
        control-cpu control-gpu run smoke pilot select-pilot apply-pilot-selection freeze-pilot final diagnostics \
        report manifest docs docs-en jupyter lint typecheck test thesis article \
        release clean status epistemic-check freeze-environment

init:
	cp -n .env.example .env || true
	./scripts/init_environment.sh

host-check:
	./scripts/host_preflight.sh

image-check:
	./scripts/check_base_image.sh

build:
	./scripts/build_controlled_image.sh

validate:
	docker compose run --rm validate

prepare:
	docker compose run --rm prepare

pin-torch2pc:
	.venv/bin/python scripts/pin_torch2pc_commit.py

control-cpu:
	docker compose run --rm control-cpu

control-gpu:
	docker compose run --rm control-gpu

run:
	STAGE=$(STAGE) METHOD=$(METHOD) DATASET=$(DATASET) SEED=$(SEED) \
	docker compose run --rm run

smoke:
	$(MAKE) run STAGE=smoke METHOD=bp DATASET=MNIST SEED=0

pilot:
	./scripts/run_matrix.sh pilot

select-pilot:
	.venv/bin/python scripts/select_pilot.py

apply-pilot-selection:
	.venv/bin/python scripts/select_pilot.py --apply

freeze-pilot:
	./scripts/freeze_milestone.sh pilot-freeze

final:
	./scripts/run_matrix.sh final

diagnostics:
	./scripts/run_matrix.sh diagnostics

report:
	docker compose run --rm report

manifest:
	docker compose run --rm manifest

freeze-environment:
	./scripts/freeze_environment.sh

docs:
	docker compose --profile dev up docs

docs-en:
	docker compose --profile dev up docs-en

jupyter:
	docker compose --profile dev up jupyter

lint:
	ruff check src tests scripts

typecheck:
	mypy src

test:
	pytest

epistemic-check:
	python scripts/check_epistemic_language.py
	python scripts/check_language_structure.py
	python scripts/check_local_links.py

thesis:
	cd thesis && latexmk -xelatex -interaction=nonstopmode main.tex

article:
	cd article && latexmk -pdf -interaction=nonstopmode manuscript_EN.tex

release:
	./scripts/build_release.sh

status:
	python -m torch2pc_thesis.cli registry
	git status --short
	git tag --list

clean:
	docker compose down --remove-orphans
	rm -rf .pytest_cache .mypy_cache .ruff_cache build dist site_ru site_en
