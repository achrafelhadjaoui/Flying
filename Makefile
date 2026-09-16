# Fly-in - drone routing simulation
#
# Override the map on any target:  make run MAP=maps/hard/01_maze_nightmare.txt

MAP ?= maps/easy/01_linear_path.txt

MYPY_FLAGS := --warn-return-any --warn-unused-ignores \
              --ignore-missing-imports --disallow-untyped-defs \
              --check-untyped-defs

.PHONY: help install run debug clean lint lint-strict

install:
	uv sync

run:
	uv run main.py $(MAP) 

debug:
	uv run -m pdb main.py $(MAP)


lint:
	uv run -m flake8 .
	uv run -m mypy . $(MYPY_FLAGS)

lint-strict:
	uv run -m flake8 . 
	uv run -m mypy . --strict

clean:
	find . -type d -name __pycache__ -not -path "./.venv/*" \
		-prune -exec rm -rf {} +
	rm -rf .mypy_cache .ruff_cache