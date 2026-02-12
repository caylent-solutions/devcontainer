"""Constants for the Caylent Devcontainer CLI."""

import os

# Directories
TEMPLATES_DIR = os.path.expanduser("~/.devcontainer-templates")
INSTALL_DIR = os.path.expanduser("~/.local/bin")

# CLI name
CLI_NAME = "Caylent Devcontainer CLI"

# File path constants
ENV_VARS_FILENAME = "devcontainer-environment-variables.json"
SHELL_ENV_FILENAME = "shell.env"
EXAMPLE_ENV_FILE = "example-container-env-values.json"
EXAMPLE_AWS_FILE = "example-aws-profile-map.json"
CATALOG_ENTRY_FILENAME = "catalog-entry.json"
SSH_KEY_FILENAME = "ssh-private-key"
