#!/usr/bin/env bash

set -euo pipefail

WORK_DIR=$(pwd)
CONTAINER_USER=$1
BASH_RC="/home/${CONTAINER_USER}/.bashrc"
ZSH_RC="/home/${CONTAINER_USER}/.zshrc"
WARNINGS=()

# Source shared functions
source "${WORK_DIR}/.devcontainer/devcontainer-functions.sh"

# Configure and log CICD environment
CICD_VALUE="${CICD:-false}"
if [ "$CICD_VALUE" = "true" ]; then
  log_info "CICD environment variable: $CICD_VALUE"
  log_info "Devcontainer configured to run in CICD mode (not a local dev environment)"
else
  log_info "CICD environment variable: ${CICD:-not set}"
  log_info "Devcontainer configured to run as a local developer environment"
fi

log_info "Starting post-create setup..."

############################
# Create Python Symlink    #
############################
if ! command -v python &> /dev/null; then
  log_info "Creating python symlink to python3"
  sudo ln -sf /usr/bin/python3 /usr/bin/python
fi

# Add Python tools to PATH for script execution
export PATH="/usr/local/py-utils/bin:/usr/local/python/current/bin:$HOME/.local/bin:$PATH"

#########################
# Require Critical Envs #
#########################
if [ -z "${DEFAULT_GIT_BRANCH:-}" ]; then
  exit_with_error "❌ DEFAULT_GIT_BRANCH is not set in the environment"
fi

if [ "$CICD_VALUE" != "true" ]; then
  AWS_CONFIG_ENABLED="${AWS_CONFIG_ENABLED:-true}"
  AWS_PROFILE_MAP_FILE="${WORK_DIR}/.devcontainer/aws-profile-map.json"

  if [ "${AWS_CONFIG_ENABLED,,}" = "true" ]; then
    if [ ! -f "$AWS_PROFILE_MAP_FILE" ]; then
      exit_with_error "❌ Missing AWS profile config: $AWS_PROFILE_MAP_FILE (required when AWS_CONFIG_ENABLED=true)"
    fi

    AWS_PROFILE_MAP_JSON=$(<"$AWS_PROFILE_MAP_FILE")

    if ! jq empty <<< "$AWS_PROFILE_MAP_JSON" >/dev/null 2>&1; then
      log_error "$AWS_PROFILE_MAP_JSON"
      exit_with_error "❌ AWS_PROFILE_MAP_JSON is not valid JSON"
    fi
  else
    log_info "AWS configuration disabled (AWS_CONFIG_ENABLED=${AWS_CONFIG_ENABLED})"
  fi
else
  log_info "CICD mode enabled - skipping AWS configuration validation"
fi

#################
# Configure ENV #
#################
log_info "Configuring ENV vars..."

# Configure shell.env sourcing for all shells (interactive and non-interactive)
log_info "Configuring shell.env sourcing for all shells"

# Verify shell.env exists before configuring shells
if [ ! -f "${WORK_DIR}/shell.env" ]; then
  exit_with_error "❌ shell.env not found at ${WORK_DIR}/shell.env"
fi

# For bash: source in .bashrc (interactive) and via BASH_ENV (non-interactive)
echo "# Source project shell.env" >> "${BASH_RC}"
echo "source \"${WORK_DIR}/shell.env\"" >> "${BASH_RC}"
echo "export BASH_ENV=\"${WORK_DIR}/shell.env\"" >> "${BASH_RC}"
echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "${BASH_RC}"
echo "alias python=python3" >> "${BASH_RC}"
echo "alias pip=pip3" >> "${BASH_RC}"

# For zsh: source in .zshenv (covers all zsh shells - interactive and non-interactive)
echo "source \"${WORK_DIR}/shell.env\"" > /home/${CONTAINER_USER}/.zshenv
echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> /home/${CONTAINER_USER}/.zshenv
echo "alias python=python3" >> /home/${CONTAINER_USER}/.zshenv
echo "alias pip=pip3" >> /home/${CONTAINER_USER}/.zshenv

