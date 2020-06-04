.PHONY: help venv

VENV       = $(CURDIR)/.venv
NIM_SOURCE = docker_tags.nim

help:
	@echo "Usage:"
	@echo "  - make [help]   - Display this help message"
	@echo "  - make venv     - Create a local python virtual environment"
	@echo "  - make nim      - Build dev version of nim port"
	@echo "  - make rel      - Build release version of nim port"
	@echo "  - make static   - Build static version of nim port"

venv:
	-rm -rf .venv
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install -U pip setuptools wheel

nim: $(NIM_SOURCE)
	nim c -d:ssl $(NIM_SOURCE)

rel: $(NIM_SOURCE)
	nim c -d:ssl -d:release --opt:size $(NIM_SOURCE)

static: $(NIM_SOURCE)
	nim c -d:ssl -d:release -d:musl --opt:size $(NIM_SOURCE)

