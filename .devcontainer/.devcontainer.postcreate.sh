#!/usr/bin/env bash

set -euo pipefail

WORK_DIR=$(pwd)
CONTAINER_USER=$1
BASH_RC="/home/${CONTAINER_USER}/.bashrc"
ZSH_RC="/home/${CONTAINER_USER}/.zshrc"
WARNINGS=()

# Source shared functions
source "${WORK_DIR}/.devcontainer/devcontainer-functions.sh"

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

#################
# Configure ENV #
#################
log_info "Configuring ENV vars..."
echo "export PATH=\"${WORK_DIR}/.localscripts:\${PATH}\"" >> ${BASH_RC}
echo "export PATH=\"${WORK_DIR}/.localscripts:\${PATH}\"" >> ${ZSH_RC}
echo "export DEVELOPER_NAME=${DEVELOPER_NAME}" >> ${BASH_RC}
echo "export DEVELOPER_NAME=${DEVELOPER_NAME}" >> ${ZSH_RC}

#################
# Shell Aliases #
#################
log_info "Setting up shell aliases with branch: ${DEFAULT_GIT_BRANCH}"
echo "alias git_sync=\"git pull origin ${DEFAULT_GIT_BRANCH}\"" >> ${BASH_RC}
echo "alias git_sync=\"git pull origin ${DEFAULT_GIT_BRANCH}\"" >> ${ZSH_RC}
echo 'alias git_boop="git reset --soft HEAD~1"' >> ${BASH_RC}
echo 'alias git_boop="git reset --soft HEAD~1"' >> ${ZSH_RC}

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
if [ "${AWS_CONFIG_ENABLED,,}" = "true" ]; then
  log_info "Configuring AWS profiles..."
  mkdir -p /home/${CONTAINER_USER}/.aws
  mkdir -p /home/${CONTAINER_USER}/.aws/amazonq/cache
  chown -R ${CONTAINER_USER}:${CONTAINER_USER} /home/${CONTAINER_USER}/.aws/amazonq

  jq -r 'to_entries[] |
    "[profile \(.key)]\n" +
    "sso_start_url = \(.value.sso_start_url)\n" +
    "sso_region = \(.value.sso_region)\n" +
    "sso_account_name = \(.value.account_name)\n" +
    "sso_account_id = \(.value.account_id)\n" +
    "sso_role_name = \(.value.role_name)\n" +
    "region = \(.value.region)\n" +
    "sso_auto_populated = true\n"' <<< "$AWS_PROFILE_MAP_JSON" \
    > /home/${CONTAINER_USER}/.aws/config
else
  log_info "Skipping AWS profile configuration (AWS_CONFIG_ENABLED=${AWS_CONFIG_ENABLED})"
fi

#####################
# Install Base Tools
#####################
log_info "Installing core packages..."
sudo apt-get update
sudo apt-get install -y curl vim git jq yq nmap sipcalc wget unzip zip

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

# Create plugins directory if it doesn't exist
mkdir -p /home/${CONTAINER_USER}/.asdf/plugins

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

# Install pipx right after Python is available
log_info "Installing pipx..."
python -m pip install --upgrade pip --root-user-action=ignore
python -m pip install pipx --root-user-action=ignore
if ! asdf reshim python; then
  exit_with_error "❌ asdf reshim python failed after pipx install"
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
echo 'export PATH="$PATH:/home/vscode/.local/bin"' >> ${BASH_RC}
echo 'export PATH="$PATH:/home/vscode/.local/bin"' >> ${ZSH_RC}

log_info "Installing Python packages..."
sudo -u ${CONTAINER_USER} bash -c "export PATH=\"\$PATH:/home/${CONTAINER_USER}/.local/bin\" && source /home/${CONTAINER_USER}/.asdf/asdf.sh && python -m pipx install aws-sso-util"
python -m pip install ruamel_yaml --root-user-action=ignore

#################
# Configure Git #
#################
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
[credential]
    credentialStore = cache
[push]
    autoSetupRemote = true
[safe]
    directory = *
EOF

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
