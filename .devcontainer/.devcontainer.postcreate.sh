#!/usr/bin/env bash

set -euo pipefail

WORK_DIR=$(pwd)
CONTAINER_USER=$1
BASH_RC="/home/${CONTAINER_USER}/.bashrc"
ZSH_RC="/home/${CONTAINER_USER}/.zshrc"
WARNINGS=()

# Source shared functions
source "${WORK_DIR}/.devcontainer/devcontainer-functions.sh"

# Ensure .tool-versions file exists with python entry
if [ ! -f "${WORK_DIR}/.tool-versions" ]; then
  log_info "Creating .tool-versions file with Python ${DEFAULT_PYTHON_VERSION}"
  echo "python ${DEFAULT_PYTHON_VERSION}" > "${WORK_DIR}/.tool-versions"
elif ! grep -q "^python " "${WORK_DIR}/.tool-versions"; then
  log_info "Adding Python ${DEFAULT_PYTHON_VERSION} to .tool-versions"
  echo "python ${DEFAULT_PYTHON_VERSION}" >> "${WORK_DIR}/.tool-versions"
fi

# Configure and log CICD environment
CICD_VALUE="${CICD:-false}"
if [ "$CICD_VALUE" = "true" ]; then
  log_info "CICD environment variable: $CICD_VALUE"
  log_info "Devcontainer configured to run in CICD mode (not a local dev environment)"
else
  log_info "CICD environment variable: ${CICD:-not set}"
  log_info "Devcontainer configured to run as a local developer environment"
fi
echo "export CICD=${CICD_VALUE}" >> ${BASH_RC}
echo "export CICD=${CICD_VALUE}" >> ${ZSH_RC}

log_info "Starting post-create setup..."

#########################
# Require Critical Envs #
#########################
if [ -z "${DEFAULT_GIT_BRANCH:-}" ]; then
  exit_with_error "❌ DEFAULT_GIT_BRANCH is not set in the environment"
fi

if [ -z "${DEFAULT_PYTHON_VERSION:-}" ]; then
  exit_with_error "❌ DEFAULT_PYTHON_VERSION is not set in the environment"
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
echo "export PATH=\"${WORK_DIR}/.localscripts:\${PATH}\"" >> ${BASH_RC}
echo "export PATH=\"${WORK_DIR}/.localscripts:\${PATH}\"" >> ${ZSH_RC}

# Configure shell.env sourcing for all shells (interactive and non-interactive)
log_info "Configuring shell.env sourcing for all shells"

# For interactive shells (bash and zsh)
echo "# Source project shell.env" >> ${BASH_RC}
echo "if [ -f \"${WORK_DIR}/shell.env\" ]; then source \"${WORK_DIR}/shell.env\"; fi" >> ${BASH_RC}
echo "# Source project shell.env" >> ${ZSH_RC}
echo "if [ -f \"${WORK_DIR}/shell.env\" ]; then source \"${WORK_DIR}/shell.env\"; fi" >> ${ZSH_RC}

# For non-interactive bash shells via BASH_ENV
echo "export BASH_ENV=\"${WORK_DIR}/shell.env\"" >> ${BASH_RC}
echo "export BASH_ENV=\"${WORK_DIR}/shell.env\"" >> ${ZSH_RC}

# For non-interactive zsh shells via .zshenv
echo "if [ -f \"${WORK_DIR}/shell.env\" ]; then source \"${WORK_DIR}/shell.env\"; fi" > /home/${CONTAINER_USER}/.zshenv

# Handle PAGER configuration by checking shell.env first
SHELL_ENV_PAGER=""
if [ -f "${WORK_DIR}/shell.env" ] && grep -q "^export PAGER=" "${WORK_DIR}/shell.env"; then
  SHELL_ENV_PAGER=$(grep "^export PAGER=" "${WORK_DIR}/shell.env" | cut -d'=' -f2 | tr -d "'\"")
  log_info "PAGER found in shell.env: ${SHELL_ENV_PAGER}"
fi

