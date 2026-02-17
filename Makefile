SHELL := /bin/bash
MODELS_DIR := $(HOME)/.cache/docling/models

.PHONY: all
all: setup
	source venv/bin/activate && python worker.py

.PHONY: setup
setup: .env venv $(MODELS_DIR)

.env:
	cp .env.template .env
	@echo "Created .env from template. Please edit it with your credentials before running again."

venv:
	python3 -m venv venv
	source venv/bin/activate && pip install -r requirements.txt

$(MODELS_DIR): venv
	source venv/bin/activate && docling-tools models download

.PHONY: update-dependencies
update-dependencies: venv
	source venv/bin/activate && pip install --upgrade pip
	source venv/bin/activate && pip install --upgrade -r requirements.txt
	source venv/bin/activate && pip freeze > requirements.txt

.PHONY: clean
clean:
	rm -rf venv
	rm -rf docs/*
	rm -rf __pycache__