# Fly-in - drone routing simulation
#
# Override the map on any target:  make run MAP=maps/hard/01_maze_nightmare.txt

PYTHON := .venv/bin/python3
MAP    ?= maps/easy/01_linear_path.txt

MYPY_FLAGS := --warn-return-any --warn-unused-ignores \
              --ignore-missing-imports --disallow-untyped-defs \
              --check-untyped-defs

.PHONY: help install run debug clean lint lint-strict maps

help:
	@echo "make install      install the dependencies with uv"
	@echo "make run          run the simulation on MAP"
	@echo "make debug        run the simulation under pdb"
	@echo "make maps         run every map of the maps/ folder"
	@echo "make lint         flake8 . and mypy . with the required flags"
	@echo "make lint-strict  flake8 . and mypy . --strict"
	@echo "make clean        remove the caches"
	@echo ""
	@echo "current MAP: $(MAP)"

install:
	uv sync

run:
	$(PYTHON) main.py $(MAP)

debug:
	$(PYTHON) -m pdb main.py $(MAP)

maps:
	@for map in maps/*/*.txt; do \
		echo "=== $$map ==="; \
		$(PYTHON) main.py $$map | tail -n 8; \
	done

lint:
	$(PYTHON) -m flake8 .
	$(PYTHON) -m mypy . $(MYPY_FLAGS)

lint-strict:
	$(PYTHON) -m flake8 .
	$(PYTHON) -m mypy . --strict

clean:
	find . -type d -name __pycache__ -not -path "./.venv/*" \
		-prune -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache .ruff_cache
