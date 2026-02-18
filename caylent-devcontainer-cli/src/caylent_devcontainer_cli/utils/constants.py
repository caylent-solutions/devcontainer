"""Constants for the Caylent Devcontainer CLI."""

import os
import re

# Directories
TEMPLATES_DIR = os.path.expanduser("~/.devcontainer-templates")

# CLI name
CLI_NAME = "Caylent Devcontainer CLI"

# File path constants
ENV_VARS_FILENAME = "devcontainer-environment-variables.json"
SHELL_ENV_FILENAME = "shell.env"
CATALOG_ENTRY_FILENAME = "catalog-entry.json"
SSH_KEY_FILENAME = "ssh-private-key"

# Default catalog URL (this repo)
DEFAULT_CATALOG_URL = "https://github.com/caylent-solutions/devcontainer.git"

# Minimum catalog tag version — the CLI resolves the latest semver tag >= this value
MIN_CATALOG_TAG_VERSION = "2.0.0"

# Catalog structure constants
CATALOG_COMMON_DIR = "common"
CATALOG_ASSETS_DIR = "devcontainer-assets"
CATALOG_ENTRIES_DIR = "catalog"
CATALOG_VERSION_FILENAME = "VERSION"
CATALOG_ROOT_ASSETS_DIR = "root-project-assets"

# Required files in common/devcontainer-assets/
CATALOG_REQUIRED_COMMON_ASSETS = (
    ".devcontainer.postcreate.sh",
    "devcontainer-functions.sh",
    "postcreate-wrapper.sh",
    "project-setup.sh",
)

# Required files in each catalog entry
CATALOG_REQUIRED_ENTRY_FILES = (
    CATALOG_ENTRY_FILENAME,
    "devcontainer.json",
    CATALOG_VERSION_FILENAME,
)

# Subdirectories expected in common/devcontainer-assets/
CATALOG_COMMON_SUBDIRS = ("nix-family-os", "wsl-family-os")

# Required files within each common asset subdirectory
CATALOG_COMMON_SUBDIR_REQUIRED_FILES = (
    "README.md",
    "tinyproxy.conf.template",
    "tinyproxy-daemon.sh",
)

# Shell scripts that must have the executable bit set
CATALOG_EXECUTABLE_COMMON_ASSETS = (
    ".devcontainer.postcreate.sh",
    "devcontainer-functions.sh",
    "postcreate-wrapper.sh",
    "project-setup.sh",
)
CATALOG_EXECUTABLE_SUBDIR_ASSETS = ("tinyproxy-daemon.sh",)

# Container source fields — at least one must exist in devcontainer.json
DEVCONTAINER_CONTAINER_SOURCE_FIELDS = (
    "image",
    "build",
    "dockerFile",
    "dockerComposeFile",
)

# Allowed top-level fields in catalog-entry.json (unknown fields = error)
CATALOG_ENTRY_ALLOWED_FIELDS = frozenset(
    {
        "name",
        "description",
        "tags",
        "maintainer",
        "min_cli_version",
    }
)

# Reusable semver pattern (X.Y.Z)
SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")

# catalog-entry.json name pattern: lowercase, dash-separated, min 2 chars
CATALOG_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9-]*[a-z0-9]$")

# Tag pattern: lowercase, dash-separated
CATALOG_TAG_PATTERN = re.compile(r"^[a-z][a-z0-9-]*[a-z0-9]$")

# Template structural requirements — top-level keys that must exist
REQUIRED_TEMPLATE_KEYS = (
    "containerEnv",
    "cli_version",
    "template_name",
    "template_path",
)

# Known key value constraints — maps key name to valid choices
VALID_KEY_VALUES = {
    "AWS_CONFIG_ENABLED": ("true", "false"),
    "AWS_DEFAULT_OUTPUT": ("json", "table", "text", "yaml"),
    "GIT_AUTH_METHOD": ("token", "ssh"),
    "HOST_PROXY": ("true", "false"),
    "PAGER": ("cat", "less", "more", "most"),
}

# Keys whose values are validated only under certain conditions
# GIT_PROVIDER_URL: hostname only — no protocol prefix, must contain at least one dot
# HOST_PROXY_URL: must start with http:// or https:// — only validated when HOST_PROXY=true

# Default NO_PROXY bypass list — addresses that should not be routed through HOST_PROXY.
# All external traffic (including apt repos) goes through the proxy when HOST_PROXY=true.
DEFAULT_NO_PROXY = (
    "localhost,127.0.0.1,.local,169.254.169.254"
)

# CLI-level environment variables — name, description, and which commands they apply to.
# Entries with an empty ``commands`` list are global (shown for every subcommand).
CLI_ENV_VARS = [
    {
        "name": "DEVCONTAINER_CATALOG_URL",
        "description": "Override the default catalog repository URL (supports @tag suffix)",
        "commands": ["setup-devcontainer", "catalog"],
    },
    {
        "name": "CDEVCONTAINER_SKIP_UPDATE",
        "description": "Set to '1' to disable automatic update checks",
        "commands": [],
    },
    {
        "name": "CDEVCONTAINER_DEBUG_UPDATE",
        "description": "Set to '1' to enable debug logging for update checks",
        "commands": [],
    },
]

# All known environment variable keys (used for conflict detection in custom env var loop)
# This is the union of EXAMPLE_ENV_VALUES keys — defined here to avoid circular imports.
KNOWN_KEYS = frozenset(
    {
        "AWS_CONFIG_ENABLED",
        "AWS_DEFAULT_OUTPUT",
        "DEFAULT_GIT_BRANCH",
        "DEVELOPER_NAME",
        "EXTRA_APT_PACKAGES",
        "GIT_AUTH_METHOD",
        "GIT_PROVIDER_URL",
        "GIT_TOKEN",
        "GIT_USER",
        "GIT_USER_EMAIL",
        "HOST_PROXY",
        "HOST_PROXY_URL",
        "PAGER",
    }
)
