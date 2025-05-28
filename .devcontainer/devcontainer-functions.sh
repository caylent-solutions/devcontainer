#!/usr/bin/env bash

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() {
  echo -e "${CYAN}[INFO]${NC} $1"
}

log_success() {
  echo -e "${GREEN}[DONE]${NC} $1"
}

log_warn() {
  echo -e "${YELLOW}[WARN]${NC} $1"
  WARNINGS+=("$1")
}

log_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

exit_with_error() {
  log_error "$1"
  exit 1
}

asdf_plugin_installed() {
  asdf plugin list | grep -q "^$1$"
}

install_asdf_plugin() {
  local plugin=$1
  if asdf_plugin_installed "$plugin"; then
    log_info "Plugin '${plugin}' already installed"
  else
    log_info "Installing asdf plugin: ${plugin}"
    if ! asdf plugin add "${plugin}"; then
      log_warn "❌ Failed to add asdf plugin: ${plugin}"
      return 1
    fi
  fi
}
