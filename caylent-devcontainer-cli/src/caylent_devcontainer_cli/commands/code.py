"""Code command for the Caylent Devcontainer CLI."""

import os
import subprocess

from caylent_devcontainer_cli.utils.fs import find_project_root, generate_shell_env
from caylent_devcontainer_cli.utils.ui import log


def register_command(subparsers):
    """Register the code command."""
    code_parser = subparsers.add_parser("code", help="Launch VS Code with the devcontainer environment")
    code_parser.add_argument(
        "project_root",
        nargs="?",
        default=None,
        help="Project root directory (default: current directory)",
    )
    code_parser.add_argument("-y", "--yes", action="store_true", help="Automatically answer yes to all prompts")
    code_parser.set_defaults(func=handle_code)


def handle_code(args):
    """Handle the code command."""
    project_root = find_project_root(args.project_root)

    # Check if devcontainer-environment-variables.json exists
    env_json = os.path.join(project_root, "devcontainer-environment-variables.json")
    shell_env = os.path.join(project_root, "shell.env")

    if not os.path.isfile(env_json):
        log("ERR", f"Configuration file not found: {env_json}")
        log("INFO", "Please create this file first:")
        print("cp .devcontainer/example-container-env-values.json devcontainer-environment-variables.json")
        import sys

        sys.exit(1)

    # Generate shell.env if needed
    if not os.path.isfile(shell_env) or os.path.getmtime(env_json) > os.path.getmtime(shell_env):
        log("INFO", "Generating environment variables...")
        generate_shell_env(env_json, shell_env)
    else:
        log("INFO", "Using existing shell.env file")

    # Launch VS Code
    log("INFO", "Launching VS Code...")

    # Create a command that sources the environment and runs VS Code
    command = f"source {shell_env} && code {project_root}"

    try:
        # Execute the command in a new shell
        process = subprocess.Popen(command, shell=True, executable=os.environ.get("SHELL", "/bin/bash"))
        process.wait()
        log("OK", "VS Code launched. Accept the prompt to reopen in container when it appears.")
    except Exception as e:
        log("ERR", f"Failed to launch VS Code: {e}")
        import sys

        sys.exit(1)
