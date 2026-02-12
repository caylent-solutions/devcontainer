"""UI utilities for the Caylent Devcontainer CLI."""

import sys

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
