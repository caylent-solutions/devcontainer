"""Shared validation detection for project files (Steps 0-3).

This module implements the shared validation logic used by both the
code command and setup-devcontainer. It detects issues without taking
corrective action — the caller decides how to respond.

Steps:
    0 — Check base keys (EXAMPLE_ENV_VALUES) in both JSON and shell.env
    1 — Validate required metadata (template_name, template_path, cli_version)
    2 — Locate and validate the developer template
    3 — Compare template containerEnv against project containerEnv
"""

import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Set

from caylent_devcontainer_cli.commands.setup import EXAMPLE_ENV_VALUES
from caylent_devcontainer_cli.utils.constants import SHELL_ENV_FILENAME
from caylent_devcontainer_cli.utils.fs import load_json_config
from caylent_devcontainer_cli.utils.template import get_template_path, validate_template
from caylent_devcontainer_cli.utils.ui import log

# Metadata keys required in both JSON and shell.env
_REQUIRED_METADATA = ("template_name", "template_path", "cli_version")


@dataclass
class ShellEnvParseResult:
    """Result of parsing a shell.env file."""

    keys: Set[str] = field(default_factory=set)
    template_name: Optional[str] = None
    template_path: Optional[str] = None
    cli_version: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of the shared validation detection (Steps 0-3).

    Attributes:
        missing_base_keys: Keys from EXAMPLE_ENV_VALUES missing from project files.
        metadata_present: Whether required metadata exists in the JSON config.
        template_name: Template name from metadata (or None).
        template_path: Template path from metadata (or None).
        cli_version: CLI version from metadata (or None).
        template_found: Whether the developer template file was found.
        validated_template: Validated template data (or None if not found/skipped).
        missing_template_keys: Keys in template but not in project containerEnv.
    """

    missing_base_keys: Dict[str, Any] = field(default_factory=dict)
    metadata_present: bool = False
    template_name: Optional[str] = None
    template_path: Optional[str] = None
    cli_version: Optional[str] = None
    template_found: bool = False
    validated_template: Optional[Dict[str, Any]] = None
    missing_template_keys: Dict[str, Any] = field(default_factory=dict)

    @property
    def has_issues(self) -> bool:
        """Return True if any validation issue was detected."""
        return (
            bool(self.missing_base_keys)
            or not self.metadata_present
            or (self.metadata_present and not self.template_found)
            or bool(self.missing_template_keys)
        )

    @property
    def all_missing_keys(self) -> Dict[str, Any]:
        """Combine missing keys from both stages (base + template)."""
        combined = dict(self.missing_base_keys)
        combined.update(self.missing_template_keys)
        return combined


def parse_shell_env(content: str) -> ShellEnvParseResult:
    """Parse shell.env content to extract exported keys and metadata.

    Args:
        content: The raw text content of a shell.env file.

    Returns:
        ShellEnvParseResult with extracted keys and metadata.
    """
    result = ShellEnvParseResult()

    for line in content.splitlines():
        stripped = line.strip()

        # Extract metadata from comment headers
        if stripped.startswith("# Template:") and not stripped.startswith("# Template Path:"):
            result.template_name = stripped.removeprefix("# Template:").strip()
        elif stripped.startswith("# Template Path:"):
            result.template_path = stripped.removeprefix("# Template Path:").strip()
        elif stripped.startswith("# CLI Version:"):
            result.cli_version = stripped.removeprefix("# CLI Version:").strip()

        # Extract exported variable names
        if stripped.startswith("export "):
            match = re.match(r"export\s+([A-Za-z_][A-Za-z0-9_]*)=", stripped)
            if match:
                result.keys.add(match.group(1))

    return result


def _read_shell_env(project_root: str) -> str:
    """Read shell.env content from disk.

    Args:
        project_root: Path to the project root directory.

    Returns:
        The file content as a string, or empty string if file doesn't exist.
    """
    shell_env_path = os.path.join(project_root, SHELL_ENV_FILENAME)
    if not os.path.isfile(shell_env_path):
        return ""
    with open(shell_env_path, "r") as f:
        return f.read()


def _step2_locate_template(template_name: str):
    """Locate and validate the developer template (Step 2).

    Args:
        template_name: The template name from project metadata.

    Returns:
        Tuple of (found: bool, validated_data: dict or None).
    """
    template_file = get_template_path(template_name)
    if not os.path.exists(template_file):
        return (False, None)

    template_data = load_json_config(template_file)
    validated = validate_template(template_data)
    return (True, validated)


def detect_validation_issues(project_root: str, config_data: Dict[str, Any]) -> ValidationResult:
    """Run shared validation detection (Steps 0-3).

    This function detects issues without taking corrective action.
    The caller (code command or setup-devcontainer) decides how to respond.

    Args:
        project_root: Path to the project root directory.
        config_data: Loaded JSON config (devcontainer-environment-variables.json).

    Returns:
        ValidationResult with all detected issues.
    """
    result = ValidationResult()
    container_env = config_data.get("containerEnv", {})

    # Read and parse shell.env for key comparison
    shell_env_content = _read_shell_env(project_root)
    shell_env_parsed = parse_shell_env(shell_env_content)

    # --- Step 0: Check base keys in both files ---
    auth_method = container_env.get("GIT_AUTH_METHOD", "token")

    for key, default_value in EXAMPLE_ENV_VALUES.items():
        # GIT_TOKEN is conditional on auth method
        if key == "GIT_TOKEN" and auth_method == "ssh":
            continue

        in_json = key in container_env
        in_shell = key in shell_env_parsed.keys

        if not in_json or not in_shell:
            result.missing_base_keys[key] = default_value

    # --- Step 1: Validate required metadata ---
    result.metadata_present = all(key in config_data for key in _REQUIRED_METADATA)

    if result.metadata_present:
        result.template_name = config_data.get("template_name")
        result.template_path = config_data.get("template_path")
        result.cli_version = config_data.get("cli_version")
    else:
        # Cannot proceed to Steps 2-3 without metadata
        log("WARN", "Project files are missing required metadata (template_name, template_path, cli_version)")
        return result

    # --- Step 2: Locate and validate template ---
    found, validated = _step2_locate_template(result.template_name)
    result.template_found = found
    result.validated_template = validated

    if not found:
        return result

    # --- Step 3: Compare against template ---
    template_env = validated.get("containerEnv", {})
    for key, value in template_env.items():
        if key not in container_env:
            result.missing_template_keys[key] = value

    return result