if [ -n "${SHELL_ENV_PAGER}" ]; then
  PAGER_VALUE="${SHELL_ENV_PAGER}"
  log_info "Using PAGER from shell.env: ${PAGER_VALUE}"
else
  PAGER_VALUE="cat"
  log_info "PAGER not in shell.env, defaulting to: cat"
fi

# Force unset any existing PAGER and set our value
unset PAGER 2>/dev/null || true
export PAGER="${PAGER_VALUE}"
log_info "PAGER configured as: ${PAGER_VALUE}"

# Add to shell profiles with explicit unset first
echo "# PAGER configuration from devcontainer" >> ${BASH_RC}
echo "unset PAGER 2>/dev/null || true" >> ${BASH_RC}
echo "export PAGER=${PAGER_VALUE}" >> ${BASH_RC}
echo "# PAGER configuration from devcontainer" >> ${ZSH_RC}
echo "unset PAGER 2>/dev/null || true" >> ${ZSH_RC}
echo "export PAGER=${PAGER_VALUE}" >> ${ZSH_RC}
if [ "$CICD_VALUE" != "true" ]; then
  echo "export DEVELOPER_NAME=${DEVELOPER_NAME}" >> ${BASH_RC}
  echo "export DEVELOPER_NAME=${DEVELOPER_NAME}" >> ${ZSH_RC}
fi

#################
# Shell Aliases #
#################
log_info "Setting up shell aliases with branch: ${DEFAULT_GIT_BRANCH}"
echo "alias git_sync=\"git pull origin ${DEFAULT_GIT_BRANCH}\"" >> ${BASH_RC}
echo "alias git_sync=\"git pull origin ${DEFAULT_GIT_BRANCH}\"" >> ${ZSH_RC}
echo 'alias git_boop="git reset --soft HEAD~1"' >> ${BASH_RC}
echo 'alias git_boop="git reset --soft HEAD~1"' >> ${ZSH_RC}

##############################
# Install asdf & Tool Versions
##############################
log_info "Installing asdf..."
mkdir -p /home/${CONTAINER_USER}/.asdf
git clone https://github.com/asdf-vm/asdf.git /home/${CONTAINER_USER}/.asdf --branch v0.15.0

# Add asdf to bash
echo '. "$HOME/.asdf/asdf.sh"' >> ${BASH_RC}
echo '. "$HOME/.asdf/completions/asdf.bash"' >> ${BASH_RC}

# Source asdf for the current script
export ASDF_DIR="/home/${CONTAINER_USER}/.asdf"
export ASDF_DATA_DIR="/home/${CONTAINER_USER}/.asdf"
. "/home/${CONTAINER_USER}/.asdf/asdf.sh"

# Make asdf available system-wide for Amazon Q agents
log_info "Configuring system-wide asdf access for Amazon Q agents..."

# Add asdf shims AND bin directory to system-wide PATH via /etc/environment
if uname -r | grep -i microsoft > /dev/null; then
  # WSL compatibility: Use sudo for /etc/environment access
  echo "PATH=\"/home/${CONTAINER_USER}/.asdf/shims:/home/${CONTAINER_USER}/.asdf/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\"" | sudo tee -a /etc/environment > /dev/null
else
  # Non-WSL: Direct write to /etc/environment
  echo "PATH=\"/home/${CONTAINER_USER}/.asdf/shims:/home/${CONTAINER_USER}/.asdf/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\"" >> /etc/environment
fi

# Create system-wide profile for asdf that sets PATH and loads asdf
if uname -r | grep -i microsoft > /dev/null; then
  # WSL compatibility: Use sudo for /etc/profile.d access
  sudo tee /etc/profile.d/asdf.sh > /dev/null << ASDF_PROFILE
#!/bin/bash
# System-wide asdf configuration for Amazon Q agents
export PATH="/home/${CONTAINER_USER}/.asdf/shims:/home/${CONTAINER_USER}/.asdf/bin:\$PATH"
if [ -f "/home/${CONTAINER_USER}/.asdf/asdf.sh" ]; then
    . "/home/${CONTAINER_USER}/.asdf/asdf.sh"
