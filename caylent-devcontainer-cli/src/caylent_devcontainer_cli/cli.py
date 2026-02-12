"""Main CLI entry point for Caylent Devcontainer CLI."""

import argparse
import sys

from caylent_devcontainer_cli import __version__
from caylent_devcontainer_cli.commands import code, setup, template
from caylent_devcontainer_cli.utils.constants import CLI_NAME


def main():
    """Main entry point for the CLI."""
    # Lightweight pre-parse for skip-update-check flag
    skip_update_check = "--skip-update-check" in sys.argv

    # Check for updates before main parsing (unless skipped)
    if not skip_update_check:
        from caylent_devcontainer_cli.utils.version import check_for_updates

        if not check_for_updates():
            sys.exit(1)

    # Create the main parser
    parser = argparse.ArgumentParser(
        description=f"{CLI_NAME} - Manage devcontainer environments",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Add global options
    parser.add_argument("-v", "--version", action="version", version=f"{CLI_NAME} {__version__}")
    parser.add_argument("--skip-update-check", action="store_true", help="Skip automatic update check")

    # Create subparsers
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Register commands
    code.register_command(subparsers)
    template.register_command(subparsers)
    setup.register_command(subparsers)

    # Parse arguments
    args = parser.parse_args()

    # Show banner
    from caylent_devcontainer_cli.utils.ui import log

    log("INFO", f"Welcome to {CLI_NAME} {__version__}")

    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)

    # Execute the command
    args.func(args)


if __name__ == "__main__":
    main()
