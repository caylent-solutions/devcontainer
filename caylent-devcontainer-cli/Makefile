.PHONY: help install lint format unit-test functional-test functional-test-report test clean build coverage coverage-text coverage-json distcheck publish

MAKEFLAGS += --no-print-directory

help: ## Show this help message
	@echo "Available make tasks:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

install: ## Install the package and dependencies
	pip install -e .
	pip install -r requirements.txt
	asdf reshim python 2>/dev/null || true

lint: ## Check code formatting and style
	ruff check src tests
	ruff format --check src tests

format: ## Format code using ruff
	ruff check --fix src tests
	ruff format src tests

unit-test: ## Run unit tests with coverage
	pytest tests/unit -v --cov=src --cov-report=term-missing

functional-test: ## Run functional tests
	pytest tests/functional -v

functional-test-report: ## Generate a report of functional test coverage
	@echo "Functional Test Coverage Report"
	@echo "=============================="
	@grep -r "def test_" tests/functional/ | wc -l | xargs echo "Total functional tests:"
	@echo "\nCommands tested:"
	@grep -r "cdevcontainer" tests/functional/ | grep -v "def\|import" | sort | uniq | sed 's/.*cdevcontainer/cdevcontainer/' | sed 's/].*/]/' || echo "No commands found"

test: unit-test functional-test ## Run all tests (unit and functional)

coverage: ## Generate HTML coverage report
	pytest tests/unit --cov=src --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

coverage-text: ## Generate text coverage report
	pytest tests/unit --cov=src --cov-report=term-missing

coverage-json: ## Generate JSON coverage report
	pytest tests/unit --cov=src --cov-report=json
	@echo "Coverage report generated in coverage.json"

clean: ## Clean build artifacts and cache files
	rm -rf build dist .coverage htmlcov coverage.json
	rm -rf *.egg-info **/*.egg-info __pycache__ .pytest_cache .mypy_cache

build: ## Build the package
	python -m build

distcheck: ## Check the built distribution
	twine check dist/*

publish: clean build distcheck ## Build package (publishing is automated via CI pipeline)
