"""File system utilities for the Caylent Devcontainer CLI."""

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Union

from caylent_devcontainer_cli import __version__
from caylent_devcontainer_cli.utils.constants import (
    ENV_VARS_FILENAME,
    EXAMPLE_AWS_FILE,
    EXAMPLE_ENV_FILE,
    SHELL_ENV_FILENAME,
    SSH_KEY_FILENAME,
)
from caylent_devcontainer_cli.utils.ui import exit_with_error, log


def write_json_file(path: str, data: Union[Dict[str, Any], List[Any]]) -> None:
    """Write data to a JSON file with indent=2 and a trailing newline.

    Args:
        path: The file path to write to.
        data: The data to serialize as JSON.
    """
    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
    except Exception as e:
        exit_with_error(f"Failed to write JSON file {path}: {e}")


def remove_example_files(target_devcontainer: str) -> None:
    """Remove example JSON files from a .devcontainer directory.

    Args:
        target_devcontainer: Path to the .devcontainer directory.
    """
    example_files = [
        os.path.join(target_devcontainer, EXAMPLE_ENV_FILE),
        os.path.join(target_devcontainer, EXAMPLE_AWS_FILE),
    ]

    for file_path in example_files:
        if os.path.exists(file_path):
            os.remove(file_path)


def load_json_config(file_path: str) -> Dict[str, Any]:
    """Load JSON configuration file."""
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
        return data
    except Exception as e:
        exit_with_error(f"Error loading {file_path}: {e}")