##############################
# Install asdf & Tool Versions
##############################
log_info "Installing asdf..."
mkdir -p /home/${CONTAINER_USER}/.asdf
git clone https://github.com/asdf-vm/asdf.git /home/${CONTAINER_USER}/.asdf --branch v0.15.0

# Source asdf for the current script
export ASDF_DIR="/home/${CONTAINER_USER}/.asdf"
export ASDF_DATA_DIR="/home/${CONTAINER_USER}/.asdf"
. "/home/${CONTAINER_USER}/.asdf/asdf.sh"

# Make asdf available system-wide for AI agents
log_info "Configuring system-wide asdf access for AI agents..."

# Create plugins directory if it doesn't exist
mkdir -p /home/${CONTAINER_USER}/.asdf/plugins

# Create wrapper scripts for asdf tools in /usr/local/bin for direct access
log_info "Creating asdf wrapper scripts for direct access..."

# Create asdf wrapper script
if uname -r | grep -i microsoft > /dev/null; then
  # WSL compatibility: Use sudo for /usr/local/bin access
  sudo tee /usr/local/bin/asdf > /dev/null << ASDF_WRAPPER
#!/bin/bash
# Wrapper script for asdf that ensures proper environment
export ASDF_DIR="/home/${CONTAINER_USER}/.asdf"
export ASDF_DATA_DIR="/home/${CONTAINER_USER}/.asdf"
if [ -f "/home/${CONTAINER_USER}/.asdf/asdf.sh" ]; then
    . "/home/${CONTAINER_USER}/.asdf/asdf.sh"
fi
exec /home/${CONTAINER_USER}/.asdf/bin/asdf "\$@"
ASDF_WRAPPER
  sudo chmod +x /usr/local/bin/asdf
else
  # Non-WSL: Direct write to /usr/local/bin
  cat > /usr/local/bin/asdf << ASDF_WRAPPER
#!/bin/bash
# Wrapper script for asdf that ensures proper environment
export ASDF_DIR="/home/${CONTAINER_USER}/.asdf"
export ASDF_DATA_DIR="/home/${CONTAINER_USER}/.asdf"
if [ -f "/home/${CONTAINER_USER}/.asdf/asdf.sh" ]; then
    . "/home/${CONTAINER_USER}/.asdf/asdf.sh"
fi
exec /home/${CONTAINER_USER}/.asdf/bin/asdf "\$@"
ASDF_WRAPPER
  chmod +x /usr/local/bin/asdf
fi

# Create pip wrapper script that sources asdf environment
if uname -r | grep -i microsoft > /dev/null; then
  # WSL compatibility: Use sudo for /usr/local/bin access
  sudo tee /usr/local/bin/pip-asdf > /dev/null << PIP_WRAPPER
#!/bin/bash
# Wrapper script for pip that ensures asdf environment is loaded
export ASDF_DIR="/home/${CONTAINER_USER}/.asdf"
export ASDF_DATA_DIR="/home/${CONTAINER_USER}/.asdf"
if [ -f "/home/${CONTAINER_USER}/.asdf/asdf.sh" ]; then
    . "/home/${CONTAINER_USER}/.asdf/asdf.sh"
fi
exec /home/${CONTAINER_USER}/.asdf/shims/pip "\$@"
PIP_WRAPPER
  sudo chmod +x /usr/local/bin/pip-asdf
else
  # Non-WSL: Direct write to /usr/local/bin
  cat > /usr/local/bin/pip-asdf << PIP_WRAPPER
#!/bin/bash
# Wrapper script for pip that ensures asdf environment is loaded
export ASDF_DIR="/home/${CONTAINER_USER}/.asdf"
export ASDF_DATA_DIR="/home/${CONTAINER_USER}/.asdf"
if [ -f "/home/${CONTAINER_USER}/.asdf/asdf.sh" ]; then
    . "/home/${CONTAINER_USER}/.asdf/asdf.sh"