fi
ASDF_PROFILE
  sudo chmod +x /etc/profile.d/asdf.sh
else
  # Non-WSL: Direct write to /etc/profile.d
  cat > /etc/profile.d/asdf.sh << ASDF_PROFILE
#!/bin/bash
# System-wide asdf configuration for Amazon Q agents
export PATH="/home/${CONTAINER_USER}/.asdf/shims:/home/${CONTAINER_USER}/.asdf/bin:\$PATH"
if [ -f "/home/${CONTAINER_USER}/.asdf/asdf.sh" ]; then
    . "/home/${CONTAINER_USER}/.asdf/asdf.sh"
fi
ASDF_PROFILE
  chmod +x /etc/profile.d/asdf.sh
fi

# Also add to /etc/bash.bashrc for non-login shells
if uname -r | grep -i microsoft > /dev/null; then
  # WSL compatibility: Use sudo for /etc/bash.bashrc access
  echo '# Load asdf for Amazon Q agents' | sudo tee -a /etc/bash.bashrc > /dev/null
  echo "export PATH=\"/home/${CONTAINER_USER}/.asdf/shims:/home/${CONTAINER_USER}/.asdf/bin:\$PATH\"" | sudo tee -a /etc/bash.bashrc > /dev/null
  echo "if [ -f \"/home/${CONTAINER_USER}/.asdf/asdf.sh\" ]; then . \"/home/${CONTAINER_USER}/.asdf/asdf.sh\"; fi" | sudo tee -a /etc/bash.bashrc > /dev/null
else
  # Non-WSL: Direct write to /etc/bash.bashrc
  echo '# Load asdf for Amazon Q agents' >> /etc/bash.bashrc
  echo "export PATH=\"/home/${CONTAINER_USER}/.asdf/shims:/home/${CONTAINER_USER}/.asdf/bin:\$PATH\"" >> /etc/bash.bashrc
  echo "if [ -f \"/home/${CONTAINER_USER}/.asdf/asdf.sh\" ]; then . \"/home/${CONTAINER_USER}/.asdf/asdf.sh\"; fi" >> /etc/bash.bashrc
fi

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

# asdf version manager (must be after oh-my-zsh)
. "$HOME/.asdf/asdf.sh"
# append completions to fpath
fpath=(${ASDF_DIR}/completions $fpath)
# initialise completions with ZSH's compinit
autoload -Uz compinit && compinit
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
    echo "export AWS_DEFAULT_OUTPUT=${AWS_OUTPUT_FORMAT}" >> ${BASH_RC}
    echo "export AWS_DEFAULT_OUTPUT=${AWS_OUTPUT_FORMAT}" >> ${ZSH_RC}
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
sudo apt-get update
sudo apt-get install -y curl vim git gh jq yq nmap sipcalc wget unzip zip

# Install Python build dependencies for asdf Python compilation
log_info "Installing Python build dependencies..."
sudo apt-get install -y \
  build-essential \
  libbz2-dev \
  libffi-dev \
  libncurses5-dev \
  libncursesw5-dev \
  libreadline-dev \
  libsqlite3-dev \
  libssl-dev \
  liblzma-dev \
  tk-dev \
  uuid-dev \
  zlib1g-dev

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
    log_info "Installing asdf plugin: $plugin"
    install_asdf_plugin "$plugin"
  done

  # Install Python first (always required for other tools)
  if grep -q "^python " "${WORK_DIR}/.tool-versions"; then
    PYTHON_VERSION=$(grep "^python " "${WORK_DIR}/.tool-versions" | cut -d' ' -f2)
    log_info "Installing Python ${PYTHON_VERSION} first (from .tool-versions, required for other tools)..."
  else
    PYTHON_VERSION="${DEFAULT_PYTHON_VERSION}"
    log_info "Installing Python ${PYTHON_VERSION} first (fallback version, required for other tools)..."
  fi

  if ! asdf install python "$PYTHON_VERSION"; then
    exit_with_error "❌ Failed to install python $PYTHON_VERSION"
  fi
  if ! asdf reshim python; then
    exit_with_error "❌ Failed to reshim python after installation"
  fi

  log_info "Installing remaining tools from .tool-versions..."
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

