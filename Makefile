NAME = src
PYTHON = python3
VENV = .venv
BIN = $(VENV)/bin

ARGS = --functions_definition data/input/functions_definition.json \
	   --input test/prompt_test.json \
	   --output test/test_output.json

install:
	uv sync
	$(BIN)/python3 -m pip install flake8
	$(BIN)/python3 -m pip install mypy

run:
	uv sync
	uv run python -m $(NAME) $(ARGS)

debug:
	PYTHONPATH=. $(BIN)/$(PYTHON) -m pdb $(NAME)/__main__.py $(ARGS)

clean:
	rm -rfv src/__pycache__
	rm -rfv $(VENV)

lint:
	$(BIN)/flake8 $(NAME)
	$(BIN)/mypy $(NAME) --warn-return-any --warn-unused-ignores \
								--ignore-missing-imports --disallow-untyped-defs \
								--check-untyped-defs

lint-strict:
	$(BIN)/flake8 $(NAME) src
	$(BIN)/mypy $(NAME) src --strict

build:
	poetry build -f wheel

.PHONY: install run debug clean lint lint-strict build