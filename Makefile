NAME = src
PYTHON = python3
VENV = .venv
BIN = $(VENV)/bin

TEST_ARGS = --functions_definition test/input/functions_definition.json\
			--input test/input/prompt_test.json \
			--output test/output/test_output.json
ARGS = --functions_definition data/input/functions_definition.json


install:
	uv sync
	$(BIN)/python3 -m pip install flake8
	$(BIN)/python3 -m pip install mypy

run:
	uv run python -m $(NAME) $(ARGS)

test:
	uv run python -m $(NAME) $(TEST_ARGS)

debug:
	PYTHONPATH=. $(BIN)/$(PYTHON) -m pdb $(NAME)/__main__.py $(ARGS)

clean:
	rm -rfv **/__pycache__/*
	rm -rfv $(VENV)

lint:
	$(BIN)/flake8 $(NAME)
	$(BIN)/mypy $(NAME) --warn-return-any --warn-unused-ignores \
								--ignore-missing-imports --disallow-untyped-defs \
								--check-untyped-defs

lint-strict:
	$(BIN)/flake8 $(NAME)
	$(BIN)/mypy $(NAME) --strict

build:
	poetry build -f wheel

.PHONY: install run test debug clean lint lint-strict build