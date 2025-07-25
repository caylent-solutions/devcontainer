.PHONY: help configure install-hooks pre-commit-check

help: ## Show this help message
	@echo "Available make tasks:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

configure: install-hooks ## Configure the development environment

pre-commit-check: ## Run pre-commit hooks and JSON validation like git hook
	pre-commit run --all-files
	@echo "Validating JSON files outside caylent-devcontainer-cli/..."
	@for file in $$(find . -name "*.json" -not -path "./caylent-devcontainer-cli/*"); do \
		echo "Validating $$file"; \
		if ! jq . "$$file" > /dev/null 2>&1; then \
			echo "❌ Invalid JSON in $$file"; \
			exit 1; \
		fi; \
		echo "✅ $$file is valid JSON"; \
	done

install-hooks: ## Install git hooks for pre-commit and pre-push
	@echo "Installing git hooks..."
	@git config --unset-all core.hooksPath || true
	@pre-commit install || echo "pre-commit not found, skipping pre-commit installation"
	@git config core.hooksPath git-hooks
	@chmod +x git-hooks/pre-commit git-hooks/pre-push
	@echo "Git hooks installed successfully!"
	@echo "Pre-commit hook will check for secrets and run formatting"
	@echo "Pre-push hook will run tests and linting for CLI changes"