def write_shell_env(
    project_root: str,
    container_env: Dict[str, Any],
    cli_version: str,
    template_name: str,
    template_path: str,
) -> None:
    """Generate shell.env from environment data.

    Produces shell.env with metadata comment header, sorted exports,
    static container values, and proxy variables if HOST_PROXY=true.

    This function is called by write_project_files() and also by the
    code command's --regenerate-shell-env flag.

    Args:
        project_root: Path to the project root directory.
        container_env: Dict of environment variable key-value pairs.
        cli_version: CLI version string for the metadata header.
        template_name: Template name for the metadata header.
        template_path: Template path for the metadata header.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    project_folder = os.path.basename(os.path.abspath(project_root))

    header_lines = [
        f"# Template: {template_name}",
        f"# Template Path: {template_path}",
        f"# CLI Version: {cli_version}",
        f"# Generated: {timestamp}",
        "",
    ]

    # Build export lines from containerEnv (sorted)
    export_lines = []
    for key in sorted(container_env.keys()):
        value = container_env[key]
        if isinstance(value, (dict, list)):
            val = json.dumps(value)
        else:
            val = str(value)
        export_lines.append(f"export {key}='{val}'")

    # Static container values (sorted into exports)
    static_vars = {
        "BASH_ENV": f"/workspaces/{project_folder}/shell.env",
        "DEVCONTAINER": "true",
        "NO_PROXY": "localhost,127.0.0.1,.local",
        "no_proxy": "localhost,127.0.0.1,.local",
    }

    # Proxy variables when HOST_PROXY=true
    if container_env.get("HOST_PROXY") == "true":
        proxy_url = container_env.get("HOST_PROXY_URL", "")
        static_vars["HTTP_PROXY"] = proxy_url
        static_vars["HTTPS_PROXY"] = proxy_url
        static_vars["http_proxy"] = proxy_url
        static_vars["https_proxy"] = proxy_url

    for key in sorted(static_vars.keys()):
        export_lines.append(f"export {key}='{static_vars[key]}'")

    # Re-sort all export lines by variable name
    export_lines.sort(key=lambda line: line.split("=")[0].replace("export ", ""))

    # Dynamic PATH and unset GIT_EDITOR (appended after sorted exports)
    tail_lines = [
        f'export PATH="$HOME/.asdf/shims:$HOME/.asdf/bin:/workspaces/{project_folder}/.localscripts:$PATH"',
        "",
        "unset GIT_EDITOR",
    ]

    shell_env_path = os.path.join(project_root, SHELL_ENV_FILENAME)
    all_lines = header_lines + export_lines + [""] + tail_lines
    try:
        with open(shell_env_path, "w") as f:
            f.write("\n".join(all_lines) + "\n")
        log("OK", f"Shell environment saved to {shell_env_path}")
    except Exception as e:
        exit_with_error(f"Failed to write {shell_env_path}: {e}")


def write_project_files(
    project_root: str,
    template_data: Dict[str, Any],
    template_name: str,
    template_path: str,
) -> None:
    """Generate all project configuration files from template data.

    This is the single function that produces project files. It always generates
    devcontainer-environment-variables.json and shell.env together, and
    conditionally writes aws-profile-map.json and ssh-private-key.

    Args:
        project_root: Path to the project root directory.
        template_data: Template data dict containing containerEnv and optional aws_profile_map.
        template_name: Name of the template (for metadata).
        template_path: Path to the template file (for metadata).
    """
    container_env = template_data.get("containerEnv", {})
    cli_version = template_data.get("cli_version", __version__)

    # --- 1. Write devcontainer-environment-variables.json ---
    sorted_env = dict(sorted(container_env.items()))
    env_json_data = {
        "template_name": template_name,
        "template_path": template_path,
        "cli_version": cli_version,
        "containerEnv": sorted_env,
    }
    env_json_path = os.path.join(project_root, ENV_VARS_FILENAME)
    write_json_file(env_json_path, env_json_data)
    log("OK", f"Environment variables saved to {env_json_path}")

    # --- 2. Generate shell.env ---
    write_shell_env(project_root, container_env, cli_version, template_name, template_path)

    # --- 3. Write aws-profile-map.json if AWS enabled ---
    if container_env.get("AWS_CONFIG_ENABLED") == "true" and template_data.get("aws_profile_map"):
        aws_map_path = os.path.join(project_root, ".devcontainer", "aws-profile-map.json")
        write_json_file(aws_map_path, template_data["aws_profile_map"])
        log("OK", f"AWS profile map saved to {aws_map_path}")

    # --- 4. Write ssh-private-key placeholder if SSH auth ---
    if container_env.get("GIT_AUTH_METHOD") == "ssh":
        ssh_key_path = os.path.join(project_root, ".devcontainer", SSH_KEY_FILENAME)
        if not os.path.exists(ssh_key_path):
            try:
                with open(ssh_key_path, "w") as f:
                    f.write("")
                os.chmod(ssh_key_path, 0o600)
                log("OK", f"SSH private key placeholder created at {ssh_key_path}")
            except Exception as e:
                exit_with_error(f"Failed to write {ssh_key_path}: {e}")

    # --- 5. Ensure .gitignore entries ---
    _ensure_gitignore_entries(project_root)


def _ensure_gitignore_entries(project_root: str) -> None:
    """Ensure all sensitive file entries exist in .gitignore.

    Args:
        project_root: Path to the project root directory.
    """
    gitignore_path = os.path.join(project_root, ".gitignore")
    required_entries = [
        SHELL_ENV_FILENAME,
        ENV_VARS_FILENAME,
        ".devcontainer/aws-profile-map.json",
        f".devcontainer/{SSH_KEY_FILENAME}",
    ]

    existing_lines = []
    gitignore_exists = os.path.exists(gitignore_path)

    if gitignore_exists:
        with open(gitignore_path, "r") as f:
            existing_lines = [line.strip() for line in f.readlines()]

    missing = [entry for entry in required_entries if entry not in existing_lines]

    if not missing:
        return

    with open(gitignore_path, "a") as f:
        if existing_lines and existing_lines[-1] != "":
            f.write("\n")
        f.write("# Environment files\n")
        for entry in missing:
            f.write(entry + "\n")


def resolve_project_root(path: str = None) -> str:
    """Resolve and validate the project root directory.

    Defaults to os.getcwd() when path is None or empty.
    Validates that a .devcontainer/ directory exists in the resolved path.

    Args:
        path: Optional path to resolve. Defaults to current working directory.

    Returns:
        The resolved project root path.

    Raises:
        SystemExit: If the resolved path does not contain a .devcontainer directory.
    """
    if not path:
        path = os.getcwd()

    # If path is a file, use its directory
    if os.path.isfile(path):
        path = os.path.dirname(path)

    # Check if the path has a .devcontainer directory
    if os.path.isdir(os.path.join(path, ".devcontainer")):
        return path

    log("INFO", "A valid project root must contain a .devcontainer directory")
    exit_with_error(f"Could not find a valid project root at {path}")
