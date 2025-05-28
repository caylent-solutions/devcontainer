.PHONY: install lint format unit-test functional-test test clean build coverage publish

install:
	pip install -e .

lint:
	black --check src tests
	isort --check-only src tests
	flake8 src tests

format:
	black src tests
	isort src tests

unit-test:
	pytest tests/unit -v --cov=src --cov-report=term-missing

functional-test:
	pytest tests/functional -v

functional-test-report:
	@echo "Functional Test Coverage Report"
	@echo "=============================="
	@grep -r "def test_" tests/functional/ | wc -l | xargs echo "Total functional tests:"
	@echo "\nCommands tested:"
	@grep -r "cdevcontainer" tests/functional/ | grep -v "def\|import" | sort | uniq | sed 's/.*cdevcontainer/cdevcontainer/' | sed 's/].*/]/' || echo "No commands found"

test: unit-test functional-test

coverage:
	pytest tests/unit --cov=src --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

coverage-text:
	pytest tests/unit --cov=src --cov-report=term-missing

coverage-json:
	pytest tests/unit --cov=src --cov-report=json
	@echo "Coverage report generated in coverage.json"

clean:
	rm -rf build dist *.egg-info __pycache__ .pytest_cache .coverage htmlcov

build:
	python -m build

publish: clean build
	twine check dist/*
	@echo "Ready to publish! To publish to PyPI, create and push a git tag:"
	@echo "git tag -a 0.1.0 -m 'Release 0.1.0'"
	@echo "git push origin 0.1.0"