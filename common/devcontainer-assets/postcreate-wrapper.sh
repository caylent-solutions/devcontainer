#!/bin/bash
# Wrapper for postCreateCommand — keeps the devcontainer.json clean
# and avoids process substitution / pipe lifecycle issues.
set -euo pipefail

# --- shell.env setup ---
if [ ! -f shell.env ]; then
    echo "ERROR: shell.env not found in $(pwd). Run: cdevcontainer setup-devcontainer" >&2
    exit 1
fi
source shell.env
echo "[INFO] HOST_PROXY=${HOST_PROXY:-false} HTTP_PROXY=${HTTP_PROXY:-unset}"

if [ "${HOST_PROXY:-false}" = "true" ] && [ -z "${HTTP_PROXY:-}" ]; then
    echo "ERROR: HOST_PROXY=true but HTTP_PROXY not set after sourcing shell.env" >&2
    exit 1
fi

# --- apt proxy configuration ---
if [ -n "${HTTP_PROXY:-}" ]; then
    echo "Acquire::http::Proxy \"${HTTP_PROXY}\";" | sudo tee /etc/apt/apt.conf.d/99proxy > /dev/null
    echo "Acquire::https::Proxy \"${HTTPS_PROXY:-${HTTP_PROXY}}\";" | sudo tee -a /etc/apt/apt.conf.d/99proxy > /dev/null

    _OLD_IFS="${IFS}"
    IFS=","
    for _e in ${NO_PROXY:-}; do
        IFS="${_OLD_IFS}"
        _e=$(echo "${_e}" | tr -d " ")
        case "${_e}" in
            [a-zA-Z]*.*)
                echo "Acquire::http::Proxy::${_e} \"DIRECT\";" | sudo tee -a /etc/apt/apt.conf.d/99proxy > /dev/null
                echo "Acquire::https::Proxy::${_e} \"DIRECT\";" | sudo tee -a /etc/apt/apt.conf.d/99proxy > /dev/null
                ;;
        esac
    done
    IFS="${_OLD_IFS}"
    echo "[INFO] Configured apt proxy via /etc/apt/apt.conf.d/99proxy"
fi

# --- package installation and postcreate ---
if uname -r | grep -qi microsoft; then
    sudo apt-get update
    sudo apt-get install -y gettext-base jq python3
    find .devcontainer -type f -exec sed -i "s/\r$//" {} +
    python3 .devcontainer/fix-line-endings.py
    sudo apt-get remove -y python3
    sudo apt-get autoremove -y
    sudo -E bash .devcontainer/.devcontainer.postcreate.sh vscode
else
    sudo apt-get update
    sudo apt-get install -y gettext-base jq
    sudo -E bash .devcontainer/.devcontainer.postcreate.sh vscode
fi

echo "Setup complete. View logs: cat /tmp/devcontainer-setup.log"
