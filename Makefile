.PHONY: configure install-hooks

configure: install-hooks

install-hooks:
	@echo "Installing git hooks..."
	@git config --unset-all core.hooksPath || true
	@pre-commit install || echo "pre-commit not found, skipping pre-commit installation"
	@git config core.hooksPath git-hooks
	@chmod +x git-hooks/pre-commit git-hooks/pre-push
	@echo "Git hooks installed successfully!"
	@echo "Pre-commit hook will check for secrets and run formatting"
	@echo "Pre-push hook will run tests and linting for CLI changes"
