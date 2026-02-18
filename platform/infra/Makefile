# Platform Infrastructure - Makefile
#
# Wraps Terragrunt operations for deploying infrastructure.
# Follows the pattern from the sql-polyglot reference repo.
#
# Prerequisites:
#   - terraform and terragrunt installed (see .tool-versions)
#   - Authenticated AWS session (explicit credentials exported)
#
# Usage:
#   make help                          # Show available targets
#   make check-auth                    # Verify AWS authentication
#   make init MODULE=ecr-public-repository   # Initialize backend
#   make plan MODULE=ecr-public-repository   # Generate execution plan
#   make apply MODULE=ecr-public-repository  # Apply changes
#   make output MODULE=ecr-public-repository # Show outputs

# =============================================================================
# Configuration
# =============================================================================

REGION ?= us-east-1
MODULE ?=
TERRAGRUNT_DIR := terragrunt/$(REGION)/$(MODULE)

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
CYAN := \033[0;36m
RESET := \033[0m

# =============================================================================
# Help
# =============================================================================

.PHONY: help check-tools check-auth check-module init plan apply destroy output fmt validate-config clean-cache

help: ## Show this help message
	@echo "$(CYAN)Platform Infrastructure - Makefile$(RESET)"
	@echo "$(CYAN)===================================$(RESET)"
	@echo ""
	@echo "$(YELLOW)Configuration:$(RESET)"
	@echo "  REGION=$(REGION)"
	@echo "  MODULE=$(MODULE)"
	@echo "  TERRAGRUNT_DIR=$(TERRAGRUNT_DIR)"
	@echo ""
	@echo "$(YELLOW)Available targets:$(RESET)"
	@awk 'BEGIN {FS = ":.*##"; printf ""} /^[a-zA-Z_-]+:.*?##/ { printf "  $(CYAN)%-20s$(RESET) %s\n", $$1, $$2 } /^##@/ { printf "\n$(YELLOW)%s$(RESET)\n", substr($$0, 5) }' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)Examples:$(RESET)"
	@echo "  make plan MODULE=ecr-public-repository"
	@echo "  make apply MODULE=ecr-public-repository"

# =============================================================================
# Validation
# =============================================================================

##@ Validation

check-tools: ## Verify required tools are installed
	@echo "$(BLUE)Checking required tools...$(RESET)"
	@command -v terraform >/dev/null 2>&1 || { echo "$(RED)terraform is required but not installed$(RESET)"; exit 1; }
	@command -v terragrunt >/dev/null 2>&1 || { echo "$(RED)terragrunt is required but not installed$(RESET)"; exit 1; }
	@command -v aws >/dev/null 2>&1 || { echo "$(RED)aws CLI is required but not installed$(RESET)"; exit 1; }
	@echo "$(GREEN)All required tools are available$(RESET)"

check-auth: ## Verify AWS authentication is active
	@echo "$(BLUE)Checking AWS authentication...$(RESET)"
	@aws sts get-caller-identity > /dev/null 2>&1 || { echo "$(RED)AWS authentication failed. Export credentials first:$(RESET)"; echo "  export AWS_PROFILE=platform-prod-admin"; echo "  eval \$$(aws configure export-credentials --format env)"; echo "  unset AWS_PROFILE"; exit 1; }
	@echo "$(GREEN)AWS authentication verified: $$(aws sts get-caller-identity --query 'Account' --output text)$(RESET)"

check-module: ## Verify MODULE is set and directory exists
	@if [ -z "$(MODULE)" ]; then \
		echo "$(RED)MODULE is required. Example: make plan MODULE=ecr-public-repository$(RESET)"; \
		exit 1; \
	fi
	@if [ ! -d "$(TERRAGRUNT_DIR)" ]; then \
		echo "$(RED)Terragrunt directory not found: $(TERRAGRUNT_DIR)$(RESET)"; \
		exit 1; \
	fi

# =============================================================================
# Terragrunt Operations
# =============================================================================

##@ Infrastructure Management

init: check-tools check-auth check-module ## Initialize Terragrunt backend
	@echo "$(BLUE)Initializing Terragrunt backend for $(MODULE)...$(RESET)"
	cd $(TERRAGRUNT_DIR) && terragrunt init

plan: check-module init ## Generate Terragrunt execution plan
	@echo "$(BLUE)Generating execution plan for $(MODULE)...$(RESET)"
	cd $(TERRAGRUNT_DIR) && terragrunt plan

apply: check-module init ## Apply Terragrunt configuration
	@echo "$(BLUE)Applying configuration for $(MODULE)...$(RESET)"
	cd $(TERRAGRUNT_DIR) && terragrunt apply

destroy: check-tools check-auth check-module ## Destroy infrastructure (use with caution)
	@echo "$(RED)DESTROY INFRASTRUCTURE: $(MODULE)$(RESET)"
	@echo "$(RED)This will permanently delete all resources$(RESET)"
	cd $(TERRAGRUNT_DIR) && terragrunt destroy

output: check-tools check-auth check-module ## Show Terragrunt outputs
	@echo "$(BLUE)Showing outputs for $(MODULE)...$(RESET)"
	cd $(TERRAGRUNT_DIR) && terragrunt output

##@ Utilities

fmt: ## Format Terragrunt/Terraform configuration files
	@echo "$(BLUE)Formatting configuration files...$(RESET)"
	terragrunt hcl fmt --working-dir terragrunt/
	terraform fmt -recursive terraform-modules/

validate-config: check-module init ## Validate Terragrunt configuration
	@echo "$(BLUE)Validating configuration for $(MODULE)...$(RESET)"
	cd $(TERRAGRUNT_DIR) && terragrunt validate

clean-cache: ## Clean Terraform/Terragrunt caches (DRY_RUN=1 to preview)
	@echo "$(BLUE)Cleaning Terraform/Terragrunt caches...$(RESET)"
	@[ "$(DRY_RUN)" = "1" ] && echo "$(YELLOW)DRY RUN ENABLED$(RESET)" || true
	@DIRS=$$(find . -type d \( -name '.terragrunt-cache' -o -name '.terraform' \) 2>/dev/null); \
	if [ -n "$$DIRS" ]; then \
		echo "$(YELLOW)Directories to remove:$(RESET)"; echo "$$DIRS"; \
		if [ "$(DRY_RUN)" != "1" ]; then \
			echo "$$DIRS" | while read -r d; do [ -n "$$d" ] && rm -rf "$$d"; done; \
			echo "$(GREEN)Cache cleanup complete$(RESET)"; \
		fi; \
	else \
		echo "$(GREEN)No cache directories found$(RESET)"; \
	fi

# Default target
.DEFAULT_GOAL := help

# Prevent parallel execution for safety
.NOTPARALLEL:
