"""Install command for the Caylent Devcontainer CLI."""

import os
import shutil
import sys

from caylent_devcontainer_cli.utils.constants import INSTALL_DIR
from caylent_devcontainer_cli.utils.ui import confirm_action, log


def register_command(subparsers):
    """Register the install command."""
    # 'install' command
    install_parser = subparsers.add_parser("install", help="Install the CLI tool to your PATH")
    install_parser.add_argument("-y", "--yes", action="store_true", help="Automatically answer yes to all prompts")
    install_parser.set_defaults(func=handle_install)

    # 'uninstall' command
    uninstall_parser = subparsers.add_parser("uninstall", help="Uninstall the CLI tool")
    uninstall_parser.add_argument("-y", "--yes", action="store_true", help="Automatically answer yes to all prompts")
    uninstall_parser.set_defaults(func=handle_uninstall)


def handle_install(args):
    """Handle the install command."""
    install_cli()


def handle_uninstall(args):
    """Handle the uninstall command."""
    uninstall_cli()


def install_cli():
    """Install the CLI tool to the user's PATH."""
    # Get the path to the entry point script
    import caylent_devcontainer_cli

    package_dir = os.path.dirname(os.path.abspath(caylent_devcontainer_cli.__file__))
    script_path = os.path.join(package_dir, "../../../bin/cdevcontainer")

    if not os.path.exists(script_path):
        # If not found, try to find it in the current directory
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "bin/cdevcontainer",
        )

    if not os.path.exists(script_path):
        log("ERR", "Could not find the CLI entry point script")
        sys.exit(1)

    install_path = os.path.join(INSTALL_DIR, "cdevcontainer")

    # Create the installation directory if it doesn't exist
    os.makedirs(INSTALL_DIR, exist_ok=True)

    # Check if the CLI is already installed
    if os.path.exists(install_path):
        if not confirm_action(
            f"The Caylent Devcontainer CLI is already installed at:\n{install_path}\nDo you want to overwrite it?"
        ):
            sys.exit(1)

    try:
        # Copy the script to the installation directory
        shutil.copy2(script_path, install_path)
        os.chmod(install_path, 0o755)  # Make it executable

        # Check if the installation directory is in PATH
        path_dirs = os.environ.get("PATH", "").split(os.pathsep)
        if INSTALL_DIR not in path_dirs:
            log("WARN", f"{INSTALL_DIR} is not in your PATH")
            print("Add the following line to your shell profile (~/.bashrc, ~/.zshrc, etc.):")
            print(f'export PATH="{INSTALL_DIR}:$PATH"')

        log("OK", f"Caylent Devcontainer CLI installed successfully at {install_path}")
        log("INFO", "You can now run 'cdevcontainer' from anywhere")
    except Exception as e:
        log("ERR", f"Failed to install CLI: {e}")
        sys.exit(1)


def uninstall_cli():
    """Uninstall the CLI tool."""
    install_path = os.path.join(INSTALL_DIR, "cdevcontainer")

    if not os.path.exists(install_path):
        log("INFO", "Caylent Devcontainer CLI is not installed")
        return

    if not confirm_action(f"This will remove the Caylent Devcontainer CLI from:\n{install_path}"):
        sys.exit(1)

    try:
        os.remove(install_path)
        log("OK", "Caylent Devcontainer CLI uninstalled successfully")
    except Exception as e:
        log("ERR", f"Failed to uninstall CLI: {e}")
        sys.exit(1)
