.PHONY: install lint format test clean build

install:
	pip install -e .

lint:
	black --check src tests
	isort --check-only src tests
	flake8 src tests

format:
	black src tests
	isort src tests

test:
	pytest tests -v --cov=src --cov-report=term-missing

clean:
	rm -rf build dist *.egg-info __pycache__ .pytest_cache .coverage

build:
	python setup.py sdist bdist_wheel