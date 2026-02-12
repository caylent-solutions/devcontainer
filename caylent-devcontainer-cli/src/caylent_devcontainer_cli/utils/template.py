"""Template utility functions for the Caylent Devcontainer CLI."""

import copy
import os
from typing import Any, Dict, List

import questionary
import semver

from caylent_devcontainer_cli import __version__
from caylent_devcontainer_cli.utils.constants import (
    TEMPLATES_DIR,
    VALID_KEY_VALUES,
)
from caylent_devcontainer_cli.utils.ui import ask_or_exit, exit_with_error, log


def get_template_path(name: str) -> str:
    """Return the full file path for a template by name.

    Args:
        name: The template name (without .json extension).

    Returns:
        The full path to the template JSON file.
    """
    return os.path.join(TEMPLATES_DIR, f"{name}.json")


def get_template_names() -> List[str]:
    """Scan TEMPLATES_DIR and return a sorted list of template names.

    Returns:
        A sorted list of template names (without .json extension).
        Returns an empty list if the templates directory does not exist.
    """
    if not os.path.exists(TEMPLATES_DIR):
        return []

    names = []
    for filename in os.listdir(TEMPLATES_DIR):
        if filename.endswith(".json"):
            names.append(filename[: -len(".json")])

    return sorted(names)


def ensure_templates_dir() -> None:
    """Create the templates directory if it does not exist."""
    os.makedirs(TEMPLATES_DIR, exist_ok=True)


