# Caylent Devcontainer CLI Makefile

.PHONY: install lint test clean build

install:
	pip install -e .

lint:
	flake8 src tests
	black --check src tests
	isort --check-only src tests

format:
	black src tests
	isort src tests

test:
	pytest tests/unit -v --cov=caylent_devcontainer_cli --cov-report=term-missing

clean:
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .coverage htmlcov/

build:
	python -m build