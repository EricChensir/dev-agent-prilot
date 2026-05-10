SHELL := /bin/bash

.PHONY: install lint type test ci run-api docker-build

install:
	python -m pip install -U pip
	pip install -e '.[dev]'

lint:
	ruff check .

type:
	mypy src

test:
	pytest

ci: lint type test

run-api:
	uvicorn issuefix_agent.api:app --reload

docker-build:
	docker build -t dev-agent-prilot:local .