fi
exec /home/${CONTAINER_USER}/.asdf/shims/pip "\$@"
PIP_WRAPPER
  chmod +x /usr/local/bin/pip-asdf
fi

#################
# Oh My Zsh     #
#################
if [ ! -d "/home/${CONTAINER_USER}/.oh-my-zsh" ]; then
  log_info "Installing Oh My Zsh..."
  sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
else
  log_info "Oh My Zsh already installed — skipping"
fi

cat <<'EOF' >> ${ZSH_RC}
export ZSH="$HOME/.oh-my-zsh"
ZSH_THEME="obraun"
ENABLE_CORRECTION="false"
HIST_STAMPS="%m/%d/%Y - %H:%M:%S"
source $ZSH/oh-my-zsh.sh
EOF

#################
# Configure AWS #
#################
if [ "$CICD_VALUE" != "true" ]; then
  if [ "${AWS_CONFIG_ENABLED,,}" = "true" ]; then
    log_info "Configuring AWS profiles..."
    mkdir -p /home/${CONTAINER_USER}/.aws
    mkdir -p /home/${CONTAINER_USER}/.aws/amazonq/cache
    chown -R ${CONTAINER_USER}:${CONTAINER_USER} /home/${CONTAINER_USER}/.aws/amazonq

    AWS_OUTPUT_FORMAT="${AWS_DEFAULT_OUTPUT:-json}"
    jq -r 'to_entries[] |
      "[profile \(.key)]\n" +
      "sso_start_url = \(.value.sso_start_url)\n" +
      "sso_region = \(.value.sso_region)\n" +
      "sso_account_name = \(.value.account_name)\n" +
      "sso_account_id = \(.value.account_id)\n" +
      "sso_role_name = \(.value.role_name)\n" +
      "region = \(.value.region)\n" +
      "output = '"$AWS_OUTPUT_FORMAT"'\n" +
      "sso_auto_populated = true\n"' <<< "$AWS_PROFILE_MAP_JSON" \
      > /home/${CONTAINER_USER}/.aws/config
  else
    log_info "Skipping AWS profile configuration (AWS_CONFIG_ENABLED=${AWS_CONFIG_ENABLED})"
  fi
else
  log_info "CICD mode enabled - skipping AWS profile configuration"
fi

#####################
# Install Base Tools
#####################
log_info "Installing core packages..."
sudo apt-get update -qq
sudo apt-get install -y -qq curl vim git gh jq yq nmap sipcalc wget unzip zip netcat-openbsd

##############################
# Install Optional Extra Tools
##############################
if [ -n "${EXTRA_APT_PACKAGES:-}" ]; then
  log_info "Installing extra packages: ${EXTRA_APT_PACKAGES}"
  sudo apt-get install -y ${EXTRA_APT_PACKAGES}
fi

if [ -f "${WORK_DIR}/.tool-versions" ]; then
  log_info "Installing asdf plugins from .tool-versions..."
  cut -d' ' -f1 "${WORK_DIR}/.tool-versions" | while read -r plugin; do
    install_asdf_plugin "$plugin"
  done

  log_info "Installing tools from .tool-versions..."
  if ! asdf install; then
    log_warn "❌ asdf install failed — tool versions may not be fully installed"
  fi
else
  log_info "No .tool-versions file found — skipping general asdf install"
fi

# Ensure reshim is run for the current user
log_info "Running asdf reshim..."
if ! asdf reshim; then
  exit_with_error "❌ asdf reshim failed"
fi

