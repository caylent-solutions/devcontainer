"""Main CLI entry point for Caylent Devcontainer CLI."""

import argparse
import sys

from caylent_devcontainer_cli import __version__
from caylent_devcontainer_cli.commands import catalog, code, completion, setup, template
from caylent_devcontainer_cli.utils.constants import CLI_ENV_VARS, CLI_NAME


class _HelpFormatter(argparse.RawDescriptionHelpFormatter, argparse.ArgumentDefaultsHelpFormatter):
    """Formatter that preserves epilog whitespace while showing argument defaults."""


def build_env_epilog(command_name=None):
    """Build an epilog string listing relevant environment variables.

    Args:
        command_name: Subcommand name to filter by (e.g. ``"setup-devcontainer"``).
            When ``None``, all env vars are included (used for the top-level parser).

    Returns:
        Formatted epilog string.
    """
    if command_name is None:
        env_vars = CLI_ENV_VARS
    else:
        env_vars = [v for v in CLI_ENV_VARS if not v["commands"] or command_name in v["commands"]]

    if not env_vars:
        return ""

    max_name = max(len(v["name"]) for v in env_vars)
    lines = ["environment variables:"]
    for var in env_vars:
        padding = " " * (max_name - len(var["name"]) + 2)
        lines.append(f"  {var['name']}{padding}{var['description']}")
    return "\n".join(lines)


def build_parser():
    """Build and return the fully configured CLI argument parser.

    Extracted so that ``shtab`` (and tests) can access the parser
    without running ``main()``.
    """
    parser = argparse.ArgumentParser(
        description=f"{CLI_NAME} - Manage devcontainer environments",
        formatter_class=_HelpFormatter,
        epilog=build_env_epilog(),
    )

    # Add global options
    parser.add_argument("-v", "--version", action="version", version=f"{CLI_NAME} {__version__}")
    parser.add_argument("--skip-update-check", action="store_true", help="Skip automatic update check")

    # Create subparsers
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Register commands
    catalog.register_command(subparsers)
    code.register_command(subparsers)
    completion.register_command(subparsers, parent_parser=parser)
    template.register_command(subparsers)
    setup.register_command(subparsers)

    return parser


def main():
    """Main entry point for the CLI."""
    # Lightweight pre-parse: skip update check for --skip-update-check flag
    # and for the completion command (which must be fast and side-effect-free)
    skip_update_check = "--skip-update-check" in sys.argv or (len(sys.argv) > 1 and sys.argv[1] == "completion")

    # Check for updates before main parsing (unless skipped)
    if not skip_update_check:
        from caylent_devcontainer_cli.utils.version import check_for_updates

        if not check_for_updates():
            sys.exit(1)

    parser = build_parser()

    # Parse arguments
    args = parser.parse_args()

    # Show banner (skip for completion — output must be clean shell script)
    if args.command != "completion":
        from caylent_devcontainer_cli.utils.ui import log

        log("INFO", f"Welcome to {CLI_NAME} {__version__}")

    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)

    # Execute the command
    args.func(args)


if __name__ == "__main__":
    main()