# Create symlinks in /usr/local/bin for direct access by Amazon Q agents
log_info "Creating symlinks for Amazon Q agent direct access..."
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

# Install pipx right after Python is available
log_info "Installing pipx..."
python -m pip install --upgrade pip --root-user-action=ignore
python -m pip install pipx --root-user-action=ignore
if ! asdf reshim python; then
  exit_with_error "❌ asdf reshim python failed after pipx install"
fi

# Install Caylent Devcontainer CLI
log_info "Installing Caylent Devcontainer CLI..."
if [ -n "${CLI_VERSION:-}" ] && [[ "${CLI_VERSION}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  log_info "Installing specific CLI version: ${CLI_VERSION}"
  CLI_INSTALL_CMD="caylent-devcontainer-cli==${CLI_VERSION}"
else
  log_info "Installing latest CLI version"
  CLI_INSTALL_CMD="caylent-devcontainer-cli"
fi

if uname -r | grep -i microsoft > /dev/null; then
  # WSL compatibility: Do not use sudo -u in WSL as it fails
  python -m pipx install "${CLI_INSTALL_CMD}"
else
  # Non-WSL: Use sudo -u to ensure correct user environment
  sudo -u ${CONTAINER_USER} bash -c "export PATH=\"\$PATH:/home/${CONTAINER_USER}/.local/bin\" && source /home/${CONTAINER_USER}/.asdf/asdf.sh && python -m pipx install '${CLI_INSTALL_CMD}'"
fi

# Verify asdf is working properly
log_info "Verifying asdf installation..."
if ! asdf current; then
  exit_with_error "❌ asdf current failed - installation may be incomplete"
fi

#################
# Python Tools  #
#################
log_info "Verifying Python installation via asdf..."
ASDF_PYTHON_PATH=$(asdf which python || true)
if [[ -z "$ASDF_PYTHON_PATH" || "$ASDF_PYTHON_PATH" != *".asdf"* ]]; then
  exit_with_error "❌ 'python' is not provided by asdf. Found: $ASDF_PYTHON_PATH"
fi

# Ensure pipx binaries are available in PATH
log_info "Configuring pipx PATH..."
echo "export PATH=\"\$PATH:/home/${CONTAINER_USER}/.local/bin\"" >> ${BASH_RC}
echo "export PATH=\"\$PATH:/home/${CONTAINER_USER}/.local/bin\"" >> ${ZSH_RC}

log_info "Installing Python packages..."
python -m pip install ruamel_yaml --root-user-action=ignore

#############
# AWS Tools #
#############
log_info "Installing AWS CLI..."
if uname -r | grep -i microsoft > /dev/null; then
  # WSL compatibility: Do not use sudo -u in WSL as it fails
  python -m pipx install awscli
else
  # Non-WSL: Use sudo -u to ensure correct user environment
  sudo -u ${CONTAINER_USER} bash -c "export PATH=\"\$PATH:/home/${CONTAINER_USER}/.local/bin\" && source /home/${CONTAINER_USER}/.asdf/asdf.sh && python -m pipx install awscli"
fi

log_info "Installing AWS SSO utilities..."
if uname -r | grep -i microsoft > /dev/null; then
  # WSL compatibility: Do not use sudo -u in WSL as it fails
  python -m pipx install aws-sso-util
else
  # Non-WSL: Use sudo -u to ensure correct user environment
  sudo -u ${CONTAINER_USER} bash -c "export PATH=\"\$PATH:/home/${CONTAINER_USER}/.local/bin\" && source /home/${CONTAINER_USER}/.asdf/asdf.sh && python -m pipx install aws-sso-util"
fi

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

  # Unset GIT_EDITOR to ensure vim is used
  echo "unset GIT_EDITOR" >> ${BASH_RC}
  echo "unset GIT_EDITOR" >> ${ZSH_RC}

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
