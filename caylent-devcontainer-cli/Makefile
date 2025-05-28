.PHONY: install lint format test clean build coverage

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

coverage:
	pytest tests --cov=src --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

clean:
	rm -rf build dist *.egg-info __pycache__ .pytest_cache .coverage htmlcov

build:
	python setup.py sdist bdist_wheel