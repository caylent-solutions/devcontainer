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

configure_apt_proxy() {
  # Configure apt to use proxy from environment variables.
  # Writes /etc/apt/apt.conf.d/99proxy if HTTP_PROXY or http_proxy is set.
  # Adds per-host DIRECT overrides from NO_PROXY because apt ignores that
  # environment variable and requires Acquire::http::Proxy::host "DIRECT" syntax.
  local apt_proxy_conf="/etc/apt/apt.conf.d/99proxy"
  local proxy_url="${HTTP_PROXY:-${http_proxy:-}}"

  if [ -z "${proxy_url}" ]; then
    log_info "No proxy configured for apt (HTTP_PROXY not set)"
    return 0
  fi

  local https_proxy_url="${HTTPS_PROXY:-${https_proxy:-${proxy_url}}}"

  log_info "Configuring apt proxy: http=${proxy_url} https=${https_proxy_url}"

  cat > "${apt_proxy_conf}" <<APT_PROXY_EOF
Acquire::http::Proxy "${proxy_url}";
Acquire::https::Proxy "${https_proxy_url}";
APT_PROXY_EOF

  # apt ignores NO_PROXY — add per-host DIRECT overrides for domain entries
  local no_proxy_val="${NO_PROXY:-${no_proxy:-}}"
  if [ -n "${no_proxy_val}" ]; then
    local _old_ifs="${IFS}"
    IFS=','
    for _entry in ${no_proxy_val}; do
      IFS="${_old_ifs}"
      _entry=$(echo "${_entry}" | tr -d ' ')
      # Add DIRECT for FQDN entries (start with letter, contain a dot)
      case "${_entry}" in
        [a-zA-Z]*.*)
          echo "Acquire::http::Proxy::${_entry} \"DIRECT\";" >> "${apt_proxy_conf}"
          echo "Acquire::https::Proxy::${_entry} \"DIRECT\";" >> "${apt_proxy_conf}"
          ;;
      esac
    done
    IFS="${_old_ifs}"
  fi

  log_success "Wrote apt proxy configuration to ${apt_proxy_conf}"
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

configure_git_shared() {
  # Write shared .gitconfig entries used by both token and SSH auth methods.
  # Args: container_user, git_user, git_user_email
  local container_user="$1"
  local git_user="${2:?GIT_USER must be set}"
  local git_user_email="${3:?GIT_USER_EMAIL must be set}"
  local gitconfig="/home/${container_user}/.gitconfig"

  cat <<EOF >> "${gitconfig}"
[user]
    name = ${git_user}
    email = ${git_user_email}
[core]
    editor = vim
[push]
    autoSetupRemote = true
[safe]
    directory = *
[pager]
    branch = false
    config = false
    diff = false
    log = false
    show = false
    status = false
    tag = false
EOF
}

configure_git_token() {
  # Configure git authentication using token method (.netrc + credential helper).
  # Args: container_user, git_provider_url, git_user, git_token
  local container_user="$1"
  local git_provider_url="${2:?GIT_PROVIDER_URL must be set}"
  local git_user="${3:?GIT_USER must be set}"
  local git_token="${4:?GIT_TOKEN must be set}"
  local netrc="/home/${container_user}/.netrc"
  local gitconfig="/home/${container_user}/.gitconfig"

  log_info "Configuring git token authentication..."

  cat <<EOF > "${netrc}"
machine ${git_provider_url}
login ${git_user}
password ${git_token}
EOF
  chmod 600 "${netrc}"

  cat <<EOF >> "${gitconfig}"
[credential]
    helper = store
EOF

  log_success "Git token authentication configured"
}

configure_git_ssh() {
  # Configure git authentication using SSH method.
  # Args: container_user, git_provider_url, work_dir
  local container_user="$1"
  local git_provider_url="${2:?GIT_PROVIDER_URL must be set}"
  local work_dir="${3:?WORK_DIR must be set}"
  local ssh_dir="/home/${container_user}/.ssh"
  local ssh_key_source="${work_dir}/.devcontainer/ssh-private-key"
  local ssh_key_dest="${ssh_dir}/id_private_key"

  log_info "Configuring git SSH authentication..."

  # Ensure openssh-client is installed
  if ! command -v ssh &> /dev/null; then
    log_info "Installing openssh-client..."
    sudo apt-get install -y -qq openssh-client
  fi

  # Create .ssh directory
  mkdir -p "${ssh_dir}"
  chmod 700 "${ssh_dir}"

  # Copy SSH private key
  if [ ! -f "${ssh_key_source}" ]; then
    exit_with_error "❌ SSH private key not found at ${ssh_key_source}. Ensure ssh-private-key exists in .devcontainer/"
  fi
  cp "${ssh_key_source}" "${ssh_key_dest}"
  chmod 600 "${ssh_key_dest}"

  # Run ssh-keyscan to add host to known_hosts
  log_info "Running ssh-keyscan for ${git_provider_url}..."
  if ! ssh-keyscan "${git_provider_url}" >> "${ssh_dir}/known_hosts" 2>/dev/null; then
    exit_with_error "❌ ssh-keyscan failed for ${git_provider_url}"
  fi
  chmod 600 "${ssh_dir}/known_hosts"

  # Create SSH config
  cat <<EOF > "${ssh_dir}/config"
Host ${git_provider_url}
    HostName ${git_provider_url}
    User git
    IdentityFile ${ssh_key_dest}
    IdentitiesOnly yes
EOF
  chmod 600 "${ssh_dir}/config"

  # Fix ownership
  chown -R "${container_user}:${container_user}" "${ssh_dir}"

  # Verify SSH connectivity
  # Note: ssh -T returns exit code 1 on GitHub (no shell access) even on success,
  # so we check output for permission denied rather than exit code.
  log_info "Verifying SSH connectivity to ${git_provider_url}..."
  local ssh_output
  ssh_output=$(sudo -u "${container_user}" ssh -T "git@${git_provider_url}" -o BatchMode=yes -o StrictHostKeyChecking=no 2>&1 || true)

  if echo "${ssh_output}" | grep -qi "permission denied\|publickey.*denied"; then
    exit_with_error "❌ SSH connectivity test failed for git@${git_provider_url}: ${ssh_output}"
  fi
  log_info "SSH connectivity response: ${ssh_output}"

  log_success "Git SSH authentication configured"
}
