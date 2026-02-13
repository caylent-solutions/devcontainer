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
  local container_user="${CONTAINER_USER:?CONTAINER_USER must be set}"
  if is_wsl; then
    # WSL compatibility: Do not use sudo -u in WSL as it fails
    if ! pipx install "${package}"; then
      exit_with_error "Failed to install ${package} with pipx in WSL environment"
    fi
  else
    # Non-WSL: Use sudo -u to ensure correct user environment
    if ! sudo -u "${container_user}" bash -c "export PATH=\"/usr/local/py-utils/bin:/usr/local/python/current/bin:\$PATH\" && pipx install '${package}'"; then
      exit_with_error "Failed to install ${package} with pipx in non-WSL environment"
    fi
  fi
}

is_wsl() {
  uname -r | grep -i microsoft > /dev/null
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

parse_proxy_host_port() {
  # Parse host and port from a proxy URL (e.g., http://host.docker.internal:3128)
  # Sets PROXY_PARSED_HOST and PROXY_PARSED_PORT as global variables
  local proxy_url="${1:?proxy URL must be provided}"

  # Strip protocol prefix (http:// or https://)
  local host_port="${proxy_url#*://}"
  # Strip trailing slash/path
  host_port="${host_port%%/*}"

  if [[ "$host_port" != *:* ]]; then
    exit_with_error "❌ HOST_PROXY_URL '${proxy_url}' does not contain a port (expected format: http://host:port)"
  fi

  PROXY_PARSED_HOST="${host_port%:*}"
  PROXY_PARSED_PORT="${host_port##*:}"

  if [ -z "$PROXY_PARSED_HOST" ] || [ -z "$PROXY_PARSED_PORT" ]; then
    exit_with_error "❌ Failed to parse host/port from HOST_PROXY_URL '${proxy_url}'"
  fi
}

validate_host_proxy() {
  # Validate that the host proxy is reachable using active nc polling (no sleep).
  # Args: proxy_host, proxy_port, timeout_seconds, readme_reference
  local proxy_host="$1"
  local proxy_port="$2"
  local timeout="${3:?timeout must be provided}"
  local readme_ref="$4"

  log_info "Validating host proxy at ${proxy_host}:${proxy_port} (timeout: ${timeout}s)..."

  local elapsed=0
  while [ "$elapsed" -lt "$timeout" ]; do
    if nc -z -w 1 "$proxy_host" "$proxy_port" 2>/dev/null; then
      log_success "Host proxy reachable at ${proxy_host}:${proxy_port}"
      return 0
    fi
    elapsed=$((elapsed + 1))
  done

  exit_with_error "❌ Host proxy not reachable at ${proxy_host}:${proxy_port} after ${timeout}s. See ${readme_ref} for troubleshooting."
}
