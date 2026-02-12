"""Code command for the Caylent Devcontainer CLI."""

import os
import shutil
import subprocess

from caylent_devcontainer_cli.utils.constants import ENV_VARS_FILENAME, SHELL_ENV_FILENAME
from caylent_devcontainer_cli.utils.fs import load_json_config, resolve_project_root, write_shell_env
from caylent_devcontainer_cli.utils.ui import COLORS, ask_or_exit, exit_cancelled, exit_with_error, log

_GENERATE_HINT = (
    "Run `cdevcontainer setup-devcontainer <path>` or "
    "`cdevcontainer template load <name> -p <path>` to generate project files"
)


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
            f"Run: {COLORS['GREEN']}cdevcontainer template upgrade {template_name}{COLORS['RESET']} "
            "# To upgrade the template"
        )
        print(
            f"Run: {COLORS['GREEN']}cdevcontainer template load --project-root . {template_name}{COLORS['RESET']} "
            "# To load the upgraded template into the project"
        )
    else:
        print(
            f"Run: {COLORS['GREEN']}cdevcontainer template upgrade <template-name>{COLORS['RESET']} "
            "# To upgrade the template"
        )
        print(
            f"Run: {COLORS['GREEN']}cdevcontainer template load --project-root <project-root> "
            f"<template-name>{COLORS['RESET']} # To load the upgraded template into the project"
        )

    choice = ask_or_exit(
        questionary.select(
            "What would you like to do?",
            choices=[
                "Exit and upgrade the profile first (recommended)",
                "Continue without the upgrade (may cause issues)",
            ],
            default="Exit and upgrade the profile first (recommended)",
        )
    )

    if "Exit" in choice:
        exit_cancelled("Please upgrade your profile and try again")
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
    code_parser.add_argument(
        "--ide", choices=["vscode", "cursor"], default="vscode", help="IDE to launch (default: vscode)"
    )
    code_parser.add_argument(
        "--regenerate-shell-env",
        action="store_true",
        help="Regenerate shell.env from existing JSON configuration without full setup",
    )
    code_parser.set_defaults(func=handle_code)


def handle_code(args):
    """Handle the code command.

    Environment variables are sourced inside the devcontainer by the
    postCreateCommand — not before IDE launch.  The launch command is
    simply ``<ide_command> <project_root>``.
    """
    project_root = resolve_project_root(args.project_root)

    env_json = os.path.join(project_root, ENV_VARS_FILENAME)
    shell_env = os.path.join(project_root, SHELL_ENV_FILENAME)

    # --regenerate-shell-env: read JSON, regenerate shell.env only
    if args.regenerate_shell_env:
        if not os.path.isfile(env_json):
            exit_with_error(f"{ENV_VARS_FILENAME} not found at {env_json}. {_GENERATE_HINT}")

        config_data = load_json_config(env_json)
        write_shell_env(
            project_root,
            config_data.get("containerEnv", {}),
            config_data.get("cli_version", ""),
            config_data.get("template_name", "unknown"),
            config_data.get("template_path", ""),
        )
        log("OK", "Regenerated shell.env from existing JSON configuration")
    else:
        # Both files must already exist
        if not os.path.isfile(env_json):
            exit_with_error(f"{ENV_VARS_FILENAME} not found at {env_json}. {_GENERATE_HINT}")
        if not os.path.isfile(shell_env):
            exit_with_error(f"{SHELL_ENV_FILENAME} not found at {shell_env}. {_GENERATE_HINT}")

    # Get IDE configuration
    ide_config = IDE_CONFIG[args.ide]
    ide_command = ide_config["command"]
    ide_name = ide_config["name"]

    # Check if IDE command exists
    if not shutil.which(ide_command):
        log("INFO", ide_config["install_instructions"])
        exit_with_error(f"{ide_name} command '{ide_command}' not found in PATH")

    # Launch IDE — env vars are sourced inside the devcontainer, not here
    log("INFO", f"Launching {ide_name}...")

    try:
        process = subprocess.Popen([ide_command, project_root])
        process.wait()
        log("OK", f"{ide_name} launched. Accept the prompt to reopen in container when it appears.")
    except Exception as e:
        exit_with_error(f"Failed to launch {ide_name}: {e}")
