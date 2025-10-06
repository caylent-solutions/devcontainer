"""Version checking and update utilities for the Caylent Devcontainer CLI."""

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from caylent_devcontainer_cli import __version__
from caylent_devcontainer_cli.utils.ui import COLORS

# Exit codes
EXIT_OK = 0
EXIT_UPGRADE_PERFORMED = 20
EXIT_UPGRADE_REQUESTED_ABORT = 21
EXIT_UPGRADE_FAILED = 30
EXIT_INVALID_INSTALL_CONTEXT = 31
EXIT_VERSION_PARSE_ERROR = 32
EXIT_LOCK_CONTENTION = 40

# Cache and lock settings
CACHE_DIR = Path(os.getenv("XDG_CACHE_HOME", Path.home() / ".cache")) / "cdevcontainer"
LOCK_FILE = CACHE_DIR / "update.lock"
LOCK_TIMEOUT = 120  # 2 minutes


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


def _acquire_lock():
    """Acquire update lock, return True if successful."""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

        # Check for existing lock
        if LOCK_FILE.exists():
            try:
                with open(LOCK_FILE, "r") as f:
                    lock_data = json.load(f)
                lock_age = time.time() - lock_data.get("created", 0)

                if lock_age < LOCK_TIMEOUT:
                    _debug_log(f"Skipped update due to active lock (pid={lock_data.get('pid')}, age={lock_age:.1f}s)")
                    print(f"Update check skipped due to active lock. If stuck, delete: {LOCK_FILE}")
                    return False
                else:
                    _debug_log("Stale lock reclaimed")
            except (json.JSONDecodeError, KeyError):
                pass

        # Create new lock atomically
        lock_data = {"pid": os.getpid(), "created": time.time()}

        # Use atomic creation with O_CREAT|O_EXCL
        try:
            fd = os.open(str(LOCK_FILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            with os.fdopen(fd, "w") as f:
                json.dump(lock_data, f)
            return True
        except FileExistsError:
            # Lock already exists, skip this time
            _debug_log("Lock file exists, skipping update check")
            return False

    except (OSError, PermissionError):
        _debug_log("Lock creation failed, proceeding without lock")
        return True  # Proceed without lock


def _release_lock():
    """Release update lock."""
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except OSError:
        pass


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


def _get_pipx_command():
    """Get the correct pipx command to use based on where the package is installed."""
    # Try direct pipx first
    try:
        result = subprocess.run(["pipx", "list", "--json"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if "caylent-devcontainer-cli" in data.get("venvs", {}):
                return ["pipx"]
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
        pass

    # Try python -m pipx
    try:
        result = subprocess.run(["python", "-m", "pipx", "list", "--json"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if "caylent-devcontainer-cli" in data.get("venvs", {}):
                return ["python", "-m", "pipx"]
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
        pass

    # Fallback: check if pipx is available at all
    try:
        subprocess.run(["pipx", "--version"], capture_output=True, timeout=2)
        return ["pipx"]
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ["python", "-m", "pipx"]


def _is_pipx_available():
    """Check if pipx command is available."""
    try:
        subprocess.run(["pipx", "--version"], capture_output=True, timeout=5)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        try:
            subprocess.run(["python", "-m", "pipx", "--version"], capture_output=True, timeout=5)
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
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


def _upgrade_with_pipx():
    """Perform automatic upgrade with pipx."""
    try:
        print("\nUpgrading with pipx...")

        # Get the correct pipx command
        pipx_cmd = _get_pipx_command()

        # Try upgrade first
        result = subprocess.run(
            pipx_cmd + ["upgrade", "caylent-devcontainer-cli"], capture_output=True, text=True, timeout=60
        )

        _debug_log(
            f"pipx upgrade result: returncode={result.returncode}, stdout={result.stdout}, stderr={result.stderr}"
        )

        # If upgrade fails OR pipx thinks local version is latest, reinstall from PyPI
        if result.returncode != 0 or "is already at latest version" in result.stdout:
            print("Standard upgrade failed, reinstalling from PyPI...")
            _debug_log("Attempting uninstall and reinstall from PyPI")

            # Uninstall current installation (ignore errors)
            uninstall_result = subprocess.run(
                pipx_cmd + ["uninstall", "caylent-devcontainer-cli"], capture_output=True, text=True, timeout=30
            )
            _debug_log(f"Uninstall result: {uninstall_result.returncode}")

            # Install from PyPI explicitly (this is the important step)
            install_result = subprocess.run(
                pipx_cmd + ["install", "--force", "caylent-devcontainer-cli"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd="/",  # Change to root directory to avoid local source
            )
            _debug_log(f"Reinstall result: returncode={install_result.returncode}, stderr={install_result.stderr}")

            # Use install result for success/failure determination
            result = install_result

        if result.returncode == 0:
            print("Upgrade successful. Please re-run your command.")
            return EXIT_UPGRADE_PERFORMED
        else:
            _debug_log(f"pipx upgrade failed: {result.stderr}")
            print("Upgrade failed. See manual instructions below.")
            _show_pipx_instructions()
            return EXIT_UPGRADE_FAILED

    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
        _debug_log(f"pipx upgrade exception: {e}")
        print("Upgrade failed. See manual instructions below.")
        _show_pipx_instructions()
        return EXIT_UPGRADE_FAILED


def _show_pipx_instructions():
    """Show manual pipx upgrade instructions."""
    print("\nManual upgrade with pipx:")
    print("  pipx upgrade caylent-devcontainer-cli")


def _show_pip_instructions():
    """Show manual pip upgrade instructions."""
    print("\nManual upgrade options:")
    print("Option 1 - Switch to pipx (recommended):")
    print("  pip uninstall caylent-devcontainer-cli")
    print("  pipx install caylent-devcontainer-cli")
    print()
    print("Option 2 - Upgrade with pip:")
    print("  pip install --upgrade caylent-devcontainer-cli")


def _show_reinstall_instructions():
    """Show reinstall instructions for editable installations."""
    print("\nReinstall from PyPI:")
    print("  pipx install caylent-devcontainer-cli")
    print()
    print("Or continue using development version with:")
    print("  git pull && pip install -e .")


def _install_pipx():
    """Install pipx if not available."""
    try:
        print("Installing pipx...")
        result = subprocess.run(["python", "-m", "pip", "install", "pipx"], capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print("pipx installed successfully.")
            return True
        else:
            print(f"Failed to install pipx: {result.stderr}")
            return False
    except Exception as e:
        print(f"Failed to install pipx: {e}")
        return False


def _upgrade_to_pipx_from_pypi(install_type):
    """Upgrade to pipx installation from PyPI for all scenarios."""
    # Ensure pipx is available
    if not _is_pipx_available():
        if not _install_pipx():
            print("Cannot proceed without pipx. Please install pipx manually.")
            return EXIT_UPGRADE_FAILED

    # Get the correct pipx command
    pipx_cmd = _get_pipx_command()

    try:
        # Clean up existing installation
        if install_type == "pipx":
            print("Upgrading pipx installation...")
            result = subprocess.run(
                pipx_cmd + ["upgrade", "caylent-devcontainer-cli"], capture_output=True, text=True, timeout=60
            )
        elif install_type == "pipx editable":
            print("Removing pipx editable installation...")
            subprocess.run(pipx_cmd + ["uninstall", "caylent-devcontainer-cli"], capture_output=True, timeout=30)
            print("Installing from PyPI with pipx...")
            result = subprocess.run(
                pipx_cmd + ["install", "caylent-devcontainer-cli"], capture_output=True, text=True, timeout=60
            )
        elif "pip" in install_type:
            print("Removing pip installation...")
            subprocess.run(["pip", "uninstall", "-y", "caylent-devcontainer-cli"], capture_output=True, timeout=30)
            print("Installing from PyPI with pipx...")
            result = subprocess.run(
                pipx_cmd + ["install", "caylent-devcontainer-cli"], capture_output=True, text=True, timeout=60
            )

        if result.returncode == 0:
            print("Upgrade successful. Please re-run your command.")
            return EXIT_UPGRADE_PERFORMED
        else:
            print(f"Upgrade failed: {result.stderr}")
            return EXIT_UPGRADE_FAILED

    except Exception as e:
        print(f"Upgrade failed: {e}")
        return EXIT_UPGRADE_FAILED


def _show_manual_upgrade_instructions(install_type):
    """Show manual upgrade instructions based on installation type."""
    pipx_available = _is_pipx_available()

    if not pipx_available:
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

    # Acquire lock
    if not _acquire_lock():
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
        elif exit_code in (EXIT_UPGRADE_PERFORMED, EXIT_UPGRADE_REQUESTED_ABORT, EXIT_UPGRADE_FAILED):
            sys.exit(exit_code)
        else:
            return True

    finally:
        _release_lock()
