"""UI utilities for the Caylent Devcontainer CLI."""

import subprocess
import sys
from typing import Any, Callable, Optional

import questionary

from caylent_devcontainer_cli import __version__

# ANSI Colors
COLORS = {
    "CYAN": "\033[1;36m",
    "GREEN": "\033[1;32m",
    "YELLOW": "\033[1;33m",
    "RED": "\033[1;31m",
    "BLUE": "\033[1;34m",
    "PURPLE": "\033[1;35m",
    "RESET": "\033[0m",
    "BOLD": "\033[1m",
}


def log(level, message):
    """Log a message with the specified level."""
    icons = {"INFO": "ℹ️ ", "OK": "✅ ", "WARN": "⚠️ ", "ERR": "❌ "}
    color_map = {
        "INFO": COLORS["CYAN"],
        "OK": COLORS["GREEN"],
        "WARN": COLORS["YELLOW"],
        "ERR": COLORS["RED"],
    }
    reset = COLORS["RESET"]
    icon = icons.get(level, "")
    color = color_map.get(level, "")
    print(f"{color}[{level}]{reset} {icon}{message}", file=sys.stderr)


def exit_with_error(message):
    """Log an error message and exit with code 1.

    Args:
        message: The error message to log at ERR level.
    """
    log("ERR", message)
    sys.exit(1)


def exit_cancelled(message="Operation cancelled by user"):
    """Log a cancellation message and exit with code 0.

    Args:
        message: The cancellation message to log at INFO level.
    """
    log("INFO", message)
    sys.exit(0)


def ask_or_exit(question):
    """Call .ask() on a questionary question, exiting if the user cancels.

    Args:
        question: A questionary question object (before .ask() is called).

    Returns:
        The user's answer.

    Raises:
        SystemExit: If the user cancels (None return) or presses Ctrl+C.
    """
    try:
        result = question.ask()
    except KeyboardInterrupt:
        exit_cancelled()
        return  # Unreachable: exit_cancelled raises SystemExit

    if result is None:
        exit_cancelled()

    return result


def mask_password(value: str) -> str:
    """Mask a password value for safe display.

    Args:
        value: The password string to mask.

    Returns:
        A masked representation showing only the length.
    """
    return f"****** ({len(value)} characters)"


def ssh_fingerprint(key_path: str) -> str:
    """Get the SSH key fingerprint for display.

    Args:
        key_path: Path to the SSH private key file.

    Returns:
        The fingerprint string, or an error message if the key is invalid.
    """
    try:
        result = subprocess.run(
            ["ssh-keygen", "-l", "-f", key_path],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return f"Error reading key: {result.stderr.strip()}"
        return result.stdout.strip()
    except FileNotFoundError:
        return "Error: ssh-keygen not found in PATH"


def prompt_with_confirmation(
    prompt_fn: Callable[[], Any],
    display_fn: Optional[Callable[[Any], str]] = None,
) -> Any:
    """Prompt the user for input with a confirmation loop.

    Implements the universal input confirmation pattern:
    1. Call prompt_fn() to get a questionary question, then ask_or_exit() it
    2. Display the entered value (formatted by display_fn if provided)
    3. Ask "Is this correct?"
    4. If no: repeat from step 1
    5. If yes: return the value

    Args:
        prompt_fn: Callable that returns a questionary question object.
        display_fn: Optional callable to format the value for display.
                    If None, displays the raw value. Use mask_password
                    for password fields, ssh_fingerprint for key paths.

    Returns:
        The confirmed user input value.

    Raises:
        SystemExit: If the user cancels at any point.
    """
    while True:
        answer = ask_or_exit(prompt_fn())

        if display_fn is not None:
            display_value = display_fn(answer)
        else:
            display_value = str(answer)

        log("INFO", f"You entered: {display_value}")

        confirmed = ask_or_exit(questionary.confirm("Is this correct?", default=True))
        if confirmed:
            return answer


def confirm_action(message):
    """Ask for user confirmation before proceeding."""
    print(f"{COLORS['YELLOW']}⚠️  {message}{COLORS['RESET']}")
    response = input(f"{COLORS['BOLD']}Do you want to continue? [y/N]{COLORS['RESET']} ")
    if not response.lower().startswith("y"):
        log("ERR", "Operation cancelled by user")
        return False
    print()
    return True


def show_banner():
    """Display a fancy banner."""
    print(f"{COLORS['BLUE']}╔═══════════════════════════════════════════════════════════╗")
    print("║                                                           ║")
    print(f"║   {COLORS['CYAN']}🐳 Caylent Devcontainer CLI v{__version__}{COLORS['BLUE']}                      ║")
    print("║                                                           ║")
    print(f"╚═══════════════════════════════════════════════════════════╝{COLORS['RESET']}")
    print()