def validate_template(template_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate template data and prompt user to fix issues.

    Runs five validation phases in order:
    1. Structural validation — required top-level keys and types
    2. Base key completeness — all EXAMPLE_ENV_VALUES keys present
    3. Known key value validation — constrained fields have valid values
    4. Auth method consistency — token vs SSH mutual exclusivity
    5. Conflict detection — new known keys vs existing custom keys

    Args:
        template_data: The template data to validate.

    Returns:
        A validated (possibly modified) copy of the template data.

    Raises:
        SystemExit: If structural validation fails or user cancels prompts.
    """
    data = copy.deepcopy(template_data)

    _validate_structure(data)
    _validate_base_key_completeness(data)
    _validate_known_key_values(data)
    _validate_auth_consistency(data)
    _detect_conflicts(data)

    return data


# ---------------------------------------------------------------------------
# Phase 1: Structural Validation
# ---------------------------------------------------------------------------


def _validate_structure(data: Dict[str, Any]) -> None:
    """Validate required top-level keys and types.

    Args:
        data: Template data dict.

    Raises:
        SystemExit: If any structural requirement is not met.
    """
    # containerEnv must exist and be a dict
    if "containerEnv" not in data:
        exit_with_error("Template is missing required key: containerEnv")
    if not isinstance(data["containerEnv"], dict):
        exit_with_error("Template key 'containerEnv' must be a dict")

    # cli_version must exist and be v2.x
    if "cli_version" not in data:
        exit_with_error("Template is missing required key: cli_version")

    cli_version_str = data["cli_version"]
    try:
        ver = semver.VersionInfo.parse(cli_version_str)
    except ValueError:
        exit_with_error(f"Invalid cli_version format: {cli_version_str}")

    if ver.major < 2:
        exit_with_error(
            f"This template was created with CLI v{ver.major}.x and is not compatible "
            "with v2.0.0. Please recreate your template using "
            "`cdevcontainer template create <name>`"
        )
    if ver.major > 2:
        try:
            current_ver = semver.VersionInfo.parse(__version__)
        except ValueError:
            exit_with_error(f"Invalid current CLI version: {__version__}")
        if ver.major != current_ver.major:
            exit_with_error(f"Template version {cli_version_str} is incompatible with CLI version {__version__}")

    # template_name and template_path must exist
    for key in ("template_name", "template_path"):
        if key not in data:
            exit_with_error(f"Template is missing required key: {key}")


# ---------------------------------------------------------------------------
# Phase 2: Base Key Completeness
# ---------------------------------------------------------------------------


def _validate_base_key_completeness(data: Dict[str, Any]) -> None:
    """Verify all EXAMPLE_ENV_VALUES keys exist in containerEnv.

    Missing keys prompt user to accept default or enter custom value.
    GIT_TOKEN is only required when GIT_AUTH_METHOD=token.

    Args:
        data: Template data dict (modified in place).
    """
    from caylent_devcontainer_cli.commands.setup import EXAMPLE_ENV_VALUES

    container_env = data["containerEnv"]
    auth_method = container_env.get("GIT_AUTH_METHOD", "token")

    for key, default_value in sorted(EXAMPLE_ENV_VALUES.items()):
        # GIT_TOKEN is conditional on auth method
        if key == "GIT_TOKEN" and auth_method == "ssh":
            continue

        if key not in container_env:
            log("WARN", f"Missing environment variable: {key} (default: {default_value})")
            answer = ask_or_exit(
                questionary.text(
                    f"Enter value for {key}:",
                    default=default_value,
                )
            )
            container_env[key] = answer


# ---------------------------------------------------------------------------
# Phase 3: Known Key Value Validation
# ---------------------------------------------------------------------------


def _validate_known_key_values(data: Dict[str, Any]) -> None:
    """Validate that constrained keys have valid values.

    For keys in VALID_KEY_VALUES, if the current value is not in the valid set,
    prompt the user to select a valid value. Also validates GIT_PROVIDER_URL
    (hostname only) and HOST_PROXY_URL (http(s):// prefix when proxy enabled).

    Args:
        data: Template data dict (modified in place).
    """
    container_env = data["containerEnv"]

    # Validate keys with enumerated valid values
    for key, valid_values in VALID_KEY_VALUES.items():
        if key not in container_env:
            continue
        current = container_env[key]
        if current not in valid_values:
            log(
                "WARN",
                f"Invalid value for {key}: '{current}'. Must be one of: {', '.join(valid_values)}",
            )
            answer = ask_or_exit(
                questionary.select(
                    f"Select a valid value for {key}:",
                    choices=list(valid_values),
                )
            )
            container_env[key] = answer

    # Validate GIT_PROVIDER_URL — hostname only, no protocol, must contain a dot
    if "GIT_PROVIDER_URL" in container_env:
        _validate_git_provider_url(container_env)

    # Validate HOST_PROXY_URL — only when HOST_PROXY=true
    if container_env.get("HOST_PROXY") == "true" and "HOST_PROXY_URL" in container_env:
        _validate_host_proxy_url(container_env)


def _validate_git_provider_url(container_env: Dict[str, Any]) -> None:
    """Validate GIT_PROVIDER_URL is hostname only with at least one dot.

    Args:
        container_env: The containerEnv dict (modified in place).
    """
    url = container_env["GIT_PROVIDER_URL"]
    if url.startswith("http://") or url.startswith("https://") or "." not in url:
        log(
            "WARN",
            f"Invalid GIT_PROVIDER_URL: '{url}'. Must be hostname only (no protocol prefix) "
            "and contain at least one dot (e.g., github.com).",
        )
        answer = ask_or_exit(
            questionary.text(
                "Enter a valid GIT_PROVIDER_URL (hostname only, e.g., github.com):",
                default="github.com",
            )
        )
        container_env["GIT_PROVIDER_URL"] = answer


def _validate_host_proxy_url(container_env: Dict[str, Any]) -> None:
    """Validate HOST_PROXY_URL starts with http:// or https://.

    Only called when HOST_PROXY=true.

    Args:
        container_env: The containerEnv dict (modified in place).
    """
    url = container_env["HOST_PROXY_URL"]
    if not url.startswith("http://") and not url.startswith("https://"):
        log(
            "WARN",
            f"Invalid HOST_PROXY_URL: '{url}'. Must start with http:// or https://.",
        )
        answer = ask_or_exit(
            questionary.text(
                "Enter a valid HOST_PROXY_URL (must start with http:// or https://):",
            )
        )
        container_env["HOST_PROXY_URL"] = answer


# ---------------------------------------------------------------------------
# Phase 4: Auth Method Consistency
# ---------------------------------------------------------------------------


def _validate_auth_consistency(data: Dict[str, Any]) -> None:
    """Enforce mutual exclusivity between token and SSH auth.

    - token: GIT_TOKEN must exist and be non-empty; ssh_private_key removed
    - ssh: GIT_TOKEN removed; ssh_private_key preserved

    Args:
        data: Template data dict (modified in place).
    """
    container_env = data["containerEnv"]
    auth_method = container_env.get("GIT_AUTH_METHOD", "token")

    if auth_method == "token":
        # GIT_TOKEN must exist and be non-empty
        git_token = container_env.get("GIT_TOKEN", "")
        if not git_token:
            log("WARN", "GIT_AUTH_METHOD is 'token' but GIT_TOKEN is empty.")
            answer = ask_or_exit(questionary.text("Enter your GIT_TOKEN:"))
            container_env["GIT_TOKEN"] = answer

        # Remove ssh_private_key if present
        data.pop("ssh_private_key", None)

    elif auth_method == "ssh":
        # Remove GIT_TOKEN if present
        container_env.pop("GIT_TOKEN", None)


# ---------------------------------------------------------------------------
# Phase 5: Conflict Detection
# ---------------------------------------------------------------------------


def _detect_conflicts(data: Dict[str, Any]) -> None:
    """Detect new known keys that conflict with existing custom keys.

    If the CLI has added new known keys since the template was created,
    and those keys already exist in the template with non-default values,
    flag each one and prompt the user.

    Args:
        data: Template data dict (modified in place).
    """
    from caylent_devcontainer_cli.commands.setup import EXAMPLE_ENV_VALUES

    container_env = data["containerEnv"]
    template_version_str = data.get("cli_version", "")

    try:
        template_ver = semver.VersionInfo.parse(template_version_str)
        current_ver = semver.VersionInfo.parse(__version__)
    except ValueError:
        return

    # Only check for conflicts if template was created with an older version
    if template_ver >= current_ver:
        return

    for key, default_value in EXAMPLE_ENV_VALUES.items():
        if key in container_env:
            current_value = container_env[key]
            if current_value != default_value:
                # This key exists with a non-default value — could be a custom key
                # that is now a known key. For constrained keys, the value validation
                # in phase 3 already handles invalid values. We only flag keys where
                # the value is valid but differs from the CLI default.
                if key in VALID_KEY_VALUES and current_value in VALID_KEY_VALUES[key]:
                    # Valid value, different from default — user intentionally set it
                    continue
