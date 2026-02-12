"""Template utility functions for the Caylent Devcontainer CLI."""

import os
import sys
from typing import Any, Dict, List

import semver

from caylent_devcontainer_cli import __version__
from caylent_devcontainer_cli.utils.constants import TEMPLATES_DIR
from caylent_devcontainer_cli.utils.ui import log


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
    """Validate template data structure.

    Full implementation is in S1.2.1. This is the function signature/stub location.

    Args:
        template_data: The template data to validate.

    Returns:
        The validated template data.
    """
    return template_data


def check_template_version(template_data: Dict[str, Any]) -> None:
    """Validate that the template's cli_version matches the current CLI major version.

    For v2.0.0, rejects any template without cli_version or with a
    non-matching major version.

    Args:
        template_data: The template data containing cli_version.

    Raises:
        SystemExit: If the template version is incompatible.
    """
    if "cli_version" not in template_data:
        log("ERR", "Template is missing cli_version field")
        log("INFO", "Templates must include a cli_version to be compatible with this CLI version")
        sys.exit(1)

    template_version_str = template_data["cli_version"]

    try:
        template_ver = semver.VersionInfo.parse(template_version_str)
    except ValueError:
        log("ERR", f"Invalid template version format: {template_version_str}")
        log("INFO", "The cli_version field must be a valid semantic version (e.g. 2.0.0)")
        sys.exit(1)

    try:
        current_ver = semver.VersionInfo.parse(__version__)
    except ValueError:
        log("ERR", f"Invalid current CLI version format: {__version__}")
        sys.exit(1)

    if template_ver.major != current_ver.major:
        log(
            "ERR",
            f"Template version {template_version_str} is incompatible with CLI version {__version__}",
        )
        log(
            "INFO",
            f"Template major version ({template_ver.major}) must match " f"CLI major version ({current_ver.major})",
        )
        sys.exit(1)
