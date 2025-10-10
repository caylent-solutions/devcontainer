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

install_with_pipx() {
  local package="$1"
  if uname -r | grep -i microsoft > /dev/null; then
    # WSL compatibility: Do not use sudo -u in WSL as it fails
    python -m pipx install "${package}"
  else
    # Non-WSL: Use sudo -u to ensure correct user environment
    sudo -u ${CONTAINER_USER} bash -c "export PATH=\"\$PATH:/home/${CONTAINER_USER}/.local/bin\" && source /home/${CONTAINER_USER}/.asdf/asdf.sh && python -m pipx install '${package}'"
  fi
}

is_wsl() {
  uname -r | grep -i microsoft > /dev/null
}

add_to_shell_profiles() {
  local content="$1"
  echo "$content" >> ${BASH_RC}
  echo "$content" >> ${ZSH_RC}
}

write_file_with_wsl_compat() {
  local file_path="$1"
  local content="$2"
  local permissions="${3:-}"

  if is_wsl; then
    echo "$content" | sudo tee "$file_path" > /dev/null
    if [ -n "$permissions" ]; then
      sudo chmod "$permissions" "$file_path"
    fi
  else
    echo "$content" > "$file_path"
    if [ -n "$permissions" ]; then
      chmod "$permissions" "$file_path"
    fi
  fi
}

append_to_file_with_wsl_compat() {
  local file_path="$1"
  local content="$2"

  if is_wsl; then
    echo "$content" | sudo tee -a "$file_path" > /dev/null
  else
    echo "$content" >> "$file_path"
  fi
}
