"""Environment command for the Caylent Devcontainer CLI."""

import os

from caylent_devcontainer_cli.utils.fs import generate_shell_env
from caylent_devcontainer_cli.utils.ui import log


def register_command(subparsers):
    """Register the env command."""
    env_parser = subparsers.add_parser("env", help="Environment variable management")
    env_subparsers = env_parser.add_subparsers(dest="env_command")

    # 'env export' command
    export_parser = env_subparsers.add_parser("export", help="Generate shell exports from JSON")
    export_parser.add_argument("json_file", help="Path to JSON with 'containerEnv'")
    export_parser.add_argument("-o", "--output", required=True, help="Output file for shell exports")
    export_parser.add_argument("--no-export", action="store_true", help="Omit 'export' prefix (for .env files)")
    export_parser.add_argument("-y", "--yes", action="store_true", help="Automatically answer yes to all prompts")
    export_parser.set_defaults(func=handle_env_export)

    # 'env load' command
    load_parser = env_subparsers.add_parser("load", help="Load environment variables")
    load_parser.add_argument("-p", "--project-root", help="Project root directory (default: current directory)")
    load_parser.add_argument("-y", "--yes", action="store_true", help="Automatically answer yes to all prompts")
    load_parser.set_defaults(func=handle_env_load)


def handle_env_export(args):
    """Handle the env export command."""
    generate_shell_env(args.json_file, args.output, args.no_export)


def handle_env_load(args):
    """Handle the env load command."""
    project_root = args.project_root or os.getcwd()
    load_environment(project_root)


def load_environment(project_root):
    """Load environment variables from shell.env file."""
    shell_env_path = os.path.join(project_root, "shell.env")
    env_vars_json = os.path.join(project_root, "devcontainer-environment-variables.json")

    # Generate shell.env if it doesn't exist
    if not os.path.exists(shell_env_path):
        if os.path.exists(env_vars_json):
            log("INFO", f"Generating shell.env from {env_vars_json}")
            generate_shell_env(env_vars_json, shell_env_path)
        else:
            log("ERR", f"Configuration file not found: {env_vars_json}")
            import sys

            sys.exit(1)

    # Print instructions for sourcing the environment
    from caylent_devcontainer_cli.utils.ui import COLORS

    print(f"{COLORS['CYAN']}To load the environment variables, run:{COLORS['RESET']}")
    print(f"source {shell_env_path}")
    print(f"\n{COLORS['CYAN']}Or to load and launch VS Code in one command:{COLORS['RESET']}")
    print(f"source {shell_env_path} && code {project_root}")
    warning = f"\n{COLORS['YELLOW']}⚠️  IMPORTANT: Use a dedicated terminal for each project{COLORS['RESET']}"
    print(warning)
