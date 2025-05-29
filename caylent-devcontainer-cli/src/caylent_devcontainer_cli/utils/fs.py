"""File system utilities for the Caylent Devcontainer CLI."""

import json
import os
from typing import Any, Dict, List

from caylent_devcontainer_cli.utils.ui import confirm_action, log


def load_json_config(file_path: str) -> Dict[str, Any]:
    """Load JSON configuration file."""
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
        return data
    except Exception as e:
        log("ERR", f"Error loading {file_path}: {e}")
        import sys

        sys.exit(1)


def generate_exports(env_dict: Dict[str, Any], export_prefix: bool = True) -> List[str]:
    """Generate shell export statements from a dictionary."""
    lines = []
    for key, value in env_dict.items():
        if isinstance(value, (dict, list)):
            val = json.dumps(value)
        else:
            val = str(value)
        prefix = "export " if export_prefix else ""
        line = f"{prefix}{key}='{val}'"
        lines.append(line)
    return lines


def generate_shell_env(json_file: str, output_file: str, no_export: bool = False) -> None:
    """Generate shell environment file from JSON config."""
    log("INFO", f"Reading configuration from {json_file}")
    data = load_json_config(json_file)

    # Only support containerEnv format
    if "containerEnv" in data and isinstance(data["containerEnv"], dict):
        env_data = data["containerEnv"]
    else:
        log(
            "ERR",
            f"Invalid JSON format in {json_file}. The file must contain a 'containerEnv' object.",
        )
        import sys

        sys.exit(1)

    lines = generate_exports(env_data, export_prefix=not no_export)

    # Ask for confirmation before writing to file
    if os.path.exists(output_file):
        if not confirm_action(f"This will overwrite the existing file at:\n{output_file}"):
            import sys

            sys.exit(1)
    else:
        if not confirm_action(f"This will create a new file at:\n{output_file}"):
            import sys

            sys.exit(1)

    try:
        with open(output_file, "w") as f:
            f.write("\n".join(lines) + "\n")
        log("OK", f"Wrote {len(lines)} exports to {output_file}")
    except Exception as e:
        log("ERR", f"Failed to write to {output_file}: {e}")
        import sys

        sys.exit(1)


def find_project_root(path: str) -> str:
    """Find the project root directory."""
    # If path is not provided, use current directory
    if not path:
        path = os.getcwd()

    # If path is a file, use its directory
    if os.path.isfile(path):
        path = os.path.dirname(path)

    # Check if the path has a .devcontainer directory
    if os.path.isdir(os.path.join(path, ".devcontainer")):
        return path

    log("ERR", f"Could not find a valid project root at {path}")
    log("INFO", "A valid project root must contain a .devcontainer directory")
    import sys

    sys.exit(1)
