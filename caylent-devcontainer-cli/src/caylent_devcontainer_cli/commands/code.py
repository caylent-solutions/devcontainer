"""Code command for the Caylent Devcontainer CLI."""

import os
import shutil
import subprocess

from caylent_devcontainer_cli.utils.constants import ENV_VARS_FILENAME, EXAMPLE_ENV_FILE, SHELL_ENV_FILENAME
from caylent_devcontainer_cli.utils.env import get_missing_env_vars
from caylent_devcontainer_cli.utils.fs import generate_shell_env, load_json_config, resolve_project_root
from caylent_devcontainer_cli.utils.ui import COLORS, log


def prompt_upgrade_or_continue(missing_vars, template_name=None):
    """Prompt user about missing variables and upgrade options."""
    import questionary

    # Display colorful warning
    print(f"\n{COLORS['RED']}⚠️  WARNING: Missing Environment Variables{COLORS['RESET']}")
    print(f"{COLORS['YELLOW']}Your profile is missing the following required variables:{COLORS['RESET']}")
    for var in missing_vars:
        print(f"  - {COLORS['CYAN']}{var}{COLORS['RESET']}")

    print(f"\n{COLORS['BLUE']}To fix this issue:{COLORS['RESET']}")
    if template_name:
        print(
            f"Run: {COLORS['GREEN']}cdevcontainer template upgrade --force {template_name}{COLORS['RESET']} "
            "# To upgrade the template"
        )
        print(
            f"Run: {COLORS['GREEN']}cdevcontainer template load --project-root . {template_name}{COLORS['RESET']} "
            "# To load the upgraded template into the project"
        )
    else:
        print(
            f"Run: {COLORS['GREEN']}cdevcontainer template upgrade --force <template-name>{COLORS['RESET']} "
            "# To upgrade the template"
        )
        print(
            f"Run: {COLORS['GREEN']}cdevcontainer template load --project-root <project-root> "
            f"<template-name>{COLORS['RESET']} # To load the upgraded template into the project"
        )

    choice = questionary.select(
        "What would you like to do?",
        choices=["Exit and upgrade the profile first (recommended)", "Continue without the upgrade (may cause issues)"],
        default="Exit and upgrade the profile first (recommended)",
    ).ask()

    if choice and "Exit" in choice:
        log("INFO", "Please upgrade your profile and try again")
        import sys

        sys.exit(0)
    else:
        log("WARN", "Continuing without upgrade - some features may not work correctly")


# IDE configuration
IDE_CONFIG = {
    "vscode": {
        "command": "code",
        "name": "VS Code",
        "install_instructions": (
            "Please install VS Code and ensure the 'code' command is available in your PATH. "
            "Visit: https://code.visualstudio.com/"
        ),
    },
    "cursor": {
        "command": "cursor",
        "name": "Cursor",
        "install_instructions": (
            "Please install Cursor and ensure the 'cursor' command is available in your PATH. "
            "Visit: https://cursor.sh/"
        ),
    },
}


def register_command(subparsers):
    """Register the code command."""
    code_parser = subparsers.add_parser("code", help="Launch IDE (VS Code, Cursor) with the devcontainer environment")
    code_parser.add_argument(
        "project_root",
        nargs="?",
        default=None,
        help="Project root directory (default: current directory)",
    )
    code_parser.add_argument("-y", "--yes", action="store_true", help="Automatically answer yes to all prompts")
    code_parser.add_argument(
        "--ide", choices=["vscode", "cursor"], default="vscode", help="IDE to launch (default: vscode)"
    )
    code_parser.set_defaults(func=handle_code)


def handle_code(args):
    """Handle the code command."""
    project_root = resolve_project_root(args.project_root)

    # Check if devcontainer-environment-variables.json exists
    env_json = os.path.join(project_root, ENV_VARS_FILENAME)
    shell_env = os.path.join(project_root, SHELL_ENV_FILENAME)

    if not os.path.isfile(env_json):
        log("ERR", f"Configuration file not found: {env_json}")
        log("INFO", "Please create this file first:")
        print(f"cp .devcontainer/{EXAMPLE_ENV_FILE} {ENV_VARS_FILENAME}")
        import sys

        sys.exit(1)

    # Check for missing environment variables
    try:
        config_data = load_json_config(env_json)
        container_env = config_data.get("containerEnv", {})
        missing_vars = get_missing_env_vars(container_env)
        if missing_vars:
            template_name = None
            if "cli_version" in config_data:
                # This might be from a template, but we can't determine the name
                # So we'll just show the generic upgrade command
                pass

            prompt_upgrade_or_continue(list(missing_vars.keys()), template_name)
    except SystemExit:
        # If config loading fails, the error was already logged, just re-raise
        raise

    # Generate shell.env if needed
    if not os.path.isfile(shell_env) or os.path.getmtime(env_json) > os.path.getmtime(shell_env):
        log("INFO", "Generating environment variables...")
        generate_shell_env(env_json, shell_env)
    else:
        log("INFO", "Using existing shell.env file")

    # Ensure .gitignore entries
    from caylent_devcontainer_cli.commands.setup import ensure_gitignore_entries

    ensure_gitignore_entries(project_root)

    # Get IDE configuration
    ide_config = IDE_CONFIG[args.ide]
    ide_command = ide_config["command"]
    ide_name = ide_config["name"]

    # Check if IDE command exists
    if not shutil.which(ide_command):
        log("ERR", f"{ide_name} command '{ide_command}' not found in PATH")
        log("INFO", ide_config["install_instructions"])
        import sys

        sys.exit(1)

    # Launch IDE
    log("INFO", f"Launching {ide_name}...")

    # Create a command that sources the environment and runs the IDE
    command = f"source {shell_env} && {ide_command} {project_root}"

    try:
        # Execute the command in a new shell
        process = subprocess.Popen(command, shell=True, executable=os.environ.get("SHELL", "/bin/bash"))
        process.wait()
        log("OK", f"{ide_name} launched. Accept the prompt to reopen in container when it appears.")
    except Exception as e:
        log("ERR", f"Failed to launch {ide_name}: {e}")
        import sys

        sys.exit(1)
