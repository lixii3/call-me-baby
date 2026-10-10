NAME = src
PYTHON = python3
VENV = .venv
BIN = $(VENV)/bin
ARGS = --functions_definition data/input/functions_definition.json

install:
	uv sync

run:
	uv sync
	uv run python -m src $(ARGS)

debug:
	$(BIN)/$(PYTHON) -m pdb $(NAME)

clean:
	rm -rfv src/__pycache__
	rm -rfv $(VENV)

lint:
	$(BIN)/flake8 $(NAME) src
	$(BIN)/mypy $(NAME) src --warn-return-any --warn-unused-ignores \
								--ignore-missing-imports --disallow-untyped-defs \
								--check-untyped-defs

lint-strict:
	$(BIN)/flake8 $(NAME) src
	$(BIN)/mypy $(NAME) src --strict

build:
	poetry build -f wheel

.PHONY: install run debug clean lint lint-strict build