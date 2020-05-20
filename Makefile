.PHONY: help venv

VENV = $(CURDIR)/.venv

help:
	@echo "Usage:"
	@echo "  - make [help]   - Display this help message"
	@echo "  - make venv     - Create a local python virtual environment"

venv:
	-rm -rf .venv
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install -U pip setuptools wheel

