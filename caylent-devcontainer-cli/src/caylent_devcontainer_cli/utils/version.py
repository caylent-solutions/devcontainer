"""Version checking and update utilities for the Caylent Devcontainer CLI."""

import json
import os
import socket
import subprocess
import sys
from urllib.error import URLError
from urllib.request import Request, urlopen

from caylent_devcontainer_cli import __version__
from caylent_devcontainer_cli.utils.ui import COLORS

# Exit codes
EXIT_OK = 0
EXIT_UPGRADE_REQUESTED_ABORT = 21


def _debug_log(message):
    """Log debug message if debug mode is enabled."""
    if os.getenv("CDEVCONTAINER_DEBUG_UPDATE") == "1":
        print(f"DEBUG: {message}", file=sys.stderr)


def _is_interactive_shell():
    """Check if running in an interactive shell."""
    # Skip in CI environments
    if os.getenv("CI") == "true":
        _debug_log("Update check skipped (reason: ci-environment)")
        return False

    # Check for pytest without TTY
    if "pytest" in sys.argv[0] and not sys.stdin.isatty():
        _debug_log("Update check skipped (reason: pytest-no-tty)")
        return False

    # If we have both stdin and stdout TTY, we're interactive
    if sys.stdin.isatty() and sys.stdout.isatty():
        return True

    # If we have at least stdout TTY and shell interactive flag, we're interactive
    if sys.stdout.isatty():
        shell_opts = os.getenv("-", "")
        if shell_opts and "i" in shell_opts:
            return True

    # If TERM is set and we're not in a pipe, assume interactive
    if os.getenv("TERM") and sys.stdout.isatty():
        return True

    _debug_log("Update check skipped (reason: non-interactive)")
    return False


def _get_latest_version():
    """Fetch latest version from PyPI."""
    try:
        req = Request("https://pypi.org/pypi/caylent-devcontainer-cli/json")
        req.add_header("User-Agent", f"caylent-devcontainer-cli/{__version__}")

        # Set socket timeouts: connect=2s, read=3s
        old_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(2)

        with urlopen(req, timeout=3) as response:
            if response.status != 200:
                _debug_log(f"Update check skipped (reason: http-status {response.status})")
                return None

            data = response.read()
            if len(data) > 200 * 1024:  # 200KB limit
                _debug_log("Update check skipped (reason: oversized-response)")
                return None

            json_data = json.loads(data.decode())
            return json_data["info"]["version"]

    except (URLError, OSError, socket.timeout):
        _debug_log("Update check skipped (reason: network-timeout)")
        return None
    except (json.JSONDecodeError, KeyError):
        _debug_log("Update check skipped (reason: invalid-json)")
        return None
    finally:
        try:
            socket.setdefaulttimeout(old_timeout)
        except Exception:
            pass


def _version_is_newer(latest, current):
    """Compare versions using semantic versioning."""
    try:
        from packaging import version

        return version.parse(latest) > version.parse(current)
    except Exception as e:
        _debug_log(f"Version parse failed: {e}")
        return False


def _is_installed_with_pipx():
    """Check if CLI is installed with pipx and return the command to use."""
    # Try direct pipx first
    try:
        result = subprocess.run(["pipx", "list", "--json"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if "caylent-devcontainer-cli" in data.get("venvs", {}):
                return True
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
        pass

    # Try python -m pipx
    try:
        result = subprocess.run(["python", "-m", "pipx", "list", "--json"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if "caylent-devcontainer-cli" in data.get("venvs", {}):
                return True
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
        pass

    return False


def _is_editable_installation():
    """Check if this is an editable/development installation."""
    try:
        import caylent_devcontainer_cli

        path = caylent_devcontainer_cli.__file__

        # Check if it's in site-packages or dist-packages (regular installation)
        if "site-packages" in path or "dist-packages" in path:
            return False

        # For pipx, check if it's truly editable by looking for .egg-link or pth files
        if _is_installed_with_pipx():
            # If installed with pipx from local source, check for editable markers
            import os

            parent_dir = os.path.dirname(path)
            # Look for .egg-link file which indicates editable installation
            for root, dirs, files in os.walk(parent_dir):
                if any(f.endswith(".egg-link") for f in files):
                    return True
            # If no .egg-link found, it's likely pipx install . (not editable)
            return False
        else:
            # For pip installations, if not in site-packages, assume editable
            return True
    except Exception:
        return False


def _get_installation_type_display():
    """Get human-readable installation type."""
    is_pipx = _is_installed_with_pipx()
    is_editable = _is_editable_installation()

    if is_pipx and is_editable:
        return "pipx editable"
    elif is_pipx:
        return "pipx"
    elif is_editable:
        return "pip editable"
    else:
        return "pip"


def _show_update_prompt(current, latest):
    """Show update prompt and handle user choice."""
    install_type_display = _get_installation_type_display()

    print("\n🔄 Update Available")
    print(f"Current version: {COLORS['RED']}{current}{COLORS['RESET']} ({install_type_display})")
    print(f"Latest version:  {latest}")
    print()
    print("Select an option:")
    print("  1 - Exit and upgrade manually")
    print("  2 - Continue without upgrading")
    print()
    choice = input("Enter your choice [1]: ").strip() or "1"

    if choice == "1":
        print("\nExiting so you can upgrade manually.")
        _show_manual_upgrade_instructions(install_type_display)
        return EXIT_UPGRADE_REQUESTED_ABORT
    else:
        return EXIT_OK


def _show_manual_upgrade_instructions(install_type):
    """Show manual upgrade instructions based on installation type."""
    print("\nFirst, install pipx:")
    print("  python -m pip install pipx")
    print()

    if install_type == "pipx":
        print("\nUpgrade with pipx:")
        print("  pipx upgrade caylent-devcontainer-cli")

    elif install_type == "pipx editable":
        print("\nUpgrade editable installation:")
        print("  cd /path/to/caylent-devcontainer-cli")
        print("  git pull")
        print("  pipx reinstall -e .")
        print()
        print("Or switch to regular pipx installation:")
        print("  pipx uninstall caylent-devcontainer-cli")
        print("  pipx install caylent-devcontainer-cli")

    elif install_type == "pip editable":
        print("\nUpgrade editable installation:")
        print("  cd /path/to/caylent-devcontainer-cli")
        print("  git pull")
        print("  pip install -e .")
        print()
        print("Or switch to pipx (recommended):")
        print("  pip uninstall caylent-devcontainer-cli")
        print("  pipx install caylent-devcontainer-cli")

    else:  # pip
        print("\nSwitch to pipx:")
        print("  pip uninstall caylent-devcontainer-cli")
        print("  pipx install caylent-devcontainer-cli")


def check_for_updates():
    """Main update check function. Returns True to continue, False to exit."""
    # Check skip conditions
    if os.getenv("CDEVCONTAINER_SKIP_UPDATE") == "1":
        _debug_log("Update check skipped (reason: global disable env)")
        return True

    if not _is_interactive_shell():
        return True

    try:
        # Get latest version
        latest = _get_latest_version()
        if not latest:
            return True

        # Compare versions
        if not _version_is_newer(latest, __version__):
            print(f"✅ You're running the latest version ({__version__})")
            return True

        # Show update prompt
        exit_code = _show_update_prompt(__version__, latest)

        if exit_code == EXIT_OK:
            return True
        elif exit_code == EXIT_UPGRADE_REQUESTED_ABORT:
            sys.exit(exit_code)
        else:
            return True

    except Exception:
        return True