# Create symlinks in /usr/local/bin for direct access by AI agents
log_info "Creating symlinks for AI agent direct access..."
if [ -d "/home/${CONTAINER_USER}/.asdf/shims" ]; then
  for shim in /home/${CONTAINER_USER}/.asdf/shims/*; do
    if [ -f "$shim" ] && [ -x "$shim" ]; then
      shim_name=$(basename "$shim")
      if [ ! -e "/usr/local/bin/$shim_name" ]; then
        if uname -r | grep -i microsoft > /dev/null; then
          # WSL compatibility: Use sudo for /usr/local/bin access
          sudo ln -s "$shim" "/usr/local/bin/$shim_name"
        else
          # Non-WSL: Direct symlink creation
          ln -s "$shim" "/usr/local/bin/$shim_name"
        fi
        log_info "Created symlink: /usr/local/bin/$shim_name -> $shim"
      fi
    fi
  done
fi

# Install Caylent Devcontainer CLI
log_info "Installing Caylent Devcontainer CLI..."
if [ -n "${CLI_VERSION:-}" ]; then
  if [[ "${CLI_VERSION}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    log_info "Installing specific CLI version: ${CLI_VERSION}"
    CLI_INSTALL_CMD="caylent-devcontainer-cli==${CLI_VERSION}"
  else
    exit_with_error "Invalid CLI_VERSION format: ${CLI_VERSION}. Expected format: X.Y.Z (e.g., 1.2.3)"
  fi
else
  log_info "Installing latest CLI version"
  CLI_INSTALL_CMD="caylent-devcontainer-cli"
fi

install_with_pipx "${CLI_INSTALL_CMD}"

# Verify asdf is working properly
log_info "Verifying asdf installation..."
if ! asdf current; then
  exit_with_error "❌ asdf current failed - installation may be incomplete"
fi

##############
# Host Proxy #
##############
# Proxy environment variables are set in devcontainer.json containerEnv
# This section only validates that host proxy is accessible

if [ "${HOST_PROXY:-false}" = "true" ]; then
  # *nix Family OS Host Proxy Validation #
  if [ -S /run/host-services/ssh-auth.sock ] || ! uname -r | grep -qi microsoft; then
    log_info "Validating host tinyproxy accessibility..."
    log_info "Checking if host proxy is reachable at host.docker.internal:3128..."
    HOST_PROXY_TIMEOUT=10
    HOST_PROXY_ELAPSED=0
    while ! nc -z host.docker.internal 3128 2>/dev/null; do
      if [ $HOST_PROXY_ELAPSED -ge $HOST_PROXY_TIMEOUT ]; then
        log_error "❌ Cannot reach host proxy at host.docker.internal:3128"
        log_error "Please ensure tinyproxy is running on your host with:"
        log_error "  tinyproxy -c <path-to-tinyproxy.conf>"
        log_error "See .devcontainer/nix-family-os/README.md for setup instructions"
        exit_with_error "❌ Host proxy not accessible - devcontainer build cannot continue"
      fi
      sleep 1
      HOST_PROXY_ELAPSED=$((HOST_PROXY_ELAPSED + 1))
    done
    log_success "Host tinyproxy is accessible at host.docker.internal:3128"
  # Windows Host Proxy Validation#
  elif uname -r | grep -qi microsoft; then
    log_warn "Windows host detected - Windows host proxy validation not yet supported"
  fi
else
  log_warn "Host proxy not enabled (HOST_PROXY=${HOST_PROXY:-false}) - skipping validation"
fi

#############
# AWS Tools #
#############
log_info "Installing AWS SSO utilities..."
install_with_pipx "aws-sso-util"

###################
# Claude Code CLI #
###################
log_info "Installing Claude Code CLI..."

# Download install script first to ensure it succeeds before piping to bash
CLAUDE_INSTALL_SCRIPT="/tmp/claude-install-${RANDOM}.sh"

if ! sudo -u "${CONTAINER_USER}" curl -fsSL https://claude.ai/install.sh -o "${CLAUDE_INSTALL_SCRIPT}"; then
  exit_with_error "❌ Failed to download Claude Code install script from https://claude.ai/install.sh - check network connectivity and proxy settings"
fi

# Verify script was downloaded and is not empty
if [ ! -s "${CLAUDE_INSTALL_SCRIPT}" ]; then
  exit_with_error "❌ Claude Code install script is empty or missing at ${CLAUDE_INSTALL_SCRIPT}"
fi

# Execute install script
log_info "Executing Claude Code install script..."
if uname -r | grep -i microsoft > /dev/null; then
  # WSL compatibility: Run directly without sudo -u
  if ! PATH="/home/${CONTAINER_USER}/.local/bin:$PATH" bash "${CLAUDE_INSTALL_SCRIPT}"; then
    rm -f "${CLAUDE_INSTALL_SCRIPT}"
    exit_with_error "❌ Failed to execute Claude Code install script"
  fi
else
  # Non-WSL: Install as container user
  if ! sudo -u "${CONTAINER_USER}" PATH="/home/${CONTAINER_USER}/.local/bin:$PATH" bash "${CLAUDE_INSTALL_SCRIPT}"; then
    rm -f "${CLAUDE_INSTALL_SCRIPT}"
    exit_with_error "❌ Failed to execute Claude Code install script"
  fi
fi

# Clean up install script
rm -f "${CLAUDE_INSTALL_SCRIPT}"

log_info "Verifying Claude Code CLI installation..."
CLAUDE_BIN="/home/${CONTAINER_USER}/.local/bin/claude"
if [ ! -f "$CLAUDE_BIN" ]; then
  exit_with_error "❌ Claude Code binary not found at expected location: $CLAUDE_BIN"
fi

if [ ! -x "$CLAUDE_BIN" ]; then
  exit_with_error "❌ Claude Code binary exists but is not executable: $CLAUDE_BIN"
fi

CLAUDE_VERSION=$(sudo -u "${CONTAINER_USER}" "${CLAUDE_BIN}" --version 2>&1 || echo "unknown")
log_success "Claude Code CLI installed successfully: ${CLAUDE_VERSION}"

#################
# Configure Git #
#################
if [ "$CICD_VALUE" != "true" ]; then
  log_info "Setting up Git credentials..."
  cat <<EOF > /home/${CONTAINER_USER}/.netrc
machine ${GIT_PROVIDER_URL}
login ${GIT_USER}
password ${GIT_TOKEN}
EOF
  chmod 600 /home/${CONTAINER_USER}/.netrc

  cat <<EOF >> /home/${CONTAINER_USER}/.gitconfig
[user]
    name = ${GIT_USER}
    email = ${GIT_USER_EMAIL}
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
[credential]
    helper = store
EOF
else
  log_info "CICD mode enabled - skipping Git configuration"
fi

###########
# Cleanup #
###########
log_info "Fixing ownership for ${CONTAINER_USER}"
chown -R ${CONTAINER_USER}:${CONTAINER_USER} /home/${CONTAINER_USER}

####################
# Warning Summary  #
####################
if [ ${#WARNINGS[@]} -ne 0 ]; then
  echo -e "\n⚠️  Completed with warnings:"
  for warning in "${WARNINGS[@]}"; do
    echo "  - $warning"
  done
else
  log_success "Dev container setup completed with no warnings"
fi

#########################
# Project-Specific Setup #
#########################
log_info "Running project-specific setup script..."
if [ -f "${WORK_DIR}/.devcontainer/project-setup.sh" ]; then
  if uname -r | grep -i microsoft > /dev/null; then
    # WSL compatibility: Run directly without sudo -u
    bash -c "source /home/${CONTAINER_USER}/.asdf/asdf.sh && cd '${WORK_DIR}' && bash '${WORK_DIR}/.devcontainer/project-setup.sh'"
  else
    # Non-WSL: Use sudo -u to run as container user
    sudo -u "${CONTAINER_USER}" bash -c "source /home/${CONTAINER_USER}/.asdf/asdf.sh && cd '${WORK_DIR}' && bash '${WORK_DIR}/.devcontainer/project-setup.sh'"
  fi
else
  log_warn "No project-specific setup script found at ${WORK_DIR}/.devcontainer/project-setup.sh"
  WARNINGS+=("No project-specific setup script found at ${WORK_DIR}/.devcontainer/project-setup.sh")
fi

exit 0
