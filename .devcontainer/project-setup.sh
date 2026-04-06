#!/usr/bin/env bash

# Project-specific setup script
# This script runs after the main devcontainer setup is complete
# Add your project-specific initialization commands here
#
# Examples:
# - make configure
# - npm install
# - pip install -r requirements.txt
# - docker-compose up -d
# - Initialize databases
# - Download project dependencies
# - Run project-specific configuration

set -euo pipefail


log_info "Running project-specific setup..."

log_info "Configuring development environment..."
if ! make -C "${WORK_DIR}" configure; then
  exit_with_error "❌ Failed to configure development environment"
fi

log_info "Installing Caylent Devcontainer CLI from local source..."
if ! make -C "${WORK_DIR}/caylent-devcontainer-cli" install; then
  exit_with_error "❌ Failed to install Caylent Devcontainer CLI"
fi

log_info "Project-specific setup complete"
