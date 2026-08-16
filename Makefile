.PHONY: format black isort check test

black:
	black --line-length 120 sampleplan/ tests/ experiments/

isort:
	isort --profile black sampleplan/ tests/ experiments/

format: black isort

check:
	black --check --line-length 120 sampleplan/ tests/ experiments/
	isort --check-only --profile black sampleplan/ tests/ experiments/

requirements:
	poetry update

install:
	poetry install

test:
	 python -m pytest tests
